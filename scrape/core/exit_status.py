from enum import IntEnum, unique


@unique
class ExitStatus(IntEnum):
    """Program exit status code constants."""

    SUCCESS = 0
    ERROR = 1
    ERROR_TIMEOUT = 2

    # Control-C is fatal error signal 2, (130 = 128 + 2)
    # <http://www.tldp.org/LDP/abs/html/exitcodes.html>
    ERROR_CTRL_C = 130
