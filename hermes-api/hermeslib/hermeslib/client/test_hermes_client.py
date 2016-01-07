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

    def test_establish_session(self):
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

    def test_client_login(self):
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

        # Once a session has been established, we can attempt to login:
        client_protocol.login("Eugene",self._user1_public_key, self._user1_private_key)
        challenge = transport.value()
        transport.clear()

    def test_challenge_verification(self):
        pass
        # factory = HermesFactory(self._server_private_key,
        #                         self._server_public_key)
        # self.p = factory.buildProtocol("localhost")
        # self.transport = proto_helpers.StringTransport()

        # pks = public_key_to_str(self._client_public_key)
        # ciphertext = asymmetric_encrypt_sign(pks,
        #                                      self._server_public_key,
        #                                      self._client_private_key)

        # self.p.makeConnection(self.transport)
        # self.p.dataReceived(ciphertext)
        # c = asymmetric_decrypt_verify(self.transport.value(),
        #                               self._client_private_key,
        #                               self._server_public_key)
        # self.transport.clear()
        # self.assertTrue(c)
        # self.assertEqual(c, self.p.challenge)

        # self.p.dataReceived(
        #     asymmetric_encrypt_sign(c,
        #                             self._server_public_key,
        #                             self._client_private_key))
        # server_reply = asymmetric_decrypt_verify(self.transport.value(),
        #                                          self._client_private_key,
        #                                          self._server_public_key)
        # self.transport.clear()
        # self.assertTrue(server_reply)
        # self.assertEqual(server_reply, self.p.session.key)

    def test_challenge_verification_failure(self):
        pass
        # factory = HermesFactory(self._server_private_key,
        #                         self._server_public_key)
        # self.proto = factory.buildProtocol("localhost")
        # self.transport = proto_helpers.StringTransport()

        # pks = public_key_to_str(self._client_public_key)
        # ciphertext = asymmetric_encrypt_sign(pks,
        #                                      self._server_public_key,
        #                                      self._client_private_key)

        # self.proto.makeConnection(self.transport)
        # self.proto.dataReceived(ciphertext)
        # challenge = asymmetric_decrypt_verify(self.transport.value(),
        #                                       self._client_private_key,
        #                                       self._server_public_key)
        # self.transport.clear()
        # self.assertTrue(challenge)
        # self.assertEqual(challenge, self.proto.challenge)

        # self.proto.dataReceived(
        #     asymmetric_encrypt_sign(challenge,
        #                             self._server_public_key,
        #                             self._server_private_key))
        # server_reply = self.transport.value()
        # self.assertEqual(server_reply, b"Challenge failure.")

    def test_basic_session_communication(self):
        pass
        # factory = HermesFactory(self._server_private_key,
        #                         self._server_public_key)
        # self.proto = factory.buildProtocol("localhost")
        # self.transport = proto_helpers.StringTransport()

        # pks = public_key_to_str(self._client_public_key)
        # ciphertext = asymmetric_encrypt_sign(pks,
        #                                      self._server_public_key,
        #                                      self._client_private_key)

        # self.proto.makeConnection(self.transport)
        # self.proto.dataReceived(ciphertext)
        # challenge = asymmetric_decrypt_verify(self.transport.value(),
        #                                       self._client_private_key,
        #                                       self._server_public_key)
        # self.transport.clear()
        # self.assertTrue(challenge)
        # self.assertEqual(challenge, self.proto.challenge)

        # self.proto.dataReceived(
        #     asymmetric_encrypt_sign(challenge,
        #                             self._server_public_key,
        #                             self._client_private_key))
        # session_key = asymmetric_decrypt_verify(self.transport.value(),
        #                                         self._client_private_key,
        #                                         self._server_public_key)
        # self.transport.clear()
        # self.assertTrue(session_key)
        # self.assertEqual(session_key, self.proto.session.key)

        # long_msg = b"""
        # All that is gold does not glitter
        # Not all those who wander are lost
        # The old that is strong does not whither
        # Deep roots are not touched by the frost

        # From the Ashes a fire shall be woken
        # A light from the shadow shall spring
        # Renewed be the blade that was broken
        # The crownless again shall be king.
        # """
        # ciphertext = symmetric_encrypt(long_msg, session_key)
        # self.proto.dataReceived(ciphertext)
        # self.assertEqual(long_msg, self.proto.session.message_buffer[-1])
