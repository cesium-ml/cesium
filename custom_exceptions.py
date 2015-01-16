from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import str
from future import standard_library
standard_library.install_aliases()
from builtins import *
# exceptions.py


class DataFormatError(Exception):
    """TS data file or header file does not improperly formatted.
    
    Attributes
    ----------
    value : str
        The exception message.
    
    """
    
    def __init__(self,value):
        self.value = value
    
    def __str__(self):
        return str(self.value)


class TimeSeriesFileNameError(Exception):
    """Provided TS data file name(s) missing from header file.
    
    Attributes
    ----------
    value : str
        The exception message.
    
    """
    
    def __init__(self,value):
        self.value = value
    
    def __str__(self):
        return str(self.value)
