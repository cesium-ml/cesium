"""
This generates creates a simple copy of a signal. It was written for the noisification process.

The noisifier generator first noisifies the data.

Created by Maxime Rischard on 2008-05-26.

"""
from __future__ import absolute_import

import numpy

from .gen_or_imp import gen_or_imp

class copy_gen(gen_or_imp):
	name = "copy generator"
	def generate(self,dic):
		inputdic = dic['input']
		rms = inputdic['rms_data']
		self.time_data = inputdic['time_data']
		# 200712076 dstarr try/excepts this:
		try:
			self.frequencies = inputdic['frequencies']
		except:
			self.frequencies = numpy.array([])
		self.s = inputdic['flux_data']
		self.set_outputs(inputdic)
		return self.store(self.signalgen)
	def set_outputs(self, inputdic):
		self.make_dics()
		self.for_input = self.sub_dics(self.signaldata)
		self.for_input = inputdic
	def store(self,data):
		from ..signal_objects import signal
		return signal(data,register=False)

class noisified_gen(copy_gen):
	name = "noisifier"
	def __init__(self, list_of_noisifiers):
		""" we'll be using __init__ to initialize the string of actions to apply to the signal """
		self.list_of_noisifiers = list_of_noisifiers
	def set_outputs(self, inputdic):
		self.make_dics()
		self.for_input = self.sub_dics(self.signaldata)
		self.for_input['old inputs'] = inputdic
		for noisifier in self.list_of_noisifiers:
			inputdic = noisifier(inputdic)
		self.for_input.update(inputdic)
	
		