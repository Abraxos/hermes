"""Common utilities for the Hermes Messaging System"""
from __future__ import print_function
from sys import stderr
from collections import namedtuple
from enum import IntEnum
from msgpack import packb
from msgpack import unpackb
from msgpack.exceptions import ExtraData
from msgpack.exceptions import UnpackException
from msgpack.exceptions import UnpackValueError

class LogLevel(IntEnum):
    """An enum representing logging information verbosity levels"""
    NONE = 0
    ERROR = 1
    WARNING = 2
    INFO = 3
    VERBOSE = 4
    DEBUG = 5

# Configuration Globals (Can be set in other modules using this one)
LOG_LEVEL = LogLevel.DEBUG

def pack_values(**kwargs):
    """Pack message as an msgpack dictionary"""
    return packb(kwargs, use_bin_type=True)

def pack(msg):
    """Pack message as an msgpack binary"""
    return packb(msg, use_bin_type=True)

def unpack(msg):
    """Unpack msgpack message"""
    try:
        result = unpackb(msg, use_list=False, encoding='utf-8')
    except (ExtraData, UnpackException, UnpackValueError):
        result = None
    return result
#
# HermesIDMessage = namedtuple('ZeusMessage', ['msg_type', 'subject', 'packed_object'])

TransmittedModel = namedtuple('TransmittedModel', ['model_id', 'variables'])

# def unpack_object(msg):
#     """Unpacks a msgpack-ed message into a ZeusMessage"""
#     msg_dict = unpack(msg)
#     if isinstance(msg_dict, dict):
#         return ZeusMessage(**msg_dict)
#     else:
#         return None

def log(msg, log_level=LogLevel.DEBUG):
    """Logs a given message at a given verbosity level"""
    if LOG_LEVEL >= log_level:
        print(str(msg), file=stderr)

def log_debug(msg): log(msg, LogLevel.DEBUG)
def log_verbose(msg): log(msg, LogLevel.VERBOSE)
def log_info(msg): log(msg, LogLevel.INFO)
def log_warning(msg): log(msg, LogLevel.WARNING)
def log_error(msg): log(msg, LogLevel.ERROR)

# Type checking decorators from: https://www.python.org/dev/peps/pep-0318/#examples
def accepts(*types):
    """A type checking decorator that enforces the types that a function accepts"""
    def check_accepts(func):
        """A check for accepted types"""
        assert len(types) == func.func_code.co_argcount, \
                "number of args for %s does not match" % func.__name__
        def new_f(*args, **kwds):
            """Generated function that does the type assertions"""
            for (arg, typ) in zip(args, types):
                assert isinstance(arg, typ), \
                       "arg %r(%s) for function %s does not match %s" % \
                       (arg, typeof(arg), func.__name__, typ)
            return func(*args, **kwds)
        new_f.func_name = func.func_name
        return new_f
    return check_accepts

def returns(rtype):
    """A type checking decorator that enforces the types that a function returns"""
    def check_returns(func):
        """A check for returned types"""
        def new_f(*args, **kwds):
            """Generated function that does type assertions"""
            result = func(*args, **kwds)
            assert isinstance(result, rtype), \
                   "return value %r does not match %s" % (result, rtype)
            return result
        new_f.func_name = func.func_name
        return new_f
    return check_returns
