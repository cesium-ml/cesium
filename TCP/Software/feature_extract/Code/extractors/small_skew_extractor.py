from ..FeatureExtractor import FeatureExtractor

from pylab import *

class small_skew_extractor(FeatureExtractor):
	""" calculates the skew of the signal using the skewness formula for small samples from http://www.xycoon.com/skewness_small_sample_test_1.htm"""
	active = True
	extname = 'small_skew' #extractor's name
	minpoints = 3 # minimum number of points for the extractor to run
	def extract(self):
		skew = self.skew_calc()
		self.uncertainty = self.uncertainty_calc()
		return skew
	def skew_calc(self):
		""" simply follows http://www.xycoon.com/skewness_small_sample_test_1.htm """
		n = float(len(self.time_data))
		average = self.fetch_extr('weighted_average')
		xi_minus_average = self.flux_data - average
		cubed = xi_minus_average**3
		sum_of_cubed = cubed.sum()
		m3 = (1/n) * sum_of_cubed
		s = self.fetch_extr('s')
		skewness = (n**2 * m3) / ((n-1)*(n-2)*(s**3))
		return skewness
	def uncertainty_calc(self):
		n = float(len(self.time_data))
		ss = sqrt(6*n*(n-1)/(n-2)/(n+1)/(n+3))
		return ss
		
