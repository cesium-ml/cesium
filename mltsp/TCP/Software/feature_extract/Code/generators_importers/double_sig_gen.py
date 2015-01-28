from __future__ import absolute_import
import numpy
from .storage import storage

from .generator import generator

class double_sig_gen(generator):
	source = 'double_sig_gen'
	def randomsine(self): #generates a random sine wave
		self.set_vars()
		self.t2 = self.tgen()
		self.r2 = self.rgen()
		self.amp2 = self.ampgen()
		self.p2 = self.pgen()
		s = self.dc + (self.amp * numpy.sin(2*numpy.pi*self.t*(self.r+1)/self.p)) + (self.amp2 * numpy.sin(2*numpy.pi*self.t2*(self.r2+1)/self.p2)) # if r=0, period=p, if r=1, period = p/2
		return(s)
	def set_outputs(self):
		super(double_sig_gen,self).set_outputs()
		self.for_input['period2']=(self.p2/(self.r2+1))
		self.for_input['amplitude2']=self.amp2
	def generate(self,stdev = 1.0):
		self.stdev = stdev	
		s = self.randomsine()
		n = self.noise(stdev_in=self.stdev,size_in=len(self.s)) # generate noise with correct length
		self.make_dics()
		self.signaldata = {'period':(self.p/(self.r+1)) ,'period2':(self.p2/(self.r2+1)), 'amplitude':self.amp,'amplitude2':self.amp2 , 'time_data':self.t , 'flux_data':(s+n) , 'clean_flux_data':s ,'dc_real':self.dc}
		self.store(self.signalgen)