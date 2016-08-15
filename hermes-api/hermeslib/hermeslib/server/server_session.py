from enum import Enum
from collections import deque
# import time
#
# from ..utils.logging import *
# from ..crypto.crypto import *
from ..server.users import *


MAX_NUM_SESS_MSG = 500


class ServerConversation(object):
    # TODO: Add some kind of END_CONVERSATION signal
    def __init__(self, conversation_id, session, initiator, recipient):
        self.id = conversation_id
        self.initiator_session = session
        self.recipient_session = recipient.conversation_starter_session()
        self.users = {initiator.id: initiator, recipient.id: recipient}

    def transmit_init_message(self, initiator):
        initiator_pubkey_str = initiator.public_key_str()
        msg = b':'.join([b'START_CONVERSATION', self.id, initiator_pubkey_str])
        self.recipient_session.send_message(msg)

    def _unhandled_command(self, session, cmd, msg):
        log("SERVER CONVERSATION({0}): WARNING - Unhandled conversation "
            "command.\n\tUSER: {1} {2}\n\tCMD: {3}\n\tMSG: {4}"
            .format(self.id, session.user.username, session.protocol.peer,
                    cmd, msg))
        session.send_message("UNHANDLED_COMMAND:")

    def handle_start_convo_cmd(self, session, cmd, msg):
        # TODO: As of right now, assertions are used in place of real error handling, this needs to be fixed.
        if cmd == b'START_CONVERSATION_CHALLENGE':
            assert session is self.recipient_session
            msg = b':'.join([cmd, self.id, msg])
            self.initiator_session.send_message(msg)
        elif cmd == b'START_CONVERSATION_RESPONSE':
            assert session is self.initiator_session
            msg = b':'.join([cmd, self.id, msg])
            self.recipient_session.send_message(msg)
        elif cmd == b'START_CONVERSATION_ACCEPT':
            assert session is self.recipient_session
            msg = b':'.join([cmd, self.id])
            self.initiator_session.send_message(msg)
        elif cmd == b'START_CONVERSATION_KEY':
            assert session is self.initiator_session
            msg = b':'.join([cmd, self.id, msg])
            self.recipient_session.send_message(msg)
        elif cmd == b'START_CONVERSATION_REJECT':
            msg = b':'.join([cmd, self.id, msg])
            if session is self.initiator_session:
                self.recipient_session.send_message(msg)
            elif session is self.recipient_session:
                self.initiator_session.send_message(msg)
            # TODO: Delete this conversation object
        else:
            self._unhandled_command(session, cmd, msg)

    def handle_message(self, session, msg):
        # TODO: handle conversation messages
        # TODO: Send the message to all other sessions
        pass


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
        self.conversations = {}
        if key:
            self.key = key
        else:
            self.key = gen_symmetric_key()

    def user_list(self):  # TODO: Turn this into a property
        return self.protocol.factory.user_list

    def _add_message(self,msg):
        # TODO: Database logging of messages goes here
        self.message_buffer.append(msg)
        while len(self.message_buffer) > MAX_NUM_SESS_MSG:
            self.message_buffer.popleft()

    def _unhandled_command(self, command, msg):
        log("SERVER SESSION({0}): WARNING - Unhandled session command.\n\t"
            "{1}\n\t{2}".format(self.protocol.peer, command, msg))
        self.send_message("UNHANDLED_COMMAND:")

    def _valid_username(self, username):
        # TODO: Implement and document what a valid username should be
        return True if username else False

    def send_message(self, msg):
        log("SERVER SESSION({0}): Transmitting:\n\t{1}"
            .format(self.protocol.peer, repr(msg)))
        self.protocol.send_session_message(msg)

    # Functions for handling a user logging in
    def _handle_login_command(self, command, msg):
        # The login command requires its own sub-state because logging in is a
        # multi-stage activity
        if command == b'LOGIN':
            self.login_state = self.LoginState.initial
            self.user_key = public_key_from_str(msg)
            self.challenge = Random.get_random_bytes(32)
            self.send_message(b'LOGIN_CHALLENGE:' + self.challenge)
            self.login_state = self.LoginState.verifying_challenge

        elif command == b'LOGIN_RESPONSE' and self.login_state \
                and self.login_state == self.LoginState.verifying_challenge:
            assert self.user_key
            signature = msg
            if asymmetric_verify(signature, self.challenge, self.user_key):
                self.send_message(b'LOGIN_CHALLENGE_ACK:')
                self.login_state = self.LoginState.receiving_username
            else:
                self._handle_login_challenge_failure(signature)

        elif command == b'LOGIN_USERNAME' and self.login_state \
                and self.login_state == self.LoginState.receiving_username:
            assert self.user_key
            username = msg
            if self._valid_username(username):
                user = self.user_list().get_user_by_username(username)
                if user:
                    if self.user_key is user.public_key:
                        user.username = username
                        user.protocols[self.protocol.id()] = self.protocol
                        self.send_message(b'LOGIN_USERNAME_ACCEPT:')
                        self.login_state = self.LoginState.login_verified
                    else:
                        self._handle_login_username_taken(username)
                else:
                    self.user = User(self.user_key, username)
                    self.user.protocols[self.protocol.id()] = self.protocol
                    self.protocol.factory.user_list.add(self.user)
                    log("SERVER SESSION({0}): New User Login.\n\tUSERNAME: {1}"
                        "\n\tPUBLIC_KEY: {2}".format(self.protocol.peer,
                                                     username, self.user_key))
                    self.send_message(b'LOGIN_USERNAME_ACCEPT:')
                    self.login_state = self.LoginState.login_verified
            else:
                self._handle_invalid_login_username(username)
        else:
            self._handle_invalid_login_command(command, msg)

    def _handle_invalid_login_command(self, command, msg):
        log("SERVER SESSION({0}): WARNING - Invalid login command.\n\t{1}:{2}".format(self.protocol.peer, command, msg))
        self.send_message("LOGIN_COMMAND_INVALID:")
        del self.login_state

    def _handle_invalid_login_username(self, username):
        log("SERVER SESSION({0}): WARNING - User attempted to login with "
            "invalid username.\n\tUSERNAME: {1}\n\tPUBLIC_KEY: {2}"
            .format(self.protocol.peer, username, self.user_key))
        self.send_message(b'LOGIN_USERNAME_INVALID:')
        del self.login_state

    def _handle_login_username_taken(self, username):
        log("SERVER SESSION({0}): WARNING - User attempted to login with "
            "existing username.\n\tUSERNAME: {1}\n\tPUBLIC_KEY: {2}"
            .format(self.protocol.peer, username, self.user_key))
        self.send_message(b'LOGIN_USERNAME_TAKEN:')
        del self.login_state

    def _handle_login_challenge_failure(self, signature):
        log("SERVER SESSION({0}): WARNING - Invalid challenge signature.\n\t{1}"
            .format(self.protocol.peer, signature))
        self.send_message(b'LOGIN_CHALLENGE_FAILURE')
        del self.login_state

    def _handle_start_conversation_command(self, cmd, msg):
        if cmd == b'START_CONVERSATION':
            s = msg.split(b':', maxsplit=1)
            convo_id, public_key_str = s[0], s[1]
            recipient = self.user_list().get_user_by_id(sha256(public_key_str))
            new_convo = ServerConversation(convo_id, self, self.user, recipient)
            # Add the conversation to this session's list
            self.conversations[convo_id] = new_convo
            # Add the conversation to the recipient session's list
            new_convo.recipient_session.conversations[convo_id] = new_convo
            new_convo.transmit_init_message(self.user)
        else:
            s = msg.split(b':', maxsplit=1)
            assert len(s) == 2 or len(s) == 1
            convo_id, msg = (s[0], s[1]) if len(s) == 2 else (s[0], None)
            self.conversations[convo_id].handle_start_convo_cmd(self, cmd, msg)

    def handle_message(self, msg):
        if msg:
            log("SERVER SESSION({0}): Received\n\t{1}"
                .format(self.protocol.peer, repr(msg)))
            self._add_message(msg)

            # Separate command from the rest of the message
            s = msg.split(b':', maxsplit=1)
            command, msg = s[0], s[1]

            # Then depending on the command, get the parameters and payload
            if command.startswith(b'LOGIN'):
                self._handle_login_command(command, msg)
            elif command.startswith(b'START_CONVERSATION'):
                self._handle_start_conversation_command(command, msg)
            elif command == b'CONVERSE':
                # TODO: handle conversation message
                pass
            else:
                self._unhandled_command(command, msg)