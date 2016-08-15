from collections import deque
from enum import Enum

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientFactory

from ..utils.logging import *
from ..crypto.crypto import *
from ..client.client_session import *

class HermesClientProtocol(Protocol):

    class State(Enum):
        initial = 0
        signing = 1
        verifying = 2
        session = 3

    def __init__(self, factory):
        self.factory = factory
        self.state = self.State.initial
        self.peer = None
        self.session = None

    def connectionMade(self):
        self.peer = self.transport.getPeer()
        self._asymmetrically_signed_encrypted_write(self.factory.public_key_str)
        self.state = self.State.signing

    def disconnect(self):
        self.transport.loseConnection()

    def login(self, username, public_key, private_key):
        log("CLIENT: Logging in as: {0}".format(username))
        self.session.login(username, public_key, private_key)

    def add_user(self, public_key, username=None):
        # TODO: definitely need a coherent user-management scheme
        assert self.session
        return self.session.add_user(public_key, username)

    def start_convo(self, with_user):
        assert self.session
        return self.session.start_convo(with_user)

    def _asymmetrically_signed_encrypted_write(self, data):
        ciphertext = asymmetric_encrypt_sign(data,
                                             self.factory.server_public_key,
                                             self.factory.private_key)
        self.transport.write(ciphertext)

    def _asymmetric_decrypt_verify(self, data):
        return asymmetric_decrypt_verify(data,
                                         self.factory.private_key,
                                         self.factory.server_public_key)

    def _symmetric_encrypt_send(self, data, key=None):
        assert data
        key = key if key else self.session.key
        if not key:
            log("CLIENT WARNING: Attempted to send session message before session was established")
            return
        ciphertext = symmetric_encrypt(data, key)
        self.transport.write(ciphertext)

    def _symmetric_decrypt(self, data, key=None):
        key = key if key else self.session.key
        if not key:
            log("CLIENT WARNING: Attempted to interpret session message before session was established")
            return
        plaintext = symmetric_decrypt(data, key)
        return plaintext

    def _handle_challenge(self, data):
        challenge = self._asymmetric_decrypt_verify(data)
        if challenge:
            log("CLIENT: Received challenge: {0}".format(challenge))
            self._asymmetrically_signed_encrypted_write(challenge)
            self.state = self.State.verifying
        else:
            log("CLIENT: Could not decrypt/verify challenge")
            self.disconnect()

    def _handle_session_key(self, data):
        session_key = self._asymmetric_decrypt_verify(data)
        if session_key:
            self.session = ClientSession(session_key, self)
            log("CLIENT: Session Established {0}".format(self.peer))
            self.state = self.State.session
        else:
            log("CLIENT: Could not decrypt/verify session key")
            self.disconnect()

    def send_session_message(self, msg):
        self._symmetric_encrypt_send(msg)

    def dataReceived(self, data):
        if self.state == self.State.signing:
            self._handle_challenge(data)
        elif self.state == self.State.verifying:
            self._handle_session_key(data)
        elif self.state == self.State.session:
            assert self.session
            plaintext = self._symmetric_decrypt(data)
            self.session.handle_message(plaintext)


class HermesClientFactory(ClientFactory):

    def __init__(self, private_key, public_key, server_public_key):
        self.private_key = private_key
        self.public_key = public_key
        self.public_key_str = public_key_to_str(self.public_key)
        self.server_public_key = server_public_key

    def buildProtocol(self, addr):
        return HermesClientProtocol(self)

    def clientConnectionFailed(self, connector, reason):
        print("Connection failed.")
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print("Connection lost.")
        reactor.stop()


class HermesClient(object):
    def __init__(self, url, port, server_pub_key_filepath, priv_key_filepath, pub_key_filepath):
        self.priv_key = private_key_from_file(priv_key_filepath)
        self.pub_key = public_key_from_file(pub_key_filepath)
        self.server_pubKey = public_key_from_file(server_pub_key_filepath)
        self.server_url = url
        self.server_port = port
        self.outgoing_session_msgs = deque([])
        self.incoming_session_msgs = deque([])

    def run(self):
        reactor.connectTCP(self.server_url, self.server_port, HermesClientFactory(self.priv_key, self.pub_key, self.server_pubKey))
        reactor.run()
