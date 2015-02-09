import numpy
from numpy import random
from scipy import fftpack, stats, optimize
try:
	from pylab import *
except:
	pass

class Example_Methods(object): # Extractors which inherit this object can make use of these methods.
	def example_main_method(self,y,f,x=None,rms=None):
		""" Inputs:
		[y]-data    (array)
		[f]unction  (function)
		[x]-axis    (array)
		[rms] noise (array)
		"""
		# Always initialize these in-case they aren't defined:
		if rms is None:
			rms = ones(len(y))
		if x is None:
			x = range(len(y))

		# Do work here.  Call inherited methods if needed.
		# - NOTE: use numpy module for basic math/array tasks.

		# Return a scalar float:
		return sum(y)

