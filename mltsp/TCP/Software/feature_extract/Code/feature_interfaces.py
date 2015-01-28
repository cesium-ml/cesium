import os, sys
import numpy
from numpy import *
import extractors
from extractors import *
import FeatureExtractor
#from fetchers import *
import internal_generated_extractors_holder

avtype = [('extname','S100') , ('extractor',object_), ('active',bool_)] # format of available_extractors

class FeatureInterface(object):
	"""This serves as an interface between signals and extractors.
	An instance of this object is generated when the module is imported
	"""
	def __init__(self):
		igea = internal_generated_extractors_holder.\
		                            Internal_Gen_Extractors_Accessor()
		# obsolete:
		self.glob_internally_generated_extractors = \
				       igea.glob_internally_generated_extractors

		# 20081216: dstarr sees that we keep on appending signals here (and growing memory) when he thinks only one signal is needed in self.subscribing_signals[] to do the feature extractions for a source. : (original function == True):
		self.debug__original_do_append_signals_to_subscribing_signals = False
		self.subscribing_signals = []
		self.available_extractors = empty(0,avtype) # declare the recipient numpy array for extractors
		
	#def register_signal(self,signal):
	#	self.subscribing_signals.append(signal)
	#	for ext_name,extractor in self.available_extractors.\
	#		                                   iteritems():
	#		signal.update(extractor())
	# 20071215: dstarr modifies this since he thinks order of load matters
	#       and a dictionary .iteritems() or .values() is not applicable:

	def register_signal(self,signal, list_of_extractors, initialize = True):
		""" initialize determines whether all the active extractors are immediately applied to the signal """
		if self.debug__original_do_append_signals_to_subscribing_signals:
			self.subscribing_signals.append(signal)
		else:
			# 20081216: dstarr sees that we keep on appending signals here (and growing memory) when he thinks only one signal is needed in self.subscribing_signals[] to do the feature extractions for a source.
			self.subscribing_signals = [signal]
		if initialize: # check that we want to initialize the signal
			for an_extractor in self.available_extractors[self.available_extractors['active']]: # loop through all active extractors
				#print "Now I'm doing " + str(an_extractor['extname'])
				#if str(an_extractor['extname']) == 'lomb_scargle':
				#	print 'yo'
				extractor_obj = an_extractor['extractor']() # instantiate
				signal.update(extractor_obj)

		
	def register_extractor(self,extractor):
		self.available_extractors = append(self.available_extractors, \
			                 array((extractor.extname, extractor, \
						extractor.active),avtype)) # append a tuple of format avtype containing (extname, extractor object, active)
		if extractor.active: self.notify(extractor)


	def notify(self,extractor):
		#print "New active extractor available!"
		for signal in self.subscribing_signals:
			signal.update(extractor())


	def remove_signal(self,signal):
		self.subscribing_signals.remove(signal)


	def remove_extractor(self,extractor):
		""" Remove an extractor from the available extractor list.
		Input is a type. To remove by name, using remove_extname """
		sizebeforeremoving = self.available_extractors.size
		self.available_extractors = self.available_extractors[ where( \
 			   self.available_extractors['extractor'] != extractor)] # slice off the corresponding extractor
		sizeafterremoving = self.available_extractors.size
		if sizebeforeremoving == sizeafterremoving:
			print "Key does not exist, can't be removed from active list", extractor.extname


	def remove_extname(self,extname):
		""" Remove an extractor from the available extractor list by
		its name. Input is a string.
		To remove by type, using remove_extractor """
		sizebeforeremoving = self.available_extractors.size
		self.available_extractors = self.available_extractors[ where( \
			       self.available_extractors['extname'] != extname)] # slice off the corresponding extractor
		sizeafterremoving = self.available_extractors.size
		if sizebeforeremoving == sizeafterremoving:
			print "Key does not exist, can't be removed from active list", extractor.extname


	def switch_extname(self,extractor_name,activate=False,deactivate=False):
		extractor_index = self.find_extname(extractor_name, index=True)
		if extractor_index: # check that find_extname worked
			extractor_row = self.available_extractors[\
				                                extractor_index]
			active = extractor_row['active']
			print "This extractor %s was in state %s" % (\
				                         extractor_name, active)
			if activate:
				active = True
			elif deactivate:
				active = False
			else:
				active = not active
			print "This extractor %s is now in state %s" % (\
				                          extractor_name,active)
			self.available_extractors[extractor_index] = array(\
				(extractor_row['extname'][0], \
				 extractor_row['extractor'][0], active),avtype)
			return "done"
		else:
			return False


	def find_extname(self,extractor_name, index = False): # linked if want to modify the array directly
		extractor_index = where(self.available_extractors['extname'] ==\
					extractor_name)[0]
		if size(extractor_index) is 0: 
			print "find_extname couldn't find extractor %s" % \
			                                        (extractor_name)
			return False # if we didn't find the object
		if index: 
			return extractor_index[0]
		extractor_row = self.available_extractors[extractor_index][0] # return the corresponding extractor row (extname, extractor and active)
		return extractor_row


	def request_extractor(self,extractor_name):
		extractor_row = self.find_extname(extractor_name)
		if extractor_row: # check that find_extname worked
			return extractor_row['extractor']
		else:
			return False


feature_interface = FeatureInterface()


def initialize(list_of_extractors):
	sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                                       'Software/ingest_tools'))
	import feature_extraction_interface
	fs = feature_extraction_interface.Internal_Feature_Extractors()
	for key_name in fs.feature_ordered_keys:
		list_of_extractors.append(key_name)
	# The following list is no-longer explicitly defined here.
	#    Rather, I build the list in feature_extraction_interface.py
	#list_of_extractors.extend([ weighted_average_extractor , chi2extractor , dc_extractor , dist_from_u_extractor , fourierextractor , linear_extractor , max_slope_extractor , medianextractor , beyond1std_extractor , stdvs_from_u_extractor , old_dcextractor , power_spectrum_extractor , power_extractor , montecarlo_extractor ,  pct_80_montecarlo_extractor , pct_90_montecarlo_extractor , pct_95_montecarlo_extractor , pct_99_montecarlo_extractor , significant_80_power_extractor , significant_90_power_extractor , significant_95_power_extractor , significant_99_power_extractor , first_freq_extractor , sine_fit_extractor , sine_leastsq_extractor , skew_extractor , stdextractor , wei_av_uncertainty_extractor  , lomb_extractor , first_lomb_extractor , sine_lomb_extractor , second_extractor , third_extractor , second_lomb_extractor , ratio21, ratio31, ratio32]) # order matters!
	#for extractor in extractors.__dict__.values():
	#for extractor in list_of_extractors:
	list_of_extractor_objects = []
	for extractor_name in list_of_extractors:
		exec("extractor = %s" % (extractor_name)) #KLUDGY
		list_of_extractor_objects.append(extractor)
		if isinstance(extractor,type):
			instance = extractor()
			if isinstance(instance,FeatureExtractor.GeneralExtractor):
				instance.register_extractor()
			else:
				pass
		else:
			pass
        return list_of_extractor_objects


def fetch_extract(extractor_name,properties,band=None):
	""" we want the result of this extractor """
	extractor = feature_interface.request_extractor(extractor_name)
	result = extractor.extr(properties,band=band)
	return result
