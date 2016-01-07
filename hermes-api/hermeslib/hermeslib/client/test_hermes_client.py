from twisted.test import proto_helpers
from twisted.trial import unittest

from hermeslib.server.hermes_server import *
from hermeslib.client.hermes_client import *
import time

def send_receive(protocol, transport, message):
    protocol.dataReceived(message)
    response = transport.value()
    transport.clear()
    return response

def login(client, server, transport, username, user_pub, user_priv):
    client.login(username, user_pub, user_priv)
    login_command = transport.value()
    transport.clear()

    challenge = send_receive(server, transport, login_command)
    challenge_signature = send_receive(client, transport, challenge)
    server_ack = send_receive(server, transport, challenge_signature)
    client_username = send_receive(client, transport, server_ack)
    server_accept = send_receive(server, transport, client_username)
    send_receive(client, transport, server_accept)

class MyTestCase(unittest.TestCase):
    _server_private_key = private_key_from_file(
        'hermeslib/tests/testing_data/server_test_key.pem')
    _server_public_key = public_key_from_file(
        'hermeslib/tests/testing_data/server_test_key_pub.pem')
    _client_private_key = private_key_from_file(
        'hermeslib/tests/testing_data/client1_test_key.pem')
    _client_public_key = public_key_from_file(
        'hermeslib/tests/testing_data/client1_test_key_pub.pem')
    _user1_public_key = public_key_from_file(
        'hermeslib/tests/testing_data/user1_test_pub.pem')
    _user1_private_key = private_key_from_file(
        'hermeslib/tests/testing_data/user1_test.pem')

    def test_basic_establish_session(self):
        server_factory = HermesFactory(self._server_private_key,
                                       self._server_public_key)
        client_factory = HermesClientFactory(self._client_private_key,
                                             self._client_public_key,
                                             self._server_public_key)

        transport = proto_helpers.StringTransport()

        server_protocol = server_factory.buildProtocol("localhost")
        client_protocol = client_factory.buildProtocol("localhost")

        # Server started
        server_protocol.makeConnection(transport)
        
        # Client sends over their public key to the server
        client_protocol.makeConnection(transport)
        client_response = transport.value()
        transport.clear()

        # Server replies with a challenge
        challenge = send_receive(server_protocol, transport, client_response)

        # Client sign challenge
        challenge_signature = send_receive(client_protocol, transport, challenge)

        # Server verifies client signature
        session_key = send_receive(server_protocol, transport, challenge_signature)

        # Client receives session key
        send_receive(client_protocol, transport, session_key)
        
        # Check that both the client and the server are in a session using the same session key
        self.assertTrue(client_protocol.session)
        self.assertTrue(client_protocol.session.key)
        self.assertTrue(server_protocol.session)
        self.assertTrue(server_protocol.session.key)
        self.assertEqual(server_protocol.session.key, client_protocol.session.key)

    def test_basic_client_login(self):
        server_factory = HermesFactory(self._server_private_key,
                                       self._server_public_key)
        client_factory = HermesClientFactory(self._client_private_key,
                                             self._client_public_key,
                                             self._server_public_key)

        transport = proto_helpers.StringTransport()

        server_protocol = server_factory.buildProtocol("localhost")
        client_protocol = client_factory.buildProtocol("localhost")

        # Server started
        server_protocol.makeConnection(transport)
        
        # Client sends over their public key to the server
        client_protocol.makeConnection(transport)
        client_response = transport.value()
        transport.clear()

        challenge = send_receive(server_protocol, transport, client_response)
        challenge_signature = send_receive(client_protocol, transport, challenge)
        session_key = send_receive(server_protocol, transport, challenge_signature)
        send_receive(client_protocol, transport, session_key)
        
        # Check that both the client and the server are in a session using the same session key
        self.assertTrue(client_protocol.session)
        self.assertTrue(client_protocol.session.key)
        self.assertTrue(server_protocol.session)
        self.assertTrue(server_protocol.session.key)
        self.assertEqual(server_protocol.session.key, client_protocol.session.key)

        # Once a session has been established, we can attempt to login:
        login(client_protocol, 
              server_protocol, 
              transport, 
              b'Eugene', 
              self._user1_public_key, 
              self._user1_private_key)

        self.assertEqual(server_protocol.session.message_buffer[-1], b'LOGIN_USERNAME:Eugene')
        self.assertEqual(client_protocol.session.message_buffer[-1], b'LOGIN_USERNAME_ACCEPT:')
