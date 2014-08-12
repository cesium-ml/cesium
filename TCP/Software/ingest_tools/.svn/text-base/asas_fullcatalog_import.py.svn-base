#!/usr/bin/env python
""" Tools for importing the full 15M ASAS source catalog

CREATE TABLE asas_fullcatalog
(name VARCHAR(13),
nobs SMALLINT,
PRIMARY KEY (name), INDEX(nobs))

alter table asas_fullcatalog add column retrieved BOOLEAN DEFAULT FALSE;
#alter table asas_fullcatalog add index (retrieved, nobs)  # this would require CPU on update of retrieved
#alter table asas_fullcatalog add index (nobs, retrieved)  # this would require CPU on update of retrieved

"""
import sys, os
import numpy
import urllib
import time
try:
    import MySQLdb
except:
    pass # only get here on the citris33 cluster

def url_query(catalog_url_str, pars):
    db = Database_Utils(pars)
    db.connect_to_db()
    
    try:
        insert_list = ["INSERT INTO asas_fullcatalog (name, nobs) VALUES "]
        f_url = urllib.urlopen(catalog_url_str)
        catalog_result_str = f_url.read()
        f_url.close()
        i_pre = catalog_result_str.find("Nobs") + len("Nobs") + 1
        i_post = catalog_result_str.rfind("</pre>")
        lines = catalog_result_str[i_pre:i_post].split('\n')
        for line in lines:
            if len(line) < 10:
                continue
            i_i = line.find('TARGET="data_plot">') + len('TARGET="data_plot">')
            i_f = line.find('</a>')
            src_name = line[i_i:i_f]
            tups = line[i_f:].split()
            nobs = int(tups[3])
            #srcname_nobs_dict[src_name] = nobs
            #srcname_nobs_tups.append((src_name, nobs))
            if nobs >= 5:
                insert_list.append('("%s", %d), ' % (src_name, nobs))
            
        insert_str = ''.join(insert_list)[:-2] + " ON DUPLICATE KEY UPDATE nobs=VALUES(nobs)"
        db.tcp_cursor.execute(insert_str)
    except:
        db.tcp_cursor.close()
        db.tutor_cursor.close()
    


class Database_Utils:
    """ Establish database connections, contains methods related to database tables.
    """
    def __init__(self, pars={}):
        self.pars = pars
        self.connect_to_db()


    def connect_to_db(self):
        try:
            import MySQLdb
        except:
            return # only get here on the citris33 cluster
        self.tcp_db = MySQLdb.connect(host=self.pars['tcp_hostname'], \
                                  user=self.pars['tcp_username'], \
                                  db=self.pars['tcp_database'],\
                                  port=self.pars['tcp_port'])
        self.tcp_cursor = self.tcp_db.cursor()

        self.tutor_db = MySQLdb.connect(host=self.pars['tutor_hostname'], \
                                  user=self.pars['tutor_username'], \
                                  db=self.pars['tutor_database'], \
                                  passwd=self.pars['tutor_password'], \
                                  port=self.pars['tutor_port'])
        self.tutor_cursor = self.tutor_db.cursor()


    def tcp_execute(self, exec_str):
        """ Catches database-disconnect errors / excepts & re-establishes connection.
        """
        try:
            self.tcp_cursor.execute(exec_str)
        except:
            print "Lost database connection... re-establising after 30s sleep", len(exec_str), exec_str[:100], exec_str[-100:]
            time.sleep(30)
            self.tcp_cursor.close()
            self.tcp_db = MySQLdb.connect(host=self.pars['tcp_hostname'], \
                                      user=self.pars['tcp_username'], \
                                      db=self.pars['tcp_database'],\
                                      port=self.pars['tcp_port'])
            self.tcp_cursor = self.tcp_db.cursor()
            self.tcp_cursor.execute(exec_str)


    def tutor_execute(self, exec_str):
        """ Catches database-disconnect errors / excepts & re-establishes connection.
        """
        try:
            self.tutor_cursor.execute(exec_str)
        except:
            print "Lost database connection... re-establising after 30s sleep", len(exec_str), exec_str[:100], exec_str[-100:]
            time.sleep(30)
            self.tutor_cursor.close()
            self.tutor_db = MySQLdb.connect(host=self.pars['tutor_hostname'], \
                                  user=self.pars['tutor_username'], \
                                  db=self.pars['tutor_database'], \
                                  passwd=self.pars['tutor_password'], \
                                  port=self.pars['tutor_port'])
            self.tutor_cursor = self.tutor_db.cursor()
            self.tutor_cursor.execute(exec_str)

class Asas_Full_Catalog_Import(Database_Utils):
    """ Query tutor.source table for source nearest a grid of points spaced
    the same as the ASAS Sky Atlas spacing.  Then using this closest known ASAS ACVS (50k)
    source's name, query the ASAS Sky Atlas for all sources near this.
      - make sure repeat source_names are not requeried to the Sky Atlas (keep in a list).
      - the resulting sources should be stored in a DB table in batches so that
           these sources can later be retrieved from ASAS.
    """
    def __init__(self, pars={}):
        self.pars = pars
        self.connect_to_db()


    def retrieve_grid_acvs_source_names(self):
        """ Query tutor.source table for source nearest a grid of points spaced
        the same as the ASAS Sky Atlas spacing.
        return a list of these ACVS sources near grid points, which are contained in tutor.sources (proj=126)
        """
        import cPickle, gzip
        if os.path.exists(pars['acvs_src_name_dist_dict_fpath']):
            fp = gzip.open(pars['acvs_src_name_dist_dict_fpath'],'rb')
            acvs_grid_name_dist_dict = cPickle.load(fp)
            fp.close()
            return acvs_grid_name_dist_dict

        acvs_grid_name_dist_dict ={} # should be no longer than 360 * 120 = 43200

        dec_list = []
        dec = self.pars['dec_min']
        while dec <= self.pars['dec_max']:
            dec_list.append(dec)
            dec += self.pars['asas_map_query_min_incr']
        dec_array = numpy.array(dec_list)

        for dec in dec_list:
            ra_list = []
            ra = self.pars['ra_min']
            while ra <= self.pars['ra_max']:
                ra_list.append(ra)
                ra += self.pars['asas_map_query_min_incr'] / numpy.cos(dec * numpy.pi/180.)

            # todo: iterate over ra_list and find nearby asas source in tutor
            for ra in ra_list:
                dec_flt = float(dec)
                if dec_flt < 0:
                    dec_str = "+ %lf" % (-1 * dec_flt)
                else:
                    dec_str = "- %lf" % (dec_flt)
                select_str = "SELECT source_name, abs(source_ra - %lf) + abs(source_dec %s) as dist FROM sources WHERE project_id=126 order by dist limit 1" % (float(ra), dec_str)
                self.tutor_execute(select_str)
                results = self.tutor_cursor.fetchall()
                if len(results) == 0:
                    continue
                source_name, dist = results[0]
                ### NOTE: having the distance information is really only for the order/limit1 but can be used
                #         as a sanity check as well.
                acvs_grid_name_dist_dict[source_name] = float(dist)
                print ra, dec
                # todo now query urllib using the source_name to get all sources
        
        fp = gzip.open(pars['acvs_src_name_dist_dict_fpath'],'wb')
        cPickle.dump(acvs_grid_name_dist_dict,fp,1) # ,1) means a binary pkl is used.
        fp.close()

        return acvs_grid_name_dist_dict


    def retrieve_asas_catalog_sources(self, acvs_src_name_dist_dict):
        """ Using this closest known ASAS ACVS (50k)
    source's name, query the ASAS Sky Atlas for all sources near this.
      - make sure repeat source_names are not requeried to the Sky Atlas (keep in a list).
      - the resulting sources should be stored in a DB table in batches so that
           these sources can later be retrieved from ASAS.
        """

        ### Initially I wanted to be smart about parsing the HTML, but it really is just unformatted:
        """
        from HTMLParser import HTMLParser
        class MyHTMLParser(HTMLParser):
            def handle_starttag(self, tag, attrs):
                print "Encountered a start tag:", tag
            def handle_endtag(self, tag):
                print "Encountered  an end tag:", tag
            def handle_data(self, data):
                print "Encountered   some data:", data

        parser = MyHTMLParser()
            x = parser.feed(catalog_result_str)
        """
        import threading
        import time

        threads = []
        acvs_source_names = acvs_src_name_dist_dict.keys()
        acvs_source_names.sort()
        for i, acvs_source_name in enumerate(acvs_source_names):
            if i <= 8417:
                continue
            #srcname_nobs_dict = {}
            catalog_url_str = "http://www.astrouw.edu.pl/cgi-asas/asas_map_query/%s,4,0.00,13.00,0.00,9.90,10,0,0,asas3?151,151" % (acvs_source_name)
            
            #url_query(catalog_url_str, pars)
            #import pdb; pdb.set_trace()
            #print 
            
            t = threading.Thread(target=url_query, args=[catalog_url_str, self.pars])
            t.start()

            j = 0
            while j < 60:
                if t.isAlive():
                    time.sleep(1)
                else:
                    j = 60
                j += 1
            if t.isAlive():
                # we need to write this i, acvs_source_name to disk
                threads.append(t)
                fp = open('/tmp/asas_fullcatalog_import.dat', 'a+')
                fp.write("%d %s\n" % (i, acvs_source_name))
                fp.close()
            else:
                t.join()



            #### isNOTE: the reason I use a dict is to ensure that no duplicate 
            #insert_list = []
            #for k,v in srcname_nobs_dict.iteritems():
            #    insert_list

            print i, acvs_source_name, catalog_url_str
            #import pdb; pdb.set_trace()
            #print 

    def get_tutor_asas_acvs_sourcenames(self):
        """ Retrieve a list of source-names from the TUTOR ASAS AVCS (proj=126) sources.
        """
        select_str = "SELECT source_name FROM sources WHERE project_id=126"
        self.tutor_execute(select_str)
        results = self.tutor_cursor.fetchall()
        if len(results) == 0:
            raise
        acvs_sourcnames = []
        for row in results:
            acvs_sourcnames.append(row[0])
        return acvs_sourcnames

            
    def get_unretrieved_asas_catalog_sourcename_list(self, sourcename_list_fpath='', nobs_min=0, nobs_max=0):
        """ If given a sourcename_list_fpath, then parse and return the list of source_names.
        Otherwise, query RDB and get a list of source_names using constraints:
           - query asas_fullcatalog for unretrieved sources, between nobs range, order by nobs desc
        Then write the list to file for potential export.
        Also return the list.
        """
        tutor_acvs_sourcenames = self.get_tutor_asas_acvs_sourcenames()

        select_str = "SELECT name, nobs FROM asas_fullcatalog WHERE nobs <= %d AND nobs >= %d AND retrieved=FALSE" % (nobs_max, nobs_min)
        self.tcp_execute(select_str)
        results = self.tcp_cursor.fetchall()
        if len(results) == 0:
            print "NO un-retrieved sources in TABLE asas_fullcatalog in range:", nobs_max, nobs_min
            import pdb; pdb.set_trace()
            print 

        print "Range: %d - %d; Num results=%d" % (nobs_min, nobs_max, len(results))

        sourcename_list = []
        outfile_lines = []
        for row in results:
            source_name, nobs = row
            if source_name in tutor_acvs_sourcenames:
                print 'This source already exists in TUTOR proj=126.  Skipping:', source_name
                continue

            sourcename_list.append(source_name)
            outfile_lines.append("%s\n" % (source_name))
            
        sourcename_fpath = "%s_%d_%d.list" % (self.pars['sourcename_fpath_root'],
                                              nobs_min, nobs_max)
        fp = open(sourcename_fpath, 'w')
        fp.writelines(outfile_lines)
        fp.close()

        return {'sourcename_list':sourcename_list,
                'sourcename_fpath':sourcename_fpath}


    def get_unretrieved_asas_catalog_lightcurves(self, sourcename_list=[]):
        """ This retrieves the lightcurve data for asas-full-catalog sources mention in RDB table.

        - If not given list of source_names to retrieve:
           - query asas_fullcatalog for unretrieved sources, between nobs range, order by nobs desc
           - bulid list of source_names to retrieve
        - Else:
           - parse list of source_names to retrieve
        - Iterate over source_names list, retrieve lightcurve files
        """
        import socket
        socket.setdefaulttimeout(20) # for urllib2 timeout of urlopen()
        import urllib2

        if not os.path.exists(self.pars['lightcurve_download_dirpath']):
            os.system("mkdir -p %s" % (self.pars['lightcurve_download_dirpath']))

        for i, source_name in enumerate(sourcename_list):
            fname = "%s/%s.dat" % (self.pars['lightcurve_download_dirpath'], source_name)
            
            if 1:
                ### slows things down a little bit, might not be nessiccary:
                if os.path.exists(fname):
                    continue # skip since already downloaded
            
            i_try = 0
            while i_try < 3:
                try:
                    url_str = "http://www.astrouw.edu.pl/cgi-asas/asas_cgi_get_data?%s,asas3" % (source_name)
                    fp = urllib2.urlopen(url_str)
                    out_str = fp.read()
                    fp.close()

                    fp = open(fname, 'w')
                    fp.write(out_str)
                    fp.close()
                    i_try = 4
                except:
                    i_try += 1

            print i, len(sourcename_list), source_name


    def update_table_retrieved(self, sourcename_list=[]):
        """ Update the RDB table that sources have been retrieved. 
        """
        insert_list = ["INSERT INTO asas_fullcatalog (name, retrieved) VALUES "]

        for src_name in sourcename_list:
            insert_list.append('("%s", TRUE), ' % (src_name))

            if len(insert_list) > 10000:
                insert_str = ''.join(insert_list)[:-2] + " ON DUPLICATE KEY UPDATE retrieved=VALUES(retrieved)"
                self.tcp_execute(insert_str)
                insert_list = ["INSERT INTO asas_fullcatalog (name, retrieved) VALUES "]

        if len(insert_list) > 1:
            insert_str = ''.join(insert_list)[:-2] + " ON DUPLICATE KEY UPDATE retrieved=VALUES(retrieved)"
            self.tcp_execute(insert_str)


class Asas_Frame_Mag_Percentile(Database_Utils):
    def __init__(self, pars={}):
        self.pars = pars
        self.connect_to_db()


    def analyze_mira_limitmag_frames(self):
        """ This is to be used to look at the frame info for limiting-mag intersection of Miras
        """
        from subprocess import call
        mira_fpath = '/home/dstarr/scratch/mira_list.dat'
        lines = open(mira_fpath).readlines()
        for line in lines:
            obj_name = line.strip()
            select_str = 'SELECT source_id FROM sources WHERE project_id=126 AND source_name="%s"' % (obj_name)
            self.tutor_execute(select_str)
            results = self.tutor_cursor.fetchall()
            if len(results) == 0:
                raise

            source_id = results[0][0]
            if source_id in [215304, 218130]:
                continue # skip
            print "source_id:"
            print source_id

            ### TODO: scp /home/pteluser/scratch/asas_fullcat_lcs/183259-3502.7.dat 192.168.1.25:/tmp/
            exec_str = "scp /home/dstarr/Data/asas_ACVS_50k_data/timeseries/%s tranx:/tmp/asas_source.dat" % (obj_name)
            #os.system(exec_str)
            call(exec_str.split(' ')) # this waits for the command to complete
            sql_str = """
DROP TABLE temp_asas_ts_raw;
            """
            try:
                self.tcp_cursor.execute(sql_str)
            except:
                pass

            sql_str = """
DROP TABLE temp_asas_ts;
            """
            try:
                self.tcp_cursor.execute(sql_str)
            except:
                pass

            sql_str = """

CREATE TABLE temp_asas_ts_raw 
   (hjd DOUBLE,
    mag_0 FLOAT,
    mag_1 FLOAT,
    mag_2 FLOAT,
    mag_3 FLOAT,
    mag_4 FLOAT,
    mer_0 FLOAT,
    mer_1 FLOAT,
    mer_2 FLOAT,
    mer_3 FLOAT,
    mer_4 FLOAT,
    grade VARCHAR(1),
    frame INT);
            """
            self.tcp_execute(sql_str)

            sql_str = """

LOAD DATA INFILE '/tmp/asas_source.dat' INTO TABLE temp_asas_ts_raw 
LINES STARTING BY '   '
      TERMINATED BY '\n'

    (@var1)
SET hjd=SUBSTR(@var1,1,10),
    mag_0=SUBSTR(@var1,12,6),
    mag_1=SUBSTR(@var1,19,6),
    mag_2=SUBSTR(@var1,26,6),
    mag_3=SUBSTR(@var1,33,6),
    mag_4=SUBSTR(@var1,40,6),
    mer_0=SUBSTR(@var1,50,5),
    mer_1=SUBSTR(@var1,56,5),
    mer_2=SUBSTR(@var1,62,5),
    mer_3=SUBSTR(@var1,68,5),
    mer_4=SUBSTR(@var1,74,5),
    grade=SUBSTR(@var1,81,1),
    frame=SUBSTR(@var1,83,6);
            """
            self.tcp_execute(sql_str)

            sql_str = """

CREATE TABLE temp_asas_ts AS SELECT * FROM temp_asas_ts_raw WHERE frame > 0;
            """
            self.tcp_execute(sql_str)

            sql_str = """
SELECT temp_asas_ts.hjd,
       temp_asas_ts.grade,
       temp_asas_ts.frame,
       temp_asas_ts.mag_2,
       asas_fullcat_frame_limits.m_avg,
       asas_fullcat_frame_limits.m_var,
       asas_fullcat_frame_limits.n,
       asas_fullcat_frame_limits.n_c_lim,
       asas_fullcat_frame_limits.n_c_nolim,
       asas_fullcat_frame_limits.n_d,
       asas_fullcat_frame_limits.m0,
       asas_fullcat_frame_limits.m_p98,
       asas_fullcat_frame_limits.m_p95,
       asas_fullcat_frame_limits.m_p93,
       asas_fullcat_frame_limits.m_p90
    FROM temp_asas_ts
    JOIN asas_fullcat_frame_limits USING (frame)
    ORDER BY hjd

            """
            ### SQL query and Print table
            self.tcp_execute(sql_str)
            results = self.tcp_cursor.fetchall()
            for row in results[:2]:
                print row
            import pdb; pdb.set_trace()
            print 
            sql_str = """
DROP TABLE temp_asas_ts_raw;
            """
            self.tcp_execute(sql_str)


    def update_mysqltable_with_magperc(self, fpath=''):
        """ using a file of frame, n, <percentile_mags>, insert this into
        Mysql table (tranx): asas_fullcat_frame_limits
        """
        data = numpy.loadtxt(fpath,
                             dtype={'names': ('frame',
                                              'n',
                                              'm_p98',
                                              'm_p95',
                                              'm_p93',
                                              'm_p90',
                                              'm_p80',
                                              'm_p70',
                                              'm_p60',
                                              'm_p50',
                                              'm_p40',
                                              'm_p30',
                                              'm_p20',
                                              'm_p10'),
                                    'formats': ('i4', 'i4',
                                                'f4', 'f4', 'f4', 'f4', 'f4', 'f4', 'f4', 'f4', 'f4', 'f4', 'f4', 'f4')},
                                           unpack=True)


        insert_list = ["INSERT INTO asas_fullcat_frame_limits (frame, m_p98, m_p95, m_p93, m_p90, m_p80, m_p70, m_p60, m_p50, m_p40, m_p30, m_p20, m_p10) VALUES "]

        for i, frame in enumerate(data['frame']):
            tups = (data['frame'][i],
                    data['m_p98'][i],
                    data['m_p95'][i],
                    data['m_p93'][i],
                    data['m_p90'][i],
                    data['m_p80'][i],
                    data['m_p70'][i],
                    data['m_p60'][i],
                    data['m_p50'][i],
                    data['m_p40'][i],
                    data['m_p30'][i],
                    data['m_p20'][i],
                    data['m_p10'][i])
            insert_list.append('(%d, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f), ' % (tups))
            if len(insert_list) > 10000:
                insert_str = ''.join(insert_list)[:-2] + " ON DUPLICATE KEY UPDATE m_p98=VALUES(m_p98), m_p95=VALUES(m_p95), m_p93=VALUES(m_p93), m_p90=VALUES(m_p90), m_p80=VALUES(m_p80), m_p70=VALUES(m_p70), m_p60=VALUES(m_p60), m_p50=VALUES(m_p50), m_p40=VALUES(m_p40), m_p30=VALUES(m_p30), m_p20=VALUES(m_p20), m_p10=VALUES(m_p10)"
                self.tcp_execute(insert_str)
                insert_list = ["INSERT INTO asas_fullcat_frame_limits (frame, m_p98, m_p95, m_p93, m_p90, m_p80, m_p70, m_p60, m_p50, m_p40, m_p30, m_p20, m_p10) VALUES "]

        if len(insert_list) > 1:
            insert_str = ''.join(insert_list)[:-2] + " ON DUPLICATE KEY UPDATE m_p98=VALUES(m_p98), m_p95=VALUES(m_p95), m_p93=VALUES(m_p93), m_p90=VALUES(m_p90), m_p80=VALUES(m_p80), m_p70=VALUES(m_p70), m_p60=VALUES(m_p60), m_p50=VALUES(m_p50), m_p40=VALUES(m_p40), m_p30=VALUES(m_p30), m_p20=VALUES(m_p20), m_p10=VALUES(m_p10)"
            self.tcp_execute(insert_str)
        import pdb; pdb.set_trace()
        print


    def main(self):
        """ This is to be run on anathem server and use the monetdb:
        """
        import datetime
        #n_frames = 350000 # a slight overestimate of the number of ASAS frames
        import monetdb.sql
        connection = monetdb.sql.connect(username="monetdb", password="monetdb", \
        	   hostname="localhost", database="my-first-db")
        cursor = connection.cursor()
        ### increase the rows fetched to increase performance (optional)
        #cursor.arraysize = n_frames
        select_str = "SELECT frame, count(*) FROM asas_frame_id_mag GROUP BY frame ORDER BY frame"
        cursor.execute(select_str)
        rows = cursor.fetchall()

        n_frames = len(rows)
        frame_arr = numpy.zeros(n_frames, dtype=numpy.int32)
        nobj_arr = numpy.zeros(n_frames, dtype=numpy.int32)
        for i, (frame, nobj) in enumerate(rows):
            frame_arr[i] = frame
            nobj_arr[i] = nobj

        perc_list = [0.98, 0.95, 0.93, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]

        dt_1 = datetime.datetime.now()
        #select_str = "SELECT frame, mag FROM asas_frame_id_mag GROUP BY frame, mag"
        #I think the group by ....mag is messing up#select_str = "SELECT frame, mag FROM asas_frame_id_mag_2 GROUP BY frame, mag ORDER BY frame, mag"
        select_str = "SELECT frame, mag FROM asas_frame_id_mag ORDER BY frame, mag"
        cursor.execute(select_str)
        dt_2 = datetime.datetime.now()
        print "delta_t of frame, mag select:", dt_2 - dt_1
        out_tups = []
        for i, nobj in enumerate(nobj_arr):
            frame = frame_arr[i]
            rows = cursor.fetchmany(size=nobj)

            out_mags = []
            for perc in perc_list:
                n_percentile = int(nobj * perc)
                mag_perc = rows[n_percentile][1]
                #print "frame=%d, nobj=%d, n_percentile=%d, perc=%f, mag_perc=%f" % (frame, nobj, n_percentile, perc, mag_perc)
                out_mags.append(mag_perc)
            out_tups.append([frame, nobj] + out_mags)
        ### I ran these commands to write this to file:
        fp = open('/home/dstarr/scratch/asas_fullcat_percentile_mags', 'w')
        for tup in out_tups: fp.write("%d %d %f %f %f %f %f %f %f %f %f %f %f %f\n" % tuple(tup))
        fp.close()
        import pdb; pdb.set_trace()
        print
        return {'fpath':'/home/dstarr/scratch/asas_fullcat_percentile_mags'}


    # OBSOLETE:  this just gets each frame, count(*) and then iterates over the frames and queriies fora  list of prercentages - to get the percentile magnitudes
    def main__old(self):
        """ This is to be run on anathem server and use the monetdb:
        """
        import datetime
        #n_frames = 350000 # a slight overestimate of the number of ASAS frames
        import monetdb.sql
        connection = monetdb.sql.connect(username="monetdb", password="monetdb", \
        	   hostname="localhost", database="my-first-db")
        cursor = connection.cursor()
        ### increase the rows fetched to increase performance (optional)
        #cursor.arraysize = n_frames
        select_str = "SELECT frame, count(*) FROM asas_frame_id_mag GROUP BY frame LIMIT 1000"
        cursor.execute(select_str)
        dt_1 = datetime.datetime.now()
        rows = cursor.fetchall()
        perc_list = [0.95] #[0.98, 0.95, 0.93, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
        perc_mag_dict = {}
        n_frames = len(rows)
        for perc in perc_list:
            perc_mag_dict[perc] = numpy.zeros(n_frames)
        frame_arr = numpy.zeros(n_frames)
        for i, (frame, nobj) in enumerate(rows):
            frame_arr[i] = frame
            for perc in perc_list:
                select_str = "SELECT mag FROM asas_frame_id_mag WHERE frame=%d ORDER BY mag LIMIT 1 OFFSET %d" % (frame, int(nobj * perc))
                cursor.execute(select_str)
                row = cursor.fetchone()
                perc_mag_dict[perc][i] = row[0]
        dt_2 = datetime.datetime.now()
        print dt_2 - dt_1, 1000, 1
        import pdb; pdb.set_trace()
        print 
        # TODO want to store these results in an altered mysql table


        # TODO altertable asas_fullcat_frame_limits to have new limit mag cols
        # TODO insert frame_mag_95 int mysql asas_fullcat_frame_limits
        # run this for several percentiles.
        #   - do this for 95, since 20 nobs is applicable



if __name__ == '__main__':

    ### NOTE: most of the RDB parameters were dupliclated from ingest_toolspy::pars{}
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
        'asas_map_query_min_incr':1.358, # degrees
        'ra_min':0.0,
        'ra_max':360.0,
        'dec_min':-90.0,
        'dec_max':30.0,
        'acvs_src_name_dist_dict_fpath':'/home/pteluser/acvs_src_name_dist_dict.pkl.gz',
        'sourcename_fpath_root':os.path.expandvars('$HOME/scratch/asas_fullcat'),
        'lightcurve_download_dirpath':os.path.expandvars('$HOME/scratch/asas_fullcat_lcs'),
        'nobs_max':589,
        'nobs_min':588, #below 604, this number should be nobs_max -1 when restarting asas_fullcatalog_import.py
        }

    if 0:
        #### This is to be run on anathem server and use the monetdb:
        afmp = Asas_Frame_Mag_Percentile(pars=pars)
        #perc_mag_dict = afmp.main()
        afmp.update_mysqltable_with_magperc(fpath='/home/dstarr/scratch/asas_fullcat_percentile_mags') #perc_mag_dict['fpath'])
        sys.exit()
    if 1:
        ### This is to be used to look at the frame info for limiting-mag intersection of Miras
        afmp = Asas_Frame_Mag_Percentile(pars=pars)
        afmp.analyze_mira_limitmag_frames()
        sys.exit()


    afci = Asas_Full_Catalog_Import(pars=pars)

    if 0:
        ### This gets the initial list of asas-full-catalog source_names and their Nobs and stores in RDB:
        acvs_src_name_dist_dict = afci.retrieve_grid_acvs_source_names()
        afci.retrieve_asas_catalog_sources(acvs_src_name_dist_dict)
    if 1:
        ### This retrieves the lightcurve data for asas-full-catalog sources mention in RDB table.

        # TODO: want to use nobs ranges that fit within a range
        
        
        nobs_min = pars['nobs_min']
        nobs_max = pars['nobs_max']


        while 1:
            n_obs = 100000 # some arbitrary large number
            while n_obs > 1000:

                select_str = "SELECT count(*) FROM asas_fullcatalog WHERE nobs <= %d AND nobs >= %d AND retrieved=FALSE" % (\
                                     nobs_max, nobs_min)
                afci.tcp_execute(select_str)
                results = afci.tcp_cursor.fetchall()
                n_obs = results[0][0]

                if n_obs > 1000:
                    nobs_min += 1
                else:
                    break
                if (nobs_min + 1) >= nobs_max:
                    break # nobs_min cant grow anymore
            # here nobs should be <= 1000, or cannot get any smaller using nobs_min and nobs_max

            print "Chosen nobs_min, nobs_max:", nobs_min, nobs_max
            #import pdb; pdb.set_trace()
            #print

            source_dict = afci.get_unretrieved_asas_catalog_sourcename_list(nobs_min=nobs_min,
                                                                            nobs_max=nobs_max)
            afci.get_unretrieved_asas_catalog_lightcurves(sourcename_list=source_dict['sourcename_list'])
            afci.update_table_retrieved(sourcename_list=source_dict['sourcename_list'])
            nobs_max = nobs_min - 1 #nobs_min has already been ingested
            nobs_min = nobs_max - 100
            if nobs_min <= 0:
                break # we probably never get here in reasonable time, since there are > 20M sources




    """
### The following commands are useful for getting
###    (asas_fullcat_frame_limits) TABLE information for a
###    specific ASAS source .dat file:
###     - constraints on m_var, or GRADE can be used.

scp /home/pteluser/scratch/asas_fullcat_lcs/183259-3502.7.dat 192.168.1.25:/tmp/

DROP TABLE temp_asas_ts_raw;
DROP TABLE temp_asas_ts;

CREATE TEMPORARY TABLE temp_asas_ts_raw 
   (hjd DOUBLE,
    mag_0 FLOAT,
    mag_1 FLOAT,
    mag_2 FLOAT,
    mag_3 FLOAT,
    mag_4 FLOAT,
    mer_0 FLOAT,
    mer_1 FLOAT,
    mer_2 FLOAT,
    mer_3 FLOAT,
    mer_4 FLOAT,
    grade VARCHAR(1),
    frame INT);

LOAD DATA INFILE '/tmp/183259-3502.7.dat' INTO TABLE temp_asas_ts_raw 
LINES STARTING BY '   '
      TERMINATED BY '\n'

    (@var1)
SET hjd=SUBSTR(@var1,1,10),
    mag_0=SUBSTR(@var1,12,6),
    mag_1=SUBSTR(@var1,19,6),
    mag_2=SUBSTR(@var1,26,6),
    mag_3=SUBSTR(@var1,33,6),
    mag_4=SUBSTR(@var1,40,6),
    mer_0=SUBSTR(@var1,50,5),
    mer_1=SUBSTR(@var1,56,5),
    mer_2=SUBSTR(@var1,62,5),
    mer_3=SUBSTR(@var1,68,5),
    mer_4=SUBSTR(@var1,74,5),
    grade=SUBSTR(@var1,81,1),
    frame=SUBSTR(@var1,83,6);

CREATE TEMPORARY TABLE temp_asas_ts AS SELECT * FROM temp_asas_ts_raw WHERE frame > 0;
DROP TABLE temp_asas_ts_raw;

select * from temp_asas_ts limit 10;

SELECT temp_asas_ts.hjd,
       temp_asas_ts.grade,
       temp_asas_ts.frame,
       temp_asas_ts.mag_2,
       asas_fullcat_frame_limits.m_avg,
       asas_fullcat_frame_limits.m_var,
       asas_fullcat_frame_limits.n,
       asas_fullcat_frame_limits.n_c_lim,
       asas_fullcat_frame_limits.n_c_nolim,
       asas_fullcat_frame_limits.n_d,
       asas_fullcat_frame_limits.m0,
       asas_fullcat_frame_limits.m1,
       asas_fullcat_frame_limits.m2,
       asas_fullcat_frame_limits.m3,
       asas_fullcat_frame_limits.m4
    FROM temp_asas_ts
    JOIN asas_fullcat_frame_limits USING (frame)
    ORDER BY hjd
    ;

    WHERE grade='D'
    LIMIT 10;


 -----+-------+--------+-------+---------+----------+--------+--------+--------+--------+--------+
| hjd        | grade | frame  | n     | m_avg   | m_var    | m0     | m1     | m2     | m3     | m4     |
+------------+-------+--------+-------+---------+----------+--------+--------+--------+--------+--------+
| 3818.81001 | D     | 183313 |     0 |       0 |        0 |      0 |      0 |      0 |      0 |      0 | 
| 2124.61804 | D     |  27642 |     0 |       0 |        0 |      0 |      0 |      0 |      0 |      0 | 
|  1948.8921 | D     |   9129 |     4 | 12.5258 | 0.554665 | 13.021 | 13.014 | 12.825 | 11.243 |      0 | 
| 1950.89155 | D     |   9476 |     0 |       0 |        0 |      0 |      0 |      0 |      0 |      0 | 
| 1978.85767 | D     |  12130 |     0 |       0 |        0 |      0 |      0 |      0 |      0 |      0 | 
    """
