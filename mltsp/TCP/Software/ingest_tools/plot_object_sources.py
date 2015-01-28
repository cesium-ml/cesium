#!/usr/bin/env python 
""" plot_object_sources.py

   v0.1 Generate image of SDSS-II image and overplot source & object positions

   TODO: need to access tranx's SDSS-II RDB
          - ? can I query tranx RDB for source & object data?

   TODO: could allow an additional XMLRPC server call to ensure all sources
         are generated for a (ra,dec) region.

"""
import sys, os
import MySQLdb
import urllib
import numpy 

pars = {\
    'local_rdb': {\
        'rdb_hostname':'127.0.0.1',
        'rdb_username':'',
        'rdb_port':3306,
        'rdb_source_db':'source_test_db',
        'rdb_object_db':'object_test_db'},
    'remote_rdb': {\
        'rdb_hostname':'192.168.1.25',
        'rdb_username':'pteluser',
        'rdb_port':3306,
        'rdb_source_db':'source_db',
        'rdb_object_db':'object_db'},
    'source_coord_fpath':'/tmp/source_coords.dat',

    'astrometry_tgz_hostname':'192.168.1.55',
    'astrometry_tgz_username':'pteluser',
    'astrometry_tgz_base_dirpath':'/media/disk-4/sdss_astrom_repository',

    'footprint_preamble':"""inputFile=;do_bestBox=yes;Submit=Submit%20Request""",
    'sdss_footprint_urls':{'DRSN1':"http://sdssw1.fnal.gov/DRSN1-cgi-bin/FOOT?",
                           'DRsup':"http://sdssw1.fnal.gov/DRsup-cgi-bin/FOOT?"},
    'coord_file_header':"""# Region file format: DS9 version 4.0
# Filename: /home/dstarr/scratch/TCP_tests/sdss_astrom_repository/5781/710/fpC-005781-r1-0710.fit
global color=green font="helvetica 10 normal" select=1 highlite=1 edit=1 move=1 delete=1 include=1 fixed=0 source
fk5
"""
    }


def get_field_cam_run_using_radec(pars, ra, dec, survey='DRSN1'):
    """ Given a (ra,dec), retrieve a list of SDSS (field,camcol,run).
    This code is derived from jbloom's sdss_astrophot.py.run_from_pos()

    NOTE: This method is duplicated from ingest_tools.py:TCP_Runtime_Methods
    """
    # http://sdssw1.fnal.gov/DRSN1-cgi-bin/FOOT?csvIn=ra%2Cdec%0D%0A30.0%2C-1.0%0D%0A;inputFile=;do_bestBox=yes;Submit=Submit%20Request
    tmp = """ra,dec\n%f,%f""" % (ra,dec)
    params = urllib.urlencode({'csvIn': tmp})
    random_fpath ="/tmp/%d.wget"%(numpy.random.random_integers(1000000000))
    wget_str = 'wget -t 1 -T 5 -O %s "%s%s;%s"' % (random_fpath, \
                                     pars['sdss_footprint_urls'][survey], \
                                     params, pars['footprint_preamble'])
    print "wget do:", wget_str
    os.system(wget_str)
    print "wget done"
    footret = open(random_fpath).read()
    os.system("rm %s" % (random_fpath))
    #f =urllib.urlopen(pars['sdss_footprint_urls'][survey], "%s;%s" % (params,pars['footprint_preamble']))
    #footret =  f.read()
    #f.close()
    start = footret.find("<pre>")
    end = footret.find("</pre>")
    if start == -1 or end == -1:
        print "ERROR: Bad return from footprint server.(ra,dec):", ra, dec
        return
    res_string = footret[start+5:end]
    res_str_list = res_string.split('\n')
    #res_string:
    #ra,        dec,       run,  rerun, camcol, field,  rowc, colc
    # 49.621196,  -1.008420, 4849,   40,    1,  786,   611.30, 443.51
    #...
    # 49.621196,  -1.008420, 6314,   40,    1,  658,   743.15, 448.94
    out_fcr_tup_list = []
    # NOTE: I believe the first line of res_string
    #       is a preamble and can be skipped:
    for row in res_str_list:
        if ((len(row) < 10) or ('rowc, colc' in row)):
            continue # skip (normally) the first and last lines
        vals = row.split(',')
        fcr_tup = (vals[5].strip(), vals[4].strip(), vals[2].strip())
        out_fcr_tup_list.append(fcr_tup)
    return out_fcr_tup_list


class Plot_Object_Sources:
    def __init__(self, pars, use_remote_servers=False):
        self.pars = pars
        self.use_remote_servers = use_remote_servers

        if self.use_remote_servers:
            self.rdb_pars = self.pars['remote_rdb']
        else:
            self.rdb_pars = self.pars['local_rdb']
        self.db = MySQLdb.connect(host=self.rdb_pars['rdb_hostname'], \
                             user=self.rdb_pars['rdb_username'], \
                             db=self.rdb_pars['rdb_source_db'], \
                             port=self.rdb_pars['rdb_port'])
        self.cursor = self.db.cursor()


    def scp_remote_sdss_fit_tgz(self, fcr_tup, gzip_dirpath, gzip_fpath, fits_fpath):
        """ Scp .tgz file of SDSS-II FITs image/astrometry data.  Store in
        expected local directory paths.
        """

        dir_1 = "%s/scratch/TCP_tests/sdss_astrom_repository/%s" % \
                    (os.path.abspath(os.environ.get("HOME")), fcr_tup[2])
        if not os.path.exists(dir_1):
            os.system("mkdir " + dir_1)

        dir_2 = "%s/scratch/TCP_tests/sdss_astrom_repository/%s/%s" % \
                    (os.path.abspath(os.environ.get("HOME")), \
                     fcr_tup[2], fcr_tup[0])
        if not os.path.exists(dir_2):
            os.system("mkdir " + dir_2)


        scp_string = "scp %s@%s:%s/%s/%s/%s_%s_%s.tgz %s/" % (\
                         self.pars['astrometry_tgz_username'], \
                         self.pars['astrometry_tgz_hostname'], \
                         self.pars['astrometry_tgz_base_dirpath'], \
                         fcr_tup[2], fcr_tup[0], \
                         fcr_tup[2], fcr_tup[1], fcr_tup[0], dir_2)

        os.system(scp_string)


    def form_local_sdss_fits_path_list(self, out_fcr_tup_list, \
                                       retrieve_remote_sdss_fits_tgz=False):
        """ Given a list of SDSS 'FCR' tuples, form and return (a list of)
        local filepath of a related SDSS FITs image.

        Returns: [] of fits filepaths.
        """
        if len(out_fcr_tup_list) == 0:
            return []

        fits_list = []
        for fcr_tup in out_fcr_tup_list:
            gzip_dirpath = \
                    "%s/scratch/TCP_tests/sdss_astrom_repository/%s/%s" % \
                    (os.path.abspath(os.environ.get("HOME")), \
                     fcr_tup[2], fcr_tup[0])
            gzip_fpath = "%s/%s_%s_%s.tgz" % \
                              (gzip_dirpath, fcr_tup[2], fcr_tup[1], fcr_tup[0])

            fits_fpath = "%s/fpC-%0.6d-r%d-%0.4d.fit" % (\
                               gzip_dirpath, \
                               int(fcr_tup[2]), \
                               int(fcr_tup[1]), \
                               int(fcr_tup[0]))

            if os.path.exists(fits_fpath):
                fits_list.append(fits_fpath)
                continue # goto next file without untar

            if retrieve_remote_sdss_fits_tgz:
                self.scp_remote_sdss_fit_tgz(fcr_tup, gzip_dirpath, gzip_fpath, fits_fpath)

            if os.path.exists(gzip_fpath):
                gzip_dirpath = gzip_dirpath
                gzip_fpath = gzip_fpath
                fcr_tup = fcr_tup
                if len(gzip_fpath) == 0:
                    continue

                os.chdir(gzip_dirpath)
                untar_command = "tar -xzf %s" % (gzip_fpath)
                os.system(untar_command)

                if os.path.exists(fits_fpath):
                    fits_list.append(fits_fpath)
                else:
                    continue
        return fits_list


    def rdb_get_object_source_lists(self, ra, dec, radius_degrees, \
                                    plot_objects=False):
        """ Given ra,dec and search radius, retrieve sources and objects from
        RDB.
        Return: filepath to source-coord list file.
        """
        radius_arcmins = radius_degrees * 60.0
        if plot_objects:
            select_str = """SELECT %s.obj_srcid_lookup.obj_id,
                               srcid_lookup_htm.src_id, 
                               srcid_lookup_htm.ra,
                               srcid_lookup_htm.decl,
                               srcid_lookup_htm.nobjs,
                               %s.sdss_events_a.ra,
                               %s.sdss_events_a.decl
                        FROM srcid_lookup_htm
                        JOIN %s.obj_srcid_lookup USING (src_id)
                        JOIN %s.sdss_events_a USING (obj_id)
                        WHERE (DIF_HTMCircle(%lf,%lf,%lf))""" % \
                           (self.rdb_pars['rdb_object_db'], \
                            self.rdb_pars['rdb_object_db'], \
                            self.rdb_pars['rdb_object_db'], \
                            self.rdb_pars['rdb_object_db'], \
                            self.rdb_pars['rdb_object_db'], \
                            ra, dec, radius_arcmins)
        else:
            select_str = """SELECT %s.obj_srcid_lookup.obj_id,
                               srcid_lookup_htm.src_id, 
                               srcid_lookup_htm.ra,
                               srcid_lookup_htm.decl,
                               srcid_lookup_htm.nobjs
                        FROM srcid_lookup_htm
                        JOIN %s.obj_srcid_lookup USING (src_id)
                        WHERE (DIF_HTMCircle(%lf,%lf,%lf))""" % \
                           (self.rdb_pars['rdb_object_db'], \
                            self.rdb_pars['rdb_object_db'], \
                            ra, dec, radius_arcmins)

        self.cursor.execute(select_str)
        results = self.cursor.fetchall()

        if os.path.exists(self.pars['source_coord_fpath']):
            os.system("rm " + self.pars['source_coord_fpath'])
        fp = open(self.pars['source_coord_fpath'], 'w')
        fp.write(self.pars['coord_file_header'])
        fp.write("circle  %sd %sd 0.004# color=red\n" % (ra, dec))
        for result in results:
            fp.write("circle %sd %sd 0.001d\n" % (result[2], result[3]))
            fp.write("text %sd %sd {%d}\n" % (result[2], result[3] + 0.002, \
                                              result[4]))
            if plot_objects:
                # The single epoch 'objects' reside in sources, so don't plot:
                fp.write("point %sd %sd # color=red point=circle \n" % (result[5], result[6]))
        fp.close()
        return self.pars['source_coord_fpath']


    def ds9_plot_for_radec(self, ra, dec, radius):
        """ Main method.
        """
        out_fcr_tup_list = get_field_cam_run_using_radec(pars, ra, dec, \
                                                         survey='DRSN1')

        fits_list = self.form_local_sdss_fits_path_list(out_fcr_tup_list, \
                                                 retrieve_remote_sdss_fits_tgz=\
                                                        self.use_remote_servers)
        if len(fits_list) == 0:
            print "Unable to find SDSS-II Fits image for:", ra, dec
            return

        source_coords_fpath = self.rdb_get_object_source_lists(ra, dec, radius,\
                                                             plot_objects=False)

        ds9_string = 'ds9 -zscale -scale squared '
        ds9_string = "%s %s -zoom to fit -regions load %s " % (ds9_string, fits_list[0], source_coords_fpath)
        for individ_fits_fpath in fits_list[1:]:
            ds9_string = "%s %s -regions load %s " % (ds9_string, individ_fits_fpath, source_coords_fpath)

        ds9_string += ' -frame first -match frames wcs -blink' # -single' # -blink'
        print ds9_string
        os.system(ds9_string)

if __name__ == '__main__':

    #ra =  49.542879
    #dec = -0.862398
    #radius = 0.03
    ra =  316.5015
    dec = 0.4299
    radius = 0.03

    pos = Plot_Object_Sources(pars, use_remote_servers=True)
    pos.ds9_plot_for_radec(ra, dec, radius)
