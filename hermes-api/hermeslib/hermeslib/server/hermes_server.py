#!/usr/bin/python3

from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol

from ..server.server_session import *
from ..server.users import *


class ServerConversation(object):
    def __init__(self, conversation_id):
        self.id = conversation_id
        self.participants = []


class HermesProtocol(Protocol):
    class State(Enum):
        initial = 0
        challenging = 1
        session = 2

    def __init__(self, factory):
        self.factory = factory
        self.state = self.State.initial
        self.client_pub_key = None
        self.client_sha256 = None
        self.peer = None
        self.session = None
        self.challenge = Random.get_random_bytes(32)

    def id(self):
        return self.client_sha256

    def connectionMade(self):
        self.peer = self.transport.getPeer()
        log("New Client Connected: {0}".format(self.peer))

    def disconnect(self):
        self.transport.loseConnection()

    def connectionLost(self, reason=None):
        del self.factory.protocols[self.id()]

    def _symmetric_encrypt_send(self, data, key=None):
        assert data
        key = key if key else self.session.key
        if not key:
            log("SERVER WARNING: Attempted to send session message before session was established")
            return
        ciphertext = symmetric_encrypt(data, key)
        self.transport.write(ciphertext)

    def _symmetric_decrypt(self, data, key=None):
        key = key if key else self.session.key
        if not key:
            log("SERVER WARNING: Attempted to interpret session message before session was established")
            return
        plaintext = symmetric_decrypt(data, key)
        return plaintext

    def _asymmetrically_signed_encrypted_write(self, data):
        assert self.client_pub_key
        ciphertext = asymmetric_encrypt_sign(data,
                                             self.client_pub_key,
                                             self.factory.private_key)
        self.transport.write(ciphertext)

    def _asymmetric_decrypt_verify(self, data):
        return asymmetric_decrypt_verify(data,
                                         self.factory.private_key,
                                         self.client_pub_key)

    def send_session_message(self, msg):
        self._symmetric_encrypt_send(msg)

    def _initial_failure(self):
        log("SERVER WARNING:[{0}]: Client sent invalid initial data.".format(self.peer))
        self.transport.write(b"Initial failure.")
        self.disconnect()

    def _handle_device_pubkey(self, data):
        client_public_key_str = asymmetric_decrypt_verify_public_key(data, self.factory.private_key)
        if client_public_key_str:
            self.client_pub_key = public_key_from_str(client_public_key_str)
            self.client_sha256 = public_key_sha256(self.client_pub_key)
            self.state = self.State.challenging
            log("SERVER: Challenging: {0}".format(repr(self.challenge)))
            self._asymmetrically_signed_encrypted_write(self.challenge)
        else:
            self._initial_failure()

    def _challenge_failure(self):
        log("SERVER WARNING:[{0}]: Client failed challenge.".format(self.peer))
        self.transport.write(b"Challenge failure.")
        self.disconnect()

    def _handle_challenge_signature(self, data):
        signature = self._asymmetric_decrypt_verify(data)
        if signature:
            log("SERVER: Received challenge signature: {0}".format(repr(signature)))
            self.factory.protocols[self.id()] = self
            self.session = ServerSession(self)
            self.state = self.State.session
            log("SERVER: Responding with key: {0}".format(repr(self.session.key)))
            self._asymmetrically_signed_encrypted_write(self.session.key)
        else:
            self._challenge_failure()

    def dataReceived(self, data):
        if self.state == self.State.initial:
            self._handle_device_pubkey(data)
        elif self.state == self.State.challenging:
            self._handle_challenge_signature(data)
        elif self.state == self.State.session:
            assert self.session
            self.session.handle_message(self._symmetric_decrypt(data))
        else:
            log("SERVER WARNING:[{0}]: Protocol received message in an invalid state. Message Ignored.".format(self.peer))


class HermesFactory(Factory):

    def __init__(self, private_key, public_key):
        self.protocols = {}  # dictionary of protocols indexed by the SHA256 of the public key of their user
        self.private_key = private_key
        self.public_key = public_key
        self.user_list = UserList()
        self.conversations = {} # dict of conversations indexed by their ids

    def buildProtocol(self, address):
        return HermesProtocol(self)

    def add_client(self, pub_key, protocol):
        self.protocols[pub_key] = protocol

    def deliver_conversation_message


class HermesServer(object):
    def __init__(self, port, private_key_filepath, public_key_filepath):
        self.port = port
        self.private_key = private_key_from_file(private_key_filepath)
        self.public_key = public_key_from_file(public_key_filepath)

    def run(self):
        reactor.listenTCP(self.port, HermesFactory(self.private_key, self.public_key))
        reactor.run()

if __name__ == '__main__':
    server = HermesServer(8080, "../server_test_key.pem", "Something something something dark side")
    server.run()
    # TODO: Write an argument handler for the server program
