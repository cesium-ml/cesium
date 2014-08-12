from ..FeatureExtractor import FeatureExtractor

from common_functions.Example_Methods import Example_Methods

class example_extractor(FeatureExtractor,Example_Methods):
	""" Just an example extractor skeleton.  For full example, see: 
	http://lyra.berkeley.edu/dokuwiki/doku.php?id=tcp:feature_testing
	"""
	internal_use_only = True
	active = True
	extname = 'example' # identifier used in final extracted value dict.
	def extract(self):
		ls_result_dict = self.fetch_extr('lomb_scargle')
		median_val = self.fetch_extr('median') # fetches the result from the media extractor (median_val is now the media value of the timecurve)
		summed_val = self.example_main_method(self.flux_data,lambda x: median_val,x=self.time_data,rms=self.rms_data) # returns sum(self.flux_data)
		return float(summed_val)/median_val
