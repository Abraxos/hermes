#!/usr/bin/python3

from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol
from enum import Enum

from ..utils.logging import *
from ..crypto.crypto import *


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
        self.session = None
        self.challenge = Random.get_random_bytes(32)

    def connectionMade(self):
        log("New Client Connected: " + self.transport.client)
        self.factory.clients.append(self)

    def connectionLost(self, reason=None):
        self.factory.remove_client(self.client_pub_key)

    def _asymmetrically_signed_encrypted_write(self, data):
        ciphertext = asymmetric_encrypt_sign(data, self.factory.priv_key, self.client_pub_key)
        self.transport.write(ciphertext)

    def _handle_device_pubkey(self, data):
        self.client_pub_key = public_key_from_str(self.factory.rsa_key.decrypt(data))
        self._asymmetrically_signed_encrypted_write(self.challenge)

    def _handle_challenge_signature(self, data):
        signature = self.factory.rsa_key.decrypt(data)
        if self.client_pub_key.verify(self.challenge, signature):
            self.session = ServerSession()
            self._asymmetrically_signed_encrypted_write(self.session.key)

    def dataReceived(self, data):
        print("Received: " + str(data))
        if self.state == self.State.initial:
            self._handle_device_pubkey(data)
        elif self.state == self.State.challenging:
            self._handle_challenge_signature(data)
        elif self.state == self.State.session:
            assert self.session
            self.session.data_received(data)
        else:
            log("WARNING: Protocol received message in and invalid state. Message Ignored.")


class HermesFactory(Factory):

    def __init__(self, private_key, public_key):
        self.protocols = {}  # dictionary of protocols indexed by the public key of their user
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
