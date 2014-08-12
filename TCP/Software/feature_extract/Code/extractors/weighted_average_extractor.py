from ..FeatureExtractor import FeatureExtractor

try:
	from pylab import *
except:
	pass
from common_functions.plot_methods import plot_horizontal_line

class weighted_average_extractor(plot_horizontal_line,FeatureExtractor):
	active = True
	extname = 'weighted_average' #extractor's name
	def extract(self):
		we_av = (self.flux_data / (self.rms_data)**2).sum()/((1/self.rms_data)**2).sum()
		self.uncertainty = sqrt(1.0/(self.rms_data**(2)).sum())
#		print 'weighted',we_av
		return we_av
	def plot_feature(self,properties):
		dc_line = ones(len(self.time_data),dtype=float)
		dc_line[:] = properties[extname]
		plot(self.time_data,dc_line,label=extname)
