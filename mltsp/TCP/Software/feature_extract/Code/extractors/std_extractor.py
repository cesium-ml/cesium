from ..FeatureExtractor import FeatureExtractor
from numpy import std

class std_extractor(FeatureExtractor):
    active = True
    extname = 'std' #extractor's name
    def extract(self):
        return(std(self.flux_data))
