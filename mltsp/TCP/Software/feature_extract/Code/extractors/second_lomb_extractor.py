
from ..FeatureExtractor import FeatureExtractor
import numpy
from numpy import random
from scipy import fftpack, stats, optimize
try:
	from pylab import *
except:
	pass
from common_functions import *

from second_extractor import second_extractor
from lomb_extractor import lomb_extractor
from first_lomb_extractor import first_lomb_extractor
#from common_functions.plot_methods import plot_vertical_line

class second_lomb_extractor(second_extractor):
	""" Extracts the second frequency from a lomb power spectrum"""
	active = False
	extname = 'second_lomb' #extractor's name
	gauss_scale = 0.002
	def set_inputs(self):
		#self.frequencies = self.fetch_extr('lomb')[0]
		(power,freq) = self.fetch_extr('lomb')
		self.power = power
		self.first = self.fetch_extr('first_lomb')
