from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
from ..FeatureExtractor import FeatureExtractor

class wei_av_uncertainty_extractor(FeatureExtractor): ### REDUNDANT
    active = False
    extname = 'wei_av_uncertainty' #extractor's name
    def extract(self):
        uncertainty = 1.0/(self.rms_data**(2)).sum()
        return uncertainty
