#!/usr/bin/env python
"""
This contains code for generating various noisification cases
  of Dotastro sources/science-classes, for viewing
  the spread of features/periods before & after noisification.

These plots are to be used to examine and ensure that the classifier is
  applicable to PTF sources and is trained correctly.


##### Components:

#) DO ONCE: generate features for all dotastro sources, store in a seperate TABLE.
#    - this is a more intelligent/recent implementation than populate_feat_db_using_TCPTUTOR_sources.py
#       - (I think) retrieve Dotastro.org .xml
#       - generate features for XML
#       - get feat:values from dict (like regenerate_vosource_xmls.py::L228)
#    - INSERT / ON DUPLICATE UPDATE    into TABLE : dotastro_feat_values

#) Given a (science class) and noisification/classifier name-string:
#    - look up all_progenitor_class_list.txt list for dotastro source_ids
#    - parse feature values from the vosource.xml in /../featured_vosource/...xml
#    - store feature:vals in noise_gen_source TABLE

) For a particular (science class) and noisification-name-string generate histogram plot:
    - N vs (feature value) for all noisified sources
    - mark input dotastro source values
    - mark PTF sources which are classified as this science-class
         - when using a classifier trained on these noisified-sources.


##############
NOTE: I cannot just create a noisified classifier for onw science class,
      since for the classifier to distinguish between different science
      classes, the classifier needs to be trained on noisified sources
      for every science class.


NOTE: to look at values in the dotastro_feat_valies TABLE:

     SELECT src_id, feat_name, feat_val from dotastro_feat_values join feat_lookup ON (dotastro_feat_values.feat_id=feat_lookup.feat_id AND feat_lookup.filter_id=8);
| src_id | feat_name                            | feat_val        |
+--------+--------------------------------------+-----------------+
|  13318 | ratio32                              |            NULL | 
|  13318 | ratio31                              |            NULL | 



"""
from __future__ import print_function
from __future__ import absolute_import

import os, sys
import MySQLdb
import glob
import time
    
class Ipython_Controller:
    """ This class controlls initialiation and task queuing of ipython-parallel
    TaskClient tasks.

    """

    def __init__(self, pars={}):
        self.pars = pars

        self.taskid_list = []

    def initialize_mec(self, mec_str=""):
        """ Initialize the mec() controller
        """
        self.mec = client.MultiEngineClient()
        #THE FOLLOWING LINE IS DANGEROUS WHEN OTHER TYPES OF TASKS MAY BE OCCURING:
        self.mec.reset(targets=self.mec.get_ids()) # Reset the namespaces of all engines
        self.tc = client.TaskClient()
        self.tc.clear() # This supposedly clears the list of finished task objects in the task-client
        self.mec.flush() # This doesnt seem to do much in our system.

        self.mec.execute(mec_str)


    def add_task(self, task_str=""):
        """ Add a task to Ipython task_client controller.
        """
        taskid = self.tc.run(client.StringTask(task_str))
        self.taskid_list.append(taskid)


    def wait_for_tasks_to_finish(self):
        """ Wait for task client / ipengine tasks to finish.
        """
	while ((self.tc.queue_status()['scheduled'] > 0) or
 	       (self.tc.queue_status()['pending'] > 0)):
            print(self.tc.queue_status())
            print('Sleep... 3 in regenerate_vosource_xmls.py')
            time.sleep(3)
        print('done with while loop')


class DB_Connector:
    """ Estableshes connection to mysql RDB.
    To be inherited by another class.
    """
    def __init__(self):
        pass

    def establish_db_connection(self, cursor=None, host='', user='', db='', port=0):
        """ connect to the rdb database, or use given cursor.
        """
    
        if cursor is None:
            db = MySQLdb.connect(host=host, \
                                 user=user, \
                                 db=db, \
                                 port=port)
            self.cursor = db.cursor()
        else:
            self.cursor = cursor


class Noisification_Task_Populator(DB_Connector):
    """ This class is to be loaded into ipython mec()
    Then this class is called for a dotastro source, which it generates the features,
    and then insertes the results into a special dotastro_feat_values TABLE.
    """

    def add_dotastro_vosource_to_rdb(self, srcid, xml_fpath, gen, tablename_dotastro_feat_values):
        """ Given a vosource XML for a dotastro source,  insert its features into
        dotastro_feat_values style RDB TABLE.
        """
        gen.generate(xml_handle=xml_fpath)
        gen.sig.add_features_to_xml_string(gen.signals_list)

        # # # # (good idea?):
        #       filt_keys.remove('combo_band')

        npoint_tup_list = []
        for filt,filt_dict in gen.signals_list[0].properties['data'].iteritems():
            npoint_tup_list.append((filt_dict['features'].get('n_points',0),filt))

        npoint_tup_list.sort(reverse=True)
        
        if len(npoint_tup_list) == 0:
            print("No filters found for source:", srcid)
            return

        filter_best = npoint_tup_list[0][1]

        filt_dict = gen.signals_list[0].properties['data'][filter_best]
        out_feat_dict = {}
        for feat_name, feat_obj in filt_dict['features'].iteritems():
            try:
                print(feat_obj, '\t', feat_name)
                out_feat_dict[feat_name] = str(float(str(feat_obj)))
                if ((out_feat_dict[feat_name] == 'Fail') or (out_feat_dict[feat_name] == 'nan') or
                    (out_feat_dict[feat_name] == 'inf')  or (out_feat_dict[feat_name] == 'None')):
                    out_feat_dict[feat_name] = 'NULL'
            except:
                out_feat_dict[feat_name] = 'NULL'

        insert_list = ["INSERT INTO %s (src_id, feat_id, feat_val) VALUES " % \
                       (tablename_dotastro_feat_values)]
        for feat_name,feat_val in out_feat_dict.iteritems():
            feat_id = self.featname_featid_lookup[feat_name]
            str_tup = "(%d, %d, %s), " % (srcid, feat_id, feat_val)
            insert_list.append(str_tup)

        if len(insert_list) > 1:
            insert_str = ''.join(insert_list)[:-2] + " ON DUPLICATE KEY UPDATE feat_val=VALUES(feat_val)"
            self.cursor.execute(insert_str)


    def fill_featname_featid_lookup_dict(self, tablename_featlookup='',
                                         filterid_featlookup_table=''):
        """ Query RDB and fill a lookup dict: {<feat_name>:<feat_val>, ...} for filter=8
        """
        select_str = "SELECT feat_name, feat_id FROM %s WHERE filter_id=%d" % ( \
                                                                tablename_featlookup,
                                                                filterid_featlookup_table)
        self.cursor.execute(select_str)

        self.featname_featid_lookup = {}
        results = self.cursor.fetchall()
        for row in results:
            self.featname_featid_lookup[row[0]] = row[1]


    def generate_featdict_using_gen_with_feats(self, gen=None):
        """ Given a gen object which has already had gen.generate() run,
        and which has features within it (from xml or from
             gen.sig.add_features_to_xml_string(gen.signals_list)).

        This function parses the features for the most relevant (populated) filter
        and returns a dictionary containing the features-values which are type==float.
        """
        npoint_tup_list = []
        for filt,filt_dict in gen.signals_list[0].properties['data'].iteritems():
            npoint_tup_list.append((filt_dict['features'].get('n_points',0),filt))

        npoint_tup_list.sort(reverse=True)
        
        if len(npoint_tup_list) == 0:
            print("No filters found for source:", srcid)
            return

        filter_best = npoint_tup_list[0][1]

        filt_dict = gen.signals_list[0].properties['data'][filter_best]
        out_feat_dict = {}
        for feat_name, feat_obj in filt_dict['features'].iteritems():
            try:
                print(feat_obj, '\t', feat_name)
                out_feat_dict[feat_name] = str(float(str(feat_obj)))
            except:
                out_feat_dict[feat_name] = 'NULL'

        return out_feat_dict
        
        

    def add_noisified_xmls_to_rdb(self, dotastro_srcid=0, xml_glob_mask="", schema_name="", class_name="", table_name="", from_xml=None):
        """ Given a glob mask string, get list matching xmls.
        These xmls have features within them, so parse these features
        and store in dotastro_feat_values.

        NOTE: the xml_glob_mask should limit the matched XML files to
              being related to a single DotAstro source-id.

        """
        xml_list = glob.glob(xml_glob_mask)

        insert_list = ["INSERT INTO %s (schema_name, class_name, noise_float_id, dotastro_srcid, feat_id, feat_val) VALUES " % \
                           (table_name)]

        for fpath in xml_list:
            # TODO: make sure that fpath is a full-filepath
            noise_float_id = float(fpath[fpath.rfind('_')+1:fpath.rfind('.')])
            signals_list = []
            #gen = generators_importers.from_xml(signals_list)
            gen = from_xml(signals_list)
            gen.generate(xml_handle=fpath)
            #??? gen.sig.add_features_to_xml_string(gen.signals_list)

            feat_dict = self.generate_featdict_using_gen_with_feats(gen=gen)

            for feat_name,feat_val_str in feat_dict.iteritems():
                feat_id = self.featname_featid_lookup[feat_name]
                if feat_val_str == "NULL":
                    continue # skip from entering NULL data.
                str_tup = '("%s", "%s", %0.12lf, %d, %d, %s), ' % ( \
                                     schema_name, 
                                     class_name,
                                     noise_float_id,
                                     dotastro_srcid,
                                     feat_id, feat_val_str)
                insert_list.append(str_tup)

        if len(insert_list) > 1:
            insert_str = ''.join(insert_list)[:-2]
            self.cursor.execute(insert_str)




class Generate_Store_Dotastro_Source_Features(DB_Connector):
    """
) DO ONCE: generate features for all dotastro sources, store in a seperate TABLE.
    - we are just concerned with all DotAstro.org sources listed in all_progenitor_class_list.txt
    - this is a more intelligent/recent implementation than populate_feat_db_using_TCPTUTOR_sources.py
       - (I think) retrieve Dotastro.org .xml
       - generate features for XML
       - get feat:values from dict (like regenerate_vosource_xmls.py)
    - INSERT / ON DUPLICATE UPDATE    into TABLE : dotastro_feat_values
    """
    def __init__(self, pars={}, cursor=None, ipython_controller=None):
        self.pars = pars
        self.ipython_controller = ipython_controller

        self.establish_db_connection(cursor=cursor, \
                                     host=self.pars['mysql_hostname'], \
                                     user=self.pars['mysql_user'], \
                                     db=self.pars['mysql_database'], \
                                     port=self.pars['mysql_port'])
        self.hist_data_dict = {}
        self.related_classes_dict = {}


    def drop_tables(self):
        # 
        drop_str_list = ["DROP TABLE %s" % (self.pars['tablename_dotastro_feat_values']),  \
                         "DROP TABLE %s" % (self.pars['tablename_noise_gen_sources'])]
        for drop_str in drop_str_list:
            try:
                self.cursor.execute(drop_str)
            except:
                print("Table already exists?:", drop_str)


    def create_tables(self):
        """ create the tables needed for analyzing / plotting the noisification
        results for both dotastro and caltech sources.
        """

        create_str = """CREATE TABLE %s (src_id INT,
                                         feat_id INT,
                                         feat_val DOUBLE,
                                         PRIMARY KEY (src_id, feat_id))
        """ % (self.pars['tablename_dotastro_feat_values'])
        self.cursor.execute(create_str)


        create_str = """CREATE TABLE %s (noise_id INT UNSIGNED AUTO_INCREMENT, 
                                         schema_name VARCHAR(80), 
                                         class_name VARCHAR(80), 
                                         noise_float_id DOUBLE, 
                                         dotastro_srcid INT,
                                         feat_id SMALLINT UNSIGNED,
                                         feat_val DOUBLE,
                                         PRIMARY KEY (noise_id),
                                         INDEX(schema_name, class_name, feat_id, dotastro_srcid))
        """ % (self.pars['tablename_noise_gen_sources'])
        self.cursor.execute(create_str)


    def get_progen_srcdict(self):
        """ Parse the all_progenitor_list file and fill a dict
        with all dotastro sources which pass the pars[all_progenitor_cutval] cut.
        """
        lines = open(self.pars['noisif_all_progenitor_list_fpath']).readlines()

        srcid_dict = {}

        for line in lines:
            a_tup = line.split('@')
            src_id = int(a_tup[1][:a_tup[1].rfind('.')])
            filt = a_tup[2]
            fname = "%d.xml" % (src_id + 100000000) # we-refom the xml the 100009028.xml format we use
            perc = float(a_tup[3].strip())
            if perc <= self.pars['all_progenitor_cutval']:
                srcid_dict[src_id] = {'class':a_tup[0],
                                      'fname':fname,
                                      'filt':a_tup[2],
                                      'progen_percent':perc}
        return srcid_dict


    def get_class_dotastro_lookup(self, progen_srcdict={}):
        """ Using progen_srcdict, generate dict of form: {class_name:dotastro_srcid}
        """
        class_dotastro_lookup = {}

        for src_id, src_dict in progen_srcdict.iteritems():
            if src_dict['class'] not in class_dotastro_lookup:
                class_dotastro_lookup[src_dict['class']] = []
            class_dotastro_lookup[src_dict['class']].append(src_id)
        return class_dotastro_lookup


    def determine_srcids_not_in_table(self, all_srcid_list):
        """ query the dotastro_feat_values TABLE to see if these srcids exist.

        Return a list of srcids which do not exist in this table.
        """
        out_srcid_list = []
        for src_id in all_srcid_list:
            
            select_str = "SELECT src_id from %s WHERE src_id=%d" % ( \
                self.pars['tablename_dotastro_feat_values'],
                src_id)
            self.cursor.execute(select_str)
            results = self.cursor.fetchall()
            if len(results) == 0:
                out_srcid_list.append(src_id)

        return out_srcid_list



    def parse_source_features_insert_into_table(self, srcid_list=[], src_dict={}):
        """
        ) Given a (science class) and noisification/classifier name-string:
            - look up all_progenitor_class_list.txt list for dotastro source_ids
            - parse feature values from the vosource.xml in /../featured_vosource/...xml
            - store feature:vals in noise_gen_source TABLE

        NOTE: we regenerate features for these dotastro sources, regardless
            of whether features exist in the vosource.xml, since those features may be
            incomplete.

        This we want to run with IPython, in parallel.
        """

        ##### This stuff is do be done in the Ipython mec()
        #"""
        task_pars = {'host':self.pars['mysql_hostname'], 
                     'user':self.pars['mysql_user'], 
                     'db':self.pars['mysql_database'], 
                     'port':self.pars['mysql_port']}
        import os,sys
        from . import noisification_analysis
        sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/feature_extract'))
        sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/feature_extract/Code'))
        from Code import *
        import db_importer

        NoiseTaskPop = noisification_analysis.Noisification_Task_Populator()
        NoiseTaskPop.establish_db_connection(host=task_pars['host'],
                                             user=task_pars['user'],
                                             db=task_pars['db'],
                                             port=task_pars['port'])
        NoiseTaskPop.fill_featname_featid_lookup_dict( \
                                        tablename_featlookup=self.pars['tablename_featlookup'], 
                                        filterid_featlookup_table=self.pars['filterid_featlookup_table'])
        #"""
        #####

        #task_str = "os.system('touch /tmp/2435666')"
        for srcid in srcid_list:
            xml_fpath = "%s/%s" % (self.pars['dotastro_xmls_rootdir'], src_dict[srcid]['fname'])

            ##### This stuff is to be done in the ipython task:
            signals_list = []
            gen = generators_importers.from_xml(signals_list)
            NoiseTaskPop.add_dotastro_vosource_to_rdb(srcid, xml_fpath, gen, \
                                                      self.pars['tablename_dotastro_feat_values'])
            ##### 

            if 0:
                # Normal:
                task_str = """signals_list = []
gen = generators_importers.from_xml(signals_list)
NoiseTaskPop.add_dotastro_vosource_to_rdb(%d,  "%s", gen, "%s")
""" % (srcid, xml_fpath, self.pars['tablename_dotastro_feat_values'])
                IpythonController.add_task(task_str=task_str)
            if 0:
                task_str = """time.sleep(3)
tmp_stdout = sys.stdout
sys.stdout = open('/tmp/noisification_analysis.log', 'a')
print '#################################################################################'
signals_list = []
gen = generators_importers.from_xml(signals_list)
NoiseTaskPop.add_dotastro_vosource_to_rdb(%d,  "%s", gen, "%s")
sys.stdout.close()
sys.stdout = tmp_stdout
time.sleep(3)
""" % (srcid, xml_fpath, self.pars['tablename_dotastro_feat_values'])
                IpythonController.add_task(task_str=task_str)

            
    def populate_update_dotastro_feat_values_table(self):
        """ This is called to populate or update the dotastro_feat_values TABLE.
        This is done occasionally, as new features are added or updated.
        """
        progen_srcdict = self.get_progen_srcdict()

        to_do_srcid_list = self.determine_srcids_not_in_table(progen_srcdict.keys())
        
        # TODO: Generate features for these sources which are not in table (using some flag)
        self.parse_source_features_insert_into_table(srcid_list=to_do_srcid_list, src_dict=progen_srcdict)


    def populate_noise_tables_using_noisified_vosource(self, progen_srcdict={}, schema_name="", table_name=""):
        """ 
        # (adding noised data to database)
        # -->> iterate over all srcids found in /featured_vosource/ directory
        #  - given science-class name
        #  - given given schema name
        #  - use progen_srcidict to find corresponding noisified source xmls in /featured_vosource/ directory
        #  - parse the features from each XML
        #  - store these features in TABLE : (<gen noise_id>, <noise xml fname>, feat_id, feat_val)
        """
        ##### (when not testing): This stuff is done in the Ipython mec()
        if 0:
            ##### For non-parallel testing:
        
            import os,sys
            from . import noisification_analysis
            sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/feature_extract'))
            sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/feature_extract/Code'))
            from Code import *
            from Code.generators_importers import from_xml
            import db_importer

            task_pars = {'host':self.pars['mysql_hostname'], 
                         'user':self.pars['mysql_user'], 
                         'db':self.pars['mysql_database'], 
                         'port':self.pars['mysql_port']}
            NoiseTaskPop = noisification_analysis.Noisification_Task_Populator()
            NoiseTaskPop.establish_db_connection(host=task_pars['host'],
                                                 user=task_pars['user'],
                                                 db=task_pars['db'],
                                                 port=task_pars['port'])
            NoiseTaskPop.fill_featname_featid_lookup_dict( \
                                            tablename_featlookup=self.pars['tablename_featlookup'], 
                                            filterid_featlookup_table=self.pars['filterid_featlookup_table'])
        #####
        for src_id, src_dict in progen_srcdict.iteritems():
            # form the true fpath name:
            xml_glob_mask = "%s/%s/featured_vosource/%d_*.xml" % (self.pars['noisified_rootdir'],
                                                schema_name,
                                                100000000 + src_id)
            if 0:
                ##### For non-parallel testing:
                if src_id != 17394:
                    continue
                NoiseTaskPop.add_noisified_xmls_to_rdb(dotastro_srcid=src_id,
                                                       xml_glob_mask=xml_glob_mask,
                                                   schema_name=schema_name,
                                                   class_name=src_dict['class'],
                                                   table_name=table_name,
                                                   from_xml=from_xml)
                #####
            else:
                task_str = """NoiseTaskPop.add_noisified_xmls_to_rdb(dotastro_srcid=%d, xml_glob_mask="%s",schema_name="%s",class_name="%s",table_name="%s",from_xml=from_xml)""" % \
                           (src_id,
                            xml_glob_mask,
                            schema_name,
                            src_dict['class'],
                            table_name)
                IpythonController.add_task(task_str=task_str)

        IpythonController.wait_for_tasks_to_finish()


    def add_noisified_sources_to_tables(self, scheam_name=''):
        """ Given a schema_id, find corresponding noisified vosource xmls
        and retrieve features and store in noise_sources TABLE.
        """
        progen_srcdict = self.get_progen_srcdict()
        self.populate_noise_tables_using_noisified_vosource(progen_srcdict=progen_srcdict,
                                                            schema_name=schema_name,
                                                            table_name=self.pars['tablename_noise_gen_sources'])
        
    def get_featname_featid_lookup(self):
        """Retrieve from RDB the (feat_name
        """
        featname_lookup = {}
        select_str = 'SELECT feat_name, feat_id FROM %s WHERE filter_id=%d' % ( \
                                                  self.pars['tablename_featlookup'],
                                                  self.pars['filterid_featlookup_table'])
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()
        for (feat_name, feat_id) in results:
            featname_lookup[feat_name] = feat_id

        return featname_lookup
        

    def get_tcpsrc_feat_prob(self, schema_name='', original_class_name='', feat_name='', \
                             feat_id=-1, all_related_classes=[]):
        """ This retrieves the tcp/ptf sources which match the schema_name, class_name:

        NOTE: iterating all potential associated/similar class_names may bot be neccissary since it looks like
        just the canonical class names are used in the query below:
        
        | class_name     (these seem to be canonical classes)
        +--------------------------------+
        | W Ursae Majoris                | 
        | Symmetrical                    | 
        | Mira                           | 
        | Binary                         | 
        | Delta Scuti                    | 
        | Algol (Beta Persei)            | 
        | Beta Lyrae                     | 
        | RR Lyrae, Fundamental Mode     | 
        | Pulsating Variable             | 
        | Multiple Mode Cepheid          | 
        | Beta Cephei                    | 
        | Be Star                        | 
        | Semiregular Pulsating Variable | 
        """

        #import pdb; pdb.set_trace()

        tcpsrc_feat_prob_dict = {}
        #for class_name in [original_class_name]:
        # I dont think it hurts to do this (although takes longer), although it may be redundant:
        for class_name in all_related_classes:
            select_str = 'SELECT %s.src_id, prob, feat_val FROM %s JOIN %s ON (%s.src_id=%s.src_id AND feat_id=%d) WHERE schema_comment="%s" AND class_name="%s"' % ( \
                self.pars['tablename_one_src_model_class_probs'], 
                self.pars['tablename_one_src_model_class_probs'], 
                self.pars['tablename_featvalues'],
                self.pars['tablename_one_src_model_class_probs'], 
                self.pars['tablename_featvalues'],
                feat_id,
                schema_name, class_name)
            self.cursor.execute(select_str)
            results = self.cursor.fetchall()
            for (src_id, prob, feat_val) in results:
                #if tcpsrc_feat_prob_dict.has_key(src_id):
                #    # For DEBUG only
                #    print '!!! ASSERTION ERROR', src_id  
                #    raise
                tcpsrc_feat_prob_dict[src_id] = {'feat_val':feat_val,
                                                 'prob':prob}
        return tcpsrc_feat_prob_dict


    def get_noisesrc_feat_dict(self, schema_name='', original_class_name='', feat_name='', \
                               feat_id=-1, all_related_classes=[]):
        """ Retrieve the noisified sources and feature_vals.
        """
        noisesrc_feat_dict = {}

        #for class_name in [original_class_name]:
        for class_name in all_related_classes:
            select_str = 'SELECT dotastro_srcid, noise_float_id, feat_val FROM %s WHERE schema_name="%s" AND class_name="%s" AND feat_id=%d' % ( \
                                                       self.pars['tablename_noise_gen_sources'],
                                                       schema_name,
                                                       class_name,
                                                       feat_id)
            self.cursor.execute(select_str)
            results = self.cursor.fetchall()
            for (dotastro_srcid, noise_float_id, feat_val) in results:
                noisesrc_feat_dict[(dotastro_srcid, noise_float_id)] = {'feat_val':feat_val}
        return noisesrc_feat_dict


    def get_dotastro_src_feat_dict(self, schema_name='', original_class_name='', feat_name='',
                                   feat_id=-1, all_related_classes=[]):
        """ This retrieves the dotastro feature-value for the given feat_id ...
        """
        dotastro_src_feat_dict = {}

        #for class_name in [original_class_name]:
        for class_name in all_related_classes:
            if not class_name in self.class_dotastro_lookup.keys():
                continue # skip this class
            for src_id in self.class_dotastro_lookup[class_name]:
                select_str = 'SELECT feat_val FROM %s WHERE src_id=%d AND feat_id=%d' % ( \
                                                      self.pars['tablename_dotastro_feat_values'],
                                                      src_id,
                                                      feat_id)
                self.cursor.execute(select_str)
                results = self.cursor.fetchall()
                for feat_val_tup in results:
                    dotastro_src_feat_dict[src_id] = feat_val_tup[0]
        return dotastro_src_feat_dict


    def get_jsbvar_src_feat_dict(self, schema_name='', original_class_name='', feat_name='',
                                   feat_id=-1, all_related_classes=[]):
        """ Retrieve JSB astronomer classified sources which match PTF/TCP sources:
        """
        jsbvar_src_feat_dict = {}

        jsbvar_classnames = []
        for tcp_classname in all_related_classes:
            if tcp_classname in self.pars['tcp_to_jsbvar_classname'].keys():
                jsbvar_classnames.extend(self.pars['tcp_to_jsbvar_classname'][tcp_classname])

        condition_list = []
        for class_name in jsbvar_classnames:
            condition_list.append('class_type="%s"' % (class_name))
        condition_str = ""
        if len(condition_list) > 0:
            condition_str = "AND (" + " OR ".join(condition_list) + ")"

            select_str = "SELECT tcp_srcid, source_test_db.feat_values.feat_val FROM %s JOIN source_test_db.feat_values ON (source_test_db.feat_values.src_id=tcp_srcid) WHERE tcp_srcid IS NOT NULL AND source_test_db.feat_values.feat_id=%d %s" % ( \
                                                          self.pars['tablename_jsbvars_lookup'],
                                                          feat_id,
                                                          condition_str)
            self.cursor.execute(select_str)
            results = self.cursor.fetchall()
            for a_tup in results:
                jsbvar_src_feat_dict[a_tup[0]] = a_tup[1]

            # TODO: I want to somehow mark shich source were correctly classified and which were misclassified
            #   - This might initially distract, since we just want to see where these real source feature values lie.
            #   - Do this with a join one_src_model_class_probs for the given schema_class
        return jsbvar_src_feat_dict



    def initialize_plot(self, font_size=7, dpi=300, figsize_tup=(9,11)):
        self.font_size = font_size
        rcParams.update({'text.fontsize':self.font_size})
        rcParams.update({'legend.fontsize':self.font_size})
        rcParams.update({'axes.labelsize':self.font_size})
        rcParams.update({'xtick.labelsize':self.font_size + 2})
        rcParams.update({'ytick.labelsize':self.font_size})

        self.fig = pyplot.figure(figsize=figsize_tup, dpi=dpi)


    def save_plot(self, fpath=''):

        if len(fpath) == 0:
            fpath = "/tmp/blah.ps"
        pyplot.savefig(fpath)
        if self.pars['show_plots']:
            os.system("gv %s & " % fpath)


    def generate_hist_plot(self, classname_list=[], max_val=None, schema_name='', feat_name=''):
        """ This uses an previosly generated, internally stored structure which contains data
        for each science-class.  This data is used here to generate histograms as well
        as calculage min, max feat_val ranges.

        self.hist_data_dict[<schema>][<feat_name>][<science_class_name>] = {'noise_array':[], 'dotastro_array':[], 'tcpsrc_array':[]}

        This will call ax.hist(), ax.plot(), ax... functions.
        """

        ##### KLUDGE: Duplicated elsewhere:
        data_name_list = ['all_noisesrc_featval_array', 'tcpsrc_featval_array', 'all_dotastro_featval_array']
        all_min = min(self.hist_data_dict[schema_name][feat_name].values()[0]['all_noisesrc_featval_array'])
        all_max = max(self.hist_data_dict[schema_name][feat_name].values()[0]['all_noisesrc_featval_array'])
        for class_dict in classname_list:
            for array_name in data_name_list:
                try:
                    cur_min = min(self.hist_data_dict[schema_name][feat_name][class_dict['class_name']][array_name])
                    if cur_min < all_min:
                        all_min = cur_min
                except:
                    pass
                try:
                    cur_max = max(self.hist_data_dict[schema_name][feat_name][class_dict['class_name']][array_name])
                    if cur_max > all_max:
                        all_max = cur_max
                except:
                    pass

        if max_val != None:
            # this makes some of the above work redundant, if this value is passed.
            all_max = max_val
        ######

                
        for class_dict in classname_list:
            ax = self.fig.add_subplot(class_dict['subplot_config_int'])
            ##### Noisified sources: #####
            try:
                n3, bins, patches = ax.hist(self.hist_data_dict[schema_name][feat_name][class_dict['class_name']]['all_noisesrc_featval_array'],
                                            50, log=1, range=(all_min, all_max),
                                            normed=0, facecolor='0.8', alpha=1.0, label='Noisified')
            except:
                ax.plot([all_min], [1], color="0.8", label='Noisified')

            ##### TCP / PTF sources which are classified as this schema:class with probability >= 90% #####
            #try:
            #    n1, bins, patches = ax.hist(self.hist_data_dict[schema_name][feat_name][class_dict['class_name']]['tcpsrc_featval_array'],
            #                                50, log=1, range=(all_min, all_max),
            #                                normed=0, facecolor='b', alpha=0.5, label='PTF classified',
            #                                rwidth=0.6)
            #except:
            #    ax.plot([all_min], [1], color='b', label='PTF classified')

            ##### JSB-vars (simbad, ...) TCP matching sources:
            #try:
            #    n2, bins, patches = ax.hist(self.hist_data_dict[schema_name][feat_name][class_dict['class_name']]['jsbvar_featval_lists']['all_featvals'],
            #                                50, log=1, range=(all_min, all_max),
            #                                normed=0, facecolor='y', alpha=0.75, label='JSBvar matching PTF',
            #                                rwidth=0.2)
            #except:
            #    ax.plot([all_min], [1], color='y', label='JSBvar matching PTF')
            
            ##### Original DotAstro sources: #####
            try:
                n2, bins, patches = ax.hist(self.hist_data_dict[schema_name][feat_name][class_dict['class_name']]['all_dotastro_featval_array'],
                                            50, log=1, range=(all_min, all_max),
                                            normed=0, facecolor="0.1", alpha=1.0, label='DotAstro.org',
                                            rwidth=0.3)
            except:
                ax.plot([all_min], [1], color='0.1', label='DotAstro.org')

            ##### (just symbols plotted for Noisified sources: #####
            #for ((dotastro_srcid, noise_float_id),feat_dict) in noisesrc_feat_dict.iteritems():
            #    if (feat_dict['feat_val'] <= max_featval_plotting_cut):
            #        ax.plot([feat_dict['feat_val']], [4], '^', color='g')


            plot_title = '\n'.join(self.related_classes_dict[schema_name][feat_name][class_dict['class_name']])
            if 'Cepheid' in plot_title:
                plot_title = 'Cepheid'
            elif 'RR Lyrae' in plot_title:
                plot_title = 'RR Lyrae'
            ax.annotate(plot_title, xy=(.5, 0.98), xycoords='axes fraction',
                        horizontalalignment='center',
                        verticalalignment='top', fontsize=self.font_size)

            if ((class_dict['subplot_config_int'] - 11) % 100) == 0:
                # Then we put a title for all plots
                full_title = "%s\n%s" % (schema_name, feat_name)
                #ax.annotate(full_title, xy=(.5, 1.35), xycoords='axes fraction',
                #            horizontalalignment='center',
                #            verticalalignment='top', fontsize=self.font_size+4)
                ax.legend()

            ##OLD##ax.set_title(class_name)
            new_feat_name = feat_name
            if feat_name == 'freq1_harmonics_freq_0':
                new_feat_name = 'Lomb Scargle 1st frequency (cycle/day)'
            elif feat_name == 'median_buffer_range_percentage':
                new_feat_name = 'Fraction of points within 10% of median magnitude'
            elif feat_name == 'skew':
                new_feat_name = 'Skew'
            ax.set_xlabel(new_feat_name)
            ax.set_ylim(1e-1, 1e3)
            #pyplot.grid(True)


    def generate_featval_relation_scatter_plot(self, classname_list=[], max_val=None, schema_name='', feat_name=''):
        """ This uses an previosly generated, internally stored structure which contains data
        for each science-class.  This data is used here to generate histograms as well
        as calculage min, max feat_val ranges.

        self.hist_data_dict[<schema>][<feat_name>][<science_class_name>] = {'noise_array':[], 'dotastro_array':[], 'tcpsrc_array':[]}

        This will call ax.hist(), ax.plot(), ax... functions.
        """
        ##### KLUDGE: Duplicated elsewhere:
        data_name_list = ['all_noisesrc_featval_array', 'all_dotastro_featval_array'] # 'tcpsrc_featval_array'
        all_min = min(self.hist_data_dict[schema_name][feat_name].values()[0]['all_noisesrc_featval_array'])
        all_max = max(self.hist_data_dict[schema_name][feat_name].values()[0]['all_noisesrc_featval_array'])
        for class_dict in classname_list:
            for array_name in data_name_list:
                try:
                    cur_min = min(self.hist_data_dict[schema_name][feat_name][class_dict['class_name']][array_name])
                    if cur_min < all_min:
                        all_min = cur_min
                except:
                    pass
                try:
                    cur_max = max(self.hist_data_dict[schema_name][feat_name][class_dict['class_name']][array_name])
                    if cur_max > all_max:
                        all_max = cur_max
                except:
                    pass

        if max_val != None:
            # this makes some of the above work redundant, if this value is passed.
            all_max = max_val
        ######

        for class_dict in classname_list:
            ax = self.fig.add_subplot(class_dict['subplot_config_int'])

            # TODO: join the lists into single arrays
            #   - make sure that the dotastro_featval array len() > 0 before appending either
            # plot.plot(arrays)

            dotastro_featvals_list = []
            noisified_featvals_list = []
            unmatched_noisified_featvals_list = []

            for src_id, src_dict in self.hist_data_dict[schema_name][feat_name] \
                                        [class_dict['class_name']]['dotastro_noise_relation_dicts'].iteritems():

                if len(src_dict['dotastro_featvals']) > 0:
                    dotastro_featvals_list.extend(src_dict['dotastro_featvals'] * len(src_dict['noisified_featvals']))
                    noisified_featvals_list.extend(src_dict['noisified_featvals'])
                else:
                    unmatched_noisified_featvals_list.extend(src_dict['noisified_featvals'])

            ax.plot(numpy.array(noisified_featvals_list), numpy.array(dotastro_featvals_list), 'x', color='r', markersize=5, label='DotAstro source matched')
            ax.plot(numpy.array(unmatched_noisified_featvals_list), numpy.array([numpy.median(unmatched_noisified_featvals_list)] * len(unmatched_noisified_featvals_list)), '+', color='g', markersize=8, label='DotAsro feature not calculated')

            plot_title = '\n'.join(self.related_classes_dict[schema_name][feat_name][class_dict['class_name']])
            ax.annotate(plot_title, xy=(.5, 0.98), xycoords='axes fraction',
                        horizontalalignment='center',
                        verticalalignment='top', fontsize=self.font_size)

            if ((class_dict['subplot_config_int'] - 11) % 100) == 0:
                # Then we put a title for all plots
                full_title = "%s\n%s" % (schema_name, feat_name)
                ax.annotate(full_title, xy=(.5, 1.35), xycoords='axes fraction',
                            horizontalalignment='center',
                            verticalalignment='top', fontsize=self.font_size+4)
                ax.legend()

            ax.set_xlabel(feat_name)
            ax.set_xlim(all_min, all_max)
            ax.set_ylim(all_min, all_max)
            pyplot.grid(True)


    #######
    def generate_featval_relation_compressed_plot(self, classname_list=[], min_val=None, max_val=None, schema_name='', feat_name=''):
        """ This uses an previosly generated, internally stored structure which contains data
        for each science-class.  This data is used here to generate histograms as well
        as calculage min, max feat_val ranges.

        self.hist_data_dict[<schema>][<feat_name>][<science_class_name>] = {'noise_array':[], 'dotastro_array':[], 'tcpsrc_array':[]}

        This will call ax.hist(), ax.plot(), ax... functions.
        """

        ##### KLUDGE: Duplicated elsewhere:
        data_name_list = ['all_noisesrc_featval_array', 'all_dotastro_featval_array'] # 'tcpsrc_featval_array'
        all_min = 0
        all_max = 0
        for class_dict in classname_list:
            for src_id, src_dict in self.hist_data_dict[schema_name][feat_name] \
                                        [class_dict['class_name']]['dotastro_noise_relation_dicts'].iteritems():

                if len(src_dict['dotastro_featvals']) > 0:
                    val_array = numpy.array(src_dict['noisified_featvals']) - src_dict['dotastro_featvals'][0]
                    try:
                        cur_min = min(val_array)
                        if cur_min < all_min:
                            all_min = cur_min
                    except:
                        pass
                    try:
                        cur_max = max(val_array)
                        if cur_max >  all_max:
                            all_max = cur_max
                    except:
                        pass

        if max_val != None:
            # this makes some of the above work redundant, if this value is passed.
            all_max = max_val
        if min_val != None:
            # this makes some of the above work redundant, if this value is passed.
            all_min = min_val
        ######

        for class_dict in classname_list:
            ax = self.fig.add_subplot(class_dict['subplot_config_int'])

            dotastro_featvals_list = []
            noisified_featvals_list = []
            unmatched_noisified_featvals_list = []

            plot_data_list = []
            for src_id, src_dict in self.hist_data_dict[schema_name][feat_name] \
                                        [class_dict['class_name']]['dotastro_noise_relation_dicts'].iteritems():

                if len(src_dict['dotastro_featvals']) > 0:
                    plot_data_list.append(numpy.array(src_dict['noisified_featvals']) - src_dict['dotastro_featvals'][0])

            try:
                n2, bins, patches = ax.hist(plot_data_list,
                                            50, log=0, range=(all_min, all_max),
                                            normed=0, alpha=0.75, label='DotAstro source matched',
                                            rwidth=1.0, histtype='barstacked') #THIS DOESNT WORK FOR .hist(): , colors=range(len(plot_data_list)), cmap=pyplot.cm.spectral
            except:
                print('EXCEPT: noisification_analysis.py:885, class_dict=', class_dict)
                #n2, bins, patches = ax.hist(plot_data_list[0],
                #                            50, log=0,
                #                            normed=0, facecolor='r', alpha=0.75, label='DotAstro source matched',
                #                            rwidth=1.0, histtype='barstacked')

                
            plot_title = '\n'.join(self.related_classes_dict[schema_name][feat_name][class_dict['class_name']])
            ax.annotate(plot_title, xy=(.5, 0.98), xycoords='axes fraction',
                        horizontalalignment='center',
                        verticalalignment='top', fontsize=self.font_size)

            if ((class_dict['subplot_config_int'] - 11) % 100) == 0:
                # Then we put a title for all plots
                full_title = "%s\n%s" % (schema_name, feat_name)
                ax.annotate(full_title, xy=(.5, 1.35), xycoords='axes fraction',
                            horizontalalignment='center',
                            verticalalignment='top', fontsize=self.font_size+4)
                ax.legend()

            ax.set_xlabel(feat_name)
            ax.set_xlim(all_min, all_max)
            #ax.set_ylim(all_min, all_max)
            #ax.set_ylim(1e-1, 1e3)
            pyplot.grid(True)

    #######

    def generate_distribution_plot_data(self, schema_name='',
                                class_name='',
                                feat_name='',
                                tcpsrc_feat_prob_dict={},
                                noisesrc_feat_dict={},
                                dotastro_src_feat_dict={},
                                jsbvar_src_feat_dict={},
                                all_related_classes=[],
                                subplot_config_int=111,
                                max_featval_plotting_cut=10):
        """ Generate a plot using data dicts generated for a specific
        (schema, class, feat_name)

        ##### NOTE:
        # tcpsrc_feat_prob_dict :: [src_id]:{'feat_val':, 'prob':}
        # noisesrc_feat_dict :: [(dotastro_srcid, noise_float_id)]:{'feat_val':}
        # dotastro_src_feat_dict :: [src_id]:<feat_val>

        """
        if schema_name not in self.hist_data_dict:
            self.hist_data_dict[schema_name] = {}
        if feat_name not in self.hist_data_dict[schema_name]:
            self.hist_data_dict[schema_name][feat_name] = {}
        if class_name not in self.hist_data_dict[schema_name][feat_name]:
            self.hist_data_dict[schema_name][feat_name][class_name] = {}


        if 'dotastro_noise_relation_dicts' not in self.hist_data_dict[schema_name][feat_name][class_name]:
            self.hist_data_dict[schema_name][feat_name][class_name]['dotastro_noise_relation_dicts'] = {} 

        if 'jsbvar_noise_relation_dicts' not in self.hist_data_dict[schema_name][feat_name][class_name]:
            self.hist_data_dict[schema_name][feat_name][class_name]['jsbvar_featval_lists'] = {'all_featvals':[]} 

        # Debug:
        #if (("RR Lyrae, Fundamental Mode" in all_related_classes)):
        #    print

        ##### Noisified sources: #####
        all_noisesrc_featval_list = []
        for ((dotastro_srcid, noise_float_id),feat_dict) in noisesrc_feat_dict.iteritems():
            #if not dotastrosrcid_featvals.has_key(dotastro_srcid):
            #    dotastrosrcid_featvals[dotastro_srcid] = []
            #dotastrosrcid_featvals[dotastro_srcid].append(feat_dict['feat_val'])
            all_noisesrc_featval_list.append(feat_dict['feat_val'])
            if dotastro_srcid not in self.hist_data_dict[schema_name][feat_name][class_name]['dotastro_noise_relation_dicts']:
                self.hist_data_dict[schema_name][feat_name][class_name]['dotastro_noise_relation_dicts'][dotastro_srcid] = {\
                            'dotastro_featvals':[],
                            'noisified_featvals':[]}
                    
            self.hist_data_dict[schema_name][feat_name][class_name] \
                     ['dotastro_noise_relation_dicts'][dotastro_srcid]['noisified_featvals'].append(feat_dict['feat_val'])
        self.hist_data_dict[schema_name][feat_name][class_name]['all_noisesrc_featval_array'] = numpy.array(all_noisesrc_featval_list)

        ##### TCP / PTF sources which are classified as this schema:class with probability >= 90% #####
        tcpsrc_featval_list = []
        for tcp_srcid, tcp_src_dict in tcpsrc_feat_prob_dict.iteritems():
            if ((tcp_src_dict['prob'] >= self.pars['prob_cut_for_plotting_of_tcpsrc']) and
                (tcp_src_dict['feat_val'] != None)):
                tcpsrc_featval_list.append(tcp_src_dict['feat_val'])
        self.hist_data_dict[schema_name][feat_name][class_name]['tcpsrc_featval_array'] = numpy.array(tcpsrc_featval_list)

        ##### Original DotAstro sources: #####
        all_dotastro_featval_list = []
        for (dotastro_srcid,feat_val) in dotastro_src_feat_dict.iteritems():
            #if not dotastrosrcid_featvals.has_key(dotastro_srcid):
            #    dotastrosrcid_featvals[dotastro_srcid] = []
            #dotastrosrcid_featvals[dotastro_srcid].append(feat_dict['feat_val'])
            if feat_val != None:
                all_dotastro_featval_list.append(feat_val)
                #ax.plot([feat_val], [3], 'o', color='r')
                if dotastro_srcid in self.hist_data_dict[schema_name][feat_name][class_name]['dotastro_noise_relation_dicts']:
                    self.hist_data_dict[schema_name][feat_name][class_name] \
                          ['dotastro_noise_relation_dicts'][dotastro_srcid]['dotastro_featvals'].append(feat_val)

        self.hist_data_dict[schema_name][feat_name][class_name]['all_dotastro_featval_array'] = numpy.array(all_dotastro_featval_list)

        ##### 
        ##### JSB-var astronomer classified sources (simbad...): #####
        jsbvar_featval_list = []
        for (tcp_srcid,feat_val) in jsbvar_src_feat_dict.iteritems():
            #if not dotastrosrcid_featvals.has_key(dotastro_srcid):
            #    dotastrosrcid_featvals[dotastro_srcid] = []
            #dotastrosrcid_featvals[dotastro_srcid].append(feat_dict['feat_val'])
            if feat_val != None:
                jsbvar_featval_list.append(feat_val)
                #ax.plot([feat_val], [3], 'o', color='r')
                #self.hist_data_dict[schema_name][feat_name][class_name]['jsbvar_featval_lists']\
                #                                                       ['all_featvals'].append(feat_val)

        self.hist_data_dict[schema_name][feat_name][class_name]['jsbvar_featval_lists']['all_featvals'] = \
                                                                              numpy.array(jsbvar_featval_list)
        

        #####

        # TODO: overplot real classified RR Lyrae or Cepheid sources
        #   - given  an identified source (ra,dec)? candidate.id?
        #   -> probably have some table which correlates
        #         user-classification with TCP srcid (and maybe confidences)

        
        ######
        # TODO:
        # For a noisification-scheme && a science-class && a feature
        #  - plot histogram of <number of noisified sources> vs <a features value range>
        #  - overplot DotAstro feature values (veritcal bar) marks.
        #     - use progen_srcidict to find corresponding DotAstro sources.
        #  - overplot resulting classified sources feature value
        #  - overplot known sources found features values
        

        #############################
        ##### EXAMPLE plotting code:
        #for dotastro_srcid, featval_list in dotastrosrcid_featvals.iteritems():
        #    featval_array = numpy.array(featval_list)
        #    pyplot.subplot(111)
        #    pyplot.plot(x, y, color=self.point_color_list[i_plot])
        #    pyplot.text(1.0, self.text_y, oplot_str)




    def plot_distribution_for_schema_class_feature(self, schema_name='', class_name='', feat_name='',
                                                   subplot_config_int=111, max_featval_plotting_cut=10):
        """ Generate a histogram plot of N vs <feature values> for a
        schema and science class.
        """
        feat_id = self.featname_lookup[feat_name]

        # TODO: These should all be methods in some Class/Object which is schema,class,featname specific:

        arff_maker = arffify.Maker()
        disambiguate_sci_class_dict = arff_maker.pars['disambiguate_sci_class_dict']

        # NOTE: unfortunately DotAstro.org has several names for similar science classes,
        #       so this kludge fix needs to be done:

        all_related_classes = []
        all_related_classes.append(class_name)
        if class_name in disambiguate_sci_class_dict:
            canonical_classname = disambiguate_sci_class_dict[class_name]
            if not canonical_classname in all_related_classes:
                all_related_classes.append(canonical_classname)
            for ambig_classname, associated_classname in disambiguate_sci_class_dict.iteritems():
                if associated_classname == canonical_classname:
                    if not ambig_classname in all_related_classes:
                        all_related_classes.append(ambig_classname)
        elif class_name in disambiguate_sci_class_dict.values():
            # kludgy:
            for k,v in disambiguate_sci_class_dict.iteritems():
                if class_name == v:
                    canonical_classname = k
                    if not canonical_classname in all_related_classes:
                        all_related_classes.append(canonical_classname)
                    #all_related_classes.append(class_name)

        if schema_name not in self.related_classes_dict:
            self.related_classes_dict[schema_name] = {}
        if feat_name not in self.related_classes_dict[schema_name]:
            self.related_classes_dict[schema_name][feat_name] = {}
        if class_name not in self.related_classes_dict[schema_name][feat_name]:
            self.related_classes_dict[schema_name][feat_name][class_name] = {}

        self.related_classes_dict[schema_name][feat_name][class_name] = all_related_classes
        #else:
        #    # No need to disambiguate the class name
        #    all_related_classes.append(class_name)

        # So, if the given some arbitrary class-name, we translate it to more generic class-name
        #    using the disambiguate_sci_class_dict{}
        #  - although, get_noisesrc_feat_dict() will need the specific classes?
        #      -> TODO: I need to pass a list of science class names into get_noisesrc_feat_dict()


        # This retrieves the tcp/ptf sources which match the schema_name, class_name:
        tcpsrc_feat_prob_dict = self.get_tcpsrc_feat_prob(schema_name=schema_name,
                                                          original_class_name=class_name,
                                                          feat_name=feat_name,
                                                          feat_id=feat_id,
                                                          all_related_classes=all_related_classes)

        # Retrieve the noisified sources and feature_vals:
        noisesrc_feat_dict = self.get_noisesrc_feat_dict(schema_name=schema_name,
                                                         original_class_name=class_name,
                                                         feat_name=feat_name,
                                                         feat_id=feat_id,
                                                         all_related_classes=all_related_classes)

        # Retrieves a {dotastro_src_id:feat_val} dict:
        dotastro_src_feat_dict = self.get_dotastro_src_feat_dict(schema_name=schema_name,
                                                                 original_class_name=class_name,
                                                                 feat_name=feat_name,
                                                                 feat_id=feat_id,
                                                                 all_related_classes=all_related_classes)
        # Retrieve JSB astronomer classified sources which match PTF/TCP sources:
        jsbvar_src_feat_dict = self.get_jsbvar_src_feat_dict(schema_name=schema_name,
                                                                 original_class_name=class_name,
                                                                 feat_name=feat_name,
                                                                 feat_id=feat_id,
                                                                 all_related_classes=all_related_classes)
                                                            
        # TODO: pass in & make use of jsbvar_src_feat_dict below:

        self.generate_distribution_plot_data(schema_name=schema_name,
                                     class_name=class_name,
                                     feat_name=feat_name,
                                     tcpsrc_feat_prob_dict=tcpsrc_feat_prob_dict,
                                     noisesrc_feat_dict=noisesrc_feat_dict,
                                     dotastro_src_feat_dict=dotastro_src_feat_dict,
                                     jsbvar_src_feat_dict=jsbvar_src_feat_dict,
                                     all_related_classes=all_related_classes,
                                     subplot_config_int=subplot_config_int,
                                     max_featval_plotting_cut=max_featval_plotting_cut)


    def plot_total_distribution_for_schema_class(self, schema_name='', class_name='', feat_name='',
                                                 subplot_config_int=111, max_featval_plotting_cut=10):
        """ Generate a histogram plot of N vs <feature values> for a
        schema and science class.
        """
        self.progen_srcdict = self.get_progen_srcdict()
        self.class_dotastro_lookup = self.get_class_dotastro_lookup(progen_srcdict=self.progen_srcdict)
        self.featname_lookup = self.get_featname_featid_lookup()

        self.plot_distribution_for_schema_class_feature(schema_name=schema_name,
                                                        class_name=class_name,
                                                        feat_name=feat_name,
                                                        subplot_config_int=subplot_config_int,
                                                        max_featval_plotting_cut=max_featval_plotting_cut)



if __name__ == '__main__':

    sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/feature_extract/MLData/'))
    import arffify # This is only used for getting the dictionary: Maker.pars['disambiguate_sci_class_dict']

    from IPython.kernel import client
    import matplotlib
    import matplotlib.pyplot as pyplot
    from matplotlib import rcParams
    #from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    import numpy

    pars = { \
        'show_plots':True,
        'all_progenitor_cutval':0.1, 
        'noisif_all_progenitor_list_fpath': \
                    '/home/pteluser/src/TCP/Software/Noisification/all_progenitor_class_list.txt',
        'dotastro_xmls_rootdir':'/home/pteluser/scratch/vosource_xml_writedir',
        'noisified_rootdir':'/home/pteluser/scratch/Noisification',
        'tablename_dotastro_feat_values':'source_test_db.dotastro_feat_values',
        'tablename_noise_gen_sources':'source_test_db.noise_sources',
        'tablename_featlookup':'source_test_db.feat_lookup',
        'tablename_featvalues':'source_test_db.feat_values',
        'tablename_one_src_model_class_probs':'source_test_db.one_src_model_class_probs',
        'tablename_jsbvars_lookup':'source_test_db.jsbvars_lookup',
        'filterid_featlookup_table':8,
        'prob_cut_for_plotting_of_tcpsrc':0.9, # probability for a science class must be >= to this percentage
        'font_size':7,
        'dpi':600,
        'figsize_tup':(6,3.5),
        'mysql_user':"pteluser", 
        'mysql_hostname':"192.168.1.25", 
        'mysql_database':'object_test_db', 
        'mysql_port':3306, 
        'tcp_to_jsbvar_classname':{'Classical Cepheid':['Cepheid'],
                                   'RR Lyrae, Fundamental Mode':['rrlyrae_ab','rrlyrae_c'],
                                   'Binary':['EB*','EB*WUMa']},
        }


    mec_str = """import os,sys
import time
import noisification_analysis
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/feature_extract'))
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/feature_extract/Code'))
from Code import *
from Code.generators_importers import from_xml
import db_importer
NoiseTaskPop = noisification_analysis.Noisification_Task_Populator()
NoiseTaskPop.establish_db_connection(host="%s",
                                     user="%s",
                                     db="%s",
                                     port=%d)
NoiseTaskPop.fill_featname_featid_lookup_dict(tablename_featlookup="%s", filterid_featlookup_table=%d)
""" % (pars['mysql_hostname'],
       pars['mysql_user'],
       pars['mysql_database'],
       pars['mysql_port'],
       pars['tablename_featlookup'],
       pars['filterid_featlookup_table'])
    IpythonController = Ipython_Controller(pars=pars)

    if 0:
        # DO THIS if running  in ipython parallel  mode:        
        IpythonController.initialize_mec(mec_str=mec_str)


    ###FOR TESTING:
    #     IpythonController.add_task(task_str=task_str)

    GSDotastroSourceFeatures = Generate_Store_Dotastro_Source_Features(pars=pars, \
                                                                       ipython_controller=IpythonController)

    ##### Done one time only:   To create TABLES
    #GSDotastroSourceFeatures.drop_tables()
    #GSDotastroSourceFeatures.create_tables()
    #sys.exit()

    ##### This is called to populate or update the dotastro_feat_values TABLE.
    #       This is done occasionally, as new features are added or updated.
    #GSDotastroSourceFeatures.populate_update_dotastro_feat_values_table()


    #science_class = "W Ursae Majoris"
    #feat_name = "skew"
    #schema_name = "50nois_00epch_010need_0.100mtrc_per900ep10day_explombfreq_expnoisefreq"
    #schema_name = "50nois_20epch_010need_0.100mtrc_surveynoise_linearlombfreq"
    schema_name = "50nois_00epch_010need_0.100mtrc_per900ep10day_linearlombfreq_expnoisefreq"

    ##### This fills a table with the features of noisified sources 
    #     for a schema_id.
    #NOTE: this assumes Ipython-parallel is being used:
    #GSDotastroSourceFeatures.add_noisified_sources_to_tables(scheam_name=schema_name)
    #sys.exit()


    #NOTE: There are no classes in all_progenitor_class_list.txt for classes:
    #         "RR Lyrae, Fundamental Mode"
    #science_class = "Double mode RR-Lyrae stars"  # "Classical Cepheids" # 

    #featname_list = [{'feat_name':'skew',
    #                  'reln_max_val':None,
    #                  'difference_min_val':None,
    #                  'difference_max_val':None,
    #                  'hist_max_val':None}]

    #"""
    featname_list = [{'feat_name':'ws_variability_self',
                      'reln_max_val':5000000,
                      'difference_min_val':-1e6,
                      'difference_max_val':None,
                      'hist_max_val':5000000},
                     {'feat_name':'freq1_harmonics_freq_0',
                      'reln_max_val':8.5,
                      'difference_min_val':-0.01,
                      'difference_max_val':0.01,
                      'hist_max_val':None},
                     {'feat_name':'freq2_harmonics_freq_0',
                      'reln_max_val':None,
                      'difference_min_val':-0.02,
                      'difference_max_val':0.02,
                      'hist_max_val':None},
                     {'feat_name':'freq3_harmonics_freq_0',
                      'reln_max_val':None,
                      'difference_min_val':-0.02,
                      'difference_max_val':0.02,
                      'hist_max_val':150},
                     {'feat_name':'freq1_harmonics_amplitude_0',
                      'reln_max_val':None,
                      'difference_min_val':None,
                      'difference_max_val':None,
                      'hist_max_val':5},
                     {'feat_name':'freq_signif',
                      'reln_max_val':None,
                      'difference_min_val':None,
                      'difference_max_val':None,
                      'hist_max_val':None},
                     {'feat_name':'median_buffer_range_percentage',
                      'reln_max_val':None,
                      'difference_min_val':None,
                      'difference_max_val':None,
                      'hist_max_val':None},
                     {'feat_name':'freq1_harmonics_peak2peak_flux',
                      'reln_max_val':None,
                      'difference_min_val':None,
                      'difference_max_val':0.2,
                      'hist_max_val':5},
                     {'feat_name':'skew',
                      'reln_max_val':None,
                      'difference_min_val':None,
                      'difference_max_val':None,
                      'hist_max_val':None}]
    #"""

    classname_list = [{'class_name':"Beta Persei",
                       'subplot_config_int':711},
                      {'class_name':"Binary",
                       'subplot_config_int':712},
                      {'class_name':"W Ursae Majoris",
                       'subplot_config_int':713},
                      {'class_name':"Beta Lyrae",
                       'subplot_config_int':714},
                      {'class_name':"RR Lyrae, Fundamental Mode",
                       'subplot_config_int':715},
                      {'class_name':"Classical Cepheids, Symmetrical",
                       'subplot_config_int':716},
                      {'class_name':"Delta Scuti",
                       'subplot_config_int':717}]

    if 1:
        ### For smaller ADASS paper plot:


        featname_list = [{'feat_name':'freq1_harmonics_freq_0',
                      'reln_max_val':8.5,
                      'difference_min_val':-0.01,
                      'difference_max_val':0.01,
                      'hist_max_val':9},
                     {'feat_name':'median_buffer_range_percentage',
                      'reln_max_val':None,
                      'difference_min_val':None,
                      'difference_max_val':None,
                      'hist_max_val':0.7},
                     {'feat_name':'skew',
                      'reln_max_val':None,
                      'difference_min_val':None,
                      'difference_max_val':None,
                      'hist_max_val':2}]

        classname_list = [{'class_name':"W Ursae Majoris",
                       'subplot_config_int':311},
                      {'class_name':"RR Lyrae, Fundamental Mode",
                       'subplot_config_int':312},
                      {'class_name':"Classical Cepheids, Symmetrical",
                       'subplot_config_int':313}]



    else:
        sys.exit()


    for featname_dict in featname_list:
        hist_fpath = "/tmp/noise_analysis_hist_" + featname_dict['feat_name'] + ".eps"
        featval_relation_fpath = "/tmp/noise_analysis_featval_relation_" + featname_dict['feat_name'] + ".eps"
        compressed_fpath = "/tmp/noise_analysis_featval_compressed_" + featname_dict['feat_name'] + ".eps"

        GSDotastroSourceFeatures.initialize_plot(font_size=pars['font_size'], dpi=pars['dpi'], figsize_tup=pars['figsize_tup'])
        for class_dict in classname_list:
            GSDotastroSourceFeatures.plot_total_distribution_for_schema_class(schema_name=schema_name,
                                                                          class_name=class_dict['class_name'],
                                                                          feat_name=featname_dict['feat_name'],
                                                                          subplot_config_int=class_dict['subplot_config_int'],
                                                                          max_featval_plotting_cut=5000000)
        GSDotastroSourceFeatures.generate_hist_plot(classname_list=classname_list, max_val=featname_dict['hist_max_val'], schema_name=schema_name,feat_name=featname_dict['feat_name'])
        GSDotastroSourceFeatures.save_plot(fpath=hist_fpath)
        #######
        #pyplot.clf()
        #GSDotastroSourceFeatures.generate_featval_relation_scatter_plot(classname_list=classname_list, max_val=featname_dict['reln_max_val'], schema_name=schema_name,feat_name=featname_dict['feat_name'])
        #GSDotastroSourceFeatures.save_plot(fpath=featval_relation_fpath)
        #######
        #pyplot.clf()
        #GSDotastroSourceFeatures.generate_featval_relation_compressed_plot(classname_list=classname_list, min_val=featname_dict['difference_min_val'], max_val=featname_dict['difference_max_val'], schema_name=schema_name,feat_name=featname_dict['feat_name'])
        #GSDotastroSourceFeatures.save_plot(fpath=compressed_fpath)

    """
SELECT count(*) AS n_noised, avg(1./feat_val) AS per_avg, std(1./feat_val) AS per_std, class_name FROM source_test_db.noise_sources WHERE schema_name="70nois_00epch_010need_0.100mtrc_per900ep10day_lessfeats_updlomb" AND feat_id=1718 GROUP BY class_name ORDER BY n_noised DESC;
+----------+---------+----------+----------------------------------------------------------+
| n_noised | per_avg | per_std  | class_name                                               |
+----------+---------+----------+----------------------------------------------------------+
| g     96 |  0.1492 |   0.0180 | W Ursae Majoris                                          | 
| g     49 |   3.246 |    0.993 | Classical Cepheids, Symmetrical                          | 
| X     38 |  0.7927 |      1.4 | Mira Variables                                           | 
|       29 |   2.699 |     1.17 | Eclipsing binaries, subtypes EB                          | 
|       28 |  0.6865 |    0.631 | Beta Persei                                              | 
|       21 |   3.323 |     2.00 | Eclipsing binaries, subtypes EA                          | 
|       20 |   3.817 |    0.844 | Eclipsing binaries, subtypes EW                          | 
|       13 |  0.2117 |   0.0697 | Delta-Scuti stars                                        | 
|       13 |   2.759 |    0.992 | Eclipsing Binary Systems                                 | 
|       11 | 0.04597 |   0.0529 | Contact Systems                                          | 
|       10 |  0.6002 |    0.417 | Beta Lyrae                                               | 
| g     10 |   2.694 |     0.42 | Multiple Mode Cepheid                                    | 
|        8 |  0.4850 |    0.806 | Beta Cephei, massive, rapidly rotating, multiperiodicity | 
| g      7 |    3.69 |    0.534 | Cepheid Variable                                         | 
|        6 |  0.7370 |    0.247 | Ellipsoidal variables                                    | 
|        6 |  0.0602 | 1.919334 | HADS                                                     | 
|        5 |  0.1812 |   0.0301 | Beta-Cephei stars                                        | 
| g      5 |   4.421 |   0.0531 | Double-mode Cepheids                                     | 
|        5 |   1.698 |    0.449 | Gamma-Doradus stars                                      | 
| g      4 |  0.3266 | 6.009242 | RR Lyrae - Near Symmetric                                | 
|        3 |  0.4112 | 0.000168 | Algol, semidetached, pulsating component                 | 
| g      3 |  0.3173 |   0.0303 | RR Lyrae - First Overtone                                | 
|        3 |  0.1473 |   0.0695 | Wolf-Rayet stars                                         | 
| g      2 |   4.160 |   0.0255 | Classical Cepheid Multiple Modes Symmetrical             | 
|        2 |   3.757 |     3.73 | Be Star                                                  | 
| g      2 |   0.552 | 0.000458 | RR-Lyrae stars, subtype ab                               | 
|        1 | 0.03337 |          | Semi-regular variables                                   | 
|        1 |   0.104 |          | Pulsating Subdwarf                                       | 
|        1 |   4.564 |          | Classical Cepheids                                       | 
+----------+---------+----------+----------------------------------------------------------+
29 rows in set (0.07 sec)

SELECT count(src_id) AS n_srcs, class_name FROM source_test_db.one_src_model_class_probs WHERE schema_comment="70nois_00epch_010need_0.100mtrc_per900ep10day_lessfeats_updlomb" AND class_rank=0 AND prob >= 0.9 GROUP BY class_name ORDER BY n_srcs DESC;
+--------+----------------------------+
| n_srcs | class_name                 |
+--------+----------------------------+
|     93 | Algol (Beta Persei)        | 
|     66 | Binary                     | 
|     49 | W Ursae Majoris            | 
|     30 | Beta Lyrae                 | 
|     27 | RR Lyrae, Fundamental Mode | 
|     12 | Delta Scuti                | 
|      8 | Symmetrical                | 
|      1 | Mira                       | 
+--------+----------------------------+
8 rows in set (0.02 sec)

    """
