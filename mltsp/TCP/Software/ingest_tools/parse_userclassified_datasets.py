#!/usr/bin/env python 
"""
TODO: parse out rrlyrae and other variables

 - need to store these in a TABLE
 - need to qyery these sources ra,dec to find correlated TCP source
 - need to store the correlated TCP source ids

#for RRL.tgz:
tar
cd RRLData
ipython --pylab
import pl        # this has way of making use of these files

"""
from __future__ import print_function
from __future__ import absolute_import
import os, sys
import copy
import numpy
import MySQLdb
import reevaluate_feat_class
from . import get_classifications_for_tcp_marked_variables
from . import ptf_master
from . import ingest_tools

# For NON-PARALLEL:
sys.path.append(os.environ.get("TCP_DIR") + '/Software/feature_extract/MLData')
import arffify

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


class Data_Parse(DB_Connector):
    """ Parse various classified source data files
    """
    def __init__(self, pars={}):
        self.pars = pars

        if self.pars['do_lbl_check']:
            self.DiffObjSourcePopulator = ptf_master.Diff_Obj_Source_Populator(use_postgre_ptf=True)
            self.PTFPostgreServer = ptf_master.PTF_Postgre_Server(pars=ingest_tools.pars, \
                                                     rdbt=self.DiffObjSourcePopulator.rdbt)



    def extract_variables_orig_csv(self, csv_fpath=''):
        """ extract a dict from variables .csv file & return dict.
        """
        out_dict = {}

        fp = open(csv_fpath)
        #a_line = fp.read()
        #a_list = a_line.replace('"','').split(',')

        col_names = ["otype","jsb_source_id","main_id","z_redshift","jsb_cand_id","lu_matches","rb_scale","rb_model_id","unclear","mag_ref","objs_extracted","sym_scale_simp","sym_scale","bogus","rb_scale_simp","dec","objs_saved","realbogus","rb_shape_score","rb_shape_str","lbl_id","ellip","ra","ujd","lmt_mg_new","pos_sub","a_image","b_image","suspect","sym","mag","merr","realish","sub_id","maybe","nn_dist","jsb_source_id_2","rock_run","is_rock","has_bright_star_been_checked","is_near_bright_star","f_aper","filter","flux_aper","sub_zp","ub1_zp_ref","a_ref","b_ref","mtotal","fwhm_ref","fwhm","seeing_ref","seeing_new","bestz","best_host_type"]
        type_list = ["S20","i4","S20","f4","i4","i4","f4","i4","f4","f4","i4","f4","f4","f4","f4","f4","i4","f4","f4","S20","i4","f4","f4","f4","f4","i4","f4","f4","f4","f4","f4","f4","f4","i4","f4","f4","i4","S20","S20","S20","S20","f4","S20","f4","f4","f4","f4","f4","f4","f4","f4","f4","f4","S20","S20"]

        all_data_dict = {}
        mac_bigline = fp.readlines()
        lines = mac_bigline[0].split('\r')
        for line in lines[1:]:
            if len(line) == 0:
                continue
            data_dict = {}
            cols_list = line.replace('"','').split(',')
            for i,val in enumerate(cols_list):
                if 'i' in type_list[i]:
                    data_dict[col_names[i]] = int(val)
                elif 'f' in type_list[i]:
                    if val == 'nul':
                        data_dict[col_names[i]] = None
                    else:
                        data_dict[col_names[i]] = float(val)
                else:
                    data_dict[col_names[i]] = str(val)
            src_id = data_dict['jsb_source_id'] # ['main_id']
            if src_id not in all_data_dict:
                all_data_dict[src_id] = {'src_id':src_id,
                                         'class_type':data_dict['otype'],
                                         'ra':data_dict['ra'],
                                         'dec':data_dict['dec'],
                                         'ts':{'ujd':[],
                                               'mtotal':[],
                                               'merr':[],
                                               'lbl_id':[],
                                               'filt':[]}}
            
            all_data_dict[src_id]['ts']['ujd'].append(data_dict['ujd'])
            all_data_dict[src_id]['ts']['mtotal'].append(data_dict['mtotal'])
            all_data_dict[src_id]['ts']['merr'].append(data_dict['merr'])
            all_data_dict[src_id]['ts']['lbl_id'].append(data_dict['lbl_id'])
            all_data_dict[src_id]['ts']['filt'].append(data_dict['filter'])

        for src_id,src_dict in all_data_dict.iteritems():
            for a_name, a_list in src_dict['ts'].iteritems():
                src_dict['ts'][a_name] = numpy.array(a_list)
        
        return all_data_dict


    def extract_variables_ceph_eb_csv(self, csv_fpath='', max_srcid=None):
        """ extract a dict from variables .csv file & return dict.
        """
        out_dict = {}

        srcid_lookup = {}

        fp = open(csv_fpath)
        #a_line = fp.read()
        #a_list = a_line.replace('"','').split(',')

        col_names = ["lbl_id","ra","dec","simbad_type","simbad_name","ujd","mtotal","merr","pos_sub","mag","realbogus","filter"]
        type_list = ["i4",    "f4","f4",  "S20",        "S20",       "f4", "f4",    "f4",  "i4",     "f4", "f4",       "S3"]

        all_data_dict = {}
        mac_bigline = fp.readlines()
        lines = mac_bigline[0].split('\r')
        for line in lines[1:]:
            if len(line) == 0:
                continue
            data_dict = {}
            cols_list = line.replace('"','').split(',')
            for i,val in enumerate(cols_list):
                if 'i' in type_list[i]:
                    data_dict[col_names[i]] = int(val)
                elif 'f' in type_list[i]:
                    if val == 'nul':
                        data_dict[col_names[i]] = None
                    else:
                        data_dict[col_names[i]] = float(val)
                else:
                    data_dict[col_names[i]] = str(val)
            if data_dict['simbad_name'] not in srcid_lookup:
                max_srcid += 1
                srcid_lookup[data_dict['simbad_name']] = copy.copy(max_srcid) # data_dict['simbad_name'] # ['main_id']
            src_id = srcid_lookup[data_dict['simbad_name']]
            if src_id not in all_data_dict:
                all_data_dict[src_id] = {'src_id':src_id,
                                         'class_type':data_dict['simbad_type'],
                                         'ra':data_dict['ra'],
                                         'dec':data_dict['dec'],
                                         'ts':{'ujd':[],
                                               'mtotal':[],
                                               'merr':[],
                                               'lbl_id':[],
                                               'filt':[]}}
            
            all_data_dict[src_id]['ts']['ujd'].append(data_dict['ujd'])
            all_data_dict[src_id]['ts']['mtotal'].append(data_dict['mtotal'])
            all_data_dict[src_id]['ts']['merr'].append(data_dict['merr'])
            all_data_dict[src_id]['ts']['lbl_id'].append(data_dict['lbl_id'])
            all_data_dict[src_id]['ts']['filt'].append(data_dict['filter'])

        for src_id,src_dict in all_data_dict.iteritems():
            for a_name, a_list in src_dict['ts'].iteritems():
                src_dict['ts'][a_name] = numpy.array(a_list)
        
        return all_data_dict


    def extract_rrlyrae(self):
        """ extract rrlyrae info from files and return dict.

        These are RRLyrae from stripe 82, with PTF detections
        """
        out_dict = {}

        all_rrl =  numpy.loadtxt("/home/pteluser/src/TCP/Data/RRLData/summary.dat",
                                 dtype={'names': ('sesar_id', 'class_type', 'nPTF', 'period','a','ra', 'dec', 'g','r', 'ptfname'),
                                        'formats': ('i4', 'S5', 'i4', 'f4','f4','f4', 'f4', 'f4','f4', 'S5')},
                                 usecols=(0,1,2,3,4,5,6,8,9,12))

        for (sesar_id, class_type, jsb_nepochs, period, ampl, ra, dec, mag_g, mag_r, ptfname) in all_rrl:
            out_dict[sesar_id] = {'src_id':sesar_id,
                                  'class_type': 'rrlyrae_' + class_type,
                                  'jsb_nepochs':jsb_nepochs,
                                  'period':period,
                                  'ampl':ampl,
                                  'ra':ra,
                                  'dec':dec,
                                  'mag_g':mag_g,
                                  'mag_r':mag_r,
                                  'ptfname':ptfname,
                                  'ts':{}}
            
            # need to do an os.listdir() and iterate over all of these and store into a dict.

            fpath = "%s/rrl%d.dat" % (self.pars['rrlyra_data_dirpath'], sesar_id)
            rrl =  numpy.loadtxt(fpath,
                                 dtype={'names':('sesar_id', 'ujd', 'mag', 'merr', 'lmt_mg_new', 'pos_sub', 'filt',
                                                 'mtotal', 'ub1_zp_ref', 'mag_ref', 'flux_aper', 'f_aper', 'lbl_id'),
                                        'formats': ('i4',"f8","f4","f4",'f4', "i4","S1","f4","f4","f4","f4","f4", 'i4')},
                                 usecols=(0,1,2,3,4,5,6,7,8,9,10,11,12))

            out_dict[sesar_id]['ts']['ujd'] = rrl['ujd']
            out_dict[sesar_id]['ts']['mtotal'] = rrl['mtotal']
            out_dict[sesar_id]['ts']['merr'] = rrl['merr']
            out_dict[sesar_id]['ts']['lbl_id'] = rrl['lbl_id']
            out_dict[sesar_id]['ts']['filt'] = rrl['filt']

        return out_dict


    def create_tables(self):
        """ Create tables.
        """
        create_str = "CREATE TABLE %s (jsb_srcid INT UNSIGNED, lbl_id BIGINT, ujd DOUBLE, mag_err FLOAT, mag_total FLOAT, filt VARCHAR(3), INDEX(jsb_srcid))" % (self.pars['data_tablename'])
        self.cursor.execute(create_str)

        create_str = "CREATE TABLE %s (jsb_srcid INT UNSIGNED, tcp_srcid INT UNSIGNED, class_type VARCHAR(40), ra DOUBLE, decl DOUBLE, jsb_period DOUBLE, jsb_amp DOUBLE, INDEX(jsb_srcid), INDEX(tcp_srcid))" % (self.pars['lookup_tablename'])
        self.cursor.execute(create_str)


    def hack__update_table_values(self, data_dict={}, jsb_tcp_srcid_lookup={}):
        """ A Hack for temporoary table fix.
        """

        for src_id, src_dict in data_dict.iteritems():
            #tcp_srcid = "Null"
            #if jsb_tcp_srcid_lookup[src_dict['src_id']] != None:
            #    tcp_srcid = str(jsb_tcp_srcid_lookup[src_dict['src_id']]['tcp_srcid'])
            update_str = "UPDATE %s SET jsb_period=%lf, jsb_amp=%lf WHERE (jsb_srcid=%d)" % ( \
                               self.pars['lookup_tablename'],
                               src_dict['period'],
                               src_dict['ampl'],
                               src_dict['src_id'])
            self.cursor.execute(update_str)


    def insert_data_into_tables(self, data_dict={}, jsb_tcp_srcid_lookup={}):
        """
        """
        ### Data Table:

        insert_list = ["INSERT INTO %s (jsb_srcid, lbl_id, ujd, mag_err, mag_total, filt) VALUES " % (self.pars['data_tablename'])]

        for src_id, src_dict in data_dict.iteritems():
            if src_dict['ts']['ujd'].size == 1:
                insert_list.append('(%d, %d, %lf, %lf, %lf, "%s"), ' % ( \
                                   src_dict['src_id'],
                                   src_dict['ts']['lbl_id'],
                                   src_dict['ts']['ujd'],
                                   src_dict['ts']['merr'],
                                   src_dict['ts']['mtotal'],
                                   src_dict['ts']['filt']))
            else:
                for i in xrange(src_dict['ts']['ujd'].size):
                    insert_list.append('(%d, %d, %lf, %lf, %lf, "%s"), ' % ( \
                                   src_dict['src_id'],
                                   src_dict['ts']['lbl_id'][i],
                                   src_dict['ts']['ujd'][i],
                                   src_dict['ts']['merr'][i],
                                   src_dict['ts']['mtotal'][i],
                                   src_dict['ts']['filt'][i]))
        if len(insert_list) > 1:
            self.cursor.execute(''.join(insert_list)[:-2])

        ### Lookup table:
        insert_list = ["INSERT INTO %s (jsb_srcid, tcp_srcid, class_type, ra, decl, jsb_period, jsb_amp) VALUES " % (self.pars['lookup_tablename'])]

        for src_id, src_dict in data_dict.iteritems():
            tcp_srcid = "Null"
            if jsb_tcp_srcid_lookup[src_dict['src_id']] != None:
                tcp_srcid = str(jsb_tcp_srcid_lookup[src_dict['src_id']]['tcp_srcid'])
            insert_list.append('(%d, %s, "%s", %lf, %lf), ' % ( \
                                   src_dict['src_id'],
                                   tcp_srcid,
                                   src_dict['class_type'],
                                   src_dict['ra'],
                                   src_dict['dec'],
                                   src_dict['period'],
                                   src_dict['amp']))
        if len(insert_list) > 1:
            self.cursor.execute(''.join(insert_list)[:-2])
        

    def match_jsb_sources_with_tcp_sources(self, data_dict={}):
        """  This queries the srcid_lookup table an finds the best matching source
        for the given JSB source's (ra,dec).
        """
        jsb_tcp_srcid_lookup = {}

        for src_dict in data_dict.values():
            src_id = src_dict['src_id']

            if self.pars['do_lbl_check']:
                get_classifications_for_tcp_marked_variables.\
                                      populate_TCP_sources_for_nonptf_radec( \
                                         ra=src_dict['ra'], dec=src_dict['dec'], \
                                         PTFPostgreServer=self.PTFPostgreServer, \
                                         DiffObjSourcePopulator=self.DiffObjSourcePopulator)

            ra_low = src_dict['ra'] - (self.pars['spatial_query_box_length'] / 2.)
            ra_high = src_dict['ra'] + (self.pars['spatial_query_box_length'] / 2.)
            dec_low = src_dict['dec'] - (self.pars['spatial_query_box_length'] / 2.)
            dec_high = src_dict['dec'] + (self.pars['spatial_query_box_length'] / 2.)
            
            select_str = "SELECT count(%s.obj_id), src_id FROM %s JOIN %s USING (src_id) WHERE DIF_HTMRectV(%lf, %lf, %lf, %lf) GROUP BY src_id" % ( \
                               self.pars['obj_srcid_lookup_tablename'],
                               self.pars['srcid_lookup_htm_tablename'],
                               self.pars['obj_srcid_lookup_tablename'],
                               ra_low, dec_low, ra_high, dec_high)

            self.cursor.execute(select_str)

            rows = self.cursor.fetchall()

            ### KLUDGE: I assume that the source with the greatest number of epochs is associated with our source.

            tup_list = []
            for row in rows:
                tup_list.append(row)

            tup_list.sort(reverse=True)
            jsb_tcp_srcid_lookup[src_id] = None
            if len(tup_list) > 0:
                jsb_tcp_srcid_lookup[src_id] = {'jsb_srcid':src_id,
                                                'tcp_nobjs':tup_list[0][0],
                                                'tcp_srcid':tup_list[0][1]}
        return jsb_tcp_srcid_lookup


    def get_max_jsb_srcid(self):
        """
        """

        select_str = "SELECT max(jsb_srcid) FROM %s" % ( \
            self.pars['lookup_tablename'])

        self.cursor.execute(select_str)

        rows = self.cursor.fetchall()

        max_srcid = rows[0][0]
        return max_srcid


    def parse_insert_dict_into_table(self):
        """
        """
        rr_dict = self.extract_rrlyrae()
        rrlyrae_srcid_lookup = self.match_jsb_sources_with_tcp_sources(data_dict=rr_dict)
        ###self.hack__update_table_values(data_dict=rr_dict)#, jsb_tcp_srcid_lookup=rrlyrae_srcid_lookup) # FOR TEMP FIX
        ###sys.exit()
        self.insert_data_into_tables(data_dict=rr_dict, jsb_tcp_srcid_lookup=rrlyrae_srcid_lookup)

        csv_vars_dict = self.extract_variables_orig_csv(csv_fpath=self.pars['variables_csv_fpath'])
        csv_vars_srcid_lookup = self.match_jsb_sources_with_tcp_sources(data_dict=csv_vars_dict)
        self.insert_data_into_tables(data_dict=csv_vars_dict, jsb_tcp_srcid_lookup=csv_vars_srcid_lookup)

        max_srcid = self.get_max_jsb_srcid()
        csv_vars_dict = self.extract_variables_ceph_eb_csv(csv_fpath=self.pars['ceph_eb_csv_fpath'], max_srcid=max_srcid)
        csv_vars_srcid_lookup = self.match_jsb_sources_with_tcp_sources(data_dict=csv_vars_dict)
        self.insert_data_into_tables(data_dict=csv_vars_dict, jsb_tcp_srcid_lookup=csv_vars_srcid_lookup)


    def retrieve_jsbclass_sources_from_rdb_write_xmls(self):
        """ This retrieves from RDB the tcp sources & writes them into XMLs (with user classes)

        Ideally this is run in parallel.
        """
        # Now I want to take the tcp_srcids & insert into 
        #  - so, given a tcp src_id, I want to generate the features
        #  - and with features in an XML file/string, I want to add to a .arff file
        ReevaluateFeatClass = reevaluate_feat_class.Reevaluate_Feat_Class(cursor=self.cursor)

        select_str = "SELECT tcp_srcid, class_type FROM %s WHERE tcp_srcid IS NOT NULL" % ( \
                      self.pars['lookup_tablename'])

        srcid_list = []
        class_list = []
        self.cursor.execute(select_str)
        rows = self.cursor.fetchall()
        for row in rows:
            srcid_list.append(row[0])
            class_list.append(row[1])
            
        for i, tcp_srcid in enumerate(srcid_list):
            xml_out_fpath = "%s/%d.xml" % (self.pars['intermed_xmls_dirpath'], tcp_srcid)
            if os.path.exists(xml_out_fpath):
                continue # skip this since the xml file already exists and thus its features were generated
            
            (srcid_xml_tuple_list, n_objs) = ReevaluateFeatClass.reeval_get_xml_tuplelist(src_id=tcp_srcid)

            xml_str = srcid_xml_tuple_list[0][1]

            i_b4_vosource = xml_str.rfind('</VOSOURCE>')

            class_str = """  <Classifications>
    <Classification type="human">
      <source type="tcp">
        <link></link>
        <name>None</name>
        <version>1.0</version>
        <comments>Retrieved from JSB astronomer classifications</comments>
      </source>
      <class name="%s" dbname="%s" prob="1.000000">
      </class>
    </Classification>
  </Classifications>
</VOSOURCE>""" % (class_list[i], class_list[i])

            new_xml_str = xml_str[:i_b4_vosource] + class_str
            fp = open(xml_out_fpath, 'w')
            fp.write(new_xml_str)
            fp.close()
            # TODO: write into files

            # OBSOLETE:
            # TODO: now we send this to arffify code.
            #   - need to disable the use fo existing class-name schema in arffify.py
            #a = arffify.Maker(search=[], skip_class=False, local_xmls=True, convert_class_abrvs_to_names=False, flag_retrieve_class_abrvs_from_TUTOR=False, dorun=False)
            #out_dict = a.generate_arff_line_for_vosourcexml(num=str(tcp_srcid), xml_fpath=new_xml_str)
            #print 
            #print out_dict['class']
            #rrlyrae_ab
        
        ############# TODO: I need to mark / fill in the <classification>
        # Maybe just pass the classifcations into function - vosource_class_obj.add_classif_prob()
        #   - so that db_importer.py:1012   "class" is inserted into sdict.
        # Otherwise, need to be able to just kludgily insert the <class> bit into the vosoure string
        #   - look at arffify.py L819 parsing of classification



        ##########
        #  - maybe similar to test4.sh's:
        #     ./generate_weka_classifiers.py -u surveynoise_linearlombfreq  --n_noisified_per_orig_vosource=50 --n_epochs=20 --n_sources_needed_for_class_inclusion=10 --fit_metric_cutoff=0.1 --regenerate_features --train_mode

        # Once I have a directory of xmls, I can run (freemind generate_weka_classifier.py) example to generate a .arff
        #    - but, it seems that there may be constrainets on class_names, which conflicts with
        #          the custom JSB class names

        # -> so I could just somehow store the classifications in the vosource xmls.

        # -> ??? so is there an arffify.py code which just generates a .arff using some generic XML without
        #                an assumed set of classnames?
        #      - arffify.py.generate_arff_line_for_vosourcexml(xml_fpath)
        #          -> this will use a <class> in the vosource.xml file
        #NO:  ${TCP_DIR}Software/ingest_tools/regenerate_vosource_xmls.py --old_xmls_dirpath=%s --new_xmls_dirpath=%s
        # This probably forms an xml using some timeseries:
        #   ${TCP_DIR}Software/Noisification/generate_noisy_tutor.py --reference_xml_dir=%s --n_noisified_per_orig_vosource=%d --noisified_xml_final_dirpath=%s --n_epochs_in_vosource=%d --archive_dirpath=%s --progenitor_class_list_fpath=%s --fit_metric_cutoff=%s %s
        #    NoisificationWrapper.main(common_fpath=fpath, pref_filter=pref_filter, n_epochs=n_epochs, n_noisif_vosource_per_reference=n_noisif_vosource_per_reference, srcid_time_array=srcid_time_array)
        # ... see generic_observatory_LGC.py to see how to custom form a vosource.xml from a data structure and store in an xml string
        ##### ingest_tools.py : get_vosourcelist_for_ptf_using_srcid()


        print()

        # TODO: ? What will arff generation code want?
        #    - want to generate arff with PTF/TCP data but user-classifications.


        # TODO store this in a table?    match with TCP sources?
        # - store all sources in one table and timeseries data
        #    srcid, t , m_tot, m_err, filt
        # - store tcp_srcid, other_srcid lookup in another table
        #    jsb_srcid (sesar_id or candidate_id), ptf_candidate_id, tcp_srcid
        #        ra, dec, class_name, period
        

    def generate_classifications(self, schema_str=""):
        """
        """
        from IPython.kernel import client # 20091202 added
        ##### Do classifications using schema
        from . import get_classifications_for_ptf_srcid_and_class_schema
        IpythonTaskController = get_classifications_for_ptf_srcid_and_class_schema.\
                                     Ipython_Task_Controller(schema_str=schema_str)
        IpythonTaskController.initialize_ipengines()
        #IpythonTaskController.spawn_tasks()

        srcid_list = []
        select_str = 'SELECT tcp_srcid FROM ' + self.pars['lookup_tablename'] + ' WHERE tcp_srcid IS NOT NULL AND (class_type LIKE "%rrl%" OR class_type LIKE "%EB%" OR class_type LIKE "\%epheid\%")'

        self.cursor.execute(select_str)
        rows = self.cursor.fetchall()
        for row in rows:
            srcid_list.append(row[0])

        list_incr = 5
        for i_low in xrange(0, len(srcid_list), list_incr):
            short_srcid_list = srcid_list[i_low:i_low + list_incr]
            if 0:
                ### For debugging only:
                from . import classification_interface
                from . import plugin_classifier
                from . import get_classifications_for_ptf_srcid_and_class_schema
                Get_Classifications_For_Ptf_Srcid = get_classifications_for_ptf_srcid_and_class_schema.GetClassificationsForPtfSrcid(schema_str=schema_str)
                Get_Classifications_For_Ptf_Srcid.main(src_id=short_srcid_list[0])
            exec_str = """schema_str="%s"
for src_id in srcid_list:
    try:
        if True:
            Get_Classifications_For_Ptf_Srcid.main(src_id=src_id)
    except:
        pass # skipping this srcid""" % (schema_str)
            taskid = IpythonTaskController.tc.run(client.StringTask(exec_str, \
                                                   push={'srcid_list':short_srcid_list}))


        IpythonTaskController.wait_for_tasks_to_finish()

        ### TODO: query the classification results table and
        #      summarize the classification results: success rates.
        #    - initially in some print out, later in some table / PHP page.


    def make_freq_nepoch_plot(self):
        """
        """
        import matplotlib
        import matplotlib.pyplot as pyplot
        from matplotlib import rcParams
        import numpy

        select_str = """select source_test_db.feat_values.feat_val, count(object_test_db.obj_srcid_lookup.obj_id) AS n_epochs, object_test_db.obj_srcid_lookup.src_id from source_test_db.jsbvars_lookup
JOIN source_test_db.feat_values ON (feat_values.src_id=source_test_db.jsbvars_lookup.tcp_srcid)
JOIN object_test_db.obj_srcid_lookup ON (object_test_db.obj_srcid_lookup.src_id=feat_values.src_id)
WHERE feat_id=1718 AND class_type like "%rrl%"
group by object_test_db.obj_srcid_lookup.src_id
order by feat_val"""

        periods = []
        nepochs = []
        self.cursor.execute(select_str)
        rows = self.cursor.fetchall()
        for row in rows:
            periods.append(row[0])
            nepochs.append(row[1])
        periods = numpy.array(periods)
        nepochs = numpy.array(nepochs)
        self.fig = pyplot.figure(figsize=(9,11), dpi=300)
        ax = self.fig.add_subplot('111')

        pyplot.plot(nepochs, periods, 'ro')
        ax.set_xlabel('n_epochs')
        ax.set_ylabel('frequency')
        ax.set_title('JSB user-classified vars: RRLyrae*')

        fpath = "/tmp/rrlyrae_nepoch_freqs.ps"
        pyplot.savefig(fpath)


    def make_jsbfreq_tcpfreq_plot(self):
        """
        """
        import matplotlib
        import matplotlib.pyplot as pyplot
        from matplotlib import rcParams
        import numpy

        select_str = """select source_test_db.feat_values.feat_val, count(object_test_db.obj_srcid_lookup.obj_id) AS n_epochs, object_test_db.obj_srcid_lookup.src_id, source_test_db.jsbvars_lookup.jsb_period from source_test_db.jsbvars_lookup
JOIN source_test_db.feat_values ON (feat_values.src_id=source_test_db.jsbvars_lookup.tcp_srcid)
JOIN object_test_db.obj_srcid_lookup ON (object_test_db.obj_srcid_lookup.src_id=feat_values.src_id)
WHERE feat_id=1718 AND class_type like "%rrl%"
group by object_test_db.obj_srcid_lookup.src_id
order by feat_val"""

        tcp_freqs = []
        jsb_freqs = []
        nepochs = []
        self.cursor.execute(select_str)
        rows = self.cursor.fetchall()
        for row in rows:
            tcp_freqs.append(row[0])
            nepochs.append(row[1])
            jsb_freqs.append(1.0 / row[3])
        tcp_freqs = numpy.array(tcp_freqs)
        jsb_freqs = numpy.array(jsb_freqs)
        nepochs = numpy.array(nepochs)
        nepochs_normalized = (numpy.array(nepochs) - numpy.min(nepochs)) / (float(numpy.max(nepochs)) - numpy.min(nepochs))
        self.fig = pyplot.figure(figsize=(9,11), dpi=300)
        ax = self.fig.add_subplot('111')

        #pyplot.plot(nepochs, tcp_freqs, 'ro')
        #ax.set_xlabel('n_epochs')
        #pyplot.plot(jsb_freqs, tcp_freqs, 'bo')
        scat = pyplot.scatter(jsb_freqs, tcp_freqs, c=nepochs_normalized, s=(nepochs_normalized * 100.0))
        scat.set_alpha(0.75)
        pyplot.plot(numpy.array([1.0,3.5]), numpy.array([1.0,3.5]), 'r')
        ax.set_xlabel('JSB/SDSS freq')
        ax.set_ylabel('TCP freq')
        ax.set_title('JSB user-classified vars: RRLyrae*')

        fpath = "/tmp/rrlyrae_jsbfreq_tcpfreq.ps"
        pyplot.savefig(fpath)


    def make_jsbfreq_best_tcpfreq_plot(self, class_glob_str="rrl"):
        """
        """
        import matplotlib
        import matplotlib.pyplot as pyplot
        from matplotlib import rcParams
        import numpy

        freq_feat_id_dict = {'freq1':{'feat_id':1718},
                             'freq2':{'feat_id':1520},
                             'freq3':{'feat_id':89}}
        all_freq_dict = {}
        for freq_name, freq_dict in freq_feat_id_dict.iteritems():
            select_str = """select source_test_db.feat_values.feat_val, count(object_test_db.obj_srcid_lookup.obj_id) AS n_epochs, object_test_db.obj_srcid_lookup.src_id, source_test_db.jsbvars_lookup.jsb_period, source_test_db.one_src_model_class_probs.class_name
FROM source_test_db.jsbvars_lookup
JOIN source_test_db.feat_values ON (feat_values.src_id=source_test_db.jsbvars_lookup.tcp_srcid)
JOIN object_test_db.obj_srcid_lookup ON (object_test_db.obj_srcid_lookup.src_id=feat_values.src_id)
JOIN source_test_db.one_src_model_class_probs ON (class_rank=0 AND schema_comment="%s")
WHERE feat_id=%d """ % ("50nois_00epch_010need_0.100mtrc_per900ep10day_linearlombfreq_expnoisefreq", freq_dict['feat_id']) + \
  """ AND class_type like "%rrl%"
group by object_test_db.obj_srcid_lookup.src_id
order by src_id"""
#     AND class_type like "%rrl%"

            tcp_freqs = []
            jsb_freqs = []
            nepochs = []
            self.cursor.execute(select_str)
            rows = self.cursor.fetchall()
            for row in rows:
                srcid = row[2]
                tcp_freqs.append(row[0])
                nepochs.append(row[1])
                jsb_freqs.append(1.0 / row[3])
                if srcid not in all_freq_dict:
                    all_freq_dict[srcid] = {}
                all_freq_dict[srcid][freq_name] = row[0]
                all_freq_dict[srcid]['jsb_freq'] = 1.0 / row[3]
                all_freq_dict[srcid]['nepochs'] = row[1]

            #jsb_freqs = numpy.array(jsb_freqs)
            #nepochs = numpy.array(nepochs)
            #nepochs_normalized = (numpy.array(nepochs) - numpy.min(nepochs)) / (float(numpy.max(nepochs)) - numpy.min(nepochs))

        # we want to have the best freq with minimum freq difference between jsb and tcp
        best_freq_list = []
        best_freq_num_list = []
        jsb_freqs = []
        nepochs = []
        for srcid,src_dict in all_freq_dict.iteritems():
            jsb_freqs.append(src_dict.get('jsb_freq',1000))
            nepochs.append(src_dict['nepochs'])
            best_freq = src_dict.get('freq1',100)
            best_num = 1
            if numpy.abs(src_dict.get('freq2',100) - src_dict.get('jsb_freq',1000)) <  numpy.abs(best_freq - src_dict.get('jsb_freq',1000)):
                best_freq = src_dict.get('freq2',100)
                best_num = 3#2
            if numpy.abs(src_dict.get('freq3',100) - src_dict.get('jsb_freq',1000)) <  numpy.abs(best_freq - src_dict.get('jsb_freq',1000)):
                best_freq = src_dict.get('freq3',100)
                best_num = 5#3
            best_freq_list.append(best_freq)
            best_freq_num_list.append(best_num)

        nepochs = numpy.array(nepochs)
        nepochs_normalized = (numpy.array(nepochs) - numpy.min(nepochs)) / (float(numpy.max(nepochs)) - numpy.min(nepochs))
        best_freq_num_list = numpy.array(best_freq_num_list)
        best_freq_list = numpy.array(best_freq_list)
        jsb_freqs = numpy.array(jsb_freqs)
        # todo: plot best_freq
        # todo: change circle size by freq1, 2, 3 number

        self.fig = pyplot.figure(figsize=(9,11), dpi=300)
        ax = self.fig.add_subplot('111')

        #pyplot.plot(nepochs, tcp_freqs, 'ro')
        #ax.set_xlabel('n_epochs')
        #pyplot.plot(jsb_freqs, tcp_freqs, 'bo')
        scat = pyplot.scatter(jsb_freqs, best_freq_list, c=nepochs_normalized, s=(best_freq_num_list)*100)
        scat.set_alpha(0.75)
        pyplot.plot(numpy.array([1.0,3.5]), numpy.array([1.0,3.5]), 'r')
        ax.set_xlabel('JSB/SDSS freq')
        ax.set_ylabel('TCP freq')
        ax.set_title('JSB user-classified vars: %s' % (class_glob_str))

        fpath = "/tmp/%s_jsbfreq_tcpfreq.ps" % (class_glob_str)
        pyplot.savefig(fpath)


    def make_jsbfreq_best_tcpfreq_plot__old(self):
        """
        """
        import matplotlib
        import matplotlib.pyplot as pyplot
        from matplotlib import rcParams
        import numpy

        freq_feat_id_dict = {'freq1':{'feat_id':1718},
                             'freq2':{'feat_id':1520},
                             'freq3':{'feat_id':89}}
        all_freq_dict = {}
        for freq_name, freq_dict in freq_feat_id_dict.iteritems():
            select_str = """select source_test_db.feat_values.feat_val, count(object_test_db.obj_srcid_lookup.obj_id) AS n_epochs, object_test_db.obj_srcid_lookup.src_id, source_test_db.jsbvars_lookup.jsb_period from source_test_db.jsbvars_lookup
JOIN source_test_db.feat_values ON (feat_values.src_id=source_test_db.jsbvars_lookup.tcp_srcid)
JOIN object_test_db.obj_srcid_lookup ON (object_test_db.obj_srcid_lookup.src_id=feat_values.src_id)
WHERE feat_id=%d """ % (freq_dict['feat_id']) + """ AND class_type like "%rrl%"
group by object_test_db.obj_srcid_lookup.src_id
order by src_id"""

            tcp_freqs = []
            jsb_freqs = []
            nepochs = []
            self.cursor.execute(select_str)
            rows = self.cursor.fetchall()
            for row in rows:
                srcid = row[2]
                tcp_freqs.append(row[0])
                nepochs.append(row[1])
                jsb_freqs.append(1.0 / row[3])
                if srcid not in all_freq_dict:
                    all_freq_dict[srcid] = {}
                all_freq_dict[srcid][freq_name] = row[0]
                all_freq_dict[srcid]['jsb_freq'] = 1.0 / row[3]
                all_freq_dict[srcid]['nepochs'] = row[1]

            #jsb_freqs = numpy.array(jsb_freqs)
            #nepochs = numpy.array(nepochs)
            #nepochs_normalized = (numpy.array(nepochs) - numpy.min(nepochs)) / (float(numpy.max(nepochs)) - numpy.min(nepochs))

        # we want to have the best freq with minimum freq difference between jsb and tcp
        best_freq_list = []
        best_freq_num_list = []
        jsb_freqs = []
        nepochs = []
        for srcid,src_dict in all_freq_dict.iteritems():
            jsb_freqs.append(src_dict.get('jsb_freq',1000))
            nepochs.append(src_dict['nepochs'])
            best_freq = src_dict.get('freq1',100)
            best_num = 1
            if numpy.abs(src_dict.get('freq2',100) - src_dict.get('jsb_freq',1000)) <  numpy.abs(best_freq - src_dict.get('jsb_freq',1000)):
                best_freq = src_dict.get('freq2',100)
                best_num = 2
            if numpy.abs(src_dict.get('freq3',100) - src_dict.get('jsb_freq',1000)) <  numpy.abs(best_freq - src_dict.get('jsb_freq',1000)):
                best_freq = src_dict.get('freq3',100)
                best_num = 3
            best_freq_list.append(best_freq)
            best_freq_num_list.append(best_num)

        nepochs = numpy.array(nepochs)
        nepochs_normalized = (numpy.array(nepochs) - numpy.min(nepochs)) / (float(numpy.max(nepochs)) - numpy.min(nepochs))
        best_freq_num_list = numpy.array(best_freq_num_list)
        best_freq_list = numpy.array(best_freq_list)
        jsb_freqs = numpy.array(jsb_freqs)
        # todo: plot best_freq
        # todo: change circle size by freq1, 2, 3 number

        self.fig = pyplot.figure(figsize=(9,11), dpi=300)
        ax = self.fig.add_subplot('111')

        #pyplot.plot(nepochs, tcp_freqs, 'ro')
        #ax.set_xlabel('n_epochs')
        #pyplot.plot(jsb_freqs, tcp_freqs, 'bo')
        scat = pyplot.scatter(jsb_freqs, best_freq_list, c=nepochs_normalized, s=(best_freq_num_list)*200)
        scat.set_alpha(0.75)
        pyplot.plot(numpy.array([1.0,3.5]), numpy.array([1.0,3.5]), 'r')
        ax.set_xlabel('JSB/SDSS freq')
        ax.set_ylabel('TCP freq')
        ax.set_title('JSB user-classified vars: RRLyrae*')

        fpath = "/tmp/rrlyrae_jsbfreq_tcpfreq.ps"
        pyplot.savefig(fpath)



if __name__ == '__main__':
    pars = { \
        'spatial_query_box_length':0.001111111, # 4 arcsec, in degrees.
        'variables_csv_fpath':'/home/pteluser/src/TCP/Data/data_for_structure_function.csv',
        'ceph_eb_csv_fpath':'/home/pteluser/src/TCP/Data/ceph_and_eb_for_dan.csv',
        'rrlyra_data_dirpath':'/home/pteluser/src/TCP/Data/RRLData',
        'intermed_xmls_dirpath':'/home/pteluser/scratch/Noisification/jsb_classified_xmls',
        'result_arff_fpath':'/home/pteluser/src/TCP/Data/jsb_classified_vars.arff',
        'srcid_lookup_htm_tablename':'source_test_db.srcid_lookup_htm',
        'obj_srcid_lookup_tablename':'object_test_db.obj_srcid_lookup',
        'data_tablename':'source_test_db.jsbvars_data',
        'lookup_tablename':'source_test_db.jsbvars_lookup',
        'mysql_user':"pteluser", 
        'mysql_hostname':"192.168.1.25", 
        'mysql_database':'object_test_db', 
        'mysql_port':3306, 
        'do_lbl_check':True,
        'tcp_to_jsbvar_classname':{'Classical Cepheid':['Cepheid'],
                                   'RR Lyrae, Fundamental Mode':['rrlyrae_ab','rrlyrae_c'],
                                   'Binary':['EB*','EB*WUMa']},
        }

    DataParse = Data_Parse(pars=pars)
    DataParse.establish_db_connection(host=pars['mysql_hostname'], \
                                      user=pars['mysql_user'], \
                                      db=pars['mysql_database'], \
                                      port=pars['mysql_port'])

    ### Generate freq(tcp) vs nepoch plot:
    #DataParse.make_freq_nepoch_plot()
    #DataParse.make_jsbfreq_tcpfreq_plot()
    DataParse.make_jsbfreq_best_tcpfreq_plot()
    sys.exit()

    ### DO ONCE ONLY:
    #DataParse.create_tables()
    #DataParse.parse_insert_dict_into_table()

    if 0:
        ##### This generates JSB_var_sources .xmls and .arff file:

        ### TODO: this could be done in IPYTHON-PARALLEL if we had > 96 sources:
        DataParse.retrieve_jsbclass_sources_from_rdb_write_xmls()


        #if os.path.exists(pars['result_arff_fpath']):
        #    os.system("rm " + pars['result_arff_fpath'])

        from . import generate_weka_classifiers
        ParallelArffMaker = generate_weka_classifiers.Parallel_Arff_Maker(pars={})
        ParallelArffMaker.generate_arff_using_xmls( \
                     vosource_xml_dirpath=pars['intermed_xmls_dirpath'], \
                     out_arff_fpath = pars['result_arff_fpath'], \
                     n_sources_needed_for_class_inclusion=1)

    if 1:
        # Once the jsbvars_* TABLES are populated, we can do this:
        #    - which updates the classifications in TABLE:
        #          source_teste_db.one_src_model_class_probs
        #
        # NOTE: uses a lot of memory for ipython1 asks, so
        #       set n_nodes <= 4
        DataParse.generate_classifications(schema_str="50nois_00epch_010need_0.100mtrc_per900ep10day_linearlombfreq_expnoisefreq")
        
