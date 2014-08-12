#!/usr/bin/env python
""" Determine SIMBAD science classifications, if available for the best matching SIMBAD source.

- Using SIMBAD VOTABLES to get classes
   - reference  kepler_find_simbad_public_sources.py when parsing votables
- Using distance cut when querying simbad votable.
     - distance cuts come from nomad / color distance code:  get_colors_for_tutor_sources.py
"""
import os, sys
import cPickle
import MySQLdb

try:
    from xml.etree import cElementTree as ElementTree # this is a nicer implementation
except:
    # This is caught in M45's python 2.4.3 distro where the elementtree module was installed instead
    from elementtree import ElementTree

sys.path.append(os.path.abspath(os.environ.get("TCP_DIR","") + \
              '/Software/feature_extract/Code/extractors')) # this for xmldict load only
try:
    import xmldict
except:
    pass

class TCPDb():
    def connect_to_db(self):
        self.db = MySQLdb.connect(host=self.pars['mysql_hostname'],
                                  user=self.pars['mysql_username'],
                                  db=self.pars['mysql_database'],
                                  port=self.pars['mysql_port'])
        self.cursor = self.db.cursor()

class Determine_Simbad_Class(TCPDb):
    """ Determine SIMBAD science classifications, if available for the best matching SIMBAD source.
    """
    def __init__(self, pars={}):
        self.pars=pars
        try:
            self.connect_to_db()
        except:
            pass

    def make_nomad_simbad_source_match_dict(self):
        """
        """

        fp = open(self.pars['source_nomad_pkl_fpath'],'rb')
        nomad_sources = cPickle.load(fp)
        fp.close()

        srcid_class_match_dict = {}
        for src_id, src_dict in nomad_sources.iteritems():
            
            votable_fpath = "%s/%d.votable" % (self.pars['simbad_votable_dirpath'], src_id)
            
            votable_str = open(votable_fpath).read()
            if len(votable_str) < 310:
                #print "NO SIMBAD match:", src_id
                continue

            elemtree = ElementTree.fromstring(votable_str)
            xmld_data = xmldict.ConvertXmlToDict(elemtree)

            ### partially adapted from kepler_find_simbad_publid_sources.py:parse_class()
            ### - TODO: probably only need to do this once, if the VOTABLE format is consistant for all simbad sources
            b = xmld_data['VOTABLE']['RESOURCE']['TABLE']['FIELD']
            i_col_otype = -1
            i_col_dist = -1
            i_col_sptype = -1
            i_col_mainid = -1
            for i, elem in enumerate(b):
                if elem['name'] == 'OTYPE':
                    i_col_otype = i
                elif elem['name'] == 'DISTANCE':
                    i_col_dist = i
                elif elem['name'] == 'SP_TYPE':
                    i_col_sptype = i
                elif elem['name'] == 'MAIN_ID':
                    i_col_mainid = i
                    #break # this doesnt seem like it should work 100% of the time
            ###

            dist_list = []
            class_list = []
            sptype_list = []
            mainid_list = []
            if type(xmld_data['VOTABLE']['RESOURCE']['TABLE']['DATA']['TABLEDATA']['TR']) != type([]):
                dist_list.append(float(xmld_data['VOTABLE']['RESOURCE']['TABLE']['DATA']['TABLEDATA']['TR']['TD'][i_col_dist]))
                class_list.append(str(xmld_data['VOTABLE']['RESOURCE']['TABLE']['DATA']['TABLEDATA']['TR']['TD'][i_col_otype]))
                sp_type = str(xmld_data['VOTABLE']['RESOURCE']['TABLE']['DATA']['TABLEDATA']['TR']['TD'][i_col_sptype])
                if sp_type == "None":
                    sptype_list.append('')
                else:
                    sptype_list.append(sp_type)                    
                mainid = str(xmld_data['VOTABLE']['RESOURCE']['TABLE']['DATA']['TABLEDATA']['TR']['TD'][i_col_mainid])
                if mainid == "None":
                    mainid_list.append('')
                else:
                    mainid_list.append(mainid)
            else:
                for xmld in xmld_data['VOTABLE']['RESOURCE']['TABLE']['DATA']['TABLEDATA']['TR']:
                    dist_list.append(float(xmld['TD'][i_col_dist]))
                    class_list.append(str(xmld['TD'][i_col_otype]))
                    sp_type = str(xmld['TD'][i_col_otype])
                    if sp_type == "None":
                        sptype_list.append('')
                    else:
                        sptype_list.append(sp_type)
                    mainid = str(xmld['TD'][i_col_mainid])
                    if mainid == "None":
                        mainid_list.append('')
                    else:
                        mainid_list.append(mainid)

            if abs(dist_list[0] - nomad_sources[src_id]['dist']) <= 0.5:
                print "[0] matches: %d nomad=%lf deldist=%lf simbad=%s mainid=%s %s %s" % (src_id, nomad_sources[src_id]['dist'], abs(dist_list[0] - nomad_sources[src_id]['dist']), class_list[0], mainid_list[0], str(dist_list), str(class_list))
                srcid_class_match_dict[src_id] = {'class':class_list[0], 'simbad_dist':dist_list[0], 'simbad_sptype':sptype_list[0], 'main_id':mainid_list[0]}
                srcid_class_match_dict[src_id].update(nomad_sources[src_id])
            else:
                match_found = False
                for i in range(len(dist_list)):
                    if abs(dist_list[i] - nomad_sources[src_id]['dist']) <= 0.5:
                        print "[%d] matches: %d nomad=%lf simbad=%lf simbad=%s mainid=%s %s %s" % (i, src_id, nomad_sources[src_id]['dist'], dist_list[i], class_list[i], mainid_list[i], str(dist_list), str(class_list))
                        srcid_class_match_dict[src_id] = {'class':class_list[i], 'simbad_dist':dist_list[i], 'simbad_sptype':sptype_list[i], 'main_id':mainid_list[i]}
                        srcid_class_match_dict[src_id].update(nomad_sources[src_id])

                        match_found = True
                        break
                if not match_found:
                    print "NO dist match: %d nomad=%lf simbad=%s simbad=%s" % (src_id, nomad_sources[src_id]['dist'], str(dist_list), str(class_list))
                    
        return srcid_class_match_dict


    def insert_src_class_match_in_table(self, srcid_class_match_dict):
        """ Store the elements of the dictionary which matches simbad sources (and the sci classes)
        with nomad sources   (which match tutor sources).

        Store this in a mysql table.

        create table using:

        CREATE TABLE tutor_simbad_classes
        (src_id INT, simbad_class VARCHAR(16), simbad_dist FLOAT, simbad_sptype VARCHAR(16), main_id VARCHAR(32), PRIMARY KEY (src_id), INDEX (simbad_class));

        """
        insert_list = ["INSERT INTO tutor_simbad_classes (src_id, simbad_class, simbad_dist, simbad_sptype, main_id) VALUES "]

        for srcid, src_dict in srcid_class_match_dict.iteritems():
            insert_list.append("(%d, '%s', %f, '%s', '%s'), " % (srcid, src_dict['class'], src_dict['simbad_dist'], src_dict['simbad_sptype'], src_dict['main_id']))

        self.cursor.execute(''.join(insert_list)[:-2] + " ON DUPLICATE KEY UPDATE simbad_class=VALUES(simbad_class), simbad_dist=VALUES(simbad_dist), simbad_sptype=VALUES(simbad_sptype), main_id=VALUES(main_id)")

        import pdb; pdb.set_trace()
        print


    def get_simbad_abstracts(self, srcid_class_match_dict):
        """ Query and retrieve SIMBAD abstracts, using previously retrieved literature references for Simbad matched ASAS sources.
        """
        import urllib
        from BeautifulSoup import BeautifulSoup, Comment
        fp = open('/tmp/src_litrefs.pkl','rb')
        src_litrefs = cPickle.load(fp)
        fp.close()

        abs_bibcodes_dirpath = '/home/obs/scratch/determine_simbad'
        abs_bibcodes = os.listdir(abs_bibcodes_dirpath)

        abstracts_pkl_dirpath = '/home/obs/scratch/determine_simbad_abstracts.pkl'
        if os.path.exists(abstracts_pkl_dirpath):
            fp = open(abstracts_pkl_dirpath,'rb')
            abstracts_dict = cPickle.load(fp)
            fp.close()
        else:
            abstracts_dict = {}

        srcid_list = src_litrefs.keys()
        srcid_list.sort()
        for i, src_id in enumerate(srcid_list):
            src_bib_dict = src_litrefs[src_id]
            for bibcode, abstract_url in src_bib_dict.iteritems():
                if abstracts_dict.has_key(bibcode):
                    continue # skip since we parsed this already
                fpath = "%s/%s" % (abs_bibcodes_dirpath, bibcode.replace('/','___'))

                # TODO: need to check that we have not parsed and place in dict
                if not bibcode in abs_bibcodes:
                    f_url = urllib.urlopen(abstract_url)
                    webpage_str = f_url.read()
                    f_url.close()
                    fp = open(fpath, 'w')
                    fp.write(webpage_str)
                    fp.close()
                else:
                    fp = open(fpath)
                    webpage_str = fp.read()
                    fp.close()
                    
                
                soup = BeautifulSoup(webpage_str)
                comments = soup.findAll(text=lambda text:isinstance(text, Comment))
                [comment.extract() for comment in comments]
                
                #print soup.html.body('p', limit=2)[1]('table', limit=2)[1].prettify()
                #import pdb; pdb.set_trace()
                #print
                try:
                    abstract_rows = soup.html.body('p', limit=2)[1]('table', limit=2)[1]('tr')
                except:
                    print "skipping:", bibcode
                    continue

                for r in abstract_rows:
                    if 'Title:' in str(r('td')[0].getText()):
                        title = r('td')[2].getText() # in UNICODE
                    elif 'Authors:' in str(r('td')[0].getText()):
                        authors = r('td')[2].getText() # in UNICODE
                    elif 'Publication:' in str(r('td')[0].getText()):
                        publication = r('td')[2].getText() # in UNICODE
                    elif 'Publication Date:' in str(r('td')[0].getText()):
                        publication_date = r('td')[2].getText() # in UNICODE
                    elif 'Keywords:' in str(r('td')[0].getText()):
                        keywords = r('td')[2].getText() # in UNICODE
                #print "title:%s \nauthors:%s \npub:%s \ndate:%s \nkeywords:%s\n" % (title, authors, publication, publication_date, keywords)
                print i, src_id, bibcode, title[:60]
                abstracts_dict[bibcode] = {'title':title,
                                           'authors':authors,
                                           'publication':publication,
                                           'pub_date':publication_date,
                                           'keywords':keywords,
                                           }
        if os.path.exists(abstracts_pkl_dirpath):
            os.system('rm ' + abstracts_pkl_dirpath)
        fp = open(abstracts_pkl_dirpath,'wb')
        cPickle.dump(abstracts_dict, fp ,1)
        fp.close()
        import pdb; pdb.set_trace()
        print


    # OBSOLETE:
    def get_simbad_literature_refs__asabsharvard(self, srcid_class_match_dict):
        """ Query and retrieve SIMBAD literature references for Simbad matched ASAS sources.
        """
        import urllib
        from BeautifulSoup import BeautifulSoup, Comment
        src_litrefs = {}
        srcid_list = srcid_class_match_dict.keys()
        srcid_list.sort()
        n_srcid = len(srcid_list)
        for i, src_id in enumerate(srcid_list):
            src_dict = srcid_class_match_dict[src_id]
            src_litrefs[src_id] = {}
            url_str = "http://adsabs.harvard.edu/cgi-bin/nph-abs_connect?db_key=AST&db_key=PRE&qform=AST&arxiv_sel=astro-ph&arxiv_sel=cond-mat&arxiv_sel=cs&arxiv_sel=gr-qc&arxiv_sel=hep-ex&arxiv_sel=hep-lat&arxiv_sel=hep-ph&arxiv_sel=hep-th&arxiv_sel=math&arxiv_sel=math-ph&arxiv_sel=nlin&arxiv_sel=nucl-ex&arxiv_sel=nucl-th&arxiv_sel=physics&arxiv_sel=quant-ph&arxiv_sel=q-bio&sim_query=YES&ned_query=YES&adsobj_query=YES&obj_req=YES&aut_logic=OR&obj_logic=OR&author=&object=%s&start_mon=&start_year=&end_mon=&end_year=&ttl_logic=OR&title=&txt_logic=OR&text=&nr_to_return=200&start_nr=1&jou_pick=ALL&ref_stems=&data_and=ALL&group_and=ALL&start_entry_day=&start_entry_mon=&start_entry_year=&end_entry_day=&end_entry_mon=&end_entry_year=&min_score=&sort=SCORE&data_type=SHORT&aut_syn=YES&ttl_syn=YES&txt_syn=YES&aut_wt=1.0&obj_wt=1.0&ttl_wt=0.3&txt_wt=3.0&aut_wgt=YES&obj_wgt=YES&ttl_wgt=YES&txt_wgt=YES&ttl_sco=YES&txt_sco=YES&version=1" % (src_dict['main_id'])
            f_url = urllib.urlopen(url_str)
            webpage_str = f_url.read()
            f_url.close()
            
            soup = BeautifulSoup(webpage_str)
            comments = soup.findAll(text=lambda text:isinstance(text, Comment))
            [comment.extract() for comment in comments]
            #print soup.html.body.form.find('table')
            #print '------------'
            #print soup.html.body.form.findAll('table')[1].table.tbody.findAll('tr')
            #soup.html.body.form.findAll('table')[1].extract()
            #bib_rows = soup.html.body.form.fetch('table')[1].fetch('tr')
            #print soup
            try:
                bib_rows = soup.html.body.form('table', limit=2)[1]('tr')
                print 'parsed:', i, n_srcid, src_id
            except:
                # likely no results returned
                #print 'len(soup.html.body.form.table):', len(soup.html.body.form.table)
                print 'skip:  ', i, n_srcid, src_id
                continue
            for r in bib_rows:
                for td in r('td'):
                    x = td.input
                    if x == None:
                        continue
                    bibcode = x['value']
                    abstract_url = td.a['href']
                    # NOTE: I could probably extract some author names, title
                    src_litrefs[src_id][bibcode] = abstract_url
                    #print bibcode, abstract_url
            #import pdb; pdb.set_trace()
            #print
            #fp = open('/tmp/124', 'w')
            #fp.write(webpage_str)
            #fp.close()
            #import pdb; pdb.set_trace()
            #print
            #elemtree = ElementTree.fromstring(webpage_str)
            #xmld_data = xmldict.ConvertXmlToDict(elemtree)
            #b = xmld_data['HTML']['body']['form']
            if (i % 500) == 0:
                fp = open('/tmp/src_litrefs_%d.pkl' % (i),'wb')
                cPickle.dump(src_litrefs,fp,1) # ,1) means a binary pkl is used.
                fp.close()


        import pdb; pdb.set_trace()
        print
        fp = open('/tmp/src_litrefs.pkl','wb')
        cPickle.dump(src_litrefs,fp,1) # ,1) means a binary pkl is used.
        fp.close()


    def get_simbad_literature_refs(self, srcid_class_match_dict):
        """ Query and retrieve SIMBAD literature references for Simbad matched ASAS sources.
        """
        import urllib
        from BeautifulSoup import BeautifulSoup, Comment

        litrefs_init_fpath = '/home/dstarr/scratch/determine_simbad__orig/src_litrefs.pkl'
        if os.path.exists(litrefs_init_fpath):
            fp = open(litrefs_init_fpath,'rb')
            src_litrefs = cPickle.load(fp)
            fp.close()
        else:
            src_litrefs = {}
        srcid_list = srcid_class_match_dict.keys()
        srcid_list.sort()
        n_srcid = len(srcid_list)
        for i, src_id in enumerate(srcid_list):
            src_dict = srcid_class_match_dict[src_id]
            if src_dict['main_id'].count(' ') > 0:
                ### Source names return random literature results if ' ' is not replaced with '+'
                src_litrefs[src_id] = {}
            else:
                ### This assumes that src_litrefs[src_id] has been filled previously
                continue # we skip re-retrieving this source.
            src_name = src_dict['main_id'].replace(' ','+')
            #url_str_new = "http://simbad.u-strasbg.fr/simbad/sim-id?Ident=%s&NbIdent=1&Radius=2&Radius.unit=arcmin&submit=submit+id" % (src_name)

            url_str = "http://adsabs.harvard.edu/cgi-bin/nph-abs_connect?db_key=AST&db_key=PRE&qform=AST&arxiv_sel=astro-ph&arxiv_sel=cond-mat&arxiv_sel=cs&arxiv_sel=gr-qc&arxiv_sel=hep-ex&arxiv_sel=hep-lat&arxiv_sel=hep-ph&arxiv_sel=hep-th&arxiv_sel=math&arxiv_sel=math-ph&arxiv_sel=nlin&arxiv_sel=nucl-ex&arxiv_sel=nucl-th&arxiv_sel=physics&arxiv_sel=quant-ph&arxiv_sel=q-bio&sim_query=YES&ned_query=YES&adsobj_query=YES&obj_req=YES&aut_logic=OR&obj_logic=OR&author=&object=%s&start_mon=&start_year=&end_mon=&end_year=&ttl_logic=OR&title=&txt_logic=OR&text=&nr_to_return=200&start_nr=1&jou_pick=ALL&ref_stems=&data_and=ALL&group_and=ALL&start_entry_day=&start_entry_mon=&start_entry_year=&end_entry_day=&end_entry_mon=&end_entry_year=&min_score=&sort=SCORE&data_type=SHORT&aut_syn=YES&ttl_syn=YES&txt_syn=YES&aut_wt=1.0&obj_wt=1.0&ttl_wt=0.3&txt_wt=3.0&aut_wgt=YES&obj_wgt=YES&ttl_wgt=YES&txt_wgt=YES&ttl_sco=YES&txt_sco=YES&version=1" % (src_name) #(src_dict['main_id'])
            f_url = urllib.urlopen(url_str)
            webpage_str = f_url.read()
            f_url.close()
            
            soup = BeautifulSoup(webpage_str)
            comments = soup.findAll(text=lambda text:isinstance(text, Comment))
            [comment.extract() for comment in comments]
            #print soup.html.body.form.find('table')
            #print '------------'
            #print soup.html.body.form.findAll('table')[1].table.tbody.findAll('tr')
            #soup.html.body.form.findAll('table')[1].extract()
            #bib_rows = soup.html.body.form.fetch('table')[1].fetch('tr')
            #print soup
            try:
                bib_rows = soup.html.body.form('table', limit=2)[1]('tr')
                print 'parsed:', i, n_srcid, src_id, src_dict['main_id']
            except:
                # likely no results returned
                #print 'len(soup.html.body.form.table):', len(soup.html.body.form.table)
                print 'skip:  ', i, n_srcid, src_id, src_dict['main_id']
                continue
            for r in bib_rows:
                for td in r('td'):
                    x = td.input
                    if x == None:
                        continue
                    bibcode = x['value']
                    abstract_url = td.a['href']
                    # NOTE: I could probably extract some author names, title
                    src_litrefs[src_id][bibcode] = abstract_url
                    #print bibcode, abstract_url
            #import pdb; pdb.set_trace()
            #print
            #fp = open('/tmp/124', 'w')
            #fp.write(webpage_str)
            #fp.close()
            #import pdb; pdb.set_trace()
            #print
            #elemtree = ElementTree.fromstring(webpage_str)
            #xmld_data = xmldict.ConvertXmlToDict(elemtree)
            #b = xmld_data['HTML']['body']['form']
            if (i % 500) == 0:
                fp = open('/tmp/src_litrefs_%d.pkl' % (i),'wb')
                cPickle.dump(src_litrefs,fp,1) # ,1) means a binary pkl is used.
                fp.close()


        import pdb; pdb.set_trace()
        print
        fp = open('/tmp/src_litrefs.pkl','wb')
        cPickle.dump(src_litrefs,fp,1) # ,1) means a binary pkl is used.
        fp.close()


    def parse_simbad_id_hierarchy(self):
        """ Parse a txt file adapted from
        http://cds.u-strasbg.fr/cgi-bin/Otype?X
         --> removed many of the "possible" classes
         --> ensured that '  ' left-seperated each heirachy level and UNKNOWN had 0 left-space

         Also changed to this:
        Cepheid             Cepheid variable Star
          deltaCep          Classical Cepheid (delta Cep type)
          MultiMode_Ceph    Multi Mode Cepheid          
      SG*                   Evolved supergiant star
        RedSG*                Red supergiant star
        YellowSG*             Yellow supergiant star
        BlueSG**              Blue supergiant star
      RGB*                  Red Giant Branch star
        SARG_A              Short amplitude red giant A
        SARG_B              Short amplitude red giant B
        LSP                 Long Secondary Period Red Giant
      AGB*                  Asymptotic Giant Branch Star (He-burning)
        C*                  Carbon Star
        S*                  S Star
        RCB                 R Cor Bor
         
        """
        import re
        ### left whitespace matcher:
        whitespace_matcher = re.compile(r'^\s+')

        fpath = '/home/dstarr/src/TCP/Data/simbad_id_hierarchy.txt'
        lines = open(fpath).readlines()
        class_descriptions = {}
        parent_dict = {}
        child_dict = {}
        parents = []
        for line in lines:
            try:
                n_left_space = len(whitespace_matcher.search(line).group())
            except:
                n_left_space = 0
            substr = line[n_left_space:]
            class_name = substr[:substr.find(' ')]
            substr = line[n_left_space + len(class_name):]
            n_middle_space = len(whitespace_matcher.search(substr).group())
            class_descript = line[n_left_space + len(class_name) + n_middle_space:].strip()

            if n_left_space == 0:
                parent_dict[class_name] = '' # just for consistancy
            elif n_left_space > ((len(parents) - 1)*2):
                parent_dict[class_name] = prev_name
            elif n_left_space < ((len(parents) - 1)*2):
                #print '  range:', len(parents) - (0.5*n_left_space), 'n_left_space:', n_left_space, 'len(parents):', len(parents)
                for i in range(len(parents) - (n_left_space/2)):
                    parents.pop()
                parent_dict[class_name] = parents[-1]
            elif n_left_space == ((len(parents) - 1)*2):
                parents.pop()
                parent_dict[class_name] = parents[-1]

            #print class_name, n_left_space, parent_dict[class_name]#, parents#, class_descript
            parents.append(class_name)
            class_descriptions[class_name] = class_descript
            if not child_dict.has_key(parent_dict[class_name]):
                child_dict[parent_dict[class_name]] = [class_name]
            else:
                child_dict[parent_dict[class_name]].append(class_name)
            prev_name = class_name
        return {'parent_dict':parent_dict,
                'child_dict':child_dict,
                'class_descriptions':class_descriptions}

    def parse_asas_classif_catalog(self, fpath=''):
        """ Parse the ASAS classifications made by Joey.
        """

        from numpy import loadtxt
        out_dict = {}
        data = loadtxt(fpath, delimiter=',', skiprows=1,
                           dtype={'names': ('ASAS_ID',
                                            'dotAstro_ID',
                                            'RA',
                                            'DEC',
                                            'Class',
                                            'P_Class',
                                            'Anomaly',
                                            'ACVS_Class',
                                            'Train_Class',
                                            'Mira',
                                            'Semireg_PV',
                                            'SARG_A',
                                            'SARG_B',
                                            'LSP',
                                            'RV_Tauri',
                                            'Classical_Cepheid',
                                            'PopII_Cepheid',
                                            'MultiMode_Cepheid',
                                            'RR_Lyrae_FM',
                                            'RR_Lyrae_FO',
                                            'RR_Lyrae_DM',
                                            'Delta_Scuti',
                                            'SX_Phe',
                                            'Beta_Cephei',
                                            'Pulsating_Be',
                                            'PerVarSG',
                                            'ChemPeculiar',
                                            'RCB',
                                            'ClassT_Tauri',
                                            'Weakline_T_Tauri',
                                            'RS_CVn',
                                            'Herbig_AEBE',
                                            'S_Doradus',
                                            'Ellipsoidal',
                                            'Beta_Persei',
                                            'Beta_Lyrae',
                                            'W_Ursae_Maj',
                                            'P',
                                            'P_signif',
                                            'N_epochs',
                                            'V',
                                            'deltaV'),
                                  'formats': ('S13',
                                              'i4',
                                              'f8',
                                              'f8',
                                              'S20',
                                              'f4',
                                              'f4',
                                              'S30',
                                              'S20',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              'f4',
                                              )})
        #print data['ASAS_ID'][:40]
        return data


    def write_source_summary_file(self, src_id=None,
                                  i_cat=None,
                                  src_litrefs=None,
                                  abstracts_dict=None,
                                  cat_probs=None,
                                  hier_dict=None,
                                  srcid_class_match_dict=None,
                                  jclass_simbadclass=None):
        """ Write summary info for a single ASAS source into a file for sharing with Olfa.

        # TODO: secondary classificaiton
        """
        assert(cat_probs['dotAstro_ID'][i_cat] == src_id)

        class_list = ['Mira',
                      'Semireg_PV',
                      'SARG_A',
                      'SARG_B',
                      'LSP',
                      'RV_Tauri',
                      'Classical_Cepheid',
                      'PopII_Cepheid',
                      'MultiMode_Cepheid',
                      'RR_Lyrae_FM',
                      'RR_Lyrae_FO',
                      'RR_Lyrae_DM',
                      'Delta_Scuti',
                      'SX_Phe',
                      'Beta_Cephei',
                      'Pulsating_Be',
                      'PerVarSG',
                      'ChemPeculiar',
                      'RCB',
                      'ClassT_Tauri',
                      'Weakline_T_Tauri',
                      'RS_CVn',
                      'Herbig_AEBE',
                      'S_Doradus',
                      'Ellipsoidal',
                      'Beta_Persei',
                      'Beta_Lyrae',
                      'W_Ursae_Maj']
        class_list.remove(cat_probs['Class'][i_cat]) # remove the top-prob class
        prob_class_tups = []
        for class_name in class_list:
            prob_class_tups.append((cat_probs[class_name][i_cat], class_name))
        prob_class_tups.sort(reverse=True)

        lines = []
        line = []
        line.append(str(src_id))
        line.append('"%s"' %(srcid_class_match_dict[src_id]['main_id']))
        line.append(str(cat_probs['ASAS_ID'][i_cat]))
        line.append(str(srcid_class_match_dict[src_id]['class'])) #simbad class
        line.append(str(srcid_class_match_dict[src_id]['simbad_sptype']))
        line.append(str(jclass_simbadclass[cat_probs['Class'][i_cat]]))
        line.append(str(cat_probs['P_Class'][i_cat]))

        line.append(str(jclass_simbadclass[prob_class_tups[0][1]]))
        line.append("%f" % (prob_class_tups[0][0]))

        line.append(str(jclass_simbadclass[prob_class_tups[1][1]]))
        line.append("%f" % (prob_class_tups[1][0]))

        lines.append(' '.join(line))

        #lines.append(str(src_id))
        #lines.append(str(srcid_class_match_dict[src_id]['main_id']))
        #lines.append(str(cat_probs['ASAS_ID'][i_cat]))
        #lines.append(str(srcid_class_match_dict[src_id]['class']))
        #lines.append(str(srcid_class_match_dict[src_id]['simbad_sptype']))
        #lines.append(str(cat_probs['Class'][i_cat]))
        #lines.append(str(cat_probs['P_Class'][i_cat]))

        bibcode_list = src_litrefs[src_id].keys()
        bibcode_list.sort(reverse=True)
        for bibcode in bibcode_list:
            if not abstracts_dict.has_key(bibcode):
                continue # there are 82 of 38000 abstracts entries which were not correctly downloaded (in HTML: Please try your query again")
            lines.append(' '*4 + str(bibcode))# + ' '*4 + str(abstracts_dict[bibcode]['title']))
            #lines.append(' '*12 + str(abstracts_dict[bibcode]['title']))
            

        out_str = '\n'.join(lines) + '\n'
        
        #print out_str
        #import pdb; pdb.set_trace()
        #print
        return out_str
    
    def write_summary_files(self, srcid_class_match_dict):
        """ Write summary files of literature / abstracts for ASAS sources.
        """
        abstracts_pkl_dirpath = '/home/dstarr/scratch/determine_simbad_abstracts.pkl'
        litrefs_init_fpath = '/home/dstarr/scratch/src_litrefs.pkl'

        jclass_simbadclass = {
            'Mira':'Mira',
            'Semireg_PV':'semi-regV*',
            'SARG_A':'SARG_A',
            'SARG_B':'SARG_B',
            'LSP':'LSP',
            'RV_Tauri':'PulsV*RVTau',
            'Classical_Cepheid':'deltaCep',
            'PopII_Cepheid':'PulsV*WVir',
            'MultiMode_Cepheid':'MultiMode_Ceph',
            'RR_Lyrae_FM':'RRLyr_FM',
            'RR_Lyrae_FO':'RRLyr_FO',
            'RR_Lyrae_DM':'RRLyr_DM',
            'Delta_Scuti':'PulsV*delSct',
            'SX_Phe':'pulsV*SX',
            'Beta_Cephei':'PulsV*bCep',
            'Pulsating_Be':'Be*',
            'PerVarSG':'SG*',
            'ChemPeculiar':'RotV*alf2CVn',
            'RCB':'RCB',
            'ClassT_Tauri':'TTau*_cl',
            'Weakline_T_Tauri':'TTau*_wk',
            'RS_CVn':'RSCVn',
            'Herbig_AEBE':'HAEBE',
            'S_Doradus':'S_Doradus',
            'Ellipsoidal':'RotV*Ell',
            'Beta_Persei':'EB*Algol',
            'Beta_Lyrae':'EB*betLyr',
            'W_Ursae_Maj':'EB*WUMa'}


        fp = open(litrefs_init_fpath,'rb')
        src_litrefs = cPickle.load(fp)
        fp.close()
        #src_litrefs[src_id][bibcode] = abstract_url

        fp = open(abstracts_pkl_dirpath,'rb')
        abstracts_dict = cPickle.load(fp)
        fp.close()
        #abstracts_dict[bibcode] = {'title':title,
        #                           'authors':authors,
        #                           'publication':publication,
        #                           'pub_date':publication_date,
        #                           'keywords':keywords,
        #                           }

        #srcid_class_match_dict[229376]
        #{'B': '12.722',
        # 'H': '6.146',
        # 'J': '7.041',
        # 'K': '5.816',
        # 'R': '10.31',
        # 'V': '11.189',
        # 'class': 'PulsV*',
        # 'dist': 0.04,
        # 'extinct_bv': '',
        # 'main_id': 'V* UV Cnc',
        # 'simbad_dist': 0.04,
        # 'simbad_sptype': 'M0'}

        # TODO: want to parse the ASAS catatlog classifications
        cat_probs = self.parse_asas_classif_catalog(fpath='/home/dstarr/src/ASASCatalog/catalog/asas_class_catalog_v2_3.dat')

        # DONE: want to convert simbad classes to Dot-astro classes
        #   - I have the lookup, so I can roughly translate simbad to DotAstro classes
        hier_dict = self.parse_simbad_id_hierarchy()
        #return {'parent_dict':parent_dict,
        #        'child_dict':child_dict,
        #        'class_descriptions':class_descriptions}

        
        if 0:
            ### This is just to ensure that all of the abstract files in a dir are relevant
            for i, src_id in enumerate(cat_probs['dotAstro_ID']):
                if not src_litrefs.has_key(src_id):
                    continue
                bibcode_list = src_litrefs[src_id].keys()
                for bibcode in bibcode_list:
                    all_fpath = '"/home/dstarr/scratch/determine_simbad__all/' + bibcode + '"'
                    final_fpath = '"/home/dstarr/scratch/determine_simbad/' + bibcode + '"'
                    if not os.path.exists(final_fpath):
                        cp_str = 'cp %s %s' % (all_fpath, final_fpath)
                        #import pdb; pdb.set_trace()
                        #print
                        os.system(cp_str)
                
        fp = open('/home/dstarr/scratch/determine_simbad.source_data', 'w')
        for i, src_id in enumerate(cat_probs['dotAstro_ID']):
            if not srcid_class_match_dict.has_key(src_id):
                continue # we skip this source since there is no simbad equivalent
            out_str = self.write_source_summary_file(src_id=src_id,
                                           i_cat=i,
                                           src_litrefs=src_litrefs,
                                           abstracts_dict=abstracts_dict,
                                           cat_probs=cat_probs,
                                           hier_dict=hier_dict,
                                           srcid_class_match_dict=srcid_class_match_dict,
                                           jclass_simbadclass=jclass_simbadclass)
            fp.write(out_str)
                                           
        fp.close()
        #abstracts_dict[bibcode] = {'title':title,
        #                           'authors':authors,
        #                           'publication':publication,
        #                           'pub_date':publication_date,
        #                           'keywords':keywords,

        fp = open('/home/dstarr/scratch/abstract_ids_and_info', 'w')

        bib_list = abstracts_dict.keys()
        bib_list.sort()
        for bibcode in bib_list:
            bib_dict = abstracts_dict[bibcode]
            lines = []
            lines.append("%s" % (bibcode))
            lines.append("    %s" % (bib_dict['title']))
            lines.append("    %s" % (bib_dict['keywords']))
            lines.append("    %s" % (bib_dict['authors']))
            lines.append("    %s" % (bib_dict['pub_date']))
            lines.append("    %s" % (bib_dict['publication']))
            
            out_str = '\n'.join(lines) + '\n'
        
            fp.write(out_str)
                                           
        fp.close()
        import pdb; pdb.set_trace()
        print

        if 0:
            ### This just prints the unique simbad classes used in literature for ASAS sources
            simbad_srcid_list = []
            for srcid, sdict in srcid_class_match_dict.iteritems():
                if not sdict['class'] in simbad_srcid_list:
                    simbad_srcid_list.append(sdict['class'])


    def main(self, do_insert=False):
        """
        """

        if not os.path.exists(self.pars['srcid_simbad_nomad_match_pkl_fpath']):
            srcid_class_match_dict = self.make_nomad_simbad_source_match_dict()
            fp = open(self.pars['srcid_simbad_nomad_match_pkl_fpath'],'wb')
            cPickle.dump(srcid_class_match_dict,fp,1) # ,1) means a binary pkl is used.
            fp.close()
        else:
            fp = open(self.pars['srcid_simbad_nomad_match_pkl_fpath'],'rb')
            srcid_class_match_dict = cPickle.load(fp)
            fp.close()
            
        if do_insert:
            self.insert_src_class_match_in_table(srcid_class_match_dict)
        
        ### currently run on anathem:
        #self.get_simbad_literature_refs(srcid_class_match_dict)
        ### Im running this on a seperate IP (pted):
        #self.get_simbad_abstracts(srcid_class_match_dict)

        ### This is for generating summary files for export:
        self.write_summary_files(srcid_class_match_dict)

        import pdb; pdb.set_trace()
        print

    
if __name__ == '__main__':

    pars = { \
        'mysql_username':"pteluser", 
        'mysql_hostname':"192.168.1.25", 
        'mysql_database':'source_test_db', 
        'mysql_port':3306,
        'source_nomad_pkl_fpath':os.path.abspath(os.environ.get("TCP_DIR") + '/Data/best_nomad_src.pkl126'), #'/Data/best_nomad_src.pkl'), # generated by get_colors_for_tutor_sources.py
        'simbad_votable_dirpath':os.path.abspath(os.environ.get("HOME") + '/scratch/simbad_votables'),
        'srcid_simbad_nomad_match_pkl_fpath':os.path.abspath(os.environ.get("TCP_DIR") + '/Data/srcid_simbad_nomad_match.pkl'),
        }

    DetermineSimbadClass = Determine_Simbad_Class(pars=pars)
    DetermineSimbadClass.main(do_insert=False)
