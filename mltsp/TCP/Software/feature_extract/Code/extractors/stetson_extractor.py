import os,sys
from ..FeatureExtractor import FeatureExtractor

from .....Algorithms.stetson_stats import stetson_mean, stetson_j, stetson_k


class stetson_mean_extractor(FeatureExtractor):
    """ An iteratively weighted mean"""
    active = True
    extname = 'stetson_mean' #extractor's name
    def extract(self):
        value = stetson_mean(self.flux_data)
        return value


class stetson_j_extractor(FeatureExtractor):
    """Robust covariance statistic between pairs of observations x,y
       whose uncertainties are dx,dy.  if y is not given, calculates
       a robust variance for x."""
    active = True
    extname = 'stetson_j' #extractor's name
    minpoints = 2 # minimum number of points for the extractor to run
    def extract(self):
        value = stetson_j(self.flux_data)
        return value


class stetson_k_extractor(FeatureExtractor):
    """A kurtosis statistic."""
    active = True
    extname = 'stetson_k' #extractor's name
    minpoints = 2 # minimum number of points for the extractor to run
    def extract(self):
        value = stetson_k(self.flux_data)
        return value
