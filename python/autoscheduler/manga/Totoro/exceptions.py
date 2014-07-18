# Exceptions for pyPhotom classes and functions

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


class TotoroError(Exception):
    """Base exception for Totoro. Other exceptions should inherit this."""
    pass


class TotoroNotImplemented():
    """A class for exceptions about functionalities not yet implemented."""
    pass


class TotoroWarning(Warning):
    """Base warning for Totoro."""
    pass

class TotoroUserWarning(UserWarning, TotoroWarning):
    """The primary warning class."""
    pass


class FieldWarning(TotoroWarning):
    """A warning for Field."""
    pass
