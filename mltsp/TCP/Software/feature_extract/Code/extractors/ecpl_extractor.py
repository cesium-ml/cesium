from ..FeatureExtractor import ContextFeatureExtractor

class ecpl_extractor(ContextFeatureExtractor): 
	"""the Ecliptic coordinate l (longitude) in degrees"""
	active = True
	extname = 'ecpl' #extractor's name

	def extract(self):
		posdict = self.fetch_extr('position_intermediate')

		if 'ecl' not in posdict or posdict['ecl'] is None:
			self.ex_error("bad ecl in the intermediate extractor. check install of pyephem and input coordiantes")
			
		return posdict['ecl']

