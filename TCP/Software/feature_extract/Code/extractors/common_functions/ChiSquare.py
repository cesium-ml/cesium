import numpy
from numpy import random
from scipy import fftpack, stats, optimize
try:
	from pylab import *
except:
	pass

class ChiSquare(object): #gives extractors the ability to calculate chi squares
	def chi_square_sum(self,y,f,x=None,rms=None):
		""" inputs: [y]-data (array) [f]unction (function), [x]-axis [rms] noise (array)"""
		chi2=self.chi_square(y,f,x,rms)
		chi2_sum = chi2.sum()
		return chi2_sum
	def chi_square(self,y,f,x=None,rms=None):
		""" inputs: [y]-data (array) [f]unction (function), [x]-axis [rms] noise (array)"""
		if rms == None:
			rms = ones(len(y))
		if x == None:
			x = range(len(y))
		chi2_total = 0.0
		fx = f(x)
#		print 'fx',fx
		chi2 = numpy.power(y - fx,2)/numpy.power(rms,2)
		return chi2
