from __future__ import print_function
from ..FeatureExtractor import MultiFeatureExtractor

class ratioRUfirst_extractor(MultiFeatureExtractor):
	""" calculates the ratio of the first frequency in the V band to the U band """
	active = False
	extname = 'ratioRUfirst' #extractor's name
	band1 = 'r'
	band2 = 'u'
	compared_extr = 'first_freq'
	def extract(self):
		self.extr1 = self.extr1 # just a reminder
		self.extr2 = self.extr2 # just a reminder
		ratioRU = self.extr1 / self.extr2
		print("ratioRU", ratioRU)
		print("band",self.band)
		return ratioRU