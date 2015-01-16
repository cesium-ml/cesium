from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
from blinker.base import (
    ANY,
    NamedSignal,
    Namespace,
    Signal,
    receiver_connected,
    signal,
)

__all__ = [
    'ANY',
    'NamedSignal',
    'Namespace',
    'Signal',
    'receiver_connected',
    'signal',
    ]


__version__ = '1.1'
