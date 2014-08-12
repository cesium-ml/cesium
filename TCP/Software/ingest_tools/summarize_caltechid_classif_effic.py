#!/usr/bin/env python 
""" summarize how well general classifications of ptf09xxx were made,
when compared with caltech followup statictics
"""

import sys, os
try:
    import psycopg2
except:
    print "UNABLE to import psycopg2"
    pass
import MySQLdb
import pprint


class CaltechDB:
    """ Everything related to connections with caltech pgsql db
    """
    def __init__(self):
        pass

    def fill_overall_dict_with_caltech_followup_info(self, overall_dict):
        """ Given a candidate shortname, get candidate ra,dec, other info.
        """
        self.conn = psycopg2.connect("dbname='ptfcands' user='tcp' host='navtara.caltech.edu' password='classify'");
        self.pg_cursor = self.conn.cursor()

        for overall_class_type, class_dict in overall_dict.iteritems():
            for shortname in class_dict['shortname_list']:
                # TODO: query caltech pgsql database for info using this shortname.
                select_str = """SELECT telescope, camera, filter, mag, issub
                                FROM photometry WHERE shortname='%s'""" % ( \
                                                             shortname)
                self.pg_cursor.execute(select_str)
                rows = self.pg_cursor.fetchall()
                followup_count = 0
                if len(rows) > 0:
                    for row in rows:
                        (telescope, camera, filt, mag, issub) = row
                        if filt in ['zpr', 'ipr', 'gpr', 'rpr', 'B', 'upr']:
                            # we want both limiting mag & detections
                            #if mag > -99:
                            followup_count += 1
                        else:
                            print "!!! %s  telescope=%s camera=%s filt=%s mag=%lf issub=%s" % (shortname, telescope, camera, filt, mag, issub)
                    # TODO: then count the number of spectroscopic & imaging
                if not overall_dict[overall_class_type]['followup_count_dict'].has_key(followup_count):
                    overall_dict[overall_class_type]['followup_count_dict'][followup_count] = []
                overall_dict[overall_class_type]['followup_count_dict'][followup_count].append(shortname)
                #print shortname, "followup_count:", followup_count
        self.conn.close()


    def fill_overall_dict_with_caltech_spec_class_info(self, overall_dict):
        """ Given a candidate shortname, get candidate ra,dec, other info.
        """
        self.conn = psycopg2.connect("dbname='ptfcands' user='tcp' host='navtara.caltech.edu' password='classify'");
        self.pg_cursor = self.conn.cursor()

        for overall_class_type, class_dict in overall_dict.iteritems():
            for shortname in class_dict['shortname_list']:
                # TODO: query caltech pgsql database for info using this shortname.
                select_str = """SELECT type, comment from sources join annotations on (sources.id=annotations.sourceid) where annotations.type='classification' AND name='%s'""" % (shortname)
                self.pg_cursor.execute(select_str)
                rows = self.pg_cursor.fetchall()
                specclass_count = 0
                if len(rows) > 0:
                    for row in rows:
                        (type, comment) = row
                        if not overall_dict[overall_class_type]['specclass_types_dict'].has_key(comment):
                            overall_dict[overall_class_type]['specclass_types_dict'][comment] = []
                        if not shortname in overall_dict[overall_class_type]['specclass_types_dict'][comment]:
                            overall_dict[overall_class_type]['specclass_types_dict'][comment].append(shortname)
                    # This condition is redundant now that I look at it:
                    if not shortname in overall_dict[overall_class_type]['specclass_ids']:
                        overall_dict[overall_class_type]['specclass_ids'].append(shortname)
        self.conn.close()


class MysqlLocalDB:
    """ Everything related to local tranx mysqldb querying.
    """
    def __init__(self):
        pars = { \
        'mysql_user':"pteluser",
        'mysql_hostname':"192.168.1.25",
        'mysql_database':'source_test_db',
        'mysql_port':3306,
            }

        db = MySQLdb.connect(host=pars['mysql_hostname'],
                             user=pars['mysql_user'],
                             db=pars['mysql_database'],
                             port=pars['mysql_port'])
        self.cursor = db.cursor()
        

    def get_caltechid_overall_classifications(self):
        """ query caltech_classif_summary table and fill dict.
        """
        select_str = "SELECT caltech_candidate_shortname, tcp_source_id, overall_class_type, overall_science_class, overall_class_prob FROM source_test_db.caltech_classif_summary"

        self.cursor.execute(select_str)
        results = self.cursor.fetchall()

        id_dict = {}
        overall_dict = {}
        for row in results:
            shortname = row[0]
            tcp_source_id = row[1]
            overall_class_type = row[2]
            overall_science_class = row[3]
            overall_class_prob = row[4]

            id_dict[shortname] = {'shortname':shortname,
                                  'tcp_source_id':tcp_source_id,
                                  'overall_class_type':overall_class_type,
                                  'overall_science_class':overall_science_class,
                                  'overall_class_prob':overall_class_prob}
            if not overall_dict.has_key(overall_class_type):
                overall_dict[overall_class_type] = {'followup_count_dict':{},
                                                    'specclass_types_dict':{},
                                                    'specclass_ids':[],
                                                    'shortname_list':[]}
            overall_dict[overall_class_type]['shortname_list'].append(shortname)
        return (id_dict, overall_dict)


def get_followup_summary_for_classtype(class_dict):
    """
    """
    total_all_count = 0
    total_follow_count = 0
    count_list = class_dict['followup_count_dict'].keys()
    count_list.sort()
    for count_num in count_list:
        #print overall_class_type, count_num, len(class_dict['followup_count_dict'][count_num])
        total_all_count += len(class_dict['followup_count_dict'][count_num])
        if count_num > 0:
            total_follow_count += len(class_dict['followup_count_dict'][count_num])
    most_followed_ptfids = []
    count_list.reverse()
    for count_num in count_list:
        most_followed_ptfids.extend(class_dict['followup_count_dict'][count_num][:(3 - len(most_followed_ptfids))])
        if len(most_followed_ptfids) >= 3:
            break
    return (total_all_count, total_follow_count, most_followed_ptfids)


def summarize_overall_dict(overall_dict):
    """ Display a summary of general classes in overall_dict.
    """
    overall_class_sort_list = overall_dict.keys()
    overall_class_sort_list.sort()
    for overall_class_type in overall_class_sort_list:
        class_dict = overall_dict[overall_class_type]
        (total_all_count, total_follow_count, most_followed_ptfids) = \
                             get_followup_summary_for_classtype(class_dict)
        print overall_class_type, "  TOTAL sources:", total_all_count, \
              ", % with Followup:", total_follow_count / float(total_all_count), most_followed_ptfids

        print "#####", overall_class_type
        pprint.pprint(class_dict['specclass_types_dict'])
        #print "#", overall_class_type, "class_dict['specclass_ids']"
        #pprint.pprint(class_dict['specclass_ids'])



class HTMLizeResults:
    """ Display results in overall_dict... in some .html file
    for further analysis.
    """

    def generate_subtable(self, a, overall_type, class_dict):
        """
        """
        (total_all_count, total_follow_count, most_followed_ptfids) = \
                         get_followup_summary_for_classtype(class_dict)

        a += '<TABLE BORDER="1" CELLPADDING=4 CELLSPACING=1>'
        a += '<tr><td  colspan="20"><b>%s</b></td></tr>' % (overall_type)
        source_count = 0
        for spec_class_name,ptfid_list in class_dict['specclass_types_dict'].iteritems():
            if spec_class_name in ['AGN', 'AGN?', 'SN', 'SN Ia', 'SN Ib/c', 'SN II', 'SN?', 'galaxy']:
                a += "<tr>"
                a += '<td style="border: none">&nbsp;&nbsp;&nbsp;</td><td style="border: none"><b>%s</b></td><td style="border: none">&nbsp;&nbsp;</td>' % (spec_class_name)
                for ptf_id in ptfid_list:
                    source_count += 1
                    a += """<td><a href="http://navtara.caltech.edu/cgi-bin/ptf/quicklc.cgi?name=%s">%s</a></td>""" % (ptf_id, ptf_id)
                a += "</tr>"
                
        a += '<tr><td style="border: none">%d</td><td style="border: none" colspan="20">&nbsp;&nbsp;&nbsp; spectroscopically confirmed SN/AGN</td></tr>' % (source_count)
        a += '<tr><td style="border: none">%d</td><td style="border: none" colspan="20">&nbsp;&nbsp;&nbsp; of 3177 ptf09xxx sources</td></tr>' % (total_all_count)
        a += "</table>"

        return a


    def main(self, overall_dict):
        """ Main 
        a += ""
        a += "<td></td>"
        a += "<tr><td></td></tr>"
        """
        a = """<HTML>
                <body>"""

        a += '<TABLE BORDER="0" CELLPADDING=4 CELLSPACING=1>'
        
        a += "<tr>"
        ######################
        a += " <td>Interesting SN/AGN<br> with spatial context</td>"
        a += " <td>"
        for overall_type in ['AGN_short_candid', 'SN_junk', 'AGN_junk', 'AGN_long_candid', 'SN_long_candid', 'SN_short_candid']:
            class_dict = overall_dict[overall_type]
            a = self.generate_subtable(a, overall_type, class_dict)
        a += " </td>"
        ######################
        a += " <td>Interesting without<br> spatial context</td>"
        a += " <td>"
        for overall_type in ['RBRatio_pass_only', 'RBRatio_nonperiodic_']:
            class_dict = overall_dict[overall_type]
            a = self.generate_subtable(a, overall_type, class_dict)
        a += " </td>"
        ######################
        a += " <td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Uninteresting</td>"
        a += " <td>"
        for overall_type in ['junk', 'rock', 'periodic_variable', 'RBRatio_periodic_can', 'nonRBRatio_long_cand', 'short_candid']:
            class_dict = overall_dict[overall_type]
            a = self.generate_subtable(a, overall_type, class_dict)
        a += " </td>"
        ######################
        a += "</tr>"
        a += "</table>"
        a += """</body>
                </html>"""
        fp = open("/tmp/summarize_caltechid_classif_effic.html", "w")
        fp.write(a)
        fp.close()
        os.system("scp /tmp/summarize_caltechid_classif_effic.html pteluser@lyra.berkeley.edu:www/tcp/")
        print "yo"


if __name__ == '__main__':

    Caltech_DB = CaltechDB()
    Mysql_Local_DB = MysqlLocalDB()

    (id_dict, overall_dict) = Mysql_Local_DB.get_caltechid_overall_classifications()

    Caltech_DB.fill_overall_dict_with_caltech_followup_info(overall_dict)
    Caltech_DB.fill_overall_dict_with_caltech_spec_class_info(overall_dict)

    #summarize_overall_dict(overall_dict)

    HTMLize_Results = HTMLizeResults()
    HTMLize_Results.main(overall_dict)

    # TODO: get ptf09xxx sources from mysql -> caltech_classif_summary
    #   - get shortname, overall class name, science_class, class_prob
    #   - place results in dict{}:
    #    {overall_class:{followup_count_dict:{0:[<ids>]  # all ids

    # TODO: for each shortname, query Caltech Postgresql
    #   - get user comments
    #   - get followup telescope info, number of observations, instrument type.
    #   - fill existing dict:
    #    {overall_class:{has_spectra_ids:[]     # followup with telescope with spectrograph.
    #                    followup_count_dict:{0:[<ids>]  # all ids
    #                                         1:[<ids>]
    #                                         2:[<ids>]
    #                                         3:[<ids>] ....

