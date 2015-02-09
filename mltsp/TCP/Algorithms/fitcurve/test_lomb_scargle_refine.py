#!/usr/bin/env python
"""
v 0.1 2011-04-21 Code from Nat

#########
Heres an example invocation to test:

from lomb_scargle_refine import lomb as lombr

sys_err=0.05
(x,y,dy)=load_some_data
dy0 = sqrt(dy**2+sys_err**2)

Xmax = x.max()
f0 = 1./Xmax; df = 0.1/Xmax; fe = 10.
numf = int((fe-f0)/df)
freqin = f0 + df*arange(numf,dtype='float64')

psd,res = lombr(x,y,dy0,f0,df,numf)
plot (freqin,psd)

###
The default is to fit 8 harmonics to every initial lomb-scargle peak
above 6, with 0th order detrending (fitting mean only).  Dan, if you
think I should, I can put the logic to define the frequency grid in
the main code and not in a wrapper like this.

res is a dictionary containing the stuff previously reported by
pre_whiten: amplitudes, phases, the folded model, etc.

To iterate 3 times (in not the most elegant fashion):
psd,res = lombr(x,y,dy0,f0,df,numf)
psd1,res1 = lombr(x,y-res['model'],dy0,f0,df,numf)
psd2,res2 = lombr(x,y-res['model']-res1['model'],dy0,f0,df,numf)

In the way we did this for the Deboscher paper, the first invocation
would have detrend_order=1 set, and we would use nharm=4 throughout.
I suspect we might get more mileage out of leaving nharm=8, but only
using stats on the first 4 as features.

"""
from __future__ import print_function


import sys, os
import random
from numpy import *


class Database_Utils:
    """ Establish database connections, contains methods related to database tables.
    """
    def __init__(self, pars={}):
        self.pars = pars
        #self.connect_to_db()


    def connect_to_db(self):
        import MySQLdb
        self.tcp_db = MySQLdb.connect(host=pars['tcp_hostname'], \
                                  user=pars['tcp_username'], \
                                  db=pars['tcp_database'],\
                                  port=pars['tcp_port'])
        self.tcp_cursor = self.tcp_db.cursor()

        self.tutor_db = MySQLdb.connect(host=pars['tutor_hostname'], \
                                  user=pars['tutor_username'], \
                                  db=pars['tutor_database'], \
                                  passwd=pars['tutor_password'], \
                                  port=pars['tutor_port'])
        self.tutor_cursor = self.tutor_db.cursor()


    def get_timeseries_for_source(self, source_id=None):
        """ Get timeseries data from tutor when given a source_id

        """
        select_str = """SELECT sources.source_id, observation_id, obsdata_time, obsdata_val, obsdata_err
        FROM sources
        JOIN observations USING (source_id)
        JOIN obs_data USING (observation_id)
        WHERE source_id=%d
        """  % (source_id)
        self.tutor_cursor.execute(select_str)
        results = self.tutor_cursor.fetchall()
        if len(results) == 0:
            raise "Error"

        t_list = []
        m_list = []
        m_err_list = []
        used_src_id = results[0][0]
        used_obs_id = results[0][1]
        for (src_id, obs_id, t, m, err) in results:
            if ((src_id == used_src_id) and
                (obs_id == used_obs_id)):
                t_list.append(t)
                m_list.append(m)
                m_err_list.append(err)

        return {'t':array(t_list),
                'm':array(m_list),
                'm_err':array(m_err_list)}



if __name__ == '__main__':

    ### NOTE: most of the RDB parameters were dupliclated from ingest_toolspy::pars{}
    pars = { \
    'tutor_hostname':'192.168.1.103', #'lyra.berkeley.edu',
    'tutor_username':'dstarr', #'tutor', # guest
    'tutor_password':'ilove2mass', #'iamaguest',
    'tutor_database':'tutor',
    'tutor_port':3306,
    'tcp_hostname':'192.168.1.25',
    'tcp_username':'pteluser',
    'tcp_port':     3306, 
    'tcp_database':'source_test_db',
    'high_conf_srcids':range(22), #[241682, 238040, 221547, 225633, 227203, 250761, 219325, 252782, 245584, 236706, 216173, 225396, 233750, 232693, 263653, 216768, 225919, 264626, 230520, 229680, 231266, 221448, 226872, 261712], # Used for session=0, iter=1 (1st)
    }


    dbutil = Database_Utils(pars=pars)

    #import pdb; pdb.set_trace()
    #print


    #########
    #Heres an example invocation to test:

    from lomb_scargle_refine import lomb as lombr

    sys_err=0.05
    #(x,y,dy)=load_some_data

    fpath = '/home/training/scratch/ls_src.dat'
    if os.path.exists(fpath):
        x = []
        y = []
        dy = []
        fp = open(fpath)
        lines = fp.readlines()
        for line in lines:
            e = line.split()
            x.append(float(e[0]))
            y.append(float(e[1]))
            dy.append(float(e[2]))
        fp.close()
        x = array(x)
        y = array(y)
        dy = array(dy)
        
        
    else:
        data = dbutil.get_timeseries_for_source(source_id=241682)
        x = data['t']
        y = data['m']
        dy = data['m_err']

        fp = open(fpath, 'w')
        for i in range(len(x)):
            fp.write("%lf %lf %lf\n" % (x[i], y[i], dy[i]))
        fp.close()


    dy0 = sqrt(dy**2+sys_err**2)

    Xmax = x.max()
    f0 = 1./Xmax; df = 0.1/Xmax; fe = 10.
    numf = int((fe-f0)/df)
    freqin = f0 + df*arange(numf,dtype='float64')

    #psd,res = lombr(x,y,dy0,f0,df,numf)
    psd,res = lombr(x,y,dy0,f0,df,numf, detrend_order=1)
    import pdb; pdb.set_trace()
    print()
    psd1,res1 = lombr(x,y-res['model'],dy0,f0,df,numf, detrend_order=0)
    plot (freqin,psd)

    ###
    """
    The default is to fit 8 harmonics to every initial lomb-scargle peak
    above 6, with 0th order detrending (fitting mean only).  Dan, if you
    think I should, I can put the logic to define the frequency grid in
    the main code and not in a wrapper like this.

    res is a dictionary containing the stuff previously reported by
    pre_whiten: amplitudes, phases, the folded model, etc.

    To iterate 3 times (in not the most elegant fashion):
    psd,res = lombr(x,y,dy0,f0,df,numf)
    psd1,res1 = lombr(x,y-res['model'],dy0,f0,df,numf)
    psd2,res2 = lombr(x,y-res['model']-res1['model'],dy0,f0,df,numf)

    In the way we did this for the Deboscher paper, the first invocation
    would have detrend_order=1 set, and we would use nharm=4 throughout.
    I suspect we might get more mileage out of leaving nharm=8, but only
    using stats on the first 4 as features.
    """ 
