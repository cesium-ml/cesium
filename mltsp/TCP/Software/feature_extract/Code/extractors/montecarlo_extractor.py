from __future__ import absolute_import
from ..FeatureExtractor import InterExtractor
import numpy

from ..generators_importers.montecarlo_gen import montecarlo_gen
from .power_extractor import power_extractor
class montecarlo_extractor(InterExtractor):
	""" Performs a montecarlo bootstrap on the data to determine the significance of a power spectrum """
	active = True
	extname = 'montecarlo' #extractor's name
	how_many = 50 # TEN IS PROBABLY NOT ENOUGH BUT IT SPEEDS THINGS UP FOR NOW
	def extract(self):
		list_for_bootstraps = []
		spectra = []
		for i in range(self.how_many):
			gen = montecarlo_gen()
			try:
				gen.generate(self.dic,list_for_bootstraps)
			except KeyError:
				self.ex_error("(KeyError in montecarlo generator) No rms data available in dictionary:%s" % self.dic['input'].keys().__str__())
		freqs = self.frequencies#self.fetch_extr('power_spectrum')[0]
		for sig in list_for_bootstraps:
			power = sig.update(power_extractor()).result
			if power == "Fail":
				self.ex_error(power.why)
			spectra.append(power)
		spec_stack = numpy.vstack(spectra)
		spec_stack.sort(axis=0)
		return spec_stack