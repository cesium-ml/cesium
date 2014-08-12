#!/usr/bin/env python 

"""
TODO: parse the tables found in ~/scratch/simbad_classes_ptf_sources/*.tab
 - create, have a table which contains this information, including the (sn,09), (agn,10).... columes
 - also have a col for the tcp srcid.
 - also have a column that the tcp has completely ingested that source


TODO: then iterate over theis table where not ingested yet,
   - do the ingesting (via ipython on tranx) for each ptf source
        - using (ra,dec)

Do as in: (but in parallel):

snclassifier_testing_wrapper.py

"""
import os, sys
import MySQLdb
import copy

sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
              'Software/feature_extract/Code')) 
import db_importer


from xml.etree import ElementTree



def invoke_pdb(type, value, tb):                                                   
    """ Cool feature: on crash, the debugger is invoked in the last 
    state of the program.  To Use, call in __main__: sys.excepthook =
    invoke_pdb                                                                     
    """                                                                            
    import traceback, pdb
    traceback.print_exception(type, value, tb)
    print
    pdb.pm() 


class Simbad_Data:
    """ Given some of Josh's simbad / ptf *.tab \t deliminated files,
    we INSERT and access this data within this object.
    """
    def __init__(self, pars):
        self.pars = pars

        self.db = MySQLdb.connect(host=self.pars['mysql_hostname'], \
                                  user=self.pars['mysql_user'], \
                                  db=self.pars['mysql_database'], \
                                  port=self.pars['mysql_port'])
        self.cursor = self.db.cursor()


    def create_tables(self):
        """
        """
        create_table_str = """CREATE TABLE simbad_ptf
       (ptf_shortname VARCHAR(8),
        src_id INT,
        init_lbl_id BIGINT,
        ra DOUBLE,
        decl DOUBLE,
        tab_filename VARCHAR(20),
        simbad_otype VARCHAR(25),
        simbad_main_id VARCHAR(100),
        ingest_dtime DATETIME,
        PRIMARY KEY (ptf_shortname),
        INDEX(src_id))"""
        self.cursor.execute(create_table_str)


    def fill_tables(self):
        """ Fill the tables up using given table filepaths
        """
        duplicate_list = [] # for debugging
        ptf_id_list = []
        insert_list = ['INSERT INTO simbad_ptf (ptf_shortname, init_lbl_id, ra, decl, tab_filename, simbad_otype, simbad_main_id) VALUES ']
        for filename in self.pars['tab_filenames']:
            fpath = "%s/%s" % (self.pars['tab_dirpath'],
                               filename)
            mondo_mac_str = open(fpath).readlines()
            lines = mondo_mac_str[0].split('\r')
            for line in lines:
                line_list = line.split('\t')
                if (line_list[0] == "PTFname") or (len(line.strip()) == 0) or (line_list[0] == "None"):
                    continue
                PTFname              = line_list[0]
                initial_lbl_cand_id  = line_list[1]
                ra                   = line_list[2]
                dec                  = line_list[3]
                tab_filename = filename
                
                otype                = line_list[4]
                main_id              = line_list[5]

                elem_str = '("%s", %s, %s, %s, "%s", "%s", "%s"), ' % (PTFname,
                                                                     initial_lbl_cand_id,
                                                                     ra,
                                                                     dec,
                                                                     tab_filename,
                                                                     otype,
                                                                     main_id)
                if PTFname in ptf_id_list:
                    duplicate_list.append((PTFname,
                                           initial_lbl_cand_id,
                                           ra,
                                           dec,
                                           tab_filename,
                                           otype,
                                           main_id))
                    #print 'DUPLICATE ptf_id:', elem_str
                    continue # we skip inserting this version of the ptf_id.
                ptf_id_list.append(PTFname)
                insert_list.append(elem_str)
        insert_str = ''.join(insert_list)[:-2]
        self.cursor.execute(insert_str)

        for (PTFname,
             initial_lbl_cand_id,
             ra,
             dec,
             tab_filename,
             otype,
             main_id) in duplicate_list:
            select_str = 'SELECT ptf_shortname, init_lbl_id, ra, decl, tab_filename, simbad_otype, simbad_main_id FROM simbad_ptf WHERE ptf_shortname="%s"' % (PTFname)
            self.cursor.execute(select_str)
            rows = self.cursor.fetchall()
            for row in rows:
                print (PTFname,
                       initial_lbl_cand_id,
                       ra,
                       dec,
                       tab_filename,
                       otype,
                       main_id), '\n', row, '\n\n'

    def get_noningested_ptfids(self):
        """ query the RDB, return a list of ids (and related information).
        """
        out_list = [] # will contain dicts
        select_str = "SELECT ptf_shortname, init_lbl_id, ra, decl FROM simbad_ptf WHERE ingest_dtime is NULL"
        self.cursor.execute(select_str)
        rows = self.cursor.fetchall()
        for row in rows:
            (ptf_shortname, init_lbl_id, ra, decl) = row
            out_list.append({'ptf_shortname':ptf_shortname,
                             'init_lbl_id':init_lbl_id,
                             'ra':ra,
                             'decl':decl})
        return out_list


    def update_table(self, short_name=None, tcp_srcid=None):
        """ Update the exting row in the database with the tcpsrcid, and a date.
        """

        update_str = 'UPDATE simbad_ptf SET src_id=%d, ingest_dtime=NOW() WHERE ptf_shortname="%s" ' % (\
                             tcp_srcid, short_name)
        self.cursor.execute(update_str)
        
        

class Associate_Simbad_PTF_Sources:
    """  Go through un-ingested entries in table and retrieve from LBL,
    find associated TCP source, and update simbad_ptf TABLE.

    NOTE: much of this is adapted from snclassifier_testing_wrapper.py
          which is adapted from get_classifications_for_caltechid.py..__main__()

    """

    def __init__(self, pars, SimbadData=None):
        self.pars = pars
        self.SimbadData = SimbadData


    def initialize_classes(self):
        """ Load other singleton classes.
        NOTE: much of this is adapted from snclassifier_testing_wrapper.py
              which is adapted from get_classifications_for_caltechid.py..__main__()
        """
        import get_classifications_for_caltechid
        import ingest_tools
        import ptf_master

        self.DiffObjSourcePopulator = ptf_master.Diff_Obj_Source_Populator(use_postgre_ptf=True)
        self.PTFPostgreServer = ptf_master.PTF_Postgre_Server(pars=ingest_tools.pars, \
                                                         rdbt=self.DiffObjSourcePopulator.rdbt)
        self.Get_Classifications_For_Ptfid = get_classifications_for_caltechid.GetClassificationsForPtfid(rdbt=self.DiffObjSourcePopulator.rdbt, PTFPostgreServer=self.PTFPostgreServer, DiffObjSourcePopulator=self.DiffObjSourcePopulator)
        self.Caltech_DB = get_classifications_for_caltechid.CaltechDB()


    def associate_ptf_sources(self, ptfid_tup_list):
        """ retrieve  and associated ptf ids to tcp sources (create them if needed).
        Retrieve extra ptf epochs from LBL if available.
        """
        out_dict = {}
        for ptf_dict in ptfid_tup_list:
            short_name = ptf_dict['ptf_shortname']

            # I think I might want to get the next bit from lbl & company
            ptf_cand_dict = {'srcid':None, #results[0][2],
                             'id':ptf_dict['init_lbl_id'], #results[0][0],
                             'shortname':ptf_dict['ptf_shortname'],
                             'ra':ptf_dict['ra'],
                             'dec':ptf_dict['decl'],
                             'mag':'',
                             'type':'',
                             'scanner':'',
                             'type2':'',
                             'class':'',
                             'isspectra':'',
                             'rundate':''}



            #matching_source_dict = get_classifications_for_caltechid.table_insert_ptf_cand(DiffObjSourcePopulator, PTFPostgreServer, Get_Classifications_For_Ptfid, Caltech_DB, ptf_cand_shortname=short_name)
            #ptf_cand_dict = Caltech_DB.get_ptf_candid_info___non_caltech_db_hack(cand_shortname=short_name)
            #TODO: check if srcid.xml composed from ptf_cand_dict{srcid} is in the expected directory.  If so, just pass that xml-fpath as xml_handle.  Otherwise, generate the xml string (and write to file) and pass that.
            xml_fpath = "%s/%s.xml" % (self.pars['out_xmls_dirpath'], short_name)
            if os.path.exists(xml_fpath):
                print "Found on disk:", xml_fpath 
            else:
                # NOTE: Since the Caltech database is currently down and we know we've ingested these ptf-ids already into our local database...
                #"""
                (ingested_srcids, ingested_src_xmltuple_dict) = self.Get_Classifications_For_Ptfid.populate_TCP_sources_for_ptf_radec( \
                                                       ra=ptf_cand_dict['ra'], \
                                                       dec=ptf_cand_dict['dec'], \
                                                       ptf_cand_dict=ptf_cand_dict, \
                                                       do_get_classifications=False) # 20100127: dstarr added the last False term due to Caltech's database being down, and our lack of interest in general classifications right now.

                matching_source_dict = self.Get_Classifications_For_Ptfid.get_closest_matching_tcp_source( \
                                                         ptf_cand_dict, ingested_srcids)
                #pprint.pprint(matching_source_dict)
                #"""
                #import pdb; pdb.set_trace()
                # # # # TODO: this will not work right now since we dont know the srcid
                fp = open(xml_fpath, 'w')
                fp.write(ingested_src_xmltuple_dict[matching_source_dict['src_id']])
                fp.close()
                print "Wrote on disk:", xml_fpath 
                #pprint.pprint(ptf_cand_dict)
                self.SimbadData.update_table(short_name=short_name, tcp_srcid=matching_source_dict['src_id'])


            #sn_classifier_final_results = apply_sn_classifier(xml_fpath)
            #pprint.pprint(sn_classifier_final_results)

            #out_dict[short_name] = copy.deepcopy(matching_source_dict)



    def fill_association_table(self):

        ptfid_tup_list = self.SimbadData.get_noningested_ptfids()

        self.initialize_classes()

        
        self.associate_ptf_sources(ptfid_tup_list)



class Generate_Summary_Webpage:
    """ This Class will:
     - query simbad_ptf table
     - find all old vosource.xml which were generated using older db_importer.py methods
     - run simpletimeseries generating algorithms, saving the simpletimeseries .xmls
     - construct a html which references these xmls, assumming local, and assuming located on http://lyra/~pteluser/
     - this html has:
        is order-able.
        - simbad science class column
        - ptf-id
        - tcp src_id
        - simbad id (some hyperlink taken from tcp_...php)?
        - ra, decl
        - first LBL candidate id        
        - has hyperlinks to both old & simpletimeseries files.
    """
    def __init__(self, pars, SimbadData=None):
        self.pars = pars
        self.SimbadData = SimbadData


    def get_simbad_ptf_table_data(self):
        """
        """
        out_dict = {} # out_dict[<simbad_otype>][<ptf_shortname>]

        colname_list = ['ptf_shortname', 'src_id', 'init_lbl_id', 'ra', 'decl', 'tab_filename', 'simbad_otype', 'simbad_main_id']
        select_str = "SELECT %s FROM source_test_db.simbad_ptf" % (', '.join(colname_list))
        self.SimbadData.cursor.execute(select_str)
        rows = self.SimbadData.cursor.fetchall()
        for row in rows:
            (ptf_shortname, src_id, init_lbl_id, ra, decl, tab_filename, simbad_otype, simbad_main_id) = row
            if not out_dict.has_key(simbad_otype):
                out_dict[simbad_otype] = {}
            out_dict[simbad_otype][ptf_shortname] = {'ptf_shortname':ptf_shortname,
                                                     'src_id':src_id,
                                                     'init_lbl_id':init_lbl_id,
                                                     'ra':ra,
                                                     'decl':decl,
                                                     'tab_filename':tab_filename,
                                                     'simbad_otype':simbad_otype,
                                                     'simbad_main_id':simbad_main_id}
        return out_dict
            


    def generate_simptimeseries_xmls(self, simbad_ptf_dict={}):
        """ Using the entries in given dict, run db_importer.py stuff and generate new .xmls in some dir.
        """
        for simbad_otype, sim_dict in simbad_ptf_dict.iteritems():
            for ptf_shortname, ptf_dict in sim_dict.iteritems():
                orig_fpath = os.path.expandvars("%s/%s.xml" % (self.pars['out_xmls_dirpath'], ptf_shortname))
                s = db_importer.Source(xml_handle=orig_fpath)
                out_str = s.source_dict_to_xml__simptimeseries(s.x_sdict)
                temp_xml_fpath = "%s/simpt_%s.xml" % (self.pars['out_xmls_simpt_dirpath'], ptf_shortname)
                fp = open(temp_xml_fpath, 'w')
                fp.write(out_str)
                fp.close()


    def construct_html_with_old_new_xml_links(self, simbad_ptf_dict={}):
        """ Construct, write an html file which summarizes all the old and new simpletimeseries xmls.
          - consider that this will be residing on lyra in the ~pteluser/public_html/ directory.
              - so that .xsl , .css renders correctly for the simpletimeseries xmls
        """
        html = ElementTree.Element("HTML")
        body = ElementTree.SubElement(html, "BODY")
        table = ElementTree.SubElement(body, "TABLE", BORDER="1", CELLPADDING="1", CELLSPACING="1")

        # First row is the table header:
        tr = ElementTree.SubElement(table, "TR")
        ElementTree.SubElement(tr, "TD").text = "PTF shortname"
        ElementTree.SubElement(tr, "TD").text = "simbad Class otype"
        ElementTree.SubElement(tr, "TD").text = "TCP src_id"
        ElementTree.SubElement(tr, "TD").text = "Initial LBL Candidate ID"
        ElementTree.SubElement(tr, "TD").text = "VOSource XML"
        ElementTree.SubElement(tr, "TD").text = "SimpleTimeSeries XML"
        ElementTree.SubElement(tr, "TD").text = "RA"
        ElementTree.SubElement(tr, "TD").text = "Decl"

        for simbad_otype, sim_dict in simbad_ptf_dict.iteritems():
            for ptf_shortname, ptf_dict in sim_dict.iteritems():
                orig_fpath = os.path.expandvars("simbad_ptf_old_vsrc_xmls/%s.xml" % (ptf_shortname))
                simpts_fpath = "simbad_ptf_simpletimeseries_xmls/simpt_%s.xml" % (ptf_shortname)
                tr = ElementTree.SubElement(table, "TR")
                ElementTree.SubElement(tr, "TD").text = ptf_shortname
                ElementTree.SubElement(tr, "TD").text = simbad_otype
                ElementTree.SubElement(tr, "TD").text = str(ptf_dict['src_id'])
                ElementTree.SubElement(tr, "TD").text = str(ptf_dict['init_lbl_id'])
                vsrc_col = ElementTree.SubElement(tr, "TD")
                vsrc_a = ElementTree.SubElement(vsrc_col, "A", href="http://lyra.berkeley.edu/~pteluser/%s" % (orig_fpath))
                vsrc_a.text = ptf_shortname + ".xml"

                sts_col = ElementTree.SubElement(tr, "TD")
                sts_a = ElementTree.SubElement(sts_col, "A", href="http://lyra.berkeley.edu/~pteluser/%s" % (simpts_fpath))
                sts_a.text = "simpt_" + ptf_shortname + ".xml"

                ElementTree.SubElement(tr, "TD").text = str(ptf_dict['ra'])
                ElementTree.SubElement(tr, "TD").text = str(ptf_dict['decl'])
                
        db_importer.add_pretty_indents_to_elemtree(html, 0)
	tree = ElementTree.ElementTree(html)
        fp = open(self.pars['out_summary_html_fpath'], 'w')
	tree.write(fp, encoding="UTF-8")
        fp.close()





    def main(self):
        """ This Class will:
         #- query simbad_ptf table
         - find all old vosource.xml which were generated using older db_importer.py methods
         - run simpletimeseries generating algorithms, saving the simpletimeseries .xmls
         - construct a html which references these xmls, assumming local, and assuming located on http://lyra/~pteluser/
         - this html has:
            is order-able.
            - simbad science class column
            - ptf-id
            - tcp src_id
            - simbad id (some hyperlink taken from tcp_...php)?
            - ra, decl
            - first LBL candidate id        
            - has hyperlinks to both old & simpletimeseries files.
        """
        simbad_ptf_dict = self.get_simbad_ptf_table_data()
        #self.generate_simptimeseries_xmls(simbad_ptf_dict=simbad_ptf_dict)     # Run Once.
        self.construct_html_with_old_new_xml_links(simbad_ptf_dict=simbad_ptf_dict)

                 


if __name__ == '__main__':

    pars = {'mysql_user':"pteluser", 
            'mysql_hostname':"192.168.1.25", 
            'mysql_database':'source_test_db', 
            'mysql_port':3306,
            'tab_dirpath':'/home/pteluser/scratch/simbad_classes_ptf_sources',
            'tab_filenames':['ptf_agn09.tab',
                             'ptf_agn10.tab',
                             'ptf_cv09.tab',
                             'ptf_cv10.tab',
                             'ptf_periodic09.tab',
                             'ptf_periodic10.tab',
                             'ptf_sn09.tab',
                             'ptf_sn10.tab'],
            'out_xmls_dirpath':'/home/pteluser/scratch/simbad_classes_ptf_sources/out_xmls',
            'out_xmls_simpt_dirpath':'/home/pteluser/scratch/simbad_classes_ptf_sources/out_xmls_simpt',
            'out_summary_html_fpath':'/home/pteluser/scratch/simbad_classes_ptf_sources/simbad_ptf_summary.html',
            }

    sys.excepthook = invoke_pdb # for debugging/error catching.        

    SimbadData = Simbad_Data(pars)
    #SimbadData.create_tables()
    #SimbadData.fill_tables()

    AssociateSimbadPTFSources = Associate_Simbad_PTF_Sources(pars, SimbadData=SimbadData)
    #AssociateSimbadPTFSources.fill_association_table()       # Do this once

    GenerateSummaryWebpage = Generate_Summary_Webpage(pars, SimbadData=SimbadData)

    GenerateSummaryWebpage.main()




    # TODO: then generate classifications by iterating over these with NULL datetime (and first periodic)
    #     - remember to update the datetime and the associated src_id
    #     - this will be in a seperate class, like snclassifier_testing_wrapper.py
