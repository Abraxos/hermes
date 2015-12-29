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


if __name__ == '__main__':
    t = MyTestCase()
    t.test_connection_made()
    t.test_receiving_initial_client_public_key()
    t.test_challenge_verification()
    t.test_challenge_verification_failure()
