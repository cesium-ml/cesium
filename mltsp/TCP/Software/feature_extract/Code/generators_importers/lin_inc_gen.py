from __future__ import absolute_import
import numpy
from .storage import storage

from .sgwindn_gen import sgwindn_gen

class lin_inc_gen(sgwindn_gen): #data with a slope
	name = 'linearly increasing generator'
	def slopegen(self):
		a = float(numpy.random.normal(loc=0.1,scale=2,size=1))
		return a
	def set_vars(self):
		super(lin_inc,self).set_vars()
		self.a = self.slopegen()
	def set_outputs(self):
		super(lin_inc,self).set_outputs()
		self.for_input['real_slope'] = self.a
		self.for_input['flux_data']=self.signalgen['flux_data'] + self.t * self.a