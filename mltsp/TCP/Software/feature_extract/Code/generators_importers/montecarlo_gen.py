from __future__ import absolute_import
import numpy

from .gen_or_imp import gen_or_imp

class montecarlo_gen(gen_or_imp):
	name = "montecarlo bootstrap generator"
	def generate(self,dic,output):
		inputdic = dic['input']
		rms = inputdic['rms_data']
		self.time_data = inputdic['time_data']
		# 200712076 dstarr try/excepts this:
		try:
			self.frequencies = inputdic['frequencies']
		except:
			self.frequencies = numpy.array([])
		noise_signal = []
		for i in range(len(rms)):
			noise = float(numpy.random.normal(loc=0.0,scale=rms[i],size=1))
			noise_signal.append(noise)
		self.s = numpy.array(noise_signal)
		self.set_outputs()
		self.store(self.signalgen,output)
	def set_outputs(self):
		self.make_dics()
		self.for_input = self.sub_dics(self.signaldata)
		self.for_input['time_data'] = self.time_data
		self.for_input['flux_data'] = self.s
		self.for_input['frequencies'] = self.frequencies
	def store(self,data,output):
		from ..signal_objects import signal
		signal_obj = signal(data,register=False)
		output.append(signal_obj)
