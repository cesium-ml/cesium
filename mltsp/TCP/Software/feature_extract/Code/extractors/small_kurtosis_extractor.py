from ..FeatureExtractor import FeatureExtractor

from numpy import *

class small_kurtosis_extractor(FeatureExtractor):
	""" calculates the kurtosis of the signal using the kurtosis formula for small samples from http://www.xycoon.com/peakedness_small_sample_test_1.htm"""
	active = True
	extname = 'small_kurtosis' #extractor's name
	minpoints = 4 # minimum number of points for the extractor to run
	def extract(self):
		kurtosis = self.kurtosis_calc()
		self.uncertainty = self.uncertainty_calc()
		return kurtosis
	def kurtosis_calc(self):
		""" simply follows http://www.xycoon.com/skewness_small_sample_test_1.htm """
		n = float(self.fetch_extr('n_points'))
		average = self.fetch_extr('weighted_average')
		s = self.fetch_extr('s')
		xi_minus_average = self.flux_data - average
		xi_minus_average_over_s = xi_minus_average / s
		to_the_fourth = power(xi_minus_average_over_s,4)
		sum_fourth_s = to_the_fourth.sum()
		kurtosis = ( n*(n+1)/((n-1)*(n-2)*(n-3)) ) * sum_fourth_s - 3*(n-1)**2 / ((n-2) * (n-3))
		return kurtosis
	def uncertainty_calc(self):
		n = float(self.fetch_extr('n_points'))
		ss = sqrt(6*n*(n-1)/(n-2)/(n+1)/(n+3))
		sk = sqrt(4*(n**2-1)*(ss**2)/(n-3)/(n+5))
		return sk
