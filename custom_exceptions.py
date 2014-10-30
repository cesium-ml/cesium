# exceptions.py


class DataFormatError(Exception):
    '''Exception that is raised when provided time series data file 
    or header file does not conform to required formatting.
    '''
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return str(self.value)
        
class TimeSeriesFileNameError(Exception):
    '''Exception that is raised when provided time series data files 
    and header file's list of file names do not match.
    '''
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return str(self.value)
