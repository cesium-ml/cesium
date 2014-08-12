#!/usr/bin/env python 
"""
   v0.1 An example / demo file on how to connect to TCP MySQL server
"""


import sys, os
import MySQLdb
import pprint


class Postgre_Database_Class_Example:
    """
    This class is used to demo a postgre database connection.

    Specifically, it connects to the PTF navtara caltech database.
    """

    def __init__(self, pars):
        """ This is a function which is always called upon class initialization.
        
        """
        # This can set a passed in parameter dictionary to a variable which is
        #    usable through-out this class/object.
        self.pars = pars 

    def print_rows_in_html_table_form(self, rows):
        """ This demo just prints the row results in something which
        could be saved as an html file and then viewed using a web browser.
        The links for sources could then be followed.
    
        """
        out_str = ""

        out_str += """
<html><head>
</head>
<body>
<table border="1">
"""
        for row in rows:
            out_str += "<tr>\n"
            for col in row:
                out_str += "<td>%s</td>" % (str(col))
            out_str += "</tr>\n"
        out_str += """
</tr>
</table>
</body></html>
"""
        print out_str
        
        # Then, out_str could be file_pointer.write(out_str) to some .html file. 

        # You could also figure out the URL for more information about a PTF source (Caltech or a nersc.gov page, I think) and then print a link column into the above html string:
        #  something like:
        # <td><a href=\"http://some.site.org/some/dirs/and/source_identifier_goes_here.php"\">Click on this link</a></td>



    def some_main_function(self):
        """ This is the main'ish function.

        This module should work on the tranx computer (psycopg2 is installed).
        
        """

        import psycopg2
        conn = psycopg2.connect("dbname='ptfcands' user='tcp' host='navtara.caltech.edu' password='classify'");
        pg_cursor = conn.cursor()

        column_list = ['shortname', 'ra', 'dec', 'mag', 'type2', 'class', 'isspectra', 'rundate']
        column_str = ', '.join(column_list)
        select_str = "SELECT %s FROM saved_cands WHERE shortname > '' AND rundate > '20090101' ORDER BY rundate DESC LIMIT 20" % (column_str)
        # The above is the same as:
        #    SELECT shortname, ra, dec, mag, type2, class, isspectra, rundate FROM saved_cands WHERE shortname > '' AND rundate > '20090101' ORDER BY rundate DESC LIMIT 20

        pg_cursor.execute(select_str)

        rows = pg_cursor.fetchall()
        for row in rows:
            print row

        # Can also display the results in an html string (which could be written to file):
        self.print_rows_in_html_table_form(rows)



    def get_ptf_data_epoch_at_classification_time(self):
        """ This function gets the datapoint / epoch for a source, which
        is closest to the time that Mansi/Robert/Brad identified the source
        as interesting / a transient.
        
        """
        import psycopg2
        conn = psycopg2.connect("dbname='ptfcands' user='tcp' host='navtara.caltech.edu' password='classify'");
        pg_cursor = conn.cursor()

        ### NOTE: The following has some duplicate rows due to there
        #      occasionally being more than one datesave time for a
        #      particular source shortname.  Thus this isn't useful:
        #select_str = "SELECT distinct shortname, datesaved, (cast(to_char(datesaved, 'J')as real) + cast(to_char(datesaved, 'SSSS') as real)/3600./24. - 0.5) as jd  FROM annotate order by datesaved ASC"

        ### NOTE: The following only selects the row with the earliest
        #    datesaved time, thus the first classification of a source.
        ### NOTE: This also calculates a Julian-date from the
        #    string-like datesaved column.
        #select_str = "SELECT DISTINCT ON (shortname) shortname, datesaved, (cast(to_char(datesaved, 'J')as real) + cast(to_char(datesaved, 'SSSS') as real)/3600./24. - 0.5) as jd FROM annotate ORDER BY shortname, datesaved"
        ### This version JOINs with sources table to also get the
        #    ra, dec, and source-id:
        # # # # # #select_str = "SELECT DISTINCT ON (annotate.shortname) annotate.shortname, sources.id, sources.ra, sources.dec, (cast(to_char(annotate.datesaved, 'J')as real) + cast(to_char(annotate.datesaved, 'SSSS') as real)/3600./24. - 0.5) as jd FROM sources JOIN annotate ON (annotate.shortname=sources.name) ORDER BY annotate.shortname, annotate.datesaved"
        #select_str = "SELECT DISTINCT ON (annotate.shortname) annotate.shortname, sources.id, sources.ra, sources.dec, saved_cands.isspectra, (cast(to_char(annotate.datesaved, 'J')as real) + cast(to_char(annotate.datesaved, 'SSSS') as real)/3600./24. - 0.5) as jd FROM sources JOIN annotate ON (annotate.shortname=sources.name) JOIN saved_cands ON (annotate.shortname=saved_cands.shortname) WHERE saved_cands.isspectra = 't' ORDER BY annotate.shortname, annotate.datesaved"
        select_str = "SELECT DISTINCT ON (annotate.shortname) annotate.shortname, sources.id, sources.ra, sources.dec, saved_cands.isspectra, (cast(to_char(annotate.datesaved, 'J')as real) + cast(to_char(annotate.datesaved, 'SSSS') as real)/3600./24. - 0.5) as jd FROM sources JOIN annotate ON (annotate.shortname=sources.name) JOIN saved_cands ON (annotate.shortname=saved_cands.shortname) ORDER BY annotate.shortname, annotate.datesaved"
        pg_cursor.execute(select_str)
        rows = pg_cursor.fetchall()
        caltech_sources = {}
        for row in rows:
            row
            caltech_sources[row[0]] = {'shortname':row[0],
                                       'caltech_srcid':row[1],
                                       'ra':row[2],
                                       'dec':row[3],
                                       'isspectra':row[4],
                                       'jd_time':row[5]}
            print

        # NOTE: Return a single ptf-events row/epoch/observation which
        #     most closely correlates to the Caltech classification time.
        #  - Thus, we believe that the observation at this time
        #    is what the Caltech person saw when they made the initial
        #    identification and classification.
        db = MySQLdb.connect(host=pars['mysql_hostname'],
                             user=pars['mysql_user'],
                             db=pars['mysql_database'],
                             port=pars['mysql_port'])
        cursor = db.cursor()
        
        for ct_src_dict in caltech_sources.values():
            #select_str = "SELECT T1.*, (T1.ujd - 2454972.8723) AS t_aftr_classif FROM (SELECT id, ra, decl, ujd, mag, mag_err, realbogus, obj_srcid_lookup.src_id FROM ptf_events_htm JOIN obj_srcid_lookup ON (id=obj_id) WHERE obj_srcid_lookup.survey_id=3 AND DIF_HTMCircle(258.96142767, 64.23848418, 0.05)) AS T1 WHERE (T1.ujd - 2454972.8723) > -0.1 ORDER BY src_id, ujd DESC"
            select_str = """
SELECT object_test_db.obj_srcid_lookup.src_id, T1.id, T1.ujd, T1.mag, T1.realbogus, (T1.ujd - %lf) AS t_aftr_classif 
FROM
       (SELECT id, ra, decl, ujd, mag, mag_err, realbogus
        FROM object_test_db.ptf_events_htm 
        WHERE DIF_HTMCircle(%lf, %lf, 0.05)) AS T1 
JOIN object_test_db.obj_srcid_lookup ON (T1.id=object_test_db.obj_srcid_lookup.obj_id)
WHERE object_test_db.obj_srcid_lookup.survey_id=3
ORDER BY src_id, ujd DESC
            """ % (ct_src_dict['jd_time'], ct_src_dict['ra'], ct_src_dict['dec'])
            cursor.execute(select_str)
            results = cursor.fetchall()

            ct_src_dict['data'] = []
            for row in results:
                ct_src_dict['data'].append({'mysql_srcid':row[0],
                                            'mysql_objid':row[1],
                                            'ujd':row[2],
                                            'mag':row[3],
                                            'realbogus':row[4],
                                            't_after_classif':row[5]})
            pprint.pprint(ct_src_dict)


    def LBL_pgsql__query_realbogus_using_ptf_id(self):
        """
        Using a (hardcoded as an example) PTF object/event/epoch id, retrieve
            RealBogus values from LBL's PostgreSQL database.
        """
        import psycopg2
        conn = psycopg2.connect("dbname='subptf' user='dstarr' host='sgn02.nersc.gov' password='*2ta77' port=6540");
        pg_cursor = conn.cursor()

        select_str = "SELECT candidate_id, bogus, suspect, unclear, maybe, realish, realbogus FROM rb_classifier WHERE candidate_id = 3000001"
        pg_cursor.execute(select_str)
        rows = pg_cursor.fetchall()
        for row in rows:
            (candidate_id, bogus, suspect, unclear, maybe, realish, realbogus) = row
            print candidate_id, realbogus


if __name__ == '__main__':

    pars = { \
    'mysql_user':"pteluser",
    'mysql_hostname':"192.168.1.25",
    'mysql_database':'source_test_db',
    'mysql_port':3306,
        }


    Pg_Db_Class_Example = Postgre_Database_Class_Example(pars)

    Pg_Db_Class_Example.LBL_pgsql__query_realbogus_using_ptf_id()
    sys.exit()
    Pg_Db_Class_Example.get_ptf_data_epoch_at_classification_time()
    sys.exit()
    Pg_Db_Class_Example.some_main_function()


    db = MySQLdb.connect(host=pars['mysql_hostname'],
                         user=pars['mysql_user'],
                         db=pars['mysql_database'],
                         port=pars['mysql_port'])
    cursor = db.cursor()

    select_str = "SELECT src_id, ra, decl FROM srcid_lookup LIMIT 3" % ()
    cursor.execute(select_str)
    results = cursor.fetchall()
    for row in results:
        print row


    # This example queries the TCP Mysql database (on tranx), for a position,
    #    and returns all the sources, and the magnitude(time) datapoints.
    # NOTE: DIF_HTMCircle(258.96142767, 64.23848418, 0.05) means:
    #     - a 0.05 arc minute (0.05 * 1/60. degrees) radius circle is queried.
    #       which is around 3 arcseconds, and probably a good standard query for sources.
    #     - if you query less than 1 arcsecond, you may begin missing a some data for a source.
    # NOTE: "ujd" is essentially time, with 1.0 representing 1 day.  Aka Julian Date.
    #
    # NOTE: besides the "realbogus" value, there are also 5 characterstics which GroupThink uses
    #       in calculating realbogus, and may be pertinant to the real/bogus classification.
    #       Ideally, these 5 params can be hidden because the realbogus value correctly
    #       represents whether the subtracted object is real or bogus.
    #       So, for now you can just concern yourself with the "realbogus" characteristic if you want.
    #       The other 5 characteristics are:
    #            bogus | suspect | unclear | maybe | realish

    ### This selects just information from the ptf_events table:
    #    SELECT id, ra, decl, ujd, mag, mag_err, realbogus, bogus, suspect, unclear,  maybe, realish FROM ptf_events_htm WHERE DIF_HTMCircle(258.96142767, 64.23848418, 0.05);

    ### This does the above select (without the 5 extra characteristics),
    #     but also including the associated TCP source-id.
    """
SELECT id, ra, decl, ujd, mag, mag_err, realbogus, obj_srcid_lookup.src_id FROM ptf_events_htm JOIN obj_srcid_lookup ON (id=obj_id) WHERE obj_srcid_lookup.survey_id=3 AND DIF_HTMCircle(258.96142767, 64.23848418, 0.05);
+---------+--------------+--------------+---------------+---------+---------+-----------+--------+
| id      | ra           | decl         | ujd           | mag     | mag_err | realbogus | src_id |
+---------+--------------+--------------+---------------+---------+---------+-----------+--------+
| 4731119 | 258.96127891 | 64.238416648 |  2454972.8723 |  18.784 |  0.0226 |     0.002 |  50343 | 
| 4731815 | 258.96142767 |  64.23848418 | 2454972.91348 | 19.8342 |  0.0788 |     0.019 |  50343 | 
+---------+--------------+--------------+---------------+---------+---------+-----------+--------+

select sources.name, sources.ra, sources.dec, phot.mag, phot.emag, phot.filter, phot.obsdate from sources JOIN phot ON (phot.sourceid=sources.id) where sources.name='09aa' ORDER BY obsdate;

 name |     ra     |   dec    |   mag   |   emag   | filter |         obsdate         
------+------------+----------+---------+----------+--------+-------------------------
 09aa | 173.336234 | -9.41118 |     999 |      999 | R      | 2009-02-20 06:46:01.983
 09aa | 173.336234 | -9.41118 |     999 |      999 | R      | 2009-02-20 10:14:15.683
 09aa | 173.336234 | -9.41118 |     999 |      999 | R      | 2009-02-24 10:11:24.683
 09aa | 173.336234 | -9.41118 |     999 |      999 | g      | 2009-02-28 06:05:30.783
 09aa | 173.336234 | -9.41118 |     999 |      999 | g      | 2009-02-28 08:00:10.433


select sources.name, sources.ra, sources.dec, annotations.username, annotations.type, annotations.comment from sources JOIN annotations ON (annotations.sourceid=sources.id) where sources.name='09aa' limit 10;

name |     ra     |   dec    | username |      type      |  comment  
------+------------+----------+----------+----------------+-----------
 09aa | 173.336234 | -9.41118 | robert   | classification | SN Ia
 09aa | 173.336234 | -9.41118 | robert   | redshift       | 0.12
 09aa | 173.336234 | -9.41118 | robert   | type           | Transient

######

select src_id, ptf_events.id, ptf_events.ujd, ptf_events.mag, ptf_events.realbogus
       from obj_srcid_lookup
       JOIN ptf_events ON (ptf_events.id=obj_srcid_lookup.obj_id)
       WHERE src_id=(SELECT src_id FROM obj_srcid_lookup WHERE obj_id = 4227695 AND survey_id = 3);


mysql> select src_id, ptf_events.id, ptf_events.ujd, ptf_events.mag, ptf_events.realbogus from obj_srcid_lookup JOIN ptf_events on (ptf_events.id=obj_srcid_lookup.obj_id) WHERE src_id=(select src_id from obj_srcid_lookup where obj_id = 4227695);
+--------+---------+---------------+---------+------------+
| src_id | id      | ujd           | mag     | realbogus  |
+--------+---------+---------------+---------+------------+
| 466081 | 4227695 | 2454972.93413 | 19.3241 |  0.0248442 | 
| 466081 | 4226964 | 2454972.90348 | 19.8569 | 0.00284416 | 
+--------+---------+---------------+---------+------------+
2 rows in set (0.05 sec)



ptfcands=> select * from sources order by creationdate DESC limit 50;
  id  | sub_id | cand_id | name | iauname | status | programid |     ra     |    dec    | era | edec | classification | redshift |        creationdate        |        lastmodified        | priority | scheduling 
------+--------+---------+------+---------+--------+-----------+------------+-----------+-----+------+----------------+----------+----------------------------+----------------------------+----------+------------
 1266 |  12985 | 4447384 | 09ke |         | active |        -1 | 215.047294 | 51.740923 |     |      |                |          | 2009-05-21 20:12:06.438379 | 2009-05-21 20:12:06.438379 |        5 | auto
 1265 |  12433 | 4256479 | 09kd |         | active |        -1 | 255.859193 | 43.766691 |     |      |                |          | 2009-05-21 19:47:39.956362 | 2009-05-21 19:47:39.956362 |        5 | auto
 1264 |  13213 | 4543054 | 09kc |         | active |        -1 | 186.805834 |  61.72272 |     |      |                |          | 2009-05-21 18:16:40.154638 | 2009-05-21 18:16:40.154638 |        5 | auto
 1263 |  11686 | 3985221 | 09kb |         | active |        -1 | 189.694058 | 79.645662 |     |      |                |          | 2009-05-20 23:34:38.119103 | 2009-05-20 23:34:38.119103 |        5 | auto
 1262 |  11444 | 3843122 | 09ka |         | active |        -1 | 257.394746 | 72.060907 |     |      |                |          | 2009-05-20 23:28:03.399104 | 2009-05-20 23:28:03.399104 |        5 | auto
 1261 |  10949 | 3605721 | 09jz |         | active |        -1 | 195.106203 | 67.460265 |     |      |                |          | 2009-05-20 23:07:32.438336 | 2009-05-20 23:07:32.438336 |        5 | auto
 1260 |  11139 | 3692473 | 09jy |         | active |        -1 | 263.846781 | 68.123137 |     |      |                |          | 2009-05-20 22:31:23.594331 | 2009-05-20 22:31:23.594331 |        5 | auto
 1259 |  10799 | 3556880 | 09jx |         | active |        -1 | 203.348915 | 59.348204 |     |      |                |          | 2009-05-20 22:25:08.14293  | 2009-05-20 22:25:08.14293  |        5 | auto
 1258 |  10581 | 3482376 | 09jw |         | active |        -1 | 193.598873 | 56.732591 |     |      |                |          | 2009-05-20 22:23:32.550871 | 2009-05-20 22:23:32.550871 |        5 | auto





    """








    """
on tranx/192.168.1.25:

mysql -u pteluser


show databases;

use source_test_db;

show tables;

select * from srcid_lookup limit 3;


### This gets all features available:

SELECT feat_name FROM feat_lookup WHERE filter_id=8 AND is_internal=0 ORDER BY feat_name


### This gets all features for an (assumed PTF) source & prints them out with feature-names:

select src_id, feat_id, feat_name, feat_val from feat_values JOIN feat_lookup USING (feat_id) WHERE filter_id=8 AND  src_id = 118 ORDER BY feat_name;
+--------+---------+--------------------------------------+------------------+
| src_id | feat_id | feat_name                            | feat_val         |
+--------+---------+--------------------------------------+------------------+
|    118 |    1061 | amplitude                            |        0.5036405 | 
|    118 |     287 | beyond1std                           |                0 | 
|    118 |     440 | chi2                                 |    57122.0446203 | 


### This mimics the query on the tcp_ptf_summary.php webpage:

SELECT x.feat_val, y.feat_val FROM feat_values AS x 
          JOIN srcid_lookup USING (src_id)
    INNER JOIN feat_values AS y 
            ON y.src_id = x.src_id
           AND y.feat_id=(SELECT feat_id FROM feat_lookup WHERE (
                          feat_lookup.filter_id = 8 AND
                          feat_lookup.feat_name = 'std'))
         WHERE x.feat_id=(SELECT feat_id FROM feat_lookup WHERE (
                          feat_lookup.filter_id = 8 AND
                          feat_lookup.feat_name = 'median'))
               AND srcid_lookup.nobjs >= 15;


#######################

# How to connect to Caltech PostgreSQL server:

#  -  use tranx
#  - password : classify

psql -d ptfcands -U tcp -h navtara.caltech.edu --password

### Commands:
# (NOTE: I'm not sure why, by /d and /dt don't work, which would normally allow us to see other tables & databases.  Maybe this has been disabled for the tcp user).

\h         # help, lists SQL commands
\h SELECT  # gives help on a particular command

######
# Here is what columns are in the ptfcands.saved_cands table:
ptfcands=> select * from saved_cands limit 1;
 canname |     ra     |    dec    |   x    |   y    |                     expname                     | scanner |       ip        | class | comments | datesaved |  a   |  b   |   mag   | fwhm | sigma | max2sig | max3sig | flag |   type    | rundate  | visit | field  | chip | shortname | isspectra |   z   | cannum | phase |   specdate    | date | id | sub_id | obsjd |      type2      
---------+------------+-----------+--------+--------+-------------------------------------------------+---------+-----------------+-------+----------+-----------+------+------+---------+------+-------+---------+---------+------+-----------+----------+-------+--------+------+-----------+-----------+-------+--------+-------+---------------+------+----+--------+-------+-----------------
         | 120.196928 | 46.948476 | 1786.7 | 3495.8 | PTF200903171418_2_o_14865_00.w_cd.ptf_100224_00 | mansi   | 198.202.125.194 | Ia    |          |           | 0.85 | 0.79 | 20.1955 |  2.4 |  7.73 |       5 |       1 |    0 | Transient | 20090317 | 1     | 100224 | 0    | 09h       | t         | 0.121 |     12 | -2d   | Mar 20.360082 |      |    |        |       | SurelyTransient
         
         | 171.386532 | 13.636271 |   1386 |  218.6 | PTF200903023554_1_o_12989_09.w_cd.ptf_002_09    | robert  | 75.27.243.136   |       |          |           | 1.31 | 1.27 | 19.0126 | 2.91 |  16.3 |       1 |       0 |    0 | Rock      |          |       |        |      | None      |           |       |        |       |               |      |    |        |       |
         
         | 171.167212 | 13.376099 |  628.4 | 1144.2 | PTF200903023554_1_o_12989_09.w_cd.ptf_002_09    | robert  | 75.27.243.136   |       |          |           | 1.38 | 1.27 | 18.6404 | 3.24 | 21.42 |       0 |       0 |    0 | Rock      |          |       |        |      | None      |           |       |        |       |               |      |    |        |       | 






"""
