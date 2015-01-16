from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
from ..FeatureExtractor import FeatureExtractor
from numpy import std

class std_extractor(FeatureExtractor):
    active = True
    extname = 'std' #extractor's name
    def extract(self):
        return(std(self.flux_data))
