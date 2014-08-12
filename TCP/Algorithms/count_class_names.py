#!/usr/bin/env python
""" Tally the occurances of various science classes found in class_names datafile
"""
import os, sys
import pprint
import MySQLdb

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

db = tutor_db()


lines = open('class_names').readlines()

tally_dict = {}
for line in lines:
    class_name = line.strip()
    if not tally_dict.has_key(class_name):
        tally_dict[class_name] = [1, class_name]
    else:
        tally_dict[class_name][0] += 1

sorted_elems = tally_dict.values()
sorted_elems.sort(reverse=True)

for a in sorted_elems:
    class_name = a[1].replace(' - ','%')
    select_str = 'SELECT * FROM classes WHERE class_name like "' + class_name + '" AND class_is_active="yes" AND class_is_public="yes"'
    db.tutor_cursor.execute(select_str)
    results = db.tutor_cursor.fetchall()
    if len(results) < 1:
        select_str = 'SELECT * FROM classes WHERE class_name like "%' + class_name + '%" AND class_is_active="yes" AND class_is_public="yes"'
        db.tutor_cursor.execute(select_str)
        results = db.tutor_cursor.fetchall()
    if len(results) < 1:
        select_str = 'SELECT * FROM classes WHERE class_name like "' + class_name + '" AND class_is_active="yes" AND class_is_public="no"'
        db.tutor_cursor.execute(select_str)
        results = db.tutor_cursor.fetchall()
    try:
        print "%4d %35s http://dotastro.org/lightcurves/class.php?Class_ID=%d " % (a[0], a[1], int(results[0][0]))
    except:
        print "!!!", len(results), class_name


"""
Num sources         science class        URL to description, class heirarchy
-----------         -------------        -----------------------------------
1048                   Classical Cepheid http://dotastro.org/lightcurves/class.php?Class_ID=238 
 889            W Ursae Majoris -  W UMa http://dotastro.org/lightcurves/class.php?Class_ID=85 
 515                         Beta Persei http://dotastro.org/lightcurves/class.php?Class_ID=253 
 240                          Beta Lyrae http://dotastro.org/lightcurves/class.php?Class_ID=251 
 223                  Type Ia Supernovae http://dotastro.org/lightcurves/class.php?Class_ID=182 
 189          RR Lyrae, Fundamental Mode http://dotastro.org/lightcurves/class.php?Class_ID=218 
 150                         Delta Scuti http://dotastro.org/lightcurves/class.php?Class_ID=211 
 121                     W Ursae Majoris http://dotastro.org/lightcurves/class.php?Class_ID=252 
 113                                Mira http://dotastro.org/lightcurves/class.php?Class_ID=208 
 110               RR Lyrae, Double Mode http://dotastro.org/lightcurves/class.php?Class_ID=220 
 110                  Pulsating Variable http://dotastro.org/lightcurves/class.php?Class_ID=203 
 107               Multiple Mode Cepheid http://dotastro.org/lightcurves/class.php?Class_ID=237 
  63                  Microlensing Event http://dotastro.org/lightcurves/class.php?Class_ID=145 
  50            RR Lyrae, First Overtone http://dotastro.org/lightcurves/class.php?Class_ID=219 
  48                              Binary http://dotastro.org/lightcurves/class.php?Class_ID=248 
  34      Semiregular Pulsating Variable http://dotastro.org/lightcurves/class.php?Class_ID=214 
  32                          Wolf-Rayet http://dotastro.org/lightcurves/class.php?Class_ID=192 
  32            Long Period (W Virginis) http://dotastro.org/lightcurves/class.php?Class_ID=235 
  31               RR Lyrae - Asymmetric http://dotastro.org/lightcurves/class.php?Class_ID=43 
  31                         Beta Cephei http://dotastro.org/lightcurves/class.php?Class_ID=213 
  27                Cataclysmic Variable http://dotastro.org/lightcurves/class.php?Class_ID=157 
  26                       Gamma Doradus http://dotastro.org/lightcurves/class.php?Class_ID=204 
  17               Population II Cepheid http://dotastro.org/lightcurves/class.php?Class_ID=216 
  16                            RR Lyrae http://dotastro.org/lightcurves/class.php?Class_ID=206 
  16                              BL Lac http://dotastro.org/lightcurves/class.php?Class_ID=139 
  15                             T Tauri http://dotastro.org/lightcurves/class.php?Class_ID=200 
  15           RR Lyrae - First Overtone http://dotastro.org/lightcurves/class.php?Class_ID=219 
  14          Short period (BL Herculis) http://dotastro.org/lightcurves/class.php?Class_ID=234 
  14    Semiregular Pulsating Red Giants http://dotastro.org/lightcurves/class.php?Class_ID=134 
  14                        SX Phoenicis http://dotastro.org/lightcurves/class.php?Class_ID=205 
  13      RR Lyrae, Closely Spaced Modes http://dotastro.org/lightcurves/class.php?Class_ID=222 
  13              Lambda Bootis Variable http://dotastro.org/lightcurves/class.php?Class_ID=261 
  13                         Ellipsoidal http://dotastro.org/lightcurves/class.php?Class_ID=246 
  10                              Blazar http://dotastro.org/lightcurves/class.php?Class_ID=256 
   9                   Herbig AE/BE Star http://dotastro.org/lightcurves/class.php?Class_ID=197 
   7                        X Ray Binary http://dotastro.org/lightcurves/class.php?Class_ID=260 
   6                            RV Tauri http://dotastro.org/lightcurves/class.php?Class_ID=215 
   6                   Anomolous Cepheid http://dotastro.org/lightcurves/class.php?Class_ID=236 
   5                           S Doradus http://dotastro.org/lightcurves/class.php?Class_ID=191 
   3                Variable Stars [Alt] http://dotastro.org/lightcurves/class.php?Class_ID=154 
   3          Flat Spectrum Radio Quasar http://dotastro.org/lightcurves/class.php?Class_ID=265 
   2                  Type II Supernovae http://dotastro.org/lightcurves/class.php?Class_ID=185 
   2                Systems with Planets http://dotastro.org/lightcurves/class.php?Class_ID=254 
   2                          Supernovae http://dotastro.org/lightcurves/class.php?Class_ID=180 
   1 SX Phoenicis  - Pulsating Subdwarfs http://dotastro.org/lightcurves/class.php?Class_ID=53 
   1                    SU Ursae Majoris http://dotastro.org/lightcurves/class.php?Class_ID=169 
   1                                 SRd http://dotastro.org/lightcurves/class.php?Class_ID=231 
   1                   Rotating Variable http://dotastro.org/lightcurves/class.php?Class_ID=240 
   1            AM Herculis (True Polar) http://dotastro.org/lightcurves/class.php?Class_ID=166 
"""
