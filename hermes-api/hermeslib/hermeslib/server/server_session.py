from enum import Enum
from collections import deque
import time

from ..utils.logging import *
from ..crypto.crypto import *
from ..server.users import *


MAX_NUM_SESS_MSG = 500


class ServerSession(object):
    class State(Enum):
        initial = 0
    class LoginState(Enum):
        initial = 0
        verifying_challenge = 1
        receiving_username = 2
        login_verified = 3

    def __init__(self, protocol, key=None):
        self.user = None
        self.protocol = protocol
        self.challenge = None
        self.state = self.State.initial
        self.message_buffer = deque([])
        if key:
            self.key = key
        else:
            self.key = gen_symmetric_key()

    def _add_message(self,msg):
        # TODO: Database logging of messages goes here
        self.message_buffer.append(msg)
        while (len(self.message_buffer) > MAX_NUM_SESS_MSG):
            self.message_buffer.popleft()

    def _unhandled_command(self, command, msg):
        log("SERVER SESSION({0}): WARNING - Unhandled session command.\n\t{1}\n\t{2}".format(self.protocol.peer, command, msg))
        self.send_message("UNHANDLED_COMMAND:")

    def _handle_invalid_login_command(self, command, msg):
        log("SERVER SESSION({0}): WARNING - Invalid login command.\n\t{1}:{2}".format(self.protocol.peer, command, msg))
        self.send_message("LOGIN_COMMAND_INVALID:")
        del self.login_state

    def _handle_invalid_login_username(self, username):
        log("SERVER SESSION({0}): WARNING - User attempted to login with invalid username.\n\tUSERNAME: {1}\n\tPUBLIC_KEY: {2}".format(self.protocol.peer, username, self.user_key))
        self.send_message(b'LOGIN_USERNAME_INVALID:')
        del self.login_state

    def _handle_login_username_taken(self, username):
        log("SERVER SESSION({0}): WARNING - User attempted to login with existing username.\n\tUSERNAME: {1}\n\tPUBLIC_KEY: {2}".format(self.protocol.peer, username, self.user_key))
        self.send_message(b'LOGIN_USERNAME_TAKEN:')
        del self.login_state

    def _handle_login_challenge_failure(self, signature):
        log("SERVER SESSION({0}): WARNING - Invalid challenge signature.\n\t{1}".format(self.protocol.peer, signature))
        self.send_message(b'LOGIN_CHALLENGE_FAILURE')
        del self.login_state

    def _valid_username(self, username):
        # TODO: Implement and document what a valid username should be
        return True

    def send_message(self, msg):
        log("SERVER SESSION({0}): Transmitting:\n\t{1}".format(self.protocol.peer, repr(msg)))
        self.protocol.send_session_message(msg)

    def _handle_login_command(self, command, msg):
        # The login command requires its own sub-state because logging in is a multi-stage activity
        if command == b'LOGIN':
            self.login_state = self.LoginState.initial
            self.user_key = public_key_from_str(msg)
            self.challenge = Random.get_random_bytes(32)
            self.send_message(b'LOGIN_CHALLENGE:' + self.challenge)
            self.login_state = self.LoginState.verifying_challenge

        elif command == b'LOGIN_RESPONSE' and self.login_state and self.login_state == self.LoginState.verifying_challenge:
            assert self.user_key
            signature = msg
            if asymmetric_verify(signature, self.challenge, self.user_key):
                self.send_message(b'LOGIN_CHALLENGE_ACK:')
                self.login_state = self.LoginState.receiving_username
            else:
                self._handle_login_challenge_failure(signature)

        elif command == b'LOGIN_USERNAME' and self.login_state and self.login_state == self.LoginState.receiving_username:
            assert self.user_key
            username = msg
            if self._valid_username(username):
                user = self.protocol.factory.user_list.get_user_by_username(username)
                if user:
                    if self.user_key is user.public_key:
                        user.username = username
                        user.protocols[self.protocol.id()] = self.protocol
                        self.send_message(b'LOGIN_USERNAME_ACCEPT:')
                        self.login_state = self.LoginState.login_verified
                    else:
                        self._handle_login_username_taken(username)
                else:
                    user = User(self.user_key, username)
                    user.protocols[self.protocol.id()] = self.protocol
                    self.protocol.factory.user_list.add(user)
                    log("SERVER SESSION({0}): New User Login.\n\tUSERNAME: {1}\n\tPUBLIC_KEY: {2}".format(self.protocol.peer, username, self.user_key))
                    self.send_message(b'LOGIN_USERNAME_ACCEPT:')
                    self.login_state = self.LoginState.login_verified
            else:
                self._handle_invalid_login_username(username)
        else:
            self._handle_invalid_login_command(command, msg)

    def handle_message(self, msg):
        if msg:
            log("SERVER SESSION({0}): Received\n\t{1}".format(self.protocol.peer, repr(msg)))
            self._add_message(msg)

            # Separate command from the rest of the message
            s = msg.split(b':', maxsplit=1)
            time.sleep(5)
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