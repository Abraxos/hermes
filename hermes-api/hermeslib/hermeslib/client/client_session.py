from enum import Enum
from collections import deque
from uuid import uuid1

# from ..utils.logging import *
from ..crypto.crypto import *


MAX_NUM_SESS_MSG = 1000


class User(object):
    def __init__(self, public_key, private_key=None, username=None):
        self.public_key = public_key
        self.id = sha256(public_key_to_str(public_key))
        self.private_key = private_key
        self.username = username

    def public_key_str(self):
        return public_key_to_str(self.public_key)


class ConversationMessage(object):
    def __init__(self, index, timestamp, sha256, content):
        self.index = index
        self.timestamp = timestamp
        self.id = sha256
        self.content = content


class ClientConversation(object):
    class State(Enum):
        initial = 0
        challenging = 1
        signing = 2
        verifying_signature = 3
        awaiting_verification = 4
        awaiting_key = 5
        conversing = 6

    def __init__(self, session, initiator, recipient, conversation_id=None):
        self.me = session.user
        self.users = {initiator.id: initiator, recipient.id: recipient}
        self.key = None
        self.challenge = None
        self.session = session
        self.initiator = initiator
        self.recipient = recipient
        self.id = conversation_id if conversation_id else uuid1().bytes
        self.state = self.State.initial
        if self.me is initiator:
            self.conversation_state = self.State.initial
            msg = b':'.join([b'START_CONVERSATION', self.id,
                             recipient.public_key_str()])
            self.session.send_message(msg)
            self.state = self.State.signing
        else:
            self.state = self.State.challenging
            self.challenge = gen_random(32)
            log("RECEIVED CONVERSATION REQUEST FROM: {0}"
                .format(initiator.username))
            challenge = asymmetric_encrypt_sign(self.challenge,
                                                initiator.public_key,
                                                self.me.private_key)
            msg = b':'.join([b'START_CONVERSATION_CHALLENGE', self.id,
                             challenge])
            self.session.send_message(msg)
            self.state = self.State.verifying_signature

    def reject(self, msg):
        msg = b':'.join([b'START_CONVERSATION_REJECT', msg])
        self.session.send_message(msg)
        self._halt()

    def _handle_start_convo_key(self, msg):
        assert self.me is self.recipient
        if self.state is self.State.awaiting_key:
            self.key = asymmetric_decrypt_verify(msg, self.me.private_key,
                                                 self.initiator.public_key)
            if self.key:
                self.state = self.State.conversing
            else:
                log("REJECTING CONVERSATION: Invalid Key")
                self.reject(b'Invalid key')
        else:
            log("REJECTING CONVERSATION: Unexpected Key")
            self.reject(b'Unexpected Key')

    def _handle_start_convo_accept(self):
        assert self.me is self.initiator
        if self.state is self.State.awaiting_verification:
            self.key = gen_symmetric_key()
            key = asymmetric_encrypt_sign(self.key,
                                          self.recipient.public_key,
                                          self.me.private_key)
            msg = b':'.join([b'START_CONVERSATION_KEY', self.id, key])
            self.session.send_message(msg)
            self.state = self.State.conversing
        else:
            log("REJECTING CONVERSATION: Unexpected Accept")
            self.reject(b'Unexpected Accept')

    def _handle_start_conversation_response(self, msg):
        assert self.me is self.recipient
        if self.state is self.State.verifying_signature:
            signature = asymmetric_decrypt_verify(msg, self.me.private_key,
                                                  self.initiator.public_key)
            if signature:
                msg = b':'.join([b'START_CONVERSATION_ACCEPT', self.id])
                self.session.send_message(msg)
                self.state = self.State.awaiting_key
            else:
                log("REJECTING CONVERSATION: Failed Challenge")
                self.reject(b'Failed Challenge')
        else:
            log("REJECTING CONVERSATION: Unexpected Challenge Response")
            self.reject(b'Unexpected Challenge Response')

    def _handle_start_conversation_challenge(self, msg):
        assert self.me is self.initiator
        if self.state is self.State.signing:
            challenge = asymmetric_decrypt_verify(msg, self.me.private_key,
                                                  self.recipient.public_key)
            if challenge:
                signature = asymmetric_sign(challenge, self.me.private_key)
                r = asymmetric_encrypt_sign(signature,
                                            self.recipient.public_key,
                                            self.me.private_key)
                msg = b':'.join([b'START_CONVERSATION_RESPONSE', self.id, r])
                self.session.send_message(msg)
                self.state = self.State.awaiting_verification
            else:
                log("REJECTING CONVERSATION: Failed Challenge Verification")
                self.reject(b'Invalid challenge')
        else:
            log("REJECTING CONVERSATION: Unexpected Challenge")
            self.reject(b'Unexpected Challenge')

    def _unhandled_message(self, msg):
        if self.state is self.State.conversing:
            log("UNHANDLED CONVERSATION MESSAGE: {0}\n\tMSG: {1}\n\tINITIATOR: "
                "{2}\n\tRECIPIENT: {3}".format(self.id, msg, self.initiator.id,
                                               self.recipient.id))
        else:
            self._halt()

    def _halt(self):
        # TODO: Write a halt-conversation method that signals to the server not
        # to forward anymore new messages to this client.
        pass

    def handle_start_convo_cmd(self, cmd, msg):
        # TODO: Implement actual error handling
        if cmd == b'START_CONVERSATION_CHALLENGE':
            self._handle_start_conversation_challenge(msg)
        elif cmd == b'START_CONVERSATION_RESPONSE':
            self._handle_start_conversation_response(msg)
        elif cmd == b'START_CONVERSATION_ACCEPT':
            self._handle_start_convo_accept()
        elif cmd == b'START_CONVERSATION_KEY':
            self._handle_start_convo_key(msg)
        elif cmd == b'START_CONVERSATION_REJECT':
            self._halt()
        else:
            self._unhandled_message(msg)

    def handle_msg(self, msg):
        pass


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
        self.users = {}
        self.message_buffer = deque([])
        self.login_state = None
        self.conversations = {}  # indexed by conversation GUIDs

    def _add_message(self, msg):
        self.message_buffer.append(msg)
        while len(self.message_buffer) > MAX_NUM_SESS_MSG:
            self.message_buffer.popleft()

    # Functions for logging in
    def _handle_login_invalid_command(self, command, msg):
        log("CLIENT SESSION: Invalid login command from server.\n\t"
            "COMMAND: {0}\n\tMESSAGE: {1}".format(command, msg))
        self.login_state = self.LoginState.failed

    def _handle_login_failed(self, command):
        log("CLIENT SESSION: Login Failed: {0}".format(repr(command)))
        self.login_state = self.LoginState.failed

    def _handle_login_command(self, command, msg):
        assert command.startswith(b'LOGIN')
        if self.login_state and self.login_state is not self.LoginState.failed:
            # The login command requires its own sub-state because logging in
            # is a multi-stage activity
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
                    log("CLIENT SESSION: Login Successful as: {0}"
                        .format(self.user.username))
                elif command == b'LOGIN_USERNAME_INVALID' or command == b'LOGIN_USERNAME_TAKEN':
                    self._handle_login_failed(command)
                else:
                    self._handle_login_invalid_command(command, msg)
            else:
                self._handle_login_invalid_command(command, msg)
        else:
            self._handle_login_invalid_command(command, msg)

    def _unhandled_command(self, msg):
        log("UNHANDLED COMMAND: {0}".format(msg))

    def login(self, username, public_key, private_key):
        self.user = User(public_key, private_key, username)
        self.login_state = self.LoginState.initial
        self.send_message(b'LOGIN:' + public_key_to_str(self.user.public_key))

    def add_user(self, public_key, username=None):
        new_user = User(public_key, username=username)
        self.users[new_user.id] = new_user
        return new_user

    # Functions for starting a conversation
    def start_convo(self, other_user):
        assert self.user is not None
        log("STARTING CONVERSATION:\n\tINITIATOR: {0}({1})\n\tRECIPIENT: "
            "{2}({3})".format(self.user.username, self.user.id,
                              other_user.username, other_user.id))
        # Send a command to the server with a public key of the other client
        new_convo = ClientConversation(self, self.user, other_user)
        self.conversations[new_convo.id] = new_convo
        return new_convo

    def handle_message(self, msg):
        if msg:
            log("CLIENT SESSION({0}): Received:\n\t{1}".format(self.user.username, repr(msg)))
            self._add_message(msg)

            # Separate command from the rest of the message
            s = msg.split(b':', maxsplit=1)
            cmd, msg = s[0], s[1]

            # Then depending on the command, get the parameters and payload
            if cmd.startswith(b'LOGIN'):
                self._handle_login_command(cmd, msg)
            elif cmd.startswith(b'START_CONVERSATION'):
                if cmd == b'START_CONVERSATION':
                    s = msg.split(b':', maxsplit=1)
                    convo_id, public_key_str = s[0], s[1]

                    initiator_id = sha256(public_key_str)
                    if initiator_id in self.users:
                        initiator = self.users[initiator_id]
                    else:
                        initiator = User(public_key_from_str(public_key_str))
                    self.conversations[convo_id] = ClientConversation(self,
                                                                      initiator,
                                                                      self.user,
                                                                      convo_id)
                else:
                    s = msg.split(b':', maxsplit=1)
                    convo_id, msg = (s[0], s[1]) if len(s) == 2 else (s[0],
                                                                      None)
                    self.conversations[convo_id].handle_start_convo_cmd(cmd,
                                                                        msg)
            elif cmd == b'CONVERSE':
                s = msg.split(b':', maxsplit=1)
                convo_id, msg = (s[0], s[1]) if len(s) == 2 else (s[0], None)
                self.conversations[convo_id].handle_msg(cmd, msg)
            else:
                self._unhandled_command(cmd + msg)

    def send_message(self, msg):
        if self.user:
            log("CLIENT SESSION({0}): Transmitting:\n\t{1}"
                .format(self.user.username, repr(msg)))
            self.protocol.send_session_message(msg)
        else:
            log("CLIENT SESSION: Transmitting:\n\t{0}".format(repr(msg)))
            self.protocol.send_session_message(msg)
