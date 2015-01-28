from ..FeatureExtractor import FeatureExtractor

class wei_av_uncertainty_extractor(FeatureExtractor): ### REDUNDANT
	active = False
	extname = 'wei_av_uncertainty' #extractor's name
	def extract(self):
		uncertainty = 1.0/(self.rms_data**(2)).sum()
		return uncertainty
