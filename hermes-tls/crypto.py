"""The cryptographic and message packing functions used by the Hermes-API"""
from os import urandom
from datetime import datetime, timedelta
from cryptography.hazmat.backends import default_backend # pylint: disable=E0401
from cryptography.hazmat.primitives.hashes import Hash # pylint: disable=E0401
from cryptography.hazmat.primitives.hashes import SHA256 # pylint: disable=E0401
from bcrypt import hashpw, gensalt # pylint: disable=E0401
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
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.hashes import Hash
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.hazmat.primitives.asymmetric.padding import MGF1
from cryptography.hazmat.primitives.asymmetric.padding import OAEP
from cryptography.hazmat.primitives.asymmetric.padding import PSS
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509 import CertificateSigningRequest
from cryptography import x509
from cryptography.x509.oid import NameOID
from utils import pack, unpack, pack_values, accepts

SERVER_COUNTRY_NAME = u'US'
SERVER_STATE = u'Denial'
SERVER_LOCALITY = u'Springfield'
SERVER_ORGANIZATION = u'Hermes Messenger Developers'
SERVER_COMMON_NAME = u'Hermes Test Server'

CLIENT_COUNTRY_NAME = u'US'
CLIENT_STATE = u'Denial'
CLIENT_LOCALITY = u'Springfield'
CLIENT_ORGANIZATION = u'Hermes Messenger Developers'

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

def gen_symmetric_key():
    """Generate symmetric key for AES256"""
    return urandom(32)

def generate_asymmetric_key():
    key = rsa.generate_private_key(public_exponent=65537, key_size=4096,
                                   backend=default_backend())
    return key

def get_issuer_name():
    issuer = x509.Name([x509.NameAttribute(NameOID.COUNTRY_NAME,
                                           SERVER_COUNTRY_NAME),
                        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME,
                                           SERVER_STATE),
                        x509.NameAttribute(NameOID.LOCALITY_NAME,
                                           SERVER_LOCALITY),
                        x509.NameAttribute(NameOID.ORGANIZATION_NAME,
                                           SERVER_ORGANIZATION),
                        x509.NameAttribute(NameOID.COMMON_NAME,
                                           SERVER_COMMON_NAME)])
    return issuer

def get_subject_name(username):
    subject = x509.Name([x509.NameAttribute(NameOID.COUNTRY_NAME,
                                            CLIENT_COUNTRY_NAME),
                         x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME,
                                            CLIENT_STATE),
                         x509.NameAttribute(NameOID.LOCALITY_NAME,
                                            CLIENT_LOCALITY),
                         x509.NameAttribute(NameOID.ORGANIZATION_NAME,
                                            CLIENT_ORGANIZATION),
                         x509.NameAttribute(NameOID.COMMON_NAME,
                                            username)])
    return subject

def generate_csr(key, subject_name):
    csr = x509.CertificateSigningRequestBuilder().subject_name(subject_name)\
              .sign(key, SHA256(), default_backend())
    return csr

@accepts(x509.Name, RSAPrivateKey, CertificateSigningRequest)
def cert_from_csr(issuer, key, csr):
    cert = x509.CertificateBuilder().subject_name(csr.subject
    ).issuer_name(issuer).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number() # pylint: disable=E1101
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(datetime.utcnow() + timedelta(days=3650)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
        critical=False,
    ).sign(key, SHA256(), default_backend())
    return cert

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
        return pack_values(iv=initialization_vector, ct=ciphertext)


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


def private_key_to_file(key, filepath, password=None):
    """Save a PEM-formatted private key to a file and optionally encrypt"""
    with open(filepath, "wb") as f:
        if password:
            f.write(key.private_bytes(encoding=Encoding.PEM,
                                      format=PrivateFormat.TraditionalOpenSSL,
                                      encryption_algorithm=BestAvailableEncryption(password)))
        else:
            f.write(key.private_bytes(encoding=Encoding.PEM,
                                      format=PrivateFormat.TraditionalOpenSSL))


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
    elif isinstance(private_key_str, bytearray):
        private_key_str = bytes(private_key_str)
    if password:
        if isinstance(password, str):
            password = bytes(password, encoding='utf-8')
        elif isinstance(password, bytearray):
            password = bytes(password)
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
