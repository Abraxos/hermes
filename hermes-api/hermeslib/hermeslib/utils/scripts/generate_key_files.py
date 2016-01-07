from rsa import verify, sign, encrypt, decrypt, PublicKey, PrivateKey, newkeys, pkcs1

PUB_KEY_DST = '../../tests/testing_data/user1_test_pub.pem'
PRIV_KEY_DST = '../../tests/testing_data/user1_test.pem'

(public,private) = newkeys(4096, poolsize=4)

with open(PUB_KEY_DST, 'wb+') as f:
    pk = PublicKey.save_pkcs1(public, format='PEM')
    f.write(pk)

with open(PRIV_KEY_DST, 'wb+') as f:
    pk = PrivateKey.save_pkcs1(private, format='PEM')
    f.write(pk)