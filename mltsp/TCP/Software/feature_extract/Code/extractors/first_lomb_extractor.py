from __future__ import absolute_import
from ..FeatureExtractor import FeatureExtractor

from .first_freq_extractor import first_freq_extractor
from .common_functions.plot_methods import plot_vertical_line

class first_lomb_extractor(first_freq_extractor):
	""" extracts the first frequency from the lomb periodogram"""
	active = False
	extname = 'first_lomb' #extractor's name
	def extract(self):
		power = self.fetch_extr('lomb')
		freqs = self.frequencies
		max_index = power[1:].argmax() + 1
		max_freq = freqs[max_index]#freqs[max_index]
		return max_freq
