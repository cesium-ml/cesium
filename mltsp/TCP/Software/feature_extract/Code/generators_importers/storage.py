import numpy
from ..signal_objects import signal_generator, signal_with_bands, signal_xml, signal

class storage(object):
	def store(self,signalfromgen,signals_list, register=True):
		if signalfromgen['source'] =='generator':
			signals_list.append(signal_generator(signalfromgen, register=register))
		elif signalfromgen['source'] == 'vizier cepheids':
			signals_list.append(signal_with_bands(signalfromgen, register=register))
		elif signalfromgen['source'] == 'xml':
			# generally going here...
			out = signal_xml(signalfromgen, register=register)
			signals_list.append(out)
		else: signals_list.append(signal(signalfromgen, register=register))
