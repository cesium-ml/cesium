from __future__ import absolute_import
from ..FeatureExtractor import InterExtractor
import numpy
from numpy import random
from scipy import fftpack, stats, optimize
try:
	from pylab import *
except:
	pass
from .common_functions import ChiSquare

class sine_fit_extractor(InterExtractor,ChiSquare):
	active = True
	extname = 'sine_fit' #extractor's name
	def extract(self):
		a = self.fetch_extr('old_dc')
		try:
			b = self.properties['amplitude'] #amplitude
		except:
			b = 1
		c = 2*numpy.pi * self.fetch_extr('first_freq') # related to amplitude
		d = 0 # x shift
		init = numpy.array([a,b,c,d])
		sine = optimize.fmin_l_bfgs_b( self.sine_fit,init,args= (self.time_data, self.flux_data, self.rms_data), approx_grad=1, bounds=[(-10,10),(10,20), (c-1/1000,c+1/1000),(0,0)])
		abcd = sine[0]
		return(abcd)
	def sine_fit(self,abcd,x,y,rms):
		fx = self.sine_wave(abcd,x)
		chi2 = numpy.power(y - fx,2)/numpy.power(rms,2)
		chi2_sum = chi2.sum()
		return chi2_sum
	def sine_wave(self,abcd,x):
		sine = abcd[0] + abcd[1]*numpy.sin(abcd[2]*x-abcd[3])
		return sine
	def plot_feature(self,properties):
		a = properties['sine_fit'][0]
		b = properties['sine_fit'][1]
		c = properties['sine_fit'][2]
		d = properties['sine_fit'][3]
		abcd = array([a,b,c,d])
		# y = a + b * sin(cx - d)
		plot(self.time_data,self.sine_wave(abcd,self.time_data),label='sine fit')
