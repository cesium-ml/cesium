from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
from ..FeatureExtractor import ContextFeatureExtractor

class ecpb_extractor(ContextFeatureExtractor):
    """the Ecliptic coordinate b (latitude) in degrees"""
    active = True
    extname = 'ecpb' #extractor's name

    def extract(self):
        posdict = self.fetch_extr('position_intermediate')

        if 'ecb' not in posdict or posdict['ecb'] is None:
            self.ex_error("bad ecb in the intermediate extractor. check install of pyephem and input coordinate")

        return posdict['ecb']
