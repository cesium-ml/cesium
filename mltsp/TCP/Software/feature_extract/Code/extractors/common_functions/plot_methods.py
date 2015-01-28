try:
	import pylab
except:
	pass
try:
	from pylab import *
except:
	pass

class plot_vs_time(object):
	""" inheritable function to plot oneself against the time axis """
	extname = 'plot vs time inheritable method' #extractor's name
	def plot_feature(self,properties):
		plot(self.time_data, properties[self.extname], label=self.extname)

class plot_vs_frequencies(object):
	""" inheritable function to plot oneself against the frequency axis """
	extname = 'plot vs frequency inheritable method'
	def plot_feature(self,properties):
		# dstarr hacks this since some 'results' are tuples with frequencies as the [1] element
		#plot(self.frequencies, properties[self.extname], label=self.extname)
		if len(properties[self.extname]) == 2:
			pylab.plot(properties[self.extname][1],properties[self.extname][0], 'bo')
			pylab.title(self.extname)
			pylab.show()
		else:
			#plot(self.frequencies, properties[self.extname], label=self.extname)
			pylab.plot(properties[self.extname], 'bo')
			pylab.title(self.extname)
			pylab.show()
		
class plot_vertical_line(object):
	""" inheritable function to plot oneself against the frequency axis """
	extname = 'plot vertical line inheritable method' #extractor's name
	def plot_feature(self,properties):
		print self.extname
		print properties[self.extname]
		axvline(x=properties[self.extname],label=self.extname)
class plot_horizontal_line(object):
	""" inheritable function to plot oneself horizontally """
	extname = 'plot horizontal line inheritable method' #extractor's name
	def plot_feature(self,properties):
		axhline(x=properties[self.extname],label=self.extname)
