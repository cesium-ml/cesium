from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
from ..FeatureExtractor import FeatureExtractor

class psd_example_extractor(FeatureExtractor):
    """ Example use of the first freq LombScargle derived PSD
    """
    active = True
    extname = "psd_example"
    def extract(self):
        lomb_dict = self.fetch_extr('lomb_scargle')
        psd = lomb_dict.get('freq1_psd',[])
        f0 = lomb_dict.get('freq1_f0',0.)
        df = lomb_dict.get('freq1_df',0.)
        numf = lomb_dict.get('freq1_numf',0.)
        return f0*df*numf + sum(psd)
