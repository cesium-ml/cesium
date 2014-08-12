#!/usr/bin/env python
"""
   v0.1 This allows storage of top 3 science classes as TCP classifies
        a simulated PTF observation stream using previously classified
        TUTOR vosource.xmls.

NOTE: Prior to running, need to initialize Ipython1 Cluster server:
        ipcluster -n 8

NOTE: Should ensure that testsuite.py database tables and socket servers
      have been initiated, and have all current feature extractors listed
      in the <source_db>.<feat_lookup> table.

"""
import sys, os
import datetime
import MySQLdb
import copy
import time
import numpy
import scipy
#import pprint # for debugging
#import cProfile # for debugging
#import lsprofcalltree # for debugging

sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                               'Software/feature_extract/Code'))
import db_importer

pars = { 
    'rdb_host_ip':"127.0.0.1",
    'rdb_user':"pteluser",
    'rdb_dbname':'source_test_db',
    'table_name':'iterative_class_probs',
    'ipython_host_ip':"127.0.0.1",
    'ipython_mec_port':10105,
    'ipython_taskclient_port':10113,
    'vosource_xml_dirpath':os.path.expandvars("$TCP_DATA_DIR"), #'/home/pteluser/scratch/new_tutor_vosources',
    'save_plot_image_suffix':'_01', # Used to uniquely label the saved image
    'num_srcids_to_retrieve_plot':999, # 999
    'sciclass_probability_cut':0.1, # don't plot sci_class points with prob <
    'polyfit_factor_threshold':1.1,# epoch_ids[] with 'densities' < are !plotted
    'polyfit_bin_size':5, # Minimum sized sub-array which is plotted
    'polyfit_poly_order':3, # fitted polynomial order
    'plot_symb':['o','s','v','d','>','<','^'], # '+', 'x','.'
    'plot_color':['b','g','r','c','m','y','k','0.25','0.5','0.75', (0.5,0,0), (0,0.5,0), (0,0,0.5), (0.75,0,0), (0,0.75,0), (0,0,0.75), (0.25,0,0), (0,0.25,0), (0,0,0.25)], # color='#eeefff', =0.75, =(1,1,1)
    'interested_sci_classes':['Algol (Beta Persei)','Beta Lyrae','W Ursae Majoris','Binary','T Tauri','Wolf-Rayet','Type Ia Supernovae','BL Lac','Microlensing Event','Semiregular Pulsating Red Giants','Semiregular Pulsating Variable','Population II Cepheid','Short period (BL Herculis)','Classical Cepheid','Long Period (W Virginis)','Symmetrical','Multiple Mode Cepheid','RR Lyrae - Asymmetric','RR Lyrae, Double Mode','RR Lyrae','RR Lyrae, Fundamental Mode','RR Lyrae - Near Symmetric','RR Lyrae, Closely Spaced Modes','Pulsating Variable','SX Phoenicis','Mira'],
    'class_color_dict':{ \
        'Algol (Beta Persei)':'b',
        'Beta Lyrae':'g',
        'W Ursae Majoris':'r',
        'Binary':'c',
        'T Tauri':'m',
        'Wolf-Rayet':'y',
        'Type Ia Supernovae':(0.5, .1, 0),
        'BL Lac':'0.25',
        'Microlensing Event':'0.5',
        'Semiregular Pulsating Red Giants':'0.6',
        'Semiregular Pulsating Variable':(0.5, 0, 0),
        'Population II Cepheid':(0, 0.5, 0),
        'Short period (BL Herculis)':(0, 0, 0.5),
        'Classical Cepheid':(0.75, 0, 0),
        'Long Period (W Virginis)':(0, 0.75, 0),
        'Symmetrical':(0, 0, 0.75),
        'Multiple Mode Cepheid':(0.25, 0, 0),
        'RR Lyrae - Asymmetric':(0, 0.25, 0),
        'RR Lyrae, Double Mode':(0, 0, 0.25),
        'RR Lyrae':(0.25, 0.25, 0),
        'RR Lyrae, Fundamental Mode':(0.25, 0, 0.25),
        'RR Lyrae - Near Symmetric':(0, 0.25, 0.25),
        'RR Lyrae, Closely Spaced Modes':'#bbbaaa',
        'Pulsating Variable':'#aaafff',
        'SX Phoenicis':'#333ccc',
        'Mira':'#666aaa',
        'single-lens':'k',
        'SN Ia':'#444aaa',
        'SN CC':'#666888',
        'SN Ibc':'#777777',
        'SN IIP':'#999777',
        'SN IIn':'#aaa666',
        'W Ursae Majoris -  W UMa':'#aaaaaa',
        'Beta Cephei':'#222aaa',
        'Variable Stars':'#222444',
        '':'k'},
    }

class Analyze_Iterative_Tutor_Classification:
    """ This is the main class of: analyze_iterative_tutor_classification.py.
    """
    def __init__(self, pars):
        self.pars = pars


    def connect_to_db(self):
        """ Make connection to MySQL database.
        """
        self.db = MySQLdb.connect(host=self.pars['rdb_host_ip'], 
                                  user=self.pars['rdb_user'],
                                    db=self.pars['rdb_dbname'])
        self.cursor = self.db.cursor()
        

    def create_mysql_table(self):
        """ Create the mysql table.
        """
        create_str = """CREATE TABLE %s (src_id INT,
                                    epoch_id INT,
                                    n_epochs INT DEFAULT 0,
                                    class_final VARCHAR(80),
                                    class_0 VARCHAR(80),
                                    class_1 VARCHAR(80),
                                    class_2 VARCHAR(80),
                                    prob_0 FLOAT,
                                    prob_1 FLOAT,
                                    prob_2 FLOAT,
                                    fpath VARCHAR(160),
                                    PRIMARY KEY (src_id, epoch_id))""" % (\
                              self.pars['table_name'])
        self.cursor.execute(create_str)


    def drop_table(self):
        """ Drop the 'iterative_class_probs' table.
        """
        try:
            self.cursor.execute("DROP TABLE %s" % (self.pars['table_name']))
        except:
            print 'Unable to DROP TABLE: ', self.pars['table_name']


    def get_tutor_vosource_xml_fpath_list(self):
        """ Given a dirpath to TUTOR vosource XML files, add fpath to list, ret.
        """
        import glob
        glob_str = "%s/*xml" % (self.pars['vosource_xml_dirpath'])
        fpath_list = glob.glob(glob_str)
        return fpath_list


    def insert_vosource_info_into_table(self, fpath):
        """ Given a vosource.xml fpath, parse XML info using db_importer.py, and
        INSERT corresponding rows into table.
        """
        dbi_src = db_importer.Source(make_dict_if_given_xml=True,
                                     make_xml_if_given_dict=False,
                                     doplot=False,
                                     xml_handle=fpath)
        src_id = dbi_src.x_sdict['src_id']
        sci_class = dbi_src.x_sdict['class']
        if len(sci_class) == 0:
            print 'No class:', src_id
            return
        if not sci_class in self.pars['interested_sci_classes']:
            print 'Not a sci-class of interest:', src_id, sci_class
            return
        insert_str = "INSERT INTO %s (src_id, epoch_id, n_epochs, class_final, fpath) VALUES (%d, 0, %d, '%s', '%s')" % (\
                                   self.pars['table_name'],
                                   src_id,
                                   len(dbi_src.x_sdict['ts'].values()[0]['t']),
                                   sci_class, 
                                   fpath)
        self.cursor.execute(insert_str)


class Parallel_Task_Controller:
    """ This controls the Ipython1 task initialization and control.
    Some of this emulates ptf_master.py..PTF_Pol_And_Spawn
    """
    def __init__(self, pars):
        self.pars = pars
        self.running_ingest_tasks = []

    def initialize_clients(self):
        """ Instantiate ipython1 clients, import all module dependencies.
        """
        from IPython.kernel import client
        self.mec = client.MultiEngineClient()
        exec_str = """
import sys
import os
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/ingest_tools'))
import ptf_master
import analyze_iterative_tutor_classification

pars = analyze_iterative_tutor_classification.pars
aitc = analyze_iterative_tutor_classification.Analyze_Iterative_Tutor_Classification(pars)
aitc.connect_to_db()
"""
        print self.mec.execute(exec_str)# Do we get an echo during execution?


    def parallel_populate_mysql_with_initial_tutor_sources(self, fpath_list, \
                                                           test_aitc=None):
        """ This takes fpaths to TUTOR Vosource.xmls and adds each source's
        srcid, science_class to class table in parallel using Ipython1. 
        
        """
        if test_aitc != None:
            # for linear TESTING without Ipython1 / parallelization:
            for fpath in fpath_list:
                test_aitc.insert_vosource_info_into_table(fpath)
            return

        from IPython.kernel import client
        tc = client.TaskClient()

        for fpath in fpath_list:
            exec_str = "aitc.insert_vosource_info_into_table('%s')" % (fpath)
            taskid = tc.run(client.StringTask(exec_str))
            self.running_ingest_tasks.append(taskid)


    def populate_mysql_with_iterative_classes_for_sources(self, aitc, \
                                                    vsrc_xml_fpath_list=[], \
                                                    do_nonparallel=False):
        """ Here we actually iteratively add the individual epochs
        for a vosource, classify, and enter into the analysis Mysql table.
        """
        # TODO: Here we retrieve all relevant vosource.xml fpaths from
        #     mysql table

        if len(vsrc_xml_fpath_list) > 0:
            vosource_fpath_list = vsrc_xml_fpath_list
        else:
            select_str = "SELECT fpath FROM %s" % (self.pars['table_name'])
            aitc.cursor.execute(select_str)

            results = aitc.cursor.fetchall()
            vosource_fpath_list = []
            for result in results:
                vosource_fpath_list.append(result[0])
            


        if do_nonparallel:
            import ptf_master
            #special_vosource_fpath_list = []
            #for elem in special_vosource_fpath_list:
            #    try:
            #        vosource_fpath_list.pop(elem)
            #    except:
            #        pass
            #special_vosource_fpath_list.extend(vosource_fpath_list)
            #for i,fpath in enumerate(special_vosource_fpath_list):
            for i,fpath in enumerate(vosource_fpath_list):
                ptf_master.test_nonthread_nonipython1(use_postgre_ptf=False, 
                              case_simulate_ptf_stream_using_vosource=True, 
                              vosource_xml_fpath=fpath,
                              case_poll_for_recent_postgre_table_entries=False,
                              insert_row_into_iterative_class_probs=True)
                print "Done: VOSource %d of %d" % (i, len(vosource_fpath_list))
            return (None, None)

            ##### For debugging using cProfile, kcachegrind, etc:
            #p = cProfile.Profile()
            #p.run("""
#import ptf_master
#for i,fpath in enumerate(%s):
#    ptf_master.test_nonthread_nonipython1(use_postgre_ptf=False, 
#    case_simulate_ptf_stream_using_vosource=True, 
#    vosource_xml_fpath=fpath,
#    case_poll_for_recent_postgre_table_entries=False,
#    insert_row_into_iterative_class_probs=True)""" % (str(vosource_fpath_list[:14])))
            #k = lsprofcalltree.KCacheGrind(p)
            #data = open('/tmp/prof_14.kgrind', 'w+')
            #k.output(data)
            #data.close()
            #sys.exit()


        from ipython1.kernel import client
        tc = client.TaskClient((self.pars['ipython_host_ip'], \
                                self.pars['ipython_taskclient_port']))

        for fpath in vosource_fpath_list:
            exec_str = \
               """ptf_master.test_nonthread_nonipython1(use_postgre_ptf=False, 
                               case_simulate_ptf_stream_using_vosource=True, 
                               vosource_xml_fpath='%s',
                               case_poll_for_recent_postgre_table_entries=False,
                               insert_row_into_iterative_class_probs=True)
               """ % (fpath)

            taskid = tc.run(client.StringTask(exec_str))
            self.running_ingest_tasks.append(taskid)
        #print 'yo' # print tc.get_task_result(self.running_ingest_tasks[243], block=False)
        return (tc, vosource_fpath_list) # for polling which task threads are still queued, which are finished.


class Retrieve_Tutor_Vosources_From_Web:
    """ Retrieve vosource.xml from web, form fpaths list, and save xml locally.
    """

    def __init__(self):
        import ingest_tools
        self.pars = ingest_tools.pars

        self.tutor_db = MySQLdb.connect(host=self.pars['tcptutor_hostname'], \
                                  user=self.pars['tcptutor_username'], \
                                  passwd=self.pars['tcptutor_password'],\
                                  db=self.pars['tcptutor_database'],\
                                  port=self.pars['tcptutor_port'])
        self.tutor_cursor = self.tutor_db.cursor()


    def get_srcid_list(self):
        """ NOTE: this is duplicated from populate_feat_db_using_TCPTUTOR_sources.py
        """
        select_str = "SELECT DISTINCT sources.source_id FROM    sources WHERE   EXISTS(SELECT Observations.Observation_ID FROM Observations WHERE Observations.Source_ID = sources.Source_ID)"
        self.tutor_cursor.execute(select_str)
        results = self.tutor_cursor.fetchall()
        srcid_list = []
        for result in results:
            srcid_list.append(result[0])
        return srcid_list
    

    def get_vosource_fpath_list(self, vosource_xml_dirpath=''):
        """ (re)create vosource_xml_dirpath, retrieve available tutor
        vosource xmls, return a list of their fpaths.        
        """
        if os.path.exists(vosource_xml_dirpath):
            assert('scratch' in vosource_xml_dirpath) # sanity check before RM
            os.system("rm -Rf " + vosource_xml_dirpath + "/*")
        else:
            os.system("mkdir " + vosource_xml_dirpath)

        srcid_list = self.get_srcid_list()
        return_vosource_fpath_list = []
        for source_id in srcid_list:
            #offset_source_id = source_id + self.pars['tcp_tutor_srcid_offset']
            source_url = "http://lyra.berkeley.edu/tutor/pub/vosource.php?Source_ID=%d" % (source_id)
            wget_fpath = "%s/%d.xml" % (vosource_xml_dirpath, source_id)
            wget_str = "wget --quiet -t 1 -T 5 -O %s %s" % \
                                                        (wget_fpath, source_url)
            os.system(wget_str)
            if os.path.exists(wget_fpath):
                return_vosource_fpath_list.append(wget_fpath)
            else:
                print "Cannot retrieve:", wget_str
        return return_vosource_fpath_list


class Sciclass_Prob_Arrays:
    """ A fairly simple object.
    """
    def __init__(self, factor_threshold=-1, bin_size=-1, poly_order=1,
                 sciclass_probability_cut=0.999):
        self.factor_threshold = factor_threshold
        self.bin_size = bin_size
        self.poly_order = poly_order
        self.sciclass_probability_cut = sciclass_probability_cut
        self.class_dict = {}

    def add(self, epoch_id, class_name, prob):

        # NOTE: (prob < 0.1) is useful but still cluttered 
        if prob < self.sciclass_probability_cut:
            return # don't plot any points with probabilites less than this %%
        if not self.class_dict.has_key(class_name):
            self.class_dict[class_name] = {'epoch_ids':[],
                                           'probs':[],
                                           'linfit_segments':[]}
        self.class_dict[class_name]['epoch_ids'].append(epoch_id)
        self.class_dict[class_name]['probs'].append(prob)


    def get_polynomial_fitted_probs(self, epoch_ids, probs, poly_order=1):
        """ Given a list of epoch_ids and a list of probabilities,
        fit a polynomial to the data and return representative, modeled
        arrays.
        """
        coeffs = scipy.polyfit(numpy.array(epoch_ids),
                               numpy.array(probs), poly_order)

        modeled_epoch_ids = [epoch_ids[0]]
        modeled_probs = [probs[0]]

        epoch_id_span = epoch_ids[-1] - epoch_ids[0]
        for i in xrange(poly_order - 1):
            x = (epoch_id_span / float(poly_order)) * (i + 1) + epoch_ids[0]
            y = scipy.polyval(coeffs, x)
            modeled_epoch_ids.append(x)
            modeled_probs.append(y)
        # TODO: I may want to ensure that the last modeled datapoint has a
        #        >= 0 probability, for plotting niceness.
        modeled_epoch_ids.append(epoch_ids[-1])
        modeled_probs.append(probs[-1])
        return (modeled_epoch_ids, modeled_probs)
    

    def generate_linearfit_endpoints_segments(self):
        """ Filter ['epoch_ids'] and ['probs'] to contain data which is
        densely populate.  Then reduce these arrays to just liner-fit
        sub-array endpoints.
        """
        for class_name, class_dict in self.class_dict.iteritems():

            array_length = len(class_dict['epoch_ids'])
            i = 0
            while ((i + self.bin_size) < array_length):
                temp_epoch_ids = []
                temp_probs = []
                if (class_dict['epoch_ids'][i + self.bin_size] <= \
                    class_dict['epoch_ids'][i] + \
                                       (self.bin_size * self.factor_threshold)):
                    temp_epoch_ids.extend( \
                                  class_dict['epoch_ids'][i:i + self.bin_size])
                    temp_probs.extend(class_dict['probs'][i:i + self.bin_size])
                    i += self.bin_size
                    for j in xrange(i,array_length):
                        if (class_dict['epoch_ids'][j] <= \
                            (class_dict['epoch_ids'][i] + \
                                          ((j - i) * self.factor_threshold))):
                            temp_epoch_ids.append(class_dict['epoch_ids'][j])
                            temp_probs.append(class_dict['probs'][j])
                        else:
                            i -= 1 # it was just incremented above.
                            break # the current point (j) is too sparse along Nepochs axis, so we stop looking for points to append to segment-lists.
                    i = j
                    (modeled_epoch_ids, modeled_probs) = \
                             self.get_polynomial_fitted_probs( \
                                       temp_epoch_ids, temp_probs, \
                                       poly_order=self.poly_order)
                    class_dict['linfit_segments'].append({\
                                                 'epoch_ids':modeled_epoch_ids,
                                                 'probs':modeled_probs})
                i += 1
        

    def arrayiffy(self):
        """ We make numarray of all probability and epoch_id lists, for plotting
        """
        for class_name, class_dict in self.class_dict.iteritems():
            class_dict['epoch_ids'] = numpy.array(class_dict['epoch_ids'])
            class_dict['probs'] = numpy.array(class_dict['probs'])
        

class Make_Summary_Plots:
    """ Make PS plots which summarize the iterative classification of TUTOR
    sources, whose data is stored in TABLE: iterative_class_probs.
    """
    def __init__(self, pars, aitc, table_name=''):
        self.pars = pars
        self.aitc = aitc
        if len(table_name) > 0:
            self.pars['table_name'] = table_name
        self.generate_sciclass_color_dict()


    def generate_sciclass_color_dict(self):
        """ Generate a science-class:color-syle-scalar dictionary for
        Mayavi plotting use.

        NOTE: I additionally offset the first science_class from style=0
              so that the z=0 lines/pipes are a color distinct from
              any science_class.   i.e.: I use (i+2)
        """
        self.sciclass_style_dict = {}
        n_sci_classes = len(self.pars['interested_sci_classes'])

        for i in xrange(n_sci_classes):
            class_name = self.pars['interested_sci_classes'][i]
            self.sciclass_style_dict[class_name] = (i+2) * \
                                           (255.0 / (n_sci_classes + 1 ))

        self.sciclass_style_dict[''] = 0 # KLUDGE: for no-name final classes, which shouldn't really occur?


    def get_srcid_sciclasses_list_from_mysql_table(self, max_n_iters=999, min_num_epochs=50):
        """ Retrieve and form [(src_id, sci_classes), ...] list from
        Mysql Table query.
        """
        srcid_sciclasses_list = []
        srcid_finalclassname_dict = {}
        select_str = "SELECT src_id FROM %s WHERE epoch_id = %d" % (self.pars['table_name'],
                                                                    min_num_epochs)
        self.aitc.cursor.execute(select_str)
        results = self.aitc.cursor.fetchall()
        srcid_list = []
        for result in results:
            srcid_list.append(result[0])

        # # # # # #
        # DEBUGGING / TESTING (I overwrite above array):
        #srcid_list = [14597,14598,14600,14599,14594,14595,14606]
        for src_id in srcid_list[:max_n_iters]:
            select_str = "SELECT class_final FROM %s WHERE src_id=%d and epoch_id = 0" % (self.pars['table_name'], src_id)
            self.aitc.cursor.execute(select_str)
            results = self.aitc.cursor.fetchall()
            final_classname = results[0][0]
            # # # # # # # # DEBUG:   
            #final_classname = ''#'Type Ia Supernovae'
            #srcid_finalclassname_dict[src_id] = final_classname

            #select_str = "SELECT epoch_id, class_0, class_1, class_2, prob_0, prob_1, prob_2 FROM %s WHERE src_id=%d and epoch_id > 0" % (self.pars['table_name'], src_id)
            select_str = "SELECT epoch_id, class_0, class_1, class_2, prob_0, prob_1, prob_2 FROM %s WHERE src_id=%d and epoch_id > 0 and epoch_id < 300" % (self.pars['table_name'], src_id)
            self.aitc.cursor.execute(select_str)

            results = self.aitc.cursor.fetchall()
            sci_classes = Sciclass_Prob_Arrays( \
                         factor_threshold=self.pars['polyfit_factor_threshold'],
                         bin_size=self.pars['polyfit_bin_size'],
                         poly_order=self.pars['polyfit_poly_order'],
                         sciclass_probability_cut=\
                                          self.pars['sciclass_probability_cut'])
            for (epoch_id, class_0, class_1, class_2, prob_0, prob_1, prob_2) in results:
                sci_classes.add(epoch_id, class_0, prob_0)
                sci_classes.add(epoch_id, class_1, prob_1)
                sci_classes.add(epoch_id, class_2, prob_2) #Looks better with...

            srcid_sciclasses_list.append((src_id, sci_classes))
        return (srcid_sciclasses_list, srcid_finalclassname_dict)


    def generate_mayavi_line_plot(self, srcid_sciclasses_list,
                                  use_linfit_segments=False,
                                  enable_mayavi2_interactive_gui=False):
        """ Generate a Mayavi mlab 3D plot which summarizes iterative
        classification of a TUTOR source over the number of epochs
        used/added.
        """
        # TODO: I would like to plot each sci class a different color
        #    - I should have each science class re-use a single number/color
        #    - I should label which science class by color, as Y axis labels
        # TODO: I will need to insert a 0 point onto arrays (for s[0]?)

        if enable_mayavi2_interactive_gui:
            from enthought.mayavi.scripts import mayavi2
            mayavi2.standalone(globals())
        from enthought.mayavi import mlab

        # scalar cut plane plotting module stuff:
        import enthought.mayavi
        from enthought.mayavi.modules.scalar_cut_plane import ScalarCutPlane
        
        epoch_ids = [0] # x
        class_groups = [0] # y
        probs = [0] # z
        styles = [0] # numbers used for coloring & glyph sizes

        used_final_classes = []
        i_srcid = 0
        for final_class in self.pars['interested_sci_classes']:
            if not finalclass_ordered_dict.has_key(final_class):
                continue # skip this science class since nothing to plot
            else:
                used_final_classes.append(final_class)
            srcid_sciclasses_list = finalclass_ordered_dict[final_class]
            for src_id,sci_classes in srcid_sciclasses_list:
                print 'src_id:', src_id, '\t', final_class
                sci_classes.generate_linearfit_endpoints_segments()
                i = 0
                for class_name,class_dict in sci_classes.class_dict.iteritems():
                    class_style = self.sciclass_style_dict[class_name]

                    if use_linfit_segments:
                        for segment_dict in class_dict['linfit_segments']:

                            epoch_ids.extend([segment_dict['epoch_ids'][0]])
                            class_groups.extend([i_srcid])
                            probs.extend([0])
                            styles.extend([0])

                            epoch_ids.extend(segment_dict['epoch_ids'])
                            class_groups.extend([i_srcid]*len(segment_dict['epoch_ids']))
                            probs.extend(segment_dict['probs'])
                            styles.extend([class_style]*len(segment_dict['epoch_ids']))
                            epoch_ids.extend([segment_dict['epoch_ids'][-1]])
                            class_groups.extend([i_srcid])
                            probs.extend([0])
                            styles.extend([0])
                    else:
                        epoch_ids.extend([class_dict['epoch_ids'][0]])
                        class_groups.extend([i_srcid])
                        probs.extend([0])
                        styles.extend([0])

                        epoch_ids.extend(class_dict['epoch_ids'])
                        class_groups.extend([i_srcid]*len(class_dict['epoch_ids']))
                        probs.extend(class_dict['probs'])
                        styles.extend([class_style]*len(class_dict['epoch_ids']))

                        epoch_ids.extend([class_dict['epoch_ids'][-1]])
                        class_groups.extend([i_srcid])
                        probs.extend([0])
                        styles.extend([0])
                    i += 1
                i_srcid += 3 # Y spacing between srcids within a science-class
            i_srcid += 20 # Y spacing between science-class groups
        mlab.plot3d(numpy.array(epoch_ids),
                    numpy.array(class_groups),
                    numpy.array(probs)*100.0,
                    numpy.array(styles),
                    colormap="Paired",
                    tube_radius=1)
        #            extent=[0,600,
        #                    0,i_srcid,
        #                    15, 110])

                    
        mlab.axes(xlabel='N of epochs',
                  ylabel='science class',
                  zlabel='% Prob.')#,
        # DEBUG/UPGRADE: These seem to trigger some bug about Actor methods:
        #          extent=[0,600,
        #                  0,i_srcid,
        #                  -10, 110])

        title_str = "num_srcids=%d   probability_cut=%0.2lf   factor_threshold=%0.2lf   bin_size=%d   poly_order=%d" % (\
                           self.pars['num_srcids_to_retrieve_plot'],
                           self.pars['sciclass_probability_cut'],
                           self.pars['polyfit_factor_threshold'],
                           self.pars['polyfit_bin_size'],
                           self.pars['polyfit_poly_order'])

        ##### TITLE:
        # The 'z' is a flag in Mayavi2 v3.1.0 documentation:
        #mlab.text(0.01, 0.97, title_str, width=1.0, name='title', z=0.0)
        mlab.text(0.01, 0.97, title_str, width=1.0, name='title')

        ##### SCIENCE CLASS LABELS:
        # TODO: Eventually I would like the class labels to be colored and
        #    placed on the y axis, but this requires:
        #     1) later mayavi version to allow 3D text positioning
        #     2) ability to match text color to the line color-map.
        if 1:
            used_final_classes.reverse()
            y = 0.95
            for class_name in used_final_classes:
                class_str = "%2d   %s" %(len(finalclass_ordered_dict[class_name]),
                                           class_name)
                mlab.text(0.85, y, class_str, width=0.095*(len(class_str)/20.0))
                y -= 0.018

        ##### Add a x-axis plane (I can't figure out code to make it opaque)
        if 0:
            cp = ScalarCutPlane()
            mayavi.add_module(cp)
            cp.implicit_plane._hideshow() # this un-displays the plane
            cp.implicit_plane.normal = 0,0,1
            cp.implicit_plane.origin = 150,168,15
            #cp.implicit_plane.position= 0.15 # feature not available yet
            print '##### cp:'
            cp.print_traits()
            print '##### cp.implicit_plane:'
            cp.implicit_plane.print_traits()
            print '##### cp.implicit_plane._HideShowAction:'
            cp.implicit_plane._HideShowAction.print_traits()

        ##### Camera position:
        if enable_mayavi2_interactive_gui:
            camera_distance = 600
        else:
            camera_distance = 1200
        enthought.mayavi.tools.camera.view(azimuth=50,
                                           elevation=70, # 0:looking down to -z
                                           distance=camera_distance,
                                           focalpoint=(100,(i_srcid*0.4),50))

        #enthought.mayavi.mlab.show_pipeline() # this introspecive feature is not available in current mayavi version.

        #####If no Mayavi2 GUI, we allow user to resize image before saving file
        if not enable_mayavi2_interactive_gui:
            print 'Please resize window & Press a Key.'
            import curses
            stdscr = curses.initscr()
            while 1:
                c = stdscr.getch()
                break
            curses.endwin()
        
        ##### Save figure:
        img_fpath ="/tmp/%s%s.png" %(title_str.replace('=','').replace(' ','_'),
                                     self.pars['save_plot_image_suffix'])
        if os.path.exists(img_fpath):
            os.system('rm ' + img_fpath)
        mlab.savefig(img_fpath)#, size=(500,500))#, dpi=200) #size flag doesn't do anything
        print "Saved:", img_fpath


    def generate_mayavi_point_plot(self, srcid_sciclasses_list):
        """ Generate a Mayavi mlab 3D plot which summarizes iterative
        classification of a TUTOR source over the number of epochs
        used/added.
        """
        # # # # # # # # #
        # TODO: I should label which science class by color, as Y axis labels

        from enthought.mayavi.scripts import mayavi2
        mayavi2.standalone(globals())
        from enthought.mayavi import mlab
        
        epoch_ids = [0] # x
        class_groups = [0] # y
        probs = [0] # z
        styles = [0] # numbers used for coloring & glyph sizes
        
        for src_id,sci_classes in srcid_sciclasses_list:
            #print 'src_id:', src_id
            i = 0
            for class_name, class_dict in sci_classes.class_dict.iteritems():
                epoch_ids.extend(class_dict['epoch_ids'])
                class_groups.extend([1]*len(class_dict['epoch_ids']))
                probs.extend(class_dict['probs'])
                styles.extend([i + 1]*len(class_dict['epoch_ids']))
                i += 1

        mlab.points3d(numpy.array(epoch_ids),
                      numpy.array(class_groups),
                      numpy.array(probs)*100.0,
                      numpy.array(styles),
                      colormap="Paired",
                      scale_mode="none",
                      scale_factor=2.0)
        mlab.axes(xlabel='N of epochs',
                  ylabel='science class',
                  zlabel='% Prob.')


    def generate_png_plots(self, srcid_sciclasses_list,
                           srcid_finalclassname_dict):
        """ Makes a .ps plot which summarizes iterative classification
        of a TUTOR source over the number of epochs used/added.
        """
        # TODO: query mysql database for iterative_class_probs_data
        # TODO: make a nice .PS plot & write it.
        # See feature_extraction_interface.py:718

        # Select all sources which have epoch_id>0 and class_final=JOE

        # ) First retrieve src_ids which have epoch_id > 10
        # ) Then for each src_id, retrieve their epoch_id=0 class_final
        # ) Then cluster similar class_final srcids together.
        # ) Then for a specific class_final (and it's set of srcids)
        #   ) For a srcid, retrieve: epoch_id, class_0, _1, _2, prob_0, _1, _2
        #   ) Then for each class_name, build lists: [epoch_ids] coorsp [probs]
        #   ) Then use the same symbol for a sourceid
        #   ) but use  a different color for each scienc-class.
        
        import pylab

        for src_id,sci_classes in srcid_sciclasses_list:
            sci_classes.arrayiffy()

            symbol = self.pars['plot_symb'][0]
            pylab.clf()

            # if len(class_dict['probs']) > 0:
            #     then add class_name to name_list
            #     class_legend_str = "%d %s" % (len(class_dict['probs']), class_name)
            #     also add {class_name:class_legend_str}
            classname_legend_str_dict = {}
            name_list = []
            for class_name, class_dict in sci_classes.class_dict.iteritems():
                if len(class_dict['probs']) > 0:
                    class_legend_str = "%d  %s" % (len(class_dict['probs']), class_name)
                    classname_legend_str_dict[class_name] = class_legend_str
                    name_list.append(class_name)
                print '!', len(class_dict['probs']), class_name
                marker = 'r' + symbol
                l = pylab.plot(class_dict['epoch_ids'], class_dict['probs'], marker)
                pylab.setp(l, 'markerfacecolor', self.pars['class_color_dict'][class_name])
                pylab.setp(l, 'markersize', 6)

            #name_list = self.pars['class_color_dict'].keys()
            name_list.sort()
            #color_list = []
            color_list = []
            legend_str_list = []
            for class_name in name_list:
                legend_str_list.append(classname_legend_str_dict[class_name])
                c_color = self.pars['class_color_dict'][class_name]
                color_list.append(c_color)

            #for c_name in name_list:
            #    c_color = self.pars['class_color_dict'][c_name]
            #    color_list.append(c_color)

            #pylab.legend(tuple(legend_str_list), shadow = True, loc = (-0.25, 0.30))
            pylab.legend(tuple(legend_str_list), shadow = True, loc = (-0.25, 0.75))
            ltext = pylab.gca().get_legend().get_texts()
            for i in xrange(len(color_list)):
                pylab.setp(ltext[i], fontsize = 7, color = color_list[i]) # doesnt do anything:#, fontweight='heavy')
            
            title_str = "%s %s" % (srcid_finalclassname_dict[src_id], src_id)
            pylab.title(title_str)
            fpath = "/tmp/%s.png" % (title_str.replace(' ','_'))
            pylab.savefig(fpath, dpi=200)


if __name__ == '__main__':
    
    aitc = Analyze_Iterative_Tutor_Classification(pars)
    aitc.connect_to_db()


    ##### Do Analysis plotting:
    if 0:
        msp = Make_Summary_Plots(pars, aitc)#, table_name='iterative_class_probs_18557')
        (srcid_sciclasses_list, srcid_finalclassname_dict) = \
                                msp.get_srcid_sciclasses_list_from_mysql_table(\
                                max_n_iters=pars['num_srcids_to_retrieve_plot'],
                                min_num_epochs=8)

        # For Mayavi axis ordering using final-science-classes:
        finalclass_ordered_dict = {}
        for src_id,sci_classes in srcid_sciclasses_list:
            final_class = srcid_finalclassname_dict[src_id]
            if not finalclass_ordered_dict.has_key(final_class):
                finalclass_ordered_dict[final_class] = []
            finalclass_ordered_dict[final_class].append((src_id,sci_classes))

        #########  Plotting of science class probabilities vs. source-ids:
        # (A) # Mayavi 3D GUI window is opened and plotted to:
        #msp.generate_mayavi_line_plot(finalclass_ordered_dict, \
        #                              use_linfit_segments=True)

        # (B) # Matplotlib style 2D plots is written to /tmp/*png
        msp.generate_png_plots(srcid_sciclasses_list,srcid_finalclassname_dict)

        sys.exit()        


    #NOTE: This retrieves the TUTOR Vosource.xml from Web and saves locally:
    #rtvfw = Retrieve_Tutor_Vosources_From_Web()
    #fpath_list = rtvfw.get_vosource_fpath_list(vosource_xml_dirpath = \
    #                                           pars['vosource_xml_dirpath'])

    ### Non-parallel version for DEBUGGING use only:
    ###aitc.insert_vosource_info_into_table('/tmp/a_vosource/rr_lyrae_fundemental_mode_HIP_90053.xml')

    if 0:
        # This populates the initial table (before iterative classification is run)

        ptc = Parallel_Task_Controller(pars)
        ptc.initialize_clients()

        #NOTE: This assumes the TUTOR Vosource.xmls have already been saved locally:
        fpath_list = aitc.get_tutor_vosource_xml_fpath_list()
    
        print 'About to: populate_mysql_with_initial_tutor_sources)...'
        aitc.drop_table()
        aitc.create_mysql_table()
        # NOTE: Use param: test_aitc=aitc for non-parallel testing:
        ptc.parallel_populate_mysql_with_initial_tutor_sources(fpath_list)#, test_aitc=aitc)

        # TODO: For this while() to be effective, I need to query each task
        #       and see whether it is completed.
        #while len(ptc.running_ingest_tasks) > 0:
        #    time.sleep(3)
        #    print 'Still waiting on:', len(ptc.running_ingest_tasks)

        #
        sys.exit()

    if 1:
        # This does the iterative classification.
        # Assumes the basic table was already populated (see above)
        #test_list=['/home/pteluser/scratch/TUTOR_vosources/SNIa_from_20080707tutor/100014484.xml'] # sdss OK, closest_in NO
        #test_list = os.path.abspath(os.environ.get("TCP_DIR") + "/Data/vosource_temp.xml")
        import glob
        #glob_str = "/home/pteluser/scratch/dstarr_SN_vosources_from_TUTOR/*xml"
        glob_str = "/home/pteluser/scratch/vosources_for_analyze_iterative/*xml"
        test_list = glob.glob(glob_str)

        ptc = Parallel_Task_Controller(pars)

        ##############
        do_nonparallel = True
        ##############

        if not do_nonparallel:
            ptc.initialize_clients()

        (tc,vosource_fpath_list) = \
             ptc.populate_mysql_with_iterative_classes_for_sources(aitc,
                                    vsrc_xml_fpath_list=test_list,
                                    do_nonparallel=do_nonparallel) #False)

        ##### This bit is just for printing which tasks are running, completed... :
        completed_tasks = {}
        queued_running_tasks = {}
        for i,task in enumerate(ptc.running_ingest_tasks):
            queued_running_tasks[i] = task
        while len(queued_running_tasks) > 0:
            taskids_to_pop = []
            for i,task  in queued_running_tasks.iteritems():
                try:
                    run_duration = tc.get_task_result(task, block=False).duration
                    taskids_to_pop.append(i)
                    completed_tasks[i] = run_duration
                    print " Finish: %d, duration=%0.2lf, id=%d %s" % \
                          (i, run_duration, tc.get_task_result(task, block=False).taskid, \
                           vosource_fpath_list[i])
                except:
                    pass # this task is still queued / running
            for task_id in taskids_to_pop:
                queued_running_tasks.pop(task_id)

            task_ids_sort = queued_running_tasks.keys()
            task_ids_sort.sort()
            print "%s : %d queued/running;  %d completed. Running tasks:" % (\
                      datetime.datetime.utcnow(),
                      len(queued_running_tasks),
                      len(completed_tasks))
            for task_id in task_ids_sort[:10]:
                print "Running: %d %s" % (task_id, vosource_fpath_list[task_id])
            time.sleep(120)
        print "Done!"

    """
    ##### This generates & prints a dictionary of colors for 2D plotting:
    #temp = copy.deepcopy(pars['plot_color'])
    #for color in temp:
    #    pars['plot_color'].append(color)

    #for i in xrange(len(pars['interested_sci_classes'])):
    #    print "'%s':'%s'," % (pars['interested_sci_classes'][i],
    #                          str(pars['plot_color'][i]))
    #sys.exit()

    """
