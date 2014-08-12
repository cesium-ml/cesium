from ..FeatureExtractor import FeatureExtractor

class beyond1std_extractor(FeatureExtractor):
	""" calculates the percentage of points that lie beyond one standard deviation from the weighted mean """
	active = True
	extname = 'beyond1std' #extractor's name
	def extract(self):
		self.x_devs()
		stdvs_from_u = self.fetch_extr('stdvs_from_u')
		dvs_from_u = 0
		for i in stdvs_from_u:
			if i > self.devs:
				dvs_from_u += 1
		try:
			ret_val = dvs_from_u / float(len(stdvs_from_u))
		except:
			self.ex_error(text="beyond1std_extractor")
		return ret_val
	def x_devs(self): # how many deviations ?
		self.devs = 1.0
