from ..FeatureExtractor import InterExtractor
import numpy
from scipy import optimize
from common_functions import ChiSquare

class linear_extractor(InterExtractor,ChiSquare): # fits ax+b	
	''' produces a linear fit, returns in the format 'a(slope), b (y-intercept) '''
	active = True
	extname = 'linear' #extractor's name
	def extract(self):
		a = 0
		b = 0
		init = numpy.array([a,b])
		linear = optimize.fmin(self.linear_fit,init,args=(self.time_data,self.flux_data,self.rms_data),disp=0)
		return(linear)
	def linear_fit(self,ab,x,y,rms):
		def linear(x):
			return ab[0]*x +ab[1]
		return self.chi_square_sum(y,linear,x=x,rms=rms)
	def plot_feature(self,properties):
		plot( self.time_data,properties[self.extname][1]+ properties[self.extname][0]* self.time_data, label=self.extname)
