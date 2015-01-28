#!/usr/bin/env python
""" Create / add to ASAS catalog MySQL tables.

NOTE: Some columns of this table can be viewed using:
lyra.berkeley.edu/allstars/asascat.php


"""

import sys, os

from activelearn_utils import Database_Utils

class Asas_Catalog(Database_Utils):
    """
    """
    def __init__(self, pars={}):
        self.pars = pars
        self.connect_to_db()


    def create_tables(self):
        """
Queries:
### For a class, show classifier 1st rank probs, for all trainingset sources
  SELECT tutor_srcid, asascat_probs.class_id, asascat_probs.prob, asascat_train_sources.class_id
              FROM asascat_train_sources
              JOIN asascat_probs ON asascat_probs.catalog_id=asascat_train_sources.catalog_id AND
                                    asascat_probs.tutor_srcid=asascat_train_sources.tutor_srcid AND
                                    asascat_probs.classifier_rank=1
              WHERE catalog_id=1 AND class_id=234
### To show all 1st probs for a class:
  SELECT prob FROM asascat_probs
              WHERE catalog_id=1 AND class_id=234 AND classifier_rank=1     
### To show 1st class prob for a source:
  SELECT prob FROM asascat_probs
              WHERE catalog_id=1 AND tutor_srcid=123456 AND classifier_rank=1  
### Show rank=1 prob, is_acvs, is_trainset info for all sources:
  SELECT tutor_srcid, asascat_probs.class_id, prob, asascat_train_sources.class_id
              FROM asascat_probs
              LEFT JOIN asascat_train_sources ON asascat_train_sources.catalog_id=asascat_probs.catalog_id
                                              ON asascat_train_sources.tutor_srcid=asascat_probs.tutor_srcid
              LEFT JOIN asascat_acvs_sources ON asascat_acvs_sources.catalog_id=asascat_probs.catalog_id
                                             ON asascat_acvs_sources.tutor_srcid=asascat_probs.tutor_srcid
              WHERE catalog_id=1 AND asascat_probs.classifier_rank=1
              

# TABLE: asascat_names
Columns:
  catalog_id
  catalog_name     # "v0.1", "v1_no_ttaur"
  dtime           DATETIME,    # catalog creation date

  ??? Store these in a seperate table / file? / or fill out using PHPMyadmin:
      skipped class?  - probably just store this info in catalog_name
      classifier error_rage

### TABLE: asascat_probs
MOTIVE: want to query using a source's catalog_id, class_id, and get the probs of:
     - probs of all sources which have top class = this sources 1st class
     - probs of all sources which have top class = this sources 2nd class
NOTE: using classifier_rank, we can have a flexible number of classes
      used for a catalog_id
Index:
  index: (catalog_id, tutor_srcid)
  index: (catalog_id, class_id, classifier_rank)
Columns:
  catalog_id
  tutor_srcid
  classifier_rank
  class_id
  prob

### TABLE: asascat_acvs_sources
Columns:
  catalog_id
  tutor_srcid
  class_id
Index:
  index: (catalog_id, class_id)
  PRIME: (catalog_id, tutor_srcid)   # for JOINing with other queries

### TABLE: asascat_train_sources
Columns:
  catalog_id
  tutor_srcid
  class_id
Index:
  index: (catalog_id, class_id)
  PRIME: (catalog_id, tutor_srcid)   # for JOINing with other queries


### TABLE: asascat_source_attribs
MOTIVE: Need to store source related attributes in a single table
       - these should be harder to query for, or potentially changing attributes, such as TCP-features
NOTE:   The feature attributes should probably be retrieved from the current .arff / data structures,
        and not from the source_test_db.feat_values DB table.
Index:
  index: (catalog_id, source_id)
  index: (catalog_id, classif_rank, class_id)
Columns:
  catalog_id
  tutor_srcid
  ra
  decl
  period
  is_periodic       # related to significance
  is_anomalous
  amplitude
  jk_color
  avg_mag
  avg_mag_error
  n_points

######################
### (existing tables):

tutor_simbad_classes
| src_id | simbad_class | simbad_dist | simbad_sptype |
+--------+--------------+-------------+---------------+
| 229376 | PulsV*       |        0.04 | M0            | 
| 262145 | Star         |       21.94 | M             | 


NOTE:
alter table asascat_source_attribs add column delta_t DOUBLE;

        """
        if 1:
            table_names = ["asascat_names",
                           "asascat_probs",
                           "asascat_acvs_sources",
                           "asascat_train_sources",
                           "asascat_source_attribs"]
            for table_name in table_names:
                try:
                    self.tcp_cursor.execute("DROP TABLE %s" % (table_name))
                except:
                    print "Table doesn't exist for DELETE:", table_name


        create_str = """
        CREATE TABLE asascat_names (
id                  INT UNSIGNED,
name                VARCHAR(512),
dtime               DATETIME,
PRIMARY KEY (id),
INDEX (name))
        """
        self.tcp_cursor.execute(create_str)


        create_str = """
        CREATE TABLE asascat_probs (
catalog_id                  INT UNSIGNED,
tutor_srcid                 INT,
classifier_rank            SMALLINT,
class_id  SMALLINT,
prob            FLOAT,
PRIMARY KEY (catalog_id, tutor_srcid, classifier_rank),
INDEX (catalog_id, class_id, classifier_rank))
        """
        self.tcp_cursor.execute(create_str)


        create_str = """
        CREATE TABLE asascat_acvs_sources (
catalog_id                  INT UNSIGNED,
tutor_srcid                 INT,
class_id  SMALLINT,
prob            FLOAT,
PRIMARY KEY (catalog_id, tutor_srcid),
INDEX (catalog_id, class_id))
        """
        self.tcp_cursor.execute(create_str)


        create_str = """
        CREATE TABLE asascat_train_sources (
catalog_id                  INT UNSIGNED,
tutor_srcid                 INT,
class_id  SMALLINT,
PRIMARY KEY (catalog_id, tutor_srcid),
INDEX (catalog_id, class_id))
        """
        self.tcp_cursor.execute(create_str)


        create_str = """
        CREATE TABLE asascat_source_attribs (
catalog_id                  INT UNSIGNED,
tutor_srcid                 INT,
ra                          DOUBLE,
decl                        DOUBLE,
freq1_harmonics_freq_0      DOUBLE,
freq1_harmonics_amplitude_0 DOUBLE,
amplitude                   DOUBLE,
freq_n_alias                DOUBLE,
freq_signif                 DOUBLE,
color_diff_jh               FLOAT,
color_diff_hk               FLOAT,
color_diff_bj               FLOAT,
avg_mag                     FLOAT,
avg_mag_error               FLOAT,
is_periodic                 FLOAT,
is_anomalous                FLOAT,
n_points                    INT,
delta_t                     DOUBLE,
PRIMARY KEY (catalog_id, tutor_srcid))
        """
        self.tcp_cursor.execute(create_str)


    def retrieve_tutor_source_info(self, catalog_id=0):
        """ Once ActiveLearn.active_learn_main() has been run
        and the following tables were filled:
                asascat_source_attribs
                asascat_probs

        This function retrieves information about source available in TUTOR database.
        """
        out_dict = {'srcid':[],
                    'ra':[],
                    'decl':[],
                    'm_avg':[],
                    'm_std':[],
                    'n_points':[],
                    'delta_t':[],
            }
        select_str = "SELECT tutor_srcid FROM asascat_source_attribs WHERE catalog_id=%d" % (catalog_id)
        self.tcp_cursor.execute(select_str)
        results = self.tcp_cursor.fetchall()
        if len(results) == 0:
            raise "ERROR"
        for srcid_row in results:
            srcid = srcid_row[0]
            # query tutor database / tables:
            select_str = "SELECT source_ra, source_dec, AVG(obsdata_val), STD(obsdata_val), count(observation_id), MAX(obsdata_time) - MIN(obsdata_time) FROM sources JOIN observations USING (source_id) JOIN obs_data USING (observation_id) WHERE source_id=%d" % (srcid)
            self.tutor_cursor.execute(select_str)
            results2 = self.tutor_cursor.fetchall()
            if len(results2) == 0:
                raise "ERROR"
            for (ra, decl, m_avg, m_std, n_points, delta_t) in results2:
                out_dict['srcid'].append(srcid)
                out_dict['ra'].append(float(ra))
                out_dict['decl'].append(float(decl))
                out_dict['m_avg'].append(m_avg)
                out_dict['m_std'].append(m_std)
                out_dict['n_points'].append(n_points)
                out_dict['delta_t'].append(delta_t)
        return out_dict


    def fill_asascat_source_attribs_using_tutor_results(self, catalog_id=0, src_dict={}):
        """ Once ActiveLearn.active_learn_main() has been run
        and the following tables were filled:
                asascat_source_attribs
                asascat_probs

        Then this function should be run so that additiona TUTOR info can be added
        as well as summary files can be generated.

        NOTE: This will actually be an UPDATE since the source rows should already exist in TABLE.
        """
        """
        insert_list = ["INSERT INTO asascat_source_attribs (catalog_id, tutor_srcid, ra, decl, avg_mag, avg_mag_error, n_points, delta_t) VALUES "]

        for i, srcid in enumerate(src_dict['srcid']):
            insert_list.append("(%d, %d, %d, %lf, %lf, %lf, %lf, %d, %lf), " % ( \
                               catalog_id, tutor_srcid, ra, decl, avg_mag, avg_mag_error, n_points, delta_t))

        insert_str = ''.join(insert_list)[:-2] + " ON DUPLICATE KEY UPDATE ra=VALUES(ra), decl=VALUES(decl), avg_mag=VALUES(avg_mag), avg_mag_error=VALUES(avg_mag_error), n_points=VALUES(n_points), delta_t=VALUES(delta_t)"
        self.tcp_cursor.execute(insert_str)
        """

        insert_list = ["INSERT INTO asascat_source_attribs (catalog_id, tutor_srcid, ra, decl, avg_mag, avg_mag_error, n_points, delta_t) VALUES "]

        for i, srcid in enumerate(src_dict['srcid']):
            insert_list.append("(%d, %d, %lf, %lf, %lf, %lf, %d, %lf), " % ( \
                               catalog_id,
                               srcid,
                               src_dict['ra'][i],
                               src_dict['decl'][i],
                               src_dict['m_avg'][i],
                               src_dict['m_std'][i],
                               src_dict['n_points'][i],
                               src_dict['delta_t'][i]))
            if len(insert_list) > 10000:
                insert_str = ''.join(insert_list)[:-2] + " ON DUPLICATE KEY UPDATE ra=VALUES(ra), decl=VALUES(decl), avg_mag=VALUES(avg_mag), avg_mag_error=VALUES(avg_mag_error), n_points=VALUES(n_points), delta_t=VALUES(delta_t)"
                self.tcp_cursor.execute(insert_str)
                insert_list = ["INSERT INTO asascat_source_attribs (catalog_id, tutor_srcid, ra, decl, avg_mag, avg_mag_error, n_points, delta_t) VALUES "]

        if len(insert_list) > 1:
            insert_str = ''.join(insert_list)[:-2] + " ON DUPLICATE KEY UPDATE ra=VALUES(ra), decl=VALUES(decl), avg_mag=VALUES(avg_mag), avg_mag_error=VALUES(avg_mag_error), n_points=VALUES(n_points), delta_t=VALUES(delta_t)"
            self.tcp_cursor.execute(insert_str)



    def retrieve_tranx_asascat_info(self, src_dict={}, catalog_id=0):
        """ Assuming that the TUTOR source info has already been added to src_dict,
        This retrieves all other info from the tranx mysql asascat tables.

        Should have these already:
        print src_dict.keys()
            ['decl', 'm_avg', 'delta_t', 'srcid', 'n_points', 'm_std', 'ra']
        
        """

        src_dict.update({'freq1_harmonics_freq_0':[],
                         'freq1_harmonics_amplitude_0':[],
                         'amplitude':[],
                         'freq_n_alias':[],
                         'freq_signif':[],
                         'color_diff_jh':[],
                         'color_diff_hk':[],
                         'color_diff_bj':[],
                         'avg_mag':[],
                         'avg_mag_error':[],
                         'n_points':[],
                         'delta_t':[],
                         'train_class_id':[],
                         })


        select_str = "SELECT tutor_srcid, freq1_harmonics_freq_0, freq1_harmonics_amplitude_0, amplitude, freq_n_alias, freq_signif, color_diff_jh, color_diff_hk, color_diff_bj, avg_mag, avg_mag_error, n_points, delta_t FROM asascat_source_attribs WHERE catalog_id=%d" % (catalog_id)
        self.tcp_cursor.execute(select_str)
        results = self.tcp_cursor.fetchall()
        if len(results) == 0:
            raise "ERROR"
        isrc_irow_tups = [] # kludgey, but requires only 1 database query rather than lots.
        for i_row, row in enumerate(results):
            (tutor_srcid, freq1_harmonics_freq_0, freq1_harmonics_amplitude_0, amplitude, freq_n_alias, freq_signif, color_diff_jh, color_diff_hk, color_diff_bj, avg_mag, avg_mag_error, n_points, delta_t) = row
            i_src = src_dict['srcid'].index(tutor_srcid) # this should always work
            isrc_irow_tups.append((i_src, i_row))
        isrc_irow_tups.sort()
        for (i_src, i_row) in isrc_irow_tups:
            (tutor_srcid, freq1_harmonics_freq_0, freq1_harmonics_amplitude_0, amplitude, freq_n_alias, freq_signif, color_diff_jh, color_diff_hk, color_diff_bj, avg_mag, avg_mag_error, n_points, delta_t) = results[i_row]

            src_dict['freq1_harmonics_freq_0'].append(freq1_harmonics_freq_0)
            src_dict['freq1_harmonics_amplitude_0'].append(freq1_harmonics_amplitude_0)
            src_dict['amplitude'].append(amplitude)
            src_dict['freq_n_alias'].append(freq_n_alias)
            src_dict['freq_signif'].append(freq_signif)
            src_dict['color_diff_jh'].append(color_diff_jh)
            src_dict['color_diff_hk'].append(color_diff_hk)
            src_dict['color_diff_bj'].append(color_diff_bj)
            src_dict['avg_mag'].append(avg_mag)
            src_dict['avg_mag_error'].append(avg_mag_error)
            src_dict['n_points'].append(n_points)
            src_dict['delta_t'].append(delta_t)


        select_str = "SELECT tutor_srcid, class_id FROM asascat_train_sources WHERE catalog_id=%d" % (catalog_id)
        self.tcp_cursor.execute(select_str)
        results = self.tcp_cursor.fetchall()
        if len(results) == 0:
            raise "ERROR"
        isrc_irow_tups = [] # kludgey, but requires only 1 database query rather than lots.
        for i_row, row in enumerate(results):
            (tutor_srcid, class_id) = row
            i_src = src_dict['srcid'].index(tutor_srcid) # this should always work
            isrc_irow_tups.append((i_src, i_row))
        isrc_irow_tups.sort()
        for (i_src, i_row) in isrc_irow_tups:
            (tutor_srcid, class_id) = results[i_row]
            src_dict['train_class_id'].append(class_id)


        import pdb; pdb.set_trace()
        print


        # TODO: retrieve all info from tranx tables & fill mondo_dict for all sources
        # TODO: generate HTML table, write in txt file

        # TODO want to have lots of infor for each srcid, may add more


    def temp_find_avgmags_for_miller_wtts(self, src_dict={}):
        """ Adam Miller requires the avg mags for some wtts sources for vanderbilt U followup
        """
        import numpy
        
        srcids = numpy.loadtxt('/home/pteluser/scratch/wtts_dotid', unpack=True)

        for srcidflt in srcids:
            srcid = int(srcidflt)
            try:
                i_src = src_dict['srcid'].index(srcid)
                print srcid, src_dict['m_avg'][i_src], src_dict['m_std'][i_src]
            except:
                print srcid



if __name__ == '__main__':

    pars = { \
        'tutor_hostname':'192.168.1.103',
        'tutor_username':'dstarr', #'tutor', # guest
        'tutor_password':'ilove2mass', #'iamaguest',
        'tutor_database':'tutor',
        'tutor_port':3306, #33306,
        'tcp_hostname':'192.168.1.25',
        'tcp_username':'pteluser',
        'tcp_port':     3306, #23306, 
        'tcp_database':'source_test_db',
        'catalog_id':0,
        }

    AsasCatalog = Asas_Catalog(pars=pars)
    #AsasCatalog.create_tables()
    #sys.exit()
    
    import cPickle, gzip
    srcdict_pkl_fpath = '/home/pteluser/scratch/asas_catalog_srcdict.pkl.gz'
    if os.path.exists(srcdict_pkl_fpath):
        fp = gzip.open(srcdict_pkl_fpath,'rb')
        src_dict = cPickle.load(fp)
        fp.close()
    else:
        src_dict = AsasCatalog.retrieve_tutor_source_info(catalog_id=pars['catalog_id'])
        fp = gzip.open(srcdict_pkl_fpath,'wb')
        cPickle.dump(src_dict,fp,1) # ,1) means a binary pkl is used.
        fp.close()

    #ONETIMEUSE# AsasCatalog.temp_find_avgmags_for_miller_wtts(src_dict=src_dict)
    
    #AsasCatalog.fill_asascat_source_attribs_using_tutor_results(catalog_id=pars['catalog_id'],
    #                                                            src_dict=src_dict)

    import pdb; pdb.set_trace()
    print
    AsasCatalog.retrieve_tranx_asascat_info(catalog_id=pars['catalog_id'],
                                            src_dict=src_dict) # retrieve_tutor_source_info() must have been called



    # TODO: once asascat_probs is filled, and mabe some of asascat_source_attribs
    #    - then fill the rest of the asascat_* tables for a catalog_id
    # TODO: then generate .html, .txt, (mondo mysql table?)


    #AsasCatalog.test_fill_asas_catalog_probs()\
    #  - initially (testing) this just retrieves sources from activelearn_algo_class
    #  - but, eventually a function within activelearn_utils.py::insert_tups_into_rdb()
    #      will insert tups into TABLE: asas_catalog_probs, similar to .insert_tups_into_rdb()'s
    #      insert into TABLE: activelearn_algo_class
    # TODO(betsy): need rpy2_classifiers.py:apply_randomforest():L966:for j in range(<<num_classes>>)
    #    - so that asas_catalog_probs will have all potential probs

    # TODO: want to have PHP/HTML which displays sources for a catalog.
    # TODO: want to generate catalog .txt
