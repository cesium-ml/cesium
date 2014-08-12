from ..FeatureExtractor import ContextFeatureExtractor

class gall_extractor(ContextFeatureExtractor): 
	"""the Galactic coordinate l (longitude) in degrees"""
	active = True
	extname = 'gall' #extractor's name

	def extract(self):
		posdict = self.fetch_extr('position_intermediate')

		if not posdict.has_key('gall') or posdict['gall'] is None:
			self.ex_error("bad gal-l in the intermediate extractor. check install of pyephem and input coordinates")
			
		return posdict['gall']

