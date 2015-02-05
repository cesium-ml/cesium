#!/usr/bin/env python
"""
classification_interface.py

   v0.2 Interfaces with plugin_classifier.py, which does all science
        classification when given a list of VOSource XML strings of filepaths.
   v0.1 Module to be called by testsuite/ingest_tools and used as interface
        to source science classification tables.  To be used for classification
        generation & table population.

PDB Command:
   /usr/lib/python2.5/pdb.py classification_interface.py

NOTE: need srcid "index server" running:
           "feat_class_srcid_groups" case in obj_id_sockets.py


TODO: Have index server which sends a list of source-ids to client which are
     reserved for the client to extract features and classify.
     - index server retrieves sources by retrieving 100k srcids with max(nobjs)
     - index server then iterates & sends (100) srcids to each requesting client
     - when 100k sources have had feats & classes made, index server retrieves
         another 100k srcids

TODO: Feature & classification client:
     - retrieve 100 srcids from <index server>
     - Method similar to get_features_for_most_sampled_sources_client_loop()
         except for unfeated_srcid_list[] coming from <index server>
     - But: do MySQL INSERT/UPDATE in all-srcid **batches**:
         - update_featsgen_in_srcid_lookup_table()
         - insert_srclist_features_into_rdb_tables()
     - Also: do classification of srcid & INSERT/UPDATE in all-srcid batches

"""
from __future__ import print_function
from __future__ import absolute_import
import sys, os
from . import ingest_tools
from . import plugin_classifier
try:
    import MySQLdb
except:
    pass
#import io  # for passing vosource xml strings to mlens3 code as fp's
from numpy import random, zeros

#sys.path.append(os.environ.get("TCP_DIR") + '/Software/feature_extract/MLData')
#import arffify

sys.path.append(os.environ.get("TCP_DIR") + '/Software/feature_extract/Code')
import db_importer

local_pars = {}
pars = ingest_tools.pars
pars.update(local_pars)

class Classification_Tables_Interface:
    """ Class which provides an interface to the source science-class
    MySQL tables.  Handles connection to RDB, INSERT/UPDATE, basic SELECTs.
    """
    def __init__(self, pars, db=None):
        self.pars = pars
        if db is None:
            self.db = MySQLdb.connect(host=self.pars['classdb_hostname'], \
                                  user=self.pars['classdb_username'], \
                                  db=self.pars['classdb_database'], \
                                  port=self.pars['classdb_port'])
        else:
            self.db = db
        self.cursor = self.db.cursor()
        

        # I think this is OBSOLETE (it's unfinished at least):
    def insert_arff_classes_into_class_db(self, arff_master_list):
        """ Using classes extracted from VOSource.xml strings or WEKA/ML
        generation, insert into class RDB Table.
        """

        # TODO: populate_feat_db_using_TCPTUTOR_sources.threaded_get_features_populate_rdb()
        #    - This can be passed schema_id which was generated earlier
        #    - This iterates over srcids for each TUTOR source.
        #    ??? does this method know class-ids for each TUTOR source?
        #       - this will have to be queried from the TUTOR database
        #       -> or maybe get class from (other code which querries the TUTOR database to get unique sources and their associated classes)

        insert_list = ["INSERT INTO src_class_probs () VALUES "]

        for source_elem in arff_master_list:
            insert_list.append("(%d, %s, '%s', '%s', %d, NOW()), " % (source_elem['num'], source_elem['class']))
        

        self.cursor.execute(''.join(insert_list)[:-2])

# Is this obsolete? :
class Source_Feature_Class_Generator:
    """ Class which deals with generating features and classes for sources.
    """
    def __init__(self, pars):
        from . import obj_id_sockets
        #import numpy # to get a random number, but also used in feature code

        #f = open('testsuite.transx_production_configs.par.py')
        f = open('testsuite.par.py')# Import params from testsuite, which
        #                             allows 127.0.0.1 test configs.
        exec f
        f.close()
        self.pars = parameters['ingest_tools_pars']
        self.pars.update(pars)

        htm_tools = ingest_tools.HTM_Tools(self.pars)
        rcd = ingest_tools.RDB_Column_Defs(\
                    rdb_table_names=self.pars['rdb_table_names'], \
                    rdb_db_name=self.pars['rdb_name_2'], \
                    col_definitions=ingest_tools.new_rdb_col_defs)
        rcd.init_generate_mysql_strings(self.pars)

        rdbt = ingest_tools.Rdb_Tools(self.pars, rcd, htm_tools, \
                    rdb_host_ip=self.pars['rdb_host_ip_2'], \
                    rdb_user=self.pars['rdb_user'], \
                    rdb_name=self.pars['rdb_name_2'])

        sdss_fcr_iso = ingest_tools.SDSS_FCR_Ingest_Status_Object(\
                    rdb_host_ip=self.pars['rdb_host_ip_3'], \
                    rdb_user=self.pars['rdb_user'], \
                    rdb_name=self.pars['rdb_name_3'], \
                    table_name=self.pars['sdss_fields_table_name'], \
                    sdss_fields_doc_fpath_list=self.pars['sdss_fields_doc_fpath_list'],\
                    hostname=self.pars['hostname'])

        srcdbt = ingest_tools.Source_Database_Tools(self.pars, rcd, htm_tools, \
                    rdb_host_ip=self.pars['rdb_host_ip_4'], \
                    rdb_user=self.pars['rdb_user_4'],\
                    rdb_name=self.pars['rdb_name_4'])
        slfits_repo = ingest_tools.SDSS_Local_Fits_Repository(self.pars)
        cur_pid = str(os.getpid())
        tcp_runs = ingest_tools.TCP_Runtime_Methods(cur_pid=cur_pid)

        self.xrsio = ingest_tools.XRPC_RDB_Server_Interface_Object(self.pars, tcp_runs, rdbt, htm_tools, srcdbt, sdss_fcr_iso, slfits_repo)

        #arffify_path = os.environ.get("TCP_DIR") + \
        #                                     '/Software/feature_extract/MLData'
        #sys.path.append(arffify_path)
        #import arffify

        # TODO: this file should only be stored in memory-disk-partition
        # TODO: this file should be deleted after read/use.
        out_fpath = "/tmp/temp_%s_%d.arff" % (cur_pid, \
                                                    random.randint(0,100000000))
        self.arffmaker = arffify.Maker(search=[], outfile=out_fpath, \
                                skip_class=True, local_xmls=True, dorun=False)

        self.socket_client = obj_id_sockets.socket_client({},\
                                          server_type='feat_class_srcid_groups')
        #feat_class_srcid_index_server_pars = {}
        #if len(feat_class_srcid_index_server_pars) == 0:
        #    # Default case where no explicit index socket server params given
        #    socket_client = obj_id_sockets.socket_client({},\
        #                                 server_type='feat_class_srcid_groups')
        #else:
        #    socket_client = obj_id_sockets.socket_client( \
        #                                    feat_class_srcid_index_server_pars)


    def main(self, class_tbl_intf):
        """ Source_Feature_Class_Generator main method.
        - Retrieves src_ids which are to have features generated & classes made
           - These src_ids are reserved for this client to generate feats,class
        - Generates features for each source
        - Generates VOSource.xml (just file pointers/strings)
            - which are then used to generate a .arff file
        - classifies the sources using command line weka
        - extracts the source classification from weka output
        - stores all source classifications and features in a couple large
            MySQL INSERT/UPDATEs

        """
        # First we get a list of SDSS sources which need features generated:
        srcid_list = self.socket_client.get_feat_class_srcid_group()

        # Generate features & insert into RDB:
        srcid_xml_tuple_list = self.xrsio.get_features_for_most_sampled_sources_client_loop(srcid_list=srcid_list)

        # Using the given VOSource xml_strings, This fills structures with
        #     source, class, feature info for .ARFF generation:
        self.arffmaker.populate_features_and_classes_using_local_xmls(\
                                      srcid_xml_tuple_list=srcid_xml_tuple_list)
        #if 1:
        #    self.arffmaker.write_arff()
            
        # TODO:
        # if flagged to generate science classes (SDSS):
        #     self.arffmaker.write_arff()
        #     execute WEKA on arrf, get classes
        # else
        #     extract classes from srcid_xml_tuple_list's XML classes


        # Seems a little KLUDGY, using two external classes here:
        class_tbl_intf.insert_arff_classes_into_class_db(self.arffmaker.master_list)


# 20080926 : This class created to handle various classification schemes:

class ClassificationHandler:
    """ This class handles executing classification algorithms and inserting
    into classification tables.  Initially parses VOSource XML which contain
    features.
    """
    def __init__(self, pars, use_database=True, use_weka_jvm=True,
                 class_abrv_lookup={}, db=None, class_schema_definition_dicts={}):
        self.pars = pars

        #arffify_path = os.environ.get("TCP_DIR") + \
        #                                     '/Software/feature_extract/MLData'
        #sys.path.append(arffify_path)
        #import arffify
        #self.arffmaker = arffify.Maker(search=[], \
        #                        skip_class=True, local_xmls=True, dorun=False, \
        #                        class_abrv_lookup=class_abrv_lookup)

        if use_database:
            self.class_interface = Classification_Tables_Interface(pars, db=db)

        #NOTE: This dict is used in the following method:
        if len(class_schema_definition_dicts) > 0:
            self.class_schema_definition_dicts = class_schema_definition_dicts
        else:
            self.class_schema_definition_dicts = \
                                      self.pars['class_schema_definition_dicts']

        # NOTE: there might be multiple schema dicts, for:
        #  (1) Arff/weka classification
        #  (2) Dovi/Nat "Berkeley Astronomer" defined classification
        #  (3) some other classification scheme which also is done in parallel
        #  ....

        # Weka class-schema case:
        #weka_defs = self.class_schema_definition_dicts['WEKA full']

        class_schema_name_list = self.class_schema_definition_dicts.keys()
        class_schema_name_list.remove('mlens3 MicroLens')
        class_schema_name_list.remove('Dovi SN')
        class_schema_name_list.remove('General')
        for class_schema_name in class_schema_name_list:
            weka_defs = self.class_schema_definition_dicts[class_schema_name]

            (classname_colnum_dict, features_list, classes_arff_str) = \
                                         self.get_classdict_featureslist_from_arff(\
                                              weka_defs['weka_training_arff_fpath'])
            weka_defs['classes_arff_str'] = classes_arff_str
            weka_defs['classname_colnum_dict'] = classname_colnum_dict
            weka_defs['class_list'] = weka_defs['classname_colnum_dict'].values()
            weka_defs['n_features'] = len(features_list)
            weka_defs['features_list'] = features_list
            #self.training_arff_features_list = features_list #KLUDGEY
            if use_database:
                self.get_create_classid_schemaid_dict(weka_defs)


        self.PlugClass = plugin_classifier.PluginClassifier( \
                            class_schema_definition_dicts=self.pars['class_schema_definition_dicts'],\
                            class_abrv_lookup=class_abrv_lookup, \
                            use_weka_jvm=use_weka_jvm, \
                            training_arff_features_list=features_list) # NOTE: this last arg is becoming obsolete.

        # # # # # #
        # # # # # #
        # TODO: I think I need to do the above bit also for other eka instances, and then do the below bit too.
        # NOTE: a problem is that self.PluginClass wants training_arff_features_list=features_list
        #     - but this changes for different weka cases have different ['weka_training_arff_fpath']


        if use_database:
            # Specific class-schema cases:
            self.get_create_classid_schemaid_dict(\
                      self.class_schema_definition_dicts['mlens3 MicroLens'])
            self.get_create_classid_schemaid_dict(\
                      self.class_schema_definition_dicts['Dovi SN'])
        

    def get_classdict_featureslist_from_arff(self, weka_training_arff_fpath):
        """ Parse the classes and features from Weka .arff file header and
        return in structures.
        """
        lines = open(os.path.expandvars(weka_training_arff_fpath)).readlines()

        feature_line_list = []
        for line in lines:
            if line[:10].lower() == '@attribute':
                feature_line_list.append(line)
            elif line[:5].lower() == '@data':
                break # no more features/classes to read

        assert(feature_line_list[-1][:17].lower() == '@attribute class ')
        classes_arff_str = feature_line_list[-1]
        classname_colnum_dict = self.build_classname_colnum_dict(classes_arff_str)
        features_list = []
        for line in feature_line_list[:-1]:
            feature_name = line.split()[1]
            features_list.append(feature_name)

        return (classname_colnum_dict, features_list, classes_arff_str)


    def get_create_classid_schemaid_dict(self, class_schema_definition):
        """ This retrieves from the src_class_probs RDB table and forms
        a dictionary containing RDB {class_id:class_names}
        as well as the classification schema_id which is associated with the
        classification scheme referenced in the input class_schema_define_dict.

        If there exists no existing schema_id:class_ids in the RDB, these
        are generated and added to the src_class_probs table in RDB.

        The resulting structures are added to the class_schema_definition_dicts.
        """
        class_schema_definition['n_classes'] = \
                                      len(class_schema_definition['class_list'])
        #class_schema_definition['n_features'] = \
        #                                  class_schema_definition['n_features']

        # Need to see whether this class schema exists in RDB. if no: add it.
        #select_str = "SELECT class_name,class_id FROM %s WHERE schema_id=%d AND schema_n_feats=%d AND schema_n_classes=%d" % \
        select_str = "SELECT class_name,class_id FROM %s WHERE schema_comment='%s' AND schema_n_feats=%d AND schema_n_classes=%d" % \
                               (self.pars['classid_lookup_tablename'], 
                                class_schema_definition['schema_comment'],
                                class_schema_definition['n_features'],
                                class_schema_definition['n_classes'])
        self.class_interface.cursor.execute(select_str)

        results = self.class_interface.cursor.fetchall()
        if len(results) > 0:
            # This class schema already exists.
            class_schema_definition['class_name_id_dict'] = {}
            for result in results:
                class_schema_definition['class_name_id_dict'][result[0]] = \
                                                                       result[1]
        else:
            # We need to add a new schema to RDB.
            # get the highest schema_id in RDB
            ### 20090420: dstarr comments this out since it seems smarter to just use schema-ids which are hard-coded in ingest_tools.py..par{}:
            """
            select_str = "SELECT max(schema_id) FROM %s" % \
                               (self.pars['classid_lookup_tablename'])
            self.class_interface.cursor.execute(select_str)
            results = self.class_interface.cursor.fetchall()
            if results[0][0] is None:
                class_schema_definition['schema_id'] = 0
            else:
                class_schema_definition['schema_id'] = results[0][0] + 1
            """
            # TODO: I need to generate class ids for all class names
            class_schema_definition['class_list'].sort()# not neccisary but nice
            
            insert_list = ["INSERT INTO %s (schema_id, class_id, class_name, schema_n_feats, schema_n_classes, schema_comment, schema_dtime) VALUES " % (self.pars['classid_lookup_tablename'])]
            class_schema_definition['class_name_id_dict'] = {}
            for i in xrange(len(class_schema_definition['class_list'])):
                class_name = class_schema_definition['class_list'][i]
                class_schema_definition['class_name_id_dict'][class_name] = i
                insert_list.append("(%d, %d, '%s', %d, %d, '%s', NOW()), " % \
                                   (class_schema_definition['schema_id'], i,
                                    class_name,
                                    class_schema_definition['n_features'],
                                    class_schema_definition['n_classes'],
                                    class_schema_definition['schema_comment']))
            #self.class_interface.cursor.execute(''.join(insert_list)[:-2])
            # 20091023: dstarr adds on duplicate update...:
            if len(insert_list) > 1:
                self.class_interface.cursor.execute(''.join(insert_list)[:-2] + " ON DUPLICATE KEY UPDATE class_name=VALUES(class_name), schema_comment=VALUES(schema_comment), schema_dtime=VALUES(schema_dtime)")


    def build_classname_colnum_dict(self, classes_arff_str):
        """ This builds a dictionary of {column_number:class_name} which
        is used in parsing weka classification results.
        """
        comma_seperated_str = classes_arff_str[classes_arff_str.find('class')+6:].strip()[1:-1]
        #obsolete:
        #raw_classname_list = comma_seperated_str.split(',')

        # KLUDGE: Here is a custom parsing of WEKA class attribute string which
        #    may or may not contain quotes, and which may have string elements
        #    with "," in them.
        # NOTE: This makes the assumption that class_names with "," in them only
        #    occur within single quotes
        temp_list = []
        shortening_str = comma_seperated_str
        do_parse = True
        while do_parse:
            if len(shortening_str) <= 2:
                do_parse = False
                break
            if shortening_str[0] == "'":
                if "," in shortening_str:
                    i_fin = shortening_str.find("'", 1)
                else:
                    i_fin = len(shortening_str)
                temp_list.append(shortening_str[1:i_fin].strip("'"))
                shortening_str = shortening_str[i_fin+2:] # skip "',"
                #for elem in temp_list:
                #    print '!', elem
                #print shortening_str
            else:
                if "," in shortening_str:
                    i_fin = shortening_str.find(",")
                else:
                    i_fin = len(shortening_str)
                temp_list.append(shortening_str[:i_fin])
                shortening_str = shortening_str[i_fin+1:]
                #for elem in temp_list:
                #    print '!', elem
                #print shortening_str
                

        # debug:
        #for elem in temp_list:
        #    print '!', elem

        #print comma_seperated_str
        #print
        #temp_list = []
        #for raw_classname in raw_classname_list:
        #    if "'" in raw_classname:
        #        temp_list.append(raw_classname.strip("'"))
        #    else:
        #        temp_list.append(raw_classname)

        classname_colnum_dict = {}
        for i in xrange(len(temp_list)):
            classname_colnum_dict[i] = temp_list[i]
        
        return classname_colnum_dict


    def classify_and_parse_using_weka_model(self, arff_fpath, model_fpath='',
                                            class_path='',
                                            schema_str='WEKA full'):
        """ Perform WEKA classification using data-arff and trained .model file.
        Parse the results into a structure.

        Weka Model building is done using a command like:
        java weka.classifiers.trees.J48 -t /home/dstarr/src/TCP/Data/TUTOR_sources_20080708_45class.arff -d test-J48.model

        NOTE: Java CLASSPATH environment variable is needed for Weka:
           e.g.:
        export CLASSPATH='/home/dstarr/src/install/weka-3-5-7/weka.jar'
        BUT, here we hardcode it into the weka system call.  
        """

        if len(class_path) > 0:
            classpath_str = '-classpath %s' % (class_path)
        else:
            classpath_str = ''

        exec_str = \
          "java %s weka.classifiers.trees.J48 -T %s -l %s -p 0 -distribution"%(\
                                         classpath_str, arff_fpath, model_fpath)

        class_prob_list = [] # will contain [(class_name,prob_float), ...] in order of highest probability first.

        (a,b,c) = os.popen3(exec_str)
        stdout_lines = b.readlines()
        for line in stdout_lines[1:-1]:
            classindex_prob_list = line.split()[-1].replace('*','').split(',')

            prob_index_tup_list = []
            for i in xrange(len(classindex_prob_list)):
                prob = float(classindex_prob_list[i])
                if prob > 0:
                    prob_index_tup_list.append((prob,i))

            prob_index_tup_list.sort()
            prob_index_tup_list.reverse() # The first element has highest prob

            class_prob_list_for_a_source = []
            for prob,i in prob_index_tup_list:
                class_prob_list_for_a_source.append((self.class_schema_definition_dicts[schema_str]['classname_colnum_dict'][i], prob))
            class_prob_list.append(class_prob_list_for_a_source)
        a.close()
        b.close()
        c.close()
        return class_prob_list


    # OBSOLETE (this function is now contained in plugin_classifier.py):
    def get_class_probs_using_jvm_weka_instance(self, vosource_list):
        """ Use an already-instantiated Java JVM to run weka classification.
        Format the results.

        RETURN: class_probs_dict = {} # {src_id:[{'schema_id':'', 'class_id':'', 'prob':'', 'class_rank':'', 'prob_weight':''}]}
        """
        self.arffmaker.populate_features_and_classes_using_local_xmls(\
                                             srcid_xml_tuple_list=vosource_list)

        new_master_features_list = []
        master_features_dict = dict(self.arffmaker.master_features) # KLUDGE: this makes a dictionary from a list of tuples.
        for feat_name in self.training_arff_features_list:
            new_master_features_list.append((feat_name,
                                             master_features_dict[feat_name]))
        ### This doesn't preserve the feature list order in the training .arff:
        #for feat_name,feat_type in self.arffmaker.master_features:
        #    if feat_name in self.training_arff_features_list:
        #        new_master_features_list.append((feat_name,feat_type))
        self.arffmaker.master_features = new_master_features_list

        # TODO: extract these features from the vosource:
        #      (should be similar to methods used when makeing a temp .arff file)
        #arff_record = [0.65815,3.518955,0.334025,0.79653,44.230391,3.163003,0.025275,0.004501,0.295447,-0.133333,3.144411,-0.65161,None,None]
        #classified_result = self.wc.get_class_distribution(arff_record)
        #print classified_result

        prob_weight = 1.0 # This property may be used in Nat/Dovi to represent
        #             science classes which are known to be non applicable (0.0)
        class_probs_dict = {}
        for obj in self.arffmaker.master_list:
            #if remove_sparse_classes:
            #    if not obj.get('class','') in self.arffmaker.master_classes:
            #    continue # skip this object due to being in a sparse class
            #tmp = []
            src_id = obj['num']
            class_probs_dict[src_id] = []
            arff_record = []

	    for fea in self.arffmaker.master_features:
	    	val = None
	    	if fea in obj['features']:
	    		str_fea_val = str(obj['features'][fea])
	    		if ((str_fea_val == "False") or 
	    		    (str_fea_val == "inf") or
	    		    (str_fea_val == "nan") or
	    		    (str_fea_val == "None")):
	    			val = None
	    		elif fea[1] == 'float':
	    			val = obj['features'][fea] # str_fea_val
	    		else:
	    			val = "%s" % str_fea_val # """'%s'""" % str_fea_val
                arff_record.append(val)

            # 20090130 old:
            #for fea in self.arffmaker.master_features:
            #    val = None # "?"
            #    if obj['features'].has_key(fea):
            #        if fea[1] == 'float':
            #            if ((obj['features'][fea] == "False") or 
            #                (str(obj['features'][fea]) == "inf") or
            #                (str(obj['features'][fea]) == "nan")):
            #                val = None # "?"
            #            elif obj['features'][fea] != None:
            #                val = obj['features'][fea] #val = str(obj['features'][fea])
            #        else:
            #            val = """'%s'""" % str(obj['features'][fea])
            #    arff_record.append(val)

            classified_result = self.wc.get_class_distribution(arff_record)
            #print src_id, classified_result
            for i, (class_name,class_prob) in enumerate(classified_result[:3]):
                class_id = self.class_schema_definition_dicts['WEKA full']['class_name_id_dict'][class_name]
                class_probs_dict[src_id].append(\
                                 {'schema_id':self.class_schema_definition_dicts['WEKA full']['schema_id'],
                                  'class_id':class_id,
                                  'class_name':class_name,
                                  'prob':class_prob,
                                  'class_rank':i,
                                  'prob_weight':prob_weight})
        return class_probs_dict


    # (obsolete) but keep around for reference / debug use:
    def get_class_probs_using_shell_weka(self, vosource_list, schema_str='WEKA full'):
        """ Older / Obsolete method which uses seperate, explicit shell calls
        of Java & Weka to generate classifications.
        """
        class_schema_definition = \
                       self.class_schema_definition_dicts[schema_str]
        # NOTE: This function retrieves/fills dicts with feature and class info.
        #           self.arffmaker.master_features [{},{},{}...]
        #           self.arffmaker.master_classes [{},{},{}...]
        #       Technically, this function and its called methods are ARFF
        #       independent and could reside elsewhere if these dicts are used
        #       universally.
        self.arffmaker.populate_features_and_classes_using_local_xmls(\
                                             srcid_xml_tuple_list=vosource_list)

        # This is KLUDGEY: we re-define the "master_features" list to
        #    include only features found in the training .arff, so that the
        #    final .arff will match the training set and thus its .model file
        #    and therefore can be classified using that .model file. :
        new_master_features_list = []
        for feat_name,feat_type in self.arffmaker.master_features:
            if feat_name in self.training_arff_features_list:
                new_master_features_list.append((feat_name,feat_type))
        self.arffmaker.master_features = new_master_features_list

        out_fpath = "/tmp/temp_%d_%d.arff" % (os.getpid(), \
                                                    random.randint(0,100000000))
        self.arffmaker.write_arff(outfile=out_fpath, classes_arff_str=\
                      self.class_schema_definition_dicts[schema_str]\
                                                          ['classes_arff_str'],\
                      remove_sparse_classes=False)

        # class_prob_list_of_lists = [(class_name, class_prob), ...]
        #import pdb; pdb.set_trace()
        class_prob_list_of_lists = self.classify_and_parse_using_weka_model(\
            out_fpath,
            model_fpath=self.class_schema_definition_dicts[schema_str]['weka_training_model_fpath'],
            class_path=self.pars['weka_java_classpath'],
            schema_str=schema_str)

        os.system("rm " + out_fpath)
        # NOTE: This makes the assumption that the srcid list order of 
        # class_prob_list corresponds to the order of self.arffmaker.master_list
        # and that their order also corresponds to vosource_list[] srcid order.
        assert(len(self.arffmaker.master_list) == len(class_prob_list_of_lists))
 
        class_probs_dict = {} # {src_id:[{'schema_id':'', 'class_id':'', 'prob':'', 'class_rank':'', 'prob_weight':''}]

        prob_weight = 1.0 # This property may be used in Nat/Dovi to represent
        #              science classes which are known to be non applicable (0.0)
        for j in xrange(len(class_prob_list_of_lists)):
            class_prob_list = class_prob_list_of_lists[j]
            src_id = self.arffmaker.master_list[j]['num']

            n_classes_to_insert = len(class_prob_list)
            if n_classes_to_insert > 3:
                n_classes_to_insert = 3
            class_probs_dict[src_id] = []
            for i in xrange(n_classes_to_insert):
                (class_name, class_prob) = class_prob_list[i]
                # NOTE: in Weka output parsing, we have already ordered the
                #       class_prob_list to have most probable as first element
                class_id = class_schema_definition.get('class_name_id_dict',{})\
                                                          .get(class_name,None)
                class_probs_dict[src_id].append(\
                                 {'schema_id':class_schema_definition['schema_id'],
                                  'class_id':class_id,
                                  'class_name':class_name,
                                  'prob':class_prob,
                                  'class_rank':i,
                                  'prob_weight':prob_weight})
        return class_probs_dict


    def determine_whether_interesting_general_class(self, src_id, class_dict):
        """ 
        This uses the src_class_probs table, the 'General' schema to store /
        identify whether this source is generally interesting or not.
        the 'General' (shema_id=2) row will have a 0/1 value set in prob_weight column
        to represent whether the general classification is interesting or not:
        prob_weight == 0 : not interesting
        prob_weight == 1 : is currently interesting

        It is then expected that some other code will query for these
        General / schema_id==2 rows for the last day or so, and emit/display
        sources with prob_weight == 1.

        ##### NOT IMPLEMENTED YET:
        ##KLUDGE: unfortunately the current algorithm requres prior knowledge of
        ##what the previous General.prob_weight / is interesting state was.  This
        ##means 

        """
        # TODO: query for existance of this src_id in TABLE: interesting_general_classified_srcid
        #         - also want previous general classification.
        #   - We shouldn't do the logic here where if it was a SN and still is a SN, then it is no longer interesting

        if class_dict['class_name'] in ['AGN_short_candid', 'SN_junk', 'AGN_junk', 'AGN_long_candid', 'SN_long_candid', 'SN_short_candid', 'RBRatio_pass_only', 'RBRatio_nonperiodic_']:
            return 1.0 # is interesting
        else:
            return 0.0 # is not interesting.
        

    def generate_insert_classification_using_vosource_list(self, vosource_list,\
                                                     return_updated_xmls=False, do_logging=False, n_objs=None):
        """ This generates classifications for sources given in vosource_list
        using multiple classification schemas/algorihtms.

        A list summarzing each source's classifications is returned.
        Optionally, returns a list of class updated VOSource XML (when flagged).

        ASSUMPTION:
        # NOTE: making the assumtion that vosource_list only contains a single source (which has benn the case so far).
        #        - thus we ASSUME:  len(vosource_list) == 1 

        """
        if do_logging:
            print("before: self.PlugClass.do_classification()")
        #does this do both mlens3 and weka & return?
        (class_probs_dict, plugin_classification_dict) = \
                                 self.PlugClass.do_classification(vosource_list, \
                                          class_schema_definition_dicts=\
                                          self.class_schema_definition_dicts, \
                                          do_logging=do_logging)
        if do_logging:
            print("before: class TABLE INSERT")

        # KLUDGE: this externally accessible list is referenced for TESTING
        #      using analyze_iterative_tutor_classification.py via ptf_master.py
        #self.classname_classprob_classrank_list = []
        self.classname_classprob_classrank_list = {}

        #insert_list = ["INSERT INTO %s (schema_id, class_id, prob, src_id, class_rank, prob_weight, gen_dtime) VALUES " % (self.pars['src_class_probs_tablename'])]
        #insert_list = ["INSERT INTO %s (schema_id, class_id, prob, src_id, class_rank) VALUES " % (self.pars['src_class_probs_tablename'])]
        insert_list = ["INSERT INTO %s (schema_id, class_id, prob, src_id, class_rank, prob_weight, gen_dtime) VALUES " % (self.pars['src_class_probs_tablename'])]
        do_insert = True # NOTE: making the assumtion that vosource_list only contains a single source (which has benn the case so far).
        for src_id,class_probs_list in class_probs_dict.iteritems():
            for class_dict in class_probs_list:
                schema_id = class_dict['schema_id']
                class_id = class_dict['class_id']
                class_name = class_dict['class_name']
                prob = class_dict['prob']
                plugin_name = class_dict['plugin_name']
                class_rank = class_dict['class_rank']
                prob_weight = class_dict['prob_weight']
                #insert_list.append("(%d, %d, %lf, %d, %s, %lf, NOW()), " % \
                #insert_list.append("(%d, %d, %lf, %d, %s), " % \
                # KLUDGE: I've inserted this here just to get us going quickly
                if class_dict['plugin_name'] == 'General':
                    is_interesting = self.determine_whether_interesting_general_class(src_id, class_dict)
                    # then do some check and determine whether we should mark this general classifcation as is-interesting
                    if ((is_interesting < 1.0) and
                        (n_objs != None)):
                        if (n_objs < 7):
                            # So, if not-interesting general classification and n_epochs is less than (7), then we do not spend time on the server/time expensive MySQL INSERT.
                            do_insert = False
                    insert_list.append("(%d, %d, %lf, %d, %s, %f, NOW()), " % \
                                       (schema_id,
                                        class_id,
                                        prob,
                                        src_id,
                                        class_rank,
                                        is_interesting))
                else:
                    insert_list.append("(%d, %d, %lf, %d, %s, 1.0, NULL), " % \
                                       (schema_id,
                                        class_id,
                                        prob,
                                        src_id,
                                        class_rank))
                if plugin_name not in self.classname_classprob_classrank_list:
                    self.classname_classprob_classrank_list[plugin_name] = []
                self.classname_classprob_classrank_list[plugin_name].append(\
                                             (class_name, prob, class_rank))

        if ((len(insert_list) > 1) and (do_insert)):
            insert_str = ''.join(insert_list)[:-2] + ' ON DUPLICATE KEY UPDATE class_id=VALUES(class_id), prob=VALUES(prob), gen_dtime=VALUES(gen_dtime)'
            self.class_interface.cursor.execute(insert_str)

        new_vosource_list = []
        if return_updated_xmls:
            # Insert classifications into VOSource.xml strings which we return:
            for (src_id, orig_vosource_xml) in vosource_list:
                if do_logging:
                    print("before: db_importer.vosource_classification_obj()")
                vosource_class_obj = db_importer.vosource_classification_obj()
                if do_logging:
                    print("before: vosource_class_obj.add_classif_prob(")
                for class_dict in class_probs_dict[src_id]:
                    schema_id = class_dict['schema_id']
                    #class_id = class_dict['class_id']
                    prob = class_dict['prob']
                    #class_rank = class_dict['class_rank']
                    class_name = class_dict['class_name']
                    #prob_weight = class_dict['prob_weight']
                    vosource_class_obj.add_classif_prob(class_name=class_name,
                                                prob=prob,
                                                src_name=str(src_id),
                                                class_schema_name=str(schema_id))
                if do_logging:
                    print("before: add_class_xml_to_existing_vosource_xml()")
                new_xml_string = vosource_class_obj.\
                        add_class_xml_to_existing_vosource_xml(orig_vosource_xml)
                new_vosource_list.append((src_id, new_xml_string))
        if do_logging:
            print("At Return in generate_insert_classification_using_vosource_list() (CLASSIFICATIONS DONE)")
        return new_vosource_list


    def classify_and_insert_using_vosource_list(self, vosource_list, do_logging=False, n_objs=None):
        """ Given a list of VOSource XMLs, generates classifications and
        inserts into class RDB tables.
        """
        some_vosource_xmls = self.generate_insert_classification_using_vosource_list(\
                                                   vosource_list, \
                                                   return_updated_xmls=True, \
                                                   do_logging=do_logging, \
                                                   n_objs=n_objs)


if __name__ == '__main__':

    class_tbl_intf = Classification_Tables_Interface(pars)

    # NOTE: intended to be called elsewhere and have another pars{} passed in.
    sfcg = Source_Feature_Class_Generator(pars)
    sfcg.main(class_tbl_intf)
