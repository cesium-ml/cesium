from ..FeatureExtractor import FeatureExtractor
from common_functions import plot_methods

from common_functions.plot_methods import plot_vertical_line

class first_freq_extractor(plot_vertical_line,FeatureExtractor): 
	"""grabs the highest frequency from an fft or lomb power spectrum"""
	active = True
	extname = 'first_freq' #extractor's name
	def extract(self):
		power = self.fetch_extr('power')
		freqs = self.frequencies
		max_index = power[1:].argmax() + 1 #power[1:len(power)/2+1].argmax() + 1
		max_freq = freqs[max_index]
		#20080123dstarr comments: #assert max_freq < 0.5, "maximum frequency higher than 0.5"
#		print "max_freq", max_freq, type(max_freq)
		return max_freq
