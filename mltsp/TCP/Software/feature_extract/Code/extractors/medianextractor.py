from ..FeatureExtractor import FeatureExtractor
from numpy import median as med
from common_functions.plot_methods import plot_horizontal_line

class medianextractor(plot_horizontal_line,FeatureExtractor):
	active = True
	extname = 'median' #extractor's name
	def extract(self):
		try:
			median = float(med(self.flux_data))
		except:
			self.ex_error("EXCEPT in medianextractor() most likely flux_data=[]")
		return(median)
