#!/usr/bin/env python 
"""
   v0.2 ned_cache_server.py : Code is now more generic and allows caching of
        SDSS server characteristics as well as NED characs.  I'm coding
        such that new SDSS extractadd new 
   v0.1 ned_cache_server.py : Code which caches and delegates NED
        'nearest object feature' information for various (ra,dec).
        This information is returned to feature-extractors.
        The purpose behind this is that the NED database only allows 1 query
        per second, so we need to regulate & cache our queries.

NOTE: This system works as follows:
      - a server continually queries a shared MySQL table for new (retrieved=0)
        table rows
          - if >= 1 row such as this exists, the 'server' retrieves these items
            from SDSS/NED and populates the MySQL tables, setting (retrieved=1)
      - a client call, generally from tmpned_extractor.py feature extractor
          will, by using a ned_cache_server.py Class for accessing, 
          will query for an (ra,dec) to see if previously retrieved feature
          data exists.
          - if no data exists, it places a (retrieved=0) row in MySQL table
          - if data exists for (ra,dec), it retrieves and fills sdss and ned
            structures which other ned and sdss feature extractors expect.


import ned_cache_server
ncc = ned_cache_server.Ned_Cache_Client(ned_cache_server.pars)
ned_dict = ncc.retrieve_queue_ned_dict(49.599486,-1.005111)
print ned_dict

### Simple DEBUG snippet to submit ra,dec & get ned dict:
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 45623))
#s.send("%lf@%lf" % (49.599486,-1.005111))
s.send("%lf@%lf" % (48.0,-3.005111))
data = s.recv(512)
s.close()
rec_data = repr(data).replace("@"," ")
print rec_data

"""
import sys, os
import time
import MySQLdb
import copy

sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                 'Software/feature_extract/Code/extractors/'))
import ned
import sdss

pars = {
    'ned_cache_hostname':'192.168.1.25',
    'ned_cache_username':'pteluser', #'dstarr',
    'ned_cache_database':'ned_feat_cache',
    'ned_cache_db_port':3306, #3306,
    'tablename__ch_id_defs':'ch_id_defs', 
    'tablename__ch_spatial':'ch_spatial',
    'tablename__ch_vals':'ch_vals',
    'tablename__ptf_footprint':'ptf_footprint',
    'ptf_postgre_dbname':'subptf', # KLUDGE: these ptf* are taken from ingest_tools.py
    'ptf_postgre_user':'dstarr',
    'ptf_postgre_host':'sgn02.nersc.gov',
    'ptf_postgre_password':'*2ta77',
    'ptf_postgre_port':6540,
    'ptf_postgre_sub_tablename':'subtraction',
    'ptf_postgre_candidate_tablename':'candidate',
    'htm_level':17, #BIGINT, ~0.024-0.053 arcsec resolution
    'htm_query_radius':0.016666 * 5.0, # in arcmins, used in SQL/HTM spatial query
    'while_loop_sleep_time':1, # seconds. Not too short: SQL query done for each
    'socket_loop_sleep_time':0.1, # seconds. May be short.
    'socket_bind_wait_time':3.0, # seconds.
    'socket_server_port':45623,
    'socket_n_backlog_connections':50,
    'do_ned_query':False,
    'do_sdss_query':True,
    'char_replace':{'-':'_',
                    '+':'_',
                    '"':'_',
                    "'":'_',
                    " ":'_'},
    }
pars['tablename__ch_spatial_htm'] = pars['tablename__ch_spatial'] + '_htm'


# For return to Feature extractors:
class Sdss_Obj:
    def __init__(self):
        self.feature = {}




# For return to Feature extractors:
class Ned_Dictlike_Obj:
    def __init__(self):
        self.__dict__ = {}


    def __getitem__(self, key):
        return self.__dict__[key]


    def __setitem__(self, key, value):
        self.__dict__[key] = value


    def __str__(self):
        return str(self.__dict__)


    def __len__(self):
        return len(self.__dict__)


    def distance_in_arcmin_to_nearest_galaxy(self):
        # NOTE: -1 is N/A
        ret_dict = {'distance':self.__dict__.get('source_info',{})\
                                            .get('distance_arcmin', -1)}
        return ret_dict

    def distance_in_kpc_to_nearest_galaxy(self):
        # NOTE: -1 is N/A
        ret_dict = {'distance':self.__dict__.get('source_info',{})\
                                            .get('kpc_offset', -1)}
        return ret_dict


def select_ned_data_from_table(ra, dec, cursor):
    """ Select NN info for a (ra,dec) and place in ned.py-like dict.
    """
    ned_out_dict = Ned_Dictlike_Obj()
    sdss_out_dict = Sdss_Obj()

    select_str = "SELECT spatial_id FROM %s WHERE (DIF_HTMCircle(%lf, %lf, %lf)) LIMIT 1" % \
                 (pars['tablename__ch_spatial_htm'], \
                  ra, dec, pars['htm_query_radius'])
    cursor.execute(select_str)
    results = cursor.fetchall()

    spatial_id = -1
    try:
        if results[0][0] >= 0:
            spatial_id = results[0][0]
    except:
        pass

    if spatial_id == -1:
        return (ned_out_dict, sdss_out_dict) # Default "empty" dict-like objects

    select_str = "SELECT y.ch_group, y.ch_name, x.ch_val_dbl, x.ch_val_str, y.ch_type FROM %s AS x JOIN %s AS y ON y.ch_id = x.ch_id WHERE spatial_id=%d" %\
                 (pars['tablename__ch_vals'],
                  pars['tablename__ch_id_defs'],
                  spatial_id)
    cursor.execute(select_str)
    results = cursor.fetchall()

    ################
    # Here we form the feature-extractor expected structures from RDB SELECT

    if len(results) > 0:
        ned_out_dict['source_info'] = {}
        for (ch_group, ch_name, ch_val_dbl, ch_val_str, ch_type) in results:
            if ch_group == 0:
                # NED
                if ch_name == 'distance':
                    ned_out_dict['distance'] = ch_val_dbl
                if ch_type:
                    ned_out_dict['source_info'][ch_name] = ch_val_str
                else:
                    ned_out_dict['source_info'][ch_name] = ch_val_dbl
            else:
                # SDSS (ch_group == 1)
                if ch_type:
                    sdss_out_dict.feature[ch_name] = ch_val_str
                else:
                    sdss_out_dict.feature[ch_name] = ch_val_dbl

    return (ned_out_dict, sdss_out_dict)


class Ned_Cache_Server:
    """ Caches and delegates NED (ra,dec) queries for 'nearest object' features.
    """
    #import socket
    def __init__(self, pars):
        self.pars = pars
        self.NED_connection_is_free = True # whether method can query NED server
        self.threads = []

        # Make general connection to MySQL server:
        self.db = MySQLdb.connect(host=self.pars['ned_cache_hostname'], 
                                  user=self.pars['ned_cache_username'],
                                  db=self.pars['ned_cache_database'],
                                  port=self.pars['ned_cache_db_port'])
        self.cursor = self.db.cursor()


    def sig_handler(self, signum, frame):
        """ Catch:  'kill':SIGTERM, ^C: SIGINT
        """
        print "Got signal: %i" % (signum)
        self.do_loop = False


    def drop_tables(self):
        """ Drop tables and MySQL stuff.
        """
        # Drop main tables:
        try:
            table_list = [('TABLE', self.pars['tablename__ch_id_defs']),
                          ('TABLE', self.pars['tablename__ch_spatial']),
                          ('TABLE', self.pars['tablename__ch_vals'])]
            for t_type, table_name in table_list:
                drop_table_str = "DROP %s IF EXISTS %s" % (t_type,
                                                           table_name)
                print drop_table_str
                self.cursor.execute(drop_table_str)

            # Drop HTM / dif triggers, views:
            drop_table_str = """DROP view %s.%s;
                                """ % ( \
                self.pars['ned_cache_database'],
                self.pars['tablename__ch_spatial_htm'])
            self.cursor.execute(drop_table_str)
        except:
            print '!!! unable to drop tables / views'


    def create_tables(self):
        """ Create MySQL Tables.
        """
        # NOTE: ch_type SMALLINT,  ### 0:double,   1:string
        create_str = """CREATE TABLE %s (
            ch_id SMALLINT,
            ch_group TINYINT,
            ch_type SMALLINT,
            ch_name VARCHAR(40),
            PRIMARY KEY (ch_id),
            INDEX(ch_group, ch_name))
        """ % (self.pars['tablename__ch_id_defs'])
        self.cursor.execute(create_str)

        #20090504: ch_val_str VARCHAR(500), # if this is changed again, also edit L357
        create_str = """CREATE TABLE %s (
            ch_id SMALLINT,
            ch_val_dbl DOUBLE,
            ch_val_str VARCHAR(20),
            spatial_id INT UNSIGNED,
            PRIMARY KEY (spatial_id, ch_id))
        """ % (self.pars['tablename__ch_vals'])
        self.cursor.execute(create_str)

        # 20090724: dstarr removes obsolete index below:
        #     INDEX(local_retr_dtime)
        create_str = """CREATE TABLE %s (
            ra DOUBLE,
            decl DOUBLE,
            spatial_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
            retrieved TINYINT DEFAULT 0,
            local_retr_dtime DATETIME DEFAULT NULL,
            PRIMARY KEY (spatial_id),
            INDEX(retrieved))
        """ % (self.pars['tablename__ch_spatial'])
        self.cursor.execute(create_str)

        create_str = """CREATE TABLE %s (
            spatial_id INT UNSIGNED NOT NULL,
            ujd DOUBLE,
            lmt_mg FLOAT,
            PRIMARY KEY (spatial_id, ujd))
        """ % (self.pars['tablename__ptf_footprint'])
        self.cursor.execute(create_str)

        make_dif = \
              "$HOME/bin/dif --index-htm %s %s %d ra decl < /dev/null" % \
                                  (self.pars['ned_cache_database'], \
                                   self.pars['tablename__ch_spatial'], \
                                   self.pars['htm_level'])
        os.system(make_dif)


    def retrieve_insert_ned_data_to_table(self, ra, dec, spatial_id, cursor, \
                                                            update_only=False):
        """ Insert ned.py extracted NN dict info into RDB table.
        """
        insert_list = ["INSERT INTO %s (%s.spatial_id, %s.ch_id, %s.ch_val_dbl, %s.ch_val_str) VALUES " % (\
                           self.pars['tablename__ch_vals'],
                           self.pars['tablename__ch_vals'],
                           self.pars['tablename__ch_vals'],
                           self.pars['tablename__ch_vals'],
                           self.pars['tablename__ch_vals'])]

        if self.pars['do_ned_query']:
            ### NED INSERT:
            n = ned.NED(pos=(ra,dec),verbose=False, do_threaded=False)
            nn_dict = n.distance_in_arcmin_to_nearest_galaxy()
            if not nn_dict.get('source_info',{}).has_key('kpc_offset'):
                print 'ERROR: odd nn_dict:', nn_dict
            else:
                nice_name = nn_dict['source_info']['name']
                for old,new in self.pars['char_replace'].iteritems():
                    nice_name = nice_name.replace(old,new)
                if nn_dict['source_info']['dm'] == '':
                    float_dm = -1
                else:
                    float_dm = float(nn_dict['source_info']['dm'])

                ################
                # Here we parse the feature-extractor structures for INSERT:
                nn_dict['source_info']['distance'] = nn_dict['distance']
                for ch_name,ch_val in nn_dict['source_info'].iteritems():
                    if not self.chname_chid_lookup.has_key((0,ch_name)):
                        continue # skip this ch_name since its not a charac.
                    if self.chname_type_lookup[(0,ch_name)]:
                        ch_val_dbl = 'NULL'
                        ch_val_str = "'%s'" % (ch_val)
                    else:
                        ch_val_dbl = "%f" % (ch_val)
                        ch_val_str = 'NULL'
                    insert_list.append("(%d, %d, %s, %s), " % ( \
                        spatial_id, self.chname_chid_lookup[(0,ch_name)], \
                        ch_val_dbl, ch_val_str))

        if self.pars['do_sdss_query']:
            ### SDSS INSERT:
            s = sdss.sdssq(pos=(ra,dec),verbose=True,maxd=0.2*1.05) # 0.2*1.05 :: dont report anything farther away than this in arcmin

            sdss_dict = s.feature
            if not sdss_dict.has_key('in_footprint'):
                print 'ERROR: odd sdss_dict:', sdss_dict
            else:
                ################
                # Here we parse the feature-extractor structures for INSERT:
                for ch_name,ch_val in sdss_dict.iteritems():
                    if not self.chname_chid_lookup.has_key((1,ch_name)):
                        continue # skip this ch_name since its not a charac.
                    if ch_val == None:
                        ch_val_dbl = 'NULL'
                        ch_val_str = 'NULL'                        
                    elif self.chname_type_lookup[(1,ch_name)] == 1:
                        ch_val_dbl = 'NULL'
                        ch_val_str = "'%s'" % (ch_val[-20:])
                    elif self.chname_type_lookup[(1,ch_name)] == 2:
                        ch_val_dbl = 'NULL'
                        ch_val_str = 'NULL'                        
                    else:
                        ch_val_dbl = "%f" % (ch_val)
                        ch_val_str = 'NULL'
                    insert_list.append("(%d, %d, %s, %s), " % ( \
                        spatial_id, self.chname_chid_lookup[(1,ch_name)], \
                        ch_val_dbl, ch_val_str))

            if len(insert_list) > 1:
                insert_str = ''.join(insert_list)[:-2] + ' ON DUPLICATE KEY UPDATE spatial_id=VALUES(spatial_id), ch_id=VALUES(ch_id), ch_val_dbl=VALUES(ch_val_dbl), ch_val_str=VALUES(ch_val_str)'
                cursor.execute(insert_str)

        update_str = \
              "UPDATE %s SET retrieved=1 WHERE (spatial_id=%d)" % (\
                     self.pars['tablename__ch_spatial'], spatial_id)
        cursor.execute(update_str)

    # obsolete:
    def retrieve_from_pgsql_insert_into_local_table(self, pgsql_cursor=None,
                                                          mysql_cursor=None,
                                                          rdb_rows=[]):
        """ Given a list of soruce-positions (ra,dec,id) which are retrieved from
        MysqlDB accounting table, retrieve:
         - footprint limiting magnitude data from PGSQL-lbl database
             and store locally.
         - (? other non-delayed tasks (like SDSS/NED) ?)
        """
        # NOTE: the following is not intended to be used as an INSERT, since the row already exists, but I use this to allow UPDATEING of many rows at once (using INSERT ... UPDATE syntax):
        #chspatial_update_list = ["INSERT INTO %s (spatial_id) VALUES " % (self.pars['tablename__ch_spatial'])]
        chspatial_update_list = ["UPDATE %s SET local_retr_dtime=NOW() WHERE " % (self.pars['tablename__ch_spatial'])]

        footprint_insert_list = ["INSERT INTO %s (spatial_id, ujd, lmt_mg) VALUES " % (self.pars['tablename__ptf_footprint'])]
        offset_deg = 0.0005556
        for (ra, dec, spatial_id) in rdb_rows:
            chspatial_update_list.append("(spatial_id=%d) OR " % (spatial_id))
            select_str = "select obsjd, lmt_mg from proc_image where box(polygon'((%lf, %lf), (%lf, %lf), (%lf, %lf), (%lf, %lf), (%lf, %lf))') && box(image_footprint)" % ( \
                ra - offset_deg,
                dec + offset_deg,
                ra + offset_deg,
                dec + offset_deg,
                ra + offset_deg,
                dec - offset_deg,
                ra - offset_deg,
                dec - offset_deg,
                ra - offset_deg,
                dec + offset_deg)
            pgsql_cursor.execute(select_str)
            rdb_rows = pgsql_cursor.fetchall()
            
            for (ujd, lmt_mg) in rdb_rows:
                if ujd == None:
                    continue # this happens occasionally
                footprint_insert_list.append("(%d, %lf, %lf), " % (spatial_id, ujd, lmt_mg))

        footprint_insert_str = ''.join(footprint_insert_list)[:-2] + ' ON DUPLICATE KEY UPDATE spatial_id=VALUES(spatial_id), ujd=VALUES(ujd), lmt_mg=VALUES(lmt_mg)'
        mysql_cursor.execute(footprint_insert_str)

        # NOTE: the following is not intended to be used as an INSERT, since the row already exists, but I use this to allow UPDATEING of many rows at once (using INSERT ... UPDATE syntax):
        chspatial_update_str = ''.join(chspatial_update_list)[:-3]
        mysql_cursor.execute(chspatial_update_str)

        # TODO: also update the accounting table with a datetimed local_retr_dtime == NOW()


    def rdb_table_watcher(self):
        """ This method continually polls the local NED MySQL table for
        new position additions which have not had NED data retrieved.
        This then queues a list of positions & retrieves NED data, updating
        the RDB table.  When in NED-querying mode, it locks/flags other methods
        from querying the remote NED service.
        """
        import time

        # ??? Why did I choose to have this DB cursor locally instantiated?

        db = MySQLdb.connect(host=self.pars['ned_cache_hostname'], 
                                  user=self.pars['ned_cache_username'],
                                  db=self.pars['ned_cache_database'])
        cursor = db.cursor()

        while self.do_loop:
            try:
                select_str = \
                  "SELECT ra,decl,spatial_id FROM %s WHERE NOT retrieved LIMIT 50000" % \
                                                (self.pars['tablename__ch_spatial'])
                #print 'select_str=', select_str
                cursor.execute(select_str)
                results = cursor.fetchall()
                if len(results) == 0:
                    time.sleep(self.pars['while_loop_sleep_time'])
                    print '.',
                    continue
                else:
                    self.NED_connection_is_free = False
                    for (ra, dec, spatial_id) in results:
                        self.retrieve_insert_ned_data_to_table(ra, dec, spatial_id,\
                                                           cursor, update_only=True)
                    self.NED_connection_is_free = True
            except:
                print 'EXCEPT during cursor.execute(), DB down?  Sleeping for a bit...'
                print 'select_str=', select_str
                time.sleep(self.pars['while_loop_sleep_time'])
        print "Out of while loop"

    ####

    # obsolete:
    def local_retr_table_watcher(self):
        """ This method continually polls the local NED MySQL table for
        new position additions which have not had NED data retrieved.
        This then queues a list of positions & retrieves NED data, updating
        the RDB table.  When in NED-querying mode, it locks/flags other methods
        from querying the remote NED service.
        """
        import time
        import psycopg2

        # I chose to have this DB cursor locally instantiated so that multiple threads can poll DB.

        mysql_db = MySQLdb.connect(host=self.pars['ned_cache_hostname'], 
                                  user=self.pars['ned_cache_username'],
                                  db=self.pars['ned_cache_database'])
        mysql_cursor = mysql_db.cursor()

        pg_conn = psycopg2.connect(\
             "dbname='%s' user='%s' host='%s' password='%s' port=%d" % \
                            (self.pars['ptf_postgre_dbname'],\
                             self.pars['ptf_postgre_user'],\
                             self.pars['ptf_postgre_host'],\
                             self.pars['ptf_postgre_password'],\
                             self.pars['ptf_postgre_port']))
        pg_cursor = pg_conn.cursor()

        while self.do_loop:
            #try:
            if 1:
                select_str = \
                  "SELECT ra,decl,spatial_id FROM %s ORDER BY local_retr_dtime ASC LIMIT 100" %\
                                                (self.pars['tablename__ch_spatial'])
                mysql_cursor.execute(select_str)
                results = mysql_cursor.fetchall()
                if len(results) == 0:
                    time.sleep(self.pars['while_loop_sleep_time'])
                    print '.',
                    continue
                else:
                    #self.NED_connection_is_free = False
                    #TODO: the passed in method should take the full list of ra,dec, spatial_id.
                    #   and then fill some other table with values retrieved from PGSQL.
                    self.retrieve_from_pgsql_insert_into_local_table( \
                                                          pgsql_cursor=pg_cursor,
                                                          mysql_cursor=mysql_cursor,
                                                          rdb_rows=results)

                    #for (ra, dec, spatial_id) in results:
                    #    self.retrieve_insert_ned_data_to_table(ra, dec, spatial_id,\
                    #                                       mysql_cursor, update_only=True)
                    #self.NED_connection_is_free = True
            #except:
            if 0:
                print 'EXCEPT during cursor.execute(), DB down?  Sleeping for a bit...'
                print 'select_str=', select_str
                time.sleep(self.pars['while_loop_sleep_time'])
        print "Out of while loop"


    ####


    def get_chdefs_from_srccode(self):
        """ Generate 'ch_id_defs_list' list(dict) from features which exist
        in current software extractors (source code).

        KLUDGE: Currently ch_id_defs_list[{}] is explicitly filled below
                for testing, development.

        TODO: Eventually parse (sdss,ned) features from
              feature_extract/Code/extractor/ directory.

              For now I just hardcode a list{dict}
        """
        ch_id_defs_list = [ \
            {'ch_id':0,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'best_dl',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':0,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'best_dm',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':0,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'best_offset_in_kpc',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':1,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'best_offset_in_petro_g',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':2,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'bestz',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':3,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'bestz_err',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':4,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'chicago_class',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':5,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'chicago_status',
             'val_type':0, # 0:double,   1:string ###20090504 1->0
             },
            {'ch_id':6,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'chicago_z',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':7,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'dec',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':8,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'dered_g',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':9,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'dered_i',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':10,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'dered_r',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':11,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'dered_u',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':12,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'dered_z',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':13,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'dist_in_arcmin',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':14,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'first_flux_in_mJy',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':15,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'first_offset_in_arcsec',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':16,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'in_footprint',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':17,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'objid',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':18,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'petroRadErr_g',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':19,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'petroRad_g',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':20,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'photo2_flag',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':21,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'photo2_z_cc',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':22,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'photo2_z_d1',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':23,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'photo2_zerr_cc',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':24,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'photo2_zerr_d1',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':25,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'photo_rest_abs_g',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':26,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'photo_rest_abs_i',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':27,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'photo_rest_abs_r',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':28,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'photo_rest_abs_u',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':29,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'photo_rest_abs_z',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':30,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'photo_rest_gr',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':31,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'photo_rest_iz',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':32,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'photo_rest_ri',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':33,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'photo_rest_ug',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':34,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'photo_z',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':35,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'photo_zerr',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':36,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'ra',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':37,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'rosat_cps',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':38,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'rosat_flux_in_microJy',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':39,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'rosat_hardness_1',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':40,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'rosat_hardness_2',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':41,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'rosat_log_xray_luminosity',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':42,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'rosat_offset_in_arcsec',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':43,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'rosat_offset_in_sigma',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':44,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'rosat_poserr',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':45,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'spec_confidence',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':46,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'spec_veldisp',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':47,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'spec_z',
             'val_type':0, # 0:double,   1:string
             },
            {'ch_id':48,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'spec_zStatus',
             'val_type':1, # 0:double,   1:string
             },
            {'ch_id':49,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'type',
             'val_type':1, # 0:double,   1:string
             },
            {'ch_id':50,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'url',
             'val_type':1, # 0:double,   1:string
             },
            {'ch_id':51,
             'ch_group':1, #0:NED, 1:SDSS featclass
             'ch_name':'urlalt',
             'val_type':2, # 0:double,   1:string,   2:NULL
             },
            {'ch_id':52,
             'ch_group':0, #0:NED, 1:SDSS featclass
             'ch_name':'distance',
             'val_type':0, # 0:double,   1:string
            },
            {'ch_id':53,
             'ch_group':0, #0:NED, 1:SDSS featclass
             'ch_name':'z',
             'val_type':0, # 0:double,   1:string
            },
            {'ch_id':54,
             'ch_group':0, #0:NED, 1:SDSS featclass
             'ch_name':'dm',
             'val_type':0, # 0:double,   1:string
            },
            {'ch_id':55,
             'ch_group':0, #0:NED, 1:SDSS featclass
             'ch_name':'name',
             'val_type':1, # 0:double,   1:string
            },
            {'ch_id':56,
             'ch_group':0, #0:NED, 1:SDSS featclass
             'ch_name':'distance_arcmin',
             'val_type':0, # 0:double,   1:string
            },
            {'ch_id':57,
             'ch_group':0, #0:NED, 1:SDSS featclass
             'ch_name':'kpc_offset',
             'val_type':0, # 0:double,   1:string
            },
            {'ch_id':58,
             'ch_group':0, #0:NED, 1:SDSS featclass
             'ch_name':'kpc_arcmin',
             'val_type':0, # 0:double,   1:string
            }]
        return ch_id_defs_list


    def get_chdefs_from_table(self):
        """ This retrieves existing charac_id entries from 'ch_id_defs' TABLE
        and returns results in a ch_defs[{}]
        """
        ch_defs = []
        select_str = "SELECT ch_id, ch_group, ch_type, ch_name FROM %s" % ( \
                                            self.pars['tablename__ch_id_defs'])
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()
        for result in results:
            if len(result) != 4:
                print 'ERROR: %s returns an unexpected result: %s' % ( \
                                                       select_str, str(result))
            result_dict = {'ch_id':result[0],
                           'ch_group':result[1], #0:NED, 1:SDSS featclass
                           'ch_name':result[3],
                           'val_type':result[2], # 0:double,   1:string
                           }
            ch_defs.append(result_dict)
        return ch_defs


    def determine_chdefs_not_in_table(self, existing_table_chdefs,
                                      srccode_chdefs):
        """Updates srccode_chdefs[{}] with 'ch_id' numbers from existing
               entries in existing_table_chdefs[{}]
        Then, for entries not in " " " ", they be given a ch_id = MAX(ch_id)+1
        """
        existing_ch_id_list = []
        for exist_chdef in existing_table_chdefs:
            existing_ch_id_list.append(exist_chdef['ch_id'])
        if len(existing_ch_id_list) == 0:
            max_ch_id = -1 # so first incremented id is 0
        else:
            max_ch_id = max(existing_ch_id_list)

        new_chdefs = []
        all_chdefs = copy.deepcopy(existing_table_chdefs)

        for srccode_chdef in srccode_chdefs:
            is_in_exist_chdef = False
            # This is done brute force & CPU slow:
            for exist_chdef in all_chdefs:
                if ((srccode_chdef['ch_name'] == exist_chdef['ch_name']) and
                    (srccode_chdef['ch_group'] == exist_chdef['ch_group'])):
                    is_in_exist_chdef = True
                    break
            if not is_in_exist_chdef:
                updated_chdef = copy.deepcopy(srccode_chdef)
                max_ch_id += 1
                updated_chdef['ch_id'] = max_ch_id
                all_chdefs.append(updated_chdef)
                new_chdefs.append(updated_chdef)

        self.chname_chid_lookup = {}
        self.chname_type_lookup = {}
        for chdef in all_chdefs:
            self.chname_chid_lookup[(chdef['ch_group'], chdef['ch_name'])] = chdef['ch_id']
            self.chname_type_lookup[(chdef['ch_group'], chdef['ch_name'])] = chdef['val_type']

        # NOTE: now we have syncd 'ch_id_defs' TABLE which matches all_chdefs[]
        self.all_chdefs = all_chdefs  # This will be referenced in later code.

        return new_chdefs


    def update_chdefs_table(self, new_ch_defs):
        """ using new_chdefs, we add new entries to 'ch_id_defs' table
        """
        if len(new_ch_defs) == 0:
            return # don't INSERT anything.
        insert_list = \
              ["INSERT INTO %s (ch_id, ch_group, ch_type, ch_name) VALUES " % (\
                                            self.pars['tablename__ch_id_defs'])]
        for ch_def in new_ch_defs:
            insert_list.append("(%d, %d, %d, '%s'), " % \
                               (ch_def['ch_id'],
                                ch_def['ch_group'],
                                ch_def['val_type'],
                                ch_def['ch_name']))

        self.cursor.execute(''.join(insert_list)[:-2])


    def initialize_loop_threads(self):
        """ Start table-watching and socket server threads.
        Both threads while(self.do_loop), which is coupled to SIGINT event.
        """
        import signal
        import threading

        self.do_loop = True
        signal.signal(signal.SIGINT, self.sig_handler) # Handle ^C

        existing_table_chdefs = self.get_chdefs_from_table()

        srccode_chdefs = self.get_chdefs_from_srccode()

        new_chdefs = self.determine_chdefs_not_in_table(existing_table_chdefs,
                                                        srccode_chdefs)
        self.update_chdefs_table(new_chdefs)

        # TODO: now we use all_chdefs[] when storing queried SDSS & NED data.
        #self.rdb_table_watcher()

        # TODO: eventually thread this off:
        # 20090524: I just coded this and then decided not to use it:
        #self.local_retr_table_watcher()

        t = threading.Thread(target=self.rdb_table_watcher, args=[])
        self.threads.append(t)
        t.start()


        ### Disable socket server for now:
        #self.socket_listening_server()
        #t = threading.Thread(target=self.socket_listening_server, args=[])
        #self.threads.append(t)
        #t.start()



    def wait_for_thread_joins(self):
        """ Wait for all loop threads to join.
        """
        for t in self.threads:
            t.join()
        print "All threads have joined"


    def insert_radec_into_cachetable_for_retrieval(self, ra, dec, cursor):
        """ This INSERTs ra,dec only row into local cache table, so
        table-watching thread will eventually retrieve from NED and UPDATE
        it's entry in the local cache table.
        """
        insert_str="INSERT INTO %s (ra, decl, retrieved) VALUES (%lf, %lf, 0)"%\
                                (self.pars['ned_cache_tablename_root'], ra, dec)
        cursor.execute(insert_str)


    def get_ned_dict_trying_local_or_remote(self, ra, dec):
        """ Attempt to retrieve NED dict from local cache table, or from
        the NED service, or lastly just queue in table for eventual NED
        retrieval by other thread.
        """
        (ned_dict, sdss_dict) = select_ned_data_from_table(ra, dec, self.cursor)
        if len(ned_dict) > 0:
            if str(ned_dict['distance']) != "NULL":
                return ned_dict
            update_only=True
        else:
            update_only=False
        if self.NED_connection_is_free:
            self.NED_connection_is_free = False
            # NOTE: OK to use self.cursor since other thread cursor is independt
            self.retrieve_insert_ned_data_to_table(ra, dec, self.cursor, \
                                                        update_only=update_only)
            self.NED_connection_is_free = True
            (ned_dict, sdss_dict) = select_ned_data_from_table(ra, dec, self.cursor)
            return ned_dict
        else:
            self.insert_radec_into_cachetable_for_retrieval(ra, dec,self.cursor)
            return {}


    def socket_listening_server(self):
        """ This loop waits for a socket connection, which passes (ra,dec)
        and then tries to retrieve a NED dict, which it returns.
        The NED dict retrieval can be done via direct NED server query or
        retrieving from local NED cache database, or queue retrieval & return {}
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try_to_bind = True
        while try_to_bind:
            try:
                s.bind(('', self.pars['socket_server_port']))
                try_to_bind = False
            except:
                print "socket %d still in use"%(self.pars['socket_server_port'])
                time.sleep(self.pars['socket_bind_wait_time'])

        print "In socket listening loop..."
        s.listen(self.pars['socket_n_backlog_connections'])
        while self.do_loop:
            time.sleep(self.pars['socket_loop_sleep_time'])
            conn, addr = s.accept()
            rec_str = conn.recv(64).split("@")
            if len(rec_str) != 2:
                continue # skip blank lines, which terminate queries
            try:
                ra = float(rec_str[0])
                dec = float(rec_str[1])
            except:
                continue # skip weird values

            ned_dict = self.get_ned_dict_trying_local_or_remote(ra, dec)

            dict_str = str(ned_dict)
            #out_str = "Hello@Joe,@%s %s" % (rec_str[0], rec_str[1])
            conn.send(dict_str)
            conn.close()


class Ned_Cache_Client:
    """ Client class called within NED feature extractor, which retrieves
    ned_dict{} from cache table, if available; or queues todo-task by
    adding a "retrieve==0" row (for ra,dec) to cache table.
    """
    def __init__(self, pars):
        self.pars = pars
        # Make general connection to MySQL server:
        self.db = MySQLdb.connect(host=self.pars['ned_cache_hostname'], 
                                  user=self.pars['ned_cache_username'],
                                  db=self.pars['ned_cache_database'],
                                  port=self.pars['ned_cache_db_port'])
        self.cursor = self.db.cursor()


    def retrieve_queue_ned_dict(self, ra, dec):
        """ Given an (ra,dec), Attempt to retrieve filled ned_dict{} from
        ned_cache table; if row is queued/empty, return {}; if (ra,dec) not
        in table, add todo (retrieve=0) entry to table (for (ra,dec)).
        """
        (ned_obj, sdss_obj) = select_ned_data_from_table(ra, dec, self.cursor)
        if len(ned_obj) > 0:
            #20090123: dstarr comments out: #if str(ned_obj['distance']) == "NULL":
            if len(sdss_obj.feature) <= 0:
                return (Ned_Dictlike_Obj(), Sdss_Obj())
            else:
                return (ned_obj, sdss_obj)
        else:
            # This is non-existant row case.  Need to add a (retrieved==0) row.
            query_str = "INSERT INTO " + self.pars['tablename__ch_spatial'] + " (retrieved, ra, decl) VALUES (0, %lf, %lf)"
            insert_str = query_str % (ra, dec)
            self.cursor.execute(insert_str)
            return (Ned_Dictlike_Obj(), Sdss_Obj())


if __name__ == '__main__':

    # Can populate ned-cache-server using ra,decs from MySQL outfile:
    #       select ra,decl from sh_spatial into outfile '/tmp/out';
    # The results can be loaded back in once the ned_cach_server.py is running:
    #       load data infile '/tmp/out' into table ch_spatial (ra,decl);

    ##### Do Index server:
    ncs = Ned_Cache_Server(pars)
    #20081026: I don't want to drop all this hard work. I comment out:
    #ncs.drop_tables()
    #ncs.create_tables()
    #sys.exit()

    ncs.initialize_loop_threads()

    ncs.wait_for_thread_joins()
