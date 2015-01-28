from __future__ import absolute_import
import numpy
from .storage import storage

from .generator import generator

class sgwindn_gen(generator): #signal with individual noise (each data point has a different standard deviation)
	name = "signal with individual noise"
	def noise(self,stdev_in = 1.0,size_in=1): #gaussian with standard deviation as input
		#indiv_noise_std = abs(numpy.random.normal(loc=stdev_in,scale=1.0,size=size_in)) # each point gets a different noise with a different st. dev., absolute value avoids negative values (not perfect, could be linear instead of gaussian)
		indiv_noise_std = numpy.random.rand(size_in)+1
#		indiv_noise_std[:] = 1
#		indiv_noise_std[5] = 20
#		indiv_noise_std[2] = 20
		indiv_noise = []
		for i in range(size_in):
			noise = float(numpy.random.normal(loc=0.0,scale=indiv_noise_std[i],size=1))
			indiv_noise.append(noise)
#		print 'indiv_noise_std',numpy.array(indiv_noise_std).sum(),'n','indiv_noise',numpy.array(indiv_noise).sum()
		return (indiv_noise_std,indiv_noise)
	def generate(self,stdev = 1.0):
		self.stdev = stdev
		self.s = self.randomsine()
#		self.s = 5 * numpy.ones(len(self.t))
		self.noise_tuple = self.noise(stdev_in=self.stdev,size_in=len(self.s))
		self.n = self.noise_tuple[1]
		self.set_outputs()
		self.store(self.signalgen)
	def set_vars(self):
		super(sgwindn_gen,self).set_vars()
	def set_outputs(self):
		super(sgwindn_gen,self).set_outputs()
		self.for_input['rms_data'] = self.noise_tuple[0]