#!/usr/bin/env python
"""
eclipse_features -- generate a dict of features related to 
                    classification of eclipsing systems
                    in pulsational variables

is_suspect             Is there a reason not to trust the orbital period measurement?
p_pulse	               Pulsational period (dominant period found by LS)
feature-X-ratio-diff   percent of sources more than X sigma fainter than model
                          relative to X sigma brighter (neg has more faint values)	
                          x = [5,8,15,20,30]
best_orb_period	       best period found after removing the pulsational period
suspect_reason         semicolon separated list why orb_period is suspect
best_orb_chi2	       best chi2 fitting orb_period from polyfit
orb_signif             LS significance
"""

__author__ = "J. S. Bloom, D. Starr"
__version__ = "0.32"

import os, sys
import numpy as np
from scipy.optimize import fmin

sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                      'Algorithms/fitcurve'))

from lomb_scargle_refine import lomb as lombr
import copy
import selectp
from matplotlib import pylab as plt

def _load_ben_data(fname="LC_246.dat"):
    
    """loader for Ben's input files"""
    
    from matplotlib.mlab import csv2rec
    ## Get the photometry
    name = str(int(fname[fname.find("_")+1:fname.find(".dat")]))
    c = csv2rec(fname,delimiter=" ",names=["t","m","merr","rrl"])
    x0 = c['t']
    y  = c['m']
    dy = c['merr']
    return x0,y,dy, name

def _load_dotastro_data(fname="013113-7829.1.xml"):
    
    """loader for dotastro xml files"""
    sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                    'Software/feature_extract/Code'))
    import db_importer

    b = db_importer.Source(xml_handle=fname)
    kk = b.ts.keys()
    ind = 0
    photkey = kk[ind]
    ts = b.ts
    x0 = np.array(ts[photkey]['t'])
    y = np.array(ts[photkey]['m'])
    dy = np.array(ts[photkey]['m_err'])
    name = fname.split(".xml")[0]
    return x0,y,dy, name
    
class ebfeature:
    
    def __init__(self,t=None, m=None, merr=None, name="", allow_plotting=True, sys_err=0.03, \
                 verbose=False, fix_initial_period=False, initial_period=1.0, srcid=0):
        
        self.allow_plotting = allow_plotting
        self.name = name
        self.t = t ; self.m = m ; self.merr = merr ; self.sys_err = sys_err            
        self.verbose = verbose
        self.fix_initial_period=fix_initial_period ; self.initial_period = initial_period
        self.features = {"run": False}
        self.srcid = srcid
        
    def _get_pulsational_period(self,min_freq=10.0,doplot=False,max_pulse_period=400.0):
        self.x0 = self.t
        self.y = self.m
        self.dy = self.merr
        self.dy0 = np.sqrt(self.dy**2+self.sys_err**2)
        self.x0 -= self.x0.min()
        self.nepochs = len(self.x0)

        # define the frequency grid
        Xmax = self.x0.max()
        if not  self.fix_initial_period:
            f0 = 1.0/max_pulse_period; df = 0.1/Xmax; fe = min_freq
            numf = int((fe-f0)/df)
        else:
            f0 = 1./self.initial_period
            df = 1e-7
            numf = 1
            
        psdr,res2 = lombr(self.x0,self.y,self.dy0,f0,df,numf,detrend_order=1)
        period=1./res2['freq']
        self.rrlp = period
        if self.verbose:
            print "Initial pulstional Period is %.8f day" % self.rrlp
        
        self.features.update({"p_pulse_initial": self.rrlp})
        
        if self.allow_plotting and doplot:
            try:
                plt.figure(3)
                plt.cla()
                tt=(self.x0/period) % 1.; s=tt.argsort()
                plt.errorbar (tt,self.y,self.dy,fmt='o'); plt.plot(tt[s],res2['model'][s])
                plt.ylim(self.y.max()+0.05,self.y.min()-0.05)
                plt.title("P=%f" % (self.rrlp))
                plt.draw()
            except:
                pass
        return res2
    
    def gen_outlier_stat_features(self,doplot=False,sig_features=[30,20,15,8,5],\
        min_freq=10.0,dosave=True,max_pulse_period=400.0):
        """here we generate outlier features and refine the initial pulsational period
            by downweighting those outliers.
        """
        
        res2 = self._get_pulsational_period(doplot=doplot,min_freq=min_freq)
        
        ## now sigclip
        offs = (self.y - res2['model'])/self.dy0
        moffs = np.median(offs)
        offs -= moffs
        
        ## do some feature creation ... find the statistics of major outliers
        for i,s in enumerate(sig_features):
            rr = (np.inf,s) if i == 0 else (sig_features[i-1],s)
            tmp = (offs < rr[0]) & (offs > rr[1])
            nlow = float(tmp.sum())/self.nepochs
            tmp = (offs > -1*rr[0]) & (offs < -1*rr[1])
            nhigh = float(tmp.sum())/self.nepochs
            if self.verbose:
                print "%i: low = %f high = %f  feature-%i-ratio-diff = %f" % (s,nlow,nhigh,s,nhigh - nlow)
            
            self.features.update({"feature-%i-ratio-diff" % s: (nhigh - nlow)*100.0})
            
        tmp = np.where(abs(offs) > 4)
        self.dy_orig = copy.copy(self.merr)
        dy      = copy.copy(self.merr)
        dy[tmp] = np.sqrt(dy[tmp]**2 + res2['model_error'][tmp]**2 + (8.0*(1 - np.exp(-1.0*abs(offs[tmp])/4)))**2)
        dy0 = np.sqrt(dy**2+self.sys_err**2)
        
        #Xmax = self.x0.max()
        #f0 = 1.0/max_pulse_period; df = 0.1/Xmax; fe = min_freq
        #numf = int((fe-f0)/df)
        
        #refine around original period
        ## Josh's original calcs, which fail for sources like: 221205
        ##df = 0.1/self.x0.max()
        ##f0 = res2['freq']*0.95
        ##fe = res2['freq']*1.05
        ##numf = int((fe-f0)/df)

        df = 0.1/self.x0.max()
        f0 = res2['freq']*0.95
        fe = res2['freq']*1.05
        numf = int((fe-f0)/df)
        if numf == 0:
            ## Josh's original calcs, which fail for sources like: 221205
            numf = 100 # kludge / fudge / magic number
            df = (fe-f0) / float(numf)
            
        psdr,res = lombr(self.x0,self.y,dy0,f0,df,numf,detrend_order=1)
        period=1./res['freq']
        
        self.features.update({"p_pulse": period})

        if self.allow_plotting and doplot:
            try:
                tt=(self.x0*res2['freq']) % 1.; s=tt.argsort()
                plt.errorbar (tt[tmp],self.y[tmp],self.dy_orig[tmp],fmt='o',c="r")
                tt=(self.x0*res['freq']) % 1.; s=tt.argsort()
                plt.plot(tt[s],res['model'][s],c="r")
                if dosave:
                    plt.savefig("pulse-%s-p=%f.png" % (os.path.basename(self.name),period))
                    if self.verbose:
                        print "saved...", "pulse-%s-p=%f.png" % (os.path.basename(self.name),period)
                plt.draw()
            except:
                pass
        return offs, res2
        
    def gen_orbital_period(self, doplot=False, sig_features=[30,20,15,8,5], min_eclipses=4,
                           eclipse_shorter=False, dynamic=True, choose_largest_numf=False):
        """ 
        """
        try:
            offs,res2 = self.gen_outlier_stat_features(doplot=doplot,sig_features=sig_features)

            ## subtract the model
            new_y = self.y - res2['model']
            
            # make new weights that penalize sources _near_ the model
            dy0 = np.sqrt(self.dy_orig**2+ res2['model_error']**2 + (3*self.sys_err*np.exp(-1.0*abs(offs)/3))**2)  ## this downweights data near the model
            Xmax = self.x0.max()
            #import pdb; pdb.set_trace()
            #print

            if choose_largest_numf:
                f0 = min_eclipses/Xmax
                df = 0.1/Xmax
                fe = res2['freq']*0.98  ## dont go near fundamental freq least we find it again
                numf = int((fe-f0)/df)

                f0_b = res2['freq']*0.98
                fe_b = 10.0
                df_b = 0.1/Xmax
                numf_b = int((fe_b-f0_b)/df_b)

                if numf < numf_b:
                    f0 = f0_b
                    fe = fe_b
                    df = df_b
                    numf = numf_b
            else:
                if not eclipse_shorter:
                    f0 = min_eclipses/Xmax
                    df = 0.1/Xmax
                    fe = res2['freq']*0.98  ## dont go near fundamental freq least we find it again
                    numf = int((fe-f0)/df)
                else:
                    f0 = res2['freq']*0.98
                    fe = 10.0
                    df = 0.1/Xmax
                    numf = int((fe-f0)/df)
                
            freqin = f0 + df*np.arange(numf,dtype='float64')
            periodin = 1/freqin
            
            if self.verbose:
                print "P min, max", min(periodin),max(periodin)

            psdr,res2 = lombr(self.x0,new_y,self.dy0,f0,df,numf)
            period=1./res2['freq']
            if self.verbose:
                print "orb period = %f sigf = %f" % (period,res2['signif'])
            self.last_res = res2
            s = selectp.selectp(self.x0, new_y, self.dy_orig, period, mults=[1.0,2.0], dynamic=dynamic, verbose=self.verbose, srcid=self.srcid)
            s.select()
            
            self.features.update({"best_orb_period": s.rez['best_period'], "best_orb_chi2": \
                s.rez['best_chi2'], 'orb_signif': res2['signif']})
                
            is_suspect = False
            reason = []
            if abs(1.0 - self.features['best_orb_period']) < 0.01 or abs(2.0 - self.features['best_orb_period']) < 0.01 or \
                abs(0.5 - self.features['best_orb_period']) < 0.01:
                ## likely an alias
                is_suspect=True
                reason.append("alias")
            if self.features['best_orb_chi2'] > 10.0 or self.features['orb_signif'] < 4:
                is_suspect=True
                reason.append("low significance")
            if self.features['best_orb_period'] > Xmax/(2*min_eclipses):
                ## probably too long
                is_suspect=True
                reason.append("too long")
            if (0.5 - abs( (self.features['best_orb_period'] / self.features['p_pulse']) % 1.0 - 0.5)) < 0.01:
                ## probably an alias of the pulse period
                is_suspect=True
                reason.append("pulse alias")
            
            self.features.update({'is_suspect': is_suspect, 'suspect_reason': None if not is_suspect else \
                "; ".join(reason)})
            
            
            if doplot:
                try:
                    plt.figure(2)
                    plt.cla()
                    s.plot_best(extra="suspect=%s %s" % (is_suspect,"" if not is_suspect else "(" + ",".join(reason) + ")"))
                    plt.savefig("orb-%s-p=%f-sig=%f.png" % (os.path.basename(self.name),period,res2['signif']))
                    if self.verbose:
                        print "saved...", "org-%s-p=%f.png" % (os.path.basename(self.name),period)
                except:
                    pass
        except:
            return

        
    def old_stuff(self):
        print res2['chi2'], res2['chi0']
        if self.verbose:
            print "New Period is %.8f day" % period
        
        plt.figure(2)
        plt.cla()
        tt=(self.x0/period) % 1.; s=tt.argsort()
        plt.errorbar (tt[s],new_y[s],self.dy_orig[s],fmt='o',c="b")
        plt.plot(tt[s],res2['model'][s],c="r")
        
        f = open("lc.dat","w")
        z = zip(tt[s] - 0.5,new_y[s],self.dy_orig[s])
        for l in z:
            f.write("%f %f %f\n" % l)
        f.close()
        
        f = open("lc0.dat","w")
        z = zip(self.x0,new_y,self.dy_orig)
        for l in z:
            f.write("%f %f %f\n" % l)
        f.close()
        
        
        psdr,res2 = lombr(self.x0,new_y,self.dy0,f0/2.,df,numf)
        period1=1./res2['freq']

        if self.verbose:
            print "New Period is %.8f day" % period1
        
        plt.figure(4)
        plt.cla()
        tt=(self.x0/period1) % 1.; s=tt.argsort()
        plt.errorbar (tt[s],new_y[s],self.dy_orig[s],fmt='o',c="b")
        plt.plot(tt[s],res2['model'][s],c="r")
        print res2['chi2'], res2['chi0']
        f = open("lc2.dat","w")
        z = zip(tt[s] - 0.5,new_y[s],self.dy_orig[s])
        for l in z:
            f.write("%f %f %f\n" % l)
        f.close()

def runben(doplot=False):

    import glob
    from matplotlib.mlab import csv2rec
    import numpy as np
    l = glob.glob("/Users/jbloom/Dropbox/LCS/LCnew_??.dat")
    if os.path.exists("benfeatures.csv"):
        ttt = csv2rec("benfeatures.csv")
        header=False
    else:
        header=True
        ttt = np.rec.fromarrays([-1],names='name',formats='i4')
        
    m = open("benfeatures.csv","a")
    has_run = False
    for f in l:
        if f.find(".dat") != -1:
            fname = f
            print "working on", f
            x0,y,dy, name =_load_ben_data(fname)
            if len(np.where(ttt['name'] == int(os.path.basename(name)))[0]) != 0:
                print "... already in list, skipping"
                continue
            a = ebfeature(t=x0,m=y,merr=dy,name=name)
            a.gen_orbital_period(doplot=doplot)
            if doplot:
                plt.draw()
            if not has_run:
                ff = a.features.keys()
                ff.remove("run")
                ff.remove("p_pulse_initial")
                if header:
                    m.write("name," + ",".join(ff) + "\n")
                has_run = True

            m.write(os.path.basename(name) + "," + ",".join([str(a.features.get(s)) for s in ff]) + "\n")
    m.close()
            
def runcand(doplot=False):
    
    import time
    l = os.listdir("BenLike/")
    m = open("features.csv","w")
    has_run = False
    for f in l:
        if f.find(".xml") != -1:
            fname = "BenLike/" + f
            print "working on", f
            x0,y,dy, name = _load_dotastro_data(fname)
            a = ebfeature(t=x0,m=y,merr=dy,name=name)
            a.gen_orbital_period(doplot=doplot)
            if doplot:
                plt.draw()
            if not has_run:
                ff = a.features.keys()
                ff.remove("run")
                ff.remove("p_pulse_initial")
                m.write("name," + ",".join(ff) + "\n")
                has_run = True
            
            m.write(os.path.basename(name) + "," + ",".join([str(a.features.get(s)) for s in ff]) + "\n")
            time.sleep(1)
    m.close()
           
                
def test():
    
    """This is a test to show how to Ben's input files (t, m, merr)"""
    x0,y,dy, name = _load_ben_data()
    import pdb; pdb.set_trace()
    print
    a = ebfeature(t=x0,m=y,merr=dy,fix_initial_period=True,initial_period=0.4422664540092584,name=name)
    a.gen_orbital_period(doplot=True)
    print a.features
    
def test2():
    
    """This is a test to show how to use doastro xml files"""
    x0,y,dy, name = _load_dotastro_data()
    
    # note: if you already know the pulsational period, see test() above for 
    #  ebfeature instantiation
    a = ebfeature(t=x0,m=y,merr=dy,name=name)
    a.gen_orbital_period(doplot=True)
    print a.features
    
if __name__ == '__main__':
    ### this section is just for testing
    # using t, m, merr:
    test()
    import pdb; pdb.set_trace()
    print

    ### using xml file:
    test2()

