#!/usr/bin/env python
""" Do a couple tasks needed for Debosscher paper tables (20101118)

"""
import os, sys
import pprint
import MySQLdb
import cPickle
import gzip
import analysis_deboss_tcp_source_compare
import glob
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                'Algorithms'))
import simbad_id_lookup

### This is a list of science class associations which Josh discerned when looking at double classified sources:
josh_classifs = {\
5267:{'tutorid':148038L, 'tcp_class':'LBV',  'comment':'2nd tutorid=161329L'},
19893:{'tutorid':148103L, 'tcp_class':'GDOR', 'comment':'2nd tutorid=148841L'},
23428:{'tutorid':148137L, 'tcp_class':'LBV',  'comment':'2nd tutorid=161330L'},
26403:{'tutorid':148174L, 'tcp_class':'HAEBE','comment':'2nd tutorid=161337L'},
54413:{'tutorid':148375L, 'tcp_class':'HAEBE','comment':'2nd tutorid=161335L'},
86624:{'tutorid':148583L, 'tcp_class':'LBV', 'comment':'2nd tutorid=161328L'},
89956:{'tutorid':148614L, 'tcp_class':'LBV', 'comment':'2nd tutorid=161327L'},
89963:{'tutorid':148615L, 'tcp_class':'LBV', 'comment':'2nd tutorid=161326L'}}

# 20101202: dstarr finds that some of the new-sources (not found in project=122 tutor) have double classes
#       and a specific dict is needed in this case to disambiguate the sources for these classes:
#   NOTE: class=='' means we skip this source
#dstarr_newsrc_classes = {30326:'',#'MIRA',# simbad found 'mira', debossfile list.dat: 'RVTAU MIRA'
#                         53461:''}#'BE'} #simbad finds Be*, debossfile list.dat: 'WR    LBV'
dstarr_newsrc_classes = {26304:'CP', #HD 37151 #joey 20100211 email of 11 srcs sent to Josh
                         27400:'RRAB',
                         30326:'RVTAU',
                         33165:'WR', # HD 50896
                         53461:'WR', # HD 94910
                         54283:'PVSG', # HD 96548
                         75377:'PVSG'}#HD 136488


simbad_classes = { \
8:'Mira',
320:'RRLyr',
781:'Mira',
1067:'PulsV*bCep',
1162:'deltaCep',
1222:'RRLyr',
4541:'RRLyr',
6115:'RRLyr',
6325:'semi-regV*',
6539:'PulsV*delSct',
7149:'RRLyr',
7398:'RRLyr',
7588:'Be*',
8210:'RotV*alf2CVn',
9306:'Mira',
9361:'RRLyr',
11390:'PulsV*delSct',
12113:'PulsV*delSct',
12193:'Mira',
12235:'EB*Algol',
12387:'PulsV*bCep',
12817:'deltaCep',
13064:'semi-regV*',
14856:'RRLyr',
16126:'Mira',
16826:'Be*',
19762:'**',
19978:'deltaCep',
20045:'Mira',
20922:'Be*',
22024:'Be*',
22127:'Mira',
22256:'Mira',
23165:'Mira',
23602:'Rapid_Irreg_V*',
23733:'RotV*alf2CVn',
23972:'Be*',
24105:'deltaCep',
24126:'Mira',
24281:'deltaCep',
24471:'RRLyr',
24500:'deltaCep',
25281:'**',
26064:'Be*',
26594:'Be*',
28945:'deltaCep',
29441:'Mira',
29655:'**',
29771:'Be*',
30326:'Mira',
31137:'**',
31400:'RRLyr',
32292:'Be*',
32516:'deltaCep',
32675:'PulsV*WVir',
32759:'Be*',
34360:'**',
34743:'RRLyr',
34895:'deltaCep',
35037:'Be*',
35281:'RRLyr',
35487:'EB*Algol',
35795:'Be*',
35951:'Be*',
36088:'deltaCep',
36394:'Mira',
36500:'PulsV*bCep',
36547:'semi-regV*',
37207:'deltaCep',
37440:'EB*Algol',
37459:'Mira',
38241:'deltaCep',
38772:'Mira',
39144:'deltaCep',
39172:'Be*',
39666:'deltaCep',
40285:'EB*betLyr',
42257:'deltaCep',
42794:'EB*Algol',
42799:'PulsV*bCep',
43589:'Star',
43778:'WR*',
44093:'V*',
44213:'Be*',
45091:'V*',
47522:'Be*',
47886:'Mira',
49751:'Mira',
49934:'Be*',
50676:'**',
50697:'Mira',
51576:'Be*',
51894:'deltaCep',
52308:'WR*',
52742:'Be*',
53461:'Be*',
54066:'deltaCep',
54891:'deltaCep',
55726:'deltaCep',
55825:'RRLyr',
56327:'V*',
56350:'RRLyr',
56379:'Be*',
56409:'RRLyr',
56898:'PulsV*WVir',
57009:'Mira',
57498:'V*',
57625:'RRLyr',
57669:'Be*',
58002:'V*',
58520:'PulsV*delSct',
59093:'PulsV*delSct',
59173:'Be*',
59196:'Be*',
59232:'Be*',
59995:'RRLyr',
60189:'Be*',
61009:'Mira',
61029:'RRLyr',
61281:'Be*',
61286:'Mira',
61809:'RRLyr',
62956:'RotV*alf2CVn',
63054:'RRLyr',
64844:'PulsV*delSct',
65063:'RRLyr',
65445:'RRLyr',
65531:'PulsV*WVir',
65547:'RRLyr',
66100:'Mira',
66189:'deltaCep',
66657:'PulsV*bCep',
67359:'Mira',
67472:'Be*',
67653:'RRLyr',
69346:'Mira',
69759:'RRLyr',
70590:'Mira',
71352:'Be*',
71995:'V*',
72300:'Mira',
72721:'Cepheid',
74556:'RRLyr',
75141:'PulsV*bCep',
75170:'Mira',
76013:'Be*',
77663:'RRLyr',
77913:'deltaCep',
78207:'Be*',
78317:'Orion_V*',
78417:'RRLyr',
78539:'RRLyr',
78771:'deltaCep',
80569:'Be*',
83304:'Mira',
83323:'Be*',
83582:'Mira',
85079:'Be*',
85792:'Be*',
86414:'PulsV*bCep',
87314:'EB*Algol',
89164:'PulsV*bCep',
89290:'V*',
89596:'deltaCep',
90474:'Mira',
91389:'**',
92013:'deltaCep',
92491:'deltaCep',
92609:'Be*',
92862:'semi-regV*',
93476:'RRLyr',
93990:'deltaCep',
94289:'WR*',
94706:'Mira',
95032:'Mira',
95118:'deltaCep',
95929:'Be*',
96031:'Mira',
96458:'deltaCep',
96580:'Mira',
98212:'deltaCep',
98217:'deltaCep',
98265:'RRLyr',
98546:'PulsV*WVir',
98675:'Cepheid',
99303:'Be*',
100048:'Mira',
100214:'WR*',
102082:'Mira',
102088:'WR*',
103803:'V*',
104015:'Mira',
104986:'PulsV*WVir',
105026:'RRLyr',
105138:'Be*',
106649:'RRLyr',
106723:'Be*',
107004:'**',
107935:'RRLyr',
108975:'Be*',
110451:'Mira',
110697:'Mira',
110836:'WR*',
111278:'gammaDor',
111633:'WR*',
112784:'Mira',
113327:'Be*',
113561:'semi-regV*',
113652:'Mira',
114114:'Mira',
114995:'Orion_V*',
116958:'RRLyr',
117863:'semi-regV*'}


simbadclass_to_debclass = { \
 'Be*':'BE',
 'V*':'',
 'Mira':'MIRA',
 'deltaCep':'CLCEP',
 'RRLyr':'RRAB',
 'RotV*alf2CVn':'',
 'PulsV*WVir':'PTCEP',
 'PulsV*bCep':'BCEP',
 'Rapid_Irreg_V*':'',
 '**':'',
 'EB*Algol':'EB',
 'Star':'',
 'WR*':'WR',
 'semi-regV*':'SR',
 'PulsV*delSct':'DSCUT',
 'gammaDor':'GDOR',
 'Cepheid':'CLCEP',
 'Orion_V*':'TTAU',
 'EB*betLyr':'EB'}

### This was retrieved from previous SIMBAD database queries:
simbad_hd_hip_dict = { \
    'HD 2724':'HIP 2388',
    'HD 2842':'HIP 2510',
    'HD 4919':'HIP 3949',
    'HD 21071':'HIP 15988',
    'HD 24587':'HIP 18216',
    'HD 26326':'HIP 19398',
    'HD 28475':'HIP 20963',
    'HD 269006':'HIP 23428',
    'HD 34282':'HIP 24552',
    'HD 34798':'HIP 24825',
    'HD 34797':'HIP 24827',
    'HD 35715':'HIP 25473',
    'HD 37151':'HIP 26304',
    'HD 46328':'HIP 31125',
    'HD 50896':'HIP 33165',
    'HD 52918':'HIP 33971',
    'HD 59693':'HIP 36521',
    'HD 61068':'HIP 37036',
    'HD 63949':'HIP 38159',
    'HD 64365':'HIP 38370',
    'HD 64722':'HIP 38438',
    'HD 69715':'HIP 40791',
    'HD 77581':'HIP 44368',
    'HD 78616':'HIP 44790',
    'HD 81009':'HIP 45999',
    'HD 88824':'HIP 50070',
    'HD 90177':'HIP 50843',
    'HD 92207':'HIP 52004',
    'HD 92287':'HIP 52043',
    'HD 96008':'HIP 54060',
    'HD 96548':'HIP 54283',
    'HD 102567':'HIP 57569',
    'HD 107447':'HIP 60259',
    'HD 107805':'HIP 60455',
    'HD 108100':'HIP 60571',
    'HD 112044':'HIP 62986',
    'HD 112481':'HIP 63250',
    'HD 113904':'HIP 64094',
    'HD 123515':'HIP 69174',
    'HD 126341':'HIP 70574',
    'HD 136488':'HIP 75377',
    'HD 138003':'HIP 75641',
    'HD 142527':'HIP 78092',
    'HD 147010':'HIP 80024',
    'HD 147985':'HIP 80563',
    'HD 156385':'HIP 84757',
    'HD 160529':'HIP 86624',
    'HD 163296':'HIP 87819',
    'HD 164975':'HIP 88567',
    'HD 165763':'HIP 88856',
    'HD 170756':'HIP 90697',
    'HD 177863':'HIP 93887',
    'HD 179588':'HIP 94377',
    'HD 181558':'HIP 95159',
    'HD 206540':'HIP 107173',
    'HD 207223':'HIP 107558',
    'HD 210111':'HIP 109306',
    'HD 214441':'HIP 111833',
    'HD 223640':'HIP 117629',
    'HD 27290':'HIP 19893',
    'HD 160529':'HIP 86624',
    'HD 269006':'HIP 23428',
    'HD 35715':'HIP 25473'}


class Deb_Paper_Analysis(analysis_deboss_tcp_source_compare.Analysis_Deboss_TCP_Source_Compare):
    """
    Since this inherits Analysis_Deboss_TCP_Source_Compare()  class, I'm assuming that __init__() is used and
    is used to load database connections.

    """

    def main(self):
        """
        """
        pkl_fpath = '/home/pteluser/scratch/debosscher_paper_tools.pkl.gz'
        if not os.path.exists(pkl_fpath):
            debos_tcp_dict = self.get_deboss_dotastro_source_lookup__modified()
            fp = gzip.open(pkl_fpath,'wb')
            cPickle.dump(debos_tcp_dict, fp, 1) # ,1) means a binary pkl is used.
            fp.close()
        else:
            fp = gzip.open(pkl_fpath,'rb')
            debos_tcp_dict = cPickle.load(fp)
            fp.close()
            
        ### NOTE: it seems there are no sources with more than 1:1 srcid matchups (so don't need to do the following):
        #for tcp_srcid, deb_srcid_list in debos_tcp_dict['dotastro_srcid_to_debos_srcname'].iteritems():
        #    if len(deb_srcid_list) > 1:
        #        print tcp_srcid, deb_srcid_list



        ### Retrieve the n_epochs for each srcid from TCP RDB
        ### NOTE: it seems that all of the sources in debos_tcp_dict['dotastro_srcid_to_debos_srcname']
        ####   have more than 0 epochs in TCP
        debos_tcp_dict['srcid_nepochs'] = {}
        for tcp_srcid, deb_srcid_list in debos_tcp_dict['dotastro_srcid_to_debos_srcname'].iteritems():
            select_str = "select nobjs from srcid_lookup where src_id = %d" % (tcp_srcid + 100000000) 
            self.tcp_cursor.execute(select_str)
            results = self.tcp_cursor.fetchall()
            if len(results) == 0:
                print "NONE!!!:", tcp_srcid
            elif results[0][0] < 1:
                print "NO epochs in TCP", tcp_srcid, results[0], deb_srcid_list, debos_tcp_dict['dotastro_srcid_to_attribfiles'][tcp_srcid]
            else:
                debos_tcp_dict['srcid_nepochs'][tcp_srcid] = results[0][0]

        self.determine_deboss_classes_for_srcids(debos_tcp_dict)
        
        #20110102disable# final_assocations_dict = self.determine_which_joey_downloaded_hip_is_not_in_tutor(debos_tcp_dict)

        new_debos_tcp_dict = self.confirm_idsdebdat_in_tutor()

        #self.count_sources(debos_tcp_dict)
        self.count_sources(new_debos_tcp_dict)


        if 0:
            final_assocations_dict = self.determine_which_joey_downloaded_hip_is_not_in_tutor(debos_tcp_dict)

            # # # TODO: need to add ogle accociations to final_assocations_dict
            #   -> ensure that classifications are correct.

            pkl_fpath = '/home/pteluser/scratch/debosscher_paper_tools__assocdict.pkl'
            if os.path.exists(pkl_fpath):
                os.system('rm ' + pkl_fpath)
            fp = open(pkl_fpath, 'w')
            cPickle.dump(final_assocations_dict, fp)
            fp.close()
            import pdb; pdb.set_trace()




        ### TODO: count sources we have per deboss class, compare with pars['deb_src_counts']
        ### TODO: use pars['debosscher_class_lookup'] and .... ms.text table to determine how many classes debosscher orig had


        ### TODO: count how many sources for each survey

        print


    def determine_which_joey_downloaded_hip_is_not_in_tutor(self, debos_tcp_dict):
        """ 

        It seems "HD xxxx" sources also may have HIPPARCOS numbers not listed in Debos datasets

        """
        all_hipids_dict = {}

        joey_hip_xmls_dirpath = '/home/pteluser/scratch/debos_newHIPP_data/xmls'
        files = glob.glob("%s/*xml" % (joey_hip_xmls_dirpath))
        joey_hip_ids = []
        for fpath in files:
            fname = fpath[fpath.rfind('/')+1:]
            hip_str = fname[fname.find('HIP') + 3 :fname.rfind('.')]
            joey_hip_ids.append(int(hip_str))
            all_hipids_dict[int(hip_str)] = {'xml':fname}

        # I actually want to do this in reverse: look for all HIP
        tcpid_to_hipid = {}
        for tcp_id, sublist in debos_tcp_dict['dotastro_srcid_to_debos_srcname'].iteritems():
            hipid_str_list = sublist
            if not debos_tcp_dict['tcpsrcid_surveys'].has_key(tcp_id):
                hipid_str_list = []
                for elem in sublist:
                    html_str = simbad_id_lookup.query_html(src_name=elem)
                    hip_ids = simbad_id_lookup.parse_html_for_ids(html_str, instr_identifier='HIP')
                    print "NOT in debos_tcp_dict['tcpsrcid_surveys'], adding:", hip_ids, 'tcp_id:', tcp_id, 'deb_id:', sublist
                    hipid_str_list.extend(hip_ids)
                    #import pdb; pdb.set_trace()
                    # TODO: want to store that this is a deboss source which is HIP, but no tcp_id
                if len(hipid_str_list) == 0:
                    print '!!!', tcp_id, sublist
                    
            elif debos_tcp_dict['tcpsrcid_surveys'][tcp_id] != 'hip':
                continue
            assert(len(hipid_str_list) == 1)

            if 'HD' in hipid_str_list[0]:
                if simbad_hd_hip_dict.has_key(hipid_str_list[0]):
                    hipid_str_list = [simbad_hd_hip_dict[hipid_str_list[0]]]
                else:
                    html_str = simbad_id_lookup.query_html(src_name=hipid_str_list[0])
                    hip_ids = simbad_id_lookup.parse_html_for_ids(html_str, instr_identifier='HIP')
                    print "HD with Simbad HIP: ", hip_ids, 'tcp_id:', tcp_id, 'deb_id:', sublist
                    hipid_str_list = hip_ids
                

            ### So now we can store hip_id:tcp_id
            hipid_str = hipid_str_list[0][hipid_str_list[0].find('HIP ') + 4:]

            tcpid_to_hipid[tcp_id] = int(hipid_str)

            if not all_hipids_dict.has_key(int(hipid_str)):
                #all_hipids_dict[int(hipid_str)] = ['NONE', tcp_id, sublist[0], debos_tcp_dict['tcpsrcid_classes'][tcp_id]]
                all_hipids_dict[int(hipid_str)] = {'xml':'NO XML', 'tutorid':tcp_id, 'tutor_name':sublist[0], 'tcp_class':debos_tcp_dict['tcpsrcid_classes'][tcp_id]}
            else:
                #all_hipids_dict[int(hipid_str)].extend([tcp_id, sublist[0], debos_tcp_dict['tcpsrcid_classes'][tcp_id]])
                if all_hipids_dict[int(hipid_str)].has_key('tutorid'):
                    #all_hipids_dict[int(hipid_str)].update({'extra':[tcp_id, sublist[0], debos_tcp_dict['tcpsrcid_classes'][tcp_id]], 'comment':"extra tutor srcid"})
                    all_hipids_dict[int(hipid_str)].update({'comment':"extra tutor srcid"})
                else:
                    all_hipids_dict[int(hipid_str)].update({'tutorid':tcp_id, 'tutor_name':sublist[0], 'tcp_class':debos_tcp_dict['tcpsrcid_classes'][tcp_id]})
 


        ##### Some summary metrics:
        #import pprint
        #pprint.pprint(all_hipids_dict)
        hids_sort = all_hipids_dict.keys()
        hids_sort.sort()
        #for hid in hids_sort:
        #    hlist = all_hipids_dict[hid]
        #    print hid, hlist

        joey_hipids_not_in_tutor = []
        for hip_id in joey_hip_ids:
            if hip_id not in tcpid_to_hipid.values():
                joey_hipids_not_in_tutor.append(hip_id)

        print
        print "num of hip_ids that joey found but which are not in TUTOR:%d" % (len(joey_hipids_not_in_tutor))

        print "There are 845 HIP sources with TCP_ids, 1044 Joey HIP sources"
        print "this means there should be 199 HIP sources which joey found which are not in TCP"
        print "There are supposedly 272 joey sources which do not have TCP matches, using above compare algos"
        print
        
        ##### Summary of final associations for each joey-xml file:
        hids_sort = all_hipids_dict.keys()
        hids_sort.sort()
        final_hipids_dict = {}

        (debos_classifs, position_dict) = self.get_deboss_listdat_classifs()

        return_dict = {}
        ### Josh says remove one multiclass source
        #remove_hipids = [104029, 25473, 34042, 36750, 39009, 57812, 58907]
        remove_hipids = [104029, 25473, 34042, 36750, 39009, 57812, 58907, 26304, 33165, 34042, 36750, 39009, 53461, 57812, 58907, 75377, 104029]
        for hipid in remove_hipids:
            try:
                hids_sort.remove(hipid)
            except:
                pass

        for hid in hids_sort:
            # # # # # # # # #
            #if hid == 26403:
            #    import pdb; pdb.set_trace()
            hdict = all_hipids_dict[hid]
            if josh_classifs.has_key(hid):
                hdict.update(josh_classifs[hid])
            if hdict.has_key('tcp_class'):
                if type(hdict['tcp_class']) == type([]):
                    #assert(len(hdict['tcp_class']) == 1)
                    if len(hdict['tcp_class']) == 2:
                        print "DOUBLE CLASS:", hdict
                        hdict['tcp_class'] = [hdict['tcp_class'][0]]
                    elif len(hdict['tcp_class']) == 0:
                        print "$$$ NO CLASS$$$:", hdict
                else:
                    hdict['tcp_class'] = [hdict['tcp_class']]
            else:
                if not hid in simbad_classes.keys():
                    a_str = simbad_id_lookup.query_votable(src_name = "HIP %d" % (hid))
                    sci_class = simbad_id_lookup.parse_class(a_str)
                else:
                    sci_class = simbad_classes[hid]
                deb_sci_class = simbadclass_to_debclass[sci_class]

                ### ok, now check whether this corresponds to debos_classifs
                test_srcname = "HIP %d" % (hid)
                if dstarr_newsrc_classes.has_key(hid):
                    deb_listdat_class = dstarr_newsrc_classes[hid]
                    if deb_listdat_class == '':
                        continue
                    if position_dict.has_key(test_srcname):
                        radec_dict = position_dict[test_srcname]
                    else:
                        html_str = simbad_id_lookup.query_html(src_name=test_srcname)
                        hd_ids = simbad_id_lookup.parse_html_for_ids(html_str, instr_identifier='HD')
                        if debos_classifs.has_key(hd_ids[0]):
                            radec_dict = position_dict[hd_ids[0]]
                        else:
                            print hid, "4_NO_MATCH", test_srcname, deb_src_class, hd_ids
                        
                elif debos_classifs.has_key(test_srcname):
                    #print hid, '1_deb:', debos_classifs[test_srcname], 'mine:', deb_sci_class
                    deb_listdat_class = debos_classifs[test_srcname]
                    radec_dict = position_dict[test_srcname]
                elif debos_classifs.has_key(hdict.get('tutor_name','xxx')):
                    #print hid, '2_deb:', debos_classifs[hdict['tutor_name']], 'mine:', deb_sci_class
                    deb_listdat_class = debos_classifs[hdict['tutor_name']]
                    radec_dict = position_dict[hdict['tutor_name']]
                else:
                    html_str = simbad_id_lookup.query_html(src_name=test_srcname)
                    hd_ids = simbad_id_lookup.parse_html_for_ids(html_str, instr_identifier='HD')
                    if debos_classifs.has_key(hd_ids[0]):
                        #print hid, '3_deb:', debos_classifs[hd_ids[0]], 'mine:', deb_sci_class
                        deb_listdat_class = debos_classifs[hd_ids[0]]
                        radec_dict = position_dict[hd_ids[0]]
                    else:
                        print hid, "4_NO_MATCH", test_srcname, deb_src_class, hd_ids

                if deb_listdat_class != deb_sci_class:
                    #print '!!!mismatch classes: ', hid, 'listdat:', deb_listdat_class, 'mine:', deb_sci_class
                    deb_sci_class = deb_listdat_class
                hdict['tcp_class'] = deb_sci_class
                hdict['comment'] = "%s class from SIMBAD=%s" % (hdict.get('comment',''), sci_class)
                hdict.update(radec_dict)
                #print hid, sci_class

            print "HIP=%d\txml='%s'\tclass='%s'\tTutorID=%s\tcomment='%s'\tra=%4.4f\tdec=%4.4f" % ( \
                       hid,
                       hdict['xml'],
                       hdict['tcp_class'],
                       hdict.get('tutorid',"''"),
                       hdict.get('comment',''),
                       hdict.get('ra',0.0),
                       hdict.get('dec',0.0))
            return_dict[hid] = hdict


        return return_dict
        
        #unmatched_deb_ids = []
        #for sublist in debos_tcp_dict['dotastro_srcid_to_debos_srcname'].values():
        #    unmatched_deb_ids.extend(sublist)

        """
        debid_joeyid_matches = {}
        for jhip_id in joey_hip_ids:
            # KLUDGEY due to inconsistant hip file names/strings:
            for debid in unmatched_deb_ids:
                if str(jhip_id) in debid:
                    debid_joeyid_matches[]
        """


    def get_deboss_listdat_classifs(self):
        """ Joey used this file to get all classifications for all 1044 HIP sources
        """
        deb_all_class_fpath = '/home/pteluser/analysis/debos_newHIPP_data/list.dat'
        # # #TODO: need to make sure these above classes correlate
        lines = open(deb_all_class_fpath).readlines()
        classif_dict = {}
        position_dict = {}
        for line in lines:
            source_name = line[:22].strip()
            class_name = line[50:63].strip()
            ra_str  = line[23:36]
            ra_tup = ra_str.split()
            ra = 15 * (float(ra_tup[0]) + float(ra_tup[1])/60. + float(ra_tup[2])/3600.)
            dec_str = line[37:50]
            dec_tup = dec_str.split()
            dec_sign = 1.
            if float(dec_tup[0]) < 0:
                dec_sign = -1.
            dec = dec_sign * (abs(float(dec_tup[0])) + float(dec_tup[1])/60. + float(dec_tup[2])/3600.)
            #print 'RA:', ra_str, ra, 'Dec:', dec_str, dec
            if (('HIP' in source_name) or ('HD' in source_name)):
                classif_dict[source_name] = class_name
                position_dict[source_name] = {'ra':ra, 'dec':dec}
                #print source_name, class_name
        return (classif_dict, position_dict)


    def fill_debclass_dict(self, data_fpath):
        """
        """
        debclass_dict = {}

        lines = open(data_fpath).readlines()
        for line in lines:
            vals = line.split()
            fname = vals[0]
            class_list = vals[1:]

            assert(not debclass_dict.has_key(fname))
            debclass_dict[fname] = class_list

        return debclass_dict


    def get_somefeats_for_tutor_sourceid(self, src_id=None):
        """ parse existing xmls with extracted features, to determine the source period
        """
        sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/feature_extract/Code/extractors')) 
        import mlens3

        d = mlens3.EventData("/home/pteluser/scratch/vosource_xml_writedir/%d.xml" % \
                             (100000000 + src_id))
        filt_list  = d.feat_dict.keys()
        filt_list.remove('multiband')
        filt = filt_list[0]
        f1_str = d.feat_dict[filt]['freq1_harmonics_freq_0']['val']['_text']
        f1_flt = float(f1_str)
        return {'f1':f1_flt,
                'nepoch':len(d.data['ts'][filt][0]['val'])}


    def count_sources(self, debos_tcp_dict):
        """ Count the number of sources we use for each sci-class and for each survey
        """

        class_count = {}
        class_nepoch_lists = {}
        class_period_lists = {}
        surveys_for_class = {}
        nepoch_list_per_survey = {'ogle':[], 'hip':[]}
        i = 0
        for src_id, class_list in debos_tcp_dict['tcpsrcid_classes'].iteritems():
            print "count_sources(%d/%d)" % (i, len(debos_tcp_dict['tcpsrcid_classes']))
            i+= 1
            #pre20110101# for a_class in class_list:
            #### So, post 20110101: we assume the first class is the chosen class
            for a_class in class_list[:1]:
                if not class_count.has_key(a_class):
                    class_count[a_class] = 0
                    class_nepoch_lists[a_class] = []
                    class_period_lists[a_class] = []
                    surveys_for_class[a_class] = {'ogle':0, 'hip':0}
                class_count[a_class] += 1
                surveys_for_class[a_class][debos_tcp_dict['tcpsrcid_surveys'][src_id]] += 1 # will count each class for double-clasified sources
                #class_nepoch_lists[a_class].append(debos_tcp_dict['srcid_nepochs'][src_id])
                feat_dict = self.get_somefeats_for_tutor_sourceid(src_id=src_id)
                freq1 = feat_dict['f1']
                nepochs = feat_dict['nepoch']
                nepoch_list_per_survey[debos_tcp_dict['tcpsrcid_surveys'][src_id]].append(nepochs)
                class_period_lists[a_class].append(freq1)
                class_nepoch_lists[a_class].append(nepochs)
                #try:
                #    class_period_lists[a_class].append(float(debos_tcp_dict['dotastro_srcid_to_debos_attribs'][src_id]['f1']))
                #except:
                #    freq1 = self.get_somefeats_for_tutor_sourceid(src_id=src_id)
                #    class_period_lists[a_class].append(freq1)
                #    print "No srcid=% in debos_tcp_dict['dotastro_srcid_to_debos_attribs']{}" % (src_id)

        survey_count = {'hip':0, 'ogle':0}
        survey_nepoch_lists = {'hip':[], 'ogle':[]}
        for src_id, survey in debos_tcp_dict['tcpsrcid_surveys'].iteritems():
            survey_count[survey] += 1
            survey_nepoch_lists[survey].append(debos_tcp_dict['srcid_nepochs'][src_id])


        #class_keys = class_count.keys()
        #class_keys.sort()
        #class_keys = ['BCEP', 'CLCEP', 'CP', 'DMCEP', 'DSCUT', 'EA', 'EB', 'ELL', 'EW', 'GDOR', 'HAEBE', 'LBOO', 'LBV', 'MIRA', 'PTCEP', 'PVSG', 'RRAB', 'RRC', 'RRD', 'RVTAU', 'SPB', 'SR', 'SXPHE', 'TTAU', 'WR', 'XB']
        class_keys = [ \
                      'MIRA',
                      'SR',
                      'RVTAU',
                      'CLCEP',
                      'PTCEP',
                      'DMCEP',
                      'RRAB',
                      'RRC',
                      'RRD',
                      'DSCUT',
                      'LBOO',
                      'BCEP',
                      'SPB',
                      'GDOR',
                      'BE',
                      'PVSG',
                      'CP',
                      'WR',
                      'TTAU',
                      'HAEBE',
                      'LBV', # s doradus
                      'ELL',
                      'EA', # Algol, beta persei
                      'EB', # beta lyrae
                      'EW', # w ursae major
                      ]
        print "class\t NLC\t %NLCdeb\tsurvey\t<Npts>\t min(f1)\t<f1>\t max(f1)"
        for deb_class in class_keys:
            count = class_count[deb_class]

            survey_n_total = surveys_for_class[deb_class]['ogle'] + surveys_for_class[deb_class]['hip']
            if ((surveys_for_class[deb_class]['ogle'] > 0) and
                (surveys_for_class[deb_class]['hip'] > 0)):
                survey_str = "%0.1fOGLE, %0.1HIP" % (100. * surveys_for_class[deb_class]['ogle'] / float(survey_n_total),
                                                     100. * surveys_for_class[deb_class]['hip'] / float(survey_n_total))
            elif (surveys_for_class[deb_class]['ogle'] > 0):
                survey_str = "OGLE"
            elif (surveys_for_class[deb_class]['hip'] > 0):
                survey_str = "HIPPARCOS"
            else:
                survey_str = "XXXXXXXXXXXXXXXXXXXX"
                
                

            #print "%s\t %d\t %0.1f\t\t%d\t %0.4f\t\t%0.2f\t %0.4f" % ( \
            print "%s\t &%d\t &%0.1f\t\t&%s&%d\t &%0.4f\t&%0.2f\t &%0.4f\\\\" % ( \
                                                deb_class,
                                                count,
                                                count / float(self.pars['deb_src_counts'][deb_class]) * 100.,
                                                survey_str,
                                                int(sum(class_nepoch_lists[deb_class])/ \
                                                    float(len(class_nepoch_lists[deb_class]))),
                                                min(class_period_lists[deb_class]), 
                                                sum(class_period_lists[deb_class])/ \
                                                float(len(class_period_lists[deb_class])),
                                                max(class_period_lists[deb_class]))
            
        print
        print "survey\t NLC\t %NLCdeb <Npts>"
        survey_names = {'hip':'HIPPARCOS', 'ogle':'OGLE'}
        nepochs_debos = {'hip':1044, 'ogle':527}
        for survey in ['hip', 'ogle']:
            count = survey_count[survey]

            #nepoch_avg = sum(survey_nepoch_lists[survey]) / float(len(survey_nepoch_lists[survey]))
            nepoch_avg = sum(nepoch_list_per_survey[survey]) / float(len(nepoch_list_per_survey[survey]))

            #print "%s\t %d\t %0.1f\t %d" % ( \
            print "%s\t &%d\t &%0.1f\t &%d\\\\" % ( \
                                            survey_names[survey],
                                            count,
                                            count / float(nepochs_debos[survey]) * 100.,
                                            int(nepoch_avg))
                    
        import pdb; pdb.set_trace()


    def confirm_idsdebdat_in_tutor(self):
        """ Check that the sources in 20110101 Joey's IDs_deb.dat are also in TUTOR RDB.
        """
        out_dict = {'tcpsrcid_classes':{},
                    'tcpsrcid_surveys':{},
                    'srcid_nepochs':{}}
        lines = open('/home/pteluser/scratch/IDs_deb.dat').readlines()
        for raw_line in lines:
            line = raw_line.strip()
            if len(line) == 0:
                continue
            f_id = int(line)
            if f_id < 140000:
                survey = 'hip'
            else:
                survey = 'ogle'

            if survey == 'hip':
                #select_str = 'select source_id, source_name, class_short_name from sources JOIN classes using (class_id) where project_id=123 and source_name like "%' + str(f_id) + '%"'
                select_str = 'select source_id, source_name, class_short_name from sources JOIN classes using (class_id) where project_id=123 and source_name="HIP%d"' % (f_id)
                self.tutor_cursor.execute(select_str)
                results = self.tutor_cursor.fetchall()
                if len(results) > 1:
                    print "matches > 1:", f_id, survey
                    for res in results:
                        print '          ', res
                elif len(results) == 1:
                    (source_id, source_name, class_short_name) = results[0]
                else:
                    #print "matches ==0:", f_id, survey
                    select_str = 'select source_id, source_name, class_short_name from sources JOIN classes using (class_id) where project_id=123 and source_name="HD%d"' % (f_id)
                    self.tutor_cursor.execute(select_str)
                    results = self.tutor_cursor.fetchall()
                    if len(results) > 1:
                        print "matches > 1:", f_id, survey
                        for res in results:
                            print '          ', res
                    elif len(results) == 1:
                        (source_id, source_name, class_short_name) = results[0]
                    else:
                        f_hdname = 'HD ' + str(f_id)
                        f_hipname = 'HIP ' + str(f_id)
                        for hd_name, hip_name in simbad_hd_hip_dict.iteritems():
                            if f_hdname == hd_name:
                                # then we query using the hip_name since query using hd_name nowork
                                select_str = 'select source_id, source_name, class_short_name from sources JOIN classes using (class_id) where project_id=123 and source_name="%s"' % (hip_name.replace(' ',''))
                                self.tutor_cursor.execute(select_str)
                                results = self.tutor_cursor.fetchall()

                                if len(results) > 1:
                                    import pdb; pdb.set_trace()
                                elif len(results) == 0:
                                    import pdb; pdb.set_trace()
                                else:
                                    (source_id, source_name, class_short_name) = results[0]

                                print results
                                import pdb; pdb.set_trace()
                                print
                                break

                            elif f_hipname == hip_name:
                                # then we query using the hd_name 
                                select_str = 'select source_id, source_name, class_short_name from sources JOIN classes using (class_id) where project_id=123 and source_name="%s"' % (hd_name.replace(' ',''))
                                self.tutor_cursor.execute(select_str)
                                results = self.tutor_cursor.fetchall()

                                if len(results) > 1:
                                    import pdb; pdb.set_trace()
                                elif len(results) == 0:
                                    import pdb; pdb.set_trace()
                                else:
                                    (source_id, source_name, class_short_name) = results[0]
                                break

                        

            elif survey == 'ogle':
                select_str = 'select source_id, source_name, class_short_name from sources JOIN classes using (class_id) where project_id=122 and source_id=%d' % (f_id)
                self.tutor_cursor.execute(select_str)
                results = self.tutor_cursor.fetchall()
                if len(results) > 1:
                    print "matches > 1:(in proj=122)", f_id, survey
                    for res in results:
                        print '          ', res
                    continue
                elif len(results) == 0:
                    print "matches ==0:(in proj=122)", f_id, survey
                    continue
                (source_id_122, source_name_122, class_short_name_122) = results[0]
                select_str = 'select source_id, source_name, class_short_name from sources JOIN classes using (class_id) where project_id=123 and source_name="%s"' % (source_name_122)
                self.tutor_cursor.execute(select_str)
                results = self.tutor_cursor.fetchall()
                if len(results) > 1:
                    print "source_name matches > 1:(in proj=123)", f_id, survey
                    for res in results:
                        print '          ', res
                    continue
                elif len(results) == 0:
                    print "source_name matches ==0:(in proj=123)", f_id, survey
                    continue
                (source_id, source_name, class_short_name) = results[0]
                if class_short_name != class_short_name_122:
                    print "id_123=%d source_name=%s class_123=%s class_122=%s" % \
                          (source_id, source_name, class_short_name, class_short_name_122)

            # KLUDGEY:
            class_short_name_upper = class_short_name.upper()
            matched_class = False
            for deb_cname, tut_cname in self.pars['debosscher_class_lookup'].iteritems():
                if class_short_name == tut_cname:
                    deb_class = deb_cname
                    matched_class = True
                    break
                elif class_short_name_upper == tut_cname:
                    deb_class = deb_cname
                    matched_class = True
                    break
            if matched_class == False:
                print tcp_srcid, fname_list, class_short_name
                import pdb; pdb.set_trace()
                print
            #print '#', f_id, source_id, source_name, class_short_name
            print f_id, '\t', deb_cname, '\t', source_name
            out_dict['tcpsrcid_classes'][source_id] = [deb_cname]
            out_dict['tcpsrcid_surveys'][source_id] = survey
            out_dict['srcid_nepochs'][source_id] = 1
        return out_dict



    def determine_deboss_classes_for_srcids(self, debos_tcp_dict):
        """ For each tcp_srcid, determine the 1 or more debosscher classes taken from the Deboss datafiles.
        """ 
        debclass_dict_ogle = self.fill_debclass_dict(self.pars['debclass_ogle_fpath'])
        ogle_fnames = debclass_dict_ogle.keys()

        debclass_dict_hip = self.fill_debclass_dict(self.pars['debclass_hip_fpath'])
        hip_fnames = debclass_dict_hip.keys()


        tcpsrcid_surveys = {}
        tcpsrcid_classes = {}
        for tcp_srcid, fname_list in debos_tcp_dict['dotastro_srcid_to_attribfiles'].iteritems():
            select_str = "select class_short_name, source_name from sources JOIN classes using (class_id) where project_id=123 and source_id=%d" % (tcp_srcid)
            self.tutor_cursor.execute(select_str)
            results = self.tutor_cursor.fetchall()

            if len(results) == 0:
                print "NONE!!!:", tcp_srcid, "Data file not in ts-OGLE / ts-HIPPARCOS files:", fname, tcp_srcid
                continue
            class_short_name = results[0][0]
            source_name = results[0][1]
            if 'hip' in source_name.lower():
                tcpsrcid_surveys[tcp_srcid] = 'hip'
            elif 'ogle' in source_name.lower():
                tcpsrcid_surveys[tcp_srcid] = 'ogle'
            else:
                hdname = source_name.replace('HD','HD ')
                if hdname in simbad_hd_hip_dict.keys():
                    tcpsrcid_surveys[tcp_srcid] = 'hip'
                else:
                    print '!!! survey not known!', tcp_srcid, source_name
            # KLUDGEY:
            class_short_name_upper = class_short_name.upper()
            matched_class = False
            for deb_cname, tut_cname in self.pars['debosscher_class_lookup'].iteritems():
                if class_short_name == tut_cname:
                    tcpsrcid_classes[tcp_srcid] = [deb_cname]
                    matched_class = True
                    break
                elif class_short_name_upper == tut_cname:
                    tcpsrcid_classes[tcp_srcid] = [deb_cname]
                    matched_class = True
                    break
            if matched_class == False:
                print tcp_srcid, fname_list, class_short_name
                import pdb; pdb.set_trace()
                print

        debos_tcp_dict['tcpsrcid_classes'] = tcpsrcid_classes
        debos_tcp_dict['tcpsrcid_surveys'] = tcpsrcid_surveys


    def determine_deboss_classes_for_srcids__old(self, debos_tcp_dict):
        """ For each tcp_srcid, determine the 1 or more debosscher classes taken from the Deboss datafiles.
        """ 

        debclass_dict = {} # 'LC_fname':[<class1>, <class2>]

        debclass_dict_ogle = self.fill_debclass_dict(self.pars['debclass_ogle_fpath'])
        debclass_dict.update(debclass_dict_ogle)
        ogle_fnames = debclass_dict_ogle.keys()

        debclass_dict_hip = self.fill_debclass_dict(self.pars['debclass_hip_fpath'])
        debclass_dict.update(debclass_dict_hip)
        hip_fnames = debclass_dict_hip.keys()


        tcpsrcid_surveys = {}
        tcpsrcid_classes = {}
        for tcp_srcid, fname_list in debos_tcp_dict['dotastro_srcid_to_attribfiles'].iteritems():
            #if tcp_srcid == 163844:
            #    print 'yo' #164149:
            tcpsrcid_classes[tcp_srcid] = []
            sorted_fname_list = []
            for fname in fname_list:
                if 'hip' in fname:
                    sorted_fname_list.insert(0,fname)
                else:
                    sorted_fname_list.append(fname)
            for fname in sorted_fname_list:
                if not debclass_dict.has_key(fname):
                    # NOTE: I checked a selection of these and indeed there dont seem to be these fnames or similar numbers in the ts-OGLE / ts-HIPPARCOS files:
                    #print "Data file not in ts-OGLE / ts-HIPPARCOS files:", fname, tcp_srcid
                    select_str = "select class_short_name, source_name from sources JOIN classes using (class_id) where project_id=123 and source_id=%d" % (tcp_srcid)
                    self.tutor_cursor.execute(select_str)
                    results = self.tutor_cursor.fetchall()
                    if len(results) == 0:
                        print "NONE!!!:", tcp_srcid, "Data file not in ts-OGLE / ts-HIPPARCOS files:", fname, tcp_srcid
                        continue
                    class_short_name = results[0][0]
                    source_name = results[0][1]
                    if not tcpsrcid_surveys.has_key(tcp_srcid):
                        if 'hip' in source_name.lower():
                            tcpsrcid_surveys[tcp_srcid] = 'hip'
                        else:
                            tcpsrcid_surveys[tcp_srcid] = 'ogle' # if below doesnt match, then we use this
                            for a_fname in hip_fnames:
                                if fname in a_fname:
                                    print "! ! ! ! tcp_srcid=%d: source_name=%s not HIPlike, but fname=%s is in ts-HIPPARCOS" % (tcp_src_id, source_name, fname)
                                    tcpsrcid_surveys[tcp_srcid] = 'hip'
                                    break
                    # KLUDGEY:
                    for deb_cname, tut_cname in self.pars['debosscher_class_lookup'].iteritems():
                        if class_short_name == tut_cname:
                            tcpsrcid_classes[tcp_srcid].append(deb_cname)
                            break
                    continue

                if fname in ogle_fnames:
                    assert(tcpsrcid_surveys.get(tcp_srcid, 'ogle') == 'ogle')
                    tcpsrcid_surveys[tcp_srcid] = 'ogle'
                elif fname in hip_fnames:
                    assert(tcpsrcid_surveys.get(tcp_srcid, 'hip') == 'hip')
                    tcpsrcid_surveys[tcp_srcid] = 'hip'
                    
                for a_class in debclass_dict[fname]:
                    assert(not a_class in tcpsrcid_classes[tcp_srcid])
                tcpsrcid_classes[tcp_srcid].extend(debclass_dict[fname])

        
                

        ### For each srcid:[filename], get the classes
        ###   -> ensure that for a srcid, there are not more than the classes what are defined for a single data file
        #for tcp_srcid, deb_class_list in tcpsrcid_classes.iteritems():
        #    if len(deb_class_list) <= 1:
        #        continue
        #    print tcp_srcid,
        #    for deb_class in deb_class_list:
        #        print deb_class,
        #    print ';',
        #    for deb_class in deb_class_list:
        #        print self.pars['debosscher_class_lookup'][deb_class],
        #    print '; Nepochs:', debos_tcp_dict['srcid_nepochs'][tcp_srcid], tcpsrcid_surveys[tcp_srcid]
            
            
        debos_tcp_dict['tcpsrcid_classes'] = tcpsrcid_classes
        debos_tcp_dict['tcpsrcid_surveys'] = tcpsrcid_surveys


    def get_deboss_dotastro_source_lookup__modified(self):
        """ Parsing Debosscher data files and querying DotAstro.org,
        determine which sources match and get related lookup info for each source.
        """
        ##### This gets a LC "filename" and its associated features/attributes
        deboss_attrib_dict = {}
        lines = open(self.pars['deboss_src_attribs_fpath']).readlines()
        for line in lines:
            line_list = line.split()
            fname = line_list[0]
            deboss_attrib_dict[fname] = {}
            for i, attrib in enumerate(self.pars['deboss_src_attribs_list'][1:]):
                deboss_attrib_dict[fname][attrib] = line_list[i+1]

        ##### This gets a source_name and all of the >=1 related lightcurve filenames:
        #    - NOTE: right now we just associate a single lightcurve per source_name since I assume . . .
        deboss_srcname_fname_lookup = {}
        lines = open(self.pars['deboss_src_datafile_lookup_fpath']).readlines()
        for line in lines:
            source_name = line[:23].strip()

            deboss_srcname_fname_lookup[source_name] = []

            filename_list = line[63:].split()
            for file_name in filename_list:
                file_name_sripped = file_name.strip()
                deboss_srcname_fname_lookup[source_name].append(file_name_sripped)

        debos_srcname_to_dotastro_srcid = {}
        dotastro_srcid_to_attribfiles = {}
        dotastro_srcid_to_debos_srcname = {}
        # # #import pdb; pdb.set_trace()
        for source_name, fname_list in deboss_srcname_fname_lookup.iteritems():
            #if 'HIP 54413' in source_name:
            #    print 'yo'
            debos_srcname_to_dotastro_srcid[source_name] = []
            fname_match_found = False
            for filename in fname_list:
                select_str = 'SELECT source_id, source_name, project_id, class_id, pclass_id FROM sources WHERE project_id=123 and source_name = "%s"' % (source_name)
                print select_str
                self.tutor_cursor.execute(select_str)
                results = self.tutor_cursor.fetchall()
                if len(results) != 0:
                    if results[0][0] not in debos_srcname_to_dotastro_srcid[source_name]:
                        debos_srcname_to_dotastro_srcid[source_name].append(results[0][0])
                    if not dotastro_srcid_to_attribfiles.has_key(results[0][0]):
                        dotastro_srcid_to_attribfiles[results[0][0]] = []
                    dotastro_srcid_to_attribfiles[results[0][0]].append(filename)
                    if not dotastro_srcid_to_debos_srcname.has_key(results[0][0]):
                        dotastro_srcid_to_debos_srcname[results[0][0]] = []
                    if not source_name in dotastro_srcid_to_debos_srcname[results[0][0]]:
                        dotastro_srcid_to_debos_srcname[results[0][0]].append(source_name)
                    continue
                select_str = 'SELECT source_id, source_name, project_id, class_id, pclass_id FROM sources WHERE project_id=123 and source_name like "%s"' % (source_name.replace(' ','\_'))
                self.tutor_cursor.execute(select_str)
                results = self.tutor_cursor.fetchall()
                if len(results) != 0:
                    if results[0][0] not in debos_srcname_to_dotastro_srcid[source_name]:
                        debos_srcname_to_dotastro_srcid[source_name].append(results[0][0])
                    if not dotastro_srcid_to_attribfiles.has_key(results[0][0]):
                        dotastro_srcid_to_attribfiles[results[0][0]] = []
                    dotastro_srcid_to_attribfiles[results[0][0]].append(filename)
                    if not dotastro_srcid_to_debos_srcname.has_key(results[0][0]):
                        dotastro_srcid_to_debos_srcname[results[0][0]] = []
                    if not source_name in dotastro_srcid_to_debos_srcname[results[0][0]]:
                        dotastro_srcid_to_debos_srcname[results[0][0]].append(source_name)
                    continue
                select_str = 'SELECT source_id, source_name, project_id, class_id, pclass_id FROM sources WHERE project_id=123 and source_name = "%s"' % (filename)
                self.tutor_cursor.execute(select_str)
                results = self.tutor_cursor.fetchall()
                if len(results) != 0:
                    if results[0][0] not in debos_srcname_to_dotastro_srcid[source_name]:
                        debos_srcname_to_dotastro_srcid[source_name].append(results[0][0])
                    if not dotastro_srcid_to_attribfiles.has_key(results[0][0]):
                        dotastro_srcid_to_attribfiles[results[0][0]] = []
                    dotastro_srcid_to_attribfiles[results[0][0]].append(filename)
                    if not dotastro_srcid_to_debos_srcname.has_key(results[0][0]):
                        dotastro_srcid_to_debos_srcname[results[0][0]] = []
                    if not source_name in dotastro_srcid_to_debos_srcname[results[0][0]]:
                        dotastro_srcid_to_debos_srcname[results[0][0]].append(source_name)
                    continue
                select_str = 'SELECT source_id, source_name, project_id, class_id, pclass_id FROM sources WHERE project_id=123 and source_name = "%s"' % (source_name.replace(' ',''))
                self.tutor_cursor.execute(select_str)
                results = self.tutor_cursor.fetchall()
                if len(results) != 0:
                    if results[0][0] not in debos_srcname_to_dotastro_srcid[source_name]:
                        debos_srcname_to_dotastro_srcid[source_name].append(results[0][0])
                    if not dotastro_srcid_to_attribfiles.has_key(results[0][0]):
                        dotastro_srcid_to_attribfiles[results[0][0]] = []
                    dotastro_srcid_to_attribfiles[results[0][0]].append(filename)
                    if not dotastro_srcid_to_debos_srcname.has_key(results[0][0]):
                        dotastro_srcid_to_debos_srcname[results[0][0]] = []
                    if not source_name in dotastro_srcid_to_debos_srcname[results[0][0]]:
                        dotastro_srcid_to_debos_srcname[results[0][0]].append(source_name)
                    ###20100802 dstarr disables this since sometimes double classifications are given in Debos:
                    ###    and the other sci-class is entered as *_a into DotAstro: HIP54413, HIP54413_a
                    #continue
                select_str = 'SELECT source_id, source_name, project_id, class_id, pclass_id FROM sources WHERE project_id=123 and source_name like "%s\_' % (source_name.replace(' ','')) + '%"'
                self.tutor_cursor.execute(select_str)
                results = self.tutor_cursor.fetchall()
                if len(results) != 0:
                    if results[0][0] not in debos_srcname_to_dotastro_srcid[source_name]:
                        debos_srcname_to_dotastro_srcid[source_name].append(results[0][0])
                    if not dotastro_srcid_to_attribfiles.has_key(results[0][0]):
                        dotastro_srcid_to_attribfiles[results[0][0]] = []
                    dotastro_srcid_to_attribfiles[results[0][0]].append(filename)
                    if not dotastro_srcid_to_debos_srcname.has_key(results[0][0]):
                        dotastro_srcid_to_debos_srcname[results[0][0]] = []
                    if not source_name in dotastro_srcid_to_debos_srcname[results[0][0]]:
                        dotastro_srcid_to_debos_srcname[results[0][0]].append(source_name)
                    continue
        #for debos_srcname, dotastro_srcid_list in debos_srcname_to_dotastro_srcid.iteritems():
        #    if len(dotastro_srcid_list) > 1:
        #        print "len(dotastro_srcid_list) > 1:", debos_srcname, dotastro_srcid_list

        #for dotastro_srcid, debos_srcname in dotastro_srcid_to_debos_srcname.iteritems():
        #    print dotastro_srcid, debos_srcname
        
        dotastro_srcid_to_debos_attribs = {}
        for dotastro_srcid, attribfiles in dotastro_srcid_to_attribfiles.iteritems():
            matches_found = 0
            for attrib_file in attribfiles:
                if deboss_attrib_dict.has_key(attrib_file):
                    if os.path.exists("/home/pteluser/analysis/debosscher_20100707/TS-HIPPARCOS/" + attrib_file):
                        matches_found += 1
                        # I've checked that this only occurs once per dotastro sourceid (no multi LCs in there):
                        dotastro_srcid_to_debos_attribs[dotastro_srcid] = deboss_attrib_dict[attrib_file]
                    elif os.path.exists("/home/pteluser/analysis/debosscher_20100707/TS-OGLE/" + attrib_file):
                        matches_found += 1
                        # I've checked that this only occurs once per dotastro sourceid (no multi LCs in there):
                        dotastro_srcid_to_debos_attribs[dotastro_srcid] = deboss_attrib_dict[attrib_file]
            ##### DEBUG PRINTING:
            #if matches_found == 0:
            #    print     '  NO ATTRIB FILE:', dotastro_srcid, attribfiles
            #elif matches_found > 1:
            #    print     'MULTIPLE ATTRIBS:', dotastro_srcid, attribfiles
            #    for fname in attribfiles:
            #        pprint.pprint((fname, deboss_attrib_dict[fname]))
        return {'dotastro_srcid_to_debos_attribs':dotastro_srcid_to_debos_attribs,
                'dotastro_srcid_to_debos_srcname':dotastro_srcid_to_debos_srcname,
                'dotastro_srcid_to_attribfiles':dotastro_srcid_to_attribfiles}


class tutor_db:
    """
    """
    def __init__(self):
        self.pars ={'tcptutor_hostname':'192.168.1.103',
                    'tcptutor_username':'tutor', # guest
                    'tcptutor_password':'ilove2mass', #'iamaguest',
                    'tcptutor_database':'tutor',
                    'tcptutor_port':3306}


        self.tutor_db = MySQLdb.connect(host=self.pars['tcptutor_hostname'], \
                                  user=self.pars['tcptutor_username'], \
                                  passwd=self.pars['tcptutor_password'],\
                                  db=self.pars['tcptutor_database'],\
                                  port=self.pars['tcptutor_port'])
        self.tutor_cursor = self.tutor_db.cursor()






if __name__ == '__main__':
    #db = tutor_db()

    
    ### 20101118: This pars{} is taken from analysis_deboss_tcp_source_compare.py:
    pars_tutor = {'num_percent_epoch_error_iterations':2, # !!! NOTE: This must be the same in pairwise_classification.py:pars[]
            'subsample_percents_to_generate_xmls':[0.1], # This takes 22 cores ??? considering that tranx will do a second round (count=22 + 8)  # # # #TODO: 16perc * 9sets is much more reasonable, memory/resource/ipython-node wise
            'tcp_hostname':'192.168.1.25',
            'tcp_username':'pteluser',
            'tcp_port':     3306, 
            'tcp_database':'source_test_db',
            'tcptutor_hostname':'192.168.1.103',
            'tcptutor_username':'tutor',
            'tcptutor_password':'ilove2mass',
            'tcptutor_port':     3306, # 13306,
            'tcptutor_database':'tutor',
            'srcid_debos_attribs_pkl_fpath':'/home/pteluser/analysis/debosscher_20100707/srcid_debos_attribs.pkl.gz',
            #OBSOLETE#'arff_fpath':os.path.expandvars(os.path.expanduser("~/scratch/dotastro_ge1srcs_period_nonper__exclude_non_debosscher.arff")),
            'trainset_pruned_pklgz_fpath':"/home/pteluser/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher/pairwise_trainset__debosscher_table3.pkl.gz",
            'deboss_src_datafile_lookup_fpath':'/home/pteluser/analysis/debosscher_20100707/list.dat', # essentially the same as debos_newHIPP_data/list.dat(19893.hip -> c-19893.hip)
            'deboss_src_attribs_fpath':'/home/pteluser/analysis/debosscher_20100707/defatts.dat',
            'deboss_src_attribs_list':['filename','f1','f2','f3','amp11','amp12','amp13','amp14','amp21','amp22','amp23','amp24','amp31','amp32','amp33','amp34','phi12','phi13','phi14','phi21','phi22','phi23','phi24','phi31','phi32','phi33','phi34','trend','varrat','varred','class'],
            }

    # 20101118: Take from pairwise_classification.py:
    pars = {'num_percent_epoch_error_iterations':2, # !!! NOTE: This must be the same in analysis_deboss_tcp_source_compare.py:pars[]
            'crossvalid_nfolds':10, # None == use n_folds equal to the minimum number of sources for a science class.  If this number is > 10, then n_folds is set to 10
            'crossvalid_do_stratified':False, # False: randomly sample sources for each fold, True: exclude a fold group of sources which is not excluded in the other folds.
            'crossvalid_fold_percent':40., #NOTE: only valid if do_stratified=False  #float x in x/y OR None==just use the percent 1/nfolds
            'tcp_hostname':'192.168.1.25',
            'tcp_username':'pteluser',
            'tcp_port':     3306, 
            'tcp_database':'source_test_db',
            'dotastro_arff_fpath':os.path.expandvars('$HOME/scratch/train_output_20100517_dotastro_xml_with_features__default.arff'),#os.path.expandvars('$HOME/scratch/train_output_20100517_dotastro_xml_with_features.arff'),
            'arff_sciclass_dict_pkl_fpath':os.path.expandvars('$HOME/scratch/arff_sciclass_dict.pkl'),
            'trainset_pruned_pklgz_fpath':os.path.expandvars('$HOME/scratch/trainset_pruned.pkl.gz'),
            'pruned_classif_summary_stats_pkl_fpath': \
                                 os.path.expandvars('$HOME/scratch/pruned_classif_summary_stats.pkl'),
            'weka_pairwise_classifiers_pkl_fpath': \
                                  os.path.expandvars('$HOME/scratch/weka_pairwise_classifiers_pkl_fpath.pkl'),
            'pairwise_trainingset_dirpath':os.path.expandvars('$HOME/scratch/pairwise_trainingsets'),
            'pairwise_classifier_dirpath':os.path.expandvars('$HOME/scratch/pairwise_classifiers'),
            'pairwise_classifier_pklgz_dirpath':os.path.expandvars('$HOME/scratch/pairwise_classifiers'),
            'pairwise_scratch_dirpath':'/media/raid_0/pairwise_scratch',
            'classification_summary_pklgz_fpath':'',#os.path.expandvars('$HOME/scratch/pairwise_classifiers'),
            'confusion_stats_html_fpath':os.path.expandvars('$HOME/Dropbox/Public/work/pairwise_confusion_matrix.html'),
            'cyto_work_final_fpath':'/home/pteluser/Dropbox/work/',
            'cyto_network_fname':'pairwise_class.cyto.network',
            'cyto_nodeattrib_fname':'pairwise_class.cyto.nodeattrib',
            'pairwise_schema_name':'noprune', # represents how the class heirarchy pruning was done.
            't_sleep':0.2,
            'number_threads':13, # on transx : 10
            'min_num_sources_for_pairwise_class_inclusion':6,
            #'feat_dist_image_fpath':"/home/pteluser/Dropbox/Public/work/feat_distribution.png",#OBSOLETE
            #'feat_dist_image_url':"http://dl.dropbox.com/u/4221040/work/feat_distribution.png",#OBSOLETE
            'feat_dist_image_local_dirpath':'/media/raid_0/pairwise_scratch/pairwise_scp_data',#"/home/pteluser/scratch/pairwise_scp_data",
            'feat_dist_image_remote_scp_str':"pteluser@lyra.berkeley.edu:www/dstarr/pairwise_images/",
            'feat_dist_image_rooturl':"http://lyra.berkeley.edu/~jbloom/dstarr/pairwise_images",
            'feat_distrib_classes':{'target_class':'lboo',#adding anything here is OBSOLETE
                                    'comparison_classes':['pvsg', 'gd', 'ds']},#adding anything here is OBSOLETE
            'plot_symb':['o','s','v','d','<'], # ,'+','x','.', ,'>','^'
            'feat_distrib_colors':['#000000',
                                   '#ff3366',
                                   '#660000',
                                   '#aa0000',
                                   '#ff0000',
                                   '#ff6600',
                                   '#996600',
                                   '#cc9900',
                                   '#ffff00',
                                   '#ffcc33',
                                   '#ffff99',
                                   '#99ff99',
                                   '#666600',
                                   '#99cc00',
                                   '#00cc00',
                                   '#006600',
                                   '#339966',
                                   '#33ff99',
                                   '#006666',
                                   '#66ffff',
                                   '#0066ff',
                                   '#0000cc',
                                   '#660099',
                                   '#993366',
                                   '#ff99ff',
                                   '#440044'],
            #'feat_distrib_colors':['b','g','r','c','m','y','k','0.25','0.5','0.75', (0.5,0,0), (0,0.5,0), (0,0,0.5), (0.75,0,0), (0,0.75,0), (0,0,0.75), (0.25,0,0), (0,0.25,0), (0,0,0.25), '#eeefff', '#bbbfff', '#888fff', '#555fff', '#000fff', '#000aaa', '#fffaaa'],
            'taxonomy_prune_defs':{
                     'terminating_classes':['be', 'bc', 'sreg', 'rr-lyr', 'c', 'bly', 'sne','nov']},
            'debosscher_confusion_table3_fpath':os.path.abspath(os.environ.get("TCP_DIR") + '/Data/debosscher_table3.html'),
            'debosscher_confusion_table4_fpath':os.path.abspath(os.environ.get("TCP_DIR") + '/Data/debosscher_table4.html'),
            'debosscher_class_lookup':{ \
                'BCEP':'bc',    
                'BE':'be', #NO LCs   # Pulsating Be-stars  (57) : HIP, GENEVA
                'CLCEP':'dc',
                'CP':'CP',
                'CV':'cv', #NO LCs   # Cataclysmic variables (3) : ULTRACAM
                'DAV':'pwd', #NO LCs # Pulsating DA white dwarfs (2) : WET
                'DBV':'pwd', #NO LCs # Pulsating DB white dwarfs (1) : WET / CFHT
                'DMCEP':'cm',
                'DSCUT':'ds',
                'EA':'alg',
                'EB':'bly',
                'ELL':'ell',
                'EW':'wu',
                'FUORI':'fuor', #NO LCs # FU-Ori stars (3) : ROTOR
                'GDOR':'gd',
                'GWVIR':'gw', #NO LCs # GW-Virginis stars (2) : CFHT
                'HAEBE':'haebe',
                'LBOO':'lboo',
                'LBV':'sdorad',
                'MIRA':'mira',
                'PTCEP':'piic',
                'PVSG':'pvsg', # Periodically variable supergiants (76) : HIP, GENEVA, ESO
                'ROAP':'rot', #NO LCs # Rapidly oscillationg Ap stars (4) : WET/ESO # 13587 is given class_id='rot' in Dotastro, but the dotastro projectclass is 'Rapidly Osc Ap stars'.
                'RRAB':'rr-ab',
                'RRC':'rr-c',
                'RRD':'rr-d',
                'RVTAU':'rv',
                'SDBV':'sdbv', #NO LCs # Pulsating subdwarf B stars (16) : ULTRACAM
                'SLR':'NOTMATCHED',  # NOT in projid=123 # NOT MATCHED  Solar-like oscillations in red giants (1) : MOST
                'SPB':'spb',   # Slowly-pulsating B stars (47) : HIP / GENEVA, MOST
                'SR':'sreg',
                'SXPHE':'sx',        ### NOT in current Debosscher confusion matrix
                'TTAU':'tt',
                'WR':'wr',
                'XB':'xrbin',        ### NOT in current Debosscher confusion matrix
                },
            'deb_src_counts':{
                 'PVSG':   76 ,
                 'BE':     57 ,
                 'BCEP':   58 ,
                 'CLCEP': 195 ,
                 'DMCEP':  95 ,
                 'PTCEP':  24 ,
                 'CP':     63 ,
                 'DSCUT': 139 ,
                 'LBOO':   13 ,
                 'SXPHE':   7 ,
                 'GDOR':   35 ,
                 'LBV':    21 ,
                 'MIRA':  144 ,
                 'SR':     42 ,
                 'RRAB':  129 ,
                 'RRC':    29 ,
                 'RRD':    57 ,
                 'RVTAU':  13 ,
                 'SPB':    47 ,
                 'SLR':     1 ,
                 'SDBV':   16 ,
                 'DAV':     2 ,
                 'DBV':     1 ,
                 'GWVIR':   2 ,
                 'ROAP':    4 ,
                 'TTAU':   17 ,
                 'HAEBE':  21 ,
                 'FUORI':   3 ,
                 'WR':     63 ,
                 'XB':      9 ,
                 'CV':      3 ,
                 'EA':    169 ,
                 'EB':    147 ,
                 'EW':     59 ,
                 'ELL':    16},
            'debclass_ogle_fpath':'/home/pteluser/analysis/debosscher_20100707/ts-OGLE',
            'debclass_hip_fpath':'/home/pteluser/analysis/debosscher_20100707/ts-HIPPARCOS',
            }
    pars.update(pars_tutor)

    DebPaperAnalysis = Deb_Paper_Analysis(pars=pars)
    DebPaperAnalysis.main()

    #AnalysisDebossTcpSourceCompare = Analysis_Deboss_TCP_Source_Compare(pars=pars)

    #srcid_to_debos_attribs = self.get_deboss_dotastro_source_lookup()
