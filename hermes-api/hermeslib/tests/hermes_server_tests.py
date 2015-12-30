from twisted.test import proto_helpers
from twisted.trial import unittest


from hermeslib.server.hermes_server import *


class MyTestCase(unittest.TestCase):
    _server_private_key = private_key_from_file('testing_data/server_test_key.pem')
    _server_public_key = public_key_from_file('testing_data/server_test_key_pub.pem')
    _client_private_key = private_key_from_file('testing_data/client_test_key.pem')
    _client_public_key = public_key_from_file('testing_data/client_test_key_pub.pem')

    def test_connection_made(self):
        factory = HermesFactory(self._server_private_key, self._server_public_key)
        self.proto = factory.buildProtocol("localhost")
        self.transport = proto_helpers.StringTransport()

        self.proto.makeConnection(self.transport)
        self.proto.dataReceived(b'testing...\n')
        # print(self.transport.value())
        self.assertEqual(self.transport.value(), b'Initial failure.')

    def test_receiving_initial_client_public_key(self):
        factory = HermesFactory(self._server_private_key,
                                self._server_public_key)
        self.proto = factory.buildProtocol("localhost")
        self.transport = proto_helpers.StringTransport()

        pks = public_key_to_str(self._client_public_key)
        ciphertext = asymmetric_encrypt_sign(pks,
                                             self._server_public_key,
                                             self._client_private_key)
        pks2, pks2s = asymmetric_decrypt(ciphertext, self._server_private_key)
        self.assertEqual(pks, pks2)

        self.proto.makeConnection(self.transport)
        self.proto.dataReceived(ciphertext)
        server_reply = asymmetric_decrypt_verify(self.transport.value(),
                                                 self._client_private_key,
                                                 self._server_public_key)
        self.assertTrue(server_reply)
        self.assertEqual(server_reply, self.proto.challenge)

    def test_challenge_verification(self):
        factory = HermesFactory(self._server_private_key,
                                self._server_public_key)
        self.proto = factory.buildProtocol("localhost")
        self.transport = proto_helpers.StringTransport()

        pks = public_key_to_str(self._client_public_key)
        ciphertext = asymmetric_encrypt_sign(pks,
                                             self._server_public_key,
                                             self._client_private_key)

        self.proto.makeConnection(self.transport)
        self.proto.dataReceived(ciphertext)
        challenge = asymmetric_decrypt_verify(self.transport.value(),
                                              self._client_private_key,
                                              self._server_public_key)
        self.transport.clear()
        self.assertTrue(challenge)
        self.assertEqual(challenge, self.proto.challenge)

        self.proto.dataReceived(asymmetric_encrypt_sign(challenge,
                                                        self._server_public_key,
                                                        self._client_private_key))
        server_reply = asymmetric_decrypt_verify(self.transport.value(),
                                                 self._client_private_key,
                                                 self._server_public_key)
        self.transport.clear()
        self.assertTrue(server_reply)
        self.assertEqual(server_reply, self.proto.session.key)

    def test_challenge_verification_failure(self):
        factory = HermesFactory(self._server_private_key,
                                self._server_public_key)
        self.proto = factory.buildProtocol("localhost")
        self.transport = proto_helpers.StringTransport()

        pks = public_key_to_str(self._client_public_key)
        ciphertext = asymmetric_encrypt_sign(pks,
                                             self._server_public_key,
                                             self._client_private_key)

        self.proto.makeConnection(self.transport)
        self.proto.dataReceived(ciphertext)
        challenge = asymmetric_decrypt_verify(self.transport.value(),
                                              self._client_private_key,
                                              self._server_public_key)
        self.transport.clear()
        self.assertTrue(challenge)
        self.assertEqual(challenge, self.proto.challenge)

        self.proto.dataReceived(asymmetric_encrypt_sign(challenge,
                                                        self._server_public_key,
                                                        self._server_private_key))
        server_reply = self.transport.value()
        self.assertEqual(server_reply, b"Challenge failure.")

    def test_basic_session_communication(self):
        factory = HermesFactory(self._server_private_key,
                                self._server_public_key)
        self.proto = factory.buildProtocol("localhost")
        self.transport = proto_helpers.StringTransport()

        pks = public_key_to_str(self._client_public_key)
        ciphertext = asymmetric_encrypt_sign(pks,
                                             self._server_public_key,
                                             self._client_private_key)

        self.proto.makeConnection(self.transport)
        self.proto.dataReceived(ciphertext)
        challenge = asymmetric_decrypt_verify(self.transport.value(),
                                              self._client_private_key,
                                              self._server_public_key)
        self.transport.clear()
        self.assertTrue(challenge)
        self.assertEqual(challenge, self.proto.challenge)

        self.proto.dataReceived(asymmetric_encrypt_sign(challenge,
                                                        self._server_public_key,
                                                        self._client_private_key))
        session_key = asymmetric_decrypt_verify(self.transport.value(),
                                                 self._client_private_key,
                                                 self._server_public_key)
        self.transport.clear()
        self.assertTrue(session_key)
        self.assertEqual(session_key, self.proto.session.key)

        long_msg = b"""
        All that is gold does not glitter
        Not all those who wander are lost
        The old that is strong does not whither
        Deep roots are not touched by the frost

        From the Ashes a fire shall be woken
        A light from the shadow shall spring
        Renewed be the blade that was broken
        The crownless again shall be king.
        """
        ciphertext = symmetric_encrypt(long_msg, session_key)
        self.proto.dataReceived(ciphertext)
        self.assertEqual(long_msg, self.proto.session.message_buffer[-1])


if __name__ == '__main__':
    t = MyTestCase()
    t.test_connection_made()
    t.test_receiving_initial_client_public_key()
    t.test_challenge_verification()
    t.test_challenge_verification_failure()
    t.test_basic_session_communication()
