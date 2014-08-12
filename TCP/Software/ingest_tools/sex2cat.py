#!/bin/env python

"""
converts sex to ds9 catalog file. Allows user to input directly
into the ds9 image and search as you would, e.g., 2MASS or USNO B1.0
"""

import os,sys,datetime,copy

__author__ = "JSB"

__version__ = "0.1; 12 June 2006"

## get this as part of the starbase list
sextotable = '/usr/local/bin/sextotable'
if not os.path.exists(sextotable):
   sextotable = os.path.expanduser("~") + "/redux/Helper/sextotable"



def sex2cat(fname,outname=None,append_filter=True):
    """
    note: it's assumed that you have a sextractor file with ALPHA_J2000 and DELTA_J2000
    headers. Such .sex files will be generated from trans.photm
    """
    if not os.path.exists(sextotable):
        print "sextotable path does not exist"
        return None
    
    if not os.path.exists(fname):
        print "input files %s does not exist" % fname
        return None
    
    if append_filter:
        ## parse out the filter name from the sextractor file
        f = open(fname,'r')
        ll = f.readlines()
        f.close()
        filter = 'unknown'
        start_cpu = 'unknown'
        stop_cpu  = 'unknown'
        phot_rms = 'unknown'
        
        for l in ll:
           if l.find('STRT_CPU =') != -1:
              start_cpu = l.split('STRT_CPU =')[1].split('#')[0].strip()
           if l.find('STOP_CPU =') != -1:
              stop_cpu = l.split('STOP_CPU =')[1].split('#')[0].strip()
           if l.find('PHOT_RMS =') != -1:
              phot_rms = l.split('PHOT_RMS =')[1].split('#')[0].strip()

        for l in ll:
           if l.find('FILTER =') != -1:
              filter = l.split('FILTER =')[1].split('#')[0].strip()
              break
        print 'detected the filter as: %s' % filter
        
    if outname is None:
        outname = fname + ".cat"
        
    
    if os.path.exists(outname):
        os.remove(outname)
    
    os.system("%s < %s > %s" % (sextotable,fname,outname))
    ## now edit that file
    f = open(outname,'r')
    ll = f.readlines()
    f.close()

    outl = []
    for l in ll:
        if l.find('ALPHA_J2000') != -1:
            l = l.replace('ALPHA_J2000',"_RAJ2000")
            l = l.replace('DELTA_J2000',"_DEJ2000")
            if append_filter and filter != 'unknown':
                l = l.replace('MAG', filter + "MAG")
        if l.find("KEYWORDS") == -1:
            outl.append(l)
        
    
    extra = ["# written by sex2cat\n", "# from file %s at %s\n" % (fname,datetime.datetime.utcnow()),\
             "# version = %s author = %s\n" % (__version__,__author__), \
             '# PHOT_RMS = %s\n' % (phot_rms), \
             '# STRT_CPU = %s\n' % (start_cpu), \
             '# STOP_CPU = %s\n\n' % (stop_cpu)]
    
    f = open(outname,'w')
    f.writelines(extra)
    f.writelines(outl)
    f.close()
    
    return outname
    
if __name__ == "__main__":
    
    outname = None
    if len(sys.argv) <= 1:
        print "usage: sex2cat.py insexname.sex [outname]"
        sys.exit()
        
    if len(sys.argv) > 2:
        outname = sys.argv[2]
    
    ret = sex2cat(sys.argv[1],outname)
    print "returned: %s" % ret
    
    
