#!/usr/bin/env python
"""
feature_extraction_interface.py

   v0.1 Interface for ingest_tools.py to Maxime's TCP/Software/feature_extract/*
   v0.2 Include specific feature definitions.  Methods for access and generate.
   v0.3 made this self-describing so no need to add new extractors if they are in the right place
PDB Command:
   /usr/lib/python2.5/pdb.py test.py
"""
from __future__ import print_function
import sys, os
try:
    import pylab
except:
    pass
import numpy


class GetFeatIdLookupDicts:
    """ This class retrieves a couple lookup dicts from disk, and
    if they dont exist, they are generated from an RDB query and written to disk.

    NOTE: The referenced file on disk should be deleted whenever new
          feature types are added to the RDB feat_lookup table.
    """

    def __init__(self, db_cursor=None):
        self.reference_feat_dict_fpath = os.environ.get('TCP_DATA_DIR') + '/reference_feat_dict.pkl'
        self.cursor = db_cursor


    def form_dicts_from_rdb_query(self):
        """ SELECT the feature tables, form dicts
        Returns : (feature_lookup_dict, filt_lookup_dict)
        """
        feature_lookup_dict = {}
        filt_lookup_dict = {}

        select_str = "SELECT feat_name, filter_id, feat_id FROM feat_lookup"
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()
        for result in results:
            (feat_name, filter_id, feat_id) = result
            feature_lookup_dict[(filter_id, feat_name)] = feat_id
            if filter_id not in filt_lookup_dict:
                filt_lookup_dict[filter_id] = {}
            filt_lookup_dict[filter_id][feat_name] = feat_id
        
        return (feature_lookup_dict, filt_lookup_dict)

        
    def write_dicts_to_disk(self, feature_lookup_dict, filt_lookup_dict):
        """ Write dicts to dictfile which is generally under $TCP_DATA_DIR.
        """
        import cPickle
        fp = open(self.reference_feat_dict_fpath, "w")
        cPickle.dump((feature_lookup_dict, filt_lookup_dict),fp)
        fp.close()


    def get_dicts(self):
        """
        See if dict file is available, if not form from RDB query, write to disk.

        Return (feat dicts).
        """
        # 20090817: dstarr disables condition since we are oftenadding new features lately, and it seems this shouldnt be a big issue since ipengines are initialized once with this dict.
        #if os.path.exists(self.reference_feat_dict_fpath):
        #    # The following fills the variables:
        #    #        (feature_lookup_dict, filt_lookup_dict)
        #    import cPickle
        #    fp = open(self.reference_feat_dict_fpath)
        #    (feature_lookup_dict, filt_lookup_dict) = cPickle.load(fp)
        #    fp.close()
        #else:

        (feature_lookup_dict, filt_lookup_dict) = \
                                self.form_dicts_from_rdb_query()
            #self.write_dicts_to_disk(feature_lookup_dict, filt_lookup_dict)

        self.feature_lookup_dict = feature_lookup_dict
        self.filt_lookup_dict = filt_lookup_dict


class Final_Features:
    """ Class which contains final, extracted (scalar) feature definition
    lists and dictionaries.

    I found a list of these in:
    signals_list[0].properties['data']['i']['features']
    """
    def __init__(self):
        self.ife = Internal_Feature_Extractors()
        #self.ife.features_tup_list

        # TODO: to form self.features_dict{} I need to:
        #  - make mysql-friendly names using replace() for 'table_name'
        #  - assume FLOAT & INDEX
        import copy

        self.string_replace_dict = {'-':'_', 
                                    ' ':'',
                                    '.':'_',
                                    '_extractor':'',
                                    'extractor':''}
        self.filter_list = ['u','g','r','i','z','j','h','k','X'] # cooresponds to RDB 'filt' indexes: [SDSS(5), PTEL(3), <dummy/extra filter is last in list>]
        self.filter_dict = {}
        i = 0
        for filt in self.filter_list:
            self.filter_dict[filt] = i
            i += 1

        self.features_dict = {}
        for (extractor_name,notso_empty_dict) in self.ife.features_tup_list:
            #print extractor_name
            ext_name_mysql_safe = copy.copy(extractor_name)
            for old_str,new_str in self.string_replace_dict.iteritems():
                ext_name_mysql_safe = ext_name_mysql_safe.replace(old_str,new_str)

            self.features_dict[extractor_name] = {\
                'out_type':'FLOAT',
                'table_name':ext_name_mysql_safe,
                'index_type':'INDEX',
                'internal':notso_empty_dict['internal'],
                'doc':notso_empty_dict['doc']}
        """
        self.features_dict = { \
            'std': {\
                'out_type':'FLOAT',
                'table_name':'std_dev',
                'index_type':'INDEX'},
            'third': {\
                'out_type':'FLOAT',
                'table_name':'third_freq',
                'index_type':'INDEX'},
            'first_frequency': {\
                'out_type':'FLOAT',
                'table_name':'first_freq',
                'index_type':'INDEX'},
            'chi2': {\
                'out_type':'FLOAT',
                'table_name':'chi2',
                'index_type':'INDEX'},
            'weighted average': {\
                'out_type':'FLOAT',
                'table_name':'weighted_avg',
                'index_type':'INDEX'},
            'median': {\
                'out_type':'FLOAT',
                'table_name':'feat_median',
                'index_type':'INDEX'},
            'dc': {\
                'out_type':'FLOAT',
                'table_name':'feat_dc',
                'index_type':'INDEX'},
            'max_slope': {\
                'out_type':'FLOAT',
                'table_name':'max_slope',
                'index_type':'INDEX'},
            'freq ratio 2-1': {\
                'out_type':'FLOAT',
                'table_name':'freq_ratio_21',
                'index_type':'INDEX'},
            'second': {\
                'out_type':'FLOAT',
                'table_name':'second_freq',
                'index_type':'INDEX'},
            'old dc': {\
                'out_type':'FLOAT',
                'table_name':'old_dc',
                'index_type':'INDEX'},
            'n of pts beyond 1 std from u': {\
                'out_type':'FLOAT',
                'table_name':'n_pts_by_1_std',
                'index_type':'INDEX'},
            'freq ratio 3-2': {\
                'out_type':'FLOAT',
                'table_name':'freq_ratio_32',
                'index_type':'INDEX'},
            'freq ratio 3-1': {\
                'out_type':'FLOAT',
                'table_name':'freq_ratio_31',
                'index_type':'INDEX'},
            'skew': {\
                'out_type':'FLOAT',
                'table_name':'feat_skew',
                'index_type':'INDEX'},
            'weighted average uncertainty': {\
                'out_type':'FLOAT',
                'table_name':'weight_avg_uncert',
                'index_type':'INDEX'}}
            """
        #self.features_ordered_list = self.features_dict.keys()
        #self.features_ordered_list.sort()

class Feature_database:
    """ Class which contains generation and access methods for
    all possible feature extractors.

    # USE:
    import feature_extraction_interface
    feat_db = feature_extraction_interface.Feature_database()
    feat_db.initialize_mysql_connection(rdb_host_ip='192.168.1.45', \ 
                                        rdb_user='', rdb_name='')
    feat_db.create_feature_tables()
    feat_db.insert_srclist_features_into_rdb_tables(self, signals_list)
    """
    def __init__(self):
        self.final_features = Final_Features()

    def initialize_mysql_connection(self, rdb_host_ip='', rdb_user='', \
                                    rdb_name='', rdb_port=3306, \
                                    feat_lookup_tablename='',\
                                    feat_values_tablename='', \
                                    db=None):
        """ Create connection to feature mysql server.
        """
        import MySQLdb
        if db is None:
            self.db = MySQLdb.connect(host=rdb_host_ip, user=rdb_user, \
                                  db=rdb_name, port=rdb_port, compress=1)
        else:
            self.db = db
        self.cursor = self.db.cursor()
        self.feat_lookup_tablename = feat_lookup_tablename
        self.feat_values_tablename = feat_values_tablename

        self.attempt_to_fill_feat_lookup_tablename()


    def attempt_to_fill_feat_lookup_tablename(self):
        """ KLUDGE: Attempt to retrieve self.feat_lookup_tablename values and
                    populate self.feature_lookup_dict{}
        """
        try:
            select_str = "SELECT (feat_id, filter_id, feat_name) FROM %s" % (self.feat_lookup_tablename)
            self.cursor.execute(select_str)
            results = self.cursor.fetchall()

            self.feature_lookup_dict = {}
            for result in results:
                (feat_id, filt_num, feat_name) = result
                self.feature_lookup_dict[(filt_num, feat_name)] = feat_id
        except:
            pass


    def drop_feature_tables(self):
        """ DROP MySQL tables for all features.

        Tables of form:
        src_id (INT UNSIGNED), feat <some-format, FLOAT?>
        """
        for feat_name,feat_dict in self.final_features.features_dict.iteritems():
            for filt_name in self.final_features.filter_list:
                #create_str = "CREATE TABLE %s_%s (INDEX(src_id), %s(%s))" % (filt_name, feat_name, feat_dict['index_type'], feat_dict['out_type'])
                create_str = "DROP TABLE %s_%s" % (filt_name, feat_dict['table_name'])
                try:
                    self.cursor.execute(create_str)
                except:
                    pass
                    #print 'FAIL:', create_str



class Internal_Feature_Extractors:
    """ Class which contains "internal feature" definition lists & dictionaries
    """
    
    ## modules (instead of classes) will break the test suite. Put these here as appropriate.
    ignores = ["min_extractor","max_extractor","third_extractor"] 
    
    def __init__(self):
        # XXX ORDER OF FEATURES IS IMPORTANT XXX

        # This needs to retain list ordering, but I figure it'd be useful
        #    to have potential dictionary attributes associated with
        #    each internal-feature extractor.

        import ast
        with open(os.path.join(
            os.path.dirname(__file__),
            '../feature_extract/Code/extractors/__init__.py'), 'r') as f:

            init_ast = ast.parse(f.read())

        features = []
        for a in init_ast.body:
            if isinstance(a, ast.ImportFrom):
                features.extend([f.name for f in a.names])

        self.features_tup_list = [(f, {}) for f in features]

        for (feat_name, feat_dict) in self.features_tup_list:
            d = {}
            from ..feature_extract.Code import extractors
            feature = getattr(extractors, feat_name)
            doc = getattr(feature, '__doc__', '')
            feat_dict['doc'] = doc

            import inspect

            feat_dict['internal'] = 'false'
            for member_name, member_val in inspect.getmembers(feature):
                if member_name == 'internal_use_only':
                    if member_val == True:
                        feat_dict['internal'] = 'true'
                    break

        # TODO: I'm sure there is an efficient way to form a dictionary
        #       from the above tuple list, using map(), filter(), etc...
        self.feature_dict = {}
        self.feature_ordered_keys = []
        for (feat_name,feat_dict) in self.features_tup_list:
            self.feature_ordered_keys.append(feat_name)
            self.feature_dict[feat_name] = feat_dict


class Final_Features:
    """ Class which contains final, extracted (scalar) feature definition
    lists and dictionaries.

    I found a list of these in:
    signals_list[0].properties['data']['i']['features']
    """
    def __init__(self):
        self.ife = Internal_Feature_Extractors()
        #self.ife.features_tup_list

        # TODO: to form self.features_dict{} I need to:
        #  - make mysql-friendly names using replace() for 'table_name'
        #  - assume FLOAT & INDEX
        import copy

        self.string_replace_dict = {'-':'_', 
                                    ' ':'',
                                    '.':'_',
                                    '_extractor':'',
                                    'extractor':''}
        self.filter_list = ['u','g','r','i','z','j','h','k','X'] # cooresponds to RDB 'filt' indexes: [SDSS(5), PTEL(3), <dummy/extra filter is last in list>]
        self.filter_dict = {}
        i = 0
        for filt in self.filter_list:
            self.filter_dict[filt] = i
            i += 1

        self.features_dict = {}
        for (extractor_name,notso_empty_dict) in self.ife.features_tup_list:
            #print extractor_name
            ext_name_mysql_safe = copy.copy(extractor_name)
            for old_str,new_str in self.string_replace_dict.iteritems():
                ext_name_mysql_safe = ext_name_mysql_safe.replace(old_str,new_str)

            self.features_dict[extractor_name] = {\
                'out_type':'FLOAT',
                'table_name':ext_name_mysql_safe,
                'index_type':'INDEX',
                'internal':notso_empty_dict['internal'],
                'doc':notso_empty_dict['doc']}
        """
        self.features_dict = { \
            'std': {\
                'out_type':'FLOAT',
                'table_name':'std_dev',
                'index_type':'INDEX'},
            'third': {\
                'out_type':'FLOAT',
                'table_name':'third_freq',
                'index_type':'INDEX'},
            'first_frequency': {\
                'out_type':'FLOAT',
                'table_name':'first_freq',
                'index_type':'INDEX'},
            'chi2': {\
                'out_type':'FLOAT',
                'table_name':'chi2',
                'index_type':'INDEX'},
            'weighted average': {\
                'out_type':'FLOAT',
                'table_name':'weighted_avg',
                'index_type':'INDEX'},
            'median': {\
                'out_type':'FLOAT',
                'table_name':'feat_median',
                'index_type':'INDEX'},
            'dc': {\
                'out_type':'FLOAT',
                'table_name':'feat_dc',
                'index_type':'INDEX'},
            'max_slope': {\
                'out_type':'FLOAT',
                'table_name':'max_slope',
                'index_type':'INDEX'},
            'freq ratio 2-1': {\
                'out_type':'FLOAT',
                'table_name':'freq_ratio_21',
                'index_type':'INDEX'},
            'second': {\
                'out_type':'FLOAT',
                'table_name':'second_freq',
                'index_type':'INDEX'},
            'old dc': {\
                'out_type':'FLOAT',
                'table_name':'old_dc',
                'index_type':'INDEX'},
            'n of pts beyond 1 std from u': {\
                'out_type':'FLOAT',
                'table_name':'n_pts_by_1_std',
                'index_type':'INDEX'},
            'freq ratio 3-2': {\
                'out_type':'FLOAT',
                'table_name':'freq_ratio_32',
                'index_type':'INDEX'},
            'freq ratio 3-1': {\
                'out_type':'FLOAT',
                'table_name':'freq_ratio_31',
                'index_type':'INDEX'},
            'skew': {\
                'out_type':'FLOAT',
                'table_name':'feat_skew',
                'index_type':'INDEX'},
            'weighted average uncertainty': {\
                'out_type':'FLOAT',
                'table_name':'weight_avg_uncert',
                'index_type':'INDEX'}}
            """
        #self.features_ordered_list = self.features_dict.keys()
        #self.features_ordered_list.sort()

class Feature_database:
    """ Class which contains generation and access methods for
    all possible feature extractors.

    # USE:
    import feature_extraction_interface
    feat_db = feature_extraction_interface.Feature_database()
    feat_db.initialize_mysql_connection(rdb_host_ip='192.168.1.45', \ 
                                        rdb_user='', rdb_name='')
    feat_db.create_feature_tables()
    feat_db.insert_srclist_features_into_rdb_tables(self, signals_list)
    """
    def __init__(self):
        self.final_features = Final_Features()

    def initialize_mysql_connection(self, rdb_host_ip='', rdb_user='', \
                                    rdb_name='', rdb_port=3306, \
                                    feat_lookup_tablename='',\
                                    feat_values_tablename='', \
                                    db=None):
        """ Create connection to feature mysql server.
        """
        import MySQLdb
        if db is None:
            self.db = MySQLdb.connect(host=rdb_host_ip, user=rdb_user, \
                                  db=rdb_name, port=rdb_port, compress=1)
        else:
            self.db = db
        self.cursor = self.db.cursor()
        self.feat_lookup_tablename = feat_lookup_tablename
        self.feat_values_tablename = feat_values_tablename

        self.attempt_to_fill_feat_lookup_tablename()


    def attempt_to_fill_feat_lookup_tablename(self):
        """ KLUDGE: Attempt to retrieve self.feat_lookup_tablename values and
                    populate self.feature_lookup_dict{}
        """
        try:
            select_str = "SELECT (feat_id, filter_id, feat_name) FROM %s" % (self.feat_lookup_tablename)
            self.cursor.execute(select_str)
            results = self.cursor.fetchall()

            self.feature_lookup_dict = {}
            for result in results:
                (feat_id, filt_num, feat_name) = result
                self.feature_lookup_dict[(filt_num, feat_name)] = feat_id
        except:
            pass


    def drop_feature_tables(self):
        """ DROP MySQL tables for all features.

        Tables of form:
        src_id (INT UNSIGNED), feat <some-format, FLOAT?>
        """
        for feat_name,feat_dict in self.final_features.features_dict.iteritems():
            for filt_name in self.final_features.filter_list:
                #create_str = "CREATE TABLE %s_%s (INDEX(src_id), %s(%s))" % (filt_name, feat_name, feat_dict['index_type'], feat_dict['out_type'])
                create_str = "DROP TABLE %s_%s" % (filt_name, feat_dict['table_name'])
                try:
                    self.cursor.execute(create_str)
                except:
                    pass
                    #print 'FAIL:', create_str


    def create_feature_lookup_dict(self):
        """ Create dictionary: feature_lookup_dict:
        """
        Get_Feat_Id_Lookup_Dicts = GetFeatIdLookupDicts(db_cursor=self.cursor)
        Get_Feat_Id_Lookup_Dicts.get_dicts()

        self.feature_lookup_dict = Get_Feat_Id_Lookup_Dicts.feature_lookup_dict
        self.filt_lookup_dict = Get_Feat_Id_Lookup_Dicts.filt_lookup_dict


    # OBSOLETE:
    def create_feature_lookup_dict__old(self):
        """ Create dictionary: feature_lookup_dict:
        """
        self.feature_lookup_dict = {} # New dict, even if exists already
        self.filt_lookup_dict = {}
        for filt_num in xrange(len(self.final_features.filter_list)):
            self.filt_lookup_dict[filt_num] = {}
        i = 0
        #feat_id_partition_groups = []
        for feat_name_internal,feat_dict in self.final_features.features_dict.iteritems():
            feat_name = feat_dict['table_name']
            #feat_id_list = []
            for filt_num in xrange(len(self.final_features.filter_list)):
                self.feature_lookup_dict[(filt_num, feat_name)] = i
                self.filt_lookup_dict[filt_num][feat_name] = i
                #feat_id_list.append(str(i))
                i += 1
            #feat_id_partition_groups.append(feat_id_list)


    def create_feature_tables(self):
        """ CREATE MySQL tables for all features.

        CREATE TABLE feature_lookup (feat_id SMALLINT UNSIGNED, filter_id TINYINT UNSIGNED, feat_name VARCHAR(120), INDEX(feat_id))

        CREATE TABLE feature_values (src_id INT UNSIGNED, feat_id SMALLINT UNSIGNED, feat_val FLOAT, feat_weight FLOAT, INDEX(feat_id, feat_val), INDEX(src_id)) PARTITION BY LIST(feat_id) (
        PARTITION p0 VALUES IN (0),
        PARTITION p0 VALUES IN (0),
        ... <for all feature-filter combination>


        NOTE: To update the partition tables of an existing feat_values table:
         - su - root, copy /var/lib/mysql/source_test_db   to a backup, so you can always copy the table files back if needed.
         - Also copy (using a shell script) all the feat_values mysql files to feat_values_orig named files
             - see: mysql_feat_values_partition_table_copy.sh   for a template of the script
         - drop table feat_values;
         - then run feature_extraction_interface.py 's create_feature_tables()
         - insert into feat_values select * from feat_values_orig;

        """
        # KLUDGE: This is repeated in create_feature_lookup_dict() which
        #   was probably called earlier.  feat_id_partition_groups should 
        #   probably be self. and everything done in mentioned function. 
        #   Then this section can be removed.
        self.feature_lookup_dict = {} # New dict, even if exists already
        self.filt_lookup_dict = {}
        for filt_num in xrange(len(self.final_features.filter_list)):
            self.filt_lookup_dict[filt_num] = {}
        i = 0
        feat_id_partition_groups = []
        inter_partition_list = []
        in_partition_count = 0

        for feat_name_internal,feat_dict in self.final_features.features_dict.iteritems():
            feat_name = feat_dict['table_name']

            feat_id_list = []
            for filt_num in xrange(len(self.final_features.filter_list)):
                self.feature_lookup_dict[(filt_num, feat_name)] = i
                self.filt_lookup_dict[filt_num][feat_name] = i
                feat_id_list.append(str(i))
                i += 1
                
            in_partition_count += 1
            inter_partition_list.extend(feat_id_list)
            # The following clusters 4 features (and their filters) to a partitn
            if in_partition_count == 4:
                feat_id_partition_groups.append(inter_partition_list)
                in_partition_count = 0
                inter_partition_list = []

        if len(inter_partition_list) > 0:
            feat_id_partition_groups.append(inter_partition_list)
        #### NOTE: Here I extend the number of partitions / features beyond
        #       what is currently used, to allow features to be added in future
        #       without re-populating feature tables.
        inter_partition_list = []
        in_partition_count = 0
        # NOTE: it seems we need at leas 50 * (9 filters) extra added at the moment
        for i_future_feature in xrange(1000):
            feat_id_list = []
            for filt_num in xrange(len(self.final_features.filter_list)):
                feat_id_list.append(str(i))
                i += 1
            in_partition_count += 1
            inter_partition_list.extend(feat_id_list)
            # The following clusters 4 features (and their filters) to a partitn
            if in_partition_count == 4:
                feat_id_partition_groups.append(inter_partition_list)
                in_partition_count = 0
                inter_partition_list = []
        ####

        if 0:
            ##### Do this section if you want to re-create the feat_lookup table (which is less likely than updating the partitions of the feat_values table)
            #####     NOTE: if you want to add new features to the feat_lookup tabe, see Add_New_fatures.add_new_features_to_featlookup_table()
            create_str = "CREATE TABLE %s (feat_id SMALLINT UNSIGNED, filter_id TINYINT UNSIGNED, feat_name VARCHAR(120), doc_str VARCHAR(2000), is_internal BOOLEAN, INDEX(feat_id), INDEX(filter_id,feat_name))" % (self.feat_lookup_tablename)
            self.cursor.execute(create_str)

            insert_list = ["INSERT INTO %s (feat_id, filter_id, feat_name, doc_str, is_internal) VALUES " % (self.feat_lookup_tablename)]
            for (filt_num,feat_name),i_feat in self.feature_lookup_dict.iteritems():
                # KLUDGY: list structure is not ideal here:
                doc_str = ''
                #for temp_feat_name,temp_dict in self.final_features.ife.\
                #                                                 features_tup_list:
                for temp_feat_name,temp_dict in self.final_features.features_dict.\
                                                                        iteritems():
                    if feat_name == temp_dict['table_name']:
                        doc_str = temp_dict['doc'][:2000].replace("'","_").replace('"',"_")#.replace("","_")
                        internal = temp_dict['internal']
                        break # get out of loop
                insert_list.append('(%d,%d,"%s","%s", %s), ' % \
                                             (i_feat, filt_num, feat_name, doc_str, internal))
            self.cursor.execute(''.join(insert_list)[:-2])

        #create_str_list = ["CREATE TABLE %s (src_id INT UNSIGNED, feat_id SMALLINT UNSIGNED, feat_val DOUBLE, feat_weight FLOAT, INDEX(feat_id, feat_val), INDEX(src_id)) PARTITION BY LIST(feat_id) (" % (self.feat_values_tablename)]
        create_str_list = ["CREATE TABLE %s (src_id INT UNSIGNED, feat_id SMALLINT UNSIGNED, feat_val DOUBLE, feat_weight FLOAT DEFAULT 1.0, INDEX(feat_id, feat_val), UNIQUE INDEX(src_id, feat_id)) PARTITION BY LIST(feat_id) (" % (self.feat_values_tablename)]

        # TODO: here I need to add additional/future feature-id numbers
        i = 0
        for feat_name_assoc_featids_list in feat_id_partition_groups:
            id_str = ','.join(feat_name_assoc_featids_list)
            create_str_list.append("PARTITION p%d VALUES IN (%s), " %(i,id_str))
            i += 1

        import pdb; pdb.set_trace()
        

        self.cursor.execute(''.join(create_str_list)[:-2] + ")")


    #############

    # obsolete:
    def create_feature_tables_old(self):
        """ CREATE MySQL tables for all features.

        CREATE TABLE feature_lookup (feat_id SMALLINT UNSIGNED, filter_id TINYINT UNSIGNED, feat_name VARCHAR(120), INDEX(feat_id))

        CREATE TABLE feature_values (src_id INT UNSIGNED, feat_id SMALLINT UNSIGNED, feat_val FLOAT, feat_weight FLOAT, INDEX(feat_id, feat_val), INDEX(src_id)) PARTITION BY LIST(feat_id) (
        PARTITION p0 VALUES IN (0),
        PARTITION p0 VALUES IN (0),
        ... <for all feature-filter combination>
        """
        # KLUDGE: This is repeated in create_feature_lookup_dict() which
        #   was probably called earlier.  feat_id_partition_groups should 
        #   probably be self. and everything done in mentioned function. 
        #   Then this section can be removed.
        self.feature_lookup_dict = {} # New dict, even if exists already
        self.filt_lookup_dict = {}
        for filt_num in xrange(len(self.final_features.filter_list)):
            self.filt_lookup_dict[filt_num] = {}
        i = 0
        feat_id_partition_groups = []
        for feat_name_internal,feat_dict in self.final_features.features_dict.iteritems():
            feat_name = feat_dict['table_name']

            feat_id_list = []
            for filt_num in xrange(len(self.final_features.filter_list)):
                self.feature_lookup_dict[(filt_num, feat_name)] = i
                self.filt_lookup_dict[filt_num][feat_name] = i
                feat_id_list.append(str(i))
                i += 1
            feat_id_partition_groups.append(feat_id_list)
        create_str = "CREATE TABLE %s (feat_id SMALLINT UNSIGNED, filter_id TINYINT UNSIGNED, feat_name VARCHAR(120), INDEX(feat_id), INDEX(filter_id,feat_name))" % (self.feat_lookup_tablename)
        self.cursor.execute(create_str)

        insert_list = ["INSERT INTO %s (feat_id, filter_id, feat_name) VALUES " % (self.feat_lookup_tablename)]
        for (filt_num,feat_name),i_feat in self.feature_lookup_dict.iteritems():
            insert_list.append('(%d,%d,"%s"), '% (i_feat, filt_num, feat_name))
        self.cursor.execute(''.join(insert_list)[:-2])

        create_str_list = ["CREATE TABLE %s (src_id INT UNSIGNED, feat_id SMALLINT UNSIGNED, feat_val DOUBLE, feat_weight FLOAT, INDEX(feat_id, feat_val), INDEX(src_id)) PARTITION BY LIST(feat_id) (" % (self.feat_values_tablename)]
        i = 0
        for feat_name_assoc_featids_list in feat_id_partition_groups:
            id_str = ','.join(feat_name_assoc_featids_list)
            create_str_list.append("PARTITION p%d VALUES IN (%s), " %(i,id_str))
            i += 1

        self.cursor.execute(''.join(create_str_list)[:-2] + ")")


    def get_rez_for_featureless_sources(self, orig_rez):
        """ Given a xrsio.get_sources_for_radec() outputed 'rez' structure,
        query the feat_values table to ensure no src_ids already exist.

        Return the reduced rez structure.
        """
        featureless_srcids = []
        reduced_rez = []
        for src_rez in orig_rez:
            for temp_rez in src_rez.values():
                if 'src_id' in temp_rez:
                    src_id = temp_rez['src_id']
                    break
            select_str ="SELECT TRUE FROM feat_values WHERE src_id=%d LIMIT 1"\
                                                                    % (src_id)
            self.cursor.execute(select_str)
            results = self.cursor.fetchall()
            if len(results) == 0:
                reduced_rez.append(src_rez)
                featureless_srcids.append(src_id)
        return (featureless_srcids, reduced_rez)


    def insert_srclist_features_into_rdb_tables(self,signals_list, srcid_list,\
                                                do_rdb_insert=True, do_delete_existing_featvals=False):
        """ Form lists of values for all features & then for each feature,
        insert each src_id & feature-list into their cooresponding table.
        """
        insert_dict = {}
        for filt_num in xrange(len(self.final_features.filter_list)):
            insert_dict[filt_num] = {}
            for feat_name_internal,feat_dict in self.final_features.features_dict.iteritems():
                feat_name = feat_dict['table_name']
                insert_dict[filt_num][feat_name] = []

        used_filters_list = []
        for i in range(len(signals_list)):
            signal_obj = signals_list[i]
            src_id = srcid_list[i]

            ### 20100527 dstarr adds a new condition since we have disabled the combo_band, which chooses the filter with the most epochs:
            filter_epoch_counts = []
            for filt_name in signal_obj.properties['data'].keys():
                if not filt_name in ['multiband', 'combo_band']:
                    filter_epoch_counts.append((len(signal_obj.properties['data'][filt_name]['input']['flux_data']), filt_name))
            filter_epoch_counts.sort(reverse=True)
            filter_most_sampled = filter_epoch_counts[0][1]
            used_filters_list.append(filter_most_sampled)
            ###

            for filt_name in signal_obj.properties['data'].keys():
                # 20090617 KLUDGE:
                #    (in the next 2 lines) I am going to just include the ['multiband', 'combo_band'] and not ['ptf_g', 'ptf_r'] bands since they are combined into ['combo_band'].  NOTE: I think ['multiband'] has features like: 'ws_variability_ru', but not other features... so it is complimentary
                ### 20100527 dstarr adds a new condition since we have disabled the combo_band, which chooses the filter with the most epochs:
                ###if not filt_name in ['multiband', 'combo_band']:
                ###    continue # skip this band (probably a specific filter)
                if not filt_name in ['multiband', 'combo_band', filter_most_sampled]:
                    continue # skip this band (probably a specific filter)

                
                if filt_name in self.final_features.filter_list:
                    filt_num = self.final_features.filter_list.index(filt_name)
                else:
                    filt_num = len(self.final_features.filter_list) - 1 # Given dummy filter
                for feat_name_internal,feat_dict in self.final_features.features_dict.iteritems():
                    feat_name = feat_dict['table_name']
                    # NOTE: if a certain feature was not generated, we don't INSERT 
                    #       it into the RDB.  This alleviates lots of NULL feat values.
                    #if not signal_obj.properties['data'][filt_name]\
                    #                            ['features'].has_key(feat_name):
                    #    feat_val = "NULL"
                    #if feat_name == 'flux_percentile_ratio_mid50':
                    #    import pdb; pdb.set_trace()
                    #    print 'yo', feat_name, filt_name
                    if feat_name in signal_obj.properties['data'][filt_name]\
                                                ['features']:
                        feat_val = str(signal_obj.properties['data'][filt_name]\
                                                        ['features'][feat_name])
                        if ((feat_val == 'Fail') or (feat_val == 'nan') or
                            (feat_val == 'inf')  or (feat_val == 'None')):
                            feat_val = "NULL"
                        else:
                            # KLUDGE we force strings and other feature values to NULL
                            try:
                                blah = float(feat_val)
                            except:
                                feat_val = "NULL"
                        # 20090727: dstarr adds this so that NULL features are not INSERTed into RDB.
                        #    - this should be ok since RDB features are just for User queries, not TCP reference.
                        if feat_val != "NULL":
                            insert_dict[filt_num][feat_name].append((src_id,feat_val))
                    #insert_dict[filt_num][feat_name].append((src_id,feat_val))

        # Here we INSERT into database for each feature (which cooresponds to
        #     a unique MySQL Table Partition file):
        # # # # # # # # # #
        # TODO: ? which is MySQL faster (using partitions): mini INSERT of MEGA
        
        if do_rdb_insert:
            #insert_list = ["INSERT INTO %s (src_id, feat_id, feat_val, feat_weight) VALUES " % (self.feat_values_tablename)]
            insert_list = ["INSERT INTO %s (src_id, feat_id, feat_val) VALUES " % (self.feat_values_tablename)]
        else:
            insert_list = []
        # THIS is pretty KLUDGY since it iterates over all know filters (multiple surveys):  And, all ptf is in filter_id=8, even though that includes 2 filter + combo_band:
        for filt_num,filt_dict in insert_dict.iteritems():
            for feat_name,val_list in filt_dict.iteritems():
                #if 'flux_percentile_ratio' in feat_name:
                #if len(val_list) == 0:
                #    print 'len()==0', feat_name, filt_num, val_list
                    
                #if (filt_num == 8) and (feat_name == 'flux_percentile_ratio_mid50'):
                #    import pdb; pdb.set_trace()
                #    print 'yo', feat_name, filt_num, val_list

                for (src_id,feat_val) in val_list:
                    # # # # TODO: remove HARDCODE of feat_weight = 1.0 :
                    #insert_list.append("(%d,%d,%s,1.0), " % (src_id, \
                    insert_list.append("(%d,%d,%s), " % (src_id, \
                               self.feature_lookup_dict[(filt_num, feat_name)],\
                               feat_val)) 
        if do_rdb_insert and len(insert_list) > 1:

            if do_delete_existing_featvals:
                ### This will make things take much longer, so this is normally disabled, although doing this
                ###    will fill fix a bug in pairwise_classifications.py:get_featcals_for_srcids()
                ###     feat-val .png distribution plots, where older feat_values were getting plotted.
                self.cursor.execute("DELETE FROM %s WHERE src_id=%d" % (self.feat_values_tablename, src_id))

            #self.cursor.execute(''.join(insert_list)[:-2])
            insert_str = ''.join(insert_list)[:-2] + ' ON DUPLICATE KEY UPDATE feat_val=VALUES(feat_val)'
            self.cursor.execute(insert_str)
            print('feature RDB INSERTed/UPDATEd %d sources.' % (len(srcid_list)))

            # TODO: lets also insert / update which filter was used for the features, into the RDB.

        return (insert_list, used_filters_list)


    def do_large_query_of_feature_rdb(self, order_by_feat=''):
        """This executes a large query of (many) features in feature RDB tables.
        The returned column (and column name?) can then be used for generating
        a summary plot.
        """
        # NOTE: can assert theres a feature table for all filter_feature combos

        table_names = []
        for filt_name in self.final_features.filter_list:
            for feat_name,feat_dict in self.final_features.features_dict.\
                                                                    iteritems():
                table_names.append("%s_%s" %(filt_name,feat_dict['table_name']))
        table_names.sort()

        select_col_strs = []
        select_join_strs = []

        sub_table_names = table_names[:len(table_names)/5]
        for table_name in sub_table_names:
            select_col_strs.append("%s.feat" % (table_name))
            select_join_strs.append("%s" % (table_name)) # TODO: skip this and just use table_names

        # ... JOIN __some_table__ USING (srcid)  JOIN __some_table__ USING (srcid)  ... WHERE ()
        select_str = "SELECT %s FROM %s" % (', '.join(select_col_strs), ' JOIN '.join(select_join_strs))
        self.cursor.execute(select_str)

        results = self.cursor.fetchall()

        out_dict = {}
        for i in range(len(table_names)):
            table_name = table_names[i]
            temp_list = [] # I think this produces a unique pointer
            for row in results:
                temp_list.append(row[i])
            out_dict[table_name] = temp_list
            
        return out_dict # e.g.: 'z_std':[4,5,6,7,...]


    def scp_feat_summary_img_to_webserver(self, \
                                    summary_img_fpath='',\
                                    feature_summary_webserver_name='',\
                                    feature_summary_webserver_user='',\
                                    feature_summary_webserver_dirpath='',\
                                    feature_summary_webserver_url_prefix=''):
        """ Scp's feature-summary-image to webserver path.
        """
        scp_str = "scp -C %s %s@%s:%s/" % (summary_img_fpath,\
                                           feature_summary_webserver_user, \
                                           feature_summary_webserver_name, \
                                           feature_summary_webserver_dirpath)
        os.system(scp_str)
        fname_root = summary_img_fpath[summary_img_fpath.rfind('/')+1:]
        remote_url = "%s%s" %(feature_summary_webserver_url_prefix, fname_root)
        return remote_url

class Plot_Signals:
    """
    # TODO: I would like a plot which:
    #   - input: signals_list[0]
    #   - contains all sub plots within it.
    #   - filters are vertical, plot types are horizontal.
    #   - plots are written to .ps file
    #   - XML file / RA,dec name is recorded in plot.
    """

    def __init__(self, signals_list, gen):
        self.signals_list = signals_list
        self.gen = gen  # this is just accessed for ra, dec, src_id info
        self.pars = {\
            'excluded_inters':[],
            'subplot_region_limits':{'x_min':0.1,#0.01,
                                     'x_max':1.0,
                                     'y_min':0.07, #0.0125, # 0.0
                                     'y_max':0.9},
            'subplot_x_buffer':0.01,
            'subplot_y_buffer':0.02,
            'filters_list':['u', 'g', 'r', 'i', 'z', 'j', 'h', 'k'],
            }   


    def get_features_to_plot_list(self, signal_obj):
        """ Determine how many feature plots are needed:
        NOTE: this covers the possibility that some filters may contain extra features
        """
        features_to_plot = []
        for filt in signal_obj.properties['data'].keys():
            for feature_name in signal_obj.properties['data'][filt]['inter'].keys():
                if feature_name not in features_to_plot:
                    if feature_name not in self.pars['excluded_inters']:
                        try:
                            feat_length = len(signal_obj.properties['data'][filt]\
                                              ['inter'][feature_name][0])
                            if feat_length > 0:
                                print('Added:  ', feature_name)
                                features_to_plot.append(feature_name)
                        except:
                            print('Skipped:', feature_name)
        features_to_plot.sort()
        return features_to_plot


    def get_feature_plot_pos_dict(self, signal_object, features_to_plot=[], \
                                                       filters_to_plot=[]):
        """ Now  set up a dict which contains positions constraints
                of all plots
        """
        n_rows = len(filters_to_plot)
        n_cols = len(features_to_plot)# + 1 # include the 'input-data' plot

        subplot_x_size = ((self.pars['subplot_region_limits']['x_max'] - \
                          self.pars['subplot_region_limits']['x_min']) - \
                          (self.pars['subplot_x_buffer'] * (n_cols - 1))) / \
                                                    (n_cols + 2)#+2 is HACK
        subplot_y_size = ((self.pars['subplot_region_limits']['y_max'] - \
                          self.pars['subplot_region_limits']['y_min']) - \
                          (self.pars['subplot_y_buffer'] * (n_rows - 1))) / \
                                                                         n_rows

        x_start_list = []
        for i in range(n_cols):
            x_start_list.append(self.pars['subplot_region_limits']['x_min'] + \
                             i*(self.pars['subplot_x_buffer'] + subplot_x_size))
        y_start_list = []
        for i in range(n_rows):
            y_start_list.append(self.pars['subplot_region_limits']['y_min'] + \
                             i*(self.pars['subplot_y_buffer'] + subplot_y_size))

        feature_plot_positions_dict = {}
        for i_filt in range(len(filters_to_plot)):
            filt = filters_to_plot[i_filt]
            if filt not in feature_plot_positions_dict.keys():
                feature_plot_positions_dict[filt] = {}
            for i_feat in range(len(features_to_plot)):
                feature = features_to_plot[i_feat]
                feature_dict = {'x_low':x_start_list[i_feat],
                                'x_high':x_start_list[i_feat] + subplot_x_size,
                                'y_low':y_start_list[i_filt],
                                'y_high':y_start_list[i_filt] + subplot_y_size}
                feature_plot_positions_dict[filt][feature] = feature_dict
        return feature_plot_positions_dict


    def generate_multi_filter_plot(self, signal_obj, ps_fpath='/tmp/blah.ps'):
        """ Generate a single plot which summarizes data and feature datae
        arrays for all filters.
        """
        import pylab
        #pylab.rcParams.update({'figure.figsize':[10,10]}) # ??x?? inches
        pylab.hold(False)
        pylab.hold(True)
        features_to_plot = self.get_features_to_plot_list(signal_obj)
        features_to_plot.insert(0,'FLUX vs TIME')
        filters_to_plot = []
        #20080326 comment out & replace:
        #available_filters = signal_obj.properties['data'].keys()
        #for filt in self.pars['filters_list']:
        #    if filt in available_filters:
        #        filters_to_plot.append(filt)
        filters_to_plot = signal_obj.properties['data'].keys()
                            
        feature_plot_positions_dict= self.get_feature_plot_pos_dict(signal_obj,\
                                           features_to_plot=features_to_plot, \
                                           filters_to_plot=filters_to_plot)
        empty_array = numpy.array([])
        pylab.hold(False)
        pylab.clf()
        pylab.plot(empty_array, empty_array, 'ro')
        pylab.hold(True)
        pylab.axis([0.12,0.9,0,0.9]) # This is needed, even with following line
        pylab.axis('off')
        #pylab.title('$\it{hi}$')

        source_info_str = "src_id=%d,    ra=%f~%f,    dec=%f~%f" % ( \
                                self.gen.sig.x_sdict['src_id'], \
                                self.gen.sig.x_sdict['ra'], \
                                self.gen.sig.x_sdict['ra_rms'], \
                                self.gen.sig.x_sdict['dec'], \
                                self.gen.sig.x_sdict['dec_rms'])
        pylab.text(0.2, 0.97, source_info_str, horizontalalignment='left', verticalalignment='bottom', rotation=0, size=10)
        # Generate feature-plot names which are labeled at the top,left of plot:
        for feature in features_to_plot:
            x_low = feature_plot_positions_dict[filters_to_plot[0]][feature]['x_low']
            pylab.text(x_low, 0.9, feature, horizontalalignment='left', verticalalignment='bottom', rotation=15, size=7)
        for filt in filters_to_plot:
            y_low = feature_plot_positions_dict[filt]['FLUX vs TIME']['y_low']
            #x_low = feature_plot_positions_dict[filters_to_plot[0]][feature]['x_low']
            #pylab.text(-0.007, y_low, filt, horizontalalignment='left', verticalalignment='bottom', rotation=0, size=10)
            pylab.text(-0.1, y_low, filt, horizontalalignment='left', verticalalignment='bottom', rotation=0, size=10)

        ######
        # Insert feature scalars in-between subplots:
        i = 0
        for filt in filters_to_plot:
            scalar_features = signal_obj.properties['data'][filt]['features'].keys()
            scalar_features.sort()
            print_list = ["%3.3s" % (filt)]
            for feat in scalar_features:
                val = str(signal_obj.properties['data'][filt]['features'][feat])
                try:
                    #print_list.append('%0.8s=%0.3f' % (feat, float(val)))
                    print_list.append('%10.10s' % ("%0.3f" % (float(val))))
                except:
                    #print_list.append('%0.8s=%s' % (feat, val))
                    print_list.append('%10.10s' % (val))
            print_str = '    '.join(print_list)
            #y_low = feature_plot_positions_dict[filt]['FLUX vs TIME']['y_low'] #- 0.1275#+ subplot_y_size / 2.0
            #pylab.text(0, -0.11 +i*0.012,print_str, horizontalalignment='left',\
            #                     verticalalignment='bottom', rotation=0, size=6)
            pylab.text(0.1, -0.11 +i*0.012,print_str, horizontalalignment='left',\
                                 verticalalignment='bottom', rotation=0, size=6)
            i += 1

        # Now add a key/title to the scalar features:
        scalar_features = signal_obj.properties['data'][filters_to_plot[0]][\
                                                              'features'].keys()
        scalar_features.sort()
        print_list = ['   '] #["%3.3s" % ('')]
        for feat in scalar_features:
            print_list.append('%10.10s' % (feat))
        print_str = '    '.join(print_list)
        print(print_str)
        pylab.text(0.1, -0.11 + i*0.012, print_str, horizontalalignment='left', \
                   verticalalignment='bottom', rotation=0, size=6)
        ######

        # Generate sub-plots:
        for filt in filters_to_plot:
            for feature in features_to_plot:
                x_low = feature_plot_positions_dict[filt][feature]['x_low']
                x_high = feature_plot_positions_dict[filt][feature]['x_high']
                y_low = feature_plot_positions_dict[filt][feature]['y_low']
                y_high = feature_plot_positions_dict[filt][feature]['y_high']

                a = pylab.axes([x_low, y_low, x_high-x_low, y_high-y_low], \
                                                                  axisbg ='y' )
                pylab.setp(a , xticks =[] , yticks =[])

                if feature == 'FLUX vs TIME':
                    y_data = signal_obj.properties['data'][filt]['input']\
                                                                   ['flux_data']
                    x_data = signal_obj.properties['data'][filt]['input']\
                                                                   ['time_data']
                    if ((len(x_data) > 0) and (len(y_data) > 0)):
                        pylab.plot(x_data, y_data, 'bo', markersize=2)
                    else:
                        pylab.plot(numpy.array([]), 'bo', markersize=2)
                        #print 'NO DATA:', filt, feature,len(x_data),len(y_data)
                else:
                    # 20080123: For some reason this suddenly FAILS:
                    #     it is as if (with SDSS) I was expecting an array
                    #     of arrays:
                    #y_data = signal_obj.properties['data'][filt]['inter']\
                    #                                               [feature][0]
                    #NOTE: properties...['inter'][feature] might be a single
                    #  array of data, or a 2-elem "list" of two arrays: [1]=t/fq
                    y_data = signal_obj.properties['data'][filt]['inter'][feature]
                    try:
                        if (type(y_data[0]) == type('')):
                            pylab.plot(numpy.array([]), 'bo', markersize=2)
                            #print 'NO DATA:', filt, feature, y_data
                        elif (type(y_data[0]) == type(numpy.array([]))):
                            # Its a 2-elem list, 1st elem is data array, 2nd: t/fq
                            pylab.plot(y_data[0], 'bo', markersize=2)
                        elif (type(y_data) == type(numpy.array([]))):
                            pylab.plot(y_data, 'bo', markersize=2)
                    except:
                        pylab.plot(numpy.array([]), 'bo', markersize=2)
                        #print 'NO DATA:', filt, feature, y_data

        if os.path.exists(ps_fpath):
            os.system('rm ' + ps_fpath)
        pylab.savefig(ps_fpath)
        #os.system('gv ' + ps_fpath + ' &')
        #pylab.show()
        pylab.hold(False)


    def write_multi_filter_ps_files(self, ps_fpath='/tmp/blah.ps'):
        for signal_obj in self.signals_list:
            # TODO: automatically generate PS filenames?
            self.generate_multi_filter_plot(signal_obj, ps_fpath=ps_fpath)


class AddNewFeatures:
    """ Add some new features to the feat_lookup TABLE without
    re-generating, re-indexing this table (rerunning testsuite.py).
    """
    def initialize_mysql_connection(self, rdb_host_ip='', rdb_user='', \
                                    rdb_name='', rdb_port=3306, \
                                    feat_lookup_tablename='',\
                                    feat_values_tablename='', \
                                    db=None):
        """ Create connection to feature mysql server.

        NOTE: this is taken from:   Feature_database class

        """
        import MySQLdb
        if db is None:
            self.db = MySQLdb.connect(host=rdb_host_ip, user=rdb_user, \
                                  db=rdb_name, port=rdb_port, compress=1)
        else:
            self.db = db
        self.cursor = self.db.cursor()


    def add_new_features_to_featlookup_table(self, new_feat_names=[]):
        """ Add some new features to the feat_lookup TABLE without
        re-generating, re-indexing this table (rerunning testsuite.py).
        """
        select_str = "SELECT max(feat_id), min(filter_id), max(filter_id) from feat_lookup"

        self.cursor.execute(select_str)
        results = self.cursor.fetchall()
        max_feat_id = results[0][0]
        min_filt_id = results[0][1]
        max_filt_id = results[0][2]

        insert_list = ["INSERT INTO feat_lookup (feat_id, filter_id, feat_name, doc_str, is_internal) VALUES "]
        i_feat = max_feat_id + 1
        for feat_name in new_feat_names:
            for filt_id in range(min_filt_id, max_filt_id+1):
                insert_list.append('(%d, %d, "%s", "%s", 0), ' % ( \
                                   i_feat, filt_id, feat_name, feat_name))
                i_feat += 1
        self.cursor.execute(''.join(insert_list)[:-2])

