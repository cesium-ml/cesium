from ..FeatureExtractor import FeatureExtractor

from numpy import median

class median_absolute_deviation_extractor(FeatureExtractor):
	""" MAD: Median Absolute Deviation : median(abs(mag[] - median(mag[])))
	"""
	active = True
	extname = 'median_absolute_deviation' #extractor's name
	def extract(self):
		mad = median(abs(self.flux_data - median(self.flux_data)))
		return mad

