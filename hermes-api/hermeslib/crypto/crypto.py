from Crypto.Cipher import AES
from Crypto import Random
from Crypto.Hash import SHA256
from rsa import verify, sign, encrypt, decrypt, PublicKey, PrivateKey, newkeys, pkcs1


from ..utils.logging import *


ENCRYPTION_BLOCK_SIZE = 501


def gen_symmetric_key():
    return Random.get_random_bytes(32)


def symmetric_encrypt(msg, key):
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CFB, iv)
    return iv + cipher.encrypt(msg)


def symmetric_decrypt(ciphertext, key):
    cipher = AES.new(key, AES.MODE_CFB, ciphertext[:AES.block_size])
    return cipher.decrypt(ciphertext)[AES.block_size:]


def private_key_to_file(private_key, filepath):
    with open(filepath, 'wb+') as f:
        pk = PublicKey.save_pkcs1(private_key, format='PEM')
        f.write(pk)


def public_key_to_file(public_key, filepath):
    with open(filepath, 'wb+') as f:
        pk = PublicKey.save_pkcs1(public_key, format='PEM')
        f.write(pk)


def public_key_from_file(filepath):
    with open(filepath, 'rb') as f:
        pk = PublicKey.load_pkcs1(f.read(), format='PEM')
    return pk


def private_key_from_file(filepath):
    with open(filepath, 'rb') as f:
        pk = PrivateKey.load_pkcs1(f.read(), format='PEM')
    return pk


def private_key_from_str(s):
    return PrivateKey.load_pkcs1(s, format='PEM')


def public_key_to_str(public_key):
    return PublicKey.save_pkcs1(public_key, format='PEM')


def public_key_from_str(s):
    return PublicKey.load_pkcs1(s, format='PEM')


def public_key_sha256(public_key):
    return SHA256.new(public_key_to_str(public_key)).hexdigest()


def private_key_to_str(private_key):
    return PrivateKey.save_pkcs1(private_key, format='PEM')


def asymmetric_decrypt_verify(ciphertext, decrypt_key, verify_key):
    signature, plaintext, verified = None, None, False
    try:
        blocks = []
        for i in range(0, len(ciphertext), 512):
            blocks.append(decrypt(ciphertext[i:i + 512], decrypt_key))
        plaintext = b''.join(blocks)
        signature, plaintext = plaintext[:512], plaintext[512:]
        verified = verify(plaintext, signature, verify_key)
    except TypeError:
        log("Warning: TypeError has occurred during a decrypt/verify. \n\tCIPHERTEXT({0}): {1}".format(len(ciphertext),ciphertext))
    except pkcs1.DecryptionError:
        log("Warning: RSA Decryption Failed. \n\tCIPHERTEXT({0}): {1}".format(len(ciphertext), ciphertext))
    except pkcs1.VerificationError:
        log("WARNING: RSA Verification Failed. \n\tPLAINTEXT({0}): {1} \n\tSIGNATURE({2}): {3}".format(len(plaintext), plaintext, len(signature), signature))
    if signature and plaintext and verified:
        return plaintext

def asymmetric_decrypt(ciphertext, decrypt_key):
    plaintext, signature = None, None
    try:
        blocks = []
        for i in range(0, len(ciphertext), 512):
            blocks.append(decrypt(ciphertext[i:i + 512], decrypt_key))
        plaintext = b''.join(blocks)
        signature, plaintext = plaintext[:512], plaintext[512:]
    except TypeError:
        log("Warning: TypeError has occurred during a decrypt/verify. \n\tCIPHERTEXT({0}): {1}".format(len(ciphertext),ciphertext))
    except pkcs1.DecryptionError:
        log("Warning: RSA Decryption Failed. \n\tCIPHERTEXT({0}): {1}".format(len(ciphertext), ciphertext))
    if plaintext and signature:
        return plaintext, signature
    else:
        return None, None


def asymmetric_decrypt_verify_public_key(ciphertext, decrypt_key):
    plaintext, signature = asymmetric_decrypt(ciphertext, decrypt_key)
    if plaintext and signature:
        try:
            public_key = PublicKey.load_pkcs1(plaintext, format='PEM')
            verify(plaintext, signature, public_key)
        except pkcs1.VerificationError:
            log("WARNING: RSA Verification Failed. \n\tPLAINTEXT({0}): {1} \n\tSIGNATURE({2}): {3}".format(len(plaintext), plaintext, len(signature), signature))
            return None
        return plaintext


def _asymmetric_encrypt_sign(plaintext, encrypt_key, sign_key):
    signature = sign(plaintext, sign_key, 'SHA-512')
    plaintext = signature + plaintext
    blocks = []
    for i in range(0, len(plaintext), ENCRYPTION_BLOCK_SIZE):
        blocks.append(encrypt(plaintext[i:i + ENCRYPTION_BLOCK_SIZE], encrypt_key))
    ciphertext = b''.join(blocks)
    return ciphertext, signature


def asymmetric_encrypt_sign(plaintext, encrypt_key, sign_key):
    return _asymmetric_encrypt_sign(plaintext, encrypt_key, sign_key)[0]
