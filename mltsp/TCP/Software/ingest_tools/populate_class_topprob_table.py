#!/usr/bin/env python 

""" Populate a table in RDB which contains classification (schema_id, class) and for
    each 5 source src_id which have the top probabilities.

### (20090720):

CREATE TABLE temp_class_srcids_with_classrank0
            (schema_id SMALLINT UNSIGNED,
             class_id SMALLINT UNSIGNED,
             prob FLOAT,
             src_id INT UNSIGNED,
             INDEX(schema_id, class_id, prob))
    AS SELECT schema_id, class_id, prob, src_id
       FROM classid_lookup
       JOIN src_class_probs USING (schema_id, class_id)
       WHERE class_rank=0;

####################################

### (20090722): With RB/nobj ratio cut:   (20090902: takes 51m:41s)

CREATE TABLE temp_class_srcids_with_classrank0
            (schema_id SMALLINT UNSIGNED,
             class_id SMALLINT UNSIGNED,
             prob FLOAT,
             src_id INT UNSIGNED,
             INDEX(schema_id, class_id, prob)) AS
SELECT source_test_db.src_class_probs.schema_id,
       source_test_db.src_class_probs.class_id,
       source_test_db.src_class_probs.prob,
       T1.src_id
FROM  (SELECT src_id FROM object_test_db.obj_srcid_lookup
       JOIN object_test_db.ptf_events AS T5 ON (T5.id=object_test_db.obj_srcid_lookup.obj_id)
       LEFT OUTER JOIN object_test_db.ptf_events AS T4 ON (T4.id=object_test_db.obj_srcid_lookup.obj_id AND
                                                           T4.realbogus > 0.165)
       WHERE src_id > 0
       GROUP BY object_test_db.obj_srcid_lookup.src_id
       HAVING count(T4.id)/count(T5.id) >= 0.61 and
              count(T5.id) >= 7
       ) AS T1
JOIN source_test_db.src_class_probs USING (src_id)
JOIN source_test_db.classid_lookup USING (schema_id, class_id)
WHERE source_test_db.src_class_probs.class_rank=0;




### Post (20091018): only PTF sources (which are jdac_class_name="VarStar").:   (20090902: takes 0m:51s)

CREATE TABLE temp_class_srcids_with_classrank0
            (schema_id SMALLINT UNSIGNED,
             class_id SMALLINT UNSIGNED,
             prob FLOAT,
             src_id INT UNSIGNED,
             INDEX(schema_id, class_id, prob)) AS
SELECT source_test_db.src_class_probs.schema_id,
       source_test_db.src_class_probs.class_id,
       source_test_db.src_class_probs.prob,
       T1.src_id
FROM  (SELECT tcp_source_id AS src_id FROM source_test_db.caltech_classif_summary
       JOIN object_test_db.obj_srcid_lookup ON source_test_db.caltech_classif_summary.tcp_source_id = object_test_db.obj_srcid_lookup.src_id
       JOIN object_test_db.ptf_events AS T5 ON (T5.id=object_test_db.obj_srcid_lookup.obj_id)
       LEFT OUTER JOIN object_test_db.ptf_events AS T4 ON (T4.id=object_test_db.obj_srcid_lookup.obj_id AND
                                                           T4.realbogus > 0.165)
       WHERE src_id > 0 AND
             caltech_classif_summary.jdac_class_name='VarStar'
       GROUP BY object_test_db.obj_srcid_lookup.src_id
       HAVING count(T4.id)/count(T5.id) >= 0.61 and
              count(T5.id) >= 7
       ) AS T1
JOIN source_test_db.src_class_probs USING (src_id)
JOIN source_test_db.classid_lookup USING (schema_id, class_id)
WHERE source_test_db.src_class_probs.class_rank=0;




### This doesnt work the way I want it to, hence I'm writing this script:

SELECT * FROM temp_class_srcids_with_classrank0
         GROUP BY schema_id, class_id
         ORDER BY prob DESC
         LIMIT 200 ;

"""
import os, sys
import MySQLdb


class Populate_Analysis_Tables:
    """ Do all the stuff here.
    """

    def __init__(self, pars={}):
        self.db = MySQLdb.connect(host=pars['mysql_hostname'], \
                                 user=pars['mysql_user'], \
                                 db=pars['mysql_database'], \
                                 port=pars['mysql_port'])
        self.cursor = self.db.cursor()

    def drop_table__class_num_srcids_at_probcut(self):
        """ Do table drop & creates
        """
        try:
            exec_str = "DROP TABLE class_num_srcids_at_probcut"
            self.cursor.execute(exec_str)
        except:
            pass # it is ok to get here since the table may not have existed.


    def drop_create_table__schem_class_top5_srcid(self):
        """ Do table drop & creates
        """
        try:
            exec_str = "DROP TABLE schem_class_top5_srcid"
            self.cursor.execute(exec_str)
        except:
            pass # it is ok to get here since the table may not have existed.
            
        exec_str = """CREATE TABLE schem_class_top5_srcid
                 (schema_id SMALLINT UNSIGNED,
                  class_id SMALLINT UNSIGNED,
                  prob FLOAT,
                  src_id INT UNSIGNED,
                  INDEX(schema_id, class_id))"""
        self.cursor.execute(exec_str)
        

    def query_insert_into__class_srcids_with_classrank0(self, schema_id_low=0, schema_id_high=100000, only_ptf_sources=False):
        """ SELECT and INSERT into table: temp_class_srcids_with_classrank0
        """
        select_str = "SELECT schema_id, class_id FROM classid_lookup WHERE schema_id >= %d AND schema_id <= %d" % \
                                             (schema_id_low, schema_id_high)
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()

        insert_list = ["INSERT INTO schem_class_top5_srcid (schema_id, class_id, prob, src_id) VALUES "]
        
        for (schema_id, class_id) in results:
            if schema_id==2:
                print 'yo'
            if only_ptf_sources:
                # This will only choose PTF sources (which are jdac_class_name="VarStar").
                select_str = "SELECT src_id, prob FROM temp_class_srcids_with_classrank0 INNER JOIN source_test_db.caltech_classif_summary ON temp_class_srcids_with_classrank0.src_id=caltech_classif_summary.tcp_source_id WHERE schema_id=%d AND class_id=%d AND caltech_classif_summary.jdac_class_name='VarStar' ORDER BY prob DESC LIMIT 6" % (schema_id, class_id)
            else:
                select_str = "SELECT src_id, prob FROM temp_class_srcids_with_classrank0 WHERE schema_id=%d AND class_id=%d ORDER BY prob DESC LIMIT 6" % (schema_id, class_id)
            self.cursor.execute(select_str)
            results_2 = self.cursor.fetchall()
            for (src_id, prob) in results_2:
                insert_list.append("(%d, %d, %lf, %d), " % (schema_id, class_id, prob, src_id))

        insert_str = ''.join(insert_list)[:-2]
        self.cursor.execute(insert_str)


    def query_insert_into__class_num_srcids_at_probcut(self):
        """ SELECT and INSERT into table results where:
        we summarize for every (schema,class) the number of srcids
        which pass various class_probability cuts.
        """

        exec_str = """
        CREATE TABLE class_num_srcids_at_probcut 
                 (schema_id SMALLINT UNSIGNED,
                  class_id SMALLINT UNSIGNED,
                  n_src_0perc INT UNSIGNED,
                  n_src_20perc INT UNSIGNED,
                  n_src_50perc INT UNSIGNED,
                  n_src_60perc INT UNSIGNED,
                  n_src_70perc INT UNSIGNED,
                  n_src_80perc INT UNSIGNED,
                  n_src_90perc INT UNSIGNED,
                  INDEX(schema_id, class_id))
SELECT T5.schema_id, T5.class_id,
       T0.src_count AS n_src_0perc,
       T2.src_count AS n_src_20perc,
       T5.src_count AS n_src_50perc,
       T6.src_count AS n_src_60perc,
       T7.src_count AS n_src_70perc,
       T8.src_count AS n_src_80perc,
       T9.src_count AS n_src_90perc
FROM (select schema_id, class_id, count(src_id) AS src_count
      from temp_class_srcids_with_classrank0
                       GROUP BY schema_id, class_id) AS T0 
LEFT OUTER JOIN (select schema_id, class_id, count(src_id) AS src_count
      from temp_class_srcids_with_classrank0
      WHERE prob > 0.2 GROUP BY schema_id, class_id) AS T2 USING (schema_id, class_id)
LEFT OUTER JOIN (select schema_id, class_id, count(src_id) AS src_count
      from temp_class_srcids_with_classrank0
      WHERE prob > 0.5 GROUP BY schema_id, class_id) AS T5 USING (schema_id, class_id)
LEFT OUTER JOIN (select schema_id, class_id, count(src_id) AS src_count
      from temp_class_srcids_with_classrank0
      WHERE prob > 0.6 GROUP BY schema_id, class_id) AS T6 USING (schema_id, class_id)
LEFT OUTER JOIN (select schema_id, class_id, count(src_id) AS src_count
      from temp_class_srcids_with_classrank0
      WHERE prob > 0.7 GROUP BY schema_id, class_id) AS T7 USING (schema_id, class_id)
LEFT OUTER JOIN (select schema_id, class_id, count(src_id) AS src_count
      from temp_class_srcids_with_classrank0
      WHERE prob > 0.8 GROUP BY schema_id, class_id) AS T8 USING (schema_id, class_id)
LEFT OUTER JOIN (select schema_id, class_id, count(src_id) AS src_count
      from temp_class_srcids_with_classrank0
      WHERE prob > 0.9 GROUP BY schema_id, class_id) AS T9 USING (schema_id, class_id)
        """
        self.cursor.execute(exec_str)



    def main(self, schema_id_low=0, schema_id_high=100000, only_ptf_sources=False):
        """ Main function
        """
        self.drop_create_table__schem_class_top5_srcid()
        self.query_insert_into__class_srcids_with_classrank0(schema_id_low=schema_id_low,
                                                             schema_id_high=schema_id_high,
                                                             only_ptf_sources=only_ptf_sources)
        self.drop_table__class_num_srcids_at_probcut()
        self.query_insert_into__class_num_srcids_at_probcut()



if __name__ == '__main__':
    pars = { \
        'mysql_user':"pteluser", \
        'mysql_hostname':"192.168.1.25", \
        'mysql_database':'source_test_db', \
        'mysql_port':3306}

    PopulateAnalysisTables = Populate_Analysis_Tables(pars=pars)
    ### This will do for all TCP sources:
    #PopulateAnalysisTables.main()

    ### This does for just VarStar PTF sources:
    # -> NOTE: you still have to do the "Post (20091018)" CREATE TABLE bit, prior to this...
    PopulateAnalysisTables.main(schema_id_low=41,
                                schema_id_high=100000,
                                only_ptf_sources=True)

    print "done"
