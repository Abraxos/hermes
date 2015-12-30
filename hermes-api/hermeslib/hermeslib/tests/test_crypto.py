import unittest
# from rsa import verify, sign, encrypt, decrypt, PublicKey, PrivateKey, newkeys
from ..crypto.crypto import *


class CryptoTestCase(unittest.TestCase):
    # Tests integration with the Cryptographic library

    def test_symmetric_key_generation(self):
        key = gen_symmetric_key()
        self.assertEqual(len(key), 32)

    def test_symmetric_encryption_decryption(self):
        msg = b'All that is gold does not glitter, not all those who wander are lost, the old that is strong does not whither, deep roots are not touched by the frost. From the ashes a fire shall be woken, a light from the shadow shall spring, renewed be the blade that was broken, the crownless again shall be king. All that is gold does not glitter, not all those who wander are lost, the old that is strong does not whither, deep roots are not touched by the frost. From the ashes a fire shall be woken, a light from the shadow shall spring, renewed be the blade that was broken, the crownless again shall be king.'
        key = gen_symmetric_key()
        ciphertext = symmetric_encrypt(msg, key)
        self.assertNotEqual(msg, ciphertext)
        deciphered = symmetric_decrypt(ciphertext, key)
        self.assertEqual(msg, deciphered)

    def test_asymmetric_encryption_decryption(self):
        msg = b'All that is gold does not glitter, not all those who wander are lost, the old that is strong does not whither, deep roots are not touched by the frost. From the ashes a fire shall be woken, a light from the shadow shall spring, renewed be the blade that was broken, the crownless again shall be king. All that is gold does not glitter, not all those who wander are lost, the old that is strong does not whither, deep roots are not touched by the frost. From the ashes a fire shall be woken, a light from the shadow shall spring, renewed be the blade that was broken, the crownless again shall be king.'
        priv_key1 = private_key_from_file('hermeslib/tests/testing_data/server_test_key.pem')
        pub_key1 = public_key_from_file('hermeslib/tests/testing_data/server_test_key_pub.pem')
        priv_key2 = private_key_from_file('hermeslib/tests/testing_data/client_test_key.pem')
        pub_key2 = public_key_from_file('hermeslib/tests/testing_data/client_test_key_pub.pem')

        ciphertext = asymmetric_encrypt_sign(msg, pub_key2, priv_key1)
        self.assertNotEqual(msg, ciphertext)
        deciphered = asymmetric_decrypt_verify(ciphertext, priv_key2, pub_key1)
        self.assertEqual(msg, deciphered)

    def test_asymmetric_import_export(self):
        # (pub_key, priv_key) = newkeys(4096, poolsize=4)
        priv_key = private_key_from_file('hermeslib/tests/testing_data/server_test_key.pem')
        pub_key = public_key_from_file('hermeslib/tests/testing_data/server_test_key_pub.pem')
        rsa_key_str = private_key_to_str(priv_key)
        pub_key_str = public_key_to_str(pub_key)
        self.assertEqual(pub_key_str[:30], b'-----BEGIN RSA PUBLIC KEY-----')
        self.assertEqual(rsa_key_str[:31], b'-----BEGIN RSA PRIVATE KEY-----')
        priv_key = private_key_from_str(rsa_key_str)
        pub_key = public_key_from_str(pub_key_str)

    def test_asymmetric_key_encryption(self):
        priv_key1 = private_key_from_file('hermeslib/tests/testing_data/server_test_key.pem')
        pub_key1 = public_key_from_file('hermeslib/tests/testing_data/server_test_key_pub.pem')
        priv_key2 = private_key_from_file('hermeslib/tests/testing_data/client_test_key.pem')
        pub_key2 = public_key_from_file('hermeslib/tests/testing_data/client_test_key_pub.pem')

        key = gen_symmetric_key()

        ciphertext = asymmetric_encrypt_sign(key, pub_key2, priv_key1)
        self.assertNotEqual(key, ciphertext)
        deciphered = asymmetric_decrypt_verify(ciphertext, priv_key2, pub_key1)
        self.assertEqual(key, deciphered)


if __name__ == '__main__':
    unittest.main()
