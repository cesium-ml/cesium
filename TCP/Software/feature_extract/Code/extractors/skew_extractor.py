from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
from ..FeatureExtractor import FeatureExtractor

from scipy import stats

class skew_extractor(FeatureExtractor):
    """ calculates the skew of the signal using scipy.stats.skew
    biased skew?"""
    active = True
    extname = 'skew' #extractor's name
    def extract(self):
        skew = stats.skew(self.flux_data)
        return skew
