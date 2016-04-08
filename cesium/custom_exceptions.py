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

