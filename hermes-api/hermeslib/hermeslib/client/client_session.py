from enum import Enum

from ..utils.logging import *
from ..crypto.crypto import *

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

    def __init__(self, key, protocol):
        self.key = key
        self.protocol = protocol
        self.user = None

    def login(self, username, public_key, private_key):
    	self.user = User(public_key, private_key, username)
    	self.login_state = self.LoginState.initial
    	self.send_message(b'LOGIN:' + public_key_to_str(self.user.public_key))

    def handle_message(self, msg):
        # TODO: Implement message handling in a session
        log("CLIENT SESSION: Received:\n\t{0}".format(repr(msg)))

    def send_message(self, msg):
    	log("CLIENT SESSION: Transmitting:\n\t{0}".format(repr(msg)))
    	self.protocol.send_session_message(msg)