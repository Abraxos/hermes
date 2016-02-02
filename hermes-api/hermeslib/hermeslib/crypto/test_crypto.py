import unittest
import filecmp
# from rsa import verify, sign, encrypt, decrypt, PublicKey, PrivateKey, newkeys
from hermeslib.crypto.crypto import *


class CryptoTestCase(unittest.TestCase):
    _priv_key1 = private_key_from_file(
        'hermeslib/tests/testing_data/server_test_key.pem')
    _pub_key1 = public_key_from_file(
        'hermeslib/tests/testing_data/server_test_pub_key.pem')
    _priv_key2 = private_key_from_file(
        'hermeslib/tests/testing_data/client1_test_key.pem')
    _pub_key2 = public_key_from_file(
        'hermeslib/tests/testing_data/client1_test_pub_key.pem')
    # Tests integration with the Cryptographic library

    def test_symmetric_key_generation(self):
        key = gen_symmetric_key()
        self.assertEqual(len(key), 32)

    def test_symmetric_encryption_decryption(self):
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

    def test_asymmetric_encryption_decryption(self):
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
            msg, self._pub_key2, self._priv_key1)
        self.assertNotEqual(msg, ciphertext)
        deciphered = asymmetric_decrypt_verify(
            ciphertext, self._priv_key2, self._pub_key1)
        self.assertEqual(msg, deciphered)

    def test_asymmetric_import_export(self):
        # test public keys
        test_pub_keys = [self._pub_key1, self._pub_key2]
        for key in test_pub_keys:
            pub_key_str = public_key_to_str(key)
            self.assertEqual(pub_key_str[:30], b'-----BEGIN RSA PUBLIC KEY-----')
            pub_suffix = b'-----END RSA PUBLIC KEY-----\n'
            self.assertEqual(pub_key_str[len(pub_key_str) - len(pub_suffix):],
                             pub_suffix)
            # make sure that key->string functions work as intended
            self.assertEqual(public_key_to_str(public_key_from_str(pub_key_str)),
                             pub_key_str)

        # now test private keys
        test_priv_keys = [self._priv_key1, self._priv_key2]
        for key in test_priv_keys:
            rsa_key_str = private_key_to_str(key)
            self.assertEqual(rsa_key_str[:31],
                             b'-----BEGIN RSA PRIVATE KEY-----')
            rsa_suffix = b'-----END RSA PRIVATE KEY-----\n'
            self.assertEqual(rsa_key_str[len(rsa_key_str) - len(rsa_suffix):],
                             rsa_suffix)
            self.assertEqual(
                private_key_to_str(private_key_from_str(rsa_key_str)),
                rsa_key_str)

    def test_asymmetric_key_encryption(self):
        key = gen_symmetric_key()

        ciphertext = asymmetric_encrypt_sign(
            key, self._pub_key2, self._priv_key1)
        self.assertNotEqual(key, ciphertext)
        deciphered = asymmetric_decrypt_verify(
            ciphertext, self._priv_key2, self._pub_key1)
        self.assertEqual(key, deciphered)

    def test_gen_random(self):
        samples = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
        for sample_num in samples:
            self.assertEqual(sample_num, len(gen_random(sample_num)))

    def test_private_key_to_file(self):
        """ Resulting files from writing same key to both should be the same
        """
        priv_keys = [self._priv_key1, self._priv_key2]
        path1 = 'hermeslib/tests/testing_data/test_priv_key_to_file1.pem'
        path2 = 'hermeslib/tests/testing_data/test_priv_key_to_file2.pem'
        for key in priv_keys:
            private_key_to_file(key, path1)
            private_key_to_file(key, path2)
            self.assertTrue(filecmp.cmp(path1, path2))

            # Even when one of them is overwritten
            private_key_to_file(key, path2)
            self.assertTrue(filecmp.cmp(path1, path2))

    def test_public_key_to_file(self):
        pub_keys = [self._pub_key1, self._pub_key2]
        path1 = 'hermeslib/tests/testing_data/test_pub_key_to_file1.pem'
        path2 = 'hermeslib/tests/testing_data/test_pub_key_to_file2.pem'
        for key in pub_keys:
            public_key_to_file(key, path1)
            public_key_to_file(key, path2)
            self.assertTrue(filecmp.cmp(path1, path2))

            public_key_to_file(key, path2)
            self.assertTrue(filecmp.cmp(path1, path2))


if __name__ == '__main__':
    unittest.main()
