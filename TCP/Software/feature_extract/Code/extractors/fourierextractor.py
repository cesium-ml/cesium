from ..FeatureExtractor import InterExtractor
import numpy
from numpy import random, round
from scipy import fftpack, stats, optimize
try:
	from pylab import *
except:
	pass
from common_functions import *
from common_functions.plot_methods import plot_vs_frequencies

class fourierextractor(plot_vs_frequencies,InterExtractor):
	active = 1
	active = False
	extname = 'fourier' #extractor's name
	def extract(self):
		self.test_even()
		#frequencies = self.frequencies #self.time_data / len(self.time_data)
		fft = fftpack.fft(self.flux_data)
		return fft
	def test_even(self):
		for x in range(len(self.time_data)-3):
			slicex = self.time_data[x:x+3] # slice with three elements
			if round((slicex[2] - slicex[1]),2) != round((slicex[1] - slicex[0]),2):
				self.ex_error("Unevenly Spaced Data")
