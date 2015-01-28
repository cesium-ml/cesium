from ..FeatureExtractor import InterExtractor
from numpy import sqrt

class s_extractor(InterExtractor):
	""" extracts the values s as shown in http://www.xycoon.com/peakedness_small_sample_test_1.htm for example
	This is used by small_kurtosis_extractor"""
	active = True
	extname = 's' #extractor's name
	minpoints = 2 # minimum number of points for the extractor to run
	def extract(self):
		n = float(self.fetch_extr('n_points'))
		average = self.fetch_extr('weighted_average')
		xi_minus_average = self.flux_data - average
		squared = xi_minus_average**2
		sum_of_squared = squared.sum()
		s = sqrt((1/(n-1)) * sum_of_squared)
		return s
