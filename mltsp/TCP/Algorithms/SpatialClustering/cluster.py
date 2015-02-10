#!/usr/bin/env python

"""
cluster: Monte Carlo simulation of clustering
"""
from __future__ import print_function

import os,sys
import datetime
try:
    from matplotlib import pylab
except:
    pass
try:
    from pylab import *
except:
    pass
from numarray import random_array
import time
import copy 
import math
import random
import numarray

start_time = time.time()
global blah


def is_object_associated_with_source_algorithm_jbloom(n_sources, \
                          obj_ra, obj_dec, obj_ra_rms, obj_dec_rms, \
                          src_ra, src_dec, src_ra_rms, src_dec_rms, sigma_0):
    """ Source matching algorithm
    Input: obj & source ra,dec,errors
    Return: True/False conditional result
    """
    # log (Po(center)*Ps(center)/Po(midpoint)Ps(midpoint))
    #Poc   = -1.0* math.log(self.assumed_err[0]*self.assumed_err[1]*2.0*math.pi)
    #Psc   = -1.0* math.log(s.current_err[0]*s.current_err[1]*2.0*math.pi)

    # This try/except is kudgy, since RMS for both sources or objects should not be 0:
    #   I think this only occurs for errant cases, while debugging, or integrating a new survey.
    try:
        midpt  = [(obj_ra/obj_ra_rms**2 + src_ra/src_ra_rms**2)/ \
                    (1/obj_ra_rms**2 + 1/src_ra_rms**2), \
              (obj_dec/obj_dec_rms**2 + src_dec/src_dec_rms**2)/ \
                    (1/obj_dec_rms**2 + 1/src_dec_rms**2)]
    except:
        if src_ra_rms == 0:
            src_ra_rms = 0.2 # default arcsecs
        if src_dec_rms == 0:
            src_dec_rms = 0.2 # default arcsecs
        if obj_ra_rms == 0:
            obj_ra_rms = 0.2 # default arcsecs
        if obj_dec_rms == 0:
            obj_dec_rms = 0.2 # default arcsecs
        midpt  = [(obj_ra/obj_ra_rms**2 + src_ra/src_ra_rms**2)/ \
                    (1/obj_ra_rms**2 + 1/src_ra_rms**2), \
              (obj_dec/obj_dec_rms**2 + src_dec/src_dec_rms**2)/ \
                    (1/obj_dec_rms**2 + 1/src_dec_rms**2)]


    #miderr = [math.sqrt(1.0/(self.assumed_err[0]**(-2) + s.current_err[0]**(-2))),\
    #          math.sqrt(1.0/(self.assumed_err[0]**(-2) + s.current_err[0]**(-2)))]
    #print (midpt,self.pos,self.assumed_err,s.current_pos,s.current_err)
    #Pom   = -1.0* math.log(self.assumed_err[0]*self.assumed_err[1]*2.0*math.pi) - 0.5*(  ((self.pos[0] - midpt[0])/self.assumed_err[0])**2 + \
    #    ((self.pos[1] - midpt[1])/self.assumed_err[1])**2)
    #Psm   = -1.0* math.log(s.current_err[0]*s.current_err[1]*2.0*math.pi) - 0.5*(  ((s.current_pos[0] - midpt[0])/s.current_err[0])**2 + \
    #        ((s.current_pos[1] - midpt[1])/s.current_err[1])**2)
    #odds = -1.0 * (Poc + Psc - Pom - Psm)
    cos_dec_term = math.cos(midpt[1]*math.pi/(180.0*3600.0)) # obj/src positions are in arcsec & need to be converted to radians in cos()
    simple_odds = - 0.5*(  (cos_dec_term*(src_ra - midpt[0])/src_ra_rms)**2 + \
                           ((src_dec - midpt[1])/src_dec_rms)**2) \
                  - 0.5*(  (cos_dec_term*(obj_ra - midpt[0])/obj_ra_rms)**2 + \
                           ((obj_dec - midpt[1])/obj_dec_rms)**2)
    #-2*logpop = chi^2 = sigma^2 --> sqrt(10)
    num_obs_associated = n_sources
    sigma_n            = sqrt(2.0*log(num_obs_associated))
            
    return ((-2.828*simple_odds < sigma_n**2 + sigma_0**2), simple_odds, sigma_n, midpt)


# 20071008 works, original algorihtms, un-normalized
def is_object_associated_with_source_algorithm_jbloom_orig(n_sources, \
                          obj_ra, obj_dec, obj_ra_rms, obj_dec_rms, \
                          src_ra, src_dec, src_ra_rms, src_dec_rms, sigma_0):
    """ Source matching algorithm
    Input: obj & source ra,dec,errors
    Return: True/False conditional result
    """
    # log (Po(center)*Ps(center)/Po(midpoint)Ps(midpoint))
    #Poc   = -1.0* math.log(self.assumed_err[0]*self.assumed_err[1]*2.0*math.pi)
    #Psc   = -1.0* math.log(s.current_err[0]*s.current_err[1]*2.0*math.pi)
    midpt  = [(obj_ra/obj_ra_rms**2 + src_ra/src_ra_rms**2)/ \
                    (1/obj_ra_rms**2 + 1/src_ra_rms**2), \
              (obj_dec/obj_dec_rms**2 + src_dec/src_dec_rms**2)/ \
                    (1/obj_dec_rms**2 + 1/src_dec_rms**2)]
    #miderr = [math.sqrt(1.0/(self.assumed_err[0]**(-2) + s.current_err[0]**(-2))),\
    #          math.sqrt(1.0/(self.assumed_err[0]**(-2) + s.current_err[0]**(-2)))]
    #print (midpt,self.pos,self.assumed_err,s.current_pos,s.current_err)
    #Pom   = -1.0* math.log(self.assumed_err[0]*self.assumed_err[1]*2.0*math.pi) - 0.5*(  ((self.pos[0] - midpt[0])/self.assumed_err[0])**2 + \
    #    ((self.pos[1] - midpt[1])/self.assumed_err[1])**2)
    #Psm   = -1.0* math.log(s.current_err[0]*s.current_err[1]*2.0*math.pi) - 0.5*(  ((s.current_pos[0] - midpt[0])/s.current_err[0])**2 + \
    #        ((s.current_pos[1] - midpt[1])/s.current_err[1])**2)
    #odds = -1.0 * (Poc + Psc - Pom - Psm)
    simple_odds = - 0.5*(  ((src_ra - midpt[0])/src_ra_rms)**2 + \
                           ((src_dec - midpt[1])/src_dec_rms)**2) \
                  - 0.5*(  ((obj_ra - midpt[0])/obj_ra_rms)**2 + \
                           ((obj_dec - midpt[1])/obj_dec_rms)**2)
    #-2*logpop = chi^2 = sigma^2 --> sqrt(10)
    num_obs_associated = n_sources
    sigma_n            = sqrt(2.0*log(num_obs_associated))
            
    return ((-2.0*simple_odds < sigma_n**2 + sigma_0**2), simple_odds, sigma_n)




class obs:
    
    def __init__(self,initial_pos,true_err=[[0.09,0.0],[0.0,0.09]],assumed_err=[0.3,0.3],t=None):
        self.initial_pos = initial_pos  # (true ra and dec)
        self.true_err = true_err
        self.assumed_err = assumed_err
        self.t = t
        self.associated_sources = []
        if self.t is None:
            ## assign a time
            self.t = time.time() - start_time ## this is in seconds
        self.pos = []
        
    def observe_pos(self):
        """
        """
        self.pos = random_array.multivariate_normal(self.initial_pos,self.true_err)
    
    def plot(self):
        scatter([self.pos[0]],[self.pos[1]],s=20)
        return

    def is_associated_with_source(self,slist,sigma_0=3.0):
        if type(slist) != type([]) or len(slist) == 0:
            return {'answer': False, 'sources': []}
        
        ## todo: put the logic here
        yes_source = []
        print(len(slist))
        source_odds = []
        for s in slist:
            (match_bool, simple_odds, sigma_n, midpt) = \
                    is_object_associated_with_source_algorithm_jbloom(\
                    len(s.associated_obs), \
                    self.pos[0], self.pos[1], self.assumed_err[0], self.assumed_err[1], \
                    s.current_pos[0], s.current_pos[1], s.current_err[0], \
                    s.current_err[1], sigma_0)

            if match_bool:
                print(("associated",sqrt(-2.0*simple_odds),sqrt(sigma_n**2 + sigma_0**2)))
                yes_source.append(s)
                source_odds.append(simple_odds)
                
                
            #print (simple_odds)

        if len(yes_source) == 0:
            print(("no association",self.pos))
            return {'answer': False, 'sources': []}
            
        else:
            mm= max(source_odds)
            ind = source_odds.index(mm)
            return {'answer': True, 'best_source': [yes_source[ind]], 'best_odds': mm, 'sources': yes_source, 'odds': source_odds}
            

    def is_associated_with_source_orig(self,slist,sigma_0=3.0):
        if type(slist) != type([]) or len(slist) == 0:
            return {'answer': False, 'sources': []}
        
        ## todo: put the logic here
        yes_source = []
        print(len(slist))
        source_odds = []
        for s in slist:
            # log (Po(center)*Ps(center)/Po(midpoint)Ps(midpoint))
            #Poc   = -1.0* math.log(self.assumed_err[0]*self.assumed_err[1]*2.0*math.pi)
            #Psc   = -1.0* math.log(s.current_err[0]*s.current_err[1]*2.0*math.pi)
            midpt  = [(self.pos[0]/self.assumed_err[0]**2 + s.current_pos[0]/s.current_err[0]**2)/(1/self.assumed_err[0]**2 + 1/s.current_err[0]**2),\
                (self.pos[1]/self.assumed_err[1]**2 + s.current_pos[1]/s.current_err[1]**2)/(1/self.assumed_err[1]**2 + 1/s.current_err[1]**2)]
            #miderr = [math.sqrt(1.0/(self.assumed_err[0]**(-2) + s.current_err[0]**(-2))),\
            #          math.sqrt(1.0/(self.assumed_err[0]**(-2) + s.current_err[0]**(-2)))]
            #print (midpt,self.pos,self.assumed_err,s.current_pos,s.current_err)
            #Pom   = -1.0* math.log(self.assumed_err[0]*self.assumed_err[1]*2.0*math.pi) - 0.5*(  ((self.pos[0] - midpt[0])/self.assumed_err[0])**2 + \
            #    ((self.pos[1] - midpt[1])/self.assumed_err[1])**2)
            #Psm   = -1.0* math.log(s.current_err[0]*s.current_err[1]*2.0*math.pi) - 0.5*(  ((s.current_pos[0] - midpt[0])/s.current_err[0])**2 + \
            #        ((s.current_pos[1] - midpt[1])/s.current_err[1])**2)
            #odds = -1.0 * (Poc + Psc - Pom - Psm)
            simple_odds = - 0.5*(  ((s.current_pos[0] - midpt[0])/s.current_err[0])**2 + \
                    ((s.current_pos[1] - midpt[1])/s.current_err[1])**2) - 0.5*(  ((self.pos[0] - midpt[0])/self.assumed_err[0])**2 + \
                        ((self.pos[1] - midpt[1])/self.assumed_err[1])**2)
            #-2*logpop = chi^2 = sigma^2 --> sqrt(10)
            num_obs_associated = len(s.associated_obs)
            sigma_n            = sqrt(2.0*log(num_obs_associated))
            
            if -2.0*simple_odds < sigma_n**2 + sigma_0**2:
                print(("associated",sqrt(-2.0*simple_odds),sqrt(sigma_n**2 + sigma_0**2)))
                yes_source.append(s)
                source_odds.append(simple_odds)
                
                
            #print (simple_odds)

        if len(yes_source) == 0:
            print(("no association",self.pos))
            return {'answer': False, 'sources': []}
            
        else:
            mm= max(source_odds)
            ind = source_odds.index(mm)
            return {'answer': True, 'best_source': [yes_source[ind]], 'best_odds': mm, 'sources': yes_source, 'odds': source_odds}


    def associate_with_source(self,slist):
        if type(slist) != type([]) or len(slist) == 0:
            return
        # todo: watch out for multiplicity
        self.associated_sources.extend(slist)
        
    def __str__(self):
        a = "  t=%f" % self.t
        a +=  "\tinitial  pos              = %s\n" % self.initial_pos
        a += "\tobserved pos              = %s\n" % self.pos
        a += "\ttrue_obsevational_err     = %s\n" % self.true_err
        return a
        
class source:
    
    def __init__(self,start_pos=[None,None],start_err=[None,None],current_pos=[None,None],current_err=[None,None],\
        associated_obs=[],stype="real"):
        """
        possible types: real and constructed
        """
        self.start_pos = start_pos
        self.start_err = start_err
        self.current_pos = current_pos
        self.current_err = current_err
        self.associated_obs = associated_obs
        self.stype = stype
        
    def add_associated_obs(self,o):
        # might want to deepcopy here
        self.associated_obs.append(copy.deepcopy(o))
    
    def plot(self,code='ys'):
        try:
            if self.stype=="real":
                scatter([self.start_pos[0]],[self.start_pos[1]],c=code[0],marker=code[1],s=60)
            else:
                scatter([self.current_pos[0]],[self.current_pos[1]],c=code[0],marker=code[1],s=60)
        except:
            pass
    
    def recalculate_position(self):
        """
        takes all the positions of the associated observation list and recalculated a position
        """
        global blah
        if self.stype=="real":
            print("! not supposed to do this with a real source..")
            return
        if len(self.associated_obs) == 0:
            return
        
        pos_array = numarray.fromlist([[x.pos[0],x.pos[1],x.assumed_err[0],x.assumed_err[1]] for x in self.associated_obs])
        raa    = numarray.fromlist([x[0] for x in pos_array])
        raerra = numarray.fromlist([x[2] for x in pos_array])
        deca    = numarray.fromlist([x[1] for x in pos_array])
        decerra = numarray.fromlist([x[3] for x in pos_array])
        
        ra  = numarray.sum(raa/raerra**2)/numarray.sum(1.0/raerra**2)
        dec =  numarray.sum(deca/decerra**2)/numarray.sum(1.0/decerra**2)
        raerr  = math.sqrt(1.0/numarray.sum(1.0/raerra**2))
        decerr =  math.sqrt(1.0/numarray.sum(1.0/decerra**2))
        self.current_pos = [ra,dec]
        self.current_err = [raerr,decerr]
        
    def __str__(self):
        a =  "===== source ====="
        a =  "type             = %s\n" % self.stype
        a += "start_pos        = %s\n" % self.start_pos
        a += "current_pos      = %s\n" % self.current_pos
        a += "associated sources (total number = %i):\n" % len(self.associated_obs)
        a += "-------------------\n"
        for o in self.associated_obs:
            v = o.__str__()
            a += v
        
        return a



class testreal:

    def __init__(self,fname="./obj_dict_309.pickle"):
        self.obj_dict = None
        self.load_data(fname=fname)
        self.constructed_source_list = []
        self.run()
        self.reg_plot_functions()
        
    def load_data(self,fname="./obj_dict_309.pickle"):
        import cPickle
        f = open(fname,"r")
        obj_dict = cPickle.load(f)
        f.close()
        print("there are %i observations loaded from the pickle file" % len(obj_dict))
        # dstarr adds this to convert the objects into the format expected by: is_object_associated_with_source_algorithm_jbloom()
        # # # # # # # #
        self.obj_dict = {}
        for obj_key,obj_elem in obj_dict.items():
            obj_ra = obj_dict[obj_key]['ra'] * 3600.0
            obj_dec = obj_dict[obj_key]['decl'] * 3600.0
            new_key = (obj_ra, obj_dec, obj_key[2], obj_key[3])
            self.obj_dict[new_key] = copy.deepcopy(obj_elem)
            self.obj_dict[new_key]['ra'] = obj_ra
            self.obj_dict[new_key]['decl'] = obj_dec


    def reg_plot_functions(self):
        self.cid1 = connect("key_press_event",self.plot_source_info)

    def plot_source_info(self,event):

        ra = event.xdata
        dec = event.ydata
        #print (event.key,ra,dec)
        if event.key == 's':
            #print self.constructed_pos[:,0]
            #print self.constructed_pos[:,1]
            dist = numarray.sqrt( (self.constructed_pos[:,0] - ra)**2 + (self.constructed_pos[:,1] - dec)**2)

            #print dist
            #print "min distance = %f " % min(dist)
            the_source_ind = numarray.compress(dist == min(dist), numarray.fromlist(range(len(self.constructed_source_list))))
            #print the_source_ind
            #the_source_ind = numarray.compress(dist == min(dist),numarray.arange(len(self.constructed_source_list)))
            the_source = self.constructed_source_list[the_source_ind[0]]
            print(the_source)
            #dist = numarray.sqrt( (the_source.current_pos[0] - self.real_pos[:,0])**2 + (the_source.current_pos[1] - self.real_pos[:,1])**2)
            #print "min distances to nearest real source = %f arcsec" % min(dist)
            #the_source_ind = numarray.compress(dist == min(dist), numarray.fromlist(range(len(self.real_list))))
            #the_source = self.real_list[the_source_ind[0]]
            #print "That real source is at ra=%f dec=%f" % (the_source.start_pos[0],the_source.start_pos[1])
        if event.key == 'r':
            dist = numarray.sqrt( (self.real_pos[:,0] - ra)**2 + (self.real_pos[:,1] - dec)**2)

            #print dist
            #print "min distance = %f " % min(dist)
            the_source_ind = numarray.compress(dist == min(dist), numarray.fromlist(range(len(self.real_list))))
            #print the_source_ind
            #the_source_ind = numarray.compress(dist == min(dist),numarray.arange(len(self.constructed_source_list)))
            the_source = self.real_list[the_source_ind[0]]
            print(the_source)


    def run(self,shuffle=True):
        constructed_source_list = []
        observation_list = []
        obslist = self.obj_dict.keys()
        if shuffle:
            random.seed()
            random.shuffle(obslist)
            random.shuffle(obslist)
            random.shuffle(obslist)
            print("shuffled")
        for theo in obslist:
            # choose a real source to draw an observation from
            o = obs(initial_pos=[theo[0],theo[1]],assumed_err=[theo[2],theo[3]])
            o.pos = [theo[0],theo[1]]
            o.plot()
            tmp = o.is_associated_with_source(constructed_source_list)
            # print tmp
            if tmp['answer'] == True:
                # o.associate_with_source(tmp['sources'])
                for s in tmp['best_source']:
                    # print (len(tmp['best_source']),o.pos,s.current_pos)
                    s.add_associated_obs(copy.deepcopy(o))
                    s.recalculate_position()
            else:
                ## make a new source
                s = source(start_pos=copy.copy(o.pos),stype='constructed',start_err=copy.copy(o.assumed_err),current_pos=copy.copy(o.pos),\
                    current_err=copy.copy(o.assumed_err),associated_obs=[copy.deepcopy(o)])
                print("1 new source")
                #print s
                #print s.associated_obs
                constructed_source_list.append(copy.deepcopy(s))

            observation_list.append(copy.deepcopy(o))
    
        for s in constructed_source_list:
            # print s
            s.plot('g^')

        self.constructed_source_list = constructed_source_list
        self.constructed_pos  = (numarray.fromlist([x.current_pos for x in self.constructed_source_list]))


class simulate:
    
    def __init__(self):

        self.constructed_source_list = []
        self.real_list = []
        self.run()
        self.reg_plot_functions()
    
    def reg_plot_functions(self):
        
        self.cid1 = connect("key_press_event",self.plot_source_info)
        
    def plot_source_info(self,event):
    
        ra = event.xdata
        dec = event.ydata
        #print (event.key,ra,dec)
        if event.key == 's':
            #print self.constructed_pos[:,0]
            #print self.constructed_pos[:,1]
            dist = numarray.sqrt( (self.constructed_pos[:,0] - ra)**2 + (self.constructed_pos[:,1] - dec)**2)
            
            #print dist
            #print "min distance = %f " % min(dist)
            the_source_ind = numarray.compress(dist == min(dist), numarray.fromlist(range(len(self.constructed_source_list))))
            #print the_source_ind
            #the_source_ind = numarray.compress(dist == min(dist),numarray.arange(len(self.constructed_source_list)))
            the_source = self.constructed_source_list[the_source_ind[0]]
            print(the_source)
            dist = numarray.sqrt( (the_source.current_pos[0] - self.real_pos[:,0])**2 + (the_source.current_pos[1] - self.real_pos[:,1])**2)
            print("min distances to nearest real source = %f arcsec" % min(dist))
            the_source_ind = numarray.compress(dist == min(dist), numarray.fromlist(range(len(self.real_list))))
            the_source = self.real_list[the_source_ind[0]]
            print("That real source is at ra=%f dec=%f" % (the_source.start_pos[0],the_source.start_pos[1]))
        if event.key == 'r':
            dist = numarray.sqrt( (self.real_pos[:,0] - ra)**2 + (self.real_pos[:,1] - dec)**2)
            
            #print dist
            #print "min distance = %f " % min(dist)
            the_source_ind = numarray.compress(dist == min(dist), numarray.fromlist(range(len(self.real_list))))
            #print the_source_ind
            #the_source_ind = numarray.compress(dist == min(dist),numarray.arange(len(self.constructed_source_list)))
            the_source = self.real_list[the_source_ind[0]]
            print(the_source)
            
            
    def run(self,n_sources = 3, n_observations = 21, ra_range = [-20.0,20.0],dec_range=[-20.0,20.0],typical_err=0.3,reuse=True):
    
        global real_list
 
        clf()
        # make the real sources
        if reuse:
            try:
                type(real_list) == type([])
            except NameError:
                reuse = False
                real_list = []

        for ns in range(n_sources):
            if not reuse:
                real_list.append(source(start_pos=[random_array.uniform(ra_range[0],ra_range[1]),random_array.uniform(dec_range[0],dec_range[1])],
                    stype='real',start_err=[0.0,0.0],associated_obs=[]))
                # print real_list[-1]
            real_list[ns].plot()
    
        
        constructed_source_list = []
        observation_list = []
    
        ## pick a vector of len n_obsevations sources to choose from from 0 --> n_source - 1
        s_start_ind = random_array.randint(0,n_sources,shape=[n_observations])
        for i in range(n_observations):
            # choose a real source to draw an observation from
            o = obs(initial_pos=real_list[s_start_ind[i]].start_pos,true_err=[[typical_err**2,0.0],[0.0,typical_err**2]],assumed_err=[1.1*typical_err,1.1*typical_err])
            o.observe_pos()
            o.plot()
            tmp = o.is_associated_with_source(constructed_source_list)
            # print tmp
            if tmp['answer'] == True:
                # o.associate_with_source(tmp['sources'])
                for s in tmp['best_source']:
                    # print (len(tmp['best_source']),o.pos,s.current_pos)
                    s.add_associated_obs(copy.deepcopy(o))
                    s.recalculate_position()
            else:
                ## make a new source
                s = source(start_pos=copy.copy(o.pos),stype='constructed',start_err=copy.copy(o.assumed_err),current_pos=copy.copy(o.pos),\
                    current_err=copy.copy(o.assumed_err),associated_obs=[copy.deepcopy(o)])
                print("new source")
                #print s
                #print s.associated_obs
                constructed_source_list.append(copy.deepcopy(s))

            observation_list.append(copy.deepcopy(o))
    
        for s in constructed_source_list:
            # print s
            s.plot('g^')
        
        ## do the comparisons between real and constructed sources
        for ns in range(n_sources):
            #real_list[ns].plot('ys')
            pass
        
        self.real_list = real_list
        self.constructed_source_list = constructed_source_list
        self.real_pos  = (numarray.fromlist([x.start_pos for x in self.real_list]))
        self.constructed_pos  = (numarray.fromlist([x.current_pos for x in self.constructed_source_list]))
        
        
        #del observation_list
    
if __name__ == '__main__':
    #s = simulate()
    tr = testreal(fname="/tmp/obj_dict.pickle_309.37471543_0.33168565")
# ipython --pylab cluster.py

#
# ipython --pylab
#import cluster
#a = cluster.testreal(fname="/tmp/obj_dict.pickle_309.37471543_0.33168565")
#s = cluster.simulate(n_sources = 4, n_observations = 27, ra_range = [180000.0,180040],dec_range=[162000,162040],typical_err=0.3)
