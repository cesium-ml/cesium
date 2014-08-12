import numpy

class gen_or_imp(object):
	name = 'gen_or_imp'
	def make_dics(self):
		self.signalgen = {'source':self.name,'data':{}}
		self.signaldata = self.signalgen['data']
	def sub_dics(self,where):
		where['input'] = {} # to receive time, flux and rms data from the generators
		where['features'] = {} # to receive the extracted features later one
		where['inter'] = {} # to receive intermediary features later on (not a single number, but useful for extractors down the line)
		return where['input']