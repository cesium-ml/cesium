from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
from ..FeatureExtractor import InterExtractor

class dist_from_u_extractor(InterExtractor):
    active = True
    extname = 'dist_from_u' #extractor's name
    def extract(self):
        u = self.fetch_extr('weighted_average')
        sd = self.fetch_extr('wei_av_uncertainty')
        diff = self.flux_data - u
        uncer = self.rms_data + sd
        self.uncertainty = uncer
        return diff
