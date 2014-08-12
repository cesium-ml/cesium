import numpy
from storage import storage

from gen_or_imp import gen_or_imp

class generator(gen_or_imp):
	name = 'generator'
	def __init__(self,signals_list=[]):
		self.storer = storage()
		self.signals_list = signals_list
	def ampgen(self):
		amp = (10.0+10.0*float(numpy.random.rand(1))) # one random number determines the amplitude between 10 and 20
		return amp
	def tgen(self): # x axis (time)
		return numpy.arange(500,dtype=float) #number of data points
	def fgen(self):
		frequencies = self.t / len(self.t) #evenly spaced data
	def dcgen(self):
		return(-10 + 20*float(numpy.random.rand(1))) # sets dc level randomly between -10 and +10
	def rgen(self):
		return(float(numpy.random.rand(1))) # one random number determines the period
	def pgen(self):
		return(30) #period
	def randomsine(self): #generates a random sine wave
		self.set_vars()
		s = self.dc + self.amp * numpy.sin(2*numpy.pi*self.t*(self.r+1)/self.p) # if r=0, period=p, if r=1, period = p/2
		return(s)
	def noise(self,stdev_in = 1.0,size_in=1): #gaussian with standard deviation as input
		# gauss = numpy.random.normal(loc=0.0,scale=stdev,size=size2) #gaussian noise signal in numpy
		gauss = numpy.random.normal(loc=0.0,scale=stdev_in,size=size_in)
		# return numarray.array(list(gauss)) #convert to numarray (in a horrible fashion) because couldn't plot with numpy
		return gauss
	def set_vars(self): # sets all the variables
		self.t = self.tgen()
		self.f = self.fgen()
		self.r = self.rgen()
		self.amp = self.ampgen()
		self.p = self.pgen()
		self.dc = self.dcgen()
	def generate(self,stdev = 1.0):
		self.stdev = stdev
		self.s = self.randomsine()
		self.n = self.noise(stdev_in=self.stdev,size_in=len(self.s)) # generate noise with correct length
		self.set_outputs()
		self.store(self.signalgen)
	def set_outputs(self):
		self.make_dics()
		self.for_input = self.sub_dics(self.signaldata)
		self.for_input['period']=(self.p/(self.r+1))
		self.for_input['amplitude']=self.amp
		self.for_input['time_data']=self.t
		self.for_input['flux_data']=(self.s+self.n)
		self.for_input['clean_flux_data']=self.s
		self.for_input['dc_real']=self.dc
		self.for_input['frequencies'] = self.f
	def store(self,data):
		self.storer.store(data,self.signals_list)
