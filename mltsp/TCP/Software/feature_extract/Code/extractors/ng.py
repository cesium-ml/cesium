#!/bin/env python
"""
ng -- gets the nearest galaxies

USAGE:
   ./ng.py [ra]
"""
import csv
import os
import sqlite3
import numpy, math
import geohash2
from math import sin, cos, radians, sqrt, atan2, degrees
import copy

__author__ = "Josh Bloom"
__version__ = "10 Nov 2008"

if os.environ.has_key("TCP_DIR"):
	DATADIR = os.environ.get("TCP_DIR") + "Data/"
else:
	DATADIR = ""
	
def_min_depth = 11

class GalGetter:
	
	dbname = "gal.db"
	rez = []
	query = ""
	index_type="index"
	
	def __init__(self,inname=DATADIR + "200MpcGalaxyCatalog_v2.dat",dbname=DATADIR + "gal_v2.db",max_rows=-1,make_db_on_instance=True,verbose=False):
		self.inname = inname
		self.dbname = dbname
		self.verbose = verbose

		if make_db_on_instance:
			self.make_db(max_rows=max_rows)
		
	# NOTE: 20090227: dstarr changes some default values so this works with normal feature extractor:
	#         	def make_db(self,in_memory=False,clobber=False,skip_headers=[''],\
	def make_db(self,in_memory=False,clobber=False,skip_headers=[''],\
		intnames=['pgc'],default_hash_depth=18,max_rows=-1):
	
		if not os.path.exists(self.inname):
			if self.verbose:
				print "inname = %s does not exist" % self.inname
			return None
		
		r = csv.reader(open(self.inname), delimiter="|")
	
		## figure out the headers
		tmp = numpy.array([s.strip() for s in r.next()])
		use_indices = []
		for i in range(len(tmp)):
			if not (tmp[i] in skip_headers):
				use_indices.append(i)
		tmp = list(tmp.take(use_indices))
		
		self.headers = copy.copy(tmp)
		self.headers.append('ghash')
		
		ra_ind = tmp.index('al2000')
		dec_ind = tmp.index('de2000')
		d_ind   = tmp.index('logd25')

		if clobber:
			if not in_memory:
				if os.path.exists(self.dbname):
					os.remove(self.dbname)
		else:
			if os.path.exists(self.dbname):
				return self.dbname

		if in_memory:
			self.dbname = ":memory:"
			
		# Make the DB
		conn = sqlite3.connect(self.dbname)
		c = conn.cursor()
		tmp1 = []
		for s in tmp:
			if s in intnames:
				tmp1.append(s + " int")
			else:
				tmp1.append(s + " real")
	
		tmp1.append("ghash text")
		tmp1 = ",".join(tmp1)
		c.execute('''create table galaxies (%s)''' % tmp1)
		#c.execute('select * from galaxies')
		#print "*"
		#for r in c:
		#	print r
		#print "*"
		i=0
		min_depth = 35
		if self.index_type == "hash":
			g = geohash2.Geohash
		else:
			g = geohash2.Geoindex
		for l in r:
			if i > max_rows and max_rows > 1:
				break
			try:
				tmp = numpy.array([s.strip() for s in l])
				tmp = list(tmp.take(use_indices))
				tmp[ra_ind] = str(float(tmp[ra_ind])*15.0)
				hashpos = (float(tmp[ra_ind]),float(tmp[dec_ind]))
				if float(tmp[d_ind]) > 0:
					hashpos_depth = int(math.floor(18.25707 - \
								3.333333*math.log10(60.0*10**(float(tmp[d_ind])*0.1))))
				else:
					hashpos_depth = default_hash_depth
				if hashpos_depth < min_depth:
					min_depth = hashpos_depth
				#hashpos_depth = 18
				#print hashpos, hashpos_depth
				tmp.append("'%s'" % str(g(hashpos,depth=hashpos_depth)))
				tmp = ",".join(tmp)
				c.execute("""insert into galaxies values (%s)""" % tmp)
				i+=1
			except:
				if self.verbose:
					print "row %i" % i
				i+=1
				continue
		conn.commit()
		conn.close()
		if self.verbose:
			print "min_depth ", min_depth
		return self.dbname

	def getgi(self,pos=(None,None),error=1.0,min_depth=def_min_depth):
		mult = 3600.0
		depth =int(math.floor(18.25707 - 3.333333*math.log10(mult*error)))
		if depth > min_depth:
			depth = min_depth
		#depth=18
		return geohash2.Geoindex(pos,depth=depth)

	def getgh(self,pos=(None,None),error=1.0,min_depth=def_min_depth):
		mult = 3600.0
		depth =int(math.floor(18.25707 - 3.333333*math.log10(mult*error)))
		if depth > min_depth:
			depth = min_depth
		#depth=18
		return geohash2.Geohash(pos,depth=depth)

	def getgals(self,pos=(49.362750 ,  41.405417),radius=5,min_depth=def_min_depth,sort_by='dist',max_d=500.0):
		if self.index_type == "hash":
			g = self.getgh
		else:
			g = self.getgi
		## radius in degrees
		## max d in Mpc
		dm_max = 5.0*math.log10(max_d*1e5)
		gh= g(pos=pos,error=radius*3,min_depth=min_depth)
		#gh1 = self.getgh(pos=(pos[0],pos[1]+radius),error=radius,min_depth=min_depth)
		#gh2 = self.getgh(pos=(pos[0],pos[1]-radius),error=radius,min_depth=min_depth)
		#gh3 = self.getgh(pos=(pos[0]-radius*cos(radians(pos[1])),pos[1]),error=radius,min_depth=min_depth)
		#gh4 = self.getgh(pos=(pos[0]+radius*cos(radians(pos[1])),pos[1]),error=radius,min_depth=min_depth)		
		#print gh.bbox()
		#print gh.point()
		#print gh1.bbox(), (pos[0],pos[1]+radius), str(gh1)
		#print gh2.bbox(), (pos[0],pos[1]-radius), str(gh2)
		#print gh3.bbox(), (pos[0]-radius*cos(radians(pos[1])),pos[1]), str(gh3)
		#print gh4.bbox(), (pos[0]+radius*cos(radians(pos[1])),pos[1]), str(gh4)
		conn = sqlite3.connect(self.dbname)
		c = conn.cursor()
		self.query = 'pos = %s, radius = %f, sort_by=%s max_d=%f \nselect * from galaxies where galaxies.ghash glob %s and galaxies.mucin < %s' % \
		 	(repr(pos), radius, sort_by, max_d, str(gh)[:-2] + "*",dm_max)
		c.execute('select * from galaxies where galaxies.ghash glob ? and galaxies.mucin < ?', (str(gh)[:-2] + "*",dm_max))
		tmp = c.fetchall()
		d_ind   = self.headers.index('logd25')
		r_ind   = self.headers.index('logr25')
		pa_ind   = self.headers.index('pa')
		mucin   =  self.headers.index('mucin')
		muc     =  self.headers.index('mup')
		#semim = 60 * 10.**(r1[0][d_ind])*0.1
		#semimin = semim / 10**r1[0][r_ind]
		#pa = r1[0][pa_ind]

		tmp1 = []
		for r in tmp:
			 d = self.distance(pos[0],pos[1],r[1],r[2])
			 if d < radius:
				dl = self.distlight(pos[0],pos[1],r[1],r[2],60 * 10.**(r[d_ind])*0.1,60 * 10.**(r[d_ind])*0.1/(10**r[r_ind]),r[pa_ind])
				if r[muc] > 0:
					off = 1e3*radians(d)*1e-5*10**(r[muc]/5.0) 
				else:
					off = 1e3*radians(d)*1e-5*10**(r[mucin]/5.0)
				#print off, d, r[mucin]
				tmp1.append( (r,d,dl,off))

		tmp = tmp1
		#print len(tmp)
		if sort_by == 'dist':
			tmp.sort(key=lambda x: x[1])
		elif sort_by == 'dm':
			tmp.sort(key=lambda x: x[0][self.headers.index('mucin')])
		elif sort_by == 'mag':
			## get the distance modulus and the b-band mag corrected
			tmp.sort(key=lambda x: x[0][self.headers.index('btc')] - x[0][self.headers.index('mucin')])
		elif sort_by == 'light':
			## distance in light units
			tmp.sort(key=lambda x: x[2][0])
		elif sort_by == 'phys':
			tmp.sort(key=lambda x: x[3])
		self.rez = tmp
		conn.close()
	
	def grab_rez(self,retkey="light",prefix="closest_in_"):
		
		
		try:
			r1=self.rez[0]
			if retkey == 'light':
				val= r1[2][0]
				sb    = "light"
				units = "galaxy_surface_brightness"
				alt_dict = {prefix + sb + "_physical_offset_in_kpc": r1[3], prefix + sb + "_angular_offset_in_arcmin": r1[1]*60}
			elif retkey == 'phys':
				val= r1[3]
				sb = "physical_offset_in_kpc"
				units = "kpc"
				alt_dict = {prefix + sb + "_light": r1[2][0], prefix + sb + "_angular_offset_in_arcmin": r1[1]*60}
			elif retkey == "dist":
				val= r1[1]*60
				sb = "angular_offset_in_arcmin"
				units = "arcmin"
				alt_dict = {prefix + sb + "_light": r1[2][0], prefix + sb + "_physical_offset_in_kpc": r1[3]}
				
			else:
				return {}
			
			d_ind   = self.headers.index('logd25')
			r_ind   = self.headers.index('logr25')
			pa_ind   = self.headers.index('pa')
			mucin   =  self.headers.index('mucin')
			muc     =  self.headers.index('mup')
			t   =  self.headers.index('t')
			te     =  self.headers.index('e_t')
			b     =  self.headers.index('btc')
			ra = self.headers.index('al2000') 
			dec = self.headers.index('de2000')
			
			smj,sminor,pa = (60 * 10.**(r1[0][d_ind])*0.1, 60 * 10.**(r1[0][d_ind])*0.1/(10**r1[0][r_ind]), r1[0][pa_ind])
			dm = r1[0][muc] if r1[0][muc] > 0 else r1[0][mucin]
			
			if smj == 6.0e-99:
				smj = None
				sminor = None
				
			## look at the t-type
			ttype = r1[0][t] if r1[0][te] < 3 and r1[0][t] != -99.0 else None
			
			## look at the absolute mag of the closest galaxy
			absb  = r1[0][b] - dm if r1[0][b] > 5.0 else None
			
			## angle from major
			angle_major = r1[2][1] or None
			
			## position (for internal purposes if we want it)
			ra, dec = r1[0][ra], r1[0][dec]
			
		except:
			return {}
		
		alt_dict.update({prefix + sb: val, prefix + sb + "_units": units, prefix + sb + "_semimajor_r25_arcsec": smj, \
					prefix + sb + "_semiminor_r25_arcsec": sminor, prefix + sb + "_dm": dm, \
					prefix + sb + "_angle_from_major_axis": angle_major, prefix + sb + "_ttype": ttype, \
					prefix + sb + "_absolute_bmag": absb, prefix + sb + "_galaxy_position": (ra, dec)})
		return copy.copy(alt_dict)
			
	def __str__(self):
		a = "%s\n%s\n%s\n" % ("*"*50, self.query,"*"*50)
		a += "dist(') offset(kpc) dist(light) angle_from_major"
		for h in self.headers:
			a += "%9s" % h
		a += "\n"
		for r1 in self.rez:
			r = r1[0]
			#print r1[2]
			a += "%7.4f %7.4f %7.4f  %7.1f " % (r1[1]*60, r1[3], r1[2][0], r1[2][1] or -999)
			a += " ".join([str(x) for x in r]) + " \n"
			# a += "%f %f %f %f %s\n" % (r[1], r[2], r[7], r1[1], r[-1])
		return a
	
	def writeds9(self,fname='ds9.reg'):
		ra_ind = self.headers.index('al2000')
		dec_ind = self.headers.index('de2000')
		d_ind   = self.headers.index('logd25')
		r_ind   = self.headers.index('logr25')
		pa_ind   = self.headers.index('pa')
		pgc_ind   = self.headers.index('pgc')
		mucin   =  self.headers.index('mucin')
		muc     =  self.headers.index('mup')
		
		f = open(fname,'w')
		f.write("# Region file\n")
		f.write('global color=green font="helvetica 10 normal" select=1 highlite=1 edit=1 move=1 delete=1 include=1 fixed=0 source\nfk5\n')
		mind = 100
		maxd = 0
		for r1 in self.rez:
			if r1[0][muc] != -99:
				m = r1[0][muc]
			else:
				m = r1[0][mucin]
			if m < mind: mind = m
			if m > maxd: maxd = m

		# max sure that maxd and mind aren't the same
		if mind == maxd:
			mind /= 1.02
		for r1 in self.rez:
			d = r1[0]
			semim = 60 * 10.**(r1[0][d_ind])*0.1
			semimin = semim / 10**r1[0][r_ind]
			pa = r1[0][pa_ind]
			if r1[0][muc] != -99:
				m = r1[0][muc]
			else:
				m = r1[0][mucin]
			#print r1, m, mind, maxd
			cc = str(hex(int(255.0 - 255.0*(m - mind)/(maxd - mind)))).split("x")[1]
			if len(cc) == 1: cc = "0" + cc
			
			col = '"#' + cc*2 + '44"'
			width = int(5 - 4.0*(m - mind)/(maxd - mind))
			d= 1e-5*10**(m/5.0)
			f.write('ellipse(%f,%f,%f",%f",%f) # text={pgc=%i, d=%4.1f Mpc} color=%s  width=%i\n' % (r1[0][ra_ind],r1[0][dec_ind],\
				semim,semimin,pa - 90.0,r1[0][pgc_ind],d,col,width))
		f.close()
			
	def distance(self,lon0, lat0, lon, lat):
	    """
	    Calculates the distance between two points (decimal)
	    """
	    d_lat = radians(lat0 - lat)
	    d_lon = radians(lon0 - lon)
	    x = sin(d_lat/2) ** 2 + \
	       cos(radians(lat0)) * cos(radians(lat)) *\
	       sin(d_lon/2) ** 2
	    y = 2 * atan2(sqrt(x), sqrt(1.0 - x))
	    distance = y*180.0/math.pi
	    return distance
	
	def distlight(self,lon, lat, lon0, lat0,semimajor,semiminor,pa,assumed_size_if_none=15.0):
		"""assumed size = 15.0 arcsec"""
		d = self.distance(lon0,lat0,lon,lat)
		if pa == -99.0 and semimajor == 6e-99:
			
			if self.verbose:
				print "bad pa or size: returning %f %f" % (d/(assumed_size_if_none/3600.0),d)
			return (d/(assumed_size_if_none/3600.0), None)
		## get the angle from the center of this galaxy to the source
		dra  = self.distance(lon0,lat0,lon,lat0)
		ddec = self.distance(lon0,lat0,lon0,lat)
		
		if lat < lat0:
			ddec *= -1
		if lon < lon0:
			dra *= -1
		#if ((lon - lon0) > -180.0) and ((lon - lon0) < 180.0):
		# dra *= -1
		
		## this is the angle between the center of the galaxy and the source (east of North)
		a = atan2(dra,ddec)
		
		## relative to the semi-major axis the angle is
		t = a - radians(pa)
		
		## here's the r25 along this direction
		r = numpy.sqrt((semimajor**2)*(semiminor**2)/( (semimajor*numpy.sin(t))**2 + (semiminor*numpy.cos(t))**2))
		
		#print r, d, d*3600.0/r, lon0, lat0, lon, lat
		#print "*"*50
		return (d*3600.0/r, degrees(t))
		
def test():
	global ddd
	ddd = GalGetter(max_rows=-1)
	ddd.getgals()
	print ddd
	ddd.writeds9()
	
def test1():
	conn = sqlite3.connect(ddd.dbname)
	c = conn.cursor()
	c.execute('select * from galaxies')
	for r in c: print r

def get_closest_by_light(pos=(None,None),max_d=300.0,radius=1.0):
	"""to be called by the extrators"""
	ddd = GalGetter(verbose=False)	
	ddd.getgals(pos=pos,radius=1.0,sort_by="light",max_d=max_d)
	return ddd.grab_rez("light")

def get_closest_by_physical_offset(pos=(None,None),max_d=300.0,radius=1.0):
		"""to be called by the extrators in kpc"""
		ddd = GalGetter(verbose=False)	
		ddd.getgals(pos=pos,radius=1.0,sort_by="phys",max_d=max_d)
		return ddd.grab_rez("phys")

def get_closest_by_angular_offset(pos=(None,None),max_d=300.0,radius=1.0):
		"""to be called by the extrators in arcmin"""
		ddd = GalGetter(verbose=False)	
		ddd.getgals(pos=pos,radius=1.0,sort_by="dist",max_d=max_d)
		return ddd.grab_rez("dist")
	
if __name__ == "__main__":
	from optparse import OptionParser
	usage = "usage: %prog [options] -p ra dec\n"
	parser = OptionParser(usage)
	
	parser.add_option("--ds9name", dest="ds9name", \
	                  help="Name of the output ds9 region file",\
					  default="ds9.reg")
	
	parser.add_option("--nds9",dest="no_ds9", action="store_true",\
				      help="dont write the ds9 file",default=False)
				
	parser.add_option("--radius",dest="radius",\
					  help="Search radius in arcmin",type="float",default=60.0)

	parser.add_option("--maxd",dest="max_d",\
					    help="Maximum distance to search (in Mpc); default = 500 Mpc",type="float",default=500.0)

	parser.add_option("-v","--verbose",dest="verbose",action="store_true",\
				      help="Be verbose",default=False)

	parser.add_option("--ntop",dest="ntop",action="store_false",\
					   help="Dont print the top result",default=False)
	
	parser.add_option("--sortkey",dest="sortkey",choices = ['dist', 'dm', 'mag', 'light','phys'], \
					  help="Sort key: (dist; default) angular distance from source, " + \
						"(dm) proximity to Earth in Mpc, (mag) galaxy absolute mag, (light) light units, (phys) offset in kpc",default="dist")

	parser.add_option("-p", type="float", nargs=2, dest="pos")
	
	(options, args) = parser.parse_args()

#	if len(args) != 2:
#		print "You must supply RA and DEC in decimal degrees"
#		print usage
#		parser.parse_args(['-h'])
	
	if not options.pos:
		parser.parse_args(['-h'])
		
	ddd = GalGetter(verbose=options.verbose)
	ddd.getgals(pos=options.pos,radius=float(options.radius)/60.,sort_by=options.sortkey,max_d=options.max_d)
	if not options.no_ds9:
		ddd.writeds9(fname=options.ds9name)
	
	if not options.ntop:
		print ddd
