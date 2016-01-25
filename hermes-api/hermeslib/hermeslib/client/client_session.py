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


class ConversationMessage(object):
    def __init__(self, index, timestamp, sha256, content):
        self.index = index
        self.timestamp = timestamp
        self.id = sha256
        self.content = content


class Conversation(object):
    class ConversationState(Enum):
        initial = 0
        challenging = 1
        signing = 2
        acknowledging_signature = 3
        generating_key = 4
        acknowledging_key = 5

    def __init__(self, conversation_id=None):
        self.users = {} # Dict of user objects indexed by id
        self.key = None
        self.messages = []
        self.id = conversation_id if conversation_id else sha256(gen_random(32))
        self.state = self.ConversationState.initial

    def add_message(self, conversation_msg):
        if conversation_msg.index > self.messages[-1].index:
            self.messages.append(conversation_msg)
        else:
            for i in reversed(range(len(self.messages))):
                msg = self.messages[i]
                if conversation_msg.index > msg.index:
                    self.messages.insert(i, conversation_msg)
                    break


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
        self.login_state = None
        self.conversations = {} # Dict containing conversation objects indexed by their ids

    def _add_message(self, msg):
        # TODO: Database logging of messages goes here
        self.message_buffer.append(msg)
        while len(self.message_buffer) > MAX_NUM_SESS_MSG:
            self.message_buffer.popleft()

    # Functions for logging in
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

    def login(self, username, public_key, private_key):
        self.user = User(public_key, private_key, username)
        self.login_state = self.LoginState.initial
        self.send_message(b'LOGIN:' + public_key_to_str(self.user.public_key))

    # Functions for starting a conversation
    def start_conversation(self, other_client_public_key):
        # Send a command to the server with a public key of the other client
        new_conversation = Conversation()
        new_conversation.conversation_state = new_conversation.ConversationState.initial
        self.send_message([b'START_CONVERSATION',
                           b':',
                           new_conversation.id,
                           b':',
                           public_key_to_str(other_client_public_key)])
        new_conversation.state = new_conversation.ConversationState.signing


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
                    s = msg.split(b':', maxsplit=1)
                    conversation_id, public_key_str = s[0], s[1]
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