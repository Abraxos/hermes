"""The Zeus client module that is used to connect to the Zeus server and API"""
from __future__ import print_function
from collections import namedtuple
from twisted.internet import ssl, reactor # pylint: disable=E0401
from twisted.internet.protocol import ClientFactory, Protocol # pylint: disable=E0401
from twisted.internet.defer import Deferred # pylint: disable=E0401
from OpenSSL import SSL # pylint: disable=E0401
import attr # pylint: disable=E0401
from utils import log_debug, log_warning, log_info, log_error,accepts, unpack
from utils import pack, pack_dict
from hermes_constants import *

class HermesIdentityClientProtocol(Protocol):

    def __init__(self, factory):
        self.factory = factory
        self.d = None

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

    # def ack(self):
    #     """Sends an ack"""
    #     self.send('ack')

    def dataReceived(self, data): # pylint: disable=C0103
        """A callback that handles receiving raw data and unpacking it"""
        msg_obj = unpack(data)
        if not msg_obj or not isinstance(msg_obj, dict):
            self.error('Invalid packet')
        else:
            self.dict_received(msg_obj)

    def dict_received(self, dict_obj): # pylint: disable=R0201
        if ID_MSG_KEY_TYPE in dict_obj:
            self.d.callback(dict_obj)
        else:
            self.error('Invalid dictionary object')

    def _register(self, username, acct_password, key_password):
        registration_request = {ID_MSG_KEY_TYPE : ID_MSG_TYPE_REGISTER,
                                ID_MSG_KEY_USERNAME : username,
                                ID_MSG_KEY_PASSWORD : acct_password,
                                ID_MSG_KEY_CSR : None, # TODO: generate CSR
                                ID_MSG_KEY_ENC_PRIV : None} # TODO: get encrypted private key
        self.send(registration_request)
        self.d = Deferred()
        return self.d

    # public API:
    def fetch(self, username):
        """Given a username, this function fetches the associated certificate from the identity server."""
        # TODO: implement this function
        pass

    def fetch_my(self, username, acct_password):
        """Given a username and password, this function fetches the associated certificate and encrypted private key from the server"""
        # TODO: implement this function
        pass

    def register(self, username, acct_password, key_password):
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
        def received_certificate(msg_dict):
            msg_type = msg_dict[ID_MSG_KEY_TYPE]
            if msg_type == ID_MSG_TYPE_NEW_CERT:
                return msg_dict[ID_MSG_KEY_CERT]
            elif msg_type == ID_MSG_TYPE_ERROR:
                if ID_MSG_KEY_ERROR_MSG in msg_dict:
                    if msg_dict[ID_MSG_KEY_ERROR_MSG] == ID_MSG_ERROR_USERNAME_EXISTS:
                        log_warning("Username {} already exists on the server!")
                    else:
                        log_warning("Unknown error message received from server: {}".format(msg_dict))
                    return None
                else:
                    log_warning("Invalid error message received from server: {}".format(msg_dict))
                    return None
        return self._register(username,
                              acct_password,
                              key_password).addCallback(received_certificate)

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
