from __future__ import absolute_import
from ..FeatureExtractor import InterExtractor
from .common_functions.plot_methods import plot_vs_frequencies
from numpy import select

class significant_80_power_extractor(plot_vs_frequencies,InterExtractor):
	""" removes noise power from the periodogram """
	active = True
	percent_significance  = 80
	extname = 'significant_80_power'
	def noise_p(self): #noise power
		pct_montecarlo_extractor = 'pct_80_montecarlo'
		return pct_montecarlo_extractor
	def extract(self):
		power = self.fetch_extr('power')
		noise = self.fetch_extr(self.noise_p())
		subtract = power - noise
		#>>> from numpy import *
		#>>> x = array([5., -2., 1., 0., 4., -1., 3., 10.])
		#>>> select([x < 0, x == 0, x <= 5], [x-0.1, 0.0, x+0.2], default = 100.)
		#array([   5.2,   -2.1,    1.2,    0. ,    4.2,   -1.1,    3.2,  100. ])
		result = select([subtract < 0],[0],default = subtract)
		return result
class significant_90_power_extractor(significant_80_power_extractor):
	percent_significance = 90
	extname = 'significant_90_power'
	def noise_p(self):
		pct_montecarlo_extractor = 'pct_90_montecarlo'
		return pct_montecarlo_extractor
class significant_95_power_extractor(significant_80_power_extractor):
	percent_significance = 95
	extname = 'significant_95_power'
	def noise_p(self):
		pct_montecarlo_extractor = 'pct_95_montecarlo'
		return pct_montecarlo_extractor
class significant_99_power_extractor(significant_80_power_extractor):
	percent_significance = 99
	extname = 'significant_99_power'
	def noise_p(self):
		pct_montecarlo_extractor = 'pct_99_montecarlo'
		return pct_montecarlo_extractor
