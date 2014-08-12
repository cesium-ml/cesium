#!/usr/bin/env python
"""

TODO: for each source (which is public and has a lightcurve), parse the ra,dec
TODO: then with the ra,dec query simbad/NED to see if any classifications / knowledge.

"""
import sys, os
import socket
socket.setdefaulttimeout(20) # for urllib2 timeout of urlopen()
import urllib
import urllib2
import cPickle
import gzip
import amara

class Kepler_Database:
    """ Object which accesses mysql database / table containing kic.txt (13M row) data.
    """

    def __init__(self, pars):
        import MySQLdb
        self.pars = pars
        self.db = MySQLdb.connect(host=pars['tcp_hostname'], \
                                  user=pars['tcp_username'], \
                                  db=pars['tcp_database'],\
                                  port=pars['tcp_port'])
        self.cursor = self.db.cursor()


    def create_load_table(self):
        """ Load data from text file into new MySQL table.

        NOTE: Run this function one time only.
        
        ###Header from kic.txt text file:
        kic_ra|kic_dec|kic_pmra|kic_pmdec|kic_umag|kic_gmag|kic_rmag|kic_imag|kic_zmag|kic_gredmag|kic_d51mag|kic_jmag|kic_hmag|kic_kmag|kic_kepmag|kic_kepler_id|kic_tmid|kic_scpid|kic_altid|kic_altsource|kic_galaxy|kic_blend|kic_variable|kic_teff|kic_logg|kic_feh|kic_ebminusv|kic_av|kic_radius|kic_cq|kic_pq|kic_aq|kic_catkey|kic_scpkey|kic_parallax|kic_glon|kic_glat|kic_pmtotal|kic_grcolor|kic_jkcolor|kic_gkcolor|kic_degree_ra|kic_fov_flag|kic_tm_designation
        """
        
        """ CREATE TABLE kepler_kic (
kic_ra DOUBLE,
kic_dec DOUBLE,
kic_pmra FLOAT,
kic_pmdec FLOAT,
kic_umag FLOAT,
kic_gmag FLOAT,
kic_rmag FLOAT,
kic_imag FLOAT,
kic_zmag FLOAT,
kic_gredmag FLOAT,
kic_d51mag FLOAT,
kic_jmag FLOAT,
kic_hmag FLOAT,
kic_kmag FLOAT,
kic_kepmag FLOAT,
kic_kepler_id INT UNSIGNED,
kic_tmid INT UNSIGNED,
kic_scpid INT UNSIGNED,
kic_altid INT UNSIGNED,
kic_altsource INT UNSIGNED,
kic_galaxy INT UNSIGNED,
kic_blend INT UNSIGNED,
kic_variable INT UNSIGNED,
kic_teff INT UNSIGNED,
kic_logg FLOAT,
kic_feh FLOAT,
kic_ebminusv FLOAT,
kic_av FLOAT,
kic_radius FLOAT,
kic_cq VARCHAR(8),
kic_pq FLOAT,
kic_aq FLOAT,
kic_catkey FLOAT,
kic_scpkey FLOAT,
kic_parallax FLOAT,
kic_glon FLOAT,
kic_glat FLOAT,
kic_pmtotal FLOAT,
kic_grcolor FLOAT,
kic_jkcolor FLOAT,
kic_gkcolor FLOAT,
kic_degree_ra FLOAT,
kic_fov_flag INT UNSIGNED,
kic_tm_designation VARCHAR(16),
PRIMARY KEY (obj_id)
"""

        create_table_str = """CREATE TABLE kepler_kic (
ra DOUBLE,
decl DOUBLE,
pmra FLOAT,
pmdec FLOAT,
umag FLOAT,
gmag FLOAT,
rmag FLOAT,
imag FLOAT,
zmag FLOAT,
gredmag FLOAT,
d51mag FLOAT,
jmag FLOAT,
hmag FLOAT,
kmag FLOAT,
kepmag FLOAT,
kepler_id INT UNSIGNED,
tmid INT UNSIGNED,
scpid INT UNSIGNED,
altid INT UNSIGNED,
altsource INT UNSIGNED,
galaxy INT UNSIGNED,
blend INT UNSIGNED,
variable INT UNSIGNED,
teff INT UNSIGNED,
logg FLOAT,
feh FLOAT,
ebminusv FLOAT,
av FLOAT,
radius FLOAT,
cq VARCHAR(8),
pq FLOAT,
aq FLOAT,
catkey FLOAT,
scpkey FLOAT,
parallax FLOAT,
glon DOUBLE,
glat DOUBLE,
pmtotal FLOAT,
grcolor FLOAT,
jkcolor FLOAT,
gkcolor FLOAT,
degree_ra DOUBLE,
fov_flag INT UNSIGNED,
tm_designation VARCHAR(16),
PRIMARY KEY (kepler_id))
"""
        self.cursor.execute(create_table_str)

        load_data_str = """
LOAD DATA INFILE '%s' INTO TABLE kepler_kic
  FIELDS TERMINATED BY '|'
  IGNORE 1 LINES
        """ % (self.pars['kictxt_filepath'])

        self.cursor.execute(load_data_str)

        alter_table = "ALTER TABLE kepler_kic ADD COLUMN simbad_class VARCHAR(16)"
        self.cursor.execute(alter_table)


        print "DONE."
        import pdb; pdb.set_trace()
        print

class Kepler_Sources:
    """
    """
    def __init__(self, pars):
        self.pars = pars
        self.kep_db = Kepler_Database(pars)

    def get_kepids(self):
        """ Retrieve a dict of kepler_ids from the public-lightcurve web dirs.
        """

        if os.path.exists(self.pars['kepid_pkl_fpath']):
            fp=gzip.open(self.pars['kepid_pkl_fpath'],'rb')
            kepid_dict=cPickle.load(fp)
            fp.close()
        else:
            out = urllib.urlopen(self.pars['pubfits_base_url']).read()
            kepid_4char_list = []
            for line in out.split('\n'):
                if "folder.gif" in line:
                    i_end = line.rfind('</a>') - 1
                    i_begin = line.rfind('>', 0, i_end) + 1
                    substr = line[i_begin:i_end]
                    if substr == 'tarfiles':
                        pass
                    else:
                        print substr
                        kepid_4char_list.append(substr)

            kepid_dict = {}
            ### Now, form a new URLs and look for all sources within these
            for kepid_4char in kepid_4char_list:
                url_str = "%s%s/" % (self.pars['pubfits_base_url'], kepid_4char)
                out = urllib.urlopen(url_str).read()
                for line in out.split('\n'):
                    if "folder.gif" in line:
                        i_end = line.rfind('</a>') - 1
                        i_begin = line.rfind('>', 0, i_end) + 1
                        substr = line[i_begin:i_end]
                        #if substr == 'tarfiles':
                        #    pass
                        #else:
                        #print substr
                        kepid = int(substr)
                        kepid_dict[kepid] = None # TODO: I want to parse and store fits URLs
                        

            fp = gzip.open(self.pars['kepid_pkl_fpath'],'wb')
            cPickle.dump(kepid_dict,fp,1) # ,1) means a binary pkl is used.
            fp.close()
        return kepid_dict


    def get_radecs(self, kepid_dict={}):
        """ Use the 3 column derived from the kic.txt.gz file.
        Then determine whether we have ra,dec for each of the kepler_id sources.

        This file is made using:

        cut -d "|" -f 1,2,16 kic.txt > kic.tct__radecid
        
        """
        ra_dict = {}
        dec_dict = {}
        n_kepids = len(kepid_dict.keys())
        for i, kepid in enumerate(kepid_dict.keys()):
            command_str = "grep \|%d$ %s" % (kepid, self.pars['kic.txt_3col_fpath'])
            (a,b,c) = os.popen3(command_str)
            a.close()
            c.close()
            lines = b.read().split('\n')
            b.close()
            #import pdb; pdb.set_trace()
            for line in lines[:-1]:
                elems = line.split('|')
                if int(elems[2]) == kepid:
                    print i, n_kepids, len(lines)
                    ra_dict[kepid] = float(elems[0])
                    dec_dict[kepid] = float(elems[1])

        return {'ra_dict':ra_dict,
                'dec_dict':dec_dict}
            # todo want kepid to be a dict

        

    def get_radecs_pklwrapper(self, kepid_dict={}):
        """
        """
        if ((not os.path.exists(self.pars['ra_dict_pkl_fpath'])) or
            (not os.path.exists(self.pars['ra_dict_pkl_fpath']))):
            radec_dict = self.get_radecs(kepid_dict=kepid_dict)

            fp = gzip.open(self.pars['ra_dict_pkl_fpath'],'wb')
            cPickle.dump(radec_dict['ra_dict'],fp,1) # ,1) means a binary pkl is used.
            fp.close()

            fp = gzip.open(self.pars['dec_dict_pkl_fpath'],'wb')
            cPickle.dump(radec_dict['dec_dict'],fp,1) # ,1) means a binary pkl is used.
            fp.close()
        else:
            radec_dict = {}
            fp=gzip.open(self.pars['ra_dict_pkl_fpath'],'rb')
            radec_dict['ra_dict']=cPickle.load(fp)
            fp.close()
            
            fp=gzip.open(self.pars['dec_dict_pkl_fpath'],'rb')
            radec_dict['dec_dict']=cPickle.load(fp)
            fp.close()

        return radec_dict
    

    def query_votable_name(self, name=''):
        """ Adapted from simbad_id_lookup.py and simbad.py
        """
        #alt_html_pre = "http://simbad.u-strasbg.fr/simbad/sim-coo?"


        #html = "http://simbad.harvard.edu/simbad/sim-coo?"
        #params = urllib.urlencode({'output.format': "VOTABLE", "Coord": "%fd%f" % (ra, dec),\
        #                               'Radius': rad, 'Radius.unit': "arcsec"})
        
        html = "http://simbad.harvard.edu/simbad/sim-id?"
        params = urllib.urlencode({'output.format':"VOTABLE","Ident":name,"NbIdent":1,\
                                   'Radius': 2, 'Radius.unit': "arcsec", 'submit':'submit id'})
        f = urllib2.urlopen("%s%s" % (html,params))
        s = f.read()
        f.close()
        #print s
        ### so this works if there is a matching obect (full xml is returned
        #import pdb; pdb.set_trace()

        return s

    def query_votable_radec(self, ra=0.0, dec=0.0, rad=2.0):
        """ Adapted from simbad_id_lookup.py and simbad.py
        """
        #alt_html_pre = "http://simbad.u-strasbg.fr/simbad/sim-coo?"


        html = "http://simbad.harvard.edu/simbad/sim-coo?"
        params = urllib.urlencode({'output.format': "VOTABLE", "Coord": "%fd%f" % (ra, dec),\
                                       'Radius': rad, 'Radius.unit': "arcsec"})
        
        #html = "http://simbad.harvard.edu/simbad/sim-id?"
        #params = urllib.urlencode({'output.format':"VOTABLE","Ident":"HD 27290","NbIdent":1,\
        #                           'Radius': 2, 'Radius.unit': "arcsec", 'submit':'submit id'})
        f = urllib.urlopen("%s%s" % (html,params))
        s = f.read()
        f.close()
        #print s
        ### so this works if there is a matching obect (full xml is returned
        #import pdb; pdb.set_trace()
        return s


    def parse_class(self, votable_str):
        """ Adapted from simbad_id_lookup.py
        """
        a = amara.parse(votable_str)
        #b = a.xml_select("/VOTABLE/RESOURCE/TABLE/FIELD")
        #b = a.xml_xpath("/VOTABLE/RESOURCE/TABLE/FIELD[@name='OTYPE']")
        b = a.xml_xpath("/VOTABLE/RESOURCE/TABLE/FIELD")
        i_col_otype = -1
        for i, elem in enumerate(b):
            if elem['name'] == 'OTYPE':
                i_col_otype = i
                break
        b = a.xml_xpath("/VOTABLE/RESOURCE/TABLE/DATA/TABLEDATA/TR/TD")
        #print len(b[i_col_otype])
        #print str(b[i_col_otype])
        #import pdb; pdb.set_trace()
        return str(b[i_col_otype])


    def get_simbad_info_for_kepids_in_table(self):
        """ Query the simbad webserver for information for each kepler id,
        assuming that we also have ra,dec info for these kepler-ids in radec_dict{}.

        NOTE: radec_dict['*_dict'] is a slightly smaller subset of kepid_dict.keys()

        """
        class_dict = {}
        fp_txt = open(self.pars['kep_simbad_class_txt_fpath'], 'w')
        n_id_increment = 100
        #i_low = 582826   # This returns a xml witha a classification
        i_low = 655619
        i_high = 0 # initial junk value
        while i_high < 13161030:
            i_high = i_low + n_id_increment
            select_str = "SELECT kepler_id, degree_ra, decl, gmag, rmag, tm_designation  FROM kepler_kic WHERE kepler_id > %d AND kepler_id <= %d" % (i_low, i_high)

            #in= [\
            #"INSERT INTO %s (ra, decl, ra_rms, dec_rms, nobjs) VALUES "%\
            #                            (self.pars['srcid_table_name'])]

            self.kep_db.cursor.execute(select_str)
            results = self.kep_db.cursor.fetchall()
            for row in results:
                (kepid, ra_deg, dec_deg, gmag, rmag, tm_designation) = row
                import pdb; pdb.set_trace()
                print
                xml_fpath = "%s/%d.xml" % (self.pars['simbad_votable_cache_dirpath'], kepid)
                ### This condition can be done if we think we will be querying previously retrieved sources:
                ###    - we have saved xmls for kepids >= 154612 (and not explicitly public_timeseries 150k)
                #if os.path.exists(xml_fpath):
                #    continue
                name_str = "2MASS J%s" % (tm_designation)
                votable_str = self.query_votable_name(name=name_str)
                if len(votable_str) < 310:
                    print "NO SIMBAD: %d len:%d RA,D: %lf %lf %s " % (kepid, len(votable_str), ra_deg, dec_deg, name_str)
                    continue

                #print "Y! SIMBAD info: %d RA, Dec: %lf %lf %s" % (kepid, ra_deg, dec_deg, name_str)
                try:
                    class_str = self.parse_class(votable_str)
                    fp_votable = open(xml_fpath, 'w')
                    fp_votable.write(votable_str)
                    fp_votable.close()
                except:
                    continue
                
                out_str = "%d '%s'" % (kepid, class_str)
                print out_str
                fp_txt.write(out_str + '\n')

                class_dict[kepid] = class_str

            #import pdb; pdb.set_trace()
            #print

            #import pdb; pdb.set_trace()
            #print
            fp_txt.flush()    
            i_low = i_high

            
        fp_txt.close()
        fp = gzip.open(self.pars['kep_simbad_class_pkl_fpath'],'wb')
        cPickle.dump(class_dict,fp,1) # ,1) means a binary pkl is used.
        fp.close()


    def get_simbad_info_for_kepid_list(self, id_list = []):
        """ Query the simbad webserver for information for each kepler id,
        assuming that we also have ra,dec info for these kepler-ids in radec_dict{}.

        NOTE: radec_dict['*_dict'] is a slightly smaller subset of kepid_dict.keys()

        """
        class_dict = {}
        fp_txt = open(self.pars['kep_simbad_class_txt_fpath'], 'w')
        for i, kepid in enumerate(id_list):
            select_str = "SELECT kepler_id, degree_ra, decl, gmag, rmag, tm_designation  FROM kepler_kic WHERE kepler_id = %d" % (kepid)

            self.kep_db.cursor.execute(select_str)
            results = self.kep_db.cursor.fetchall()
            if len(results) == 0:
                continue
            (kepid, ra_deg, dec_deg, gmag, rmag, tm_designation) = results[0]
            name_str = "2MASS J%s" % (tm_designation)
            votable_str = self.query_votable_name(name=name_str)
            if len(votable_str) < 300:
                #print "NO SIMBAD info: %d RA, Dec: %lf %lf %s" % (kepid, ra_deg, dec_deg, name_str)
                continue

            #print "Y! SIMBAD info: %d RA, Dec: %lf %lf %s" % (kepid, ra_deg, dec_deg, name_str)
            try:
                class_str = self.parse_class(votable_str)
            except:
                continue
            
            out_str = "%d '%s'" % (kepid, class_str)
            print out_str
            fp_txt.write(out_str + '\n')

            class_dict[kepid] = class_str

            #import pdb; pdb.set_trace()
            #print
            if (i % 100 == 0):
                fp_txt.flush()

            
        fp_txt.close()
        fp = gzip.open(self.pars['kep_simbad_class_pkl_fpath'],'wb')
        cPickle.dump(class_dict,fp,1) # ,1) means a binary pkl is used.
        fp.close()


    # # # IN PROGRESS: # # #
    def update_table_with_simbad_classes(self):
        """ query database to see what highest kepler_id which has a simbad class
         - parse text file
         - update database with all sources which are not in the database
        """

        select_str = "SELECT max(kepler_id) FROM kepler_kic where simbad_class NOT NULL"
        self.kep_db.cursor.execute(select_str)
        results = self.kep_db.cursor.fetchall()
        results[0][0]
        fp = open(self.pars['kep_simbad_class_txt_fpath'])
        
        for row in results:
            print row


        

    def main(self):
        """
        """
        ### TEST/debug: 
        #import pdb; pdb.set_trace()
        #print
        #votable_str = self.query_votable_radec(ra=64.0066071, dec=-51.4866481, rad=20.0)
        #a_class = self.parse_class(votable_str)

        kepid_dict = self.get_kepids()
        
        ###OBSOLETE / BROKEN:
        #radec_dict = self.get_radecs_pklwrapper(kepid_dict=kepid_dict)

        ### This populates txt and pkl file with simbad classes for each source_id
        self.get_simbad_info_for_kepids_in_table() # retrieve for all 13M kepler sources
        #self.get_simbad_info_for_kepid_list(id_list=kepid_dict.keys()) # for retrieving 150k pubTS sources and get 5898 sources with simbad classifs

        ### IN PROGRESS:
        #self.update_table_with_simbad_classes()

        # TODO: query simbad code with given ra, dec

        import pdb; pdb.set_trace()
        print

if __name__ == '__main__':

    ### NOTE: most of the RDB parameters were dupliclated from ingest_toolspy::pars{}
    pars = { \

            'tcp_hostname':'192.168.1.25',
            'tcp_username':'pteluser',
            'tcp_port':     3306, 
            'tcp_database':'source_test_db',

            'pubfits_base_url':'http://archive.stsci.edu/pub/kepler/lightcurves/',
            'kepid_pkl_fpath':'/home/pteluser/scratch/kepler/kepid.pkl.gz',
            'kic.txt_3col_fpath':'/home/pteluser/scratch/kepler/kic.txt__radecid',
            'ra_dict_pkl_fpath':'/home/pteluser/scratch/kepler/kep_ra.pkl.gz',
            'dec_dict_pkl_fpath':'/home/pteluser/scratch/kepler/kep_dec.pkl.gz',
            'kictxt_filepath':'/home/pteluser/scratch/kepler/kic.txt', # 2.5GB metadata file
            'kep_simbad_class_txt_fpath':'/home/pteluser/scratch/kepler/kepid_simbad_classes.txt',
            'kep_simbad_class_pkl_fpath':'/home/pteluser/scratch/kepler/kepid_simbad_classes.pkl.gz',
            'simbad_votable_cache_dirpath':'/media/raid_0/kepler_simbad_votables',
        }

    KeplerSources = Kepler_Sources(pars)
    KeplerSources.main()





    ### do once only to load Kepler source meta data into Tables:
    #kep_db = Kepler_Database(pars)
    #kep_db.create_load_table() 
    #sys.exit()
