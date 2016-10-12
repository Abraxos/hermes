from twisted.internet import task
from twisted.trial import unittest
from twisted.test import proto_helpers

from hermes.utils.utils import pack, unpack # pylint: disable=E0401
from hermes.crypto.crypto import private_key_from_file, cert_from_file # pylint: disable=E0401

from hermes.client.hermes_identity_client import _fetch_request, _fetch_my_request # pylint: disable=E0401
from hermes.client.hermes_identity_client import _registration_request # pylint: disable=E0401
from hermes.server.identity.hermes_identity import HermesIdentityServerProtocolFactory # pylint: disable=E0401
from hermes.server.identity.hermes_identity import HermesIdentityServerProtocol # pylint: disable=E0401

TEST_SERVER_PRIVATE_KEY_FILEPATH = '/home/eugene/Development/hermes/hermes-tls/hermes/test/testing_keys/server/server.cert'
TEST_SERVER_SUBJECT_INFO = 'testing.hermes.messenger.com'

class IdentityServerTestCase(unittest.TestCase):
    def setUp(self):
        self.pk = private_key_from_file(TEST_SERVER_PRIVATE_KEY_FILEPATH)
        self.subject_info = TEST_SERVER_SUBJECT_INFO
        self.factory = HermesIdentityServerProtocolFactory(TEST_SERVER_PRIVATE_KEY_FILEPATH, self.subject_info)
        self.tr = proto_helpers.StringTransportWithDisconnection()
        self.proto = HermesIdentityServerProtocol(self.pk, self.subject_info)
        self.tr.protocol = self.proto
        self.proto.makeConnection(self.tr)

    def _test(self, input_data, expected_output):
        self.tr.clear()
        self.proto.dataReceived(pack(input_data))
        print(input_data)
        print(unpack(self.tr.value()))
        self.assertEqual(expected_output, unpack(self.tr.value()))

    def test_fetch_non_existent_user(self):
        fetch_request = _fetch_request('non_existent_username')
        self._test(fetch_request, None)
