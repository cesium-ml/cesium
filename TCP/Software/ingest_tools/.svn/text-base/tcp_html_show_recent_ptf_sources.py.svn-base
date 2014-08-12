#!/usr/bin/env python

######!/Library/Frameworks/Python.framework/Versions/Current/bin/python
"""

"""
import sys, os
# 566  export PGPASSWORD="classify"
#  567  psql -d ptfcands -h navtara.caltech.edu -U tcp
#  568  echo "\dt" | psql -d ptfcands -h navtara.caltech.edu -U tcp

class ShowRecentPtfSources:
    """ Class which is called by XMLRpcServer and which queries LBL
    PostgreSQl server.
    """
    def __init__(self):
        pass


    def get_period_fold(self, source_id):
        """ Calls Justin code which generates period folding array for a src_id
        # to be called by PHP code, and generates then prints a javascript JSON like array.
        """
        # # # # #
        # #old_stdout = sys.stdout
        # #sys.stdout = open('/dev/null','w')
        ######print """[{"label":"Period Fold", "color":"#36477b", "data":[[1,1],[2,4],[3,9],[4,16]]}]"""
        sys.path.append(os.path.expandvars("$TCP_DIR") + '/Algorithms/fitcurve')
        try:
            import lightcurve
        except:
            print "!!! Probably running tcp_html_show_recent_ptf_sources.py get_period_fold   in TESTING mode."

        GetPeriodFoldForWeb = lightcurve.GetPeriodFoldForWeb()
        json_out_string = GetPeriodFoldForWeb.main(source_id)

        # #sys.stdout.close()
        # #sys.stdout = old_stdout
        return json_out_string

    def get_html_data(self, source_id):
        old_stdout = sys.stdout
        sys.stdout = open('/dev/null','w')
        sys.path.append(os.path.expandvars("$TCP_DIR") + '/Algorithms/fitcurve')
        import lightcurve
        GetPeriodFoldForWeb = lightcurve.GetPeriodFoldForWeb()
        html_str = GetPeriodFoldForWeb.html_table(source_id)
        sys.stdout.close()
        sys.stdout = old_stdout
        return html_str


    def generate_imgsrc_for_id(self, candidate_id):
        """
        TODO: want to have a function which is given an LBL candidate.id
         - and generates an <img src= ... > html string which it returns.
         - this requires querying LBL PGSQL db for field id, chip id, x, y
             for the candidate.id
         - This is called via some lyra php -> py (xmlrpc client)
        """
        import psycopg2
        pg_conn = psycopg2.connect("dbname='subptf' user='dstarr' host='sgn02.nersc.gov' password='*2ta77' port=6540");
        pg_cursor = pg_conn.cursor()
        pg_conn.set_isolation_level(2)
        pg_cursor = pg_conn.cursor()
        ###
        #select_str = """SELECT subtraction.id, proc_image.id, candidate.x_sub, candidate.y_sub, subtraction.ptffield, subtraction.ccdid, proc_image.date_obs
        select_str = """SELECT candidate.x_sub, candidate.y_sub, subtraction.ptffield, subtraction.ccdid, proc_image.date_obs
        FROM candidate
        JOIN subtraction ON (subtraction.id = candidate.sub_id)
        JOIN proc_image ON (proc_image.id = subtraction.proc_image_id)
        WHERE candidate.id=%d
        """% (candidate_id)
        pg_cursor.execute(select_str)
        print select_str
        rdb_rows = pg_cursor.fetchall()
        pg_cursor.close()
        pg_conn.rollback()
        if len(rdb_rows) > 0:
            x_sub = rdb_rows[0][0]
            y_sub = rdb_rows[0][1]
            ptffield = rdb_rows[0][2]
            ccdid = rdb_rows[0][3]
            date_obs = rdb_rows[0][4]
            date_yyyymmdd = "%d%0.2d%0.2d" % (date_obs.year, date_obs.month, date_obs.day)
            url_prefix = "http://portal.nersc.gov/project/deepsky/ptfvet/thumb.cgi?type="
            url_suffix = "&mode=cand&grow=2&width=100&rundate=%s&visit=8&field=%d&chip=%d&cross=yes&x=%lf&y=%lf" % ( \
                  date_yyyymmdd, ptffield, ccdid, x_sub, y_sub)
            for url_type in ['new', 'ref', 'sub']:
                url_str = url_prefix + url_type + url_suffix
                print url_str
        print 'yo'

        """
        http://portal.nersc.gov/project/deepsky/ptfvet/scan.cgi?candid=352403
<td width="200" height="200" align="center">
<img src="thumb.cgi?type=new&mode=cand&grow=2&width=100&rundate=20090620&visit=1&field=4151&chip=8&cross=yes&x=1215.080000&y=638.659000"/>
</td>
<td width="200" height="200" align="center">
<img src="thumb.cgi?type=ref&mode=cand&grow=2&width=100&rundate=20090620&visit=1&field=4151&chip=8&cross=yes&x=1215.080000&y=638.659000"/>
</td>
<td width="200" height="200" align="center">
<img src="thumb.cgi?type=sub&mode=cand&grow=2&width=100&rundate=20090620&visit=1&field=4151&chip=8&cross=yes&x=1215.080000&y=638.659000"/>
</td>


http://portal.nersc.gov/project/deepsky/ptfvet/thumb.cgi?type=new&mode=cand&grow=2&width=100&rundate=2009417&visit=8&field=100056&chip=11&cross=yes&x=1736.230000&y=1544.000000
http://portal.nersc.gov/project/deepsky/ptfvet/thumb.cgi?type=ref&mode=cand&grow=2&width=100&rundate=2009417&visit=8&field=100056&chip=11&cross=yes&x=1736.230000&y=1544.000000
http://portal.nersc.gov/project/deepsky/ptfvet/thumb.cgi?type=sub&mode=cand&grow=2&width=100&rundate=2009417&visit=8&field=100056&chip=11&cross=yes&x=1736.230000&y=1544.000000

        """
        

    def get_it(self):
        """ Testing method
        """
        try:
            import psycopg2
        except:
            pass
        conn = psycopg2.connect("dbname='ptfcands' user='tcp' host='navtara.caltech.edu' password='classify'");
        pg_cursor = conn.cursor()

        column_list = ['shortname', 'ra', 'dec', 'mag', 'type2', 'class', 'isspectra', 'rundate']
        column_str = ', '.join(column_list)
        #column_list = column_str.split(' ')
        select_str = "SELECT %s FROM saved_cands WHERE shortname > '' AND rundate > '20090101' ORDER BY rundate DESC LIMIT 20" % (column_str)

        pg_cursor.execute(select_str)
        out_str = '<TABLE BORDER CELLPADDING=1 CELLSPACING=1>'
        out_str += '<TR>'
        for elem in column_list:
            out_str += "<TD><FONT SIZE=\"2\">%s</FONT</TD>" % (elem)
        out_str += '</TR>'
        for row in pg_cursor.fetchall():
            out_str += '<TR>'
            out_str += "<TD><input type=\"button\" onClick=\"javascript:query_using_ptf_ra_dec(%lf, %lf);\"  value=\"%s\"/></TD>" % (row[1], row[2], str(row[0])) 
            for elem in row[1:]:
               out_str += "<TD><FONT SIZE=\"2\">%s</FONT></TD>" % (str(elem)) 
            out_str += '</TR>'
        out_str += '</TABLE>'

        return out_str



if __name__ == '__main__':
    
    pars = { \
        'xmlrpc_server_ip':'192.168.1.25',
        'xmlrpc_server_port':45361, #justin on tranx uses: 45333, dstarr old uses: 45361
        }

    if sys.argv[1] == 'get_period_fold':
        src_id = int(sys.argv[2])
        # # # # # # #
        # # # # # # #
        # # # # # # #
        if True:
            ### Testing only:
            Show_Recent_Ptf_Sources = ShowRecentPtfSources()
            json_out_string = Show_Recent_Ptf_Sources.get_period_fold(src_id)
            print json_out_string
        else:
            # Normal mode:
            import xmlrpclib
            server = xmlrpclib.ServerProxy("http://%s:%d" % ( \
                                           pars['xmlrpc_server_ip'], \
                                           pars['xmlrpc_server_port']))
            #json_out_string = server.get_period_fold(src_id)
            try:
                json_out_string = server.get_period_fold(src_id)
            except:
                json_out_string = """[{"label":"No Fit Found", "color":"#36477b", "data":[[0,0]]}]"""
            print json_out_string
        

    elif sys.argv[1] == 'gen_id_imgsrc':
        # obsolete / not implemented:
        candidate_id = int(sys.argv[2])
        if False:
            ### Testing only:
            Show_Recent_Ptf_Sources = ShowRecentPtfSources()
            Show_Recent_Ptf_Sources.generate_imgsrc_for_id(candidate_id)
        else:
            # Normal mode:
            import xmlrpclib
            server = xmlrpclib.ServerProxy("http://%s:%d" % ( \
                                           pars['xmlrpc_server_ip'], \
                                           pars['xmlrpc_server_port']))
            print server.generate_imgsrc_for_id(candidate_id)

    elif sys.argv[1] == 'client':
        import xmlrpclib
        server = xmlrpclib.ServerProxy("http://%s:%d" % ( \
                                       pars['xmlrpc_server_ip'], \
                                       pars['xmlrpc_server_port']))
        print server.get_it()

    elif sys.argv[1] == 'server':
        print 'XMLRPC server mode...'
        import SimpleXMLRPCServer
        server = SimpleXMLRPCServer.SimpleXMLRPCServer(\
                              (pars['xmlrpc_server_ip'], \
                               pars['xmlrpc_server_port']))
        server.register_instance(ShowRecentPtfSources())
        server.register_multicall_functions()
        server.register_introspection_functions()
        server.serve_forever()

    elif sys.argv[1] == 'get_table_data':
        sys.stderr = open('/dev/null','w')
        src_id = int(sys.argv[2])
        import xmlrpclib
        server = xmlrpclib.ServerProxy("http://%s:%d" % ( \
                                        pars['xmlrpc_server_ip'], \
                                        pars['xmlrpc_server_port']))

        #for testing:
        #show = ShowRecentPtfSources()
        #html_table_str = show.get_html_data(src_id)


        try:
            #html_table_str = server.get_html_data(src_id)
            show = ShowRecentPtfSources()
            html_table_str = show.get_html_data(src_id)
        except:
            html_table_str = "Check lightcurve.py"
            
        print html_table_str
