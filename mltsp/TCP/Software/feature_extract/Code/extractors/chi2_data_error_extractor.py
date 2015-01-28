from ..FeatureExtractor import FeatureExtractor

class chi2_data_error_extractor(FeatureExtractor):
	active = True
	extname = 'chi2_data_error' # identifier used in final extracted value dict.
	def extract(self):
		mean_val = self.fetch_extr('weighted_average')
		chi2 = sum( ((self.flux_data-mean_val)/self.rms_data)**2 )
		return chi2
