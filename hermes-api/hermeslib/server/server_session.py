from enum import Enum

from ..utils.logging import *
from ..crypto.crypto import *


class ServerSession(object):
    class State(Enum):
        initial = 0

    def __init__(self, key=None):
        self.user = None
        if key:
            self.key = key
        else:
            self.key = gen_symmetric_key()

    def data_received(self, data):
        msg = symmetric_decrypt(data, self.key)
        # TODO: Implement message handling in a session
        log("Received Message: " + msg)