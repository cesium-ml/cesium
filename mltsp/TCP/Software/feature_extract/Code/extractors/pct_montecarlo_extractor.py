from __future__ import absolute_import
from ..FeatureExtractor import InterExtractor

from .common_functions.plot_methods import plot_vs_frequencies


class pct_80_montecarlo_extractor(plot_vs_frequencies,InterExtractor):
	""" picks the right montecarlo cruve according to the desired significance """
	active = True
	extname = 'pct_80_montecarlo' #extractor's name
	percent_significance = 80
	def extract(self):
		self.spectra = self.fetch_extr('montecarlo')
		spectr_index = self.calc_index()
		if spectr_index == len(self.spectra):
			self.ex_error("too high degree of certainty for this number of montecarlo iteration")
		nth_spectrum = self.spectra[spectr_index]
		return nth_spectrum
	def calc_index(self):
		" will calculate the correct index for the sorted array of spectra according to the desired percent significance "
		how_many = self.spectra.shape[0]
		sign = float(self.percent_significance)
		ind_rough = sign/100.0 * how_many
		ind = int(round(ind_rough))
		return ind
class pct_90_montecarlo_extractor(pct_80_montecarlo_extractor):
	""" picks the right montecarlo cruve according to the desired significance """
	active = True
	extname = 'pct_90_montecarlo' #extractor's name
	percent_significance = 90
class pct_95_montecarlo_extractor(pct_80_montecarlo_extractor):
	""" picks the right montecarlo cruve according to the desired significance """
	active = True
	extname = 'pct_95_montecarlo' #extractor's name
	percent_significance = 95
class pct_99_montecarlo_extractor(pct_80_montecarlo_extractor):
	""" picks the right montecarlo cruve according to the desired significance """
	active = True
	extname = 'pct_99_montecarlo' #extractor's name
	percent_significance = 99
