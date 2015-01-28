from ..FeatureExtractor import FeatureExtractor

from scipy import stats

class kurtosis_extractor(FeatureExtractor):
	""" calculates the kurtosis of the signal using scipy.stats.kurtosis
	"""
	active = True
	extname = 'kurtosis' #extractor's name
	def extract(self):
		kurtosis = stats.kurtosis(self.flux_data)
		return kurtosis
