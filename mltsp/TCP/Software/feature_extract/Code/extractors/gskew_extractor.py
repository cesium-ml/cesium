from ..FeatureExtractor import FeatureExtractor
from numpy import median, sort, round
class gskew_extractor(FeatureExtractor):
	""" Doesnt really have anything to do with skew at all. I tested this on the RCBs that we found and its clear that they all have fairly negative ghetto skew. Of course, for RCBs near the detection limit this wont be that helpful, and for highly active RCBs it may not be great, but for your typical RCB is should separate out from other things. Im curious to see what this produces for SRPV and Mira sources.

Note - Ive arbitrarily selected 3 percent here. It could be 5 percent or 10, we should probably test a few different values to see how much difference it makes.

	"""
	active = True
	extname = 'gskew' # identifier used in final extracted value dict.
	def extract(self):
            """2012-06-12 Adam Miller coded
            """
            medmag = median(self.flux_data)
            sortmag = sort(self.flux_data)
            three_per = int(round(0.03*len(self.flux_data)))
            ghetto_skew = (medmag - median(sortmag[-three_per:])) + (medmag-median(sortmag[0:three_per]))
            return ghetto_skew
