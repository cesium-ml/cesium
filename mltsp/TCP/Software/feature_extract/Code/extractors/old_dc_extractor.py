from ..FeatureExtractor import FeatureExtractor

from numpy import ones, mean
from scipy import stats
from pylab import *

class old_dc_extractor(FeatureExtractor):
    """ Old DC
    """
    active = True
    extname = 'old_dc' #extractor's name
    def extract(self):
        return(mean(self.flux_data))
    def plot_feature(self,properties):
        dc_line = ones(len(self.time_data),dtype=float)
        dc_line[:] = properties['old dc']
        plot(self.time_data,dc_line,label='old dc')
