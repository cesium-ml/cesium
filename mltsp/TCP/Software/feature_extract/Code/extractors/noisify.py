from ..FeatureExtractor import InterExtractor
from numpy import inf
import numpy

from ..generators_importers.copy_gen import noisified_gen # the class that will generate the new (noisified) signal

class noisify(InterExtractor):
	""" Noisifies the data as wished, and re-extracts all the features"""
	active = False
	extname = 'noisify' #extractor's name
	list_of_noisifiers = [badpoints(p=0.001, sigma=10), addgaussian(sigma = 2), cliptop(maxvalue = 20), clipbottom(minvalue = 3)] # list of noisifying functions that will be applied in order to the signal, presumably this list should be defined elsewhere to make it more flexible and modifiable at runtime. Order matters, and entries can of course be repeated.
	dic_of_noisifiers = {'badpoints':badpoints, 'addgaussian':addgaussian, 'cliptop':cliptop, 'clipbottom':clipbottom, 'makefainter':makefainter} # this dictionary (dic_of_noisifiers) is simply to be able to export all the noisifying functions outside of this module
	def extract(self):
		for i in range(len(self.list_of_noisifiers)):
			self.list_of_noisifiers[i] = self.list_of_noisifiers[i].noisify # we want the actual function, not the class
		generator = noisified_gen(self.list_of_noisifiers) # generate a new signal
		signal = generator.generate(self.dic) # send the generator the list of functions to apply to the signal
		return signal # the result is the actual signal, so far we haven't applied any feature extractions to it
		
		
class noisifier(object):
	def noisify(self,inputdic):
		self.flux_data = inputdic['flux_data']
		self.time_data = inputdic['time_data']
		self.n = len(self.flux_data) # because this is often useful
		return self.myaction(inputdic)
	def myaction(self,inputdic):
		pass
		
		
class cliptop(noisifier):
	""" clips the faintest points """
	def __init__(self,maxvalue=inf):
		self.maxvalue = maxvalue
	def myaction(self,inputdic):
		self.flux_data = self.flux_data.clip(min = -inf, max = self.maxvalue)
		inputdic['flux_data'] = self.flux_data
		return inputdic
		
class clipbottom(noisifier):
	""" clips the brightest points """
	def __init__(self,minvalue=-inf):
		self.minvalue = minvalue
	def myaction(self,inputdic):
		self.flux_data = self.flux_data.clip(min = self.minvalue, max = inf)
		inputdic['flux_data'] = self.flux_data
		return inputdic
		
class addgaussian(noisifier):
	""" _add_ gaussian noise to the signal 
		Here we will specify a sigma, and add corresponding noise to the signal.
		The array of RMS values will simply be augmented by this sigma
	"""
	def __init__(self, sigma = 1):
		self.sigma = sigma
	def myaction(self,inputdic):
		gauss = numpy.random.normal(loc=0.0,scale=self.sigma,size=self.n) # create the gaussian noise
		self.flux_data = self.flux_data + gauss # add the gaussian noise to the signal
		inputdic['flux_data'] = self.flux_data
		inputdic['rms_data'] += self.sigma
		return inputdic
		
class badpoints(noisifier):
	""" simulate bad points
		input: the probability of a bad point, and the sigma associated with such a bad point
		Note: it would make sense to apply the bad points _before_ clipping, to avoid points outside the clipping boundaries
		 """
	def __init__(self, p=0.001, sigma = 10):
		self.p = p
		self.sigma = sigma
	def myaction(self,inputdic):
		isitbad = numpy.random.binomial(1, self.p, size=self.n) # Create a bunch of zeros and ones using a binomial distribution. The ones will become bad points. Each point is just one trial (by definition), hence the first input.
		nbadpoints = isitbad.sum() # number of bad points
		isitbad = isitbad.astype(bool) # convert to True/False so we can use it to index things
		gauss = numpy.random.normal(loc=0.0,scale=self.sigma,size=nbadpoints) # create the bad points
		self.flux_data[isitbad] = gauss # the bad points are replaced by the random values we just created
		inputdic['flux_data'] = self.flux_data
		return inputdic
		
class makefainter(noisifier):
	""" Make an object fainter by a fixed number of magnitudes """
	def __init__(self, mags = 1):
		self.mags = mags
	def myaction(self,inputdic):
		self.flux_data += self.mags # add that number of magnitudes (-> make fainter)
		inputdic['flux_data'] = self.flux_data
		return inputdic