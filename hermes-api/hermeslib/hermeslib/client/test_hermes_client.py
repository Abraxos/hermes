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


def establish_session(client, server, transport):
    # Server started
    server.makeConnection(transport)

    # Client sends over their public key to the server
    client.makeConnection(transport)
    client_response = transport.value()
    transport.clear()

    challenge = send_receive(server, transport, client_response)
    challenge_signature = send_receive(client, transport, challenge)
    session_key = send_receive(server, transport, challenge_signature)
    send_receive(client, transport, session_key)


class ClientTestCase(unittest.TestCase):
    _server_private_key = private_key_from_file(
        'hermeslib/tests/testing_data/server_test_key.pem')
    _server_public_key = public_key_from_file(
        'hermeslib/tests/testing_data/server_test_pub_key.pem')
    _client_a_private_key = private_key_from_file(
        'hermeslib/tests/testing_data/client1_test_key.pem')
    _client_a_public_key = public_key_from_file(
        'hermeslib/tests/testing_data/client1_test_pub_key.pem')
    _client_b_private_key = private_key_from_file(
        'hermeslib/tests/testing_data/client2_test_key.pem')
    _client_b_public_key = public_key_from_file(
        'hermeslib/tests/testing_data/client2_test_pub_key.pem')
    _user1_public_key = public_key_from_file(
        'hermeslib/tests/testing_data/user1_test_pub_key.pem')
    _user1_private_key = private_key_from_file(
        'hermeslib/tests/testing_data/user1_test_key.pem')
    _user2_public_key = public_key_from_file(
        'hermeslib/tests/testing_data/user2_test_pub_key.pem')
    _user2_private_key = private_key_from_file(
        'hermeslib/tests/testing_data/user2_test_key.pem')

    def test_basic_establish_session(self):
        server_factory = HermesFactory(self._server_private_key,
                                       self._server_public_key)
        client_factory = HermesClientFactory(self._client_a_private_key,
                                             self._client_a_public_key,
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
        client_factory = HermesClientFactory(self._client_a_private_key,
                                             self._client_a_public_key,
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

    def test_client_to_client_establish_conversation(self):
        server_factory = HermesFactory(self._server_private_key,
                                       self._server_public_key)
        client_a_factory = HermesClientFactory(self._client_a_private_key,
                                               self._client_a_public_key,
                                               self._server_public_key)

        client_b_factory = HermesClientFactory(self._client_b_private_key,
                                               self._client_b_public_key,
                                               self._server_public_key)

        server_a_transport = proto_helpers.StringTransport()
        server_b_transport = proto_helpers.StringTransport()

        server_a = server_factory.buildProtocol("localhost")
        server_b = server_factory.buildProtocol("localhost")
        client_a = client_a_factory.buildProtocol("localhost")
        client_b = client_b_factory.buildProtocol("localhost")

        establish_session(client_a, server_a, server_a_transport)
        establish_session(client_b, server_b, server_b_transport)

        # Check that both client and the server are in a session using the same session key
        self.assertTrue(client_a.session)
        self.assertTrue(client_a.session.key)
        self.assertTrue(server_a.session)
        self.assertTrue(server_a.session.key)
        self.assertEqual(server_a.session.key, client_a.session.key)

        self.assertTrue(client_b.session)
        self.assertTrue(client_b.session.key)
        self.assertTrue(server_b.session)
        self.assertTrue(server_b.session.key)
        self.assertEqual(server_b.session.key, client_b.session.key)

        # Once a session has been established, we can attempt to login:
        login(client_a, server_a, server_a_transport, b'Eugene',
              self._user1_public_key, self._user1_private_key)
        login(client_b, server_b, server_b_transport, b'Jonathan',
              self._user2_public_key, self._user2_private_key)

        self.assertEqual(server_a.session.message_buffer[-1], b'LOGIN_USERNAME:Eugene')
        self.assertEqual(client_a.session.message_buffer[-1], b'LOGIN_USERNAME_ACCEPT:')
        self.assertEqual(server_b.session.message_buffer[-1], b'LOGIN_USERNAME:Jonathan')
        self.assertEqual(client_b.session.message_buffer[-1], b'LOGIN_USERNAME_ACCEPT:')

        jonathan = client_a.add_user(self._user2_public_key, b'Jonathan')
        eugene = client_b.add_user(self._user1_public_key, b'Eugene')

        client_a_convo = client_a.start_convo(jonathan)
        m = server_a_transport.value()
        server_a_transport.clear()
        # A(START_CONVERSATION)->S(START_CONVERSATION)->B
        m = send_receive(server_a, server_b_transport, m)
        # S(START_CONVERSATION)->B(START_CONVERSATION_CHALLENGE)->S
        m = send_receive(client_b, server_b_transport, m)
        # B(START_CONVERSATION_CHALLENGE)->S(START_CONVERSATION_CHALLENGE)->A
        m = send_receive(server_b, server_a_transport, m)
        # S(START_CONVERSATION_CHALLENGE)->A(START_CONVERSATION_RESPONSE)->S
        m = send_receive(client_a, server_a_transport, m)
        # A(START_CONVERSATION_RESPONSE)->S(START_CONVERSATION_RESPONSE)->B
        m = send_receive(server_a, server_b_transport, m)
        # S(START_CONVERSATION_RESPONSE)->B(START_CONVERSATION_ACCEPT)->S
        m = send_receive(client_b, server_b_transport, m)
        # B(START_CONVERSATION_ACCEPT)->S(START_CONVERSATION_ACCEPT)->A
        m = send_receive(server_b, server_a_transport, m)
        # S(START_CONVERSATION_ACCEPT)->A(START_CONVERSATION_KEY)->S
        m = send_receive(client_a, server_a_transport, m)
        # A(START_CONVERSATION_KEY)->S(START_CONVERSATION_KEY)->B
        m = send_receive(server_a, server_b_transport, m)
        # S(START_CONVERSATION_KEY)->B
        send_receive(client_b, server_b_transport, m)

        client_b_convo = client_b.session.conversations[client_a_convo.id]

        self.assertEqual(client_b_convo.state, client_b_convo.State.conversing)
        self.assertEqual(client_a_convo.state, client_a_convo.State.conversing)

        self.assertEqual(client_a_convo.key, client_b_convo.key)
