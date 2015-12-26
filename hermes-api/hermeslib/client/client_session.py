from enum import Enum

from ..utils.logging import *
from ..crypto.crypto import *


class ClientSession(object):
    class State(Enum):
        initial = 0

    def __init__(self, key):
        self.key = key

    def data_received(self, data):
        msg = symmetric_decrypt(data, self.key)
        # TODO: Implement message handling in a session
        log("Received Message: " + msg)