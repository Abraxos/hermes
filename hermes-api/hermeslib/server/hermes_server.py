#!/usr/bin/python3

from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol


from ..server.server_session import *


class User(object):
    def __init__(self, public_key, username):
        self.public_key = public_key
        self.username = username
        self.protocols = {}


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
        self._peer = None
        self.session = None
        self.challenge = Random.get_random_bytes(32)

    def id(self):
        return self.client_sha256

    def connectionMade(self):
        self._peer = self.transport.getPeer()
        log("New Client Connected: {0}".format(self._peer))

    def disconnect(self):
        self.transport.loseConnection()

    def connectionLost(self, reason=None):
        del self.factory.protocols[self.id()]

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

    def _initial_failure(self):
        log("SERVER WARNING:[{0}]: Client sent invalid initial data.".format(self._peer))
        self.transport.write(b"Initial failure.")
        self.disconnect()

    def _handle_device_pubkey(self, data):
        client_public_key_str = asymmetric_decrypt_verify_public_key(data, self.factory.private_key)
        if client_public_key_str:
            self.client_pub_key = public_key_from_str(client_public_key_str)
            self.client_sha256 = public_key_sha256(self.client_pub_key)
            self.state = self.State.challenging
            self._asymmetrically_signed_encrypted_write(self.challenge)
        else:
            self._initial_failure()

    def _challenge_failure(self):
        log("SERVER WARNING:[{0}]: Client failed challenge.".format(self._peer))
        self.transport.write(b"Challenge failure.")
        self.disconnect()

    def _handle_challenge_signature(self, data):
        signature = self._asymmetric_decrypt_verify(data)
        if signature:
            self.factory.protocols[self.id()] = self
            self.session = ServerSession()
            self.state = self.State.session
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
            self.session.data_received(data)
        else:
            log("SERVER WARNING:[{0}]: Protocol received message in and invalid state. Message Ignored.".format(self._peer))


class HermesFactory(Factory):

    def __init__(self, private_key, public_key):
        self.protocols = {}  # dictionary of protocols indexed by the SHA256 of the public key of their user
        self.private_key = private_key
        self.public_key = public_key

    def buildProtocol(self, address):
        return HermesProtocol(self)

    def add_client(self, pub_key, protocol):
        self.protocols[pub_key] = protocol


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
