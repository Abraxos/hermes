from ..utils.logging import *
from ..crypto.crypto import *


class User(object):
    def __init__(self, public_key, username):
        self.public_key = public_key
        self.id = public_key_sha256(self.public_key)
        self.username = username
        self.protocols = {}

    def deliver_conversation_message(self, msg):
        for protocol_id in self.protocols:
            protocol = self.protocols[protocol_id]
            if protocol.session:
                protocol.session.send_message(msg)


class UserList(object):
    def __init__(self, users = None):
        self.users_by_id = {x.id: x for x in users} if users else {} # convert the list to a dictionary keyed by ID
        self.users_by_username = {x.username: x for x in users} if users else {}

    def add(self, user):
        self.users_by_id[user.id] = user
        self.users_by_username[user.username] = user

    def username_exists(self, username):
        return username in self.users_by_username

    def get_user_by_username(self, username):
        if self.username_exists(username):
            return self.users_by_username[username]