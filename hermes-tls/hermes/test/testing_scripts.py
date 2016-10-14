from hermes.crypto.crypto import generate_asymmetric_openssl_key
from hermes.crypto.crypto import private_key_to_file

key = generate_asymmetric_openssl_key()
private_key_to_file(key, 'hermes/test/testing_keys/server/server.key')
