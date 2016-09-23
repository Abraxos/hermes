from __future__ import print_function
from enum import IntEnum
from OpenSSL.SSL import VERIFY_PEER # pylint: disable=E0401
from OpenSSL.SSL import VERIFY_FAIL_IF_NO_PEER_CERT # pylint: disable=E0401
from OpenSSL.SSL import Connection # pylint: disable=E0401
from OpenSSL.crypto import X509 # pylint: disable=E0401
from twisted.internet import reactor # pylint: disable=E0401
from twisted.internet.ssl import DefaultOpenSSLContextFactory # pylint: disable=E0401
from twisted.internet.protocol import Factory, Protocol # pylint: disable=E0401
import attr # pylint: disable=E0401
from attr.validators import instance_of # pylint: disable=E0401

from utils import log_debug, log_warning, log_info, log_error,accepts, unpack
from utils import pack, pack_dict
from crypto import password_verified, hash_salt

ID_MSG_KEY_TYPE = 'type'
ID_MSG_KEY_USERNAME = 'username'
ID_MSG_KEY_PASSWORD = 'password'
ID_MSG_KEY_CERT = 'cert'
ID_MSG_KEY_CSR = 'csr'
ID_MSG_KEY_ENC_PRIV = 'encrypted_privkey'
ID_MSG_KEY_CA = 'ca'
ID_MSG_KEY_ERROR_MSG = 'error_msg'

ID_MSG_TYPE_ERROR = 'error'
ID_MSG_TYPE_FETCH = 'fetch'
ID_MSG_TYPE_REGISTER = 'register'
ID_MSG_TYPE_FETCH_MY = 'fetch_my'
ID_MSG_TYPE_FETCHED_CREDS = 'fetched_credentials'
ID_MSG_TYPE_YOUR_KEY_AND_CERT = 'your_key_and_cert'
ID_MSG_TYPE_NEW_CERT = 'new_cert'

# TODO: Replace global users dictionary with a database connection for each protocol
USERS = {}

@attr.s
class UserInfo(object):
    username =              attr.ib(validator=instance_of(str))
    hased_salted_pw =       attr.ib(validator=instance_of(str))
    encrypted_private_key = attr.ib(validator=instance_of(str))
    certificate =           attr.ib(validator=instance_of(X509))

class HermesIdentityServerProtocol(Protocol):
    """HermesIdentityServerProtocol object which handles communication with a single client"""
    # TODO: Replace this in-memory list with a database connection
    users = {} # dict{username:str : user:UserInfo}

    def __init__(self):
        self.users = USERS

    def send(self, msg):
        self.transport.write(pack(msg))

    def send_error(self, msg):
        self.send({ID_MSG_KEY_TYPE:ID_MSG_TYPE_ERROR,
                   ID_MSG_KEY_ERROR_MSG:msg})

    def error(self, msg):
        """Sends an error and terminates the connection"""
        log_error(msg)
        self.send_error(msg)
        self.transport.loseConnection()

    def ack(self):
        """Sends an ack"""
        self.send('ack')

    def dataReceived(self, data): # pylint: disable=C0111, C0103
        """A callback that handles receiving raw data and unpacking it"""
        msg_obj = unpack(data)
        if not msg_obj or not isinstance(msg_obj, dict):
            self.error('Invalid packet')
        else:
            self.dict_received(msg_obj)

    def handle_fetch(self, dict_obj):
        if ID_MSG_KEY_USERNAME in dict_obj:
            username = dict_obj[ID_MSG_KEY_USERNAME]
            if username in self.users:
                self.send({ID_MSG_KEY_TYPE:ID_MSG_TYPE_FETCHED_CREDS,
                           ID_MSG_KEY_CERT:self.users[username].certificate})
            else:
                self.error("No such user: {}".format(username))
        else:
            self.error("Fetch request doesn't have a username")

    def handle_fetch_my(self, dict_obj):
        if all (k in dict_obj for k in (ID_MSG_KEY_USERNAME,
                                        ID_MSG_KEY_PASSWORD)):
            username = dict_obj[ID_MSG_KEY_USERNAME]
            password = dict_obj[ID_MSG_KEY_PASSWORD]
            user_info = self.users[username]
            if password_verified(password, user_info.hased_salted_pw):
                self.send({ID_MSG_KEY_TYPE:ID_MSG_TYPE_YOUR_KEY_AND_CERT,
                           ID_MSG_KEY_ENC_PRIV:user_info.encrypted_private_key,
                           ID_MSG_KEY_CERT:user_info.certificate})
            else:
                self.error("Invalid username or password")
        else:
            self.error("Invalid message format - lacks username/password")

    def handle_registration(self, dict_obj):
        if all (k in dict_obj for k in (ID_MSG_KEY_USERNAME,
                                        ID_MSG_KEY_PASSWORD,
                                        ID_MSG_KEY_CSR,
                                        ID_MSG_KEY_ENC_PRIV)):
            username =          dict_obj[ID_MSG_KEY_USERNAME]
            password =          dict_obj[ID_MSG_KEY_PASSWORD]
            csr =               dict_obj[ID_MSG_KEY_CSR]
            encrypted_privkey = dict_obj[ID_MSG_KEY_ENC_PRIV]
            # TODO: Approve the CSR and return the certificate
            cert = None
            hashed_salted_pw = hash_salt(password)
            user_info = UserInfo(username, hashed_salted_pw,
                                 encrypted_privkey, cert)
            self.users[username] = user_info
            self.send({ID_MSG_KEY_TYPE:ID_MSG_TYPE_NEW_CERT,
                       ID_MSG_KEY_CERT:cert})
        else:
            self.error("Invalid message format - lacks username/password/csr")

    def dict_received(self, dict_obj): # pylint: disable=R0201
        if ID_MSG_KEY_TYPE in dict_obj:
            msg_type = dict_obj[ID_MSG_KEY_TYPE]
            if msg_type == ID_MSG_TYPE_FETCH:
                self.handle_fetch(dict_obj)
                self.transport.loseConnection()
            elif msg_type == ID_MSG_TYPE_FETCH_MY:
                self.handle_fetch_my(dict_obj)
                self.transport.loseConnection()
            elif msg_type == ID_MSG_TYPE_REGISTER:
                self.handle_registration(dict_obj)
                self.transport.loseConnection()
            else:
                self.error('Invalid message type')
        else:
            self.error('Invalid dictionary object')


@accepts(Connection, X509, int, int, int)
def verify_client(connection, x509, errnum, errdepth, auth_ok):
    """Verifies the identity of the client using SSL"""
    if not auth_ok:
        log_warning('Invalid Client Authentication: {0}\n\tConnection: {1}\n'\
                    '\tErrNum: {2} ErrDepth: {3}'.format(x509.get_subject(),
                                                         connection, errnum,
                                                         errdepth))
        return False
    log_info('Client Authentication Successful: {0}'.format(x509.get_subject()))
    return True

@attr.s
class HermesIdentityServer(object):
    """Hermes Identity Server object that handles actually running the server reactor"""
    port = attr.ib()
    key_filepath = attr.ib()
    cert_filepath = attr.ib()
    ca_filepath = attr.ib()
    factory = None
    context_factory = None
    context = None

    def initialize(self, protocol):
        """Initialize the SSL context and protocol factory with all relevant information"""
        self.factory = Factory()
        self.factory.protocol = protocol
        self.context_factory = DefaultOpenSSLContextFactory(self.key_filepath,
                                                            self.cert_filepath)
        self.context = self.context_factory.getContext()

    def run_reactor(self):
        """Run the reactor using the context"""
        assert self.context is not None
        reactor.listenSSL(self.port, self.factory, self.context_factory)
        reactor.run()

if __name__ == '__main__':
    SERVER = HermesIdentityServer(8000,
                                  'testing_keys/server/server.key',
                                  'testing_keys/server/server.cert',
                                  'testing_keys/ca/ca.cert')
    SERVER.initialize(HermesIdentityServerProtocol)
    SERVER.run_reactor()
