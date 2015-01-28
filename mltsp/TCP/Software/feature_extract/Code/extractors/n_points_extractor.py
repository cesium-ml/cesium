from ..FeatureExtractor import FeatureExtractor

class n_points_extractor(FeatureExtractor):
	active = True
	extname = 'n_points' # identifier used in final extracted value dict.
	def extract(self):
		n_val = len(self.flux_data) # number of photometric points in the light curve
		return n_val
