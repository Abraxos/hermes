from twisted.internet import task
from twisted.trial import unittest
from twisted.test import proto_helpers

from hermes.utils.utils import pack, unpack
from hermes.crypto.crypto import private_key_from_file

from hermes.client.hermes_identity_client import _fetch_request
from hermes.client.hermes_identity_client import _fetch_my_request
from hermes.client.hermes_identity_client import _registration_request
from hermes.server.identity.identity import HermesIdentityServerProtocolFactory
from hermes.server.identity.identity import HermesIdentityServerProtocol
from hermes.server.identity.identity import USERS

TEST_SERVER_PRIVATE_KEY_FILEPATH = '/home/eugene/Development/hermes/hermes-tls/hermes/test/testing_keys/server/server.key'
TEST_SERVER_SUBJECT_INFO = 'testing.hermes.messenger.com'

class IdentityServerTestCase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.pk = private_key_from_file(TEST_SERVER_PRIVATE_KEY_FILEPATH)
        self.subject_info = TEST_SERVER_SUBJECT_INFO
        self.factory = HermesIdentityServerProtocolFactory(TEST_SERVER_PRIVATE_KEY_FILEPATH, self.subject_info)
        self.tr = proto_helpers.StringTransportWithDisconnection()
        self.proto = HermesIdentityServerProtocol(self.pk, self.subject_info)
        self.tr.protocol = self.proto
        self.proto.makeConnection(self.tr)

    def _test(self, input_data, expected_output, check_func=None):
        self.tr.clear()
        print('CLIENT: {}'.format(input_data))
        self.proto.dataReceived(pack(input_data))
        print('SERVER: {}'.format(unpack(self.tr.value())))
        if not check_func:
            self.assertEqual(expected_output, unpack(self.tr.value()))
        else:
            self.assertTrue(check_func(expected_output, unpack(self.tr.value())))

    def test_fetch_non_existent_user(self):
        fetch_request = _fetch_request('non_existent_username')
        self._test(fetch_request, {'type': 'error', 'error_msg': 'No such user: non_existent_username'})

    def test_registration(self):
        if 'player1' not in self.proto.users:
            def check_cert(_, result):
                self.assertTrue('cert' in result)
                self.assertTrue('type' in result)
                self.assertEqual(result['type'], 'new_cert')
                self.assertTrue(result['cert'].startswith('-----BEGIN CERTIFICATE-----'))
                return True
            registration_request = _registration_request('player1', 'password123', self.pk, 'letmein')
            self._test(registration_request, None, check_cert)
        else:
            print("This test was already run successfully as part of another")

    def test_registration_username_already_exists(self):
        registration_request = _registration_request('player1', 'password123', self.pk, 'letmein')
        self._test(registration_request, {'type': 'error', 'error_msg': 'username_already_exists'})

    def test_fetch_existent_user(self):
        def check_cert(_, result):
            self.assertTrue('cert' in result)
            self.assertTrue('type' in result)
            self.assertEqual(result['type'], 'fetched_credentials')
            self.assertTrue(result['cert'].startswith('-----BEGIN CERTIFICATE-----'))
            return True
        if 'player1' not in self.proto.users:
            self.test_registration()
        fetch_request = _fetch_request('player1')
        self._test(fetch_request, None, check_cert)

    def test_fetch_my(self):
        def check_reply(_, result):
            self.assertIn('cert', result)
            self.assertIn('type', result)
            self.assertIn('encrypted_privkey', result)
            self.assertEqual(result['type'], 'your_key_and_cert')
            self.assertTrue(result['cert'].startswith('-----BEGIN CERTIFICATE-----'))
            self.assertTrue(result['encrypted_privkey'].startswith('-----BEGIN ENCRYPTED PRIVATE KEY-----'))
            return True
        if 'player1' not in self.proto.users:
            self.test_registration()
        fetch_request = _fetch_my_request('player1', 'password123')
        self._test(fetch_request, None, check_reply)

    def test_fetch_my_nonexistent_username(self):
        fetch_request = _fetch_my_request('non_existent_username', 'password123')
        self._test(fetch_request, {'type': 'error', 'error_msg': 'Invalid username or password'})

    def test_fetch_my_bad_password(self):
        if 'player1' not in self.proto.users:
            self.test_registration()
        fetch_request = _fetch_my_request('player1', 'wrong password')
        self._test(fetch_request, {'type': 'error', 'error_msg': 'Invalid username or password'})
