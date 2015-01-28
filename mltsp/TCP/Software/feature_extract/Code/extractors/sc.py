#!/usr/bin/env python

"""
dumbass tool to run skycoor on random assortment of coordinate string formats
"""
from __future__ import print_function
import os,string
skycoor = "/scisoft/i386/bin/skycoor"

def string_metrics(sss):
	
	if type(sss) != type("sss"):
		return {'digits': None, 'separators': None, 'letters': None}

	n_digits  = len([x for x in sss if x in string.digits])
	n_letters = len([x for x in sss if x in string.ascii_letters])
	n_digits  = len([x for x in sss if x in ",'=&+-: hmsd" or x in '"'])
	return {'digits': n_digits, 'separators': n_letters, 'letters': n_digits, 'len': len(sss)}
	
def sexify(sss):
	
	met = string_metrics(sss)
	if met['separators'] > 0:
		## figure out what the separator is
		nsplit ={}
		for s in ":hmsd":
			nsplit.update({s: len(sss.split(s)) - 1})
		#print nsplit
	
	## remove the letters
	sss = "".join([s for s in sss if s in string.digits or s in ["."]])
	
	hh = sss[0:2]
	mm = sss[2:4]
	ss = sss[4:]
	val = ":".join([hh,mm,ss])
	if sss.find(".") not in [6,-1]:
		val = sss
	
	return val
	
def reckonpos(a):
	
	ra, dec = None, None
		
	if len(a) == 1:
		## try removing letters
		#print a[0]
		seps = "hmso'" + '""'
		b = a[0]
		print(b)
		for s in seps:
			ttt = b.index(s)
			print(ttt)
			if ttt != -1:
				if string.digits.find(b[ttt - 1]) != -1  and string.digits.find(b[ttt - 2]) == -1:
					b[ttt - 2] = "0"
		a[0] = b
		print(b + "***")
		tmp = [a for a in a[0] if string.ascii_letters.find(a) == -1 and "=".find(a) == -1 and "'".find(a) == -1 \
		    and '"'.find(a) == -1]
		tmp = "".join(tmp)
		sss = "".join(tmp)
		sss = sss.strip()
		sss.replace("="," ")
		sss.replace("  "," ")
		sss.replace("\t","")
		sss.replace("\n","")
		if sss.count(".") > 1:
			## too many periods, remove all those at the beginning and the end
			sss = string.strip(sss,".")
		
		print(sss)
		tmp = [x for x in sss.split(" ") if x != ""]
		if len(tmp) == 6:
			ra = ":".join(tmp[0:3])
			dec = ":".join(tmp[3:6])
			return (ra,dec)
			

			
		tmp = [x for x in sss.split(":") if x != ""]		
		if len(tmp) == 6:
			ra = ":".join(tmp[0:3])
			dec = ":".join(tmp[3:6])
			return (ra,dec)
			
		# probably like: J000356.67+010007.3
	  	met = string_metrics(sss)

		## try to break on + or -
		notgood = False
		tmp  = sss.split("-")
		decsign = "-"
		if len(tmp) != 2:
			tmp = sss.split("+")
			decsign="+"
		 	if len(tmp) != 2:
				notgood = True
		if not notgood:
			ra  = sexify(tmp[0])
			dec = decsign + sexify(tmp[1])
		else:
			tmp = [x for x in sss.split(" ") if x != ""]
			if len(tmp) == 2:
				ra, dec = tmp[0], tmp[1]
				return (ra,dec)
			else:
				return (None,None)
	if len(a) == 6:
		## this is probably HH MM SS DD MM SS
		pass
	
	return (ra,dec)
	#print (ra, dec)

def clean(sss):
	
	if sss.count(".") > 1:
		## too many periods, remove all those at the beginning and the end
		sss = string.strip(sss,".")
	
	return sss	
if __name__ == "__main__":
	from optparse import OptionParser
	usage = "usage: %prog [options] 'ra dec'\n"
	parser = OptionParser(usage)

	(options, args) = parser.parse_args()

	if len(args) < 1:
		parser.parse_args(['-h'])
		
	#print args
	ra,dec = reckonpos(args)
	
	ra = clean(ra)
	dec = clean(dec)
	if ra.find(":") != -1:
		os.system(skycoor + " -dv %s %s" % (ra,dec))
	else:
		os.system(skycoor + " -v %s %s" % (ra,dec))

	#os.system(skycoor + " -v %s %s" % (ra,dec))
	
##
"""
./sc.py "3 33 48.97  +0 42 33.6"
./sc.py "RA 09:43:26.22  Dec 25:10:21.9 "
./sc.py "ra=55.497287&dec=-0.782905"
/sc.py " ra=55.49728745, dec=-0.78290499"

"""