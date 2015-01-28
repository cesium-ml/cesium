import numpy
from numpy import log, exp, random, ones, arange
from storage import storage

from sgwindn_gen import sgwindn_gen

class uneven_sine_gen(sgwindn_gen):
	name = 'uneven sine with individual noise'
	def tgen(self):
		poiss = random.poisson(lam = 1000, size = 200) # 1000 = 1 day = expected time between measuremens
		poiss = poiss / 1000.0
		x_axis = ones(len(poiss),dtype=float)
		for i in arange(len(x_axis))[:-1]:
			x_axis[i+1] = x_axis[i] + poiss[i]
		return x_axis
	def fgen(self):
		noisetime = self.t
		#var = { 'x': noisetime, 'y': noisedata, 'ylabel': 'Amplitude', 'xlabel':'Time (s)' }
		N= len(noisetime)
		dt = 1.0 #findAverageSampleTime(var,0)
		maxlogx = log(1/(2*dt)) # max frequency is the sampling rate
		minlogx = log(1/(max(noisetime)-min(noisetime))) #min frequency is 1/T
		frequencies = exp(arange(N, dtype = float) / (N-1.) * (maxlogx-minlogx)+minlogx)
		return frequencies