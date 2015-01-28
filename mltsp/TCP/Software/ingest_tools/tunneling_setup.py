#!/usr/bin/env python 
"""
   v0.1 Tool which sets up ssh tunneling / port forwarding
        for both ipengine/TCP client and TCP server/ipcontroller
        - In the case of ipengine client, local ports are forwarded 
          to lyra, which has ports forwared to transx servers.

   This parses obj_id_sockets to see what the id-socket ports are, and
        uses them for port forwarding to lyra ports.

NOTE: This script is to be run in a *NIX 'screen' to persist.

"""
import os, sys
import obj_id_sockets


class Tunnel_Class:
    """ 1+ methods be inherited.
    """
    def execute_str(self, a_str):
        if not self.pars['only_print_ssh_tunnels']:
            print '#     EXECUTING:'
            os.system(a_str)

        print a_str


    def make_local_tunnel_str(self, port_client_local=0, \
                                    port_midway=0, \
                                    midway_userhost='', \
                                    localhost_name=''):
        ret_str = "ssh -fNc blowfish -L %d:%s:%d %s &" % ( \
                         port_client_local, 
                         localhost_name, 
                         port_midway,
                         midway_userhost)
        return ret_str


    def make_remote_tunnel_str(self, port_server_local=0, \
                                    port_midway=0, \
                                    midway_userhost='', \
                                    localhost_name=''):
        #ssh -R 23671:localhost:3306 pteluser@lyra.berkeley.edu

        ret_str = "ssh -fNc blowfish -R %d:%s:%d %s &" % ( \
                         port_midway, 
                         localhost_name, 
                         port_server_local,
                         midway_userhost)
        return ret_str


    def final(self):
        os.system("ps x | grep ssh | grep blowfish")



class Server_Setup(Tunnel_Class):
    """ This sets up port tunnels for ipcontroller/TCP server.

    """
    def __init__(self, pars={}):
        self.pars = pars


    def setup_mysql_tunnel(self):
        """
        """
        tunnel_str = self.make_remote_tunnel_str( \
              port_server_local=self.pars['mysql_port_server_local'],\
              port_midway=      self.pars['mysql_port_midway'], \
              midway_userhost=  self.pars['mysql_midway_userhost'],\
              localhost_name=   self.pars['mysql_localhost_name'])
        self.execute_str(tunnel_str)


    def setup_ipengine_tunnel(self):
        """
        """
        tunnel_str = self.make_remote_tunnel_str( \
              port_server_local=self.pars['ipengine_port_server_local'],\
              port_midway=      self.pars['ipengine_port_midway'], \
              midway_userhost=  self.pars['ipengine_midway_userhost'],\
              localhost_name=   self.pars['ipengine_localhost_name'])
        self.execute_str(tunnel_str)


    def setup_socket_server_tunnels(self):
        """  Retrieves all socket port instances from obj_id_sockets.py
        and executes a series of ssh port forwards.
        """
        for socket_name,socket_dict in obj_id_sockets.pars.iteritems():
            if not type(socket_dict) == type({}):
                continue

            tunnel_str = self.make_remote_tunnel_str( \
                port_server_local=socket_dict['socket_server_port'],\
                port_midway=      socket_dict['socket_midway_port'], \
                midway_userhost=  self.pars['socket_midway_userhost'],\
                localhost_name=   self.pars['socket_localhost_name'])

            self.execute_str(tunnel_str)


    def main(self):
        """ Main function.
        """
        self.setup_socket_server_tunnels()
        self.setup_mysql_tunnel()
        self.setup_ipengine_tunnel()

        self.final()
        pass


class Client_Setup(Tunnel_Class):
    """ This sets up port tunnels for ipengine/TCP clients.

    """
    def __init__(self, pars={}):
        self.pars = pars


    def setup_mysql_tunnel(self):
        """
        """
        tunnel_str = self.make_local_tunnel_str( \
              port_client_local=self.pars['mysql_port_client_local'],\
              port_midway=      self.pars['mysql_port_midway'], \
              midway_userhost=  self.pars['mysql_midway_userhost'],\
              localhost_name=   self.pars['mysql_localhost_name'])
        self.execute_str(tunnel_str)


    def setup_ipengine_tunnel(self):
        """
        """
        tunnel_str = self.make_local_tunnel_str( \
              port_client_local=self.pars['ipengine_port_client_local'],\
              port_midway=      self.pars['ipengine_port_midway'], \
              midway_userhost=  self.pars['ipengine_midway_userhost'],\
              localhost_name=   self.pars['ipengine_localhost_name'])
        self.execute_str(tunnel_str)


    def setup_socket_server_tunnels(self):
        """  Retrieves all socket port instances from obj_id_sockets.py
        and executes a series of ssh port forwards.
        """
        for socket_name,socket_dict in obj_id_sockets.pars.iteritems():
            if not type(socket_dict) == type({}):
                continue

            tunnel_str = self.make_local_tunnel_str( \
                port_client_local=socket_dict['socket_server_port'],\
                port_midway=      socket_dict['socket_midway_port'], \
                midway_userhost=  self.pars['socket_midway_userhost'],\
                localhost_name=   self.pars['socket_localhost_name'])

            self.execute_str(tunnel_str)
            

    def main(self):
        """ Main function.
        """
        self.setup_socket_server_tunnels()
        self.setup_mysql_tunnel()
        self.setup_ipengine_tunnel()
        self.final()


if __name__ == '__main__':

    pars = { \
        'only_print_ssh_tunnels':False, # True: dont execute, for debugging
        'mysql_port_client_local':23672,
        'mysql_port_server_local':3306,
        'mysql_port_midway':23671,
        'mysql_midway_userhost':'pteluser@lyra.berkeley.edu',
        'mysql_localhost_name':'localhost', #for server case this must reflect bind-address
        
        'ipengine_port_client_local':23610,
        'ipengine_port_server_local':23612,
        'ipengine_port_midway':23611,
        'ipengine_midway_userhost':'pteluser@lyra.berkeley.edu',
        'ipengine_localhost_name':'localhost',

        'socket_localhost_name':'localhost',
        'socket_midway_userhost':'pteluser@lyra.berkeley.edu',
        }

if 0:
    ### ipengine client case

    ClientSetup = Client_Setup(pars)
    ClientSetup.main()

    sys.exit()
if 1:
    ### ipcontroller/TCP server case

    ServerSetup = Server_Setup(pars)
    ServerSetup.main()
