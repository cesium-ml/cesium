"""
First, import this module
> import random_number
then run its test, assigning it a name
> sig = random_number.test()
then you can plot more things if you want, e.g.:
> sig.plots('dc')
"""
from __future__ import print_function
from __future__ import absolute_import

from . import generators_importers

signals_list = []


def test(stdev = 1.0, clear=True, signals_list=signals_list):
	""" performs a basic test and plots stuff
		change the generator to sgwindn (line 13) to get an evenly sampled signal
	"""
#	gen = generators_importers.vizier_importer(signals_list)
#	gen = generators_importers.sgwindn_gen(signals_list)
	gen = generators_importers.from_xml(signals_list)
#	gen = generators_importers.uneven_sine_gen(signals_list)
#	gen = generators_importers.double_uneven_gen(signals_list)
#	gen = generators_importers.double_sig_gen(signals_list)
#	gen = generators_importers.test_lomb(signals_list)
	i=0
	while i < 1:
		gen.generate()
		i += 1
		sig = signals_list[-1]
#		sig.properties['data']['inter']['99pct significant power'].plots()
		#sig.properties['data']['inter']['power'].plots()
	#sig.properties['data']['inter']['pct 80 montecarlo'].plots()
	#sig.properties['data']['inter']['pct 90 montecarlo'].plots()
	#sig.properties['data']['inter']['pct 95 montecarlo'].plots()
	#sig.properties['data']['inter']['pct 99 montecarlo'].plots()
	return sig
def xml_print():
	for signal in signals_list:
		print(signal.xml_print.xml())
