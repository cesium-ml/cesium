#!/usr/bin/env python
# web_feat_extract_wrapper.py
#   v0.1 initial version

import sys, os
import xmlrpclib

if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit()
    vosource_url = sys.argv[1]
    srcid = sys.argv[2]
    if "http" not in vosource_url:
        sys.exit()

    server = xmlrpclib.ServerProxy("http://192.168.1.66:8000")
    #print "Input:", srcid, vosource_url
    try:
	out_vals = server.get_sources_using_xml_file_with_feature_extraction(\
                                                          srcid, vosource_url)
    	#print "<br>Output:<br>"
   	#for elem in out_vals:
    	#    print "%s<br>" % (str(elem))

    	print """
<TABLE BORDER CELLPADDING=0 CELLSPACING=2>
<tr>
  <td><a href="%s"> <IMG SRC="%s" WIDTH=950 HEIGHT=700></a>  </td>
</tr>
</table>
""" % (str(out_vals[1]), str(out_vals[1]))
    except:
	print "EXCEPT: in web_feat_extract_wrapper.py", srcid, vosource_url