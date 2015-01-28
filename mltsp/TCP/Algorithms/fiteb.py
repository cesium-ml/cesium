#!/usr/bin/env python

"""
EB fitting code wrapping around JKTEBOP (http://www.astro.keele.ac.uk/~jkt/codes/jktebop.html)

v1.0 written by J. S. Bloom
v1.1 updated by dstarr

From the command line:

 a) this will fit dotastro source 237224 on a period of 2.55535306 and plot the results
  ./fiteb.py 237224 2.55535306 -p
 
 b) this will fit dotastro source 237224 on a period of 2.55535306 and plot the results using 
   alternative starting point 0
  ./fiteb.py 237224 2.55535306 -p -a --altnum=0

 c) this will fit dotastro source 237224 on a period of 2.55535306 and plot the results using 
   alternative starting point 1
  ./fiteb.py 237224 2.55535306 -p -a --altnum=1

 d)  will fit dotastro source 237224 on a period of 2.55535306 and plot the results using
   all three starting points. Finding the best fit result and the best harmonic of the period
      ./fiteb.py 237224 2.55535306 -p -s -a
   *** this is the preferred usage to make sure you have a wide sweep over parameter space

From the command line, the meat of the code can be run in three different ways:

 a) Dotastro source, where the XML is grabbed off of the web
     e = fiteb.EB(dotastro_id=217688,period=2.76901598*2,use_xml=True)
     e.run()
     e.plot()

	  # you can grab the time-series recarray
	  newrecarray = numpy.rec.fromarrays([e.ts['V:table542421']['t'],e.ts['V:table542421']['m'],\
	                e.ts['V:table542421']['m_err']],names='t,m,m_err',formats='f8,f8,f8')
	
 b) From a timeseries numpy recarray
     b = fiteb.EB(dotastro_id=217688,period=2.76901598*2,use_xml=False,rec_array=newrecarray)
     # here the dotastro id isn't really used other than as a placeholder for the bookkeeping
     b.run()
     b.plot()

 options to run():
   fittype=3,sigma=3.0

   fittype = same types as on the JKTEBOP website. 3 is the quick and dirty one. 4 does sigma clipping
    sigma = 3.0  (used for fittype 4)

 c) You can also try to do model selection when you're not confident which period is correct:

  p = fiteb.period_select(225431,11.9680949,try_alt=True)
  # this will search over period 1/2, 1, and 2x the input period, returning the period with the best chisq
  # this should also work with a recarray as in case b) above. try_alt will use three different starting points



"""

import urllib2, urllib
import os, sys
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
              'Software/feature_extract/Code'))
import db_importer
import matplotlib


from matplotlib import pylab as plt
from matplotlib import mlab
import numpy
import argparse

__author__ = "JS Bloom (UC Berkeley)"
__version__ = "12 May 2011"

rez_dict = {"Reduced chi-squared from errorbars:": "chisq", "Number of degrees of freedom:": "dof",\
			"Oblateness of the secondary star:": "ob2", "Oblateness of the primary star:": "ob1", \
			"Geometric reflection coeff (star B):": "reflect2", "Geometric reflection coeff (star A):": "reflect1",\
			"Omega (degrees):": "omega_deg", "Eccentricity:": "e", "Secondary contrib'n to system light:": "l2", \
			"Primary contribut'n to system light:": "l1", "Fractional secondary radius:": "r2", "Fractional primary radius:": "r1",
			"Phase of primary eclipse:": "primary_eclipse_phase", "Orbit inclination": "i", "Mass ratio (q)": "q",
			"Ephemeris timebase": "t0", "Orbital period (P)": "period", "Surf. bright. ratio": "l1/l2"}


class EB:
	
	dotastro_url = "http://dotastro.org/lightcurves/vosource.php?Source_ID="
	xml_dir  = "XML/"
	phot_dir = "Phot/"
	rez_dir  = "Results/"
	
	# newrecarray = numpy.rec.fromarrays([e.ts['V:table542421']['t'],e.ts['V:table542421']['m'],e.ts['V:table542421']['m_err']],names='t,m,m_err',formats='f8,f8,f8')
	
	#def __init__(self,dotastro_id=216313,period=0.97154408):
	
	def __init__(self,dotastro_id=217688,period=2.76901598*2,use_xml=True,rec_array=None,verbose=True):
		"""
		rec_array should have t, m, m_err at the column names
		"""
		self.dotastro_id = dotastro_id
		self.gotxml = False
		self.outname = None
		self.photkey = None
		self.period = period
		self.use_xml = use_xml
		self.rec_array = rec_array
		self.outrez = {'valid': False, 'chisq':None}
		self.verbose= verbose
		
	def run(self,fittype=3,sigma=3.0,try_alt=False,altnum=1):
		
		inf, outf, outpar, outfit = self._prep_infiles(fittype=fittype,sigma=sigma,try_alt=try_alt,altnum=altnum)
		if inf is None or outf is None:
			print "Sorry. Refusing to go further here."
			return 
		for x in [outf, outpar, outfit]:
			if os.path.exists(x):
				os.remove(x)
		
		os.system("./timeout 240 ./jktebop " + inf)

		# replace the output
		f = open(outf,"r")
		ff = f.readlines()
		f.close()
		if len(ff) == 0:
			print "!!! len(ff) == 0", 
			self.outrez = {'valid': False, 'okfit': False, 'fittype':fittype,'chisq':None, "parameter_file": "", "outfile": ""}
			return
		ff[0] = ff[0].replace("#"," ")
		f = open(outf,"w")
		f.writelines(ff)
		f.close()
		self.outf = outf
		
		# gobble up the output
		self.outrez = self._gobbleout(outpar,fittype=fittype)
		if self.verbose:
			print "Summary of Results (see %s for more info):" % self.outrez.get('parameter_file')
			print "*"*40
			print "Chisq/dof:", self.outrez.get('chisq')
			print "Is this an Ok fit (chisq aside)?", self.outrez.get("okfit")
			print "period:", self.outrez.get('period'), "day"
			print 'eccentricity', self.outrez.get('e')
			try:
				print "(r1 + r2)/a:", self.outrez.get('r1') + self.outrez.get('r2')
				print "r1/r2:", self.outrez.get('r1')/self.outrez.get('r2')
			except:
				pass
			
			print 'r1 overflow:', self.outrez.get('r1overflow')
			print 'r2 overflow:', self.outrez.get('r2overflow')
			print 'classification:', self.outrez.get('class')
			print "inclination:", self.outrez.get('i'), "+-", self.outrez.get('i_err'), " deg"
			print "mass ratio (q):", self.outrez.get('q'), "+-", self.outrez.get('q_err')
			print "lum ratio (l1/l2):", self.outrez.get('l1/l2'), "+-", self.outrez.get('l1/l2_err')
			print "*"*40
			print ""
			
	def _gobbleout(self,outfile,fittype=None):
		rez = {'valid': False, 'okfit': False, 'fittype':fittype,'chisq':None, "parameter_file": outfile, "outfile": self.outf}
		if not os.path.exists(outfile):
			return rez
		
		f = open(outfile,"r")
		ff = f.readlines()
		f.close()
		ff.reverse()  # look backwards
		failed = False
		kys = rez_dict.keys()
		for l in ff:
			for k in kys:
				if l.find(k) != -1:
					tmp = l.split(k)[-1]
					if tmp.find("+/-") != -1:
						## this has an error bar
						tmp1 = tmp.split("+/-")
						try:
							rez.update({rez_dict[k]: float(tmp1[0])})
						except:
							failed = True
						try:
							rez.update({rez_dict[k]+"_err": float(tmp1[1])})
						except:
							rez.update({rez_dict[k]+"_err": None})
							
					else:
						tmp = tmp.strip()
						tmp1 = tmp.split(" ")
						try:
							rez.update({rez_dict[k]: float(tmp1[0])})
						except:
							failed = True
					kys.remove(k)
					break
		rez.update({"valid": True})
		try:
			if rez['l1/l2'] > -0.05 and rez['reflect1'] > 0.0:
				if not failed:
					rez['okfit'] = True
		except:
			rez['okfit'] = False
			
		if ((not rez.has_key('r2')) or (not rez.has_key('r1'))) and (rez['okfit'] == False):
			return rez
		if rez['r2'] > 0 and rez['r1'] > 0:
			
			q = (rez['r2']/rez['r1'])**1.534 
			vv1 = (0.49*q**(-2./3))/(0.6*q**(-2./3) + numpy.log(1 + q**(-1./3)))
			vv2 = (0.49*q**(2./3))/(0.6*q**(2./3) + numpy.log(1 + q**(1./3)))
			print q, rez['r1'], vv1, rez['r2'], vv2
			if q <= 1:
				r1over = rez['r1'] > vv1*0.95
				r2over = rez['r2'] > vv2*0.95
			else:
				## fit gave the wrong r1 and r2 (r2 should be smaller)
				r2over = rez['r2'] > vv1*0.95
				r1over = rez['r1'] > vv2*0.95			
			
			rez.update({'r1overflow': r1over, 'r2overflow': r2over})
			if not r1over and not r2over:
				cl = 'detached'
			elif r1over and r2over:
				cl = 'contact'
			else:
				cl = 'semi-detached'
			rez.update({'class': cl})
		else:
			rez.update({'class': 'unknown'})

		return rez
		
	def plot(self,outf = None,dosave=True,savedir="Plot/",show=True):
		if outf is None:
			outf = self.outf
		#print outf
		oo = mlab.csv2rec(outf,delimiter=" ")
		#print oo
		plt.errorbar(oo['time'] % self.period, oo['magnitude'], oo['error'], fmt="b.")
		plt.plot(oo['time'] % self.period, oo['model'],"ro")
		plt.title("#%i P=%f d (chisq/dof = %f) r1+r2=%f" % (self.dotastro_id,self.period,self.outrez['chisq'],\
			self.outrez.get('r1') + self.outrez.get('r2')))
		ylim = plt.ylim()
		#print ylim
		if ylim[0] < ylim[1]:
			plt.ylim(ylim[1],ylim[0])
		plt.draw()
		if show:
		   plt.show()
                if dosave:
			if not os.path.isdir(savedir):
				os.mkdir(savedir)
			plt.savefig("%splot%i.png" % (savedir,self.dotastro_id))#,self.period))
			print "Saved", "%splot%i.png" % (savedir,self.dotastro_id)#,self.period)
		plt.clf()
			
	def _prep_infiles(self,dotastro_id=None,fittype=3,sigma=3.0,ntries=20,try_alt=False,altnum=1):
		if dotastro_id is None:
			dotastro_id = self.dotastro_id
		
		if self.use_xml:
			if dotastro_id is None or not isinstance(dotastro_id,int):
				return (None,None,None,None)
		
		print "preppin the infile"
		photname, hjd = self._make_intable(dotastro_id=dotastro_id)
		if photname is None:
			return (None,None,None,None)
		
		alt = "" if not try_alt else ".alt" + str(altnum)
		template_file = "Templates/" +  "eb." + str(fittype) + alt + ".template"
		print "using template", template_file
		if not os.path.exists(template_file):
			print "no template file for that type"
			return (None,None,None,None)
		
		# #import pdb; pdb.set_trace()
		# #print
		a = open(template_file,"r").readlines()
		tmp = self.rez_dir + "dotastro" + str(dotastro_id)
		if fittype == 4:
			b = "".join(a) % (self.period,hjd,sigma,'"' + photname + '"','"' + tmp + '.par"',\
			'"' + tmp + '.out"', '"' + tmp + '.fit"')
		elif fittype == 3:
			b = "".join(a) % (self.period,hjd,'"' + photname + '"','"' + tmp + '.par"',\
			'"' + tmp + '.out"', '"' + tmp + '.fit"')
		elif fittype == 5:
			b = "".join(a) % (self.period,hjd,ntries,'"' + photname + '"','"' + tmp + '.par"',\
				'"' + tmp + '.out"', '"' + tmp + '.fit"')
		elif fittype == 6:
			b = "".join(a) % (self.period,hjd,'"' + photname + '"','"' + tmp + '.par"',\
				'"' + tmp + '.out"', '"' + tmp + '.fit"')
		else:
			return (None,None,None,None)
			
		inname = "dotastro" +   str(dotastro_id) + ".in"
		f = open(inname,"w")
		f.writelines(b)
		f.close()
		print "wrote %s" % (inname)
		return (inname, tmp + ".out", tmp + ".par", tmp + ".fit")
		

	def _make_intable(self,dotastro_id=None,verbose=True,percentile=0.95):
		if dotastro_id is None:
			dotastro_id = self.dotastro_id
		if self.use_xml:
			if dotastro_id is None or not isinstance(dotastro_id,int):
				return None, None
			self._get_xml(dotastro_id,verbose=verbose)
		
		self._get_timeseries()
		
		if not os.path.isdir(self.phot_dir):
			os.mkdir(self.phot_dir)
		
		self.photname = self.phot_dir + "dotastro" + str(dotastro_id) + ".dat"
		f=open(self.photname,"w")
		merr = numpy.array( self.ts[self.photkey]['m_err'])
		
		merr[numpy.where(merr == 0.0)] += 0.005
		
		self.ts[self.photkey]['m_err'] = list(merr)
		
		try:
			rez = zip(self.ts[self.photkey]['t'],self.ts[self.photkey]['m'],self.ts[self.photkey]['m_err'])
		except:
			print "problem with the timeseries of that source. Bailing"
			return (None, None)
			
		tmp = [f.write("%f %f %f\n" % (x[0], x[1], x[2])) for x in rez]
		f.close()
		
		rez = sorted(rez,key=lambda x: x[1])  ## sort by magnitude
		
		# return the time near the minimum flux
		return (self.photname, rez[int(percentile*len(rez))][0])
		
			
	def _get_timeseries(self):
		if self.use_xml:
			if not self.gotxml or self.outname is None:
				print "dont have the xml to build the timeseries"
				return
			try:
				self.b = db_importer.Source(xml_handle=self.outname)
			except:
				print "timeseries import failed. Check your XML file. Maybe rm %s" % self.outname
				return
				
			kk = self.b.ts.keys()
			ind = 0
			if len(kk) > 1:
				print "note: lots of phototometry keys to choose from...using the first FIXME"
				ind = -1
				for i,k in enumerate(kk):
					if k[0].lower() == 'r':
						ind = i
						break
				if ind == -1:
					ind = 0
				
			self.photkey = kk[ind]
                        print "phot key = ", kk[ind] ## FIXME...maybe want to choose V band first
			self.ts = self.b.ts
		else:
			if self.rec_array is None:
				print "must give me a recarray!"
				return
			self.photkey = "V"
			self.ts = {self.photkey: self.rec_array}
			
	def _get_xml(self,dotastro_id=None,verbose=True):
		if dotastro_id is None:
			dotastro_id = self.dotastro_id
		if dotastro_id is None or not isinstance(dotastro_id,int):
			self.gotxml = False
			print "no dotastro"
			return
		
		if not os.path.isdir(self.xml_dir):
			os.mkdir(self.xml_dir)
		self.outname = self.xml_dir + "dotastro" + str(dotastro_id) + ".xml"
		if not os.path.exists(self.outname):
			print self.dotastro_url + str(dotastro_id)
			urllib.urlretrieve(self.dotastro_url + str(dotastro_id), self.outname)
			
			#f = open(self.outname,"w")
			#r = urllib2.urlopen(self.dotastro_url + str(dotastro_id))
			#f.writelines(r.readlines())
			#f.close()
		else:
			if verbose:
				print "already have file %s locally." % (self.outname)
		self.gotxml = True


def period_select(idd=243641,per=2.20770441,use_xml=True,rec_array=None,plot=True,trials=[0.5,1,2],\
	try_alt=False,all_models=True,dosave=False,show=True, fittype=3):
	
	if try_alt and all_models:
		#alts  = [-1,0,1] # OLD
		#alts  = range(-1, 1 + 126)
		alts  = range(-1, 1 + 5)
	else:
		alts = [-1]
	tt    = []
	altuse = []
	result_keys = []
	results = {'chisq':[],
 		   'class':[],
 		   'dof':[],
 		   'e':[],
 		   'i':[],
 		   'i_err':[],
 		   'l1':[],
 		   'l1/l2':[],
 		   'l1/l2_err':[],
 		   'l2':[],
 		   'ob1':[],
 		   'ob2':[],
 		   'okfit':[],
 		   'omega_deg':[],
 		   'period':[],
 		   'primary_eclipse_phase':[],
 		   'q':[],
 		   'q_err':[],
 		   'r1':[],
 		   'r2':[],
 		   'r1overflow':[],
 		   'r2overflow':[],
 		   'reflect1':[],
 		   'reflect2':[],
 		   't0':[],
 		   't0_err':[],
 		   'valid':[],
		   }

		
	for i,t in enumerate(trials):
		for alt in alts:
			a = EB(idd,per*t,use_xml=use_xml,rec_array=rec_array)
			print "trying period = %f" % (per*t)
			#if alt < 0:
			#	a.run(fittype=3,try_alt=False,altnum=alt)
			#else:
			#	a.run(fittype=3,try_alt=True,altnum=alt)

			###164593: using fittype=4 returns the same detached class and only a slightly tighter chi2:
			if alt < 0:
				a.run(fittype=fittype,try_alt=False,altnum=alt)
			else:
				a.run(fittype=fittype,try_alt=True,altnum=alt)
			for result_k, result_list in results.iteritems():
				#result_list.append(a.outrez.get(result_k, 999999)) # 999999 is a KLUDGE
				result_list.append(a.outrez.get(result_k, numpy.nan)) # 999999 is a KLUDGE
				### doesnt work:
				#if a.outrez.has_key(result_k):
				#	result_list.append(a.outrez[result_k])
			tt.append(t)
			altuse.append(alt)
			#print '>>>', i, t, alt
		
	for k in results.keys():
		results[k] = numpy.array(results[k])

	trials = numpy.array(tt)
	altuse = numpy.array(altuse)
	
	#print ok, trials, chisq, altuse
	
	oks = numpy.where(results['okfit'] == True)[0]

	#print ok, trials, chisq, altuse

	ok_results = {}
	for k in results.keys():
		ok_results[k] = results[k][oks]
	
	
	if len(oks) == 0:
		print "warning...no EB models seem like ok fits"
		bestt = trials[numpy.where(chisq == min(chisq))]
		bestalt = altuse[numpy.where(chisq == min(chisq))]
		
		rez = {'okfit': False, 'best_period': bestt[0]*per, "best_chisq": min(chisq), "best_alt": bestalt[0]}
	else:
		trials = trials[oks]
		chisq = ok_results['chisq']
		altuse = altuse[oks]
		bestt = trials[numpy.where(chisq == min(chisq))]
		bestalt = altuse[numpy.where(chisq == min(chisq))]
		rez =  {'okfit': True, 'best_period': bestt[0]*per, "best_chisq": min(chisq), "best_alt": bestalt[0]}
	print rez

	from scipy.stats import scoreatpercentile

	results_for_class = {}
	for class_name in ['detached', 'semi-detached', 'contact']:
		results_for_class[class_name] = {}
	        for k in ok_results.keys():
		        results_for_class[class_name][k] = ok_results[k][numpy.where(ok_results['class'] == class_name)]
	results_class_perc = {}
	chosen_chisq_class_tups = []

	attribs_for_percentiles = ['chisq', 'i_err', 'q_err', 'l1/l2_err', 'l1/l2', 'q', 'r1', 'r2', 'reflect1', 'reflect2', 'primary_eclipse_phase', 'period', 'omega_deg', 'l1', 'l2', 'e']
	rez['nmodels'] = {}
	#npass_vs_attrib_percentile = {}
	vals_for_attribute = {}
	for cur_attrib in attribs_for_percentiles:
		rez['nmodels'][cur_attrib] = {}
		chisq_percentiles = {}
		#npass_vs_attrib_percentile[cur_attrib] = {}
		vals_for_attribute[cur_attrib] = []
		#for perc in [5, 10, 15, 20, 30, 40, 50, 60, 70, 80, 90]:
		#	npass_vs_attrib_percentile[cur_attrib][perc] = 0
		for class_name in results_for_class.keys():
			subarr = results_for_class[class_name][cur_attrib][numpy.where(results_for_class[class_name][cur_attrib] > -numpy.inf)] # excludes: None, Nan
			rez['nmodels'][cur_attrib][class_name] = len(subarr)
			vals_for_attribute[cur_attrib].extend(list(subarr))
			if len(results_for_class[class_name][cur_attrib]) <= 1:
				continue
			chisq_percentiles[class_name] = {}
			#subarr = results_for_class[class_name][cur_attrib][numpy.where(results_for_class[class_name][cur_attrib] > -numpy.inf)] # excludes: None, Nan
			if len(subarr) > 1:
				for perc in [5, 10, 15, 20, 30, 40, 50, 60, 70, 80, 90]:
					#subarr = results_for_class[class_name][cur_attrib][numpy.where(results_for_class[class_name][cur_attrib] > -numpy.inf)] # excludes: None, Nan
					#if len(subarr) <= 1:
					#	continue
					n_at_percentile = len(subarr[numpy.where(subarr <= scoreatpercentile(subarr, perc))])
					chisq_percentiles[class_name][perc] = {'val_at_perc':scoreatpercentile(subarr, perc),
									       'n_pass':n_at_percentile/float(len(subarr))}
					#npass_vs_attrib_percentile[cur_attrib][perc] += n_at_percentile
			if cur_attrib == 'chisq':
				### KLUGEY
				results_class_perc[class_name] = {}
				chisq_percentile_cut = scoreatpercentile(results_for_class[class_name]['chisq'], 10)
		        	for k in results_for_class[class_name].keys():
				        results_class_perc[class_name][k] = results_for_class[class_name][k][numpy.where(results_for_class[class_name]['chisq'] <= chisq_percentile_cut)]
				#import pdb; pdb.set_trace()
				#print
			
				source_chisq_at_cut = max(results_for_class[class_name]['chisq'][numpy.where(results_for_class[class_name]['chisq'] <= chisq_percentile_cut)])
				chosen_chisq_class_tups.append((chisq_percentile_cut,
								class_name,
								trials[numpy.where(chisq == source_chisq_at_cut)],
								altuse[numpy.where(chisq == source_chisq_at_cut)],
								len(results_class_perc[class_name]['chisq'])))

		#import copy
		percentiles_name = "%s_percentiles" % (cur_attrib)
		rez[percentiles_name] = chisq_percentiles# copy.deepcopy(chisq_percentiles) # does this help??? (no: the bug was elsewhere)
	#import pdb; pdb.set_trace()
	#print
	rez['ratiopass_for_percentile'] = {}
	rez['vals_for_percentile'] = {}
	for cur_attrib in attribs_for_percentiles:
		total_models_for_attrib = sum(rez['nmodels'][cur_attrib].values())
		rez['ratiopass_for_percentile'][cur_attrib] = {}
		rez['vals_for_percentile'][cur_attrib] = {}
		for perc in [5, 10, 15, 20, 30, 40, 50, 60, 70, 80, 90]:
			#rez['ratiopass_for_percentile'][cur_attrib][perc] = npass_vs_attrib_percentile[cur_attrib][perc] / float(total_models_for_attrib)
			val_array = numpy.array(vals_for_attribute[cur_attrib])
			rez['vals_for_percentile'][cur_attrib][perc] = scoreatpercentile(val_array, perc)
			n_at_percentile = len(val_array[numpy.where(val_array <= rez['vals_for_percentile'][cur_attrib][perc])])
			rez['ratiopass_for_percentile'][cur_attrib][perc] = n_at_percentile / float(total_models_for_attrib)
	#import pprint
	#import pdb; pdb.set_trace()
	#print

	### NOTE: could probably stick this above so not all attributes are iterated over.
	if len(chosen_chisq_class_tups) == 0:
		return {}, {} #{}, {'valid': False, 'okfit': False, 'fittype':fittype,'chisq':None, "parameter_file": "", "outfile": ""}

	chosen_chisq_class_tups.sort()
	#print "### Sorted chi2 5% percentiles (chisq, class, bestt, bestalt, N_cut): "
	#import pprint
	#pprint.pprint(chosen_chisq_class_tups)
	#for tup in chosen_chisq_class_tups:
	#	print tup[0], tup[1], results_class_perc[tup[1]]['chisq']
	#import pdb; pdb.set_trace()
	#print   
	
	(best_chisq, best_class, bestt, bestalt, n_cut) = chosen_chisq_class_tups[0]

	#	results_detach_perc[k] = ok_results[k][numpy.where(numpy.logical_and( \
	#		                                               (ok_results['class'] == 'semi-detached'),
     	#		                                               (ok_results['chisq'] < 1.0)))]

	
	a = EB(idd,per*bestt[0],use_xml=use_xml,rec_array=rec_array)
	a.run(fittype=fittype, try_alt=(bestalt[0] >= 0), altnum=bestalt[0])
	#import pdb; pdb.set_trace()
	#print   
	if plot:
		print dosave,show
		a.plot(dosave=dosave,show=show)
	
	return rez, a.outrez


# OBSOLETE:
def period_select__old(idd=243641,per=2.20770441,use_xml=True,rec_array=None,plot=True,trials=[0.5,1,2],\
	try_alt=False,all_models=True,dosave=False,show=True, fittype=3):
	
	chisq = []
	ok    = []
	if try_alt and all_models:
		#alts  = [-1,0,1] # OLD
		alts  = range(-1, 1 + 126)
	else:
		alts = [-1]
	tt    = []
	altuse = []
	classif = []
	for i,t in enumerate(trials):
		for alt in alts:
			a = EB(idd,per*t,use_xml=use_xml,rec_array=rec_array)
			print "trying period = %f" % (per*t)
			#if alt < 0:
			#	a.run(fittype=3,try_alt=False,altnum=alt)
			#else:
			#	a.run(fittype=3,try_alt=True,altnum=alt)

			###164593: using fittype=4 returns the same detached class and only a slightly tighter chi2:
			if alt < 0:
				a.run(fittype=fittype,try_alt=False,altnum=alt)
			else:
				a.run(fittype=fittype,try_alt=True,altnum=alt)
			chisq.append(a.outrez['chisq'])
			ok.append(a.outrez['okfit'])
			tt.append(t)
			altuse.append(alt)
			classif.append(a.outrez['class'])
			print '>>>', i, t, alt
			#import pdb; pdb.set_trace()
			#print   
		
	ok = numpy.array(ok)
	trials = numpy.array(tt)
	chisq = numpy.array(chisq)
	altuse = numpy.array(altuse)
	classif = numpy.array(classif)
	
	#import pdb; pdb.set_trace()
	#print   
	#print ok, trials, chisq, altuse
	
	oks = numpy.where(ok == True)[0]

	#print ok, trials, chisq, altuse
	
	if len(oks) == 0:
		print "warning...no EB models seem like ok fits"
		bestt = trials[numpy.where(chisq == min(chisq))]
		bestalt = altuse[numpy.where(chisq == min(chisq))]
		
		rez = {'okfit': False, 'best_period': bestt[0]*per, "best_chisq": min(chisq), "best_alt": bestalt[0]}
	else:
		trials = trials[oks]
		chisq = chisq[oks]
		altuse = altuse[oks]
		classif = classif[oks]
		bestt = trials[numpy.where(chisq == min(chisq))]
		bestalt = altuse[numpy.where(chisq == min(chisq))]
		rez =  {'okfit': True, 'best_period': bestt[0]*per, "best_chisq": min(chisq), "best_alt": bestalt[0]}
	
	print rez
	a = EB(idd,per*bestt[0],use_xml=use_xml,rec_array=rec_array)
	a.run(fittype=fittype, try_alt=(bestalt[0] >= 0), altnum=bestalt[0])
	#import pdb; pdb.set_trace()
	#print   
	if plot:
		print dosave,show
		a.plot(dosave=dosave,show=show)
	
	return rez, a.outrez

	
def test(idd=243641,per=2.20770441,plot=True,try_alt=False,altnum=1,dosave=False,show=True):
	#e = EB(dotastro_id=217688,period=2.76901598)
	#e = EB(216887,4.39149364)  ## interesting asmmyetry
	#e = EB(216470,2.97443659)  ## cannot be fit easily
	e = EB(idd,per)
	e.run(try_alt=try_alt,altnum=altnum)
	if plot:
		e.plot(dosave=dosave,show=show)
	
if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(description='Fit eclipsing binary model to dotastro sources')
	parser.add_argument('did', metavar='dotastro_id', type=int, nargs=1,
	                   help='dotastro id (e.g. 233474)')
	parser.add_argument('per', metavar='period', type=float, nargs=1,
					           help='period of that source in days (e.g. 1.51608476)')
	parser.add_argument('-p', dest='plot', action='store_true',
	                   default=False,
	                   help='plot')
	parser.add_argument('-a', dest='alt', action='store_true',
					                   default=False,
					                   help='Try alternative template (closer starting point)')
	parser.add_argument('-s', dest='select', action='store_true',
					            default=False,
					             help='Do period selection')

	parser.add_argument('--altnum',dest='altnum',type=int,default=1,
							 help='altnative starting point number 0 or 1')

	parser.add_argument("-f",dest='savefig',action='store_true',default=False,help="save the figure")
	parser.add_argument("-x",dest='showfig',action='store_false',default=True,help="dont show the figure. No X11 screen.")
	
	args = parser.parse_args()
	if not args.showfig:
		matplotlib.use('Agg')

	if args.select:
		out = period_select(args.did[0],args.per[0],plot=args.plot,use_xml=True,try_alt=args.alt,dosave=args.savefig,show=args.showfig, fittype=4)
		import pprint
		pprint.pprint(out)
	else:
		test(args.did[0],args.per[0],args.plot,try_alt=args.alt,altnum=args.altnum,dosave=args.savefig,show=args.showfig)

	
	# test(230476,2.34910859)
	# test(243473,2.21889119)
	# test(225492,1.18067021)
	# test(255056,1.16160775)
	# test(233474,1.51608476)
	# test(261052,1.11247858)
	# test(216493,1.1935771)

	#test(225332,8.99898396)
	#test(216887,8.78298728)
