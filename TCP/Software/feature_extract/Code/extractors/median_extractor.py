from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
from ..FeatureExtractor import FeatureExtractor
from numpy import median as med
from .common_functions.plot_methods import plot_horizontal_line

class median_extractor(plot_horizontal_line,FeatureExtractor):
    active = True
    extname = 'median' #extractor's name
    def extract(self):
        try:
            median = float(med(self.flux_data))
        except:
            self.ex_error("EXCEPT in medianextractor() most likely flux_data=[]")
        return(median)
