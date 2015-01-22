from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
from ..FeatureExtractor import FeatureExtractor

from numpy import median

class median_absolute_deviation_extractor(FeatureExtractor):
    """ MAD: Median Absolute Deviation : median(abs(mag[] - median(mag[])))
    """
    active = True
    extname = 'median_absolute_deviation' #extractor's name
    def extract(self):
        mad = median(abs(self.flux_data - median(self.flux_data)))
        return mad
