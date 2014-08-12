#!/usr/bin/env python
"""
Using JSB's fiteb.py, found at:
     wget http://commondatastorage.googleapis.com/bloom_code/jsb_eb_fit_v12may2011.tgz

This code fits eclipsing models in order to determine which type of eclipsing class a TUTOR source is.

"""

import sys, os
import MySQLdb
import glob
from numpy import loadtxt
import numpy
import matplotlib.pyplot as pyplot

sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/ingest_tools'))
from activelearn_utils import Database_Utils

sys.path.append(os.path.abspath(os.environ.get("HOME") + '/src/install/jsb_eb_fit'))
import fiteb

import pprint
import copy
import cPickle
import datetime
import time

class IPython_Task_Administrator:
    """ Send of Imputation tasks

    Adapted from activelearn_utils.py which was 
            adapted from generate_weka_classifiers.py:Parallel_Arff_Maker()

    """
    def __init__(self, pars={}):
        try:
            from IPython.kernel import client
        except:
            pass

        self.kernel_client = client

        self.pars = pars
        # TODO:             - initialize ipython modules
        self.mec = client.MultiEngineClient()
        #self.mec.reset(targets=self.mec.get_ids()) # Reset the namespaces of all engines
        self.tc = client.TaskClient()
	self.task_id_list = []

        #### 2011-01-21 added:
        self.mec.reset(targets=self.mec.get_ids())
        self.mec.clear_queue()
        self.mec.clear_pending_results()
        self.tc.task_controller.clear()


    def initialize_clients(self, mec_str):
        """ Instantiate ipython1 clients, import all module dependencies.
        """
	#task_str = """cat = os.getpid()"""
	#taskid = self.tc.run(client.StringTask(task_str, pull="cat"))
	#time.sleep(2)
	#print self.tc.get_task_result(taskid, block=False).results

        # 20090815(before): a = arffify.Maker(search=[], skip_class=False, local_xmls=True, convert_class_abrvs_to_names=False, flag_retrieve_class_abrvs_from_TUTOR=True, dorun=False)
        import time

        self.mec.execute(mec_str)
	time.sleep(2) # This may be needed.

	### testing:
	#task_str = """cat = os.getpid()"""
	#taskid = self.tc.run(client.StringTask(task_str, pull="cat"))
	#time.sleep(1)
	#print self.tc.get_task_result(taskid, block=False).results



class Run_FitEB_Parallel:
    """ Do the equivalent of run_fiteb_generate_html_pkl() in parallel.
    """

    def __init__(self):
        self.pars = {'tutor_hostname':'192.168.1.103',
                'tutor_username':'dstarr', #'tutor', # guest
                'tutor_password':'ilove2mass', #'iamaguest',
                'tutor_database':'tutor',
                'tutor_port':3306, #33306,
                'tcp_hostname':'192.168.1.25',
                'tcp_username':'pteluser',
                'tcp_port':     3306, #23306, 
                'tcp_database':'source_test_db',
                'pkl_fpath':os.path.abspath(os.environ.get("HOME") + '/scratch/evaluate_eclipsing_classifs_using_fiteb__dict.pkl'),
                'fiteb_class_lookup':{'contact':'y. W Ursae Maj.',
                                      'detached':'w. Beta Persei',
                                      'semi-detached':'x. Beta Lyrae'},
                'analysis_params':['chisq', 'i_err', 'q_err', 'l1/l2_err', 'l1/l2', 'q', 'r1', 'r2', 'reflect1'],
                'al_dirpath':os.path.abspath(os.environ.get("TCP_DIR") + 'Data/allstars'),
                'al_glob_str':'AL_*_*.dat',
                'classids_of_interest':[251,#'x. Beta Lyrae',
                                        253,#'w. Beta Persei',
                                        252,#'y. W Ursae Maj.',
                                        ],
                'fittype':4,
                'skip_list':[234996, 164830, 164872, 239309, 216110, 225745],
                }


    def client_setup(self, class_id_name={}):
        """ Routines for setting up params, database connections for ipython client
        """

        #orig_cwd = os.getcwd()
        os.chdir(os.path.abspath(os.environ.get("HOME") + '/src/install/jsb_eb_fit'))

        if len(class_id_name) == 0:
            self.DatabaseUtils = Database_Utils(pars=self.pars)
            rclass_tutorid_lookup = self.DatabaseUtils.retrieve_tutor_class_ids()
            self.class_id_name = dict([[v,k] for k,v in rclass_tutorid_lookup.items()])
        else:
            self.class_id_name = class_id_name


    def client_task(self):
        """ Computation task which is to be run on Ipython engines.
        """
        pass


    def add_task(self, srcid=None, period=None, fittype=None, filename=None, classid=None):
        """
        """
        tc_exec_str = """
try:
    (alt_rez, rez) = fiteb.period_select(idd=int(srcid),
                             per=period,
                             plot=False,
                             use_xml=True,
                             try_alt=True,
                             dosave=False,
                             show=False,
                             fittype=fittype)
    out_dict = {'alt_rez':alt_rez,
                'rez':rez,
                'srcid':srcid,
                'traceback':"",
                'filename':filename,
                'classid':classid}
except:
    out_dict = {'traceback':traceback.format_exc(),
                'srcid':srcid}
                         """
        tc_exec_str__test = """
out_dict = {'alt_rez':fiteb.__author__}
                         """
        task_id = self.ipy_tasks.tc.run(self.ipy_tasks.kernel_client.StringTask(tc_exec_str,
                                               push={'srcid':srcid,
                                                     'period':period,
                                                     'fittype':fittype,
                                                     'filename':filename,
                                                     'classid':classid,
                                                     },
                                      pull='out_dict', 
                                      retries=3))
        #print self.ipy_tasks.tc.get_task_result(task_id, block=False)
        #import pdb; pdb.set_trace()
        #print
        self.ipy_tasks.task_id_list.append(task_id)



    def ipython_master(self):
        """
        """
        self.ipy_tasks = IPython_Task_Administrator()
        self.client_setup() # Needed here to make database connections

        mec_str = """
import sys, os
import MySQLdb
import glob
from numpy import loadtxt
import numpy
import matplotlib.pyplot as pyplot

sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/ingest_tools'))
from activelearn_utils import Database_Utils

sys.path.append(os.path.abspath(os.environ.get("HOME") + '/src/install/jsb_eb_fit'))
import fiteb

import pprint
import copy
import cPickle
import traceback

sys.path.append(os.environ.get('TCP_DIR') + '/Algorithms')
import evaluate_eclipsing_classifs_using_fiteb
RunFitEBParallel = evaluate_eclipsing_classifs_using_fiteb.Run_FitEB_Parallel()
RunFitEBParallel.client_setup(class_id_name=%s)
""" % (str(self.class_id_name))
        self.ipy_tasks.initialize_clients(mec_str=mec_str)

        fpaths = glob.glob("%s/%s" % (self.pars['al_dirpath'], self.pars['al_glob_str']))

        pickle_dict = {}

        fp = open(os.path.abspath(os.environ.get("HOME") + '/scratch/evaluate_eclipsing_classifs.html'),'w')
        fp.write("""<html><body><table border="1">
        <tr><td><b>source_id</b></td><td><b>plot</b></td><td><b>file</b></td><td><b>TUTOR class</b></td><td><b>fitEB class</b></td><td><b>okfit</b></td><td><b>chi2</b></td><td><b>eccentricity</b></td><td><b>inclination (deg)</b></td><td><b>mass ratio</b></td><td><b>lum ratio</b></td><td><b>reflect 1</b></td><td><b>reflect 2</b></td></tr>
        """)

        ########### AL*dat sources:
        if 1:
            for fpath in fpaths:
                tup_list = loadtxt(fpath,
                                   dtype={'names': ('src_id', 'class_id'),
                                          'formats': ('i4', 'i4')},
                                   usecols=(0,1),
                                   unpack=False)
                srcid_list = tup_list['src_id']
                classid_list = tup_list['class_id']
                for i, classid in enumerate(classid_list):            
                    ### NOTE: i corresponds to classid and srcid_list[i]
                    if classid not in self.pars['classids_of_interest']:
                        continue
                    srcid = srcid_list[i]
                    if int(srcid) in self.pars['skip_list']:
                        continue
                    print "srcid:", srcid
                    select_str = "SELECT feat_val FROM source_test_db.feat_values JOIN feat_lookup USING (feat_id) WHERE filter_id=8 AND feat_name='freq1_harmonics_freq_0' AND src_id=%d" % (srcid + 100000000)
                    self.DatabaseUtils.tcp_cursor.execute(select_str)
                    results = self.DatabaseUtils.tcp_cursor.fetchall()
                    if len(results) == 0:
                        raise "Error"
                    period = 1. / results[0][0]

                    if 0:
                        ### For single-thread testing only:
                        RunFitEBParallel = Run_FitEB_Parallel()
                        RunFitEBParallel.client_setup()
                        (alt_rez, rez) = fiteb.period_select(idd=int(srcid),
                                                             per=period,
                                                             plot=True,
                                                             use_xml=True,
                                                             try_alt=True,
                                                             dosave=True,
                                                             show=False,
                                                             fittype=self.pars['fittype']) #) #True,#verbose=False)
                        import pdb; pdb.set_trace()
                        print

                    self.add_task(srcid=srcid,
                                  period=period,
                                  fittype=self.pars['fittype'],
                                  filename=fpath[fpath.rfind('/')+1:],
                                  classid=classid)

        ######### Debosscher sources using TUTOR database query:
        select_str = "select source_id, class_id from sources where project_id = 123"
        self.DatabaseUtils.tutor_cursor.execute(select_str)
        results = self.DatabaseUtils.tutor_cursor.fetchall()
        if len(results) == 0:
            raise "Error"
        for row in results:
            (srcid, classid) = row
            if classid in self.pars['classids_of_interest']:
                    if int(srcid) in self.pars['skip_list']:
                        continue
                    print "22222222", srcid

                    select_str = "SELECT feat_val FROM source_test_db.feat_values JOIN feat_lookup USING (feat_id) WHERE filter_id=8 AND feat_name='freq1_harmonics_freq_0' AND src_id=%d" % (srcid + 100000000)
                    self.DatabaseUtils.tcp_cursor.execute(select_str)
                    results = self.DatabaseUtils.tcp_cursor.fetchall()
                    if len(results) == 0:
                        raise "Error"
                    period = 1. / results[0][0]

                    self.add_task(srcid=srcid,
                                  period=period,
                                  fittype=self.pars['fittype'],
                                  filename="Debosscher",
                                  classid=classid)

        #########
        #import pdb; pdb.set_trace()
        #print

        task_id_list = self.ipy_tasks.task_id_list
        tc = self.ipy_tasks.tc
        
        dtime_pending_1 = None
        while ((tc.queue_status()['scheduled'] > 0) or
               (tc.queue_status()['pending'] > 0)):
            tasks_to_pop = []
            for task_id in self.ipy_tasks.task_id_list:
                temp = self.ipy_tasks.tc.get_task_result(task_id, block=False)
                if temp == None:
                    continue
                temp2 = temp.results
                if temp2 == None:
                    continue
                results = temp['out_dict']
                if len(results.get('traceback',"")) > 0:
                    print "Task Traceback:", results.get('srcid',""), results.get('traceback',"")
                    continue
                tasks_to_pop.append(task_id)
                srcid = results['srcid']
                rez = results['rez']
                alt_rez = results['alt_rez']
                filename = results['filename']
                classid = results['classid']
                fp.write('<tr><td><A href="http://lyra.berkeley.edu/allstars/?mode=inspect&srcid=%d">%d</A></td><td><A href="http://lyra.berkeley.edu/~pteluser/fiteb_plots/plot%d.png" target="_blank">plot</A></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%4.2f</td><td>%4.4f</td><td>%4.2f +- %4.2f</td><td>%4.2f +- %4.2f</td><td>%4.2f +- %4.2f</td><td>%s</td><td>%s</td></tr>\n' % \
                         (srcid, srcid, srcid, filename, self.class_id_name[classid], pars['fiteb_class_lookup'].get(rez.get('class',None),'unknown'), str(rez.get('okfit',False)),
                          rez.get('chisq',False) if rez.get('chisq',99999) is not None else 99999,
                          rez.get('e',False),
                          rez.get('i',99999),
                          rez.get('i_err',99999) if rez.get('i_err',99999) is not None else 99999,
                          rez.get('q',99999),
                          rez.get('q_err',99999) if rez.get('q_err',99999) is not None else 99999,
                          rez.get('l1/l2',99999),
                          rez.get('l1/l2_err',99999) if rez.get('l1/l2_err',99999) is not None else 99999,
                          str(rez.get('reflect1',99999) if rez.get('reflect1',99999) is not None else 99999),
                          str(rez.get('reflect2',99999) if rez.get('reflect2',99999) is not None else 99999),
                          ))
                fp.flush()
                pickle_dict[srcid] = rez
                pickle_dict[srcid].update({'file':filename,
                                           'tutor_class':self.class_id_name[classid],
                                           'fiteb_class':pars['fiteb_class_lookup'].get(rez.get('class',None),'unknown'),
                                           'okfit':rez.get('okfit',False),
                                           'chisq':rez.get('chisq',False),
                                           'chisq_percentiles':alt_rez.get('chisq_percentiles',{}),
                                           'e_percentiles':alt_rez.get('e_percentiles',{}),
                                           'i_err_percentiles':alt_rez.get('i_err_percentiles',{}),
                                           'l1/l2_err_percentiles':alt_rez.get('l1/l2_err_percentiles',{}),
                                           'l1/l2_percentiles':alt_rez.get('l1/l2_percentiles',{}),
                                           'l1_percentiles':alt_rez.get('l1_percentiles',{}),
                                           'l2_percentiles':alt_rez.get('l2_percentiles',{}),
                                           'omega_deg_percentiles':alt_rez.get('omega_deg_percentiles',{}),
                                           'primary_eclipse_phase_percentiles':alt_rez.get('primary_eclipse_phase_percentiles',{}),
                                           'period_percentiles':alt_rez.get('period_percentiles',{}),
                                           'ratiopass_for_percentile':alt_rez.get('ratiopass_for_percentile',{}),
                                           'vals_for_percentile':alt_rez.get('vals_for_percentile',{}),
                                           'nmodels':alt_rez.get('nmodels',{}),
                                           'q_err_percentiles':alt_rez.get('q_err_percentiles',{}),
                                           'q_percentiles':alt_rez.get('q_percentiles',{}),
                                           'r1_percentiles':alt_rez.get('r1_percentiles',{}),
                                           'r2_percentiles':alt_rez.get('r2_percentiles',{}),
                                           'reflect1_percentiles':alt_rez.get('reflect1_percentiles',{}),
                                           'reflect2_percentiles':alt_rez.get('reflect2_percentiles',{}),
                                           'e':rez.get('e',False),
                                           'i':rez.get('i',99999),
                                           'i_err':rez.get('i_err',99999),
                                           'q':rez.get('q',99999),
                                           'q_err':rez.get('q_err',99999) if rez.get('q_err',99999) is not None else 99999,
                                           'l1/l2':rez.get('l1/l2',99999),
                                           'l1/l2_err':rez.get('l1/l2_err',99999) if rez.get('l1/l2_err',99999) is not None else 99999,
                                           'reflect1':rez.get('reflect1',99999) if rez.get('reflect1',99999) is not None else 99999,
                                           'reflect2':rez.get('reflect2',99999) if rez.get('reflect2',99999) is not None else 99999,
                                           })
                #import pdb; pdb.set_trace()
                #print   
            for task_id in tasks_to_pop:
                task_id_list.remove(task_id)
                # # #
            if ((tc.queue_status()['scheduled'] == 0) and 
                (tc.queue_status()['pending'] <= 2)):
               if dtime_pending_1 == None:
                   dtime_pending_1 = datetime.datetime.now()
               else:
                   now = datetime.datetime.now()
                   if ((now - dtime_pending_1) >= datetime.timedelta(seconds=300)):
                       print "dtime_pending=1 timeout break!"
                       break
            print tc.queue_status()
            print 'Sleep... 20', datetime.datetime.utcnow()
            time.sleep(20)
        print '> > > > tc.queue_status():', tc.queue_status()

        ### IN CASE THERE are still tasks which have not been pulled/retrieved:
        for task_id in self.ipy_tasks.task_id_list:
            temp = self.ipy_tasks.tc.get_task_result(task_id, block=False)
            if temp == None:
                continue
            temp2 = temp.results
            if temp2 == None:
                continue
            results = temp['out_dict']
            if len(results.get('traceback',"")) > 0:
                print "Task Traceback:", results.get('srcid',""), results.get('traceback',"")
                continue
            tasks_to_pop.append(task_id)
            srcid = results['srcid']
            rez = results['rez']
            alt_rez = results['alt_rez']
            filename = results['filename']
            classid = results['classid']
            fp.write('<tr><td><A href="http://lyra.berkeley.edu/allstars/?mode=inspect&srcid=%d">%d</A></td><td><A href="http://lyra.berkeley.edu/~pteluser/fiteb_plots/plot%d.png" target="_blank">plot</A></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%4.2f</td><td>%4.4f</td><td>%4.2f +- %4.2f</td><td>%4.2f +- %4.2f</td><td>%4.2f +- %4.2f</td><td>%s</td><td>%s</td></tr>\n' % \
                     (srcid, srcid, srcid, filename, self.class_id_name[classid], pars['fiteb_class_lookup'].get(rez.get('class',None),'unknown'), str(rez.get('okfit',False)),
                      rez.get('chisq',False) if rez.get('chisq',99999) is not None else 99999,
                      rez.get('e',False),
                      rez.get('i',99999),
                      rez.get('i_err',99999) if rez.get('i_err',99999) is not None else 99999,
                      rez.get('q',99999),
                      rez.get('q_err',99999) if rez.get('q_err',99999) is not None else 99999,
                      rez.get('l1/l2',99999),
                      rez.get('l1/l2_err',99999) if rez.get('l1/l2_err',99999) is not None else 99999,
                      str(rez.get('reflect1',99999) if rez.get('reflect1',99999) is not None else 99999),
                      str(rez.get('reflect2',99999) if rez.get('reflect2',99999) is not None else 99999),
                      ))
            fp.flush()
            pickle_dict[srcid] = rez
            pickle_dict[srcid].update({'file':filename,
                                       'tutor_class':self.class_id_name[classid],
                                       'fiteb_class':pars['fiteb_class_lookup'].get(rez.get('class',None),'unknown'),
                                       'okfit':rez.get('okfit',False),
                                       'chisq':rez.get('chisq',False),
                                       'chisq_percentiles':alt_rez.get('chisq_percentiles',{}),
                                       'e_percentiles':alt_rez.get('e_percentiles',{}),
                                       'i_err_percentiles':alt_rez.get('i_err_percentiles',{}),
                                       'l1/l2_err_percentiles':alt_rez.get('l1/l2_err_percentiles',{}),
                                       'l1/l2_percentiles':alt_rez.get('l1/l2_percentiles',{}),
                                       'l1_percentiles':alt_rez.get('l1_percentiles',{}),
                                       'l2_percentiles':alt_rez.get('l2_percentiles',{}),
                                       'omega_deg_percentiles':alt_rez.get('omega_deg_percentiles',{}),
                                       'primary_eclipse_phase_percentiles':alt_rez.get('primary_eclipse_phase_percentiles',{}),
                                       'period_percentiles':alt_rez.get('period_percentiles',{}),
                                       'ratiopass_for_percentile':alt_rez.get('ratiopass_for_percentile',{}),
                                       'vals_for_percentile':alt_rez.get('vals_for_percentile',{}),
                                       'nmodels':alt_rez.get('nmodels',{}),
                                       'q_err_percentiles':alt_rez.get('q_err_percentiles',{}),
                                       'q_percentiles':alt_rez.get('q_percentiles',{}),
                                       'r1_percentiles':alt_rez.get('r1_percentiles',{}),
                                       'r2_percentiles':alt_rez.get('r2_percentiles',{}),
                                       'reflect1_percentiles':alt_rez.get('reflect1_percentiles',{}),
                                       'reflect2_percentiles':alt_rez.get('reflect2_percentiles',{}),
                                       'e':rez.get('e',False),
                                       'i':rez.get('i',99999),
                                       'i_err':rez.get('i_err',99999),
                                       'q':rez.get('q',99999),
                                       'q_err':rez.get('q_err',99999) if rez.get('q_err',99999) is not None else 99999,
                                       'l1/l2':rez.get('l1/l2',99999),
                                       'l1/l2_err':rez.get('l1/l2_err',99999) if rez.get('l1/l2_err',99999) is not None else 99999,
                                       'reflect1':rez.get('reflect1',99999) if rez.get('reflect1',99999) is not None else 99999,
                                       'reflect2':rez.get('reflect2',99999) if rez.get('reflect2',99999) is not None else 99999,
                                       })

        

        fp.write("""</table></body></html>
        """)
        fp.close()

        fp_pickle = open(pars['pkl_fpath'], 'wb')
        cPickle.dump(pickle_dict, fp_pickle, 1)
        fp_pickle.close()
        
        import pdb; pdb.set_trace()
        print   






def run_fiteb_generate_html_pkl(pars={}):
    """ Run fiteb.py on all ASAS AL / Debosscher sources.
    Generate .png plots, .html summary, and dictionary .pkl
    """
    pars = copy.copy(pars)
    pars.update({ \
        'al_dirpath':os.path.abspath(os.environ.get("TCP_DIR") + 'Data/allstars'),
        'al_glob_str':'AL_*_*.dat',
        'classids_of_interest':[251,#'x. Beta Lyrae',
                                253,#'w. Beta Persei',
                                252,#'y. W Ursae Maj.',
                                ],
        'fittype':3,
        'skip_list':[234996, 164830, 164872, 239309, 216110, 225745],
        })

    #period_select(args.did[0],args.per[0],plot=args.plot,use_xml=True,try_alt=args.alt,dosave=args.savefig,show=args.showfig)
    orig_cwd = os.getcwd()
    os.chdir(os.path.abspath(os.environ.get("HOME") + '/src/install/jsb_eb_fit'))

    DatabaseUtils = Database_Utils(pars=pars)
    rclass_tutorid_lookup = DatabaseUtils.retrieve_tutor_class_ids()
    class_id_name = dict([[v,k] for k,v in rclass_tutorid_lookup.items()])

    fpaths = glob.glob("%s/%s" % (pars['al_dirpath'], pars['al_glob_str']))

    pickle_dict = {}

    fp = open(os.path.abspath(os.environ.get("HOME") + '/scratch/evaluate_eclipsing_classifs.html'),'w')
    fp.write("""<html><body><table border="1">
    <tr><td><b>source_id</b></td><td><b>plot</b></td><td><b>file</b></td><td><b>TUTOR class</b></td><td><b>fitEB class</b></td><td><b>okfit</b></td><td><b>chi2</b></td><td><b>eccentricity</b></td><td><b>inclination (deg)</b></td><td><b>mass ratio</b></td><td><b>lum ratio</b></td><td><b>reflect 1</b></td><td><b>reflect 2</b></td></tr>
    """)
    if 1:
        for fpath in fpaths:
            tup_list = loadtxt(fpath,
                               dtype={'names': ('src_id', 'class_id'),
                                      'formats': ('i4', 'i4')},
                               usecols=(0,1),
                               unpack=False)
            srcid_list = tup_list['src_id']
            classid_list = tup_list['class_id']
            for i, classid in enumerate(classid_list):            
                if int(srcid_list[i]) != 164594:
                    continue
                if classid in pars['classids_of_interest']:
                    srcid = srcid_list[i]
                    if int(srcid) in pars['skip_list']:
                        continue
                    print "11111111", srcid
                    select_str = "SELECT feat_val FROM source_test_db.feat_values JOIN feat_lookup USING (feat_id) WHERE filter_id=8 AND feat_name='freq1_harmonics_freq_0' AND src_id=%d" % (srcid + 100000000)
                    DatabaseUtils.tcp_cursor.execute(select_str)
                    results = DatabaseUtils.tcp_cursor.fetchall()
                    if len(results) == 0:
                        raise "Error"
                    period = 1. / results[0][0]

                    #try:
                    if 1:
                        (alt_rez, rez) = fiteb.period_select(idd=int(srcid),
                                                     per=period,
                                                     plot=True,
                                                     use_xml=True,
                                                     try_alt=True,
                                                     dosave=True,
                                                     show=False,
                                                     fittype=pars['fittype']) #True,#verbose=False)
                    #except:
                    #    print srcid, period
                    #    import pdb; pdb.set_trace()
                    #    print
                    #    continue

                    #pprint.pprint(rez)
                    fp.write('<tr><td><A href="http://lyra.berkeley.edu/allstars/?mode=inspect&srcid=%d">%d</A></td><td><A href="http://lyra.berkeley.edu/~pteluser/fiteb_plots/plot%d.png" target="_blank">plot</A></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%4.2f</td><td>%4.4f</td><td>%4.2f +- %4.2f</td><td>%4.2f +- %4.2f</td><td>%4.2f +- %4.2f</td><td>%s</td><td>%s</td></tr>\n' % \
                             (srcid, srcid, srcid, fpath[fpath.rfind('/')+1:], class_id_name[classid], pars['fiteb_class_lookup'].get(rez.get('class',None),'unknown'), str(rez.get('okfit',False)),
                              rez.get('chisq',False),
                              rez.get('e',False),
                              rez.get('i',99999),
                              rez.get('i_err',99999) if rez.get('i_err',99999) is not None else 99999,
                              rez.get('q',99999),
                              rez.get('q_err',99999) if rez.get('q_err',99999) is not None else 99999,
                              rez.get('l1/l2',99999),
                              rez.get('l1/l2_err',99999) if rez.get('l1/l2_err',99999) is not None else 99999,
                              str(rez.get('reflect1',99999) if rez.get('reflect1',99999) is not None else 99999),
                              str(rez.get('reflect2',99999) if rez.get('reflect2',99999) is not None else 99999),
                              ))
                    fp.flush()
                    pickle_dict[srcid] = rez
                    pickle_dict[srcid].update({'file':fpath[fpath.rfind('/')+1:],
                                               'tutor_class':class_id_name[classid],
                                               'fiteb_class':pars['fiteb_class_lookup'].get(rez.get('class',None),'unknown'),
                                               'okfit':rez.get('okfit',False),
                                               'chisq':rez.get('chisq',False),
                                               'e':rez.get('e',False),
                                               'i':rez.get('i',99999),
                                               'i_err':rez.get('i_err',99999),
                                               'q':rez.get('q',99999),
                                               'q_err':rez.get('q_err',99999) if rez.get('q_err',99999) is not None else 99999,
                                               'l1/l2':rez.get('l1/l2',99999),
                                               'l1/l2_err':rez.get('l1/l2_err',99999) if rez.get('l1/l2_err',99999) is not None else 99999,
                                               'reflect1':rez.get('reflect1',99999) if rez.get('reflect1',99999) is not None else 99999,
                                               'reflect2':rez.get('reflect2',99999) if rez.get('reflect2',99999) is not None else 99999,
                                               })
                    #import pdb; pdb.set_trace()
                    #print   

    select_str = "select source_id, class_id from sources where project_id = 123"
    DatabaseUtils.tutor_cursor.execute(select_str)
    results = DatabaseUtils.tutor_cursor.fetchall()
    if len(results) == 0:
        raise "Error"
    for row in results:
        (srcid, classid) = row
        if classid in pars['classids_of_interest']:
                if int(srcid) in pars['skip_list']:
                    continue
                if int(srcid) != 164594:
                    continue
                print "22222222", srcid

                select_str = "SELECT feat_val FROM source_test_db.feat_values JOIN feat_lookup USING (feat_id) WHERE filter_id=8 AND feat_name='freq1_harmonics_freq_0' AND src_id=%d" % (srcid + 100000000)
                DatabaseUtils.tcp_cursor.execute(select_str)
                results = DatabaseUtils.tcp_cursor.fetchall()
                if len(results) == 0:
                    raise "Error"
                period = 1. / results[0][0]

                (alt_rez, rez) = fiteb.period_select(idd=int(srcid),
                                                 per=period,
                                                 plot=True,
                                                 use_xml=True,
                                                 try_alt=True,
                                                 dosave=True,
                                                 show=False,
                                                 fittype=pars['fittype'])#, #True,verbose=False)

                #pprint.pprint(rez)
                fp.write('<tr><td><A href="http://lyra.berkeley.edu/allstars/?mode=inspect&srcid=%d">%d</A></td><td><A href="http://lyra.berkeley.edu/~pteluser/fiteb_plots/plot%d.png" target="_blank">plot</A></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%4.2f</td><td>%4.4f</td><td>%4.2f +- %4.2f</td><td>%4.2f +- %4.2f</td><td>%4.2f +- %4.2f</td><td>%s</td><td>%s</td></tr>\n' % \
                         (srcid, srcid, srcid, "Debosscher", class_id_name[classid], pars['fiteb_class_lookup'].get(rez.get('class',None),'unknown'), str(rez.get('okfit',False)),
                              rez.get('chisq',False),
                              rez.get('e',False),
                              rez.get('i',0),
                              rez.get('i_err',99999) if rez.get('i_err',99999) is not None else 99999,
                              rez.get('q',0),
                              rez.get('q_err',0) if rez.get('q_err',0) is not None else 99999,
                              rez.get('l1/l2',0),
                              rez.get('l1/l2_err',0) if rez.get('l1/l2_err',0) is not None else 99999,
                              str(rez.get('reflect1',99999) if rez.get('reflect1',99999) is not None else 99999),
                              str(rez.get('reflect2',99999) if rez.get('reflect2',99999) is not None else 99999),
                              ))
                          
                fp.flush()
                pickle_dict[srcid] = rez
                pickle_dict[srcid].update({'file':"Debosscher",
                                           'tutor_class':class_id_name[classid],
                                           'fiteb_class':pars['fiteb_class_lookup'].get(rez.get('class',None),'unknown'),
                                           'okfit':rez.get('okfit',False),
                                           'chisq':rez.get('chisq',False),
                                           'e':rez.get('e',False),
                                           'i':rez.get('i',99999),
                                           'i_err':rez.get('i_err',99999),
                                           'q':rez.get('q',99999),
                                           'q_err':rez.get('q_err',99999) if rez.get('q_err',99999) is not None else 99999,
                                           'l1/l2':rez.get('l1/l2',99999),
                                           'l1/l2_err':rez.get('l1/l2_err',99999) if rez.get('l1/l2_err',99999) is not None else 99999,
                                           'reflect1':rez.get('reflect1',99999) if rez.get('reflect1',99999) is not None else 99999,
                                           'reflect2':rez.get('reflect2',99999) if rez.get('reflect2',99999) is not None else 99999,
                                           })
                #break

    fp.write("""</table></body></html>
    """)
    fp.close()

    fp_pickle = open(pars['pkl_fpath'], 'wb')
    cPickle.dump(pickle_dict, fp_pickle, 1)
    fp_pickle.close()



class FitEB_Param_Analysis(Database_Utils):
    """
    """
    def __init__(self, pars={}):
        self.pars = pars
        self.pars['fiteb_class_lookup_rev'] = {}
        for k, v in self.pars['fiteb_class_lookup'].iteritems():
            self.pars['fiteb_class_lookup_rev'][v] = k
        self.connect_to_db()


    def reduce_arff_attrib_list_using_SVMranker(self, arff_attrib_list_orig):
        """ Parse the WEKA results file returned from the attribute-select SVM-ranker.
        Return; a reduced  arff_attrib_list

* want to parse SVM_ranker file and construct ordered lists for each attribute
      - storing merit, rank : 
** This code runs at: 
** then store attribs in final allowed list which:
   - have a merit above a certain value
   - OR, that attribute has not been stored yet.
        - initially allowing 4/7 percentiles for each attribute to pass
        - then iterateing and weeding down again and maybe allowing
          2/7 or 1/7 attribs

average merit      average rank  attribute
672 +- 0             1   +- 0         658 detached_e_npass_50
669.3 +- 1.418         3.7 +- 1.42      616 detached_l2_npass_50

        """
        attrib_added_dict = {}
        arff_attrib_list_out = []
        in_header = True
        for line in open(self.pars['SVMrank_results_input_fpath']).readlines():
            if len(line) <= 1:
                continue
            if "average merit" in line:
                in_header = False
                continue # skip this line
            if in_header:
               continue
            line_rep = line.replace("+-", "")
            elems = line_rep.split()
            merit = float(elems[0])
            rank = float(elems[2])
            attrib = elems[5]
            i_split = attrib.rfind("_")
            attrib_root = attrib[:i_split]
            if merit < self.pars['SVMrank_allow_cut']:
                #import pdb; pdb.set_trace()
                #print   
                pass # we do not use this percentile attribute
            elif not attrib_added_dict.has_key(attrib_root):
                attrib_added_dict[attrib_root] = [attrib]
                arff_attrib_list_out.append(attrib)
            elif len(attrib_added_dict[attrib_root]) < self.pars['n_attrib_percentiles_cut']:
                attrib_added_dict[attrib_root].append(attrib)
                arff_attrib_list_out.append(attrib)
            else:
                pass
        arff_attrib_list_out.sort()
        return arff_attrib_list_out

        
    def parse_trainset_srcid_list(self):
        """ Parse a list file of srcids, classified as one of 3 eclipsing classes.
        These are to be used as the training set for the WEKA classifier, and are
        added to the .arff file in main().
        """
        srcid_class_dict = {}
        lines = open(self.pars['trainset_srcid_list_fpath']).readlines()
        for line in lines:
            if len(line) <= 1:
                continue
            elems = line.split()
            class_name = self.pars['class_short_lookup'][elems[0]]
            srcid = int(elems[1])
            srcid_class_dict[srcid] = class_name

        return srcid_class_dict



    def main(self, use_trainset_srcid_list=True):
        """
        ** Need to generate these plots for:
            - different matched classes: EA, EB, EW
            - different surveys:  Debosscher, ASAS
            - different parameters : chi2, incl_
        ** so we need to plot a historgram for:
            - sources we agree on (with some tightness cuts)
            - all other sources

        Reference existing liklihood code:
           - tutor_database_project_insert.py:plot_aperture_mag_relation()
           - get_colors_for_tutor_sources.py:determine_color_param_likelyhoods()

        """
        if use_trainset_srcid_list:
            trainset_srcid_class_dict = self.parse_trainset_srcid_list()

        fp_pickle = open(self.pars['pkl_fpath'])
        data_dict = cPickle.load(fp_pickle)
        fp_pickle.close()

        fp_html = open(os.path.abspath(os.environ.get("HOME") + '/scratch/evaluate_eclipsing_classifs.html'),'w')
        fp_html.write("""<html><body><table border="1">
        <tr><td><b>source_id</b></td><td><b>plot</b></td><td><b>file</b></td><td><b>TUTOR class</b></td><td><b>fitEB class</b></td><td><b>okfit</b></td><td><b>chi2</b></td><td><b>eccentricity</b></td><td><b>inclination (deg)</b></td><td><b>mass ratio</b></td><td><b>lum ratio</b></td><td><b>reflect 1</b></td><td><b>reflect 2</b></td></tr>
        """)

        attribs_for_percentiles = ['chisq', 'i_err', 'q_err', 'l1/l2_err', 'l1/l2', 'q', 'r1', 'r2', 'reflect1', 'reflect2', 'primary_eclipse_phase', 'period', 'omega_deg', 'l1', 'l2', 'e'] # 'primary_eclipse_phase', 'period', 'omega_deg', 'l1', 'l2', 'e']
        arff_attrib_list_orig = copy.copy(self.pars['analysis_params'])
        for a_name in attribs_for_percentiles:
            for c_name in self.pars['fiteb_class_lookup'].keys():
                for temp_type in ['perc', 'npass']:
                    for perc in [5, 10, 15, 20, 30, 40, 50, 60, 70, 80, 90]:
                        temp_param_name = "%s_%s_%s_%d" % (c_name, a_name, temp_type, perc)
                        if temp_param_name in self.pars['percentile_attrib_skip_list']:
                            continue
                        arff_attrib_list_orig.append(temp_param_name)
        for a_name in attribs_for_percentiles:
            for perc in [5, 10, 15, 20, 30, 40, 50, 60, 70, 80, 90]:
                temp_param_name = "perc_val_%s_%d" % (a_name, perc)
                arff_attrib_list_orig.append(temp_param_name)
        for a_name in attribs_for_percentiles:
            for perc in [5, 10, 15, 20, 30, 40, 50, 60, 70, 80, 90]:
                temp_param_name = "perc_pass_%s_%d" % (a_name, perc)
                arff_attrib_list_orig.append(temp_param_name)



        arff_attrib_list = self.reduce_arff_attrib_list_using_SVMranker(arff_attrib_list_orig)
        ###DO THIS ONLY ON FIRST ITERATION, prior to running SVM Ranker:
        #arff_attrib_list = arff_attrib_list_orig

        fp_arff = open(os.path.abspath(os.environ.get("HOME") + '/scratch/evaluate_eclipsing_classifs.arff'),'w')
        fp_arff.write("@RELATION ts\n")
        fp_arff.write("@ATTRIBUTE srcid NUMERIC\n")
        for param_name in arff_attrib_list:
            fp_arff.write("@ATTRIBUTE %s NUMERIC\n" % (param_name))
        fp_arff.write("@ATTRIBUTE class {'contact','detached','semi-detached'}\n@DATA\n")


        xlim_dict = {'q_err':    [0.0, 50],
                     'q':        [-5.0, 45],
                     'l1/l2_err':[0.0, 10],
                     'l1/l2':    [0.0, 10],
                     'chisq':    [0.0, 5],
                     'reflect1': [0.0, 0.1],
                     'r1':       [0.0, 2],
                     'r2':       [0.0, 2],
                     'i_err':    [0.0, 100]}

        for class_name in self.pars['fiteb_class_lookup'].values():
            for i_param, param_name in enumerate(self.pars['analysis_params']):
                match_vals = []
                mismatch_vals = []
                for srcid, src_dict in data_dict.iteritems():
                    ### NOTE: cannot apply these constraints:
                    ##  i : even for detached, i spread for matches is >= mismatch i value spread
                    ##  e : doesnt seem to be related to match / mismatch
                    ##  l1 : doesnt seem to be related to match / mismatch
                    ##  dof : probably related to N-epochs
                    #if ((class_name == src_dict['tutor_class'] == src_dict['fiteb_class']) and
                    #    (src_dict['chisq'] <= 2.4) and
                    #if ((class_name == src_dict['fiteb_class']) and
                    #    (src_dict['chisq'] <= 0.91) and

                    # # # Below list are ambigious sources which may be classified wrong by Debosscher or Allstars users
                    """
                    if ((class_name == src_dict['tutor_class']) and
                        (src_dict['tutor_class'] != src_dict['fiteb_class'])
                        ):
                    """

                    ## ## ## Prior to reclassification of non tutor_class == fiteb_class sources:
                    # # # Below list are ambigious sources which may be classified wrong by Debosscher or Allstars users
                    """
                    if ((class_name == src_dict['tutor_class'] == src_dict['fiteb_class']) and
                        ((srcid not in [ \

164798,
164636,
164633,
164612,
164869,
221996,
228218,
164768,
164772,
244713,
164850,
164880,
261921,
237428,
249855,
164624,
164649,
164736,
164775,
164790,
164794,
164814,
164822,
234812,
227324,
219432,
252570,
164828,
164839,
164535,
164581,
164598,
164606,
246724,
249004,
226992,
231228]) or (srcid in [ \
164843,
164847,
164851,
164854,
217524,
232806,
237022,
222870,
164537,
164512,
164518,
164543,
164776,
164786,
]))
                        ):
                    """

                    if use_trainset_srcid_list:
                        if not srcid in trainset_srcid_class_dict.keys():
                            continue # skip this source
                        source_class = trainset_srcid_class_dict[srcid]
                        #import pdb; pdb.set_trace()
                        #print
                    else:
                        source_class = src_dict['tutor_class']

                    # # # Below list are ambigious sources which may be classified wrong by Debosscher or Allstars users
                    if ((class_name == source_class)
                        ):
                        if i_param == 0:
                            fp_html.write('<tr><td><A href="http://lyra.berkeley.edu/allstars/?mode=inspect&srcid=%d">%d</A></td><td><A href="http://lyra.berkeley.edu/~pteluser/fiteb_plots/plot%d.png" target="_blank">plot</A></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%4.2f</td><td>%4.4f</td><td>%4.2f +- %4.2f</td><td>%4.2f +- %4.2f</td><td>%4.2f +- %4.2f</td><td>%s</td><td>%s</td></tr>\n' % \
                             (srcid, srcid, srcid, src_dict['file'],
                              source_class,
                              src_dict['fiteb_class'],
                              str(src_dict['okfit']),
                              src_dict['chisq'],
                              src_dict['e'],
                              src_dict['i'],
                              src_dict.get('i_err',99999) if src_dict.get('i_err',99999) is not None else 99999,
                              src_dict['q'],
                              src_dict['q_err'],
                              src_dict['l1/l2'],
                              src_dict['l1/l2_err'],
                              str(src_dict['reflect1']),
                              str(src_dict['reflect2']),
                              ))
                            ### KLUDGEY:
                            val_strs = []
                            for param_name2 in arff_attrib_list:
                                #if ((srcid == 264245) and (param_name2 == 'semi-detached_chisq_perc_5')):
                                #import pdb; pdb.set_trace()
                                #print   
                                if '_perc_' in param_name2:
                                    perc_num = int(param_name2[param_name2.rfind('_')+1:])
                                    cls_name = param_name2[:param_name2.find('_')]
                                    attrib_root = param_name2[param_name2.find('_')+1:param_name2.rfind('_perc_')]
                                    attrib_percentiles_name = attrib_root + "_percentiles"
                                    v = src_dict.get(attrib_percentiles_name,{}).get(cls_name,{}).get(perc_num,{}).get('val_at_perc',"?")
                                elif '_npass_' in param_name2:
                                    perc_num = int(param_name2[param_name2.rfind('_')+1:])
                                    cls_name = param_name2[:param_name2.find('_')]
                                    attrib_root = param_name2[param_name2.find('_')+1:param_name2.rfind('_npass_')]
                                    attrib_percentiles_name = attrib_root + "_percentiles"
                                    v = src_dict.get(attrib_percentiles_name,{}).get(cls_name,{}).get(perc_num,{}).get('n_pass',"?")
                                elif 'perc_val_' in param_name2:
                                    perc_num = int(param_name2[param_name2.rfind('_')+1:])
                                    attrib_root = param_name2[param_name2.find('perc_val_')+9:param_name2.rfind('_')]
                                    v = src_dict.get('vals_for_percentile',{}).get(attrib_root,{}).get(perc_num,"?")
                                elif 'perc_pass_' in param_name2:
                                    perc_num = int(param_name2[param_name2.rfind('_')+1:])
                                    attrib_root = param_name2[param_name2.find('perc_pass_')+10:param_name2.rfind('_')]
                                    v = src_dict.get('ratiopass_for_percentile',{}).get(attrib_root,{}).get(perc_num,"?")
                                else:
                                    v = src_dict.get(param_name2, "?") if src_dict.get(param_name2, "?") is not None else "?"
                                    if numpy.isnan(v):
                                        v = "?" # KLUDGE
                                if v == 999999:
                                    print 'INT 999999'
                                    v = "?" # KLUDGE: catches this N/A value which is generated in fiteb.py::period_select() when EB.run().outrez{} is missing some physical parameters
                                elif v == 99999:
                                    print 'INT 99999'
                                    v = "?" # KLUDGE: catches this N/A value which is generated in fiteb.py::period_select() when EB.run().outrez{} is missing some physical parameters
                                val_strs.append(str(v))
                            a_str = "%d,%s,'%s'\n" % (srcid, ",".join(val_strs), self.pars['fiteb_class_lookup_rev'][class_name])
                            fp_arff.write(a_str)
                            
                        if 'chi2_perc' in param_name:
                            perc_num = int(param_name[param_name.rfind('_')+1:])
                            cls_name = self.pars['fiteb_class_lookup_rev'][class_name]
                            if src_dict['chisq_percentiles'].has_key(cls_name):
                                v = src_dict['chisq_percentiles'][cls_name][perc_num]['val_at_perc']
                            else:
                                v = None
                        elif 'chi2_npass' in param_name:
                            perc_num = int(param_name[param_name.rfind('_')+1:])
                            cls_name = self.pars['fiteb_class_lookup_rev'][class_name]
                            if src_dict['chisq_percentiles'].has_key(cls_name):
                                v = src_dict['chisq_percentiles'][cls_name][perc_num]['n_pass']
                            else:
                                v = None
                        else:
                            v = src_dict[param_name]
                        if v != None:
                            match_vals.append(v)
                            print "   MATCH plot:%s TUTOR:%s fiteb:%s chi2:%f" % (class_name, source_class, src_dict['fiteb_class'], src_dict['chisq'])                        
                    elif ((class_name == source_class) and
                          (source_class != src_dict['fiteb_class']) and
                          (srcid in [260456, 220490, 217279, 222948, 219432, 216954, 251878, 226123, 247767, 237081, 235730, 250580, 231228, 222870, 246079, 164512, 164525, 164531, 164533, 164541, 164542, 164543, 164544, 164558, 164556, 164562, 164577, 164579, 164583, 164588, 164596, 164592, 164603, 164611, 164613, 164625, 164628, 164643, 164651, 164667, 164669, 164674, 164683, 164685, 164684, 164690, 164697, 164704, 164703, 164701, 164712, 164707, 164710, 164725, 164744, 164766, 164771, 164778, 164797, 164833, 164867, 164876, 164881])
                          ):
                        if 'chi2_perc' in param_name:
                            perc_num = int(param_name[param_name.rfind('_')+1:])
                            cls_name = self.pars['fiteb_class_lookup_rev'][class_name]
                            if src_dict['chisq_percentiles'].has_key(cls_name):
                                v = src_dict['chisq_percentiles'][cls_name][perc_num]['val_at_perc']
                            else:
                                v = None
                        elif 'chi2_npass' in param_name:
                            perc_num = int(param_name[param_name.rfind('_')+1:])
                            cls_name = self.pars['fiteb_class_lookup_rev'][class_name]
                            if src_dict['chisq_percentiles'].has_key(cls_name):
                                v = src_dict['chisq_percentiles'][cls_name][perc_num]['n_pass']
                            else:
                                v = None
                        else:
                            v = src_dict.get(param_name,88888)
                        if v != None:
                            mismatch_vals.append(v)
                            print "MISMATCH plot:%s TUTOR:%s fiteb:%s chi2:%f" % (class_name, source_class, src_dict['fiteb_class'], src_dict['chisq'] if src_dict.get('chisq',99999) is not None else 99999)

                #mags = vals
                #fits = norm.fit(mags)
                #dist = norm(fits)
                #for m in mags:
                #    probs.append(dist.pdf(m)[0]) # * len(param_list)/float(len(mag)))

                if (len(xlim_dict.get(param_name,[])) == 0):
                    minmax_list = []
                    for a_list in [match_vals, mismatch_vals]:
                        if len(a_list) > 0:
                            minmax_list.extend([min(a_list), max(a_list)])
                    x_range = (min(minmax_list), max(minmax_list))
                    #if (len(match_vals) > 0):
                    #    x_range = (min(match_vals), max(match_vals))
                    #else:
                    #    x_range = (min(mismatch_vals), max(mismatch_vals))
                else:
                    x_range = (xlim_dict[param_name][0], xlim_dict[param_name][1])

                pyplot.hist(mismatch_vals, bins=50, normed=False, facecolor='b', alpha=0.3, range=x_range)
                pyplot.hist(match_vals, bins=50, normed=False, facecolor='r', alpha=0.3, range=x_range)
                #pyplot.plot(mags, probs, 'ro', ms=3)

                title_str = '%s  %s' % (class_name, param_name)
                pyplot.title(title_str)
                fpath = "/tmp/evaluate_eclipsing_classifs__%s.png" % (title_str.replace(' ','_').replace('/','_'))
                pyplot.savefig(fpath)
                #os.system('eog %s ' % (fpath))
                #pyplot.show()

                print param_name
                pyplot.clf()


        fp_html.write("""</table></body></html>
        """)
        fp_html.close()
        fp_arff.close()
        os.system('eog /tmp/evaluate_eclipsing_classifs*png &')
        #import pdb; pdb.set_trace()
        #print
        
class Classify_And_Summarize:
    """ Classify and generate summary html, as well as classification distribution summary file.
    """ 
    def __init__(self, pars={}):
        self.DatabaseUtils = Database_Utils(pars=pars)


    def classify_and_summarize(self):
        """ Classify and generate summary html, as well as classification distribution summary file.

    ### ### ###
    # 1st iteration, producing initial classification distribution with .model generated using
    #    dstarr's hand selected training-set.
        p = {'test_arff_withsrcid':'/home/pteluser/scratch/evaluate_eclipsing_classifs__2of11perc__tutor_fiteb_mismatch_testset2__noclassattribs.arff',
             'test_arff_nosrcid':"/home/pteluser/scratch/evaluate_eclipsing_classifs__2of11perc__tutor_fiteb_mismatch_testset2__noclassattribs__nosrcid.arff",
             'train_arff_withsrcid':'/home/pteluser/scratch/evaluate_eclipsing_classifs__2of11perc__trainset2__noclassattribs.arff',
             'train_model':"/home/pteluser/scratch/evaluate_eclipsing_classifs__RandForest_2of11__nonclassattribs__trainset2_crossvalid.model",
             'comment_file':"/home/pteluser/scratch/evaluate_eclipsing_classifs.comments",
             'classif_distrib_fpath':'/home/pteluser/scratch/evaluate_eclipsing_classifs.class_distrib',
             'classif_distrib_html_fpath':'/home/pteluser/scratch/evaluate_eclipsing_classifs_distribution_summary.html',
             'classes':['contact','detached','semi-detached'],  # order used in the .arff / classifier distrib output
             'distribclass_to_classes_lookup':{
                 'detached':'detached',
                 'semi-det':'semi-detached',
                 'contact':'contact',
                 },
             }
    ### ### ###
    # 2nd iteration, using 2 corrberating classifications in papers for a source to be used in the training set.
    # Maybe 5-10 sources which were not in trainingset or in the wrong trainingset classes.
    ### ### ###
        p = {'test_arff_withsrcid':'/home/pteluser/scratch/evaluate_eclipsing_classifs__2of11perc__tutor_fiteb_mismatch_testset2__noclassattribs.arff',
             'test_arff_nosrcid':"/home/pteluser/scratch/evaluate_eclipsing_classifs__2of11perc__tutor_fiteb_mismatch_testset2__noclassattribs__nosrcid.arff",
             'train_arff_withsrcid':'/home/pteluser/scratch/evaluate_eclipsing_classifs__2of11perc__trainset3.arff',
             'train_model':"/home/pteluser/scratch/evaluate_eclipsing_classifs__RandForest_2of11__trainset3_crossvalid.model",
             'comment_file':"/home/pteluser/scratch/evaluate_eclipsing_classifs.comments",
             'classif_distrib_fpath':'/home/pteluser/scratch/evaluate_eclipsing_classifs.class_distrib',
             'classif_distrib_html_fpath':'/home/pteluser/scratch/evaluate_eclipsing_classifs_distribution_summary.html',
             'classes':['contact','detached','semi-detached'],  # order used in the .arff / classifier distrib output
             'distribclass_to_classes_lookup':{
                 'detached':'detached',
                 'semi-det':'semi-detached',
                 'contact':'contact',
                 },
             }

    ### ### ###
    Fourth iteration (there was no third):
        p = {'test_arff_withsrcid':'/home/pteluser/scratch/evaluate_eclipsing_classifs__2of11perc__tutor_fiteb_mismatch_testset2__noclassattribs.arff',
             'test_arff_nosrcid':"/home/pteluser/scratch/evaluate_eclipsing_classifs__2of11perc__tutor_fiteb_mismatch_testset2__noclassattribs__nosrcid.arff",
             'train_arff_withsrcid':'/home/pteluser/scratch/evaluate_eclipsing_classifs__2of11perc__trainset4.arff',
             'train_model':"/home/pteluser/scratch/evaluate_eclipsing_classifs__RandForest_2of11__trainset4_crossvalid.model",
             'comment_file':"/home/pteluser/scratch/evaluate_eclipsing_classifs.comments",
             'classif_distrib_fpath':'/home/pteluser/scratch/evaluate_eclipsing_classifs.class_distrib',
             'classif_distrib_html_fpath':'/home/pteluser/scratch/evaluate_eclipsing_classifs_distribution_summary.html',
             'classes':['contact','detached','semi-detached'],  # order used in the .arff / classifier distrib output
             'distribclass_to_classes_lookup':{
                 'detached':'detached',
                 'semi-det':'semi-detached',
                 'contact':'contact',
                 },
             }
    ### ### ###
    5th iteration, re-analysis of attributes using SVM Ranker
        p = {'test_arff_withsrcid':'/home/pteluser/scratch/evaluate_eclipsing_classifs__allsrcs__attribsfrom_testset5redone.arff',
             'test_arff_nosrcid':"/home/pteluser/scratch/evaluate_eclipsing_classifs__allsrcs__attribsfrom_testset5redone__nosrcid.arff",
             'train_arff_withsrcid':'/home/pteluser/scratch/evaluate_eclipsing_classifs__2of11perc__trainset5__redoneattribs.arff',
             'train_model':"/home/pteluser/scratch/evaluate_eclipsing_classifs__RandForest_2of11__trainset5__redoneattribs__crossvalid.model",
             'comment_file':"/home/pteluser/scratch/evaluate_eclipsing_classifs.comments",
             'classif_distrib_fpath':'/home/pteluser/scratch/evaluate_eclipsing_classifs.class_distrib', # for output
             'classif_distrib_html_fpath':'/home/pteluser/scratch/evaluate_eclipsing_classifs_distribution_summary.html', # for output
             'classes':['contact','detached','semi-detached'],  # order used in the .arff / classifier distrib output
             'distribclass_to_classes_lookup':{
                 'detached':'detached',
                 'semi-det':'semi-detached',
                 'contact':'contact',
                 },
             }

    ### ### ###

        """
        p = {'test_arff_withsrcid':'/home/pteluser/scratch/evaluate_eclipsing_classifs__allsrcs__attribsfrom_testset6.arff',
             'test_arff_nosrcid':"/home/pteluser/scratch/evaluate_eclipsing_classifs__allsrcs__attribsfrom_testset6__nosrcid.arff",
             'train_arff_withsrcid':'/home/pteluser/scratch/evaluate_eclipsing_classifs__2of11perc__trainset6.arff',
             'train_model':"/home/pteluser/scratch/evaluate_eclipsing_classifs__RandForest_2of11__trainset6_crossvalid.model",
             'comment_file':"/home/pteluser/scratch/evaluate_eclipsing_classifs.comments",
             'classif_distrib_fpath':'/home/pteluser/scratch/evaluate_eclipsing_classifs.class_distrib', # for output
             'classif_distrib_html_fpath':'/home/pteluser/scratch/evaluate_eclipsing_classifs_distribution_summary.html', # for output
             'classes':['contact','detached','semi-detached'],  # order used in the .arff / classifier distrib output
             'distribclass_to_classes_lookup':{
                 'detached':'detached',
                 'semi-det':'semi-detached',
                 'contact':'contact',
                 },
             }

        srcid_comment = {}
        for line in open(p['comment_file']).readlines():
            if len(line) <= 1:
                continue
            srcid = int(line[:line.find(' ')])
            comment = line[line.find(' '):]
            srcid_comment[srcid] = comment.strip()


        testing_srcid_list = []
        found_data = False
        for line in open(p['test_arff_withsrcid']).readlines():
            if found_data:
                srcid = int(line[:line.find(',')])
                testing_srcid_list.append(srcid)
                # NOTE: I dont think we need to parse the class, snce this is contained in the class distrib output        
            elif "@DATA" in line:
                found_data = True
            
        training_srcid_list = []
        found_data = False
        for line in open(p['train_arff_withsrcid']).readlines():
            if found_data:
                srcid = int(line[:line.find(',')])
                training_srcid_list.append(srcid)
                # NOTE: I dont think we need to parse the class, snce this is contained in the class distrib output        
            elif "@DATA" in line:
                found_data = True

        ### Apply classifier to test-set
        sys_str = "java weka.classifiers.trees.RandomForest -T %s -l %s -p 1 -distribution > %s" % (p['test_arff_nosrcid'], p['train_model'], p['classif_distrib_fpath'])
        os.system(sys_str)
        time.sleep(2)
            
        #training_srcid_list = []
        found_header = False
        test_srcid_classifs = {}
        test_class_prob_srcid_tups = []
        i_src = 0
        for line in open(p['classif_distrib_fpath']).readlines():
            if found_header and (len(line) > 1):
                elems = line[:i_error].split()
                tutor_class = p['distribclass_to_classes_lookup'][elems[1][elems[1].find(':') +1:]]
                pred_class = elems[2][elems[2].find(':') +1:]

                srcid = testing_srcid_list[i_src]
                elems = line[i_error + 5:].split()
                prob_elems = elems[0].split(',')
                class_probs = []
                for i_class, prob_str in enumerate(prob_elems):
                    if '*' in prob_str:
                        i_chosen_class = i_class
                    prob_num = float(prob_str.replace("*",''))
                    class_probs.append(prob_num)
                test_srcid_classifs[srcid] = {'primary_class_i':i_chosen_class,
                                              'class_probs':class_probs,
                                              'tutor_class':tutor_class,
                                              }
                ### Here we append (class_name, primary_classprob, srcid) to a list for sorting:
                test_class_prob_srcid_tups.append((p['classes'][i_chosen_class], class_probs[i_chosen_class], srcid))
                i_src += 1

            elif "inst#" in line:
                found_header = True
                i_error = line.index('error')

        fp = open(p['classif_distrib_html_fpath'], 'w')
        fp.write("""<html><body><table border="1">
            <tr><td><b>source_id</b></td>
            <td><b>plot</b></td>
            <td><b>Matches</b></td>
            <td><b>TrainSet</b></td>
            <td><b>TUTOR/ALLStars</b></td>
            <td><b>Predicted</b></td>
            <td><b>Pred. Prob</b></td>
            <td><b>&nbsp; &nbsp; &nbsp; &nbsp;</b></td>
            <td><b>contact</b></td>
            <td><b>detached</b></td>
            <td><b>semi-det</b></td>
            <td><A href="http://lyra.berkeley.edu/~pteluser/evaluate_eclipsing_classifs.comments" target="_blank"><b>COMMENT</b></A></td>
            </tr>
            """)
        test_class_prob_srcid_tups.sort(reverse=True)
        #import pdb; pdb.set_trace()
        #print
        for (pred_class, pred_prob, srcid) in test_class_prob_srcid_tups:
            tutor_matches_pred_str = ""
            if pred_class == test_srcid_classifs[srcid]['tutor_class']:
                tutor_matches_pred_str = "match"

            in_trainingset_str = ""
            if srcid in training_srcid_list:
                in_trainingset_str = "train"
                
            comment_str = ""
            if srcid in srcid_comment.keys():
                comment_str = srcid_comment[srcid]

            a_str = """<tr><td><A href="http://lyra.berkeley.edu/allstars/?mode=inspect&srcid=%d" target="_blank">%d</A></td>
                            <td><A href="http://lyra.berkeley.edu/~pteluser/fiteb_plots/plot%d.png" target="_blank">plot</A></td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%0.2f</td>
                            <td></td>
                            <td>%0.2f</td>
                            <td>%0.2f</td>
                            <td>%0.2f</td>
                            <td>%s</td>\n""" % ( \
                srcid,
                srcid,
                srcid,
                tutor_matches_pred_str,
                in_trainingset_str,
                test_srcid_classifs[srcid]['tutor_class'],
                p['classes'][test_srcid_classifs[srcid]['primary_class_i']],
                test_srcid_classifs[srcid]['class_probs'][test_srcid_classifs[srcid]['primary_class_i']],
                test_srcid_classifs[srcid]['class_probs'][0],
                test_srcid_classifs[srcid]['class_probs'][1],
                test_srcid_classifs[srcid]['class_probs'][2],
                comment_str,
                         )
            #import pdb; pdb.set_trace()
            #print
            fp.write(a_str)


            select_str = "select source_ra, source_dec, source_name from sources where source_id = %d" % (srcid)
            self.DatabaseUtils.tutor_cursor.execute(select_str)
            results = self.DatabaseUtils.tutor_cursor.fetchall()
            if len(results) == 0:
                raise "Error"
            ra = results[0][0]
            decl = results[0][1]
            source_name = results[0][2]            
            # ASAS only:   if srcid >= 215153:
            if ((test_srcid_classifs[srcid]['tutor_class'] != p['classes'][test_srcid_classifs[srcid]['primary_class_i']]) and
                ((test_srcid_classifs[srcid]['class_probs'][0] >= 0.8) or
                 (test_srcid_classifs[srcid]['class_probs'][1] >= 0.8) or
                 (test_srcid_classifs[srcid]['class_probs'][2] >= 0.8))):
                print "%d %s %12.6lf %12.6lf %s %0.7s %0.7s %0.2f %0.2f %0.2f %s" % ( \
                    srcid,
                    source_name,
                    ra,
                    decl,
                    in_trainingset_str if in_trainingset_str == "train" else "     ",
                    test_srcid_classifs[srcid]['tutor_class'],
                    p['classes'][test_srcid_classifs[srcid]['primary_class_i']],
                    test_srcid_classifs[srcid]['class_probs'][0], #test_srcid_classifs[srcid]['class_probs'][test_srcid_classifs[srcid]['primary_class_i']],
                    test_srcid_classifs[srcid]['class_probs'][1],
                    test_srcid_classifs[srcid]['class_probs'][2],
                    comment_str,
                    )
                #import pdb; pdb.set_trace()
                #print

        fp.write("""</table></body></html>
            """)
        fp.close()



def generate_jktebop_templates(pars={}):
    """
    ### generate additional JKTEBOP template files, to better explore param space
    #      when trying to fit an eclipsing model to a lightcurve.
    """
    if len(pars) == 0:
        pars = {'template_dirpath':os.path.abspath(os.environ.get("HOME") + '/src/install/jsb_eb_fit/Templates'),
                'reference_template_fpath':os.path.abspath(os.environ.get("HOME") + '/src/install/jsb_eb_fit/Templates/eb.4.template'),#'/home/pteluser/src/install/jsb_eb_fit/Templates/eb.3.template',
                'fname_i_start':2,
                'tweak_params':{'Orbital inclination':{'i_low':0,
                                                       'i_high':4,
                                                       'min':65.,
                                                       'max':90.,
                                                       'n_samples':5},
                                'Mass ratio of system':{'i_low':5,
                                                        'i_high':9,
                                                        'min':-0.5,
                                                        'max':2.0,
                                                        'n_samples':5},
                                'Ratio of the radii':{'i_low':5,
                                                        'i_high':9,
                                                        'min':0.1,
                                                        'max':3.0,
                                                        'n_samples':5},
                                },
                }
    lines = open(pars['reference_template_fpath']).readlines()
            
    i_template = pars['fname_i_start']

    pname_1 = 'Orbital inclination'
    pdict_1 = pars['tweak_params'][pname_1]
    val_arr_1 = numpy.linspace(pdict_1['min'], pdict_1['max'], pdict_1['n_samples'])
    for val_1 in list(val_arr_1):
        new_lines = []
        for i_line, line in enumerate(lines):
            if pname_1 in line:
                val_1_str = "%0.1f" % (val_1)
                new_line = "%s%s%s" % (line[:pdict_1["i_low"]], val_1_str, line[pdict_1["i_low"] + len(val_1_str):])
                print new_line
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        lines = new_lines

        pname_2 = 'Mass ratio of system'
        pdict_2 = pars['tweak_params'][pname_2]
        val_arr_2 = numpy.linspace(pdict_2['min'], pdict_2['max'], pdict_2['n_samples'])
        for val_2 in list(val_arr_2):
            new_lines = []
            for i_line, line in enumerate(lines):
                if pname_2 in line:
                    val_2_str = "%0.1f" % (val_2)
                    new_line = "%s%s%s" % (line[:pdict_2["i_low"]], val_2_str, line[pdict_2["i_low"] + len(val_2_str):])
                    print new_line
                    new_lines.append(new_line)
                else:
                    new_lines.append(line)

            lines = new_lines

            pname_3 = 'Ratio of the radii'
            pdict_3 = pars['tweak_params'][pname_3]
            val_arr_3 = numpy.linspace(pdict_3['min'], pdict_3['max'], pdict_3['n_samples'])
            for val_3 in list(val_arr_3):
                new_lines = []
                for i_line, line in enumerate(lines):
                    if pname_3 in line:
                        val_3_str = "%0.1f" % (val_3)
                        new_line = "%s%s%s" % (line[:pdict_3["i_low"]], val_3_str, line[pdict_3["i_low"] + len(val_3_str):])
                        print new_line
                        new_lines.append(new_line)
                    else:
                        new_lines.append(line)


                fpath = "%s/eb.4.alt%d.template" % (pars['template_dirpath'], i_template)
                #fpath = "%s/eb.3.alt%d.template" % (pars['template_dirpath'], i_template)
                if os.path.exists(fpath):
                    os.system("rm " + fpath)
                fp = open(fpath, 'w')
                fp.writelines(new_lines)
                fp.close()
                i_template += 1
    #import pdb; pdb.set_trace()
    #print

    """
    # KLUDGEY: doesnt iterate perfectly over MxN combinations
    i_template = pars['fname_i_start']
    for param_str, p_dict in pars['tweak_params'].iteritems():
        val_arr = numpy.linspace(p_dict['min'], p_dict['max'], p_dict['n_samples'])
        for val in list(val_arr):
            new_lines = []
            for i_line, line in enumerate(lines):
                if param_str in line:
                    new_line = "%s%s%s" % (line[:p_dict["i_low"]], str(val), line[p_dict["i_high"]:])
                    #import pdb; pdb.set_trace()
                    #print
                    new_lines.append(new_line)
                else:
                    new_lines.append(line)
            fpath = "%s/eb.3.alt%d.template" % (pars['template_dirpath'], i_template)
            if os.path.exists(fpath):
                os.system("rm " + fpath)
            fp = open(fpath, 'w')
            fp.writelines(new_lines)
            fp.close()
            i_template += 1
        #import pdb; pdb.set_trace()
        #print
        lines = new_lines

    """



if __name__ == '__main__':
    pars = {'tutor_hostname':'192.168.1.103',
            'tutor_username':'dstarr', #'tutor', # guest
            'tutor_password':'ilove2mass', #'iamaguest',
            'tutor_database':'tutor',
            'tutor_port':3306, #33306,
            'tcp_hostname':'192.168.1.25',
            'tcp_username':'pteluser',
            'tcp_port':     3306, #23306, 
            'tcp_database':'source_test_db',
            'pkl_fpath':os.path.abspath(os.environ.get("HOME") + '/scratch/evaluate_eclipsing_classifs_using_fiteb__dict.pkl'),
            'class_short_lookup':{'EW':'y. W Ursae Maj.',
                                  'EA':'w. Beta Persei',
                                  'EB':'x. Beta Lyrae'},
            'fiteb_class_lookup':{'contact':'y. W Ursae Maj.',
                                  'detached':'w. Beta Persei',
                                  'semi-detached':'x. Beta Lyrae'},
            'analysis_params':['chisq', 'i_err', 'q_err', 'l1/l2_err', 'l1/l2', 'q', 'r1', 'r2', 'reflect1',
                               'reflect2', 'primary_eclipse_phase', 'period', 'omega_deg', 'l1', 'e',
                               ],
            'al_dirpath':os.path.abspath(os.environ.get("TCP_DIR") + 'Data/allstars'),
            'al_glob_str':'AL_*_*.dat',
            'classids_of_interest':[251,#'x. Beta Lyrae',
                                    253,#'w. Beta Persei',
                                    252,#'y. W Ursae Maj.',
                                    ],
            'fittype':3,
            'skip_list':[234996, 164830, 164872, 239309, 216110, 225745],
            'percentile_attrib_skip_list':[],
            'SVMrank_results_input_fpath':"/home/pteluser/scratch/evaluate_eclipsing_classifs__SVMranker_3of11perc__trainset6.results",
            'SVMrank_allow_cut':0.1, #30.2,# SKIP attrib when: merit < self.pars['SVMrank_allow_cut']
            'n_attrib_percentiles_cut':2, #N of percentiles to allow, of 7 percentiles: [5, 10, 15, 20, 30, 40, 50, 60, 70, 80, 90]
            'trainset_srcid_list_fpath':'/home/pteluser/scratch/evaluate_eclipsing_classifs__trainset_srcid.list__subset6',
            }

    if 0:
        ### For generating pickle & html files:
        ### IPython-Parallel mode:
        RunFitEBParallel = Run_FitEB_Parallel()
        RunFitEBParallel.ipython_master()

        ### Single mode (for only for debugging a srcid now):
        #run_fiteb_generate_html_pkl(pars=pars)
        import pdb; pdb.set_trace()
        print

    if 0:
        ### For generating parameter liklihood plots in order to choose param cuts.
        new_pars = {}
        new_pars.update(pars)
        fpa = FitEB_Param_Analysis(pars=new_pars)
        fpa.main(use_trainset_srcid_list=False) # use_trainset_srcid_list=True # generate small train-set arff; =False: generate arff with all eclip sources

    if 1:
        ### Generate classification and a summary HTML
        ### - using an existing WEKA .model, test/train .arff
        cas = Classify_And_Summarize(pars=pars)
        cas.classify_and_summarize()

    if 0:
        ### generate additional JKTEBOP template files, to better explore param space
        #      when trying to fit an eclipsing model to a lightcurve.
        generate_jktebop_templates(pars=pars)
