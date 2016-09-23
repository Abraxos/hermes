"""The cryptographic and message packing functions used by the Hermes-API"""
from cryptography.hazmat.backends import default_backend # pylint: disable=E0401
from cryptography.hazmat.primitives.hashes import Hash # pylint: disable=E0401
from cryptography.hazmat.primitives.hashes import SHA256 # pylint: disable=E0401
from bcrypt import hashpw, gensalt # pylint: disable=E0401

def sha256(message):
    """Generates a SHA256 hash of a message"""
    if isinstance(message, str):
        message = bytes(message, encoding='utf-8')
    elif isinstance(message, bytearray):
        message = bytes(message)
    digest = Hash(SHA256(), backend=default_backend())
    digest.update(message)
    return digest.finalize()

def hash_salt(password):
    return hashpw(password, gensalt(16))

def password_verified(password, hashed):
    return hashpw(password, hashed) == hashed
