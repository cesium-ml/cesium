import numpy
from numpy import random
from scipy import fftpack, stats, optimize

try:
	from pylab import *
except:
	pass
try:
	from extractors import *
except:
	pass

import internal_generated_extractors_holder # 20080508 KLUDGE

try:
	import feature_interfaces
except:
	pass
#20090321#import amara

class ExtractException(Exception):
	"extractor refused to extract"
	pass
class ResultObject(object):
	def __init__(self,result):
		self.result = result
	def __str__(self):
		return str(self.result)
class Intermediary(ResultObject):
	pass
class Feature(ResultObject):
	pass

class GeneralExtractor(object):
	# 20080508 KLUDGE:
	igea = internal_generated_extractors_holder.\
	                Internal_Gen_Extractors_Accessor() # 20080508 KLUDGE
	glob_internally_generated_extractors = igea.glob_internally_generated_extractors

	why_fail = "This didn't fail as far as I know" # implement in subclasses please
	minpoints = 0
	maxpoints = 28200 #20090127: dstarr adds this after seeing a ws_variability_extractor related memory balloon possibly due to a +30k dataset.
	def __init__(self):
		pass
	active = False
	extname = 'FeatureExtractorctor' #extractor's name
	counter = 0 # number of extractions performed
	def extr(self,properties,band=None): #general code run before extraction
		self.properties = properties
		self.finddatadic(properties,band=band) # find the dictionary of the signal properties that contains the actual data
		if not self.checkalready(): # if it doesn't exist already
			print self.extname, "extracting right now"
			try:
				self.set_names(self.dic['input'])
				self.longenough() # check that there is enough data to run this
				result = self.extract()
				self.why_fail = False # I didn't fail so far
			except ExtractException:
				result = False
				#self.why_fail = "I don't know why it failed"
			self.prepare_obj(result)
		### check that resources are not wasted
		self.__class__.counter += 1 # number of times this feature has been run, supposed to be used as a check for redundancies, doesn't do anyting right now
		#if self.counter > 1:
			#dstarr com out# print "I just did this thing twice, that's ridiculous", self.extname, self.counter, "times"
		###
		return self.output
	def finddatadic(self,properties,band=None):
		""" find the dictionary of the signal properties that contains the actual data """
		if band: # if the signal has bands, look for data in respective subdictionary
			self.dic = self.properties['data'][band]
			self.band = band
		else: # otherwise the data is directly in ['data'] (no bands)
			self.dic = self.properties['data']
			self.band = None
		return None
	def checkalready(self):
		""" check if this feature has already been extracted in the past """
		for subdic in ['input','features','inter']:
			if self.dic[subdic].has_key(self.extname): # test to see if this feature has already been extracted
				output = self.dic[subdic][self.extname]
				#print "SKIP", self.extname, subdic
				self.output = output
				print "skipping", self.extname
				return True # yes it already exists
			else: pass
		return False # no it doesn't exist yet

	def prepare_obj(self,result):
		self.output = self.out_type(result)
		self.output.plots = self.plots # give my plot method
		self.output.dic = self.dic # give it the signal/band's dictionary (this is kinda crazy actually)
		self.output.__doc__ = self.__doc__ # give my docstring
		self.output.extname = self.extname # give my name
		try:
			self.output.uncertainty = self.uncertainty # if the feature extractor specifies an uncertainty value, export it
		except AttributeError:
			self.output.uncertainty = 0 # otherwise, the uncertainty is zero
		#if self.why_fail: #don't pass anything if not failed
		self.output.why = self.why_fail # explanation of why a feature extraction failed (or refused to perform)
		self.general_obj(self.output) # implement different behavior if this is a feature or an intermediary result
		if self.output.result is not False: # no need to do so if failed
			self.specific_obj(self.output) # specific feature extractors may be interested in particular behaviors
	def general_obj(self,output):
		"""implement different behavior if this is a feature or an intermediary result"""
		pass
	def specific_obj(self,output):
		"""add more information in the output object on a feature-specific basis (implemented at subclass level)""" # this docstring gets overridden down the line, kinda stupid
		pass
	def extract(self): # delegates the actual implementation to subclasses
		pass
	def set_names(self,where):
		""" prepares the most commonly used inputs for easy access """
		try:
			self.time_data = where['time_data']
			self.flux_data = where['flux_data']
		except KeyError:
			pass
		
                ####20110512commentout#'frequencies':self.fgen(input_dic['time_data'])}) # 20110512: NOTE: this and self.frequencies are not used by any current features (used to be related to old lomb implementations).  About to add a new self.frequencies overwriting declaration in lomb_scargle_extractor.py:extractor(), which will allow the first freq self.frequencies, self.psd to be accessible to outside code.
                #try:
		#        import pdb; pdb.set_trace()
		#	self.frequencies = where['frequencies']
		#except KeyError:
		#	self.frequencies = numpy.array([])
		try:
			self.rms_data = where['rms_data']
		except KeyError:
			try: # sorry this is getting messy, this is for multiband extractors
				self.rms_data = numpy.ones(len(self.time_data), dtype=float)
			except AttributeError:
				pass
		try:
			self.ra = where['ra']
			self.dec = where['dec']
		except KeyError:
			pass
		try:
			self.ra_rms = where['ra_rms']
			self.dec_rms = where['dec_rms']
		except KeyError:
			pass
		
		try:
			self.time_data_unit = where['time_data_unit']
			self.flux_data_unit = where['flux_data_unit']
			self.rms_data_unit  = where['rms_data_unit']
			self.time_data_ucd  = where['time_data_ucd']
			self.flux_data_ucd = where['flux_data_ucd']
			self.rms_data_ucd = where['rms_data_ucd']
		except KeyError:
			pass
			
	def register_extractor(self): # broken
		""" register this extractor as an active extractor"""
		feature_interfaces.feature_interface.register_extractor(type(self))
	def remove_extractor(self): # broken
		""" inactivate this extractor """
		feature_interfaces.feature_interface.remove_extractor(type(self))
	def plots(self,properties=None):
		if not properties: properties = self.dic
		self.set_names(properties['input'])
		merge = dict(properties['input'], **properties['features'])
		merge = dict(merge, **properties['inter'])
		if self == 'Fail':
			print "I can't print myself, I'm a failure", self.extname
		else:
			self.plot_feature(merge) # delegates at extractor (subclass) level, each extractor knows how to plot itself
		legend()
	def plot_feature(self,properties):
		print "I don't know how to plot myself", self.extname # implement in subclasses


	def fetch_extr(self,extractor_name,properties=None,error=True, band=None, returnall = False, return_object = False):
		""" Fetch the result from other extractors
		error (boolean): True to proagate the error of fetched extractors """
		if not band: band = self.band
		if not properties: properties = self.properties
		if not isinstance(extractor_name, str):
			print "Method %s is still using old fetch procedure, calling %s" % (self.extname, extractor_name.extname)
			return self.fetch_extr_old(extractor_name,properties,error, band, returnall, return_object)
		#print extractor_name, self.properties, self.band
		# # # # # # # # dstarr KLUDGE (next single condition:):
		fetched_extractor = feature_interfaces.feature_interface.request_extractor(extractor_name) # the feature interface is in charge of storing and finding extractors, receives an extractor or False
		if not fetched_extractor: #if the feature_interface was unable to find the extractor
			self.ex_error("Extractor %s not able to fetch extractor %s" % (self.extname, extractor_name))
		fetched_instance = fetched_extractor() # instantiate
		if return_object:
			return fetched_instance
		elif returnall: # return the entire object
			ret_object = fetched_instance.extr(properties,band=band)
			returner = ret_object
		else: 
			ret_object = fetched_instance.extr(properties,band=band)
			returner = ret_object.result
		if ret_object.result is False and error: # if the result is an error
			self.ex_error(ret_object.why) # then propagate the error
		return returner
	def fetch_extr_old(	self,extractor_name,properties=None,error=True, band=None, returnall = False, return_object = False):
			""" Fetch the result from other extractors
			error (boolean): True to proagate the error of fetched extractors """
			if not band: band = self.band
			if not properties: properties = self.properties
			#print extractor_name, self.properties, self.band
			# # # # # # # # dstarr KLUDGE (next single condition:):
			if return_object:
				ret_object = extractor_name()
				#result = ret_object.result
				result = True # KLUDGE
				returner = ret_object
			elif returnall: # return the entire object
				ret_object = extractor_name().extr(properties,band=band)
				result = ret_object.result
				returner = ret_object
			else: 
				ret_object = extractor_name().extr(properties,band=band)
				result = ret_object.result
				returner = result
			if result is False and error:
				self.ex_error(ret_object.why)
			return returner
	def ex_error(self,text="I don't know why"):
		""" a feature extractor's way of raising an error cleanly """
		self.why_fail = text
		print self.why_fail, self.extname
		raise ExtractException, text
	def longenough(self):
		""" will not perform extraction if there aren't enough data points, minpoints set at extractor level """
		try:
			if (len(self.flux_data) < self.minpoints) or \
			   (len(self.flux_data) > self.maxpoints): # if 4 or less points, error
				self.ex_error("not enough (or too much) data points: %d" % (len(self.flux_data)))
		except:
			self.ex_error("not enough (or too much) data points")
class FeatureExtractor(GeneralExtractor):
	out_type = Feature
	internal_use_only = False # dstarr adds this.  But a bit of a KLUDGE
	#       since non-feature extractors should be InterExtractors and
	#       not FeatureExtractors.  But with users making feature extractors
	#       this parameter may be needed.
	def general_obj(self,output):
		pass

class InterExtractor(GeneralExtractor):
	out_type = Intermediary
	internal_use_only = True # dstarr adds this.  But a bit of a KLUDGE
	#       since non-feature extractors should be InterExtractors and
	#       not FeatureExtractors.  But with users making feature extractors
	#       this parameter may be needed.
	def general_obj(self,output):
		pass
		
class ContextExtractor(GeneralExtractor):
	""" This is a special extractor class for context features. """
	def longenough(self): # we're getting rid of the longenough method because it does not make sense
		pass
		
class MultiExtractor(ContextExtractor):
	""" for feature extractors that need to *compare* multiple bands """
	band1 = 'v'
	band2 = 'u'
	compared_extr = None
	def finddatadic(self,properties,band=None):
		""" this needs to be changed so the extractor has access to data from multiple bands """
		assert (band == 'multiband'), 'band should be multiband'
		self.dic = self.properties['data']['multiband']
		self.multidic = self.properties['data']
		self.band = band
		return None
	def set_names(self,where):
		""" prepares the most commonly used inputs for easy access """
		ContextExtractor.set_names(self,where)
		if not self.multidic.has_key(self.band1):
			self.ex_error("Multiband extractor %s did not find band '%s' in '%s'" % (self.extname, self.band1, self.multidic.keys()))
		else: pass
		if not self.multidic.has_key(self.band2):
			self.ex_error("Multiband extractor %s did not find band '%s' in '%s'" % (self.extname, self.band2, self.multidic.keys()))
		else: pass
		self.dic1 = self.multidic[self.band1]
		self.dic2 = self.multidic[self.band2]
		self.extr1 = self.fetch_extr(self.compared_extr, band=self.band1)
		self.extr2 = self.fetch_extr(self.compared_extr, band=self.band2)
		return None
	def general_obj(self,output):
		output.band1 = self.band1
		output.band2 = self.band2
		output.compared_extr = self.compared_extr
		return None
		
class MultiFeatureExtractor(MultiExtractor,FeatureExtractor):
	pass
class MultiInterExtractor(MultiExtractor,InterExtractor):
	pass
	
class ContextFeatureExtractor(ContextExtractor,FeatureExtractor):
	pass
class ContextInterExtractor(ContextExtractor,InterExtractor):
	pass

# Extractors
####################****************############
# Extractor Outputs
		
"""class Extracted(object):
	def __init__(self,data):
		self.data = data
	def __repr__(self):
		return str(self.data)
	def newobj(self,new):
		self.data = new
		return self
	def __add__(self,other):
		new = self.data + other
		self.newobj(new)
	def __abs__(self):
		new = abs(self.data)
		self.newobj(new)
	def __getitem__(self,key):
		return self.data[key]
	def __getattr__(self,name):
		print name
#		exec "return self.data.%s" % name
		out = eval("self.data.%s" % name)
		return out"""
