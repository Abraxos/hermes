from Crypto.Cipher import AES
from Crypto import Random
from rsa import verify, sign, encrypt, decrypt, PublicKey, PrivateKey, newkeys

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


def private_key_to_str(private_key):
    return PrivateKey.save_pkcs1(private_key, format='PEM')


def asymmetric_decrypt_verify(ciphertext, verify_key, decrypt_key):
    blocks = []
    for i in range(0, len(ciphertext), 512):
        blocks.append(decrypt(ciphertext[i:i + 512], decrypt_key))
    plaintext = b''.join(blocks)
    signature, plaintext = plaintext[:512], plaintext[512:]
    if verify(plaintext, signature, verify_key):
        return plaintext


def asymmetric_encrypt_sign(plaintext, sign_key, encrypt_key):
    signature = sign(plaintext, sign_key, 'SHA-512')
    plaintext = signature + plaintext
    blocks = []
    for i in range(0, len(plaintext), ENCRYPTION_BLOCK_SIZE):
        blocks.append(encrypt(plaintext[i:i + ENCRYPTION_BLOCK_SIZE], encrypt_key))
    ciphertext = b''.join(blocks)
    return ciphertext
