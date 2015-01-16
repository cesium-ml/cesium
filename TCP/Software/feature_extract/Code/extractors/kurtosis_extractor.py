from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
from ..FeatureExtractor import FeatureExtractor

from scipy import stats

class kurtosis_extractor(FeatureExtractor):
    """ calculates the kurtosis of the signal using scipy.stats.kurtosis
    """
    active = True
    extname = 'kurtosis' #extractor's name
    def extract(self):
        kurtosis = stats.kurtosis(self.flux_data)
        return kurtosis
