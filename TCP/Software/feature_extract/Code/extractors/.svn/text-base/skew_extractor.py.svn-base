from ..FeatureExtractor import FeatureExtractor

from scipy import stats

class skew_extractor(FeatureExtractor):
	""" calculates the skew of the signal using scipy.stats.skew
	biased skew?"""
	active = True
	extname = 'skew' #extractor's name
	def extract(self):
		skew = stats.skew(self.flux_data)
		return skew