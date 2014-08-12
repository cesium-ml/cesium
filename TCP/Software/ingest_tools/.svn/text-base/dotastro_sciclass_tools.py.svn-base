#!/usr/bin/env python 
""" Tools for accessing science-classes in Dotastro.org mysql database.

   v0.1 20100503 developed for use by pairwise_classification.py, for
        generation of .pkl.gz classifier.

  

"""
import os, sys
try:
    import MySQLdb
except:
    pass
import glob

#OBSOLETE / UNUSED:
#class Populate_Arff_Wrapper:
#    """ These tools are less reusable and are intended to only be run from
#    dotastro_sciclass_tools.py
#    """


class Dotastro_Sciclass_Tools:
    """ These tools should be fairly reuseable and lightweight, since other
    modules will import and use them.
    """

    def __init__(self, pars={}):


        # This Canonical lookup dict allows one to find the canonical class shortname
        #   for a more ambiguous shortname.  Normally this is for tutor class shortnames
        #   which need to be matched with their dotastro shortnames.
        #   - if there is no key for a shortname, then it is assumed that the key is not ambiguous.
        canonical_shortnames = {'AM':'am',
                                'EA':'alg',
                                'ACYG':'ac',
                                'ACV':'aii',
                                'BLBOO':'ca',
                                'BY':'by',
                                'BE':'be',
                                'BCEP':'bc',
                                'EB':'bly',
                                'Cataclysmic':'cv',
                                'CEP':'c',
                                'DQ':'dqh',
                                'DSCT':'ds',
                                'Eruptive':'ev',
                                'FKCOM':'fk',
                                'FU':'fuor',
                                'GCAS':'gc',
                                'GDOR':'gd',
                                'GRB':'grb',
                                'LSB':'lgrb',
                                'M':'mira',
                                'N':'nov',
                                'NL':'n-l',
                                'PVTEL':'pvt',
                                'SNIa-pec':'tiapec',
                                'Polars':'p',
                                'Pulsating':'puls',
                                'RCB':'rcb',
                                'RR':'rr-lyr',
                                'RRcl':'rr-cl',
                                'RRe':'rr-e',
                                'RS':'rscvn',
                                'RV':'rv',
                                'RVA':'rvc',
                                'RVB':'rvv',
                                'NR':'rn',
                                'Rotating':'rot',
                                'SDOR':'sdorad',
                                'UGSS':'ssc',
                                'UGSU':'su',
                                'SXARI':'sxari',
                                'SXPHE':'sx',
                                'SHB':'sgrb',
                                'SGR':'srgrb',
                                'SNIa-sc':'tiasc',
                                'SN':'sne',
                                'ZAND':'sv',
                                'SNI':'tsni',
                                'SNII':'tsnii',
                                'SNIIL':'iil',
                                'SNIIN':'iin',
                                'SNIIP':'iip',
                                'SNIa':'tia',
                                'SNIb':'tib',
                                'SNIc':'tic',
                                'UG':'ug',
                                'UV':'uv',
                                'UXUma':'ux',
                                'GCVS':'vs',
                                'DW':'wu',
                                'EW':'wu',
                                'XB':'xrb',
                                'UGZ':'zc',
                                'ZZ':'zz',
                                'ZZA':'zzh',
                                'ZZB':'zzhe',
                                'ZZO':'zzheii',
                                'WR':'wr',
                                'CEP(B)':'cm',
                                'SR':'sreg',
                                'INT':'tt',
                                'IN':'ov',
                                }

        #self.pars = {'tcptutor_hostname':'lyra.berkeley.edu',
	#	'tcptutor_username':'pteluser',
	#	'tcptutor_password':'Edwin_Hubble71',
	#	'tcptutor_port':     3306, # 13306,
	#	'tcptutor_database':'tutor',
        #        'canonical_shortnames':canonical_shortnames}
        self.pars = {'tcptutor_hostname':'192.168.1.103',
		'tcptutor_username':'tutor',
		'tcptutor_password':'ilove2mass',
		'tcptutor_port':     3306, # 13306,
		'tcptutor_database':'tutor',
                'canonical_shortnames':canonical_shortnames}
        self.pars.update(pars)


    def make_tutor_db_connection(self):
        """
        """
        try:
            self.db = MySQLdb.connect(host=self.pars['tcptutor_hostname'], \
                                     user=self.pars['tcptutor_username'], \
                                     passwd=self.pars['tcptutor_password'],\
                                     db=self.pars['tcptutor_database'],\
                                     port=self.pars['tcptutor_port'])
            self.cursor = self.db.cursor()
        except:
            self.db = None
            self.cursor = None


    def generate_dotastro_arff_using_subset_from_db_query(self, old_arff='', new_arff='', select_str=''):
        """ Query the Tutor/dotastro database for all sources with
        high confidence classifications. 
        copy all arff rows in reference .arff which dont match low-confidence condition.

        # #Copy existing vosource
        # # xmls with high classification confidences to a new directory.

        NOTE: if we want to just exclude CataLina Sky Survey sources, we can
        WHERE using:              Sources.project_id = 115;


        NOTE: This assumes that the srcid is in the first element/column of the .arff file.

        """
        self.make_tutor_db_connection()
        
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()
        srcid_list = []
        for row in results:
            srcid_list.append(str(row[0]))

        old_arff_lines = open(old_arff).readlines()
        new_arff_lines = []
        in_data = False
        for old_arff_row in old_arff_lines:
            if not in_data:
                new_arff_lines.append(old_arff_row)
                if '@data' in old_arff_row.lower():
                    in_data = True
                continue
            else:
                elems = old_arff_row.split(',')
                if elems[0] in srcid_list:
                    pass # we do not use this srcid / arff row
                else:
                    new_arff_lines.append(old_arff_row)
        if os.path.exists(new_arff):
            os.system('rm ' + new_arff)
        fp = open(new_arff, 'w')
        fp.writelines(new_arff_lines)
        fp.close()

        
    def generate_dotastro_sql_filterd_arff(self, old_arff='', new_arff='', filter_type=''):
        """ Generate a .arff file by determining a subset of sources drawn from
        a given larger arff file.

        LSST synthetic eclipsing data is projet_id=114
        Catalina Sky Survey project is project_id == 115

        Original Debosscher data is project_id=12,
        new import Debosscher dataset is project_id=122

        """
        if len(new_arff) == 0:
            new_arff = "%s__%s.arff" % (old_arff[:old_arff.rfind('.')], filter_type)

        ### NOTE: these conditions are ordered starting with most recent additions:
        if filter_type == "exclude_non_debosscher":
            excluded_source_select_str = """SELECT  Sources.Source_ID FROM    Sources
                LEFT JOIN Classes ON Sources.Class_ID = Classes.Class_ID
                WHERE   Sources.project_id != 122"""
        elif filter_type == "exclude_catalina_lowconf_LSST":
            # NOTE: it seems the original source .arff does not have LSST (114) sources anyway:
            #             $HOME/scratch/train_output_20100517_dotastro_xml_with_features.arff
            excluded_source_select_str = """SELECT  Sources.Source_ID FROM    Sources
                LEFT JOIN Classes ON Sources.Class_ID = Classes.Class_ID
                WHERE   (Sources.Source_Class_Confidence < 0.9 AND
                         Sources.project_id = 115) 
                      OR Sources.project_id = 114
                      OR Sources.project_id = 12 """
        elif filter_type == "exclude_catalina_lowconf":
            excluded_source_select_str = """SELECT  Sources.Source_ID FROM    Sources
                LEFT JOIN Classes ON Sources.Class_ID = Classes.Class_ID
                WHERE   (Sources.Source_Class_Confidence < 0.9 AND
                        Sources.project_id = 115)
                     OR Sources.project_id = 12"""
        elif filter_type == "exclude_all_catalina":
            excluded_source_select_str = """SELECT  Sources.Source_ID FROM    Sources
                LEFT JOIN Classes ON Sources.Class_ID = Classes.Class_ID
                WHERE   Sources.project_id = 115
                     OR Sources.project_id = 12"""
        elif filter_type == "only_catalina_highconf":
            excluded_source_select_str = """SELECT  Sources.Source_ID FROM    Sources
                LEFT JOIN Classes ON Sources.Class_ID = Classes.Class_ID
                WHERE   (Sources.project_id != 115) OR ((Sources.project_id = 115) AND (Sources.Source_Class_Confidence < 0.9))"""
    
        self.generate_dotastro_arff_using_subset_from_db_query(old_arff=old_arff,
                                                               new_arff=new_arff,
                                                               select_str=excluded_source_select_str)


    def get_sciclass_lookup_dict(self):
        """ Fill dicts:

        classid_shortname[<classid>] = shortname

        shortname_longname[<shortname>] = longname

        shortname_parentshortname[<shortname>] = parent_shortname

        shortname_isactive[<shortname>] = class_is_active

        shortname_ispublic[<shortname>] = class_is_public


        TODO: number of sources in dotastro for a <shortname>

        TODO: number of *period-foldable* sources in dotastro for a <shortname>

        """        
        out_dict = {'classid_shortname':{},
                    'shortname_longname':{},
                    'longname_shortname':{},
                    'shortname_parent_id':{},
                    'shortname_parentshortname':{},
                    'shortname_isactive':{},
                    'shortname_ispublic':{},
                    'shortname_nsrcs':{}}

        self.make_tutor_db_connection()
        
        select_str = "SELECT class_id, class_id_parent, class_short_name, class_name, class_is_active, class_is_public FROM classes"
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()
        for row in results:
            (class_id, class_id_parent, class_shortname, class_name, class_is_active, class_is_public) = row
            out_dict['classid_shortname'][class_id] = class_shortname
            out_dict['shortname_longname'][class_shortname] = class_name
            out_dict['longname_shortname'][class_name] = class_shortname
            out_dict['shortname_parent_id'][class_shortname] = class_id_parent
            out_dict['shortname_isactive'][class_shortname] = class_is_active
            out_dict['shortname_ispublic'][class_shortname] = class_is_public

        ### Add the top class, which seems to connect the "moving source", "variable stars [Alt]", "Variable Stars", "Variable Sources (Non-stellar)" together
        out_dict['classid_shortname'][0L] = "_varstar_" # top grandfather science class
        out_dict['shortname_longname']["_varstar_"] = "_varstar_" # top grandfather science class
        out_dict['longname_shortname']["_varstar_"] = "_varstar_" # top grandfather science class
        out_dict['shortname_isactive']["_varstar_"] = "No"
        out_dict['shortname_ispublic']["_varstar_"] = "No"
        out_dict['shortname_nsrcs']["_varstar_"] = 0

        #import pdb; pdb.set_trace()
        ### 'Chemically Peculiar Stars':'CP' is only a Deboscher(12) project-class and has no parents or equivalent science classes.  So, we hardcode "_varstar_" as the parent
        out_dict['classid_shortname'][1000000L] = "Chemically Peculiar Stars"
        out_dict['shortname_longname']["CP"] = "Chemically Peculiar Stars"
        out_dict['longname_shortname']["Chemically Peculiar Stars"] = "CP" # top grandfather science class
        out_dict['shortname_isactive']["CP"] = "No"
        out_dict['shortname_ispublic']["CP"] = "No"
        out_dict['shortname_nsrcs']["CP"] = 0
        out_dict['shortname_parent_id']["CP"] = 0L

        ### Add counts of sources: select * FROM sources WHERE   EXISTS(SELECT Observations.Observation_ID FROM Observations WHERE Observations.Source_ID = sources.Source_ID) limit 10;

        for class_id, class_shortname in out_dict['classid_shortname'].iteritems():
            if class_id == 0L:
                continue # skip
            select_str = "SELECT count(*) FROM sources WHERE class_id=%d" % (class_id)
            self.cursor.execute(select_str)
            results = self.cursor.fetchall()
            if len(results) > 0:
                out_dict['shortname_nsrcs'][class_shortname] = results[0][0]

        ### Replace old classes/shortnames with canonical shortname/class
        classid_list = out_dict['classid_shortname'].keys()
        for class_id in classid_list:
            class_shortname = out_dict['classid_shortname'][class_id]
            if (self.pars['canonical_shortnames'].has_key(class_shortname) and
                           out_dict['shortname_longname'].has_key(class_shortname)):
                out_dict['shortname_nsrcs'][self.pars['canonical_shortnames'][class_shortname]] += \
                                           out_dict['shortname_nsrcs'][class_shortname]
                ### ??? Why are these pop()'d?
                #     - so that the Cytoscape csv files dont have obsolete classes
                #  - but: I would like to have this information available for finding the parents of these ....
                #out_dict['classid_shortname'].pop(class_id)
                out_dict['shortname_longname'].pop(class_shortname)
                out_dict['shortname_parent_id'].pop(class_shortname)
                out_dict['shortname_isactive'].pop(class_shortname)
                out_dict['shortname_ispublic'].pop(class_shortname)

        ### Add parent shortnames:
        for class_shortname, class_parent_id in out_dict['shortname_parent_id'].iteritems():
            parent_shortname = out_dict['classid_shortname'][class_parent_id]
            if self.pars['canonical_shortnames'].has_key(parent_shortname):
                parent_shortname = self.pars['canonical_shortnames'][parent_shortname]
            out_dict['shortname_parentshortname'][class_shortname] = parent_shortname


        self.db.close()
        return out_dict


    def generate_cytoscape_viewable_files(self, sciclass_lookup):
        """ Generate data files which cytoscape can read, in order to
        visualize the science class heirarchy.

        """ 
        fp_cyto_class_parent = open(self.pars['cyto_class_parent_fpath'], 'w')
        #fp_cyto_class_attrib = open(self.pars['cyto_class_attrib_fpath'], 'w')

        for class_shortname, parent_shortname in sciclass_lookup['shortname_parentshortname'].iteritems():

            fp_cyto_class_parent.write("%s\t%s\t%s\t%s\t%s\t%s\n" % (class_shortname, parent_shortname,
                                                sciclass_lookup['shortname_isactive'][class_shortname],
                                                sciclass_lookup['shortname_ispublic'][class_shortname],
                                                sciclass_lookup['shortname_longname'][class_shortname],
                                                sciclass_lookup['shortname_nsrcs'][class_shortname]))
            #fp_cyto_class_attrib.write("%s\t%s\t%s\t%s\n" % (class_shortname,
            #                                   sciclass_lookup['shortname_isactive'][class_shortname],
            #                                   sciclass_lookup['shortname_ispublic'][class_shortname],
            #                                   sciclass_lookup['shortname_longname'][class_shortname]))
        fp_cyto_class_parent.close()
        #fp_cyto_class_attrib.close()

    
    #OBSOLETE / UNUSED:
    def create_new_dotastro_arff_using_xmldir_and_filters(self):
        """ Using generate_weka_classifiers.py --train_mode and an vosource xml dir
        and some SQL filter of certain sources, recreate a new .arff.

        This is useful if we want to pass specific parameters to generate_weka_classifiers.py
           -> like the number-of-sources cut.

        """
        # TODO: SQL the dotastro sources we are interested in, use srcids to copy into
        #      a seperate directory
        # TODO: have ipython restarted
        # TODO: ./generate_weka_classifiers.py --train_mode --train_xml_dir=/home/pteluser/scratch/vosource_xml_writedir --train_arff_path=/home/pteluser/scratch/dotastro_ge3srcs.arff --n_sources_needed_for_class_inclusion=3
        pass


    def get_debosscher_sources_in_dirs(self):
        """ Get all source names for sources found in extracted Debosscher tarball dirs.
        """
        self.pars.update({'debosscher_data_dirpaths':{ \
                              'ogle':'/home/pteluser/analysis/debosscher_20100707/TS-OGLE',
                              'hip':'/home/pteluser/analysis/debosscher_20100707/TS-HIPPARCOS'}})

        source_list = []
        short_fpath_lookup = {}

        lc_fname_list = glob.glob("%s/*.hip" % (self.pars['debosscher_data_dirpaths']['hip']))
        for fpath in lc_fname_list:
            fname = fpath[fpath.rfind('/')+1:]
            id_str = fname[fname.find('-')+1:fname.rfind('.')]
            src_name_str = "HIP %s" % (id_str)
            source_list.append(src_name_str)

            ##
            i_last_slash = fpath.rfind('/')
            i_2ndlast_slash = fpath[:i_last_slash].rfind('/')
            short_fpath_lookup[src_name_str] = fpath[i_2ndlast_slash+1:] 
            #print '!!!', src_name_str, fpath[i_2ndlast_slash+1:] 
            ##

        lc_fname_list = glob.glob("%s/*.dat" % (self.pars['debosscher_data_dirpaths']['ogle']))
        for fpath in lc_fname_list:
            fname = fpath[fpath.rfind('/')+1:]
            if fname.count('.') > 1:
                id_str = fname[:fname.rfind('.')]
                src_name_str = "%s" % (id_str)
                source_list.append(src_name_str)
            else:
                id_str = fname[:fname.rfind('.')]
                #src_name_str = "HD %s" % (id_str)
                src_name_str = "%s" % (id_str) # generally source_name in dotastro like 'OGLE SMC-SC11 13365'
                source_list.append(src_name_str)

            ##
            i_last_slash = fpath.rfind('/')
            i_2ndlast_slash = fpath[:i_last_slash].rfind('/')
            short_fpath_lookup[src_name_str] = fpath[i_2ndlast_slash+1:] 
            #print '!!!', src_name_str, fpath[i_2ndlast_slash+1:] 
            ##

        return {'tar_src_list':source_list,
                'short_fpath_lookup':short_fpath_lookup}


    def hack_find_deboscher_sources_not_in_arff(self):
        """ This summarizes which sources exist in .arff file, which exist in dotastro, and which exist in Debosscer tarball directories.
        """
        self.pars.update({'arff_fpath':'/home/pteluser/scratch/dotastro_ge1srcs_period_nonper.arff'})

        tar_dict = self.get_debosscher_sources_in_dirs()

        self.make_tutor_db_connection()
        
        #select_str = """SELECT  Sources.Source_ID FROM    Sources
        #        LEFT JOIN Classes ON Sources.Class_ID = Classes.Class_ID
        #        WHERE   Sources.project_id = 12"""
        select_str = """SELECT  Sources.Source_ID, project_classes.pclass_name, Sources.source_name
                FROM Sources
                JOIN project_classes USING (pclass_id)
                WHERE   Sources.project_id = 122"""
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()
        all_srcid_list = []
        class_name_lookup = {}
        source_name_lookup = {}
        for row in results:
            srcid = str(row[0])
            all_srcid_list.append(srcid)
            class_name_lookup[srcid] = row[1]
            # need to change OGLE names like 'OGLE SMC-SC10 85943', which are labeled in tar as: '85943.dat'
            source_name = row[2]
            if ((source_name.count('OGLE') >= 1) and
                (source_name.count(' ') >= 2)):
                source_name_lookup[srcid] = source_name[source_name.rfind(' ')+1:]
            else:
                source_name_lookup[srcid] = source_name

        ### Now parse ids from (1295 / 1641) arff file.
        deb_in_arff_srcid_list = []
        lines = open(self.pars['arff_fpath']).readlines()
        for line in lines[43:]:
            line_split = line.split(',')
            srcid = line_split[0].strip()
            if srcid in all_srcid_list:
                deb_in_arff_srcid_list.append(srcid)

        nonarff_srcid_list = []
        for srcid in all_srcid_list:
            if not srcid in deb_in_arff_srcid_list:
                nonarff_srcid_list.append(srcid)
                #print 'Not in arff:', srcid, class_name_lookup[srcid]
            else:
                print '          IN arff,  IN DotA: %7s\t%s\t%s' % (srcid, source_name_lookup[srcid], class_name_lookup[srcid])
                
        nonarff_srcid_list.sort()

        for srcid in nonarff_srcid_list:
            if source_name_lookup[srcid] in tar_dict['tar_src_list']:
                print ' IN tar, NOT arff,  IN DotA: %7s\t%s\t%s' % (srcid, source_name_lookup[srcid], class_name_lookup[srcid])
            else:
                print 'NOT tar, NOT arff,  IN DotA: %7s\t%s\t%s' % (srcid, source_name_lookup[srcid], class_name_lookup[srcid])

        source_names_in_dotastro = source_name_lookup.values()
        for source_name in tar_dict['tar_src_list']:
            if source_name not in source_names_in_dotastro:
                print ' IN tar, NOT arff, NOT DotA: %7s\t%s\t%s' % ('', source_name, tar_dict['short_fpath_lookup'][source_name])

        #for srcid in nonarff_srcid_list:
        #    print 'Not in arff:', srcid, source_name_lookup[srcid], class_name_lookup[srcid]
        #import pprint
        #pprint.pprint(nonarff_srcid_list)
        print tar_dict['tar_src_list']
        print 
        print len(nonarff_srcid_list), 'out of:', len(all_srcid_list), '(', len(all_srcid_list) - len(nonarff_srcid_list), ')'
        print
                




if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog cmd [options]")
    parser.add_option("-o","--old_arff_fpath",
                      dest="old_arff_fpath", 
                      action="store",
                      default=os.path.expandvars('$HOME/scratch/train_output_20100517_dotastro_xml_with_features.arff'),
                      help="")
    (options, args) = parser.parse_args()


    pars = {'cyto_class_parent_fpath':os.path.expandvars('$HOME/scratch/cyto_dotastro_class_parent.dat'),
            'cyto_class_attrib_fpath':os.path.expandvars('$HOME/scratch/cyto_dotastro_class_attrib.dat')}

    DotastroSciclassTools = Dotastro_Sciclass_Tools(pars=pars)

    ##### This allows analysis of which Debosscher sources have lightcurve data in Dotastro/xmls/.arff:
    #DotastroSciclassTools.hack_find_deboscher_sources_not_in_arff()
    #sys.exit()
    #####

    #old_arff = os.path.expandvars('$HOME/scratch/train_output_20100517_dotastro_xml_with_features.arff')
    #old_arff = os.path.expandvars('$HOME/scratch/dotastro_ge1srcs.arff')
    old_arff = os.path.expandvars(options.old_arff_fpath)
    new_arff = '' #NULL MEANS AUTOGENERATED FILENAME USING OLD ARFF FILE#
    #new_arff = os.path.expandvars('$HOME/scratch/train_output_20100517_dotastro_xml_with_features__nolowconf_catalina.arff')

    filter_types = ["exclude_non_debosscher",
                    "exclude_catalina_lowconf_LSST",
                    "exclude_catalina_lowconf",
                    "exclude_all_catalina",
                    "only_catalina_highconf"]

    for filter_type in filter_types:
        print filter_type
        DotastroSciclassTools.generate_dotastro_sql_filterd_arff(old_arff=old_arff, new_arff=new_arff,
                                                                 filter_type=filter_type)

    #sciclass_lookup = DotastroSciclassTools.get_sciclass_lookup_dict()

    #DotastroSciclassTools.generate_cytoscape_viewable_files(sciclass_lookup)

    print 
