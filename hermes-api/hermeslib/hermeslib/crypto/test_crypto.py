"""Unittests for the crypto module of the hermes-API"""
import unittest
import filecmp
from os import remove
from os import urandom
from hermeslib.crypto.crypto import unpack # pylint: disable=E0401
from hermeslib.crypto.crypto import gen_symmetric_key # pylint: disable=E0401
from hermeslib.crypto.crypto import symmetric_encrypt # pylint: disable=E0401
from hermeslib.crypto.crypto import symmetric_decrypt # pylint: disable=E0401
from hermeslib.crypto.crypto import private_key_from_str # pylint: disable=E0401
from hermeslib.crypto.crypto import public_key_from_str # pylint: disable=E0401
from hermeslib.crypto.crypto import private_key_to_str # pylint: disable=E0401
from hermeslib.crypto.crypto import public_key_to_str # pylint: disable=E0401
from hermeslib.crypto.crypto import private_key_to_file # pylint: disable=E0401
from hermeslib.crypto.crypto import public_key_to_file # pylint: disable=E0401
# from hermeslib.crypto.crypto import asymmetric_encrypt # pylint: disable=E0401
from hermeslib.crypto.crypto import asymmetric_decrypt # pylint: disable=E0401
from hermeslib.crypto.crypto import asymmetric_encrypt_sign # pylint: disable=E0401
from hermeslib.crypto.crypto import asymmetric_decrypt_verify # pylint: disable=E0401
# from hermeslib.crypto.crypto import asymmetric_sign # pylint: disable=E0401
from hermeslib.crypto.crypto import asymmetric_verify # pylint: disable=E0401
from hermeslib.crypto.crypto import public_key_sha256 # pylint: disable=E0401
from hermeslib.crypto.crypto import sha256 # pylint: disable=E0401
from hermeslib.crypto.crypto import _asymmetric_encrypt_sign # pylint: disable=E0401
from hermeslib.crypto.testing_keys import CLIENT_1_PRIV_KEY, CLIENT_1_PUB_KEY # pylint: disable=E0401
from hermeslib.crypto.testing_keys import SERVER_PRIV_KEY, SERVER_PUB_KEY # pylint: disable=E0401

class CryptoTestCase(unittest.TestCase):
    """Unittests for the crypto module of the hermes-API"""
    _server_priv_key1 = private_key_from_str(SERVER_PRIV_KEY)
    _server_pub_key1 = public_key_from_str(SERVER_PUB_KEY)
    _client_priv_key2 = private_key_from_str(CLIENT_1_PRIV_KEY)
    _client_pub_key2 = public_key_from_str(CLIENT_1_PUB_KEY)
    # Tests integration with the Cryptographic library

    def test_symmetric_key_generation(self):
        """Tests generating symmetric keys"""
        key = gen_symmetric_key()
        self.assertEqual(len(key), 32)

    def test_symmetric_enc_dec(self):
        """Tests symmetric encryption/decryption"""
        msg = b'''All that is gold does not glitter, not all those who wander
         are lost, the old that is strong does not whither, deep roots are
         not touched by the frost. From the ashes a fire shall be woken, a
         light from the shadow shall spring, renewed be the blade that was
         broken, the crownless again shall be king. All that is gold does not
          glitter, not all those who wander are lost, the old that is strong
          does not whither, deep roots are not touched by the frost. From
          the ashes a fire shall be woken, a light from the shadow shall
          spring, renewed be the blade that was broken, the crownless again
          shall be king.'''
        key = gen_symmetric_key()
        ciphertext = symmetric_encrypt(msg, key)
        self.assertNotEqual(msg, ciphertext)
        deciphered = symmetric_decrypt(ciphertext, key)
        self.assertEqual(msg, deciphered)

    def test_asymmetric_enc_dec(self):
        """Tests asymmetric encryption/decryption"""
        msg = b'''All that is gold does not glitter, not all those who wander
         are lost, the old that is strong does not whither, deep roots are
         not touched by the frost. From the ashes a fire shall be woken, a
         light from the shadow shall spring, renewed be the blade that was
         broken, the crownless again shall be king. All that is gold does not
          glitter, not all those who wander are lost, the old that is strong
          does not whither, deep roots are not touched by the frost. From
          the ashes a fire shall be woken, a light from the shadow shall
          spring, renewed be the blade that was broken, the crownless again
          shall be king.'''
        ciphertext = asymmetric_encrypt_sign(
            msg, self._client_pub_key2, self._server_priv_key1)
        self.assertNotEqual(msg, ciphertext)
        deciphered = asymmetric_decrypt_verify(
            ciphertext, self._client_priv_key2, self._server_pub_key1)
        self.assertEqual(msg, deciphered)

    def test_asymmetric_import_export(self):
        """Tests asymmetric key import/export"""
        # test public keys
        test_pub_keys = [self._server_pub_key1, self._client_pub_key2]
        for key in test_pub_keys:
            pub_key_s = public_key_to_str(key)
            pub_prefix = b'-----BEGIN PUBLIC KEY-----'
            self.assertEqual(pub_key_s[:len(pub_prefix)], pub_prefix)
            pub_suffix = b'-----END PUBLIC KEY-----\n'
            self.assertEqual(pub_key_s[len(pub_key_s) - len(pub_suffix):],
                             pub_suffix)
            # make sure that the reversals work as intended
            self.assertEqual(public_key_to_str(public_key_from_str(pub_key_s)),
                             pub_key_s)

        # now test private keys
        test_priv_keys = [self._server_priv_key1, self._client_priv_key2]
        for key in test_priv_keys:
            priv_key_s = private_key_to_str(key)
            priv_prefix = b'-----BEGIN PRIVATE KEY-----'
            self.assertEqual(priv_key_s[:len(priv_prefix)], priv_prefix)
            priv_suffix = b'-----END PRIVATE KEY-----\n'
            self.assertEqual(priv_key_s[len(priv_key_s) - len(priv_suffix):],
                             priv_suffix)
            self.assertEqual(
                private_key_to_str(private_key_from_str(priv_key_s)),
                priv_key_s)

    def test_asymmetric_key_encryption(self):
        """Tests asymmetric key encryption"""
        key = gen_symmetric_key()

        ciphertext = asymmetric_encrypt_sign(
            key, self._client_pub_key2, self._server_priv_key1)
        self.assertNotEqual(key, ciphertext)
        deciphered = asymmetric_decrypt_verify(
            ciphertext, self._client_priv_key2, self._server_pub_key1)
        self.assertEqual(key, deciphered)

    def test_gen_random(self):
        """Tests random-value generation"""
        samples = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
        for sample_num in samples:
            self.assertEqual(sample_num, len(urandom(sample_num)))

    def test_private_key_to_file(self):
        """ Resulting files from writing same key to both should be the same
        """
        priv_keys = [self._server_priv_key1, self._client_priv_key2]
        path1 = 'test_priv_key_to_file1.pem'
        path2 = 'test_priv_key_to_file2.pem'
        for key in priv_keys:
            private_key_to_file(key, path1)
            private_key_to_file(key, path2)
            self.assertTrue(filecmp.cmp(path1, path2))

            # Even when one of them is overwritten
            private_key_to_file(key, path2)
            self.assertTrue(filecmp.cmp(path1, path2))
        remove(path1)
        remove(path2)

    def test_public_key_to_file(self):
        """Tests public key file-export"""
        pub_keys = [self._server_pub_key1, self._client_pub_key2]
        path1 = 'test_pub_key_to_file1.pem'
        path2 = 'test_pub_key_to_file2.pem'
        for key in pub_keys:
            public_key_to_file(key, path1)
            public_key_to_file(key, path2)
            self.assertTrue(filecmp.cmp(path1, path2))

            public_key_to_file(key, path2)
            self.assertTrue(filecmp.cmp(path1, path2))
        remove(path1)
        remove(path2)

    def test_sha(self):
        """Tests SHA256 hashing"""
        self.assertEqual(len(public_key_sha256(self._server_pub_key1)), 32)
        self.assertEqual(len(public_key_sha256(self._client_pub_key2)), 32)
        self.assertEqual(len(sha256(b'salutations world')), 32)
        self.assertEqual(
            len(sha256(bytearray(b'''Like most North Americans of his
                       generation, Hal tends to know way less about why he feels
                       certain ways about the objects and pursuits he's devoted
                       to than he does about the objects and pursuits
                       themselves. It's hard to say for sure whether this is
                       even exceptionally bad, this tendency.'''))), 32)

    def test_asymmetric_sign(self):
        """Tests asymmetric signatures"""
        # TODO: test asymmetric_sign
        pass

    def test_asymmetric_verify(self):
        """Tests asymmetric signature verification"""
        pub_keys = [self._server_pub_key1, self._client_pub_key2]
        priv_keys = [self._server_priv_key1, self._client_priv_key2]
        original_plaintext = b'''I do things like get in a taxi and say, \'The
                             library, and step on it.\''''

        # The enumeration assumes both key lists are of same size and the index
        # of one list holds a key that corresponds to the same index of the
        # other list.
        for i, pub_key in enumerate(pub_keys):
            ciphertext, original_signature = _asymmetric_encrypt_sign(
                original_plaintext, pub_key, priv_keys[i])
            msg = unpack(asymmetric_decrypt(ciphertext, priv_keys[i]))
            plaintext, signature = msg['msg'], msg['signature']
            self.assertEqual(original_plaintext, plaintext)
            self.assertEqual(original_signature, signature)
            self.assertTrue(asymmetric_verify(signature, plaintext, pub_key))

            for other_priv_key in priv_keys:
                if other_priv_key != priv_keys[i]:
                    # making sure other private keys don't work if they are not
                    # equal
                    other_ciphtext, other_sig = _asymmetric_encrypt_sign(
                        original_plaintext, pub_key, other_priv_key)
                    self.assertNotEqual(other_ciphtext, ciphertext)
                    self.assertNotEqual(other_sig, signature)
                    for other_pub_key in pub_keys:
                        if other_pub_key != pub_key:
                            self.assertTrue(asymmetric_verify(
                                other_sig, original_plaintext, other_pub_key))
                            self.assertFalse(asymmetric_verify(
                                other_sig, original_plaintext, pub_key))
                            self.assertFalse(asymmetric_verify(
                                signature, original_plaintext, other_pub_key))


if __name__ == '__main__':
    unittest.main()
