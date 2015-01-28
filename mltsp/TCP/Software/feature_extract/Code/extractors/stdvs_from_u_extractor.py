from __future__ import absolute_import

from ..FeatureExtractor import InterExtractor
import numpy
from numpy import random
from scipy import fftpack, stats, optimize
try:
	from pylab import *
except:
	pass
from .common_functions import *

from .dist_from_u_extractor import dist_from_u_extractor
from .wei_av_uncertainty_extractor import wei_av_uncertainty_extractor

class stdvs_from_u_extractor(InterExtractor):
	active = True
	extname = 'stdvs_from_u' #extractor's name
	def extract(self):
		dist_from_u = self.fetch_extr('dist_from_u', returnall=True) 
		dist = dist_from_u.result
		sd = self.fetch_extr('weighted_average', returnall=True).uncertainty # returns the uncertainty in the weighted average
		num = dist/sd # number of standard deviations from the weighted average
		uncer = dist_from_u.uncertainty/sd # scales the uncertainty (not sure this is correct)
		self.uncertainty = uncer
		return num
