#!/usr/bin/env python
"""
An example client / server of xmlrpc transport with python.

You could have the server using one version of python and the client using another version of python (within reason : maybe not with Python 1.0 and Python3000...).

To use in it's current simple form:
1) start server by having "if 1:" under __main__

2) start client by having "if 0:" under __main__

"""
import os, sys

server_hostname = "192.168.1.25"
server_port = 23459

class Some_Class_We_Want_Remotely_Accessible:
    """ Awesome Class which does awesome stuff.
    """
    def __init__(self, important_parameter=123):
        self.important_parameter = important_parameter

    def some_method(self, passed_value):
        print 'important_parameter=', self.important_parameter
        print 'passed_value=', passed_value


if __name__ == '__main__':

    if 1:
        # server:
        import SimpleXMLRPCServer
        server = SimpleXMLRPCServer.SimpleXMLRPCServer( \
                                                    (server_hostname, server_port), \
                                                    allow_none=True)
        server.register_instance( \
                       Some_Class_We_Want_Remotely_Accessible(important_parameter=1))
        server.register_multicall_functions()
        server.register_introspection_functions()
        print 'XMLRPC Server is starting at:', server_hostname, server_port
        server.serve_forever()

    else:
        # client:
        import xmlrpclib
        server = xmlrpclib.ServerProxy("http://%s:%d" % \
                                                      (server_hostname, server_port))
        try:
            print server.system.listMethods()
        except:
            print 'EXCEPT at server.system.listMethods() : Probably XMLRPC server is down!'
            sys.exit()
        print server.system.methodHelp("some_method")
        #src_list = server.get_sources_for_radec(ra, dec, box_range)
        src_list = server.some_method('hello')
