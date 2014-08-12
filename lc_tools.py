#!/usr/bin/python
# filename: lc_tools.py


import re
import urllib2
try:
	from bs4 import BeautifulSoup
except:
	BeautifulSoup = False
import numpy as np
try:
	from matplotlib import pyplot as plt
except:
	pass
import scipy.stats as stats
import pickle as p
#from matplotlib.backends.backend_pdf import PdfPages
import heapq
#import pyPdf
#import lcs_db
import os
import sys
import cfg







'''Scalars to use:
				ra,
				dec,
				avg_mag,
				n_epochs,
				avg_err,
				med_err,
				std_err,
				start,
				end,
				total_time,
				avgt,
				cads_std,
				cads_avg,
				cads_med,
				cad_probs_1, ..., cad_probs_10000000, # 17 total incl. 1 & 10000000
				med_double_to_single_step,
				avg_double_to_single_step,
				std_double_to_single_step,
				all_times_hist_peak_val,
				all_times_hist_peak_bin,
				all_times_nhist_numpeaks,
				all_times_nhist_peak_val,
				all_times_nhist_peak_1_to_2, 1_to_3, 2_to_3, 1_to_4, 2_to_4, 3_to_4, # (6 total)
				all_times_nhist_peak1_bin, peak2_bin, peak3_bin, peak4_bin # 4 total
				
'''




class lightCurve:
	def __init__(self,epochs,mags,errs=[],ra='none',dec='none',source_id='none',time_unit='day',classname='unknown',band='unknown',features_to_use=[]):
		
		''' Extracts the following features (and all are lightCurve obj attrs):
				epochs: array of times of all observations,
				mags: array of magnitudes of observations,
				avg_mag: average magnitude,
				errs: array of errors or observations,
				n_epochs: the number of epochs,
				avg_err: average of the errors,
				med_err: median of the errors,
				std_err: standard deviation of the errors,
				start: time of first observation,
				end: time of last observation,
				total_time: end - start
				avgt: average time between observations, 
				cads: array of time between successive observations, 
				cads_std: standard deviation of cads
				cads_avg: average of cads
				cads_med: median of cads
				cad_probs: dictionary of time value (in minutes) keys and percentile score values for that time,
				cad_probs_1, etc: percentile score of cad_probs for 1 minute, etc,
				double_to_single_step: array of deltaT_3-1 to deltaT_3-2 ratios,
				med_double_to_single_step: median of double_to_single_step,
				avg_double_to_single_step: average of double_to_single_step,
				std_double_to_single_step: standard deviation of double_to_single_step,
				all_times: array of time intervals to all possible later observations from each obs in lc
				all_times_hist: histogram of all_times (list)
				all_times_bins: bin edges of histogram of all_times (list)
				all_times_hist_peak_val: peak value of all_times_hist
				all_times_hist_peak_bin: bin number of peak of all_times_hist
				all_times_hist_normed: all_times_hist normalized s.t. it sums to one
				all_times_bins_normed: all_times_bins normalized s.t. last bin edge equals one
				all_times_nhist_numpeaks: number of peaks in all_times_hist_normed
				all_times_nhist_peaks: list of up to four biggest peaks of all_times_hist_normed, each being a two-item list: [peak_val, bin_index]
				all_times_nhist_peak_1_to_2, etc: ratio of all_times histogram peak_1 to peak_2, etc
				all_times_nhist_peak1_bin, etc: bin number of 1st, etc peak of all_times_hist
				all_times_nhist_peak_val: peak value of all_times_hist_normed
				
			Additional attrs:
				time_unit: string specifying time unit (i.e. 'day')
				id: dotAstro source id (string)
				classname: string, name of class if part of training set
				ra: right ascension (decimal degrees),
				dec: declination (decimal degrees),
				band: observation band
				
			
		'''
		
		self.time_unit = time_unit
		self.id = str(source_id)
		self.classname = classname
		self.start = epochs[0]
		self.end = epochs[-1]
		self.total_time = self.end - self.start
		self.epochs = epochs
		self.n_epochs = len(epochs)
		self.errs = errs
		self.mags = mags
		self.avg_mag = np.average(mags)
		self.ra = ra
		self.dec = dec
		self.band = band
		self.avgt = round((self.total_time)/(float(len(epochs))),3)
		self.cads = []
		
		self.double_to_single_step = []
		self.all_times = []
		
		if len(errs) > 0:
			self.avg_err = np.average(errs)
			self.med_err = np.median(errs)
			self.std_err = np.std(errs)
		else:
			self.avg_err = None
			self.med_err = None
			self.std_err = None
		
		
		
		for i in range(len(epochs)):
			
			# all the deltaTs (time to next obs)
			try:
				self.cads.append(epochs[i+1]-epochs[i])
			except IndexError:
				pass
			
			# ratio of time to obs after next to time to next obs
			try:
				self.double_to_single_step.append((epochs[i+2]-epochs[i])/(epochs[i+2]-epochs[i+1]))
			except IndexError:
				pass
			except ZeroDivisionError:
				pass
			
			
			# all possible deltaTs ()
			for j in range(1,len(epochs)):
				try:
					self.all_times.append(epochs[i+j]-epochs[i])
				except IndexError:
					pass
		
		self.all_times_std = np.std(self.all_times)
		self.all_times_med = np.median(self.all_times)
		self.all_times_avg = np.average(self.all_times)
		
		hist, bins = np.histogram(self.all_times,bins=50)
		nhist, bins = np.histogram(self.all_times,bins=50,normed=True)
		self.all_times_hist = hist
		self.all_times_bins = bins
		self.all_times_hist_peak_val = np.max(hist)
		self.all_times_hist_peak_bin = np.where(hist==self.all_times_hist_peak_val)[0][0]
		self.all_times_hist_normed = nhist
		self.all_times_bins_normed = bins/np.max(self.all_times)
		self.all_times_nhist_peak_val = np.max(nhist)
		
		peaks = [] # elements are lists: [peak, index]
		for peak in heapq.nlargest(10,nhist):
			index = np.where(nhist == peak)[0][0]
			try:
				if nhist[index-1] < peak and nhist[index+1] < peak:
					peaks.append([peak,index])
				elif nhist[index-1] == peak:
					if nhist[index-2] < peak:
						peaks.append([peak,index])
				elif nhist[index+1] == peak:
					if nhist[index+2] < peak:
						peaks.append([peak,index])
			except IndexError:
				# peak is first or last entry
				peaks.append([peak,index])
		
		peaks = sorted(peaks,key=lambda x:x[1])
		
		self.all_times_nhist_peaks = peaks[:4]
		self.all_times_nhist_numpeaks = len(peaks)
		if len(peaks) > 0:
			self.all_times_nhist_peak1_bin = peaks[0][1]
		else:
			self.all_times_nhist_peak1_bin = None
		self.all_times_nhist_peak_1_to_2, self.all_times_nhist_peak_1_to_3, self.all_times_nhist_peak_2_to_3, \
			self.all_times_nhist_peak_1_to_4, self.all_times_nhist_peak_2_to_4, \
			self.all_times_nhist_peak_3_to_4 = [None,None,None,None,None,None]
		self.all_times_nhist_peak4_bin, self.all_times_nhist_peak3_bin, self.all_times_nhist_peak2_bin = [None,None,None]
		if len(peaks) >= 2:
			self.all_times_nhist_peak_1_to_2 = peaks[0][0]/peaks[1][0]
			self.all_times_nhist_peak2_bin = peaks[1][1]
			if len(peaks) >= 3:
				self.all_times_nhist_peak_2_to_3 = peaks[1][0]/peaks[2][0]
				self.all_times_nhist_peak_1_to_3 = peaks[0][0]/peaks[2][0]
				self.all_times_nhist_peak3_bin = peaks[2][1]
				if len(peaks) >= 4:
					self.all_times_nhist_peak_1_to_4 = peaks[0][0]/peaks[3][0]
					self.all_times_nhist_peak_2_to_4 = peaks[1][0]/peaks[3][0]
					self.all_times_nhist_peak_3_to_4 = peaks[2][0]/peaks[3][0]
					self.all_times_nhist_peak4_bin = peaks[3][1]
			
		
		
		self.avg_double_to_single_step = np.average(self.double_to_single_step)
		self.med_double_to_single_step = np.median(self.double_to_single_step)
		self.std_double_to_single_step = np.std(self.double_to_single_step)
		
		self.cads_std = np.std(self.cads)
		self.cads_avg = np.average(self.cads)
		self.cads_med = np.median(self.cads)
		
		self.cad_probs = {}
		for time in [1,10,20,30,40,50,100,500,1000,5000,10000,50000,100000,500000,1000000,5000000,10000000]:
			if self.time_unit == 'day':
				self.cad_probs[time] = stats.percentileofscore(self.cads,float(time)/(24.0*60.0))/100.0
			elif self.time_unit == 'hour':
				self.cad_probs[time] = stats.percentileofscore(self.cads,float(time))/100.0
		
		self.cad_probs_1 = self.cad_probs[1]
		self.cad_probs_10 = self.cad_probs[10]
		self.cad_probs_20 = self.cad_probs[20]
		self.cad_probs_30 = self.cad_probs[30]
		self.cad_probs_40 = self.cad_probs[40]
		self.cad_probs_50 = self.cad_probs[50]
		self.cad_probs_100 = self.cad_probs[100]
		self.cad_probs_500 = self.cad_probs[500]
		self.cad_probs_1000 = self.cad_probs[1000]
		self.cad_probs_5000 = self.cad_probs[5000]
		self.cad_probs_10000 = self.cad_probs[10000]
		self.cad_probs_50000 = self.cad_probs[50000]
		self.cad_probs_100000 = self.cad_probs[100000]
		self.cad_probs_500000 = self.cad_probs[500000]
		self.cad_probs_1000000 = self.cad_probs[1000000]
		self.cad_probs_5000000 = self.cad_probs[5000000]
		self.cad_probs_10000000 = self.cad_probs[10000000]
		
	
	
	def extractScienceFeatures(self):
		return
	
	
	def showInfo(self):
		print [self.start,self.end,len(self.epochs),self.avgt]
	
	
	
	def showAllInfo(self):
		for attr, val in vars(self).items():
			print attr, ":", val

	
	def allAttrs(self):
		count = 0
		for attr, val in vars(self).items():
			print attr
			count += 1
		print count, "attributes total."


	def put(self,cursor):
		
		
		return

	def generate_features_dict(self):
		features_dict = {}
		for attr, val in vars(self).items():
			if attr in cfg.features_list:
				features_dict[attr] = val
		return features_dict



def generate_features_dict(lc_obj):
	return lc_obj.generate_features_dict()






def makePdf(sources):
	pdf = PdfPages("sample_features.pdf")
	classnames = []
	classname_dict = {}
	x = 2 # number of subplot columns
	y = 3 # number of subplot rows
	for source in sources:
		lc = source.lcs[0]
		
		if lc.classname not in classnames:
			classnames.append(lc.classname)
			classname_dict[lc.classname] = [lc]
		else:
			classname_dict[lc.classname].append(lc)
			
		if len(classname_dict[lc.classname]) < 3:
		
			label = lc.classname + "; ID: " + lc.id
			# all_times histogram:
			fig = plt.figure()
			ax = fig.add_subplot(111)
			ax.set_title(label)
			ax.axis('off')
			
			
			ax1 = fig.add_subplot(321)
			ax2 = fig.add_subplot(322)
			ax2.axis('off')
			ax3 = fig.add_subplot(323)
			ax4 = fig.add_subplot(324)
			ax4.axis('off')
			ax5 = fig.add_subplot(325)
			ax6 = fig.add_subplot(326)
			ax6.axis('off')
			
			
			hist, bins, other = ax1.hist(lc.all_times,50,normed=True)
			ax1.text(np.max(bins)*0.1,np.max(hist)*0.8,r'Histogram (normed) of all $\Delta$Ts')
			
			ax2.text(0.0,0.9,r'$\bullet$med time to next obs: ' + str(np.round(lc.cads_med,4)))
			ax2.text(0.0,0.75,r'$\bullet$avg time to next obs: ' + str(np.round(lc.avgt,4)))
			ax2.text(0.0,0.6,r'$\bullet$std dev of time to next obs: ' + str(np.round(lc.cads_std,4)))
			ax2.text(0.0,0.45,r'$\bullet$med of all $\Delta$Ts: ' + str(np.round(lc.all_times_med,4)))
			ax2.text(0.0,0.3,r'$\bullet$avg of all $\Delta$Ts: ' + str(np.round(lc.all_times_avg,4)))
			ax2.text(0.0,0.15,r'$\bullet$std dev of all $\Delta$Ts: ' + str(np.round(lc.all_times_std,4)))
			
			hist, bins, other = ax3.hist(lc.cads,50)
			ax3.text(np.max(bins)*0.1,np.max(hist)*0.8,r'Hist of time to next obs')
			
			ax6.text(0.0,0.9,r'$\bullet$Number of epochs: ' + str(lc.n_epochs))
			ax6.text(0.0,0.75,r'$\bullet$Time b/w first & last obs (days): ' + str(np.round(lc.total_time,2)))
			ax6.text(0.0,0.6,r'$\bullet$Average error in mag: ' + str(np.round(lc.avg_err,4)))
			ax6.text(0.0,0.45,r'$\bullet$Median error in mag: ' + str(np.round(lc.med_err,4)))
			ax6.text(0.0,0.3,r'$\bullet$Std dev of error: ' + str(np.round(lc.std_err,4)))
			ax6.text(0.0,0.15,'')
			
			ax5.scatter(lc.epochs,lc.mags)
			
			ax4.text(0.0,0.9,r'$\bullet$Avg double to single step ratio: ' + str(np.round(lc.avg_double_to_single_step,3)))
			ax4.text(0.0,0.75,r'$\bullet$Med double to single step: ' + str(np.round(lc.med_double_to_single_step,3)))
			ax4.text(0.0,0.6,r'$\bullet$Std dev of double to single step: ' + str(np.round(lc.std_double_to_single_step,3)))
			ax4.text(0.0,0.45,r'$\bullet$1st peak to 2nd peak (in all $\Delta$Ts): ' + str(np.round(lc.all_times_nhist_peak_1_to_2,3)))
			ax4.text(0.0,0.3,r'$\bullet$2ndt peak to 3rd peak (in all $\Delta$Ts): ' + str(np.round(lc.all_times_nhist_peak_2_to_3,3)))
			ax4.text(0.0,0.15,r'$\bullet$1st peak to 3rd peak (in all $\Delta$Ts): ' + str(np.round(lc.all_times_nhist_peak_1_to_3,3)))
			
			pdf.savefig(fig)
	
	
	pdf.close()
	
	
	pdf = PdfPages('feature_plots.pdf')
	
	fig = plt.figure()
	
	ax1 = fig.add_subplot(221)
	ax2 = fig.add_subplot(222)
	ax3 = fig.add_subplot(223)
	ax4 = fig.add_subplot(224)
	
	plt.subplots_adjust(wspace=0.4,hspace=0.4)
	
	classnamenum = 0
	
	
	colors = ['red','yellow','green','blue','gray','orange','cyan','magenta']
	for classname, lcs in classname_dict.items():
		classnamenum += 1
		print classname, len(lcs), 'light curves.'
		attr1 = []
		attr2 = []
		attr3 = []
		attr4 = []
		attr5 = []
		attr6 = []
		attr7 = []
		attr8 = []
		for lc in lcs:
			attr1.append(lc.n_epochs)
			attr2.append(lc.avgt)
			attr3.append(lc.cads_std)
			attr4.append(lc.total_time)
			attr5.append(lc.all_times_hist_peak_val)
			attr6.append(lc.cad_probs[5000])
			attr7.append(lc.all_times_nhist_peak_1_to_3)
			attr8.append(lc.all_times_nhist_peak_val)
		
		
		
		
		ax2.scatter(attr1,attr2,color=colors[classnamenum],label=classname)
		ax1.scatter(attr3,attr4,color=colors[classnamenum],label=classname)
		ax2.set_xlabel('N Epochs')
		ax2.set_ylabel('Avg time to next obs')
		ax1.set_xlabel('Standard dev. of time to next obs')
		ax1.set_ylabel('Time b/w first and last obs')
		
		ax3.scatter(attr5,attr6,color=colors[classnamenum],label=classname)
		ax4.scatter(attr7,attr8,color=colors[classnamenum],label=classname)
		ax3.set_xlabel(r'All $\Delta$T hist peak val')
		ax3.set_ylabel('Prob time to next obs <= 5000 min')
		ax4.set_xlabel(r'$\Delta$Ts normed hist peak 1 to peak 3')
		ax4.set_ylabel(r'Peak val of all $\Delta$Ts normed hist')
		
		
	#ax1.legend(bbox_to_anchor=(1.1, 1.1),prop={'size':6})
	ax2.legend(bbox_to_anchor=(1.1, 1.1),prop={'size':6})
	#ax3.legend(loc='upper right',prop={'size':6})
	#ax4.legend(loc='upper right',prop={'size':6})
	
	
	pdf.savefig(fig)
		
	pdf.close()
	return









def generate_lc_snippets(lc):
	epochs,mags,errs = [lc.epochs,lc.mags,lc.errs]
	lc_snippets = []
	n_epochs = len(epochs)
	for binsize in [20,40,70,100,150,250,500,1000,10000]:
		nbins = 0
		if n_epochs > binsize:
			bin_edges = np.linspace(0,n_epochs-1,int(round(float(n_epochs)/float(binsize)))+1)
			#for chunk in list(chunks(range(n_epochs),binsize)):
			bin_indices = range(len(bin_edges)-1)
			np.random.shuffle(bin_indices)
			for i in bin_indices:
				nbins += 1
				if int(round(bin_edges[i+1])) - int(round(bin_edges[i])) >= 10 and nbins < 4:
					lc_snippets.append(lightCurve(epochs[int(round(bin_edges[i])):int(round(bin_edges[i+1]))],mags[int(round(bin_edges[i])):int(round(bin_edges[i+1]))],errs[int(round(bin_edges[i])):int(round(bin_edges[i+1]))],classname=lc.classname))
	
	return lc_snippets







class Source:
	def __init__(self,id,lcs,classname='unknown'):
		self.lcs = []
		self.lc_snippets = []
		self.id = id
		self.classname = classname
		for lc in lcs:
			self.lcs.append(lc)
			self.lc_snippets.extend(generate_lc_snippets(lc))
	
	def showInfo(self):
		print "dotAstro ID: " + str(self.id) + "Num LCs: " + str(len(self.lcs))
	
	def plotCadHists(self):
		n_lcs = len(self.lcs)
		if n_lcs > 0:
			x = int(np.sqrt(n_lcs))
			y = n_lcs/x + int(n_lcs%x > 0)
			plotnum = 1
			for lc in self.lcs:
				plt.subplot(x,y,plotnum)
				plt.hist(lc.cads,50,range=(0,np.std(lc.cads)*2.0))
				plt.xlabel('Time to next obs.')
				plt.ylabel('# Occurrences')
				plotnum += 1
			plt.show()
		return
	
	def put(self, cursor, lc_cursor):
		cursor.execute("INSERT INTO sources VALUES(?, ?)",(self.id, self.classname))
		for lc in self.lcs:
			lc.put(lc_cursor)











def getMultiple(source_ids,classname='unknown'):
	'''Returns an array of Source objects corresponding to source IDs in source_ids.
		source_ids is either a filename or an array of dotAstro IDs.
	'''
	if type(source_ids) == str:
		f = open(source_ids,'r')
		ids = f.read().split()
		f.close()
	elif type(source_ids) == list:
		ids = source_ids
	
	# assuming dotAstro IDs:
	sources = []
	for id in ids:
		lc = getLcInfo(id,classname)
		if lc: # getLcInfo returns False if no data found
			sources.append(lc)
	
	return sources







def getLcInfo(id,classname='unknown'):
	id = str(id)
	isError = False
	if("http" in id):
		url = id
	elif id.isdigit():
		url = "http://dotastro.org/lightcurves/vosource.php?Source_ID=" + id
	try:
		lc = urllib2.urlopen(url).read()
		if lc.find("<TD>") == -1:
			raise urllib2.URLError('No data for specified source ID.')
			
	except (IOError, urllib2.URLError) as error:
		print "Could not read specified file.", id, error
		isError = True
		return False
	except Exception as error:
		print "Error encountered.", id, error
		isError = True
		return False
	
	if not isError:
		lcs = dotAstroLc(lc,id,classname)
		newSource = Source(id,lcs,classname)
		#print len(lcs), "light curves processed for source", id
		return newSource
	
	return










def dotAstroLc(lc,id,classname):
	lcs = []
	numlcs = 0
	data = lc
	soup = BeautifulSoup(data)
	try:
		ra = float(soup('position2d')[0]('value2')[0]('c1')[0].renderContents())
		dec = float(soup('position2d')[0]('value2')[0]('c2')[0].renderContents())
	except IndexError:
		print 'position2d/value2/c1 or c2 tag not present in light curve file'
		ra, dec = [None,None]
	time_unit = []
	for timeunitfield in soup(ucd="time.epoch"):
		time_unit.append(timeunitfield['unit'])
	
	for data_table in soup('tabledata'):
	
		epochs = []
		mags = []
		errs = []
		
		for row in data_table('tr'):
			tds = row("td")
			epochs.append(float(tds[0].renderContents()))
			mags.append(float(tds[1].renderContents()))
			errs.append(float(tds[2].renderContents()))
			
		if len(epochs) > 0:
			lcs.append(lightCurve(epochs,mags,errs,ra,dec,id,time_unit[numlcs],classname))
			numlcs += 1
	
	return lcs











def getMultipleLocal(filenames,classname='unknown'):
	sources = []
	for filename in filenames:
		sources.append(getLocalLc(filename,classname))
	return sources





def csvLc(lcdata,classname='unknown',sep=',',single_obj_only=False):
	lcdata = lcdata.split('\n')
	epochs = []
	mags = []
	errs = []
	for line in lcdata:
		line = line.replace("\n","")
		if len(line.split()) > len(line.split(sep)):
			sep = ' '
		if len(line) > 0:
			if line[0] != "#":
				if sep.isspace():
					els = line.split()
				else:
					els = line.split(sep)
				if len(els) == 3:
					epochs.append(float(els[0]))
					mags.append(float(els[1]))
					errs.append(float(els[2]))
				elif len(els) == 2:
					epochs.append(float(els[0]))
					mags.append(float(els[1]))
				else:
					print len(els), "elements in row - cvsLc()"
	if len(epochs) > 0:
		if single_obj_only:
			lc = lightCurve(epochs,mags,errs,classname=classname)
		else:
			lc = [lightCurve(epochs,mags,errs,classname=classname)]
		return lc
	else:
		print 'csvLc() - No data.'
		return []




def getLocalLc(filename,classname='unknown',sep=',',single_obj_only=False,ts_data_passed_directly=False):
	
	
	if ts_data_passed_directly:
		lcdata = filename
		for i in range(len(lcdata)):
			try:
				lcdata[i] = ','.join(lcdata[i])
			except Exception as theError:
				for j in range(len(lcdata[i])):
					lcdata[i][j] = str(lcdata[i][j])
				lcdata[i] = ','.join(lcdata[i])
	else:
		f = open(filename, 'r')
		lcdata = []
		for line in f.readlines():
			lcdata.append(line.replace('\n',''))
		f.close()
	lcdata = '\n'.join(lcdata)
	if lcdata.find("<Position2D>") > 0 and lcdata.find("xml") > 0:
		lcs = dotAstroLc(lcdata,filename,classname)
	else:
		lcs = csvLc(lcdata,classname,sep,single_obj_only=single_obj_only)
	if single_obj_only:
		return lcs
	else:
		#print len(lcs), "light curves processed for", filename
		newSource = Source(filename,lcs,classname)
		return newSource







def generate_timeseries_features(filename,classname='unknown',sep=',',single_obj_only=True,ts_data_passed_directly=False):
	lc_obj = getLocalLc(filename,classname=classname,sep=sep,single_obj_only=single_obj_only,ts_data_passed_directly=ts_data_passed_directly)
	features_dict = lc_obj.generate_features_dict()
	return features_dict





def dotAstro_to_csv(id):
	id = str(id)
	isError = False
	if("http" in id):
		url = id
	elif id.isdigit():
		url = "http://dotastro.org/lightcurves/vosource.php?Source_ID=" + id
	else:
		print "dotAstro ID not a digit."
	try:
		lc = urllib2.urlopen(url).read()
		if lc.find("<TD>") == -1:
			raise urllib2.URLError('No data for specified source ID.')
			
	except (IOError, urllib2.URLError) as error:
		print "Could not read specified file.", id, error
		isError = True
		return False
	except Exception as error:
		print "Error encountered.", id, error
		isError = True
		return False
	
	
	lcs = []
	numlcs = 0
	lcdata = lc
	soup = BeautifulSoup(lcdata)
	try:
		ra = float(soup('position2d')[0]('value2')[0]('c1')[0].renderContents())
		dec = float(soup('position2d')[0]('value2')[0]('c2')[0].renderContents())
	except IndexError:
		print 'position2d/value2/c1 or c2 tag not present in light curve file'
		ra, dec = [None,None]
	time_unit = []
	for timeunitfield in soup(ucd="time.epoch"):
		time_unit.append(timeunitfield['unit'])
	
	for data_table in soup('tabledata'):
		csv_str = ""
		for row in data_table('tr'):
			tds = row("td")
			if len(tds) == 3:
				csv_str += ','.join([str(tds[0].renderContents()),str(tds[1].renderContents()),str(tds[2].renderContents())]) + '\n'
			
		if len(csv_str) > 0:
			lcs.append(csv_str)
			numlcs += 1
	
	return lcs

testurl = 'http://timemachine.iic.harvard.edu/search/lcdb/astobject/lightcurve/135278496/download=ascii/pro=cal/'


def parse_harvard_lc(id):
	id = str(id)
	url = "http://timemachine.iic.harvard.edu/search/lcdb/astobject/lightcurve/ID/download=ascii/pro=cal/".replace("ID",id)
	lc = urllib2.urlopen(url).read().split("\n")
	lcdata = ""
	for line in lc:
		if len(line) > 0:
			if line[0] != "#":
				lcdata += ",".join(line.split()) + "\n"
	return [lcdata]
