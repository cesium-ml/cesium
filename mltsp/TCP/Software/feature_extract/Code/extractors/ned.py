from __future__ import print_function
import os,sys
import urllib
#20090321#import amara
import copy
import threading
import warnings

class NED(object):
    
    max_dist_search_arcmin = 100.0 ## 5 degree radius at most
    max_z_for_local_search = 0.003 ## otherwise it aint local and could hang
    max_small_dist_search_arcmin = 1.0
    max_field_dist_search_arcmin = 30.0
    
    local_results = None
    nearest_results = None
    field_results = None
    
    indict = {"in_csys": "Equatorial", "in_equinox": "J2000.0",\
                "out_csys": "Equatorial", "out_equinox": "J2000.0",\
                "obj_sort": "Distance to search center",\
                "of": "pre_text","zv_breaker": 30000.0, \
                "list_limit": 5, "img_stamp": "NO", "z_constraint": "Available",\
                "z_value1": "", "z_value2": "", "z_unit": "z", "ot_include": "ANY", \
                "in_objtypes1": "Galaxies", "nmp_op": "ANY", "search_type": "Near Position Search"}

    name_search_dict = {"objname": "", "extend": "no","of":"xml_derved","img_stamp":"NO"}

    ned_url = "http://ned.ipac.caltech.edu/cgi-bin/nph-objsearch?"

    ucd_lookup = {'name': "meta.id;meta.main", "ra": "pos.eq.ra;meta.main", 
        "dec": "pos.eq.dec;meta.main", "z": "src.redshift", "zflag": "meta.code;src.redshift", 
        "distance_arcmin": "pos.distance"}
        
    def __init__(self,pos=(None,None),verbose=False,object_types="Galaxies",precompute_on_instantiation=True,
        do_threaded=True,do_local=True, do_field = True, do_nearest=True):
        self.good_pos = False
        self.ra  = None
        self.dec = None
        self.parse_pos(pos)
        self.verbose = verbose
        self.indict.update({"in_objtypes1": object_types})
        self.objects = []
        self.threads = []
        self.do_threaded = do_threaded
        self.do_local = do_local
        self.do_nearest = do_nearest
        self.do_field = do_field

        if precompute_on_instantiation:
            if self.do_threaded:
                self._run_threaded()
            else:
                if self.verbose:
                    print("precomuting")
                if self.do_local:
                    self._local_gal_search()
                if self.do_nearest:
                    self._nearest_galaxy_search()
                if self.do_field:
                    self._field_galaxy_search()
                
    def _run_threaded(self):
        if self.do_local:
            if self.verbose:
                print("Starting local search in a thread")
            self.threads.append(threading.Thread(target=self._local_gal_search,name="local"))
            self.threads[-1].start()
        if self.do_nearest:
            if self.verbose:
                print("Starting nearest search in a thread")
            self.threads.append(threading.Thread(target=self._nearest_galaxy_search,name="nearest"))
            self.threads[-1].start()
        if self.do_field:
            if self.verbose:
                print("Starting field search in a thread")
                
            self.threads.append(threading.Thread(target=self._field_galaxy_search,name="field"))
            self.threads[-1].start()
        ### dstarr adds, to insure all threads join before returning:
        #for t in self.threads:
        #    t.join()

    def _local_gal_search(self,z_max=0.002,rad=100.0):

        local_dict = copy.copy(self.indict)
        if rad > self.max_dist_search_arcmin:
            rad = self.max_dist_search_arcmin
            if self.verbose:
                print("!NED: setting search radius to max_dist_search_arcmin (%f)" % self.max_dist_search_arcmin)

        if z_max > self.max_z_for_local_search:
            z_max = self.max_z_for_local_search
            if self.verbose:
                print("!NED: setting max z to max_z_for_local_search (%f)" % self.max_z_for_local_search)
                
        ## get the xml_main for this, maybe nothing
        local_dict.update({"lon": self.ra, "lat": self.dec, "radius": rad, "of": "xml_main",\
                      "z_constraint": "Less Than","z_value1": z_max})
        self.local_results = self._do_search(local_dict)

    def print_local_gal_search(self, z_max=0.002,rad=150.0,timeout=60.0):
        """ will do very wide search for local galaxies (z < z_max) consistent with a position """
        
        if self.do_threaded:
            for t in self.threads:
                if t.getName() == 'local':
                    if self.verbose:
                        print("Joining the local thread and waiting for it to finish")
                    t.join(timeout)

        if self.local_results is None:
            self._local_gal_search(z_max = z_max, rad= rad)
                        
        print("*"*30)
        print("Local Galaxy Results")
        print("*"*30)
        self._rez_print(self.local_results,key='kpc_offset')
    

    def _nearest_galaxy_search(self,rad=0.2):
        """ searches really nearby for all types of galaxies whether z is known or not ... default is 12 arcsec """
        local_dict = copy.copy(self.indict)
        if rad > self.max_field_dist_search_arcmin:
            rad = self.max_field_dist_search_arcmin
        
        ## get the xml_main for this, maybe nothing
        local_dict.update({"lon": self.ra, "lat": self.dec, "radius": rad, "of": "xml_main",\
                          "z_constraint": "Unconstrained"})

        # we really only care about the nearest few guys
        self.nearest_results = self._do_search(local_dict,max_derived=3)
        
    def print_nearest_galaxy_search(self,rad=0.2,timeout=60):
        if self.do_threaded:
            for t in self.threads:
                if t.getName() == 'nearest':
                    if self.verbose:
                        print("Joining the 'nearest' thread and waiting for it to finish")
                    t.join(timeout)
                    
        if self.nearest_results is None:
            self._nearest_galaxy_search(rad= rad)
            
        print("*"*30)
        print("Nearest Galaxy Results")
        print("*"*30)
        self._rez_print(self.nearest_results,key='distance_arcmin')
        
    def _field_galaxy_search(self,rad=10):
        """ searches field galaxies """
        
        local_dict = copy.copy(self.indict)
        if rad > self.max_field_dist_search_arcmin:
            rad = self.max_field_dist_search_arcmin

        ## get the xml_main for this, maybe nothing
        local_dict.update({"lon": self.ra, "lat": self.dec, "radius": rad, "of": "xml_main",\
                          "z_constraint": "Available", "z_value1": "", "z_value2": ""})

        # we really only care about the nearest few guys
        self.field_results = self._do_search(local_dict,max_derived=100)

    def print_field_galaxy_search(self,rad=5,timeout=60):
        if self.do_threaded:
            for t in self.threads:
                if t.getName() == 'field':
                    if self.verbose:
                        print("Joining the 'field' thread and waiting for it to finish")
                    t.join(timeout)
                    
        if self.field_results is None:
            self._field_galaxy_search(rad= rad)
            
        print("*"*30)
        print("Field Galaxy Results")
        print("*"*30)
        self._rez_print(self.field_results,key='kpc_offset')

    def distance_in_kpc_to_nearest_galaxy(self,timeout=60):
        """ cutoff in kpc ... dont return anything if more than that """
        ans = {"request": "distance_in_kpc_to_nearest_galaxy","distance": None}
        if self.do_threaded:
            # we need to join field and local results
            for t in self.threads:
                if t.getName() in ['field','local']:
                    t.join(timeout)
        else:
            if self.field_results is None:
                self._field_galaxy_search()
            if self.local_results is None:
                self._local_galaxy_search()
        
        if self.field_results is None or self.local_results is None:
            warnings.warn("no field or local result return")
            ans.update({'feedback': 'no field or local result return'})
            return ans
        
        tmp = copy.copy(self.field_results)
        tmp.extend(copy.copy(self.local_results))
        
        ## sort by kpc offset
        key = 'kpc_offset'
        obj = copy.copy(tmp)
        for o in tmp:
            if key not in o:
                obj.remove(o)
        
        if len(obj) == 0:
            ans.update({'feedback': 'no sources found with spatial position values known'})
            return ans

        obj.sort(key=lambda x: x[key])
        ans.update({'feedback': 'seems good','distance': obj[0][key], 'source_info': copy.copy(obj[0])})
        return ans

    def distance_in_arcmin_to_nearest_galaxy(self,timeout=60):
        """  """
        ans = {"request": "distance_in_arcmin_to_nearest_galaxy","distance": None}
        if self.do_threaded:
            # we need to join field and local results
            for t in self.threads:
                if t.getName() in ['field','local','nearest']:
                    t.join(timeout)
        else:
            if self.field_results is None:
                self._field_galaxy_search()
            if self.nearest_results is None:
                self._nearest_galaxy_search()
            if self.local_results is None:
                self._local_galaxy_search()

        if self.field_results is None or self.local_results is None or self.nearest_results is None:
            warnings.warn("no field or local or nearest result return")
            ans.update({'feedback': 'no field or local or nearest result return'})
            return ans

        tmp = copy.copy(self.field_results)
        tmp.extend(copy.copy(self.local_results))

        ## sort by kpc offset
        key = 'distance_arcmin'
        obj = copy.copy(tmp)
        for o in tmp:
            if key not in o:
                obj.remove(o)

        if len(obj) == 0:
            ans.update({'feedback': 'no sources found with spatial position values known'})
            return ans

        obj.sort(key=lambda x: x[key])
        ans.update({'feedback': 'seems good','distance': obj[0][key], \
            'source_info': copy.copy(obj[0])})
        return ans
    def _rez_print(self,objects,key='kpc_offset'):

        ## sort by kpc offset
        other = []
        obj = copy.copy(objects)
        
        for o in objects:
            if key not in o:
                other.append(o)
                obj.remove(o)
            
        obj.sort(key=lambda x: x[key])
        
        print("%-30s\t%9s\t%9s\t%9s\t%9s" % ("Name","z","dm","dist","offset"))
        print("%-30s\t%9s\t%9s\t%9s\t%9s" % ("","","mag","arcmin","kpc"))
        for o in obj:
            if "dm" in o:
                dm = o['dm']
            else:
                dm = "---"
            if 'kpc_offset' in o:
                ko = o['kpc_offset']
            else:
                ko = "---"
            if 'z' in o:
                z = o['z']
            else:
                z = "---"
                                    
            print("%-30s\t%9s\t%9s\t%9.3f\t%9s" % (o['name'],str(z),str(dm),o["distance_arcmin"],str(ko)))
        
        if len(other) > 0:
            print(" *** OTHER (those that cannot be sorted by requested sort key)**** ")
            print("%-30s\t%9s\t%9s\t%9s\t%9s" % ("Name","z","dm","dist","offset"))
            print("%-30s\t%9s\t%9s\t%9s\t%9s" % ("","","mag","arcmin","kpc"))
            for o in other:
                if "dm" in o:
                    dm = o['dm']
                else:
                    dm = "---"
                if 'kpc_offset' in o:
                    ko = o['kpc_offset']
                else:
                    ko = "---"
                if 'z' in o:
                    z = o['z']
                else:
                    z = "---"

                print("%-30s\t%9s\t%9s\t%9.1f\t%9s" % (o['name'],str(z),str(dm),o["distance_arcmin"],str(ko)))
        
    def _do_search(self,local,get_derived_obj_info=True,max_derived=500):
        """ actually performs the search and parses the output """

        if not self.good_pos:
            return []

        params = urllib.urlencode(local)
        if self.verbose:
            print(self.ned_url + params)
        f = urllib.urlopen(self.ned_url + params)
        
        tmp =  f.read()
        try:
            doc = amara.parse(tmp)
        except:
            print("EXCEPT: ned() extractor")
            return []
        self.doc = doc
        if self.verbose:
            print("got the document from NED")
        try:
            main_table = doc.xml_xpath(u'//TABLE[@ID="NED_MainTable"]')[0]
        except:
            print("no main table")
            return []
        objs = self._get_objects_from_main_table(main_table)
        if get_derived_obj_info:
            objs = self._get_derived_info(objs,max_derived=max_derived)
        
        return objs
        
    def _get_derived_info(self,objs,max_derived=500):
        
        ret = []
        local = copy.copy(self.name_search_dict)
        for o in objs[:max_derived]:
            ## do a search on the name
            if "name" not in o:
                ret.append(o)
            else:
                tmp = copy.copy(o)
                
            local.update({"objname": o['name']})
            params = urllib.urlencode(local)
            if self.verbose:
                print(self.ned_url + params)
            f = urllib.urlopen(self.ned_url + params)
            tmp1 =  f.read()
            doc = amara.parse(tmp1)
            if self.verbose:
                print("got the derived document from NED for source %s" % o['name'])
            try:
                d= doc.xml_xpath(u'//TABLE[@ID="NED_DerivedValuesTable"]')[0]
            except:
                print("no dervived table")
                continue
    
            dfields = d[0].xml_xpath(u'FIELD')
            dat = d[0].xml_xpath(u'DATA/TABLEDATA/TR/TD')
            for i in range(len(dfields)):
                if dfields[i].xml_xpath(u'@ucd="pos.distance;scale;hubble.flow.galactocentric" and @unit="kpc/arcmin"'):
                    tmp1 = unicode(dat[i])
                    try:
                        ug1 = float(tmp1)
                    except:
                        ug1 = str(tmp1).strip()
                    tmp.update({'kpc_arcmin': ug1})
                    try:
                        tmp.update({'kpc_offset': tmp['kpc_arcmin']*tmp['distance_arcmin']})
                    except:
                        pass
                if dfields[i].xml_xpath(u'@ucd="pos.distance;luminosity_moduli" and @unit="mag"'):
                    tmp1 = unicode(dat[i])
                    try:
                        ug1 = float(tmp1)
                    except:
                        ug1 = str(tmp1).strip()
                    tmp.update({'dm': ug1}) 
            ret.append(tmp)
        return ret
        
    def _get_objects_from_main_table(self,main_table):
        vals = self.ucd_lookup.values()
        table_lookup = self.ucd_lookup.fromkeys(self.ucd_lookup)

        fields = main_table.xml_xpath(u'FIELD')
        for i in range(len(fields)):
            f = fields[i]
            if f.ucd in vals:
                for k,v in self.ucd_lookup.items():
                    if v == f.ucd:
                        table_lookup[k] = i
                        break

        objs = main_table.xml_xpath(u'DATA/TABLEDATA/TR')
        objects = []
        for o in objs:
        	ug = o.xml_xpath(u'TD')
        	tmp = {}
        	for k, i in table_lookup.items():
        		tmp1 = unicode(ug[i])
        		try:
        			ug1 = float(tmp1)
        		except:
        			ug1 = str(tmp1).strip()
        		tmp.update({k: ug1})
        	objects.append(tmp)
        
        return objects
        
    def parse_pos(self,pos):
        """ parses the position and set local variables """
        ## TODO: more error checking ... assume degrees now
        #print pos
        ra = pos[0]
        dec = pos[1]
        if type(ra) != type(1.2) or type(dec) != type(1.2):
            warnings.warn("RA and/or DEC is not a type of float")
            self.good_pos = False
            return
        
        if ra < 0.0 or ra >= 360.0 or dec < -90.0 or dec > 90.0:
            warnings.warn("RA and/or DEC out of range")
            self.good_pos = False
            return
         
        self.good_pos = True  
        self.ra  = "%fd" % ra
        self.dec = "%fd" % dec

        return
    
def test():
    ra =  199.83412 
    dec =  8.92897
    #ra = 286.61986  
    #dec = 68.79320 
    #ra  = 185.1282480
    #dec = 28.346232
    b = NED(pos=(ra,dec),verbose=False)
    #b.print_local_gal_search(rad=150)
    #b.print_nearest_galaxy_search(rad=0.2)
    #b.print_field_galaxy_search(rad=8)
    print(b.distance_in_kpc_to_nearest_galaxy())
    print(b.distance_in_arcmin_to_nearest_galaxy())
    b.print_local_gal_search()
    b.print_nearest_galaxy_search()
    b.print_field_galaxy_search()

if __name__ == "__main__":
    test()  


