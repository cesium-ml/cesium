
from ..FeatureExtractor import FeatureExtractor
import numpy
from numpy import random
from scipy import fftpack, stats, optimize
try:
	from pylab import *
except:
	pass
from common_functions import *

#from power_extractor import power_extractor as power_extractor # could also use one of the x% significant extractors
from scipy import stats
from common_functions.plot_methods import plot_vertical_line


class second_extractor(plot_vertical_line,FeatureExtractor):
	""" extracts the second highest peak from a power spectrum"""
	active = True
	extname = 'second' #extractor's name
	gauss_scale = 0.005
	def set_inputs(self):
		#self.frequencies = self.fetch_extr('power_spectrum')[0]
		#self.frequencies = self.frequencies[:len(self.frequencies)+1]
		result = self.fetch_extr('significant_90_power')
		(power, freq) = result
		self.power = power
		self.frequencies = freq
		self.previous = self.fetch_extr('first_freq')
	def extract(self):
		# 20071215 dstarr adds try/except:
		try:
			self.set_inputs()
		except:
			why = "Except: {second,third}_extractor.set_inputs().  Probably Failure of self.fetch_extr(...) for second_extractor,first_freq_extractor, or power_extractor."
			self.ex_error(text=why)

		gaussian = self.make_gaussian()
		self.subtracted_gauss = self.power - gaussian
		max_index = self.subtracted_gauss[1:].argmax() + 1
		max_freq = self.frequencies[max_index]
		if self.subtracted_gauss[max_index] < 0.1:
			why = "No %s frequency, power spectrum is zero/low at all points" % self.extname
			self.ex_error(text=why)
		#if self.extname == 'second lomb':
		#	plot(self.frequencies,subtracted_gauss,label="subtracted gaussian")
		#	plot(self.frequencies,gaussian,label="gaussian")
		return max_freq
	def make_gaussian(self):
		gaussian = stats.norm.pdf(self.frequencies,loc=self.previous,scale = self.gauss_scale)
#		plot(self.frequencies,gaussian,label = "early gaussian")
		index = self.frequencies.searchsorted(self.previous)
		ratio = self.power[index]/gaussian[index]
		gaussian *= ratio
		return gaussian
	def specific_obj(self,output):
		output.subtracted_gauss = self.subtracted_gauss
		
class third_extractor(second_extractor):
	""" extracts the third highest peak from a power spectrum"""
	active = True
	extname = 'third' #extractor's name
	def set_inputs(self):
		#self.power = self.fetch_extr('second').subtracted_gauss # result object has data about the subtracted gaussian
		# 20071215 dstarr changes to this:
		result = self.fetch_extr('second')
			
		self.power = result.subtracted_gauss
		self.frequencies = result.frequencies

		# 20071215 dstarr notes this can probably be done instead:
		##### self.previous = result
		self.previous = self.fetch_extr('second')
