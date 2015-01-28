from ..FeatureExtractor import FeatureExtractor

from scipy import optimize
from common_functions import ChiSquare
from common_functions.plot_methods import plot_horizontal_line


class dc_extractor(plot_horizontal_line,FeatureExtractor,ChiSquare):
	active = True
	extname = 'dc' #extractor's name
	def extract(self):
#		print 'xdata',self.time_data,'ydata', self.flux_data,'rms_data',self.rms_data
		dc = optimize.fminbound(self.weighted_average,-10,10,args=(self.time_data,self.flux_data,self.rms_data))
		# KLUDGY 20090810: (on some systems optimizes.fminbound returns an array, other ones it returns a numpy.float). The least painful fix is this:
		try:
			return(dc[0])
		except:
			return(dc)
	def weighted_average(self,u,x,y,rms):
		def average(x):
			dc = x.copy()
			dc[:] = u
			return dc
		return self.chi_square_sum(y,average,x=x,rms=rms)
