#!/usr/bin/env python
"""
   v0.1 Initial prototype for testing dbxml

PDB: /scisoft/Library/Frameworks/Python.framework/Versions/2.4/lib/python2.4/pdb.py dbxml_test.py
"""
import sys, os
import datetime
import traceback
import dbxml

XML_BASEDIR = '/Network/Servers/boom.cluster.private/Home/pteluser/src/voevent_initial/Bloom_Code_copy'
#os.chdir(XML_BASEDIR)
pars = {\
    'db_fpath':'/tmp/test_db.dbxml', # must be a non-NFS path
    'import_xml_files':[\
        XML_BASEDIR + '/ivo_GCN_SWIFT_61_206773-0_2006-04-24T04:16:37.xml',
        XML_BASEDIR + '/ivo_GCN_SWIFT_65_203974-0_2006-04-05T06:43:47.xml',
        XML_BASEDIR + '/ivo_GCN_SWIFT_65_205373-0_2006-04-15T03:38:22.xml',
        XML_BASEDIR + '/ivo_GCN_SWIFT_67_208169-0_2006-05-02T03:20:29.xml',
        XML_BASEDIR + '/ivo_GCN_SWIFT_73_205851-0_2006-04-18T03:17:03.xml',
        ],
    'xml_replace_dict':{\
        'xmlns=':'xmlns:schemaLocation=', #Needed to find xmlns schema
        },
    'wwwable_replace_dict':{'/': 'S', '_': 'U', '-': 'D',':': 'C', ".": 'd'},
    }


def make_wwwable(messy_str, replace_dict):
    """ Make a messy string www printable.
    """
    for bad_str,new_str in replace_dict.iteritems():
        messy_str = messy_str.replace(bad_str,new_str)
    return messy_str


class DBXML_Container_Instance:
    """ This object class wraps methods for single dbxml container use.

    REQUIRES:
    import dbxml
    """
    def __init__(self, xml_replace_dict={}):
        self.xml_replace_dict = xml_replace_dict
        self.mgr = dbxml.XmlManager()
        self.oldcwd = ''
        self.query_context = self.mgr.createQueryContext()
        self.update_context = self.mgr.createUpdateContext()


    def create(self, db_fpath):
        """ Create new dbxml container
        """ 
        self.db_fpath = db_fpath
        self.dirname = os.path.dirname(self.db_fpath)
        self.fname = os.path.basename(self.db_fpath)
        if os.path.exists(self.db_fpath):
            os.system('rm ' + self.db_fpath)
        self.oldcwd = os.getcwd()
        os.chdir(self.dirname)
        self.container = self.mgr.createContainer(self.fname)

        # # # # # # # # It seems (at the moment) queries are faster without using these indexes:
        # TODO: figure out why.  I think the dbxml elements may all contain strings, and the slowdown is
        # something like the converstion of string to float (during a query).

        self.container.addIndex("", "htm", "node-element-substring-string", self.update_context)
        #self.container.addIndex("", "ra", "node-element-equality-float", self.update_context)
        #self.container.addIndex("", "dec", "node-element-equality-float", self.update_context)
        ### Haven't tried:    self.container.addIndex("", "uid", "unique-node-attribute-presence-string", self.update_context)


    def open(self, db_fpath):
        """ Open existing dbxml container
        """ 
        self.db_fpath = db_fpath
        self.dirname = os.path.dirname(self.db_fpath)
        self.fname = os.path.basename(self.db_fpath)
        self.oldcwd = os.getcwd()
        os.chdir(self.dirname)
        self.container = self.mgr.openContainer(self.fname)


    def conform_xml_str(self, xml_string):
        for bad_str,new_str in self.xml_replace_dict.iteritems():
            xml_string = xml_string.replace(bad_str,new_str)
        return xml_string


    def fill(self, doc_name, xml_string):
        good_xml_string = self.conform_xml_str(xml_string)
        # KLUDGE: If the document exists already, .putDocument() fails.
        #        Here I then delete the existing document & .putDocument()
        #    TODO: It would probably be smarter to discern update/put cases.
        try:
            self.container.putDocument(doc_name, good_xml_string, \
                                                       self.update_context)
        except:
            self.container.deleteDocument(doc_name, self.update_context)
            self.container.putDocument(doc_name, good_xml_string, \
                                                       self.update_context)


    def insert_element(self, xmldoc_id, insert_xpath, element_key, \
                           element_val_str):
        #self.mgr
        #self.container
        #self.update_context
        #self.query_context
        # # # # # # # # # # #
        mymodify = self.mgr.createModify()
        queryexp = self.mgr.prepare(insert_xpath, self.query_context)
        # TODO: there has to be something different than dbxml.XmlModify.Attribute
        #  dbxml.XmlModify.Element
        mymodify.addAppendStep(queryexp, dbxml.XmlModify.Element,\
                                  element_key, element_val_str)
        document = self.container.getDocument(xmldoc_id)
        docvalue = dbxml.XmlValue(document)
        mymodify.execute(docvalue, self.query_context, self.update_context)




    def query(self, query_string, verbose='no'):
        qc = self.mgr.createQueryContext()
        results = self.mgr.query(query_string, qc)
        results.reset()
        #for value in results:
        #    document = value.asDocument()
        #    print document.getName(), "=", value.asString()
        result_list = []
        for value in results:
            result_list.append(value.asString())
        if verbose == 'yes':
            for result in result_list:
                print result
        return result_list


    def close(self):
        self.container.close()
        os.chdir(self.oldcwd)


if __name__ == '__main__':
    os.chdir(XML_BASEDIR) # I moved this from above, to here.  I think it'll work

    out_dbxml_fpath = '/tmp/ivo_test.dbxml'
    dbxml_cont = DBXML_Container_Instance(\
        xml_replace_dict=pars['xml_replace_dict'])
    # Create & fill dbxml:
    dbxml_cont.create(out_dbxml_fpath)
    import amara # just do this in __main__ so 'import dbxml_test' won't load

    for xml_fpath in pars['import_xml_files']:
        ao = amara.parse(xml_fpath) # = open(xml_fpath).read()
        xml_str = ao.xml()
        try:
            voevent_id_raw = str(ao.VOEvent.xml_properties[u'id'])
        except:
            voevent_id_raw = str(xml_fpath) #OR some kind of somewhat useful id
        voevent_id = voevent_id_raw # make_wwwable(voevent_id_raw, pars['wwwable_replace_dict'])
        dbxml_cont.fill(voevent_id, xml_str)
    dbxml_cont.close()
    # Query dbxml:
    #query_str = "collection('ivo_test.dbxml')/VOEvent/Citations"
    query_str = """<html><body><ul>
      {
        for $voe in
          (collection("ivo_test.dbxml")/VOEvent[Citations])
        return
          <li>{$voe/@id}
          <li>{$voe/Citations}</li></li>
      }
    </ul></body></html>"""
    dbxml_cont.open(out_dbxml_fpath)
    result_list = dbxml_cont.query(query_str, verbose='yes')
    # URL: http://lyra.berkeley.edu/~jbloom/dstarr/test/test.html
    open('/Volumes/BR1/Graham/Bloom-store/Josh/public_html/dstarr/test/test.html',\
         'w+').write(result_list[0])
    dbxml_cont.close()

    sys.exit()

          


    ##########
    ### Simple dbxml create & query example:
    xml_str = """<phonebook>
    <name>
        <first>Tom</first>
        <last>Jones</last>
    </name>
    <phone type="home">420-203-2032</phone>
</phonebook>"""
    query_str = "collection('test.dbxml')/phonebook/name"
    dbxml_cont = DBXML_Container_Instance(xml_replace_dict=pars['xml_replace_dict'])
    dbxml_cont.create('/tmp/test.dbxml')
    dbxml_cont.fill('blah_docname', xml_str)
    dbxml_cont.close()
    dbxml_cont.open('/tmp/test.dbxml')
    dbxml_cont.query(query_str)
    dbxml_cont.close()
    ###########

# We eventually want to set up a query system/webpage which allows:
#   - a combination of different filters/queries for returned XML objects
#   - combine multple queries as a single, mondo one.
#   - repeat queries on database updates.
#   - returned results should be shaped into various usable forms.
#      -html, rss, pairitel-next.obs
#   - Use object-type templates when constructing queries, so various objtypes
#     can be modularly stuck in.
#   - ? Use query results (objects like blah1, blah2), to form new queries
#   - some query elements may have parts which try to retrieve/process data
#        to complete the query.
    query_str = """<html><body><ul>
      {
        for $citation in
          (collection("ivo_test.dbxml")/VOEvent/Citations)
        return
          <li>{$citation}</li>
      }
    </ul></body></html>"""
