"""
sdss -- query tools
182.520649 
+18.534407
"""

import os, sys, string,urllib,copy
from math import log10, radians, pi
import time, traceback, datetime
import threading
import StringIO

global limit_per_min, recent_query_list, do_limit
limit_per_min = 19.99
recent_query_list = []
do_limit = True

dr7_mirrors = [{'url': "http://cas.sdss.org/astrodr7/en/tools/search/x_sql.asp", "second_per_query": 1.02,
						"active": True, "last": None, "running": False},
				{'url': "http://skyserver.sdss.org/astro/en/tools/search/x_sql.asp", "second_per_query": 1.02, "active": True, "last": None,
						 "running": False},
			   {'url': "http://www.sdss.org.uk/dr7/en/tools/search/x_sql.asp", "second_per_query": 1.02, "active": True, "last": None,
			            "running": False}]

class sdssq:
	#dr_url='http://skyserver.sdss.org/dr6/en/tools/search/x_sql.asp'
	dr_url="http://cas.sdss.org/astrodr7/en/tools/search/x_sql.asp"
	formats = ['csv','xml','html']
	def_fmt = "csv"
	all_completed = False
	completed  = False
	z_completed = False
	completed_master = False
	threads = []
	z_results = None
	results   = None
	results_master = None
	feature = None
	in_footprint = False

	def _get_dr_url(self,old=False,max_wait=10.0):
		## get the next available dr7 mirror
		if old:
			return self.dr_url
		
		## loop over the dr7 mirrors
		now = time.time()
		while time.time() - now < max_wait:
			for dr7 in dr7_mirrors:
				if not dr7['active'] or dr7['running'] == True:
					continue
				if dr7['last'] is None:
					## we haven't used this guy yet!
					dr7['last'] = time.time()
					dr7['running'] =True
					return dr7['url']
				if time.time() - dr7['last'] > dr7['second_per_query']:
					dr7['last'] = time.time()
					dr7['running'] =True
					return dr7['url']
			time.sleep(0.01)
		
		return None
				
			
	def __init__(self,pos=(None,None),threaded=True,verbose=False,block=True,maxd=1,timeout=10.0, \
		run_on_instance=False,run_feature_maker=True,runfoot=False):
		
		"""maxd in arcmin"""
		self.runfoot = runfoot
		self.threaded = threaded
		self.verbose  = verbose
		self.pos   = pos
		self.maxd = maxd
		self.timeout = timeout
		self.block =block

		self.run_on_instance = run_on_instance
		self.run_feature_maker = run_feature_maker
		self.threaded = threaded
		self.do_runs()
		return
                t = threading.Thread(target=self.do_runs, args=[])
                t.start()
		t.join(120.0) # wait 120 seconds before giving up on SDSS queries (I've seen some take ~50 seconds)
		if t.isAlive():
			print "! Thread has not returned!"

	def do_runs(self):
		""" This is to be threaded so that a timeout in thread .join() can be used.
		"""
		if self.runfoot:
			ss = self.run_footprint_check()
			if self.verbose:
				print "Position in footprint: %s" % repr(ss)
			
		if self.run_on_instance:
			if not self.threaded:
				self.run_all()
			else:
				self.run_all_threaded()
			if self.verbose:
				print self.__str__()
		
		if self.run_feature_maker:
			self.feature_maker()

			
	def run_all(self):
		self._get_z_objs()
		self._get_objs(force_galaxy=True,include_photo_z=True)
		self._get_objs(force_galaxy=False,include_photo_z=False)
		if self.completed and self.z_completed and self.completed_master:
			self.all_completed = True

	def run_footprint_check(self,old=False):
		sss = """SELECT count(*) as total from dbo.fFootprintEq(%f,%f,%f)""" % (self.pos[0],self.pos[1],0.2)
		if old:
			fff = self._query(sss)
		else:
			fff = self._new_query(sss)
		
		line = fff.readline()
		if line.startswith("ERROR") or line.find("HTTP Error 404") != -1:
			if self.verbose:
				print line
				print fff.readlines()
			return False
		## get the keys
		#kkk = line.split(",")
		## now go line by line
		line = fff.readline()
		vvv = line.strip().split(",")
		if vvv[0] == "0" or vvv[0].find("The page cannot be found") != -1:
			self.in_footprint = False
		else:
			self.in_footprint = True
		return self.in_footprint
		
	def run_all_threaded(self):
		
		import threading
		self.threads.append(threading.Thread(target=self._get_objs,name="master",kwargs={'force_galaxy': False,'include_photo_z': False}))
		self.threads[-1].start()
		self.threads.append(threading.Thread(target=self._get_objs,name="near",kwargs={'force_galaxy': True,'include_photo_z': True}))
		self.threads[-1].start()
		self.threads.append(threading.Thread(target=self._get_z_objs,name="z"))
		self.threads[-1].start()

		if self.block:
			for t in self.threads:
				#print "joining %s" % repr(t) 
				t.join(self.timeout)
				
		if self.completed and self.z_completed and self.completed_master:
			self.all_completed = True
					
	def feature_maker(self,force=False,old=False,verbose=False):
		"""http://www.sdss.org/dr6/algorithms/redshift_type.html#eclass"""
		if not self.in_footprint:
			self.feature = {"in_footprint": False}
			if not force:
				return
		else:
			self.feature = {"in_footprint": True}

		sss = """SELECT TOP 3 p.objid, case
			  WHEN S.bestObjID is NOT NULL then dbo.fSpecClassN(S.specClass)
			  WHEN p.probPSF = 0 THEN "galaxy"
			  WHEN p.probPSF = 1 THEN "star"
			  ELSE "unknown"
			end as type, p.ra, p.dec,p.dered_u, p.dered_g, p.dered_r, p.dered_i, p.dered_z, p.err_u, p.err_g, p.err_r, p.err_i, p.err_z, 
			             n.distance as dist_in_arcmin, R.spz as chicago_z, R.eclass as chicago_class, R.spz_status as chicago_status,
			             T.z as photo_z, T.zerr as photo_zerr, T.pzType as photo_z_pztype,
			             T.rest_ug as photo_rest_ug,T.rest_gr as photo_rest_gr,T.rest_ri as photo_rest_ri,
			             T.rest_iz as photo_rest_iz,T.absMag_g as photo_rest_abs_g,T.absMag_u as photo_rest_abs_u,
			             T.absMag_r as photo_rest_abs_r,T.absMag_i as photo_rest_abs_i,T.absMag_z as photo_rest_abs_z,
			             Q.photozcc2 as photo2_z_cc,Q.photozerrcc2 as photo2_zerr_cc,Q.photozd1 as photo2_z_d1,
			             Q.photozerrd1 as photo2_zerr_d1,Q.flag as photo2_flag,S.z as spec_z, S.velDisp as spec_veldisp, dbo.fSpecZWarningN(S.zWarning) as spec_zWarning,
			             dbo.fSpecZStatusN(S.zStatus) as spec_zStatus, S.zConf as spec_confidence, S.zErr as spec_zerr, case
			  WHEN S.bestObjID is NOT NULL AND S.zConf > 0.5 THEN S.z
			  WHEN Q.objID     IS NOT NULL AND p.r > 20 then Q.photozcc2
			  WHEN Q.objID     IS NOT NULL AND p.r < 20 then Q.photozd1
			  WHEN T.objID     is NOT NULL AND T.z != -9999 THEN T.z
			  ELSE NULL
			end as bestz, case
				WHEN S.bestObjID is NOT NULL AND S.zConf > 0.5 THEN S.zErr
				WHEN Q.objID     IS NOT NULL AND p.r > 20 then Q.photozerrcc2
				WHEN Q.objID     IS NOT NULL AND p.r < 20 then Q.photozerrd1
				WHEN T.objID     is NOT NULL AND T.z != -9999 THEN T.zerr
				ELSE NULL
			end as bestz_err,
			dbo.fCosmoDl(case
			  WHEN S.bestObjID is NOT NULL AND S.zConf > 0.5 AND S.z < 0.0001 THEN 0.00001
			  WHEN S.bestObjID is NOT NULL AND S.zConf > 0.5 AND S.z > 0.0001 THEN S.z
			  WHEN Q.objID     IS NOT NULL AND p.r > 20 then Q.photozcc2
			  WHEN Q.objID     IS NOT NULL AND p.r < 20 then Q.photozd1
			  WHEN T.objID     is NOT NULL AND T.z != -9999 THEN T.z
			  ELSE 1500
			end) as best_dl,case
			    WHEN p.petroRad_g > 0.0 THEN p.petroRad_g
			    ELSE NULL
			end as petroRad_g, case
				WHEN p.petroRad_g > 0.0 THEN p.petroRadErr_g
				ELSE NULL
			end as petroRadErr_g, case
				    WHEN p.petroRad_g > 0.0 THEN n.distance * 60.0 / p.petroRad_g
				    ELSE NULL
			end as best_offset_in_petro_g, f.delta as first_offset_in_arcsec, f.integr as first_flux_in_mJy,
			X.delta as rosat_offset_in_arcsec, X.hard1 as rosat_hardness_1,X.hard2 as rosat_hardness_2, X.cps as rosat_cps, X.posErr as rosat_poserr, case 
			    WHEN X.objID is NOT NULL THEN X.delta /  X.posErr
			end as rosat_offset_in_sigma, X.cps * 6.9 as rosat_flux_in_microJy, R.seguetargetclass as classtype, 
			R.sptypea as spectral_stellar_type, R.hammersptype as spectral_hammer_type, R.flag as spectral_flag, R.zbclass as segue_class, R.zbsubclass as segue_star_type
			FROM PhotoPrimary p
			 JOIN dbo.fGetNearbyObjEq(%f,%f,%f) as n ON p.objID = n.objID
			 LEFT JOIN photoz as T ON p.objID=T.objID
			 LEFT JOIN photoz2 as Q ON p.objID=Q.objID
			 LEFT JOIN SpecObjAll as S ON p.objId=S.bestObjId
			 LEFT JOIN sppParams as R ON S.specObjID=R.specObjID
			 LEFT JOIN First as f ON p.objID=f.objID
			 LEFT JOIN Rosat as X on p.objID=X.objID
			ORDER by n.distance
		""" % (self.pos[0],self.pos[1],self.maxd)
		## as per Dovi's suggestion, get the nearest guy, no questions asked.
		#print sss
		#""""""
		if old:
			fff = self._query(sss)
		else:
			fff = self._new_query(sss,verbose=verbose)

		line = fff.readline()
		if line.startswith("ERROR") or line.startswith("No objects"):
			if self.verbose:
				print line
				print fff.readlines()
			return self.feature
		## get the keys
		kkk = line.split(",")
		## now go line by line
		line = fff.readline()
		rez = []
		try:
			if not self.in_footprint:
				self.in_footprint = True
				self.feature = {"in_footprint": True}
			while line:
				tmp = {}
				vvv = line.strip().split(",")
				for k,v in dict(zip(kkk,vvv)).iteritems():
					#print "***" + k + "****" + str(v) + "****"
					if v == "0" or v == "null":
						v = None
					if k.strip() in ['objid',"photo2_flag"]:
						if v != None:
							v1 = long(v)
						else:
							v1 = None
					elif k.strip() in ['type','spec_zStatus','spec_zWarning',"spectral_flag","spectral_hammer_type",\
							   "spectral_stellar_type","spectral_flag","classtype","segue_class","segue_star_type"]:
						v1 = v
						if v1 != None:
							v1 = v1.lower()
						if v1 == 'null':
							v1 = None
					else:
						if v != None:
							if v != "-9999":
								try:
								   v1 = float(v)
								except:
								   print traceback.print_exc()
								   if v.startswith("ERR"):
									   time.sleep(60.0)
								   v1 = None
							else:
								v1 = None
							#v1 = float(v) if v != "-9999" else None
						else:
							v1 = None
					tmp.update({k.strip(): v1})
				tmp.update({"url": "http://cas.sdss.org/astrodr7/en/tools/explore/obj.asp?id=%i" % tmp['objid']})
				tmp.update({"urlalt": "http://cas.sdss.org/astrodr7/en/tools/chart/chart.asp?ra=%f&dec=%f" % (tmp['ra'],tmp['dec'])})
				if tmp.has_key('best_dl'):
					if tmp['best_dl'] > 1e6:
						## kludge here
						tmp.update({"best_dl": None})
					if tmp['best_dl'] != None:
						tmp.update({"best_dm": 5.0*log10(tmp['best_dl']*1e5)}) 
						if tmp.has_key('bestz') and tmp.has_key('dist_in_arcmin'):
							angdist =tmp['best_dl']/(1.0 + tmp['bestz'])**2
							tmp.update({"best_offset_in_kpc": 1e3*angdist*radians(tmp['dist_in_arcmin']/60.0)})
				if tmp.has_key("rosat_flux_in_microJy") and tmp.has_key("best_dl") and tmp.has_key("best_z"):
					if tmp["rosat_flux_in_microJy"] > 0.0 and tmp["best_dl"] and tmp["best_z"]:
						l = ((3.085e24)**2)*4.0*pi*tmp["best_dl"]*tmp["best_dl"]*(1.0 + tmp["best_z"])*1e-29
						tmp.update({"rosat_log_xray_luminosity": log10(l)})
				else:
					tmp.update({"rosat_log_xray_luminosity": None})
				rez.append(copy.copy(tmp))
				line = fff.readline()
		except:
			print traceback.format_exc()
			print line
		# 20090211: dstarr adds try/except:
		try:
			if len(rez) == 0:
				self.feature.update(copy.copy(rez[0]))
			elif len(rez) > 1:
				## make sure there isn't a more nearby galaxy
				if rez[0]['type'] != 'galaxy' and rez[0]['best_offset_in_petro_g'] > 2.0:
					## we're sort of far from the closest star. Just check to make sure there isn't a galaxy closer in petro
					usei = 0
					bestp = 100.0
					for i,r in enumerate(rez[1:]):
						if r['type'] == 'galaxy' and  r['best_offset_in_petro_g']  < bestp:
							bestp =  r['best_offset_in_petro_g']
							usei = i+1
					if bestp < 3.0:
						self.feature.update(copy.copy(rez[usei]))
						self.feature.update({"note": "nearer star not used. Instead nearby galaxy"})
						
					else:
						self.feature.update(copy.copy(rez[0]))
				else:
					self.feature.update(copy.copy(rez[0]))
		except:
			print "EXCEPT: sdss.py...self.feature.update(rez[0])"
			return self.feature
		return

	def nearest(self):
		ret = None
		if self.completed and self.results:
			if len(self.results) > 0:
				ret = copy.copy(self.results[0])
		return ret

	def nearest_all(self):
		ret = None
		if self.completed_master and self.results_master:
			if len(self.results_master) > 0:
				ret = copy.copy(self.results_master[0])
		return ret
			
	def nearest_with_z(self):
		ret = None
		if self.z_completed and self.z_results:
			if len(self.z_results) > 0:
				ret = copy.copy(self.z_results[0])
		return ret
		
	def __str__(self):
		printone = False
		a = ""
		if self.z_completed:
			a += "*** redshift search results within %6.1f arcmin of pos = %s *** \n" % (self.maxd, self.pos)
			if self.z_results:
				kkk = self.z_results[0].keys()
				a += "   ".join(kkk) + "\n"
				if printone:
					nn = 1
				else:
					nn = len(self.z_results[0])
				for i in range(nn):
					a += "   ".join([str(x) for x in self.z_results[i].values()]) + "\n"
			else:
				a += " nothing found \n"
		else:
			a += "*** [redshift search not completed] \n"

		if self.completed:
			a += "*** galaxy search results within %6.1f arcmin of pos = %s *** \n" % (self.maxd, self.pos)
			if self.results:
				kkk = self.results[0].keys()
				a += "   ".join(kkk) + "\n"
				if printone:
					nn = 1
				else:
					nn=  len(self.results[0])
				for i in range(nn):
					a += "   ".join([str(x) for x in self.results[i].values()]) + "\n"
			else:
				a += " nothing found \n"
		else:
			a += "*** [galaxy search not completed] \n"

		if self.completed_master:
			a += "*** galaxy/star search results within %6.1f arcmin of pos = %s *** \n" % (self.maxd, self.pos)
			if self.results_master:
				kkk = self.results_master[0].keys()
				a += "   ".join(kkk) + "\n"
				if printone:
					nn = 1
				else:
					nn = len(self.results_master[0])
				for i in range(nn):
					a += "   ".join([str(x) for x in self.results_master[i].values()]) + "\n"
			else:
				a += " nothing found \n"
		else:
			a += "*** [galaxy search not completed] \n"
		
		return a
			
	def _get_z_objs(self,force_galaxy=True,old=False):
		if force_galaxy:
			the_table = "Galaxy"
		else:
			the_table =  "PhotoPrimary"
		sss = """SELECT p.objid, p.ra, p.dec,p.dered_u, p.dered_g, p.dered_r,  p.dered_i, p.dered_z, n.distance, S.z, S.velDisp, dbo.fSpecZStatusN(S.zStatus) as zStatus, S.zConf
			FROM %s  p
			     JOIN SpecObjAll as S ON p.objId=S.bestObjId
			     JOIN dbo.fGetNearbyObjEq(%f, %f,%f) as n ON p.objID = n.objID
			WHERE
			     S.zStatus != dbo.fSpecZStatus('FAILED')
			ORDER BY n.distance""" % (the_table,self.pos[0],self.pos[1],self.maxd)
		
		if old:
				fff = self._query(sss)
		else:
				fff = self._new_query(sss)
		line = fff.readline()
		if line.startswith("ERROR") or line.startswith("No objects"):
			self.z_completed = True
			if self.verbose:
				print line
				print fff.readlines()
			return
		## get the keys
		kkk = line.split(",")
		## now go line by line
		line = fff.readline()
		rez = []
		while line:
			tmp = {}
			vvv = line.strip().split(",")
			for k,v in dict(zip(kkk,vvv)).iteritems():
				if k == 'objid':
					v1 = long(v)
				elif k == 'zStatus':
					v1 = v
				else:
					if v != "-9999":
						v1 = float(v)
					else:
						v1 = None

				tmp.update({k.strip(): v1})
			rez.append(copy.copy(tmp))
			line = fff.readline()
		self.z_results = copy.copy(rez[0])
		self.z_completed = True
		return
		
	def _get_objs(self,force_galaxy=True,include_photo_z=True,old=False):
		if force_galaxy:
			the_table = "Galaxy"
		else:
			the_table =  "PhotoPrimary"

		if include_photo_z:
			extra_col = ",T.z, T.zerr,T.dmod,T.rest_ug,T.rest_gr,T.rest_ri,T.rest_iz,T.absMag_g"
			extra_join = "JOIN photoz as T ON p.objID=T.objID " 
		else:
			extra_col = " "
			extra_join = " "

		if include_photo_z or force_galaxy:
			complete_flag = "self.completed"
			results       = "self.results"
		else:
			complete_flag = "self.completed_master"
			results = "self.results_master"

		
		sss = """SELECT p.objid, p.ra, p.dec,p.dered_u, p.dered_g, p.dered_r,  p.dered_i, p.dered_z, n.distance %s
			FROM %s  p
			     JOIN dbo.fGetNearbyObjEq(%f, %f,%f) as n ON p.objID = n.objID
			     %s
			ORDER BY n.distance""" % (extra_col,the_table,self.pos[0],self.pos[1],self.maxd,extra_join)
		
		#print sss, complete_flag, results
		if old:
			fff = self._query(sss)
		else:
			fff = self._new_query(sss)

		#print fff.readlines()
		line = fff.readline()
		#if line.startswith("ERROR") or line.startswith("No objects"):
		# dstarr 20090127 adds len() condition:
		if line.startswith("ERROR") or \
		          line.startswith("No objects") or \
			  (len(line) == 0):
			exec(complete_flag + " = True")
			if self.verbose:
				print line
				print fff.readlines()
			return
		## get the keys
		kkk = line.split(",")
		## now go line by line
		line = fff.readline()
		rez = []
		while line:
			tmp = {}
			vvv = line.strip().split(",")
			for k,v in dict(zip(kkk,vvv)).iteritems():
				if k == 'objid':
					v1 = long(v)
				elif k == 'zStatus':
					v1 = v
				else:
					v1 = float(v)
				tmp.update({k.strip(): v1})
			rez.append(copy.copy(tmp))
			line = fff.readline()
		exec(results + " = copy.copy(rez)")
		exec(complete_flag + " = True")
		#print complete_flag, self.completed, self.completed_master
		return
		
	def _filtercomment(self,sql):
		"Get rid of comments starting with --"
		fsql = ''
		for line in sql.split('\n'):
			fsql += line.split('--')[0] + ' ' + os.linesep;
		return fsql
	
	def _new_query(self,sql,fmt=def_fmt,wait_period=62,verbose=True):
		#print dr7_mirrors
		url = self._get_dr_url(old=False)
		if verbose:
			print url
		#print dr7_mirrors
		if url is None:
			return StringIO.StringIO() # This is an empty filehandler
			
		fsql = self._filtercomment(sql)
		params = urllib.urlencode({'cmd': fsql, 'format': fmt})
		try:
			ttt = urllib.urlopen(url+'?%s' % params)
			for d in dr7_mirrors:
				if d['url'] == url:
					d['running'] = False
					break
			#print dr7_mirrors
			return ttt
		except:
			print "TRIED: " + url+'?%s' % params
			print "EXCEPT: sdss.py._query()"
			for d in dr7_mirrors:
				if d['url'] == url:
					d['running'] = False
					d['active'] = False
					break
			return StringIO.StringIO() # This is an empty filehandler
		
		
	def _query(self,sql,url=dr_url,fmt=def_fmt,wait_period=62):
		"Run query and return file object"
		global limit_per_min, recent_query_list, do_limit
		if do_limit:
			recent_query_list.append((time.time(),sql))
			## cull out all the old calls
			recent_query_list = [x for x in recent_query_list if time.time() - x[0] < wait_period]
			if len(recent_query_list) > limit_per_min:
				## ug, we've got to wait
				tmp = [time.time() - x[0] for x in recent_query_list if time.time() - x[0] < wait_period]
				wait = wait_period - max(tmp) + 1
				if self.verbose:
					print "Date: %s Query length is %i in the last %f sec" % (str(datetime.datetime.now()),len(recent_query_list) - 1 , wait_period)  
					print "waiting %f sec, so as not to block the SDSS query %s" % (wait,sql)
				time.sleep(wait)
				
		fsql = self._filtercomment(sql)
		params = urllib.urlencode({'cmd': fsql, 'format': fmt})
		try:
			return urllib.urlopen(url+'?%s' % params) 
		except:
			print "TRIED: " + url+'?%s' % params
			print "EXCEPT: sdss.py._query()"
			return StringIO.StringIO() # This is an empty filehandler

def test(verbose=True):
	
	dr7_mirrors[0]["second_per_query"] = 10
	dr7_mirrors[1]["second_per_query"] = 7
	
	s = sdssq(pos=(36.522917   ,-0.540500),verbose=verbose)
	#s = sdssq(pos=(38.522917   ,1.540500),verbose=verbose)	
	#s = sdssq(pos=(40.522917   ,2.540500),verbose=verbose)
	#s = sdssq(pos=(42.522917   ,3.540500),verbose=verbose)
	#s = sdssq(pos=(170.76476675499998,-8.5050723541500002), verbose=verbose)
	
	#print s.nearest()
	#print s.nearest_with_z()
	s.feature_maker(force=True,verbose=True)
	import pprint
	pprint.pprint(s.feature)
	import webbrowser
	try:
		webbrowser.open_new_tab(s.feature["urlalt"])
	except:
		pass

if __name__ == "__main__":	
	test(verbose=False)
