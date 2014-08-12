from ..FeatureExtractor import FeatureExtractor
from numpy import std

class stdextractor(FeatureExtractor):
	active = True
	extname = 'std' #extractor's name
	def extract(self):
		return(std(self.flux_data))
