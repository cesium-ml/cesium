from ..FeatureExtractor import FeatureExtractor

class ratio21(FeatureExtractor):
	""" Computes the ratio from the second frequency to the first frequency"""
	active = True
	extname = 'ratio21' #extractor's name
	topex = 'second'
	bottomex = 'first_freq'
	def extract(self):
		top = self.fetch_extr(self.topex)
		bottom = self.fetch_extr(self.bottomex)
		result = top/bottom
		return result
class ratio31(ratio21):
	""" Computes the ratio from the third frequency to the first frequency"""
	active = True
	extname = 'ratio31' #extractor's name
	topex = 'third'
	bottomex = 'first_freq'
class ratio32(ratio21):
	""" Computes the ratio from the third frequency to the second frequency"""
	active = True
	extname = 'ratio32' #extractor's name
	topex = 'third'
	bottomex = 'second'
