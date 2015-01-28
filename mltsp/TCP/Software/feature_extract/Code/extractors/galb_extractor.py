from ..FeatureExtractor import ContextFeatureExtractor

class galb_extractor(ContextFeatureExtractor): 
	"""the Galactic coordinate b (latitude) in degrees"""
	active = True
	extname = 'galb' #extractor's name

	def extract(self):
		posdict = self.fetch_extr('position_intermediate')

		if 'galb' not in posdict or posdict['galb'] is None:
			self.ex_error("bad gal-b in the intermediate extractor. check install pyephem and input coordinates")
			
		return posdict['galb']

