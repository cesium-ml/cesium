from ..FeatureExtractor import ContextFeatureExtractor

class ecpb_extractor(ContextFeatureExtractor): 
	"""the Ecliptic coordinate b (latitude) in degrees"""
	active = True
	extname = 'ecpb' #extractor's name

	def extract(self):
		posdict = self.fetch_extr('position_intermediate')

		if not posdict.has_key('ecb') or posdict['ecb'] is None:
			self.ex_error("bad ecb in the intermediate extractor. check install of pyephem and input coordinate")
			
		return posdict['ecb']

