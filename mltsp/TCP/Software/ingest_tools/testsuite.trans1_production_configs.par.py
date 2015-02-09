parameters = {
    'test_suite__enable_traceback':False, # False: (default), True: for PDB use
    'test_suite__preserve_tables_databases_servers':False, # False: (default)
    'test_suite__use_tunnel_mysql_server':True,
    'test_suite__force_astrom_photometry':False,#True: Test mos.fits reductions
    'xmlrpc_server_name':"192.168.1.45", #SVN: 127.0.0.1 # Must be non-local IP if XMLRPC Server is to be called by other computers (eg.: 192.168.1.45).
    'local_hostname':'127.0.0.1',
    'local_username':'pteluser', ####SVN COMMITTED DEFAULT: 'pteluser'
    'local_mysql_port':3306,
    'local_ssh_port':22, ##########SVN COMMITTED DEFAULT:  37921
    'local_TCP_path':'$TCP_DIR/',
    'remote_hostname':'192.168.1.55', # Only usable within Evans 260 LAN.
    'remote_username':'pteluser',
    'remote_mysql_port':3306,
    'remote_ssh_port':22,
    'remote_TCP_path':'/home/pteluser/src/TCP/',
    'table_create_script_fpath':'/tmp/create_ptel_object_tables.sh',
    'mosfits_cleanup_wildcards':['*sex', '*pkl', '*match*'],
    'mysql_float_condition_accuracy':0.00005,#=.18" Seen .16" matchng float errs
    'source_table_name':'srcid_lookup',
    'index_server':{ \
        'obj_id':{\
            'socket_server_port':50020,
            'rdb_server_db':'object_db',
            'primary_table_colname':'obj_id',
            'obj_id_reference_tablename':'sdss_events_a',
            },
        'ptel_obj_id':{\
            'socket_server_port':50040,
            'rdb_server_db':'object_db',
            'primary_table_colname':'obj_id',
            'obj_id_reference_tablename':'pairitel_events_a',
            },
        'src_id':{\
            'socket_server_port':50030,
            'rdb_server_db':'source_db',
            'primary_table_colname':'src_id',
            'obj_id_reference_tablename':'srcid_lookup',
            },
        'footprint_id':{\
            'socket_server_port':50050,
            'rdb_server_db':'object_db',
            'primary_table_colname':'footprint_id',
            'obj_id_reference_tablename':'footprint_regions',
            },
    },
    'ingest_tools_pars':{ \
        'rdb_name_2':'object_db',
        'rdb_name_3':'object_db',
        'rdb_table_names':{'sdss':'sdss_events_a',
                           'pairitel':'pairitel_events_a'},
        'ptel_object_table_name_DIF_HTM14':'pairitel_events_a_htm',
        'ptel_object_table_name_DIF_HTM25':'pairitel_events_a_htm25xx',
        'sdss_object_table_name_DIF_HTM14':'sdss_events_a_htm',
        'sdss_object_table_name_DIF_HTM25':'sdss_events_a_htm25xx',
        'rdb_user_4':"pteluser",
        'rdb_name_4':'source_db',
        'sdss_fields_table_name':'rfc_ingest_status',
        'rdb_features_user':"pteluser",
        'rdb_features_db_name':'source_db', #USE SOURCE 'features_test_db',
        'feat_lookup_tablename':'feat_lookup',
        'feat_values_tablename':'feat_values',
        'source_region_lock_dbname':'source_db',
        'source_region_lock_tablename':'source_region_locks',
        'footprint_dbname':'object_db',
        'footprint_regions_tablename':'footprint_regions',
        'footprint_values_tablename':'footprint_values',
        'xmlrpc_server_port':8000,
        'sdss_astrom_repo_host_ip':"192.168.1.55",
        'sdss_astrom_repo_dirpath':'/media/disk-4/sdss_astrom_repository',
    },
    'testvals_object_database_table_columns':{ \
        'pairitel_events_a':12,
        'pairitel_ingest_accounting':2,
        'obj_srcid_lookup':3,
        'footprint_values':4,
        'footprint_regions':5,
    },
    'testvals_source_database_table_columns':{ \
        'srcid_lookup':9,
        'source_region_locks':3,
        'feat_lookup':3,
        'feat_values':4,
    },
    'testvals_ptel_feature_boxrange':0.02,
    'testvals_ptel_feature_values':[ \
      (5, {'old dc':14.40365, 'weighted average uncertainty':240.014042127, \
           'freq ratio 2-1':0.8, 'median':14.40975, \
           'weighted average':14.4256568054,'first_frequency':0.12862724324,\
           'second':0.102901794592, 'std':0.254517518498})],
    'testvals_single_ptel_object_values':[ \
        {'ra':137.4028815, 'decl':33.0225845, 'filt':5,\
         'ra_rms':0.416186, 'jsb_mag':19.6688, 'jsb_mag_err':0.326344, \
         't':54474.3657234, 'htmID':4025698717, 'footprint_id':2}],
    'testvals_single_ptel_footprint_values':[ \
        {'footprint_id':2, 'filter_id':5, 'mag_type':9, 'mag_val':19.2991},
        {'footprint_id':2, 'filter_id':5, 'mag_type':1,  'mag_val':18.0516}],
    'testvals_ptel_source_values':[ \
        {'ra':137.41988, 'decl':33.13833, 'ra_rms':0.083636, \
        'dec_rms':0.096588, 'nobjs':18, 'htmID':4025699154}],
    'testvals_ptel_source_boxrange_table_count':(0.05,32),
    'testvals_ptel_object_table_count':32153,
    'testvals_ptel_objects_fov_props':{ # these derived from object table ranges
        'ra_min':137.2785363,
        'ra_max':137.5173698,
        'dec_min':33.0192298,
        'dec_max':33.2194623,
    },
    'ptel_mosfits_dirpath':'$HOME/scratch/TCP_tests/',
    'ptel_mosfits_fname_list':[ \
        'mosjSN.112.1-2008Jan09.fits',
        'mosjSN.112.10-2008Jan26.fits',
        'mosjSN.112.2-2008Jan10.fits',
        'mosjSN.112.3-2008Jan11.fits',
        'mosjSN.112.4-2008Jan12.fits',
        'mosjSN.112.5-2008Jan15.fits',
        'mosjSN.112.6-2008Jan16.fits',
        'mosjSN.112.7-2008Jan18.fits',
        'mosjSN.112.8-2008Jan21.fits',
        'mosjSN.112.9-2008Jan22.fits',
        'mosjSN.112.14-2008Feb09.fits',
        'mosjSN.112.17-2008Feb12.fits',
        'mosjSN.112.18-2008Feb13.fits',
        'mosjSN.112.19-2008Feb14.fits',
        'mosjSN.112.20-2008Feb17.fits',
        'mosjSN.112.21-2008Feb18.fits',
        'mosjSN.112.22-2008Feb19.fits',
        'mosjSN.112.23-2008Feb20.fits'],
    'create_object_tables_str':"""#!/bin/sh
echo "
CREATE DATABASE %s;
USE %s;
CREATE TABLE obj_srcid_lookup (src_id INT, obj_id INT UNSIGNED, survey_id TINYINT, PRIMARY KEY (survey_id, obj_id), INDEX(src_id));

# PAIRITEL Object tables:
CREATE TABLE pairitel_ingest_accounting (mosfits_name VARCHAR(30), ingest_dtime DATETIME);
CREATE TABLE pairitel_events_a (obj_id INT UNSIGNED, footprint_id INT UNSIGNED, filt TINYINT UNSIGNED, t DOUBLE, jsb_mag FLOAT, jsb_mag_err FLOAT, ra DOUBLE, decl DOUBLE, ra_rms FLOAT, dec_rms FLOAT, PRIMARY KEY (obj_id), INDEX(footprint_id));

" | mysql

$HOME/bin/dif --index-htm %s pairitel_events_a 25 ra decl < /dev/null
 
# MYSQL:
echo "
USE %s;
ALTER TABLE %s.pairitel_events_a CHANGE htmID htmID25 BIGINT;

DROP trigger %s.difu_pairitel_events_a;
DROP trigger %s.difi_pairitel_events_a;
DROP view %s.pairitel_events_a_htm;
" | mysql
 
$HOME/bin/dif --index-htm %s pairitel_events_a 14 ra decl < /dev/null
 
echo "
USE %s;
drop trigger %s.difu_pairitel_events_a;
drop trigger %s.difi_pairitel_events_a;
 
delimiter //
CREATE TRIGGER %s.difi_pairitel_events_a BEFORE INSERT ON %s.pairitel_events_a
FOR EACH ROW BEGIN
  SET NEW.htmID = DIF_HTMLookup(14, NEW.ra, NEW.decl);
  SET NEW.htmID25 = DIF_HTMLookup(25, NEW.ra, NEW.decl);
END;
//
delimiter ;
 
delimiter //
CREATE TRIGGER %s.difu_pairitel_events_a BEFORE UPDATE ON %s.pairitel_events_a
FOR EACH ROW BEGIN
  SET NEW.htmID = DIF_HTMLookup(14, NEW.ra, NEW.decl);
  SET NEW.htmID25 = DIF_HTMLookup(25, NEW.ra, NEW.decl);
END;
//
delimiter ;
 
CREATE VIEW %s.pairitel_events_a_htm25xx AS SELECT obj_id, filt, t, jsb_mag, jsb_mag_err, ra, decl, ra_rms, dec_rms, htmID25 AS htmID FROM %s.pairitel_events_a INNER JOIN DIF.dif ON (%s.pairitel_events_a.htmID25=DIF.dif.id) WHERE DIF_setHTMDepth(25) AND DIF_FineSearch(ra, decl, DIF.dif.full);
################################# :::
# SDSS Object tables:
CREATE TABLE rfc_ingest_status (run SMALLINT, field SMALLINT, camcol TINYINT, error TINYINT, ingest_status TINYINT, ingest_date DATETIME, host VARCHAR(10), INDEX USING HASH (field, camcol, run)) ENGINE=MEMORY;

LOAD DATA INFILE '%s/Data/sdss_rfc_ingest_status.cleaned_no34_with7.mysql_outfile' INTO TABLE rfc_ingest_status;

CREATE TABLE sdss_events_a (obj_id INT UNSIGNED, footprint_id INT UNSIGNED, filt TINYINT UNSIGNED, objc_type TINYINT UNSIGNED, flags INT, flags2 INT, t DOUBLE, jsb_mag FLOAT, jsb_mag_err FLOAT, ra DOUBLE, decl DOUBLE, ra_rms FLOAT, dec_rms FLOAT, htmID14 INT(10) UNSIGNED, INDEX(obj_id), INDEX(footprint_id), INDEX(htmID14)) PARTITION BY RANGE (htmID14) (
PARTITION p0 VALUES LESS THAN (2147483648),
PARTITION p1 VALUES LESS THAN (2159414112),
PARTITION p2 VALUES LESS THAN (2171344576),
PARTITION p3 VALUES LESS THAN (2183275040),
PARTITION p4 VALUES LESS THAN (2195205504),
PARTITION p5 VALUES LESS THAN (2207135968),
PARTITION p6 VALUES LESS THAN (2219066432),
PARTITION p7 VALUES LESS THAN (2230996896),
PARTITION p8 VALUES LESS THAN (2242927360),
PARTITION p9 VALUES LESS THAN (2254857824),
PARTITION p10 VALUES LESS THAN (2266788288),
PARTITION p11 VALUES LESS THAN (2278718752),
PARTITION p12 VALUES LESS THAN (2290649216),
PARTITION p13 VALUES LESS THAN (2302579680),
PARTITION p14 VALUES LESS THAN (2314510144),
PARTITION p15 VALUES LESS THAN (2326440608),
PARTITION p16 VALUES LESS THAN (2338371072),
PARTITION p17 VALUES LESS THAN (2350301536),
PARTITION p18 VALUES LESS THAN (2362232000),
PARTITION p19 VALUES LESS THAN (2374162464),
PARTITION p20 VALUES LESS THAN (2386092928),
PARTITION p21 VALUES LESS THAN (2398023392),
PARTITION p22 VALUES LESS THAN (2970685710),
PARTITION p23 VALUES LESS THAN (2982616174),
PARTITION p24 VALUES LESS THAN (2994546638),
PARTITION p25 VALUES LESS THAN (3006477102),
PARTITION p26 VALUES LESS THAN (3078059892),
PARTITION p27 VALUES LESS THAN (3089990356),
PARTITION p28 VALUES LESS THAN (3101920820),
PARTITION p29 VALUES LESS THAN (3113851284),
PARTITION p30 VALUES LESS THAN (3125781748),
PARTITION p31 VALUES LESS THAN (3137712212),
PARTITION p32 VALUES LESS THAN (3149642676),
PARTITION p33 VALUES LESS THAN (3161573140),
PARTITION p34 VALUES LESS THAN (3173503604),
PARTITION p35 VALUES LESS THAN (3185434068),
PARTITION p36 VALUES LESS THAN (3221225468),
PARTITION p37 VALUES LESS THAN (3233155932),
PARTITION p38 VALUES LESS THAN (3245086396),
PARTITION p39 VALUES LESS THAN (3257016860),
PARTITION p40 VALUES LESS THAN (3268947324),
PARTITION p41 VALUES LESS THAN (3280877788),
PARTITION p42 VALUES LESS THAN (3292808252),
PARTITION p43 VALUES LESS THAN (3364391044),
PARTITION p44 VALUES LESS THAN (3376321508),
PARTITION p45 VALUES LESS THAN (3388251972),
PARTITION p46 VALUES LESS THAN (3400182436),
PARTITION p47 VALUES LESS THAN (3435973832),
PARTITION p48 VALUES LESS THAN (3447904296),
PARTITION p49 VALUES LESS THAN (3459834760),
PARTITION p50 VALUES LESS THAN (3471765224),
PARTITION p51 VALUES LESS THAN (4044427530),
PARTITION p52 VALUES LESS THAN (4056357994),
PARTITION p53 VALUES LESS THAN (4068288458),
PARTITION p54 VALUES LESS THAN (4080218922),
PARTITION p55 VALUES LESS THAN (4151801712),
PARTITION p56 VALUES LESS THAN (4163732176),
PARTITION p57 VALUES LESS THAN (4175662640),
PARTITION p58 VALUES LESS THAN (4187593104),
PARTITION p59 VALUES LESS THAN MAXVALUE);

CREATE TABLE sdss_obj_fcr_lookup (obj_id INT UNSIGNED, field SMALLINT UNSIGNED, camcol TINYINT UNSIGNED, run SMALLINT UNSIGNED, rerun TINYINT UNSIGNED, INDEX(field, camcol, run));

" | mysql

###$HOME/bin/dif --index-htm %s sdss_events_a 14 ra decl < /dev/null
 
# MYSQL:
echo "
USE %s;
UPDATE %s.sdss_events_a SET htmID14 = DIF_HTMLookup(14, ra, decl) WHERE ISNULL(htmID14);
#ALTER TABLE %s.sdss_events_a CHANGE htmID htmID25 BIGINT;

#DROP trigger %s.difu_sdss_events_a;
#DROP trigger %s.difi_sdss_events_a;
#DROP view %s.sdss_events_a_htm;
" | mysql
 
$HOME/bin/dif --index-htm %s sdss_events_a 25 ra decl < /dev/null
 
echo "
USE %s;
drop trigger %s.difu_sdss_events_a;
drop trigger %s.difi_sdss_events_a;
DROP view %s.sdss_events_a_htm;

ALTER TABLE %s.sdss_events_a CHANGE htmID htmID25 BIGINT;
#ALTER TABLE %s.sdss_events_a CHANGE htmID14 htmID INT(20) UNSIGNED; 
delimiter //
CREATE TRIGGER %s.difi_sdss_events_a BEFORE INSERT ON %s.sdss_events_a
FOR EACH ROW BEGIN
  SET NEW.htmID14 = DIF_HTMLookup(14, NEW.ra, NEW.decl);
  SET NEW.htmID25 = DIF_HTMLookup(25, NEW.ra, NEW.decl);
END;
//
delimiter ;
 
delimiter //
CREATE TRIGGER %s.difu_sdss_events_a BEFORE UPDATE ON %s.sdss_events_a
FOR EACH ROW BEGIN
  SET NEW.htmID14 = DIF_HTMLookup(14, NEW.ra, NEW.decl);
  SET NEW.htmID25 = DIF_HTMLookup(25, NEW.ra, NEW.decl);
END;
//
delimiter ;
 
CREATE VIEW %s.sdss_events_a_htm25xx AS SELECT obj_id, footprint_id, filt, objc_type, flags, flags2, t, jsb_mag, jsb_mag_err, ra, decl, ra_rms, dec_rms, htmID25 AS htmID FROM %s.sdss_events_a INNER JOIN DIF.dif ON (%s.sdss_events_a.htmID25=DIF.dif.id) WHERE DIF_setHTMDepth(25) AND DIF_FineSearch(ra, decl, DIF.dif.full);
CREATE VIEW %s.sdss_events_a_htm AS SELECT obj_id, footprint_id, filt, objc_type, flags, flags2, t, jsb_mag, jsb_mag_err, ra, decl, ra_rms, dec_rms, htmID14 AS htmID FROM %s.sdss_events_a INNER JOIN DIF.dif ON (%s.sdss_events_a.htmID14=DIF.dif.id) WHERE DIF_setHTMDepth(14) AND DIF_FineSearch(ra, decl, DIF.dif.full);


################################# ^^^^
# Footprint Server tables:
CREATE TABLE footprint_regions (footprint_id INT NOT NULL, survey_id TINYINT, t DOUBLE, ing_date DATETIME, radec_region GEOMETRY NOT NULL, KEY(footprint_id), SPATIAL INDEX(radec_region), INDEX(t));
 
#CREATE TABLE footprint_values (footprint_id INT NOT NULL, filter_id TINYINT UNSIGNED, mag_type TINYINT UNSIGNED, mag_val FLOAT, INDEX(footprint_id), INDEX(filter_id, mag_type));

CREATE TABLE footprint_values (footprint_id INT NOT NULL, filter_id TINYINT UNSIGNED, mag_type TINYINT, mag_val FLOAT, INDEX(footprint_id), INDEX(filter_id, mag_type));

" | mysql
    """,
    'create_source_tables_str':"""#!/bin/sh
echo "
CREATE DATABASE %s;
USE %s;

CREATE TABLE srcid_lookup (src_id INT UNSIGNED, ra DOUBLE, decl DOUBLE, ra_rms FLOAT, dec_rms FLOAT, nobjs SMALLINT UNSIGNED, feat_gen_date DATETIME, PRIMARY KEY (src_id));
CREATE TABLE source_region_locks (region_id INT, radec_region GEOMETRY NOT NULL, lock_dtime DATETIME, SPATIAL INDEX(radec_region));

" | mysql
 
$HOME/bin/dif --index-htm %s srcid_lookup 25 ra decl < /dev/null

echo "

# MYSQL:
USE %s;
ALTER TABLE %s.srcid_lookup CHANGE htmID htmID25 BIGINT;
 
drop trigger %s.difu_srcid_lookup;
drop trigger %s.difi_srcid_lookup;
drop view %s.srcid_lookup_htm;
 
" | mysql
 
$HOME/bin/dif --index-htm %s srcid_lookup 14 ra decl < /dev/null

echo "
#MYSQL:
USE %s;
drop trigger %s.difu_srcid_lookup;
drop trigger %s.difi_srcid_lookup;
 
delimiter //
CREATE TRIGGER %s.difi_srcid_lookup BEFORE INSERT ON %s.srcid_lookup
FOR EACH ROW BEGIN
  SET NEW.htmID = DIF_HTMLookup(14, NEW.ra, NEW.decl);
  SET NEW.htmID25 = DIF_HTMLookup(25, NEW.ra, NEW.decl);
END;
//
delimiter ;
 
delimiter //
CREATE TRIGGER %s.difu_srcid_lookup BEFORE UPDATE ON %s.srcid_lookup
FOR EACH ROW BEGIN
  SET NEW.htmID = DIF_HTMLookup(14, NEW.ra, NEW.decl);
  SET NEW.htmID25 = DIF_HTMLookup(25, NEW.ra, NEW.decl);
END;
//
delimiter ;
 
CREATE VIEW %s.srcid_lookup_htm25xx AS SELECT src_id, ra, decl, ra_rms, dec_rms, nobjs, feat_gen_date, htmID25 AS htmID FROM %s.srcid_lookup INNER JOIN DIF.dif ON (%s.srcid_lookup.htmID25=DIF.dif.id) WHERE DIF_setHTMDepth(25) AND DIF_FineSearch(ra, decl, DIF.dif.full) ;
 
" | mysql
    """,
}
