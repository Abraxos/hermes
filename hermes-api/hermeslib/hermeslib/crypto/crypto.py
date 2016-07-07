"""The cryptographic and message packing functions used by the Hermes-API"""
from os import urandom

from msgpack import packb
from msgpack import unpackb
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization import PublicFormat
from cryptography.hazmat.primitives.serialization import PrivateFormat
from cryptography.hazmat.primitives.serialization import NoEncryption
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption
from cryptography.hazmat.primitives.hashes import Hash
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.hazmat.primitives.asymmetric.padding import MGF1
from cryptography.hazmat.primitives.asymmetric.padding import OAEP
from cryptography.hazmat.primitives.asymmetric.padding import PSS
from cryptography.hazmat.primitives.padding import PKCS7

from ..utils.logging import log # pylint: disable=E0401

ENCRYPTION_BLOCK_SIZE = 470
DECRYPTION_BLOCK_SIZE = 512

def pack(**kwargs):
    """Pack message as an msgpack dictionary"""
    return packb(kwargs, use_bin_type=True)


def unpack(msg):
    """Unpack msgpack message"""
    return unpackb(msg, use_list=False, encoding='utf-8')


def gen_symmetric_key():
    """Generate symmetric key for AES256"""
    return urandom(32)


def symmetric_encrypt(msg, key):
    """Symmetrically encrypt a message and pack with IV using msgpack"""
    if msg and key:
        backend = default_backend()
        initialization_vector = urandom(16)
        cipher = Cipher(algorithms.AES(key),
                        modes.CBC(initialization_vector),
                        backend=backend)
        encryptor = cipher.encryptor()
        padder = PKCS7(128).padder()
        msg = padder.update(msg) + padder.finalize()
        ciphertext = encryptor.update(msg) + encryptor.finalize()
        return pack(iv=initialization_vector, ct=ciphertext)


def symmetric_decrypt(msg, key):
    """Unpack 'iv' and 'ct' (ciphertext) values and symmetrically decrypt"""
    if msg and key:
        msg = unpack(msg)
        backend = default_backend()
        initialization_vector = msg['iv']
        ciphertext = msg['ct']
        cipher = Cipher(algorithms.AES(key),
                        modes.CBC(initialization_vector),
                        backend=backend)
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        return plaintext


def private_key_to_file(private_key, filepath, password=None):
    """Save a PEM-formatted private key to a file and optionally encrypt"""
    with open(filepath, 'wb+') as privkey_file:
        pem = private_key_to_str(private_key, password)
        privkey_file.write(pem)


def public_key_to_file(public_key, filepath):
    """Save a PEM-formatted public key to a file"""
    with open(filepath, 'wb+') as pubkey_file:
        pem = public_key_to_str(public_key)
        pubkey_file.write(pem)


def public_key_from_file(filepath):
    """Load a PEM-formatted public key from a file"""
    with open(filepath, 'rb') as pubkey_file:
        public_key = public_key_from_str(pubkey_file.read())
    return public_key


def private_key_from_file(filepath, password=None):
    """Load a PEM-formatted private key from a file and optionally decrypt"""
    with open(filepath, 'rb') as privkey_file:
        private_key = private_key_from_str(privkey_file.read(), password)
    return private_key


def private_key_from_str(private_key_str, password=None):
    """Load a PEM-formatted private key from a string and optionally decrypt"""
    if isinstance(private_key_str, str):
        private_key_str = bytes(private_key_str, encoding='utf-8')
    return load_pem_private_key(private_key_str,
                                password=password,
                                backend=default_backend())



def public_key_to_str(public_key):
    """Write a PEM-formatted public key to a string"""
    return public_key.public_bytes(encoding=Encoding.PEM,
                                   format=PublicFormat.SubjectPublicKeyInfo)


def public_key_from_str(public_key_str):
    """Load a PEM-formatted public key from a string"""
    if isinstance(public_key_str, str):
        public_key_str = bytes(public_key_str, encoding='utf-8')
    return load_pem_public_key(public_key_str, default_backend())


def sha256(message):
    """Generates a SHA256 hash of a message"""
    if isinstance(message, str):
        message = bytes(message, encoding='utf-8')
    elif isinstance(message, bytearray):
        message = bytes(message)
    digest = Hash(SHA256(), backend=default_backend())
    digest.update(message)
    return digest.finalize()


def public_key_sha256(public_key):
    """Generates a SHA256 of a public key after PEM encoding"""
    return sha256(public_key_to_str(public_key))


def private_key_to_str(private_key, password=None):
    """Load a PEM-formatted private key from a string and optionally decrypt"""
    if not password:
        return private_key.private_bytes(encoding=Encoding.PEM,
                                         format=PrivateFormat.PKCS8,
                                         encryption_algorithm=NoEncryption())
    else:
        return private_key.private_bytes(encoding=Encoding.PEM,
                                         format=PrivateFormat.PKCS8,
                                         encryption_algorithm=BestAvailableEncryption(password))


def asymmetric_decrypt_verify(msg, decrypt_key, verify_key):
    """Asymmetrically decrypts and verifies a packed and signed  message"""
    msg = unpack(asymmetric_decrypt(msg, decrypt_key))
    signature, msg = msg['signature'], msg['msg']
    if not asymmetric_verify(signature, msg, verify_key):
        log("WARNING: RSA Verification Failed. \n\tPLAINTEXT({0}): {1} \n\t"
            "SIGNATURE({2}): {3}".format(len(msg), msg,
                                         len(signature), signature))
    else:
        return msg


def asymmetric_verify(signature, plaintext, public_key):
    """Verifies an asymmetrically signed message"""
    try:
        if isinstance(plaintext, str):
            plaintext = bytes(plaintext, encoding='utf-8')
        elif isinstance(plaintext, bytearray):
            plaintext = bytes(plaintext)
        public_key.verify(signature,
                          plaintext,
                          PSS(mgf=MGF1(SHA256()),
                              salt_length=PSS.MAX_LENGTH),
                          SHA256())
        return True
    except InvalidSignature:
        return False


def decrypt_pubkey(ciphertext, decrypt_key):
    """Asymmetrically decrypts and verifies a packed and self-signed pubkey"""
    msg = unpack(asymmetric_decrypt(ciphertext, decrypt_key))
    signature, pubkey = msg['signature'], msg['pubkey']
    public_key = public_key_from_str(pubkey)
    if not asymmetric_verify(pubkey, signature, public_key):
        log("WARNING: RSA Verification Failed\n\tPLAINTEXT({0}): {1} \n\t"
            "SIGNATURE({2}): {3}".format(len(pubkey),
                                         pubkey,
                                         len(signature),
                                         signature))
    return public_key


def encrypt_pubkey(public_key, encrypt_key):
    """Asymmetrically sign and encrypt a public key"""
    public_key_str = public_key_to_str(public_key)
    signature = asymmetric_sign(public_key_str, public_key)
    msg = pack(signature=signature, pubkey=public_key_str)
    return asymmetric_encrypt(msg, encrypt_key)


def _asymmetric_encrypt_sign(plaintext, encrypt_key, sign_key):
    """Asymmetrically encrypts, signs, and msg-packs a message"""
    signature = asymmetric_sign(plaintext, sign_key)
    msg = pack(msg=plaintext, signature=signature)
    ciphertext = asymmetric_encrypt(msg, encrypt_key)
    return ciphertext, signature

def asymmetric_encrypt(msg, public_key):
    """Asymmmetrically encrypts a message"""
    size = ENCRYPTION_BLOCK_SIZE
    blocks = [msg[i:i+size] for i in range(0, len(msg), size)]
    ciphertext = []
    for block in blocks:
        ciphertext.append(public_key.encrypt(block,
                                             OAEP(mgf=MGF1(algorithm=SHA1()),
                                                  algorithm=SHA1(),
                                                  label=None)))
    return b''.join(ciphertext)


def asymmetric_decrypt(ciphertext, private_key):
    """Asymmetrically decrypt a message"""
    size = DECRYPTION_BLOCK_SIZE
    blocks = [ciphertext[i:i+size] for i in range(0, len(ciphertext), size)]
    plaintext = []
    for block in blocks:
        plaintext.append(private_key.decrypt(block,
                                             OAEP(mgf=MGF1(algorithm=SHA1()),
                                                  algorithm=SHA1(),
                                                  label=None)))
    return b''.join(plaintext)

def asymmetric_sign(msg, sign_key):
    """Asymmetrically signs a message"""
    signer = sign_key.signer(PSS(mgf=MGF1(SHA256()),
                                 salt_length=PSS.MAX_LENGTH),
                             SHA256())
    if isinstance(msg, str):
        msg = bytes(msg, encoding='utf-8')
    elif isinstance(msg, bytearray):
        msg = bytes(msg)
    signer.update(msg)
    return signer.finalize()


def asymmetric_encrypt_sign(plaintext, encrypt_key, sign_key):
    """Asymmetrically encrypts, signs, and msg-packs a message"""
    return _asymmetric_encrypt_sign(plaintext, encrypt_key, sign_key)[0]
