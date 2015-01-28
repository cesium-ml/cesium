from ..FeatureExtractor import FeatureExtractor

class chi2_per_deg_extractor(FeatureExtractor): #Chi Square per degree of freedom
	active = 1
	active = True
	extname = 'chi2_per_deg' #extractor's name
	def extract(self):
		chi2 = self.fetch_extr('chi2')
		degrees = len(self.flux_data) - 1
		chi2_per_degrees = chi2 / degrees
		return chi2_per_degrees
