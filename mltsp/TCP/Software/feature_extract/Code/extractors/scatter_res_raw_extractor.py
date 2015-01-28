from ..FeatureExtractor import FeatureExtractor

class scatter_res_raw_extractor(FeatureExtractor):
	""" From arXiv 1101_2406v1 Dubath 20110112  paper.

	Scatter:res/raw: 
	Median Absolute Deviation (MAD) of the  residuals 
	(obtained by subtracting model values from the raw light curve) 
	divided by the MAD of the raw light-curve values 
	around the median. 
	"""
	active = True
	extname = "scatter_res_raw"
	def extract(self):
		median_absolute_deviation = self.fetch_extr('median_absolute_deviation')
		lomb_dict = self.fetch_extr('lomb_scargle')
		mad_of_model_residuals = lomb_dict.get('mad_of_model_residuals',0.)
		return mad_of_model_residuals / median_absolute_deviation
