from ..FeatureExtractor import FeatureExtractor

class min_extractor(FeatureExtractor):
	""" extracts the minimum magnitude (i.e. brightest points)"""
	active = True
	extname = 'min' #extractor's name
	def extract(self):
		try:
			min_index = self.flux_data.argmin()
			self.vplot = self.time_data[min_index] # tells plotting method where to plot this line
			minimum = self.flux_data[min_index]
		except:
			minimum = None
		return minimum
		
class max_extractor(FeatureExtractor):
	""" extracts the maximum magnitude (i.e. faintest points)"""
	active = True
	extname = 'max' #extractor's name
	def extract(self):
		try:
			max_index = self.flux_data.argmax()
			self.vplot = self.time_data[max_index] # tells plotting method where to plot this line
			maximum = self.flux_data[max_index]
		except:
			maximum = None
		return maximum
