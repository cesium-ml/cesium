from ..FeatureExtractor import FeatureExtractor

class pair_slope_trend_extractor(FeatureExtractor):
	"""percentage of pairs of points which continually rise, over total number number of pairs.
	
		We only want to run this on the last MAX_PAIRS points to see if there is an
		overall trend to the rise/fall.
		
		To account for plateaus, we devide by the total number of pairs examined, and
		not the total of rising/falling pairs.
		
		The slopes are not weighted, but you can change the value of PLATEAU_SLOPE
		to included values close to 0 as 0 slope.
		
		Blame: john m. brewer
	"""
	active = True
	extname = 'pair_slope_trend' # extractor name
	MAX_PAIRS = 30		# maximum number of pairs to examine from end of epochs
	PLATEAU_SLOPE = 0.0	# slope considered equal to 0
	
	def extract(self):
		rising = 0;
		falling = 0;
		lastpoint = len(self.time_data) - 1
		firstpoint = max(0,lastpoint-self.MAX_PAIRS)
		
		for i in range(firstpoint,lastpoint):
			fluxDiff = self.flux_data[i+1] - self.flux_data[i]
			timeDiff = self.time_data[i+1] - self.time_data[i]
			slope = fluxDiff/timeDiff
			rising += (slope > self.PLATEAU_SLOPE)
			falling += (slope < (0.0 - self.PLATEAU_SLOPE))
		
		return float(rising - falling)/max(1.0,(lastpoint - firstpoint))
