from enum import Enum
from collections import deque

from ..utils.logging import *
from ..crypto.crypto import *


MAX_NUM_SESS_MSG = 1000


class User(object):
    def __init__(self, public_key, private_key, username):
        self.public_key = public_key
        self.private_key = private_key
        self.username = username

class ClientSession(object):
    class State(Enum):
        initial = 0

    class LoginState(Enum):
        initial = 0
        signing_challenge = 1
        sending_username = 2
        successful = 3
        failed = 4

    def __init__(self, key, protocol):
        self.key = key
        self.protocol = protocol
        self.user = None
        self.message_buffer = deque([])

    def login(self, username, public_key, private_key):
        self.user = User(public_key, private_key, username)
        self.login_state = self.LoginState.initial
        self.send_message(b'LOGIN:' + public_key_to_str(self.user.public_key))

    def _add_message(self,msg):
        # TODO: Database logging of messages goes here
        self.message_buffer.append(msg)
        while (len(self.message_buffer) > MAX_NUM_SESS_MSG):
            self.message_buffer.popleft()

    def _handle_login_invalid_command(self, command, msg):
        log("CLIENT SESSION: Invalid login command from server.\n\tCOMMAND: {0}\n\tMESSAGE: {1}".format(command, msg))
        self.login_state = self.LoginState.failed

    def _handle_login_failed(self, command):
        log("CLIENT SESSION: Login Failed: {0}".format(repr(command)))
        self.login_state = self.LoginState.failed

    def _handle_login_command(self, command, msg):
        assert command.startswith(b'LOGIN')
        if self.login_state and self.login_state is not self.LoginState.failed:
            # The login command requires its own sub-state because logging in is a multi-stage activity
            if command.startswith(b'LOGIN_CHALLENGE'):
                
                if command == b'LOGIN_CHALLENGE' and self.login_state == self.LoginState.initial:
                    signature = asymmetric_sign(msg, self.user.private_key)
                    self.send_message(b'LOGIN_RESPONSE:' + signature)
                    self.login_state = self.LoginState.signing_challenge

                elif self.login_state == self.LoginState.signing_challenge:
                    
                    if command == b'LOGIN_CHALLENGE_ACK':
                        self.send_message(b'LOGIN_USERNAME:' + self.user.username)
                        self.login_state = self.LoginState.sending_username
                    
                    elif command == b'LOGIN_CHALLENGE_FAILURE':
                        self._handle_login_failed(command)
                    
                    else:
                        self._handle_login_invalid_command(command, msg)
                
                else:
                    self._handle_login_invalid_command(command, msg)
            
            elif self.login_state == self.LoginState.sending_username:
                
                if command == b'LOGIN_USERNAME_ACCEPT':
                    self.login_state = self.LoginState.successful
                    log("CLIENT SESSION: Login Successul as: {0}".format(self.user.username))
                
                elif command == b'LOGIN_USERNAME_INVALID' or command == b'LOGIN_USERNAME_TAKEN':
                    self._handle_login_failed(command)
                
                else:
                    self._handle_login_invalid_command(command, msg)
            
            else:
                self._handle_login_invalid_command(command, msg)
        
        else:
            self._handle_login_invalid_command(command, msg)

    def handle_message(self, msg):
        if msg:
            log("CLIENT SESSION: Received:\n\t{0}".format(repr(msg)))
            self._add_message(msg)

            # Separate command from the rest of the message
            s = msg.split(b':', maxsplit=1)
            command, msg = s[0], s[1]

            # Then depending on the command, get the parameters and payload
            if command.startswith(b'LOGIN'):
                self._handle_login_command(command, msg)

            elif command.startswith(b'START_CONVERSATION'):
                # TODO: handle starting a conversation
                if command == b'START_CONVERSATION':
                    pass
                elif command == b'START_CONVERSATION_CHALLENGE':
                    pass
                elif command == b'START_CONVERSATION_RESPONSE':
                    pass
                elif command == b'START_CONVERSATION_ACCEPT':
                    pass
                else:
                    self._unhandled_command(command, msg)
            elif command == b'CONVERSE':
                # TODO: handle conversation message
                pass
            else:
                self._unhandled_command(command, msg)

    def send_message(self, msg):
        log("CLIENT SESSION: Transmitting:\n\t{0}".format(repr(msg)))
        self.protocol.send_session_message(msg)