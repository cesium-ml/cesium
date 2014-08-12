import numpy
from storage import storage

from gen_or_imp import gen_or_imp

class vizier_importer(gen_or_imp):
	name = 'vizier cepheids'
	def __init__(self,signals_list=[]):
		self.storer = storage()
		self.signals_list = signals_list
	def generate(self):
#		filepath = 'table.dat'
		filepath = 'table2.dat' #smaller version for testing purposes
		data = open(filepath, mode='r')
		self.signalgen={}
		first_line = data.readline()
		self.name = first_line[0:9]
		self.dates = [float(first_line[10:22])]
		self.mags = [float(first_line[24:29])]
		for line in data:
			if line[0:9] != self.name:
				self.set_outputs()
				self.store(self.signalgen)
				self.name = line[0:9]
				self.dates=[]
				self.mags=[]
			jd = line[10:22] #julian date, specified from http://vizier.u-strasbg.fr/viz-bin/Cat?II/217
			mag = line[24:29] #[-0.93/16.0]? V (Johnson) magnitude
			if mag != '     ':
				self.dates.append(float(jd))
				self.mags.append(float(mag))
		self.set_outputs()
		self.store(self.signalgen)
	def set_outputs(self):
		self.make_dics()
		self.for_input = self.sub_dics(self.signaldata['Vmag'])
		self.for_input = dict(time_data=numpy.array(self.dates,dtype=float), flux_data=numpy.array(self.mags,dtype=float), rms_data=numpy.ones(len(self.dates),dtype=float)/10.0)
#		self.signalgen['time_data']= numpy.array(self.dates,dtype=float)
#		self.signalgen['flux_data']= numpy.array(self.mags,dtype=float)
		self.signalgen['object_name'] = self.name
	def store(self,data):
		self.storer.store(data,self.signals_list)