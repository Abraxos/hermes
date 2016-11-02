"""The Zeus client module that is used to connect to the Zeus server and API"""
from __future__ import print_function
from collections import namedtuple
from twisted.internet import ssl, reactor # pylint: disable=E0401
from twisted.internet.protocol import ClientFactory, Protocol # pylint: disable=E0401
from twisted.internet.defer import Deferred # pylint: disable=E0401
from OpenSSL import SSL
from OpenSSL.crypto import PKey
from hermes.utils.utils import log_debug, log_warning, log_info, log_error, accepts, unpack
from hermes.utils.utils import pack
from hermes.utils.constants import *
from hermes.crypto.crypto import serialize_csr, generate_csr
from hermes.crypto.crypto import private_key_to_str

@accepts(str)
def _fetch_request(username):
    return {ID_MSG_KEY_TYPE : ID_MSG_TYPE_FETCH,
            ID_MSG_KEY_USERNAME : username}

@accepts(str, str)
def _fetch_my_request(username, password):
    return {ID_MSG_KEY_TYPE : ID_MSG_TYPE_FETCH_MY,
            ID_MSG_KEY_USERNAME : username,
            ID_MSG_KEY_PASSWORD : password}

def _registration_request(username, acct_password, key, key_password):
    """Helper function for generating registration request messages."""
    return {ID_MSG_KEY_TYPE : ID_MSG_TYPE_REGISTER,
            ID_MSG_KEY_USERNAME : username,
            ID_MSG_KEY_PASSWORD : acct_password,
            ID_MSG_KEY_CSR : serialize_csr(generate_csr(key, username)),
            ID_MSG_KEY_ENC_PRIV : private_key_to_str(key, key_password)}

class HermesIdentityClientProtocol(Protocol):

    def __init__(self, factory):
        """A constructor for the protocol object."""
        self.factory = factory
        self.d = None

    def send(self, msg):
        """A function for packing and sending messages on the transport"""
        self.transport.write(pack(msg))

    @accepts(object, str)
    def send_error(self, msg):
        """A function for sending error messages to the server."""
        self.send({ID_MSG_KEY_TYPE:ID_MSG_TYPE_ERROR,
                   ID_MSG_KEY_ERROR_MSG:msg})

    @accepts(object, dict)
    def error(self, msg):
        """Sends an error and terminates the connection"""
        log_error(msg)
        self.send_error(msg)
        self.transport.loseConnection()

    def dataReceived(self, data): # pylint: disable=C0103
        """A callback that handles receiving raw data and unpacking it"""
        msg_obj = unpack(data)
        if not msg_obj or not isinstance(msg_obj, dict):
            self.error('Invalid packet')
        else:
            self.dict_received(msg_obj)

    @accepts(object, dict)
    def dict_received(self, dict_obj): # pylint: disable=R0201
        """A callback for verifying that a received dictionary is properly formatted and calling a callback on the current deferred"""
        if ID_MSG_KEY_TYPE in dict_obj:
            self.d.callback(dict_obj)
        else:
            self.error('Invalid dictionary object')
            log_warning('Invalid dictionary object')

    @accepts(object, str)
    def _fetch(self, username):
        fetch_request = _fetch_request(username)
        self.send(fetch_request)
        self.d = Deferred()
        return self.d

    @accepts(object, str)
    def fetch(self, username):
        """Given a username, this function fetches the associated certificate from the
           identity server."""
        def received_user_certificate(msg):
            """Callback for handling received certificates of other users"""
            msg_type = msg[ID_MSG_KEY_TYPE]
            if msg_type == ID_MSG_TYPE_FETCHED_CREDS:
                return msg[ID_MSG_KEY_CERT]
            elif msg_type == ID_MSG_TYPE_ERROR:
                if ID_MSG_KEY_ERROR_MSG in msg:
                    if msg[ID_MSG_KEY_ERROR_MSG] == ID_MSG_ERROR_USERNAME_DOES_NOT_EXIST:
                        log_warning("Username {} does not on the server!")
                    else:
                        log_warning("Unknown error message received from server in response to fetch query: {}".format(msg))
                    return None
                else:
                    log_warning("Invalid error message received from server in response to fetch query: {}".format(msg))
                    return None
        return self._fetch(username).addCallback(received_user_certificate)
        # TODO: write errback as well

    @accepts(object, str, str)
    def _fetch_my(self, username, acct_password):
        """Helper function for sending a fetch_my request to the server"""
        fetch_request = _fetch_my_request(username, acct_password)
        self.send(fetch_request)
        self.d = Deferred()
        return self.d

    @accepts(object, str, str)
    def fetch_my(self, username, acct_password):
        """Given a username and password, this function fetches the associated certificate and encrypted private key from the server"""
        def received_credentials(msg):
            msg_type = msg[ID_MSG_KEY_TYPE]
            if msg_type == ID_MSG_TYPE_YOUR_KEY_AND_CERT:
                private_key = msg[ID_MSG_KEY_ENC_PRIV]
                cert = msg[ID_MSG_KEY_CERT]
                return private_key, cert
            elif msg_type == ID_MSG_TYPE_ERROR:
                if ID_MSG_KEY_ERROR_MSG in msg:
                    if msg[ID_MSG_KEY_ERROR_MSG] == ID_MSG_ERROR_USERNAME_DOES_NOT_EXIST:
                        log_warning("Username {} does not exist on the server!")
                    else:
                        log_warning("Unknown error message received from server in response to fetch_my query: {}".format(msg))
                    return None
                else:
                    log_warning("Invalid error message received from server in response to fetch query: {}".format(msg))
                    return None
        return self._fetch_my(username, acct_password).addCallback(received_credentials)
        # TODO: write errback as well

    @accepts(object, str, str, PKey, str)
    def _register(self, username, acct_password, key, key_password):
        """Helper function for sending a registration request to the server."""
        registration_request = _registration_request(username,
                                                     acct_password,
                                                     key,
                                                     key_password)
        self.send(registration_request)
        self.d = Deferred()
        return self.d

    def register(self, username, acct_password, key, key_password):
        """Registers a new username to an identity server

        Given a username, account password, and private key encryption password,
        this function generates a Certificate Signing request, and sends that
        along with the username, account password, and encrypted provate key to
        the identity server. The server will reply with a signed certificate if
        it accepts the username and other information as valid.

        Args:
            username: The username that the user desires on a particular
                      identity server.
            acct_password: The password associated with the account the user
                           wants to create. Note that this password should be assumed as being known to the server but is only used
                           to verify user identity in lieu of certificates so
                           that the user can add new devices. All messages and
                           keys are encrypted using the other password.
            key_password: The password that is used to encrypt the private key
                          before they are sent to the server. This password
                          should be extremely strong as the security of all messages sent through hermes is tied to this password. It should never be sent to the server. In this function it is used to open the private key for creating the CSR.

        Returns:
            A certificate, signed by the server acting as the CA if the server
            if the server accepts the username and other information. Otherwise
            it will return false.
        """
        def received_certificate(msg):
            msg_type = msg[ID_MSG_KEY_TYPE]
            if msg_type == ID_MSG_TYPE_NEW_CERT:
                return msg[ID_MSG_KEY_CERT]
            elif msg_type == ID_MSG_TYPE_ERROR:
                if ID_MSG_KEY_ERROR_MSG in msg:
                    if msg[ID_MSG_KEY_ERROR_MSG] == ID_MSG_ERROR_USERNAME_EXISTS:
                        log_warning("Username {} already exists on the server!")
                    else:
                        log_warning("Unknown error message received from server: {}".format(msg))
                    return None
                else:
                    log_warning("Invalid error message received from server: {}".format(msg))
                    return None
        return self._register(username,
                              acct_password,
                              key,
                              key_password).addCallback(received_certificate)
                              # TODO: write errback as well

class HermesIdentityClientFactory(ClientFactory):
    """The factory that handles generating protocol objects for the client to connect to servers"""
    protocol = HermesIdentityClientProtocol
    last_call_result = None

    # def __init__(self, zeus_msg):
    #     pass

    def buildProtocol(self, _): # pylint: disable=C0103
        """Protocol builder method"""
        return self.protocol(self)

    def clientConnectionFailed(self, _, reason): # pylint: disable=C0103, R0201
        """A callback for handling failed connections"""
        log_warning("Connection lost - " + repr(reason))
        # reactor.stop()

    def clientConnectionLost(self, _, reason): # pylint: disable=C0103, R0201
        """A callback for handling lost connections"""
        log_warning("Connection lost - " + repr(reason))
        # reactor.stop()

if __name__ == '__main__':
