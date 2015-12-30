from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientFactory
from enum import Enum

from ..utils.logging import *
from ..crypto.crypto import *


class HermesClientProtocol(Protocol):

    class State(Enum):
        initial = 0
        signing = 1
        verifying = 2
        session = 3

    def __init__(self, factory):
        self.factory = factory
        self.state = self.SessionState.initial
        self.session = None

    def connectionMade(self):
        self._asymmetrically_signed_encrypted_write(self.factory.pub_key_str)

    def disconnect(self):
        self.transport.loseConnection()

    def _asymmetrically_signed_encrypted_write(self, data):
        ciphertext = asymmetric_encrypt_sign(data, self.factory.priv_key, self.factory.server_pub_key)
        self.transport.write(ciphertext)

    def _asymmetric_decrypt_verify(self, data):
        return asymmetric_decrypt_verify(data, self.factory.server_pub_key,
                                         self.factory.priv_key)

    def _handle_challenge(self, data):
        challenge = self._asymmetric_decrypt_verify(data)
        if challenge:
            self._asymmetrically_signed_encrypted_write(challenge)
        else:
            self.disconnect()

    def _handle_session_key(self, data):
        session_key = self._asymmetric_decrypt_verify(data)
        if session_key:
            self.session = ClientSession(session_key)
        else:
            self.disconnect()

    def dataReceived(self, data):
        if self.state == self.State.signing:
            self._handle_challenge(data)
        elif self.state == self.State.verifying:
            self.handle_session_key(data)
        elif self.state == self.State.session:
            assert self.session
            self.session.data_received(data)


class HermesClientFactory(ClientFactory):

    def __init__(self, private_key, public_key, server_pub_key):
        self.private_key = private_key
        self.public_key = public_key
        self.server_pub_key = server_pub_key

    def buildProtocol(self, addr):
        return HermesClientProtocol(self.client_id)

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
        self.pub_key_str = public_key_to_str(self.pub_key)
        self.server_pubKey = public_key_from_file(server_pub_key_filepath)
        self.server_url = url
        self.server_port = port

    def run(self):
        reactor.connectTCP(self.server_url, self.server_port, HermesClientFactory(self.priv_key, self.pub_key, self.server_pubKey))
        reactor.run()
