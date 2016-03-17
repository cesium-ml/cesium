class DataFormatError(Exception):

    """TS data file or header file does not improperly formatted.

    Attributes
    ----------
    value : str
        The exception message.

    """

    def __init__(self, value):
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

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)
