from ..FeatureExtractor import InterExtractor
from common_functions.plot_methods import plot_vs_frequencies

class power_spectrum_extractor(plot_vs_frequencies,InterExtractor):
	active = False
	extname = 'power_spectrum' #extractor's name
	def extract(self):
		fourier = self.fetch_extr('fourier')
		if not isinstance(fourier,numpy.ndarray):
			self.ex_error("Did not receive the correct type as input")
		power_spec = abs(fourier)**2
		return power_spec
