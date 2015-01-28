#!/usr/bin/env python
""" Dump simple data files of timeseries data as well as source summary file
    for Damian Eads to parse.
    - should include Debosscher proj_id=123, ASAS proj_1d=126.

 - srcid filename: t m merr
 - lookup file describes:
 - proj_id src_id survey_name orig_class algo_class_1 algo_prob_1 . . .
"""

import sys, os

sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                      'Software/feature_extract'))
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
              'Software/feature_extract/Code'))
from Code import *
import db_importer


class Database_Utils:
    """ Establish database connections, contains methods related to database tables.
    """
    def __init__(self, pars={}):
        self.pars = pars
        self.connect_to_tcp_db()
        self.connect_to_tutor_db()


    def connect_to_tcp_db(self):
        import MySQLdb
        self.tcp_db = MySQLdb.connect(host=pars['tcp_hostname'], 
                                      user=pars['tcp_username'], 
                                      db=pars['tcp_database'],
                                      port=pars['tcp_port'])
        self.tcp_cursor = self.tcp_db.cursor()

    def connect_to_tutor_db(self):
        import MySQLdb
        self.tutor_db = MySQLdb.connect(host=pars['tutor_hostname'], 
                                        user=pars['tutor_username'], 
                                        db=pars['tutor_database'],
                                        port=pars['tutor_port'],
                                        passwd=pars['tutor_password'])
        self.tutor_cursor = self.tutor_db.cursor()


class Write_TS_For_Damian(Database_Utils):
    """ Write timeseries files for Damian.
TODO:
 - find xmls
 - parse xmls
   - write .dat for each source xml
 - tar.gz .dats
 - retrieve classes, survey_name
 - write summary file
    """
    def __init__(self, pars={}):
        self.pars = pars
        self.connect_to_tcp_db()
        self.connect_to_tutor_db()


    def parse_xmls_write_dats(self, do_write=True):
        """ Parse ts data from vosource xmls, write into .dat files
        """
        import glob
        srcid_list = []
        for proj_id, dirpath in self.pars['xml_dirs'].iteritems():
            xml_fpaths = glob.glob("%s/*xml" % (dirpath))
            for xml_fpath in xml_fpaths:
                src_id = int(xml_fpath[xml_fpath.rfind('/')+1:xml_fpath.rfind('.')]) - 100000000
                srcid_list.append((proj_id, src_id))

                if do_write:
                    ### parse the timeseries
                    signals_list = []
                    gen = generators_importers.from_xml(signals_list)
                    ###  This is taken from from_xml.py::generate():
                    gen.signalgen = {}
                    gen.sig = db_importer.Source(xml_handle=xml_fpath,doplot=False, make_xml_if_given_dict=False)
                    ### Here we assume only one filter (true for proj_id=[123,126]):
                    t = gen.sig.x_sdict['ts'].values()[0]['t']
                    m = gen.sig.x_sdict['ts'].values()[0]['m']
                    m_err = gen.sig.x_sdict['ts'].values()[0]['m_err']


                    dat_fpath = "%s/%d.dat" % (self.pars['dat_dirpath'], src_id)

                    fp = open(dat_fpath, 'w')
                    for i in xrange(len(t)):
                        fp.write("%lf %lf %lf\n" % (t[i], m[i], m_err[i]))

                    fp.close()
        return srcid_list


    def make_summary_file(self, srcid_list=[], srcid_classname={}):
        """
        - proj_id src_id survey_name orig_class algo_class_1 algo_prob_1 ...

        """
        fp = open(self.pars['source_summary_fpath'], 'w')

        for proj_id, src_id in srcid_list:
            select_str = "select source_name, class_short_name from sources left outer join classes USING (class_id) where source_id=%d" % (src_id)
            self.tutor_cursor.execute(select_str)
            results = self.tutor_cursor.fetchall()
            (source_name, tutor_class_name) = results[0]

            #if proj_id == 123:
            #    continue

            if proj_id == 126:
                survey_name = 'ASAS'
                ### I would rather only pass ASAS classes which user-consensus was made, rather than ASAS's original classifications which are 20% wrong anyeays

                tutor_class_name = srcid_classname.get(src_id, 'None')
            elif proj_id == 123:
                if (('HIP' in source_name) or 'HD' in source_name):
                    survey_name = 'HIPP'
                elif 'OGLE' in source_name:
                    survey_name = 'OGLE'
                else:
                    raise
                
            select_str = "select class_short_name, rank, prob from activelearn_algo_class left outer join activelearn_tutorclasses_copy ON (activelearn_algo_class.tutor_class_id=activelearn_tutorclasses_copy.class_id) where act_id=%d and source_id=%d order by rank" % (self.pars['actlearn_actid'], src_id)
            self.tcp_cursor.execute(select_str)
            results = self.tcp_cursor.fetchall()
            algo_class_list = []
            for row in results:
                (class_short_name, rank, prob) = row
                algo_class_list.extend([class_short_name, str(prob)])

            if len(algo_class_list) == 0:
                algo_class_str = "None 0.0 None 0.0 None 0.0"
            else:
                algo_class_str = ' '.join(algo_class_list)

            write_str = "%d %d %s %s %s\n" % ( \
                            src_id, proj_id, survey_name, tutor_class_name,
                            algo_class_str)
            print write_str,
            #import pdb; pdb.set_trace()
            #print
            fp.write(write_str)
        fp.close()


    def get_classid_shortname_lookup(self):
        """ form a TUTOR class_id :: class_short_name lookup dictionary
        """
        classid_shortname = {}

        select_str = "select class_id, class_short_name from activelearn_tutorclasses_copy"
        self.tcp_cursor.execute(select_str)
        results = self.tcp_cursor.fetchall()
        for row in results:
            (class_id, class_short_name) = row
            classid_shortname[class_id] = class_short_name

        return classid_shortname


    def parse_actlearn_classifs(self):
        """ Parse ActiveLearning user-consensus classifications
        similar to activelearn_utils.py::pars{}
                or get_colors_for_tutor_sources.py::add_AL_addToTrain_classids()
        """

        classid_shortname = self.get_classid_shortname_lookup()

        user_classifs_fpaths = { \
            1:os.path.expandvars('$TCP_DIR/Data/allstars/AL_addToTrain_1.dat'),
            2:os.path.expandvars('$TCP_DIR/Data/allstars/AL_addToTrain_2.dat'),
            3:os.path.expandvars('$TCP_DIR/Data/allstars/AL_addToTrain_3.dat'),
            4:os.path.expandvars('$TCP_DIR/Data/allstars/AL_addToTrain_4.dat'),
            5:os.path.expandvars('$TCP_DIR/Data/allstars/AL_addToTrain_5.dat'),
            6:os.path.expandvars('$TCP_DIR/Data/allstars/AL_addToTrain_6.dat'),
            7:os.path.expandvars('$TCP_DIR/Data/allstars/AL_addToTrain_7.dat'),
            8:os.path.expandvars('$TCP_DIR/Data/allstars/AL_addToTrain_8.dat'),
            9:os.path.expandvars('$TCP_DIR/Data/allstars/AL_addToTrain_9.dat'),
            #10:os.path.expandvars('$TCP_DIR/Data/allstars/AL_SIMBAD_confirmed.dat'), # SIMBAD confirmed sources
        }

        from numpy import loadtxt
        all_srcid_classid = {}
        for n, fpath in user_classifs_fpaths.iteritems():
            data = loadtxt(fpath, dtype={'names': ('src_id', 'class_id'),
                                         'formats': ('i4', 'i4')})
            for i, src_id in enumerate(data['src_id']):
                all_srcid_classid[src_id] = classid_shortname[data['class_id'][i]]
        return all_srcid_classid


    def main(self):
        """
        TODO:
        # - find xmls
        # - parse xmls
        #   - write .dat for each source xml
         - retrieve classes, survey_name
         - write summary file
         - tar.gz .dats
        """
        srcid_list = self.parse_xmls_write_dats(do_write=False)
        ### tar -czf damian_ts_dats.tar.gz damian_ts_dats/
        srcid_classname = self.parse_actlearn_classifs()
        self.make_summary_file(srcid_list=srcid_list, srcid_classname=srcid_classname)
        
        import pdb; pdb.set_trace()
        print


if __name__ == '__main__':

    pars = { \
    'tutor_hostname':'192.168.1.103',
    'tutor_username':'dstarr',
    'tutor_password':'ilove2mass',
    'tutor_database':'tutor',
    'tutor_port':3306,
    'tcp_hostname':'192.168.1.25',
    'tcp_username':'pteluser',
    'tcp_port':     3306, 
    'tcp_database':'source_test_db',
    'xml_dirs':{123:'/media/raid_0/debosscher_xmls/xmls',
                126:'/media/raid_0/historical_archive_featurexmls_arffs/tutor_126/2011-02-06_00:03:02.699641/xmls'},
    'dat_dirpath':'/media/raid_0/damian_ts_dats',
    'source_summary_fpath':'/media/raid_0/damian_source_summary.dat',
    'actlearn_actid':12, # determines which algorithmic classifications are retrieved fomr activelearn_algo_class TABLE
    }


    WTS = Write_TS_For_Damian(pars=pars)
    WTS.main()
