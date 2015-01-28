#!/usr/bin/env python 
"""
   v0.2 code adapted for src-id index generation as well
   v0.1 initial version: obj-id index generation

Socket server, with client methods.
Does accounting for the obj_id index assignment.

On server startup, it queries the MySQL database to determine the max
existing obj_id index.  Then, it listens for 'ingest_tool.py' clients
query the socket server for an index of <some number of row range>.  This
server responds with the low and high indicies now reserved for the
client.  The server then increments its internal index counter and then waits
for the next client connection.

NOTE: Don't have multiple instances of obj_id_toold.py running at once.
NOTE: There is a bit of a hysteresis in how quickly the clients add objects
     to the MySQL database, so restarting obj_id_sockets.py may require
     a miniute pause.
NOTE: Often the pars['socket_server_port'] needs to be incremented on restart.

NOTE: If MySQL tables are going to be dropped (for testing purposes), 
      obj_id_sockets.py will need to be restarted, in order to account for
      the max(obj_id).
NOTE: Client is run with methods:
        import obj_id_sockets
        obj_id_sockets.socket_client().get_index_range_from_server(400)
NOTE: Server started using shell command:
        ./obj_id_sockets.py server_type=src_id

"""
import os, sys
import MySQLdb
import socket
import time
import datetime
import param_tool

### Global variable used in <object>.pars:
pars = {'server_type':'', # This must be specified as an argv parameter
        'obj_id':{\
            'socket_server_host_ip':"127.0.0.1", #"192.168.1.45",
            'socket_server_port':50020,
            'socket_midway_port':50021,
            'rdb_server_host_ip':"127.0.0.1", # "192.168.1.45",
            'rdb_server_port':3306,
            'rdb_server_user':"pteluser",
            'rdb_server_db':'object_db', #'tcp_db_2',
            'primary_table_colname':'obj_id',
            'obj_id_reference_tablename':'sdss_events_a',
            },
        'ptel_obj_id':{\
            'socket_server_host_ip':"127.0.0.1",#"192.168.1.45",
            'socket_server_port':50040,
            'socket_midway_port':50041,
            'rdb_server_host_ip':"127.0.0.1",# "192.168.1.45",
            'rdb_server_port':3306,
            'rdb_server_user':"pteluser",
            'rdb_server_db':'object_db',
            'primary_table_colname':'obj_id',
            'obj_id_reference_tablename':'pairitel_events_a',
            },
        'ptf_obj_id':{\
            'socket_server_host_ip':"127.0.0.1",#"192.168.1.45",
            'socket_server_port':50070,
            'socket_midway_port':50071,
            'rdb_server_host_ip':"127.0.0.1",# "192.168.1.45",
            'rdb_server_port':3306,
            'rdb_server_user':"pteluser",
            'rdb_server_db':'object_db',
            'primary_table_colname':'obj_id',
            'obj_id_reference_tablename':'ptf_events',
            },
        'src_id':{\
            'socket_server_host_ip':"127.0.0.1",#"192.168.1.25",
            'socket_server_port':50030,
            'socket_midway_port':50031,
            'rdb_server_host_ip':"127.0.0.1",#"192.168.1.25",
            'rdb_server_port':3306,
            'rdb_server_user':"pteluser",
            'rdb_server_db':'source_db',
            'primary_table_colname':'src_id',
            'obj_id_reference_tablename':'srcid_lookup',
            },
        'footprint_id':{\
            'socket_server_host_ip':"127.0.0.1",#"192.168.1.45",
            'socket_server_port':50050,
            'socket_midway_port':50051,
            'rdb_server_host_ip':"127.0.0.1",#"192.168.1.45",
            'rdb_server_port':3306,
            'rdb_server_user':"pteluser",
            'rdb_server_db':'object_db',
            'primary_table_colname':'src_id',
            'obj_id_reference_tablename':'footprint_regions',
            },
        'feat_class_srcid_groups':{\
            'socket_server_host_ip':"127.0.0.1",
            'socket_server_port':50060,
            'socket_midway_port':50061,
            'rdb_server_host_ip':"127.0.0.1",
            'rdb_server_port':3306,
            'rdb_server_user':"pteluser",
            'rdb_server_db':'source_test_db', #'source_db',
            #'primary_table_colname':'src_id',
            #'obj_id_reference_tablename':'footprint_regions',
            },
        'socket_server_host_ip':"",
        'socket_server_port':-1,
        'rdb_server_host_ip':"",
        'rdb_server_port':3306,
        'rdb_server_user':"",
        'rdb_server_db':'',
        'primary_table_colname':'',
        'obj_id_reference_tablename':'',
        }


class socket_server:
    """ The socket server class.  One instance needed for each index type.

    NOTE: (passed in) pars{} is expected to be either:
     (1) a dict with server_type keys & config-dict values
     (2) or a dict with all config values, when server_type == ''
    """
    def __init__(self, pars, server_type=''):
        if len(server_type) == 0:
            self.pars = pars # these can come from command line argv
        else:
            self.pars = pars[server_type]
        self.server_type = server_type # used by debugging print statements only
        self.db = MySQLdb.connect(host=self.pars['rdb_server_host_ip'], user=self.pars['rdb_server_user'], db=self.pars['rdb_server_db'], port=self.pars['rdb_server_port'])
        self.cursor = self.db.cursor()


    def get_current_max_obj_id(self):
        """ Query the MySQL database to determine the current max obj_id index.
        NOTE: This assumes there are no other obj_id_sockets.py sessions 
        currently running.
        """
        # First test if the table is new & with no lines:
        select_str = "SELECT count(*) FROM %s" % (\
            self.pars['obj_id_reference_tablename'])
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()
        try:
            n_rows = long(results[0][0])
        except:
            print "ERROR: unable to retrieve count(*):", select_str
            sys.exit()
        if n_rows == 0:
            return 1 # start at obj_id = 1
        # Otherwise we get the max index:
        select_str = "SELECT MAX(%s) FROM %s" % (\
            self.pars['primary_table_colname'], \
            self.pars['obj_id_reference_tablename'])
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()
        try:
            max_obj_id = long(results[0][0])
        except:
            print "ERROR: unable to retrieve max(obj_id):", select_str
            sys.exit()
        return max_obj_id

    
    def listen_loop(self, max_obj_id):
        """ Listening loop which waits for client requests
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(('', int(self.pars['socket_server_port'])))
        except:
            print "!!! EXCEPT obj_id_sockets.py: ", self.server_type, self.pars['socket_server_port'], self.pars['socket_server_host_ip'], self.pars['rdb_server_user'], self.pars['rdb_server_db'], self.pars['obj_id_reference_tablename']
            raise 
        print "Listen Port:", self.pars['socket_server_port']
        cur_obj_id = max_obj_id 
        print "In listening loop..."
        while 1:
            s.listen(1)
            while 1:
                conn, addr = s.accept()
                #print 'Connected by', addr
                rec_str = conn.recv(1024).strip("'")
                if len(rec_str) ==0:
                    continue # skip blank lines, which terminate queries
                num_rows_wanted = long(rec_str)
                out_i_low = cur_obj_id + 1
                cur_obj_id = cur_obj_id + num_rows_wanted 
                out_i_high = cur_obj_id
                print datetime.datetime.now(), num_rows_wanted, out_i_low, out_i_high
                out_str = "%d %d" % (out_i_low, out_i_high)
                conn.send(out_str)
                conn.close()
                time.sleep(0.01)


    def run(self):
        """ Main server runtime routine.
        """
        max_obj_id = self.get_current_max_obj_id()
        print "Initial index:", max_obj_id
        self.listen_loop(max_obj_id)


    def run_feat_class_srcid_groups(self):
        """ Index server which generates groups of source-ids which client
        generates features and science-classifications for.
        """
        ##### TODO: 
        # - bind to socket
        # - while 1 loop
        #   - retrieve 100k srcids using MySQL SELECT
        #   - while len(<available srcid list>) > 0
        #     - listen for socket connection.
        #     - allocate 100 srcids, de-iterate <available srcid list>
        #     - form out string, send to connection client

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', int(self.pars['socket_server_port'])))
        print "Listen Port:", self.pars['socket_server_port']
        #cur_obj_id = max_obj_id 
        print "In listening loop..."
        socket_served_srcid_list = []
        while 1:
            s.listen(1)
            select_srcids_str = "SELECT * from srcid_lookup WHERE (feat_gen_date is NULL) ORDER BY nobjs DESC LIMIT 100000"
            self.cursor.execute(select_srcids_str)
            results = self.cursor.fetchall()
            unfeated_srcid_list = []
            for result in results:
                srcid = result[0]
                if srcid not in socket_served_srcid_list: # TODO: use SET here?
                    unfeated_srcid_list.append(result[0])
            unfeated_srcid_list.reverse() # So large nobj srcids are 1st to pop
            socket_served_srcid_list.extend(unfeated_srcid_list)

            srcid_chunck_size = 2 # 100
            while len(unfeated_srcid_list) > 0:
                if len(unfeated_srcid_list) < srcid_chunck_size:
                    i_range = len(unfeated_srcid_list)
                else:
                    i_range = srcid_chunck_size
                #srcid_list_for_client = []
                out_str = ""
                for i in xrange(i_range):
                    srcid = unfeated_srcid_list.pop()
                    #srcid_list_for_client.append(srcid)
                    out_str += " %s" % (srcid)

                conn, addr = s.accept()
                #print 'Connected by', addr
                rec_str = conn.recv(1024).strip("'")
                if len(rec_str) ==0:
                    continue # skip blank lines, which terminate queries
                #num_rows_wanted = long(rec_str)
                #out_i_low = cur_obj_id + 1
                #cur_obj_id = cur_obj_id + num_rows_wanted 
                #out_i_high = cur_obj_id
                print datetime.datetime.now(), i_range, "srcids sent"
                #out_str = "%d %d" % (out_i_low, out_i_high)
                conn.send(out_str)
                conn.close()
                time.sleep(0.1)




class socket_client:
    """ The socket client object.
    The client sends how many rows it wants indicies for,
    expecting the server to return the start and end indexes allocated to it.

    NOTE: (passed in) pars{} is expected to be either:
     (1) a dict with server_type keys & config-dict values
     (2) or a dict with all config values, when server_type == ''
    """
    def __init__(self, passed_pars, server_type=''):
        if len(server_type) == 0:
            self.pars = passed_pars 
        else:
            self.pars = pars[server_type] # obj_id_sockets.py local defined pars


    def get_index_range_from_server(self, num_rows_wanted):
        """ Connect to the socket server, send num_rows_wanted, 
        and get the obj_id index range.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.pars['socket_server_host_ip'], self.pars['socket_server_port']))
            s.send(str(num_rows_wanted))
            data = s.recv(1024)
            s.close()
            rec_data = repr(data).strip("'").split()
            i_low = long(rec_data[0])
            i_high = long(rec_data[1])
            return (i_low, i_high)
        except:
            print "FAIL: obj_id_sockets.py:", self.pars['socket_server_host_ip'], self.pars['socket_server_port']
            return (-1, -1)


    def get_feat_class_srcid_group(self):
        """ Get a list of srcids which will be used for feature & class
        generation.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.pars['socket_server_host_ip'], self.pars['socket_server_port']))
            s.send('hi')
            data = s.recv(1024) #1024 characters should contain the 100x~8 strs
            s.close()
            str_data = repr(data).strip("'").split()
            srcid_list = []
            for elem in str_data:
                srcid_list.append(int(elem)) # ? Do no anamolous entries occur?
            return srcid_list
        except:
            print "FAIL: obj_id_sockets.py: get_feat_class_srcid_group()"
            return []


if __name__ == '__main__':

    param_tool.add_command_args(pars, 0)
    if pars['server_type'] == 'feat_class_srcid_groups':
        # KLUDGE condition: allows us to still use ARGV passed parameters
        ss = socket_server(pars, server_type='')
        ss.run_feat_class_srcid_groups()
    else:
        ss = socket_server(pars, server_type=pars['server_type'])
        ss.run()

