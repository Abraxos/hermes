from Crypto.Cipher import AES
from Crypto import Random
from Crypto.Hash import SHA256
from rsa import verify, sign, encrypt, decrypt, PublicKey, PrivateKey, pkcs1


from ..utils.logging import *


# TODO: Contact library maintainer and find out why these numbers are...
ENCRYPTION_BLOCK_SIZE = 501
DECRYPTION_BLOCK_SIZE = 512
""" int: encryption and decryption block sizes

    The encryption block size refers to tbe maximum size of a string that the rsa library will accept as input.
    Consequently the decryption block size is the size of the output that an input of size 501 will produce. This does
    not quite make sense as the library documentation clearly states that the encryption/decryption functions should
    handle input of the same size as the key without issue. We are using keys of size 4096. Hence the todo above.
"""


def gen_symmetric_key():
    """ This function generates a key for symmetric encryption. More specifically it uses a secure randomness generator
        from the PyCrypto library to generate 32 random bits to use as a key for an AES256 symmetric encryption cipher.

        Args: None

        Returns:
            bytearray: A byte array of size 32 containing secure, randomly generated bits that can be used as a key for
                       an AES256 cipher.
    """
    return Random.get_random_bytes(32)


def symmetric_encrypt(msg, key):
    """ Encrypts a given message with a symmetric cipher, AES256 to be specific, and returns the ciphertext as an array
        of bytes. The ciphertext actually begins with an IV which is a random sequence of numbers that are used to
        initialize the cipher, but so long as you use the symmetrix_decrypt function included below on the ciphertext
        you should get the plaintext back without the IV.
    
    Args:
        msg (bytearray): The message that is to be encrypted.
        key (bytearray): The key, length 32, with which the message is to be encrypted.

    Returns:
        bytearray: A bytearray containing the ciphertext of the message encrypted with the key.
    """
    if msg and key:
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(key, AES.MODE_CFB, iv)
        return iv + cipher.encrypt(msg)


def symmetric_decrypt(ciphertext, key):
    """ Decrypts a ciphertext that was encrypted with a symmetric cipher, AES256 to be specific, and returns the 
        plaintext as an array of bytes. The key must be the same key that the message was originally encrypted with. 
        This function, along with its counterpart, symmetric_encrypt, is used to encrypt messages inside of sessions,
        but it can also be used to encrypt/decrypt information that needs to be stored on the hard-drive. Just be sure
        to read the file as bytes by using the "rb" flag for the open() function. This function does not take strings.

        If you use the symmetric_encrypt function, the result is actually the ciphertext with an IV value prepended.
        This value is used to initialize the cipher before the actual decryption. Therefore, there is a set of bytes at
        the start of the bytearray that are completely random. The number of these bytes is equal to the block size.
        The function uses these bytes to initialize the cipher object and then decrypt the message.

    Args:
        ciphertext (bytearray): The ciphertext that needs to be decrypted.
        key (bytearray): The key, length 32, with which the message is to be decrypted.

    Returns:
        bytearray: A bytearray containing the plaintext of the message that was decrypted.

    """
    if ciphertext and key:
        cipher = AES.new(key, AES.MODE_CFB, ciphertext[:AES.block_size])
        return cipher.decrypt(ciphertext)[AES.block_size:]


def private_key_to_file(private_key, filepath):
    """ Writes a private key to a file in PEM format. This function will create a file if one does not exist and it 
        will erase the contents of the file if it does exist.

    Args:
        private_key (rsa.PrivateKey): The key that is to be written to the file.
        filepath (string): A path to the file where you wish to write the key.
    Returns:
        None
    """
    with open(filepath, 'wb+') as f:
        pk = PrivateKey.save_pkcs1(private_key, format='PEM')
        f.write(pk)


def public_key_to_file(public_key, filepath):
    """ Writes a public key to a file in PEM format. This function will create a file if one does not exist and it 
        will erase the contents of the file if it does exist.

    Args:
        public_key (rsa.PublicKey): The key that is to be written to the file.
        filepath (string): A path to the file where you wish to write the key.
    Returns:
        None
    """
    with open(filepath, 'wb+') as f:
        pk = PublicKey.save_pkcs1(public_key, format='PEM')
        f.write(pk)


def public_key_from_file(filepath):
    """ Loads a public key from a given filepath.

    Args:
        filepath (string): A path to the file which contains the public key in a PEM format.
    Returns:
        rsa.PublicKey: The public key that results from reading the given file.
    """
    with open(filepath, 'rb') as f:
        pk = PublicKey.load_pkcs1(f.read(), format='PEM')
    return pk


def private_key_from_file(filepath):
    """ Loads a private key from a given filepath.

    Args:
        filepath (string): A path to the file which contains the private key in a PEM format.
    Returns:
        rsa.PrivateKey: The private key that results from reading the given file.
    """
    with open(filepath, 'rb') as f:
        pk = PrivateKey.load_pkcs1(f.read(), format='PEM')
    return pk


def private_key_from_str(private_key_str):
    """ Loads a private key from a given PEM-formatted string.

    Args:
        private_key_str (bytearray): A byte string which contains the private key in a PEM format.
    Returns:
        rsa.PrivateKey: The private key that results from reading the given file.
    """
    return PrivateKey.load_pkcs1(private_key_str, format='PEM')


def public_key_to_str(public_key):
    """ This function produces a string that represents the public key in PEM format. This was it can be written to a 
        database or transferred accross an internet connection.

    Args:
        public_key (rsa.PublicKey): The key that is to be interpreted to a PEM-format string.
    Returns:
        bytearray: A string of bytes representing the key in PEM format.
    """
    return PublicKey.save_pkcs1(public_key, format='PEM')


def public_key_from_str(public_key_str):
    """ Interprets a PEM-formatted string into a PublicKey object.

    Args:
        public_key_str (bytearray): The bytearray that represents the public key in a PEM format.

    Returns:
        rsa.PublicKey: The public key that is the result of interpreting the PEM-formatted bytearray.

    """
    return PublicKey.load_pkcs1(public_key_str, format='PEM')


def public_key_sha256(public_key):
    """ This function produces a string that represents the SHA256 hash of the public key. This SHA256 hash can be used
    as the ID of the public key and anyone associated with it, for example, in a dictionary of a database. This 
    function exists because one cannot hash a public_key object directly, it needs to be turned into a string first. 
    Its more efficient to use this function once and associate the result with the key somehow and then use this hash 
    as the key in a dictionary of database rather than try to interpret the key as a string every time.

    Args:
        public_key (rsa.PublicKey): The key that is to be interpreted to a PEM-format string.
    Returns:
        bytearray: A string of bytes representing the SHA256 hash of the public key.
    """
    return SHA256.new(public_key_to_str(public_key)).hexdigest()


def private_key_to_str(private_key):
    """ This function produces a string that represents the public key in PEM format. This was it can be written to a 
        database or transferred accross an internet connection.

    Args:
        private_key (rsa.PrivateKey): The key that is to be interpreted to a PEM-format string.
    Returns:
        bytearray: A string of bytes representing the key in PEM format.
    """
    return PrivateKey.save_pkcs1(private_key, format='PEM')


def asymmetric_decrypt_verify(ciphertext, decrypt_key, verify_key):
    """ This function decrypts a message that was encrypted with an asymmetric cipher. In this case, we use an RSA 
        algorithm. This function returns the plaintext of the message from the ciphertext only if the message
        signature is valid. Specifically, this function expects the signature to be the first 512 bytes of the 
        decrypted message, so once it acquires the plaintext, it extracts the signature. This function expects the
        ciphertext along with a key to be used for decryption (the recipient's public key) and the verification key
        (the sender's public key). It decrypts the ciphertext and then extracts the signature and verifies it. If the
        signature is verified then the function returns the decrypted message, otherwise it returns None and logs a 
        warning that the verification failed. This function also returns None and logs when there is a decryption
        failure or a type error (when the wrong type is given in place of the ciphertext).

    Args:
        ciphertext (bytearray): The ciphertext that is to be decrypted. For best results, this should be the ciphertext
                            that was produced by the asymmetric_encrypt_sign() function. The ciphertext should be the
                            encrypted message with its signature of 512 bytes prepended to it before encryption.
        decrypt_key (rsa.PrivateKey): The private key object that should be used to decrypt the message.
        verify_key (rsa.PublicKey): The public key object that should be used to verify the signature of the message.
    Returns:
        bytearray: The ciphertext if the message can be decrypted and verified, and None otherwise as well as logging
                   certain common types of errors.

    """
    signature, plaintext, verified = None, None, False
    try:
        blocks = []
        for i in range(0, len(ciphertext), DECRYPTION_BLOCK_SIZE):
            blocks.append(decrypt(ciphertext[i:i + DECRYPTION_BLOCK_SIZE], decrypt_key))
        plaintext = b''.join(blocks)
        signature, plaintext = plaintext[:DECRYPTION_BLOCK_SIZE], plaintext[DECRYPTION_BLOCK_SIZE:]
        verified = verify(plaintext, signature, verify_key)
    except TypeError:
        log("Warning: TypeError has occurred during a decrypt/verify. \n\tCIPHERTEXT({0}): {1}".format(len(ciphertext),
                                                                                                       ciphertext))
    except pkcs1.DecryptionError:
        log("Warning: RSA Decryption Failed. \n\tCIPHERTEXT({0}): {1}".format(len(ciphertext), ciphertext))
    except pkcs1.VerificationError:
        log("WARNING: RSA Verification Failed. \n\tPLAINTEXT({0}): {1} \n\tSIGNATURE({2}): {3}".format(len(plaintext),
                                                                                                       plaintext,
                                                                                                       len(signature),
                                                                                                       signature))
    if signature and plaintext and verified:
        return plaintext


def asymmetric_verify(signature, plaintext, verify_key):
    """ This function verifies the signature (bytearray) of a message given the original plaintext (bytearray) and the
        public key with which to verify the signature (rsa.PublicKey). The function returns true if the signature is
        valid or false if the signature is invalid or if the type of input is incorrect.

    Args:
        signature (bytearray): The signature that needs to be verified.
        plaintext (bytearray): The plaintext that has been signed.
        verify_key (rsa.PublicKey): The private key object that should be used to verify the signature.
    Returns:
        bytearray: A byte array containing the plaintext of the message as long as the verification passes, and None
                   otherwise.
    """
    verified = False
    try:
        verified = verify(plaintext, signature, verify_key)
    except TypeError:
        log("Warning: TypeError has occurred during a verify. \n\tSIGNATURE({0}): {1}".format(len(signature),
                                                                                              signature))
    except pkcs1.VerificationError:
        log("WARNING: RSA Verification Failed. \n\tPLAINTEXT({0}): {1} \n\tSIGNATURE({2}): {3}".format(len(plaintext),
                                                                                                       plaintext,
                                                                                                       len(signature),
                                                                                                       signature))
    return verified


def asymmetric_decrypt(ciphertext, decrypt_key):
    """ This function decrypts a message that was encrypted with an asymmetric cipher. In this case we use an RSA
        algorithm. This function returns the plaintext of the message from the ciphertext even if the message signature
        is invalid. The function expects the first 512 bytes of the decrypted plaintext to be the signature of the
        message. Once the ciphertext is decrypted it separates the signature from the plaintext and returns both. If
        the decryption fails the function returns (None, None), otherwise the function returns the plaintext and the
        signature regardless of whether the signature is valid.

        It is not advisable to use this function for anything other than debugging with the exception of the function
        asymmetric_decrypt_verify_public_key() which uses it to decrypt the message and then verify the signature with
        the public key contained in the message.

    Args:
        ciphertext (bytearray): The ciphertext that is to be decrypted. For best results, this should be the ciphertext
                            that was produced by the asymmetric_encrypt_sign() function. The ciphertext should be the
                            encrypted message with its signature of 512 bytes prepended to it before encryption.
        decrypt_key (rsa.PrivateKey): The private key object that should be used to decrypt the message.
    """
    plaintext, signature = None, None
    try:
        blocks = []
        for i in range(0, len(ciphertext), DECRYPTION_BLOCK_SIZE):
            blocks.append(decrypt(ciphertext[i:i + DECRYPTION_BLOCK_SIZE], decrypt_key))
        plaintext = b''.join(blocks)
        signature, plaintext = plaintext[:DECRYPTION_BLOCK_SIZE], plaintext[DECRYPTION_BLOCK_SIZE:]
    except TypeError:
        log("Warning: TypeError has occurred during a decrypt/verify. \n\tCIPHERTEXT({0}): {1}".format(len(ciphertext),
                                                                                                       ciphertext))
    except pkcs1.DecryptionError:
        log("Warning: RSA Decryption Failed. \n\tCIPHERTEXT({0}): {1}".format(len(ciphertext), ciphertext))
    if plaintext and signature:
        return plaintext, signature
    else:
        return None, None


def asymmetric_decrypt_verify_public_key(ciphertext, decrypt_key):
    """ This is a variant of the asymmetric_decrypt_verify() function that is meant to be used to verify a public key
        that was signed by the associated private key. More specifically this function takes a bytearray containing the
        ciphertext of a public key and its prepended signature of 512 bytes. The function decrypts the ciphertext,
        creates the public key object from the plaintext, and then verifies the message with the public key. This
        function is designed primarily to establish the fact that the client sending the public key is indeed the owner
        of the private key. There is an issue with this function in that anyone could listen to someone sending the
        same message and just resend it, which would pass verification. In the Hermes protocol the server needs to
        send a challenge to the client after this function.

    Args:
        ciphertext (bytearray): The ciphertext that is to be decrypted. The decrypted message of this ciphertext needs
                                to be the public key of the client with the signature of the public key prepended.
        decrypt_key (rsa.PrivateKey): The private key object that should be used to decrypt the message.
    Returns:
        bytearray: A byte array containing the plaintext of the message as long as the verification passes, and None
                   otherwise.
    """
    plaintext, signature = asymmetric_decrypt(ciphertext, decrypt_key)
    if plaintext and signature:
        try:
            public_key = PublicKey.load_pkcs1(plaintext, format='PEM')
            verify(plaintext, signature, public_key)
        except pkcs1.VerificationError:
            log("WARNING: RSA Verification Failed\n\tPLAINTEXT({0}): {1} \n\tSIGNATURE({2}): {3}".format(len(plaintext),
                                                                                                         plaintext,
                                                                                                         len(signature),
                                                                                                         signature))
            return None
        return plaintext


def _asymmetric_encrypt_sign(plaintext, encrypt_key, sign_key):
    """ This function takes a plaintext message, encryption key (typically the public key of the sender), and the
        signature key (typically the private key) and produces the ciphertext using an RSA encryption algorithm
        along with the signature. A key thing to keep in mind is that the plaintext of the outputted ciphertext
        contains the signature in its first 512 bytes. So the output of this function is something like this:
        ciphertext                   signature
        signature        message     signature
        ([   512 bytes   ][message]) [signature]
        Where the items in parenthesis are encrypted.
    Args:
        plaintext (bytearray): The plaintext message that is meant to be encrypted.
        encrypt_key (rsa.PublicKey): The key with which the message is to be encrypted, the public key of the recipient.
        sign_key (rsa.PrivateKey): The key with which the message is to be signed, the private key of the sender.
    Returns:
        bytearray: A bytearray containing the ciphertext of the message pre-pended with the signature.
        bytearray: A bytearray containing the plaintext signature of the message.
    """
    signature = sign(plaintext, sign_key, 'SHA-512')
    plaintext = signature + plaintext
    blocks = []
    for i in range(0, len(plaintext), ENCRYPTION_BLOCK_SIZE):
        blocks.append(encrypt(plaintext[i:i + ENCRYPTION_BLOCK_SIZE], encrypt_key))
    ciphertext = b''.join(blocks)
    return ciphertext, signature


def asymmetric_sign(plaintext, sign_key):
    return sign(plaintext, sign_key, 'SHA-512')


def asymmetric_encrypt_sign(plaintext, encrypt_key, sign_key):
    """ This function is identical to the one above except that it only returns the ciphertext of the signature and
        message and not the plaintext signature. This is the function you should probably be using.

    Args:
        plaintext (bytearray): The plaintext message that is meant to be encrypted.
        encrypt_key (rsa.PublicKey): The key with which the message is to be encrypted, the public key of the recipient.
        sign_key (rsa.PrivateKey): The key with which the message is to be signed, the private key of the sender.
    Returns:
        bytearray: A bytearray containing the ciphertext of the message pre-pended with the signature.
    """
    return _asymmetric_encrypt_sign(plaintext, encrypt_key, sign_key)[0]
