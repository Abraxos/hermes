import unittest
import filecmp
# from rsa import verify, sign, encrypt, decrypt, PublicKey, PrivateKey, newkeys
from hermeslib.crypto import crypto
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
            # make sure that the reversals work as intended
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

    def test_sha(self):
        self.assertEqual(len(public_key_sha256(self._pub_key1)), 64)
        self.assertEqual(len(public_key_sha256(self._pub_key2)), 64)
        self.assertEqual(len(sha256(bytearray(b'salutations world'))), 64)
        self.assertEqual(
            len(sha256(bytearray(b'''Like most North Americans of his generation, Hal
                       tends to know way less about why he feels certain ways
                       about the objects and pursuits he's devoted to than he
                       does about the objects and pursuits themselves. It's
                       hard to say for sure whether this is even exceptionally
                       bad, this tendency.'''))), 64)

    def test_asymmetric_sign(self):
        # TODO: test asymmetric_sign
        pass

    def test_asymmetric_verify(self):
        pub_keys = [self._pub_key1, self._pub_key2]
        priv_keys = [self._priv_key1, self._priv_key2]
        original_plaintext = b'''I do things like get in a taxi and say, \'The
                             library, and step on it.\''''

        # The enumeration assumes both key lists are of same size and the index
        # of one list holds a key that corresponds to the same index of the
        # other list.
        for i, pub_key in enumerate(pub_keys):
            priv_key = priv_keys[i]
            ciphertext, original_signature = crypto._asymmetric_encrypt_sign(
                original_plaintext, pub_key, priv_key)
            plaintext, signature = asymmetric_decrypt(ciphertext, priv_key)
            self.assertEqual(original_plaintext, plaintext)
            self.assertEqual(original_signature, signature)
            self.assertTrue(asymmetric_verify(signature, plaintext, pub_key))

            for other_priv_key in priv_keys:
                if other_priv_key != priv_key:
                    # making sure other private keys don't work if they are not
                    # equal
                    other_ciphtext, other_sig = crypto._asymmetric_encrypt_sign(
                        original_plaintext, pub_key, other_priv_key)
                    self.assertNotEqual(other_ciphtext, ciphertext)
                    self.assertNotEqual(other_sig, signature)

                    # TODO (Henry, @Eugene):
                    # The below assertion CHECKS OUT, but I have a problem
                    # understanding why. Basically, after asymmetrically encrypting
                    # and signing a plaintext with non-matching pub and priv
                    # keys, the signature received (other_sig) seems to be a
                    # valid one. Because, in below, it is then passed into
                    # the verify function along with the non-matching private
                    # key and the verification checks out as True.
                    # self.assertTrue(asymmetric_verify(
                    #     other_sig, original_plaintext, other_priv_key))

                    self.assertFalse(asymmetric_verify(
                        other_sig, original_plaintext, priv_key))
                    self.assertFalse(asymmetric_verify(
                        signature, original_plaintext, other_priv_key))


if __name__ == '__main__':
    unittest.main()
