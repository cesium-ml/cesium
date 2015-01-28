import feature_interfaces
import plotters
import FeatureExtractor

#global_list_of_extractors = [] # Global KLUDGE: # 20071215 dstarr.  Apparently this is done since feature_interfaces.initialize() is called outside of everything
global_list_of_extractors = feature_interfaces.initialize([])
#20090321#import amara

class signal(object):
	def __init__(self,data,register=True):
		self.properties = data
		self.choose_plotter()
		if register: self.register_signal()
	def choose_plotter(self):
		self.plotter = plotters.plotter()
	def update(self,extract_method):
		control = self.properties.copy()
		result = extract_method.extr(self.properties)
		assert (control == self.properties), "this bastard changed my dictionary" # this is just a test, can be removed if we trust our code
		write_where = self.find_where()
		self.write_result(write_where,result)
		return result
	def write_result(self,write_where,result):
		""" the type (class) of result I get informs me of where to put it """
		if isinstance(result,FeatureExtractor.Feature):
			write_where['features'][result.extname] = result
		elif isinstance(result,FeatureExtractor.Intermediary):
			write_where['inter'][result.extname] = result 
		else: raise "weird kinda of result, don't know what to do with it"
	def register_signal(self, initialize = True):
		""" says to the interface: i'm interested in hearing about new features 
		initialize determines whether active features should immediately be applied
		"""
		feature_interfaces.feature_interface.register_signal(self, \
						     global_list_of_extractors, initialize=initialize)
	def remove_signal(self):
		""" says to the interface: I don't care about new features anymore """
		feature_interfaces.feature_interface.remove_signal(self)
	#def plots(self,what = 'data'):
	#	self.plotter.plots(what)
	def find_where(self,band=None):
		return self.properties['data']
	def plots(self,list_what,band=None):
		self.iplot(list_what,band)
	def iplot(self,list_what,band=None):
		for what in list_what:
			self.plotter.plots(self.find_where(band)['input'],what)
		plotters.grid(True)
		plotters.legend()
	def xml_print(self):
		xml = amara.create_document(u"root")
		xml_where = xml
		waiting_dics = []
		dic = self.properties
		while 1:
			for key in dic:
				value = dic[key]
				xml_where[unicode(key)] = None
				if isinstance(value,dict):
					waiting_dics.append((value,xml_where[unicode(key)]))
				if isinstance(value,ResultObject):
					xml_where[unicode(key)] = value.xml_print()
				else:
					xml_where[unicode(key)] = value
			try:
				next_dic = waiting_dics.pop()
			except IndexError:
				break
			dic = next_dic[0]
			xml_where[1]
		return xml
			
					
					
				
		
class signal_generator(signal): #signal from random sine wave generator
	pass
class signal_with_bands(signal):
	def update(self,extract_method):
		for key in self.properties['data'].keys():
			if key == 'multiband':
				continue
			elif 'NOMAD' in key:
				# 20110517: dstarr adds this case since I want NOMAD color info available to color_diff_extractor.py, but I do not want to extract features for this "*:NOMAD" band.
				continue
			elif 'extinct_' in key:
				# 20110517: dstarr adds this case since I want (NED extinction) color info available to color_diff_extractor.py, but I do not want to extract features for this "extinct_*" band.
				continue
			if isinstance(extract_method,FeatureExtractor.ContextExtractor):
				write_where = self.find_where(band='multiband')
				myband = 'multiband'
			else:
				write_where = self.find_where(band=key)
				myband = key
			result = extract_method.extr(self.properties.copy(),band=myband) # we could decide not to send a copy if we trust our code
			if isinstance(extract_method,FeatureExtractor.FeatureExtractor):
				# 20080508: dstarr adds condition:
				if not extract_method.internal_use_only:
					write_where['features'][result.extname] = result
			elif isinstance(extract_method,FeatureExtractor.InterExtractor):
				write_where['inter'][result.extname] = result 
			else: raise "weird kinda of result, don't know what to do with it"
			#self.write_result(write_where,result)
	def default_band(self):
		print "Warning: using default band"
		return 'Vmag'
	def choose_plotter(self):
		self.plotter = plotters.plotter()
	def prinprop(self,list_what,band=None):
		if band == 'all':
			for aband in self.properties['data']:
				print aband,
				self.iprint(list_what,aband)
		else: self.iprint(list_what,band)
	def iprint(self,list_what,band=None):
		for what in list_what:
			print self.find_where(band)[what]
	def plots(self,list_what,band=None):
		if band == 'all':
			for aband in self.properties['data']:
				self.iplot(list_what,aband)
		else: self.iplot(list_what,band)
	def find_where(self,band=None):
		return self.properties['data'][band]
class signal_xml(signal_with_bands):
	def default_band(self):
		return 'z'
		
