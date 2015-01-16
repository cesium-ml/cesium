from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
from ..FeatureExtractor import FeatureExtractor

class n_points_extractor(FeatureExtractor):
    active = True
    extname = 'n_points' # identifier used in final extracted value dict.
    def extract(self):
        n_val = len(self.flux_data) # number of photometric points in the light curve
        return n_val
