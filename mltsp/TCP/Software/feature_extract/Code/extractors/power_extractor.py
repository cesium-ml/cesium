from __future__ import absolute_import
from ..FeatureExtractor import InterExtractor
from .common_functions.plot_methods import plot_vs_frequencies

class power_extractor(plot_vs_frequencies,InterExtractor):
	""" extracts a periodogram, chooses either a lomb or fft extraction method """
	active = True
	extname = 'power'
	def extract(self):
		self.longenough()
		if 0:#self.iseven(): # determines if the data is evenly sampled / commented out assuming all our data is uneven
			#print "Evenly sampled data detected"
			result = self.fetch_extr('power_spectrum')
		else: # otherwise use lomb-scargle
			#print "Unevenly sampled data detected"
			power = self.fetch_extr('lomb')
			result = power
		return result
	def longenough(self):
		try:
			if len(self.flux_data) < 5: # if 4 or less points, error
				self.ex_error("not enough data points")
			return None
		except:
			self.ex_error("not enough data points")
			
	def iseven(self):
		iseven = True
		for x in range(len(self.time_data)-3):
			slicex = self.time_data[x:x+3] # slice with three elements
			if round((slicex[2] - slicex[1]),2) != round((slicex[1] - slicex[0]),2):
				iseven = False
				break
		return iseven
