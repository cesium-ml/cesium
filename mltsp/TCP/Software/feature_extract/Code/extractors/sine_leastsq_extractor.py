from __future__ import absolute_import
from ..FeatureExtractor import InterExtractor
import numpy
from numpy import random, pi
from scipy import fftpack, stats, optimize
try:
	from pylab import *
except:
	pass
from .common_functions import *

class sine_leastsq_extractor(InterExtractor,ChiSquare):
	active = True
	extname = 'sine_leastsq' #extractor's name
	def extract(self):
		a = self.dc_estimate()
		b = 15#properties['amplitude'] #amplitude
		c = self.frequency_estimate() * 2 * pi
		d = 0 # x shift
		init = numpy.array([a,b,c,d])
#		print 'real', 'a:', properties['dc_real'], 'b:', properties['amplitude'], 'c:', 2* numpy.pi / properties['period']
		sine = optimize.leastsq(self.sine_fit,init,args=(self.time_data,self.flux_data,self.rms_data))
		return(sine[0])
#	def sine_fit(self,abcd,x,y,rms):
#		def sine(x):
#			# y = a + b * sin(cx - d)
#			return abcd[0] + abcd[1]*numpy.sin(abcd[2]*x-abcd[3])#ab[0]*x +ab[1]
#		print self.chi_square(y,sine,x=x,rms=rms)	
#		return self.chi_square(y,sine,x=x,rms=rms)
	def frequency_estimate(self):
		freq = self.fetch_extr('first_freq') #2*numpy.pi/20
		return freq
	def dc_estimate(self):
		dc = self.fetch_extr('weighted_average')
		return dc
	def sine_fit(self,abcd,x,y,rms):
		fx = self.sine_wave(abcd,x)
		chi2 = numpy.power(y - fx,2)/numpy.power(rms,2)
		return chi2
	def sine_wave(self,abcd,x):
		sine = abcd[0] + abcd[1]*numpy.sin(abcd[2]*x-abcd[3])
		return sine
	def plot_feature(self,properties):
		a = properties[self.extname][0]
		b = properties[self.extname][1]
		c = properties[self.extname][2]
		d = properties[self.extname][3]
		abcd = array([a,b,c,d])
		# y = a + b * sin(cx - d)
		plot(self.time_data,self.sine_wave(abcd,self.time_data),label=self.extname)
