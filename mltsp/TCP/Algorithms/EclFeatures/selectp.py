"""
Select a period.

Runs polyfit (adapted from PHOEBE) and looks for a period 
with the lowest chi-sq. you input the trial period and it will look 
at aliases of that period. Assumed to be an eclipsing system.

See test() for usage

J.S.Bloom, Aug 2011

"""
import ctypes, sys, tempfile, os
from ctypes import c_char_p
from matplotlib.mlab import csv2rec
from matplotlib import pylab as plt
from numpy import where
import StringIO
import traceback
import time
# path to polyfit executable if dynamic = False

# gcc -m32 -L/usr/local/lib polyfit.c -lgsl -lgslcblas -lm -o polyfit
# gcc -m32 -shared -Wl -o polyfit.so polyfit.o -lc -lgsl -lgslcblas -lm 
exec_path = "./polyfit"

class selectp:
    

    def __init__(self,t, y, dy, period, mults=[0.5,1,2],\
        order=2, iknots=[-0.4,-0.2,0.2,0.4], exec_fpath='',
        dynamic=True, mag=True, verbose=False, srcid=0):
        
        self.verbose = verbose
        self.rez    = {'models': []}
        self.order  = order
        self.iknots = iknots
        self.t      = t
        self.y      = y
        self.dy     = dy
        self.period = period
        self.mults  = mults
        self.mag    = mag   # y values in mag not flux
        self.srcid = srcid
        self.dynamic = dynamic
        #if len(exec_fpath) > 0:
        #    self.poly = exec_fpath
        #else:
        #    self.poly = exec_path
        self.poly = os.path.abspath(os.environ.get("TCP_DIR") + 'Algorithms/EclFeatures/polyfit')
        if dynamic:
            ## load the dynamic library
            try:
                self.polyfit = ctypes.cdll.LoadLibrary(os.path.abspath(os.environ.get("TCP_DIR") + 'Algorithms/EclFeatures/polyfit.so'))
            except:
                print "cannot load polyfit.so"            

        self.ok = True
        
    def _runp(self,p):
        if not self.ok:
            return -1
            
        ## try running with that period
        if self.verbose:
            print "   --> running with period ... %f" % p
        # write out phased photometry to the file -- center the most faint point at 0
        tt=(self.t/p) % 1.; s=tt.argsort()
        x = tt[s]; y = self.y[s] ; z = self.dy[s]
        if self.mag:
            mm = where(y == max(y))
        else:
            mm = where(y == min(y))
        pmm = x[mm]
        tt = (((self.t/p) % 1.0) - pmm + 0.5) % 1.0; s=tt.argsort()
        x = tt[s]; y = self.y[s] ; z = self.dy[s]
        z = zip(x - 0.5,y,z)
        f = tempfile.NamedTemporaryFile(dir="/tmp",suffix=".dat",delete=False)
        name = f.name
        #(f,name) = tempfile.mkstemp(dir="/tmp",suffix=".dat")
        #f = open(name,"w")
        lines = []
        for l in z:
            lines.append("%f %f %f\n" % l)
        write_str = ''.join(lines)
        f.write(write_str)
        f.flush() # dstarr adds to maybe reduce segfaults
        f.close()

        try:
            loop_max = 300
            i_loop = 0
            while ((os.stat(name).st_size < len(write_str)) and (i_loop < loop_max)):
                time.sleep(1)
                i_loop += 1
            if i_loop >= loop_max:
                self.rez["models"].append({"period": p, "phase": None, 'f': None, 'chi2': 100000})
                os.remove(name)
                return # maybe this is a good way to catch the segfault issue sources prior to segfaulting?
        except:
            self.rez["models"].append({"period": p, "phase": None, 'f': None, 'chi2': 100000})
            os.remove(name)
            return # maybe this is a good way to catch the segfault issue sources prior to segfaulting?

        
        tmp = "%s -o %i -k %s --find-step --chain-length 30 %s" % \
            (self.poly,self.order," ".join(["%.2f" % k for k in self.iknots]),name)
        alttmp = "%s -o %i -k %s --find-knots --find-step --chain-length 30 %s" % \
            (self.poly,self.order," ".join(["%.2f" % k for k in [-0.45,-0.35,0.40,0.45]]),name)

        #import pdb; pdb.set_trace()
        #print
        
        if self.dynamic: 
            # make the argv vector           
            argv = tmp.split()
            argc = len(argv)
            argv_type = ctypes.c_char_p * len(argv)
            argv = argv_type(*argv)
            argc = ctypes.c_int(argc)
            self.polyfit.altmain.restype = ctypes.c_float
            f1 = tempfile.TemporaryFile()
            oldstdout = os.dup(sys.stdout.fileno())
            os.dup2(f1.fileno(), 1)
            res = self.polyfit.altmain(argc,argv)
            os.dup2(oldstdout, 1)
            f1.seek(0)
            s = csv2rec(f1,delimiter="\t")
            self.rez["models"].append({"period": p, "phase": s['phase'], 'f': s['flux'], 'chi2': res})
        else:
            from subprocess import PIPE,Popen

            #os.system("touch /global/home/users/dstarr/500GB/debug2/%d" % (self.srcid + 100000000))

            pp = Popen(tmp, shell=True,stdin=PIPE, stdout=PIPE, \
                                 stderr=PIPE, close_fds=True)
            #sts = os.waitpid(pp.pid, 0)[1]
            pp.wait()


            (child_stdin,child_stdout,child_stderr) = (pp.stdin, pp.stdout, pp.stderr)
            ttt = child_stdout.readlines() ; ttt1 =  child_stderr.readlines() 
            child_stdin.close() ;  child_stdout.close() ; child_stderr.close()
            if len(ttt) == 0 and len(ttt1) == 0:
                # probably a seg fault
                if self.verbose:
                    print "  --> trying",alttmp
                pp = Popen(alttmp, shell=True,stdin=PIPE, stdout=PIPE, \
                                     stderr=PIPE, close_fds=True)
                pp.wait()
                (child_stdin,child_stdout,child_stderr) = (pp.stdin, pp.stdout, pp.stderr)
                ttt = child_stdout.readlines() ; ttt1 =  child_stderr.readlines() 
                child_stdin.close() ;  child_stdout.close() ; child_stderr.close()
                if len(ttt) == 0 and len(ttt1) == 0:
                    self.rez["models"].append({"period": p, "phase": None, 'f': None, 'chi2': 100000})
                    os.remove(name)
                    return
            ttt1 = StringIO.StringIO("".join(ttt))  # make a new file
            s = csv2rec(ttt1,delimiter="\t")
            chi2 = 100000
            for l in ttt:
                if l.find("Final chi2:") == -1:
                    continue
                chi2 = float(l.split("Final chi2:")[-1])
            self.rez["models"].append({"period": p, "phase": s['phase'], 'f': s['flux'], 'chi2': chi2})
        os.remove(name)
            
    def select(self):
        for m in self.mults:
            self._runp(m*self.period)
        r = [(x['chi2'],x['period']) for x in self.rez['models']]
        r.sort()
        if self.verbose:
            print "   .... best p = ", r[0][1], "best chi2 = ", r[0][0]
        self.rez.update({"best_period": r[0][1], "best_chi2": r[0][0]})
    
    def plot_best(self,extra=""):
        b = [x for x in self.rez['models'] if x['period'] == self.rez['best_period']][0]
        from matplotlib import pylab as plt
       
        tt=(self.t/self.rez['best_period']) % 1; s=tt.argsort()
        x = tt[s]; y = self.y[s] ; z = self.dy[s]
        if self.mag:
            mm = where(y== max(y))
        else:
            mm = where(y== min(y))
        pmm = x[mm]
        tt = (((self.t/self.rez['best_period']) % 1.0) - pmm + 0.5) % 1.0; s=tt.argsort()
        x = tt[s] - 0.5; y = self.y[s] ; z = self.dy[s]
        
        plt.errorbar (x,y,z,fmt='o',c="r")
        plt.plot(b['phase'],b['f'],c="b")
        plt.ylim(self.y.max()+0.05,self.y.min()-0.05)
        plt.xlabel("phase")
        plt.ylabel("flux/mag")
        plt.title("Best p = %.6f (chi2 = %.3f)" % (self.rez['best_period'],self.rez['best_chi2']))
        plt.text(-0.2,self.y.max() - 0.05, "%s" % extra, ha='center',alpha=0.5)
        
def test():
    x = csv2rec("lc.dat",delimiter=" ",names=["t","y","dy"])
    s = selectp(x['t'],x['y'],x['dy'],21.93784630,dynamic=False,verbose=True)
    s.select()
    print s.rez
    s.plot_best()

            
