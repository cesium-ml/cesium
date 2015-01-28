#!/usr/bin/env python 
"""
   v0.1 Scipt used with PDB, to simulate what the ptf_master.py ipython tasks
        do, when given a new diff-object.
        - Useful for debugging source clustering, classification, ...

   NOTE: 20090615: typically break around:
          break ingest_tools.py:4528

   NOTE: Before running with a test object/source, make sure it's IDs are not in RDB tables:
        mysql> delete from ptf_events where id=1;
        delete from ptf_events where id=1;
        Query OK, 1 row affected (0.00 sec)

        mysql> delete from obj_srcid_lookup where obj_id=1 and survey_id=3;
        delete from obj_srcid_lookup where obj_id=1 and survey_id=3;
        Query OK, 1 row affected (0.00 sec)
"""
import sys
import os
import MySQLdb
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/ingest_tools'))
import ptf_master
import ingest_tools # just needed to set PDB breakpoints
pars = { \
    'mysql_user':"pteluser", \
    'mysql_hostname':"192.168.1.25", \
    'mysql_database':'object_test_db', \
    'mysql_port':3306}
db = MySQLdb.connect(host=pars['mysql_hostname'], \
                         user=pars['mysql_user'], \
                         db=pars['mysql_database'], \
                         port=pars['mysql_port'])
cursor = db.cursor()
DiffObjSourcePopulator = ptf_master.Diff_Obj_Source_Populator(use_postgre_ptf=True)
print "DONE: DiffObjSourcePopulator = ptf_master.Diff_Obj_Source_Populator()"

# NOTE: the list order corresponds to order of INSERT into MySQL RDB:
#"""
test_objs = [ \
    {'obj_id':    0,
     'ra':        224.55255677,
     'dec':        18.44210702,
     'realbogus': 0.9,
     'flux':      1803.0,
     't_val':     0.0},
    ]

for dict_elem in test_objs:
    ra = dict_elem['ra']
    dec = dict_elem['dec']
    obj_id = dict_elem['obj_id']
    realbogus = dict_elem['realbogus']
    t_val = dict_elem['t_val']
    flux = dict_elem['flux']
    
    diff_obj = {'decl': dec, 'ub1_zp_new': 27.5, 'flux_aper_err': 100.331, 'filt': 9, 'obj_ids': [obj_id], 'unclear': 0.0050000000000000001, 'lmt_mg_new': 20.608000000000001, 'mag_ref': 14.8698, 'sub_m': 19.296199999999999, 'id': [obj_id], 'sub_m_err': 0.0717, 'src_id': 0, 'f_aper_err': 85.051199999999994, 'flags2': 0, 'mag_ref_err': 0.0063, 'objc_type': 10, 'flux_err': 119.136, 'ub1_zp_ref': 25.600000000000001, 'suspect': 0.002, 'ra': ra, 'b_image': [1.0069999999999999], 'a_image': [1.2529999999999999], 'filts': [9], 'mag_err': [0.0717], 'dec_rms': 1.0, 'mag': [19.296199999999999], 'f_aper': 3228.6500000000001, 'lmt_mag_ref': 21.876899999999999, 'dec': dec, 'ra_rms': 1.0, 'sub_id': [13695L], 'maybe': 0.0, 'bogus': 0.0, 'm': 14.894467501872207, 'flux_aper': 15923.299999999999, 'filter': ['R'], 'm_err': 0.0717, 'lmt_mg_ref': [21.876899999999999], 'flags': 0, 't': t_val, 'flux': flux, 'ujd': [t_val], 'realish': 0.0, 'realbogus':realbogus}
    k_list = diff_obj.keys()
    k_list.remove('filt')
    k_list.remove('filts')
    k_list.remove('obj_ids')
    k_list.remove('sub_m')
    k_list.remove('sub_m_err')
    k_list.remove('src_id')
    k_list.remove('flags')
    k_list.remove('flags2')
    k_list.remove('objc_type')
    k_list.remove('lmt_mag_ref')
    k_list.remove('m')
    k_list.remove('m_err')
    k_list.remove('t')
    k_list.remove('dec')
    #k_list.remove('id')

    if False:
        #v_str = str(map(lambda x: str(diff_obj[x]), k_list))[1:-1].replace("'","")
        v_str = ""
        for k in k_list:
            v = diff_obj[k]
            if k == 'filter':
                v_str += '"%s", ' % (str(v[0]))
            elif type(v) == type([]):
                v_str += str(v[0]) + ", "
            else:
                v_str += str(v) + ", "
        insert_str = "INSERT INTO object_test_db.ptf_events (%s) VALUES (%s)" % ( \
                             str(k_list)[1:-1].replace("'",""),
                             v_str[:-2])
        # # #cursor.execute(insert_str)

        print " (new) INSERT id=",  obj_id
        insert_str_2 = "INSERT INTO obj_srcid_lookup (src_id, obj_id, survey_id) VALUES (0, %d, 3)" % (obj_id)
        # # #cursor.execute(insert_str_2)
        print
    (srcid_xml_tuple_list, n_objs) = DiffObjSourcePopulator.ingest_diffobj(diff_obj, feat_db=DiffObjSourcePopulator.feat_db)
    # NOTE: enable the fillowing if you want te TEST / DEBUG the classification code:
    DiffObjSourcePopulator.class_interface.classify_and_insert_using_vosource_list(srcid_xml_tuple_list)
print 'done'

"""
test_objs = [ \
    {'obj_id':    0,
     'ra':        169.383670165,
     'dec':        53.303472271,
     'realbogus': 0.9,
     'flux':      1803.0,
     't_val':     0.0},
    {'obj_id':    0,
     'ra':        80.00,
     'dec':      -80.0,
     'realbogus': 0.001,
     'flux':      1803.0,
     't_val':     2454972.0},
    {'obj_id':    1,
     'ra':        80.00,
     'dec':      -80.0,
     'realbogus': 0.001,
     'flux':      1803.1,
     't_val':     2454972.1},
    {'obj_id':    2,
     'ra':        80.00,
     'dec':      -80.0,
     'realbogus': 0.3,
     'flux':      1803.2,
     't_val':     2454972.2},
    {'obj_id':    3,
     'ra':        80.00,
     'dec':      (-80.00000),
     'realbogus': 0.3,
     'flux':      1803.3,
     't_val':     2454972.3},
    {'obj_id':    4,
     'ra':        80.00,
     'dec':      (-80.00000),
     'realbogus': 0.4,
     'flux':      1803.4,
     't_val':     2454972.4},
    {'obj_id':    5,
     'ra':        80.00,
     'dec':      (-80.00000),
     'realbogus': 0.5,
     'flux':      1803.5,
     't_val':     2454972.5},
    {'obj_id':    6,
     'ra':        80.00,
     'dec':      (-80.00000),
     'realbogus': 0.6,
     'flux':      1803.6,
     't_val':     2454972.6},
    {'obj_id':    7,
     'ra':        80.00,
     'dec':      (-80.00000),
     'realbogus': 0.7,
     'flux':      1803.7,
     't_val':     2454972.7},
    {'obj_id':    8,
     'ra':        80.00,
     'dec':      (-80.00000),
     'realbogus': 0.8,
     'flux':      1803.8,
     't_val':     2454972.8},
    {'obj_id':    9,
     'ra':        80.00,
     'dec':      (-80.00000),
     'realbogus': 0.9,
     'flux':      1803.9,
     't_val':     2454972.9},
    ]


"""
