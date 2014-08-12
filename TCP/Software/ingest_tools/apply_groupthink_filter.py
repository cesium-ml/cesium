#!/usr/bin/env python 
"""
   v0.1 First version, using Josh's Grey groupthink .model

INPUT:
    - list of (objid, ra, dec)
    - postgresql server connection to LBL/PTF database.

RETURN:
    - list: obj_id, real_metric

TODO: just format into the expected database output file format.
    - pass in as a stringio filepointer
    - the output .arff file ???doesnt need to be disk-written??? for classification?

"""
import os, sys
try:
    import psycopg2
except:
    print "cant: import psycopg2"
    pass
import ingest_tools
import datetime
import time

sys.path.append(os.path.expandvars('$TCP_DIR/Software/RealBogus/Code/'))
import out2arff

class Classify_LBL_PTF_Using_GroupThink:
    """ This handles applying groputhink real-bogus classifiers to
    LBL PTF candidates.
    """
    def __init__(self, pg_cursor=None):

        self.pg_cursor=pg_cursor

        ptf_candidate_table_columns_tups = \
        [('id','BIGINT'),
         ('sub_id','BIGINT'),
         ('ra','DOUBLE'),
         ('decl','DOUBLE'),# # # # # # # # NOTE: need this to be 'decl' since this is used in MySQL table creation, and a .replace() will catch it for PTF PostgreSQL strings
         #('mag_deep_ref','DOUBLE'),
         ('mag','DOUBLE'),#('mag','DOUBLE'),
         ('mag_err','DOUBLE'),#('mag_err','DOUBLE'),
         ('a_image','DOUBLE'),#('a_major_axis','DOUBLE'),
         ('b_image','DOUBLE'),#('b_minor_axis','DOUBLE'),
         ('flux','DOUBLE'),
         ('flux_err','DOUBLE'),
         ('fwhm', ''),
         ('fwhm_ref', ''),
         ('flag', ''),
         ('mag_ref', ''),
         ('mag_ref_err', ''),
         ('a_ref', ''),
         ('b_ref', ''),
         ('n2sig3', ''),
         ('n3sig3', ''),
         ('n2sig5', ''),
         ('n3sig5', ''),
         ('nmask', ''),
         ('pos_sub', ''),
         ('nn_dist', ''),
         ('f_aper', ''),
         ('flux_aper', ''),
         ('x_sub', ''),
         ('y_sub', ''),
         #('mag_sub','DOUBLE'),
         #('nn_a','DOUBLE'),
         #('nn_b','DOUBLE'),
         #('nn_ra','DOUBLE'),
         #('nn_dec','DOUBLE'),
         #('nn_dist','DOUBLE'), # This is no longer a NN distinct from the candidate
         #('nn_mag','DOUBLE'),
         #('nn_sigma_mag','DOUBLE'),
         #('nn_star2galaxy_sep','DOUBLE'),
         #('percent_incr','DOUBLE'),
         #('sigma_mag_deep_ref','DOUBLE'),
         #('sigma_mag_sub','DOUBLE'),
         #('surface_brightness','DOUBLE'),
         ('ra_rms','DOUBLE'),   # REQUIRED, not in PostgreSQL, but is in MySQL table
         ('dec_rms','DOUBLE'),] # REQUIRED, not in PostgreSQL, but is in MySQL table #[0..21]

        ptf_sub_table_columns_tups = \
           [('ujd','DOUBLE'), #('ujd_proc_image','DOUBLE'),
            ('filter','VARCHAR(20)'),
            ('lmt_mg_ref', ''),
            ('seeing_new',''),
            ('seeing_ref',''),
            ('objs_saved',''),
            ('good_pix_area', ''),
            ] #('filter_num','INT')

        self.ptf_candidate_table_columns_list = []
        for a_tup in ptf_candidate_table_columns_tups:
            self.ptf_candidate_table_columns_list.append(a_tup[0])

        self.ptf_sub_table_columns_list = []
        for a_tup in ptf_sub_table_columns_tups:
            self.ptf_sub_table_columns_list.append(a_tup[0])

        self.ptf_postgre_select_columns = ("candidate.%s, subtraction.%s" % (\
                  ', candidate.'.join(self.ptf_candidate_table_columns_list[:-2]), 
                  ', subtraction.'.join(self.ptf_sub_table_columns_list))).replace('decl','dec')

        ### Import some modules:
        try:
            import jpype
        except:
            print "EXCEPT: import jpype"
        import weka_classifier
        os.environ["JAVA_HOME"] = '/usr/lib/jvm/java-6-sun-1.6.0.03'
        os.environ["CLASSPATH"] += os.path.expandvars(':$TCP_DIR/Software/ingest_tools')
        if not jpype.isJVMStarted():
            #TODO / DEBUG: disable the next line for speed-ups once stable?
        	_jvmArgs = ["-ea"] # enable assertions
        	_jvmArgs.append("-Djava.class.path=" + \
                                os.environ["CLASSPATH"])
        	jpype.startJVM(jpype.getDefaultJVMPath(), *_jvmArgs)

        model_fpath = '/home/pteluser/scratch/groupthink_training/PTFgray-short-weka357.model'
        training_arff_fpath = '/home/pteluser/scratch/groupthink_training/PTFgray-short-train-noid.arff'

        self.wc = weka_classifier.WekaClassifier(model_fpath, training_arff_fpath) #generated_arff_fpath)

        import assemble_classification_results

        self.seps_dict = {}
        for elem in assemble_classification_results.seps:
            self.seps_dict.update(elem)


    def get_groupthink_classifications(self, id_low=0, id_high=0):
        """ Given a range of lbl ptf candidate ids, here we get groupthink/RealBogus
        classification results for each object.

        NOTE: ptf_master..insert_pgsql_ptf_objs_into_mysql() does pass candidate.ids into id_low,id_high
        """
        select_str = """ SELECT %s
    FROM candidate
    JOIN subtraction ON (candidate.sub_id = subtraction.id)
    WHERE candidate.id >= %d AND
          candidate.id <= %d
        """ % (self.ptf_postgre_select_columns, id_low, id_high)
        do_pgsql_query = True
        while do_pgsql_query:
            try:
                self.pg_cursor.execute(select_str)
                rdb_rows = self.pg_cursor.fetchall()
                do_pgsql_query = False
            except:
                try:
                    import psycopg2 # KLUDGE
                except:
                    pass
                print datetime.datetime.utcnow(), 'EXCEPT near apply_groupthink_filter.py:L147: self.pg_cursor.execute().   Waiting 30 secs...'
                time.sleep(30) # something happened to the LBL PostgreSQL server.  Wait a bit.
                try:
                    conn = psycopg2.connect(\
                          "dbname='%s' user='%s' host='%s' password='%s' port=%d" % \
                            (ingest_tools.pars['ptf_postgre_dbname'],\
                             ingest_tools.pars['ptf_postgre_user'],\
                             ingest_tools.pars['ptf_postgre_host'],\
                             ingest_tools.pars['ptf_postgre_password'],\
                             ingest_tools.pars['ptf_postgre_port']))
                    self.pg_cursor = conn.cursor()
                except:
                    print "unable to do: conn = psycopg2.connect()"


        #self.pg_cursor.execute(select_str)
        #rdb_rows = self.pg_cursor.fetchall()

        out_list = [("%s|%s" % (\
                  '|'.join(self.ptf_candidate_table_columns_list[:-2]), 
                  '|'.join(self.ptf_sub_table_columns_list))).replace('decl','dec')]

        rownum_lblid_lookup = {}
        for i,row in enumerate(rdb_rows):
            rownum_lblid_lookup[i] = row[0]
            line_str = ''
            for elem in row:
                line_str += str(elem) + '|'
            out_list.append(line_str[:-1])

        out_tup_list = out2arff.writearff(infile_readlines=out_list) #, outfile=generated_arff_fpath)

        #sh_cmd_str = "java -Xms512m -Xmx1024m  weka.classifiers.meta.MetaCost -T %s -l %s -p 0 -distribution" % (generated_arff_fpath, model_fpath)
        #print sh_cmd_str
        #print generated_arff_fpath

        id_classif_dict = {} # {<id>:{'realbogus':<>, 'bogus':<>, 'suspect':<>, 'unclear':<>, ...}
        for i, arff_record in enumerate(out_tup_list):
            classified_result = self.wc.get_class_distribution(arff_record)
            total_match_percentage = 0.0
            obj_realbogus_dict = {}
            for class_type,class_val in classified_result:
                value = self.seps_dict[class_type]['w'] * class_val
                total_match_percentage += value
                obj_realbogus_dict[class_type] = value
            #id_classif_dict[rownum_lblid_lookup[i]] = total_match_percentage
            obj_realbogus_dict['realbogus'] = total_match_percentage
            id_classif_dict[rownum_lblid_lookup[i]] = obj_realbogus_dict
            #print rownum_lblid_lookup[i], total_match_percentage, '::', classified_result
        return id_classif_dict
        ################
            # TODO: now do the above functionality in a method which can be called by ptf_master # # # # when 1000 rows are available.
            # TODO: use 0.50 as the cut.
            # TODO: restart the ptf_master system. 


    def get_ptf_rows_with_good_classification(self, ptf_rows,
                                           id_classif_dict={}, gt_perc_cut=0.9):
        """  Apply RealBogus percentage cut to row/candidate.id found
        classifications.
        """
        out_good_rows = []
        for row in ptf_rows:
            if id_classif_dict.get(row[0],0.0) >= gt_perc_cut:
                out_good_rows.append(row)
        return out_good_rows


if __name__ == '__main__':

    #test_ptf_rows = [ \
    #(767466 ,1),
    #(767467 ,1),
    #(767468 ,1),
    #(767469 ,1),
    #(767470 ,1),
    #(767471 ,1),
    #(767472 ,1),
    #(767473 ,1)]

    test_ptf_rows = [ \
               (4154373 ,1)]
    id_low=4154373
    id_high=4154373

    pars = ingest_tools.pars

    conn = psycopg2.connect(\
         "dbname='%s' user='%s' host='%s' password='%s' port=%d" % \
                        (pars['ptf_postgre_dbname'],\
                         pars['ptf_postgre_user'],\
                         pars['ptf_postgre_host'],\
                         pars['ptf_postgre_password'],\
                         pars['ptf_postgre_port']))
    pg_cursor = conn.cursor()

    Classify_LBL_PTF_Using_GT = Classify_LBL_PTF_Using_GroupThink(pg_cursor=pg_cursor)

    id_classif_dict = Classify_LBL_PTF_Using_GT.get_groupthink_classifications(id_low=id_low, id_high=id_high)
    real_rows = Classify_LBL_PTF_Using_GT.get_ptf_rows_with_good_classification( \
                        test_ptf_rows,
                        id_classif_dict=id_classif_dict,
                        gt_perc_cut=0.05)
    for row in real_rows:
        print row[0], id_classif_dict[row[0]], row

    print 'done'
