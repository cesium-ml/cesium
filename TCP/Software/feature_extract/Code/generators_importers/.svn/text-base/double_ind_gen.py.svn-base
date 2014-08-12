import numpy
from storage import storage

from sgwindn_gen import sgwindn_gen
from double_sig_gen import double_sig_gen

class double_ind_gen(sgwindn_gen,double_sig_gen):
	name = 'double sine wave with individual noise, evenly sampled'
	def generate(self,stdev = 1.0):
				self.stdev = stdev
				self.s = self.randomsine()
		#		self.s = 5 * numpy.ones(len(self.t))
				self.noise_tuple = self.noise(stdev_in=self.stdev,size_in=len(self.s))
				self.n = self.noise_tuple[1]
				self.set_outputs()
				self.signaldata = {'period':(self.p/(self.r+1)) ,'period2':(self.p2/(self.r2+1)), 'amplitude':self.amp,'amplitude2':self.amp2 , 'time_data':self.t , 'flux_data':(self.s+self.n) , 'clean_flux_data':self.s ,'dc_real':self.dc}
				self.store(self.signalgen)
	def set_outputs(self):
#		generator.set_outputs(self)
#		self.for_input['rms_data'] = self.noise_tuple[0]
		sgwindn_gen.set_outputs(self)
		self.for_input['period2']=(self.p2/(self.r2+1))
		self.for_input['amplitude2']=self.amp2