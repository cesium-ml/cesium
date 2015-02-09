#!/usr/bin/env python
"""
Josh's Dumb-Ass Classifier
"""
import pprint
import sys,os, copy
sys.path.append(os.environ.get("TCP_DIR") + '/Software/feature_extract/Code/extractors')

import sdss, ned, ng

class bogus_sdss:
    def __init__(self):
        self.in_footprint = False
        self.feature = {}

class JDAC:
    
    def __init__(self,pos=(176.70883     ,11.79869),verbose=True,seeing=2.5, do_sdss=True):
        self.verbose=verbose
        self.pos = pos
        self.seeing = seeing/2  # in arcsec ... to make this circumnuclear
        if do_sdss:
            self._get_sdss_feature()
        else:
            self.s = bogus_sdss()
        #self._get_ned_features()
        self._get_mansi_gals()
        self.val_add = {}
        self.set_nearest_type()
        self.set_probability()

        if self.val_add["nearest_type_confidence"] < 0.95 and self.val_add["nearest_type"] in ["galaxy", "stellar"]:
            #pprint.pprint(self.val_add)
            #print "***"*10
            self.ttt = copy.copy(self.val_add)
            ## probability is low here...compute for the other case
            if self.ttt["nearest_type"] == "galaxy":
                self.val_add["nearest_type"] = "stellar"
            else:
                self.val_add["nearest_type"] = "galaxy"
                
            self.val_add["nearest_type_confidence"]  = 1.0 - self.ttt["nearest_type_confidence"]
            self.set_probability()
            self.val_add.pop("nearest_type_from")
            self.ttt.update({'alt': self.val_add})
            self.val_add = self.ttt
            
        #pprint.pprint(self.val_add)
        self.make_clean_prob()
        self.make_clean_prob(doalt=True)
        #pprint.pprint(self.p)
        
    def make_clean_prob(self,doalt=False):
        if not doalt:
            self.p = {}
            for k,v in self.val_add.iteritems():
                if k not in ["alt", "nearest_type", "nearest_type_confidence", "prob"]:
                    if "flags" not in self.p:
                        self.p.update({"flags": {k: v}})
                    else:
                        self.p["flags"].update({k: v})
        else:
            if "alt" in self.val_add:
                self.ttt = copy.copy(self.val_add)
                self.val_add = self.ttt['alt']
            else:
                return
        if self.val_add['nearest_type'] in ['qso','galaxy']:
            top_prob = self.val_add['nearest_type_confidence']
            self.p.update({"extragalactic": {"val": top_prob}})
            for k,v in self.val_add['prob'].iteritems():
                self.p['extragalactic'].update({k: {'val': v}})
        elif self.val_add['nearest_type'] in ['stellar','cv']:
            top_prob = self.val_add['nearest_type_confidence']
            self.p.update({"galactic": {"val": top_prob}})
            multi = self.val_add['prob']['VarStar']['prob']
            self.val_add['prob']['VarStar'].pop("prob")
            for k,v in self.val_add['prob']['VarStar'].iteritems():
                self.p['galactic'].update({k: {'val': v}})
                
        if doalt:
            self.val_add = self.ttt
            
        
    def _get_sdss_feature(self):
        self.s = sdss.sdssq(pos=self.pos,verbose=self.verbose,run_on_instance=False)    
        self.s.feature_maker()
        
    def _get_ned_features(self):
        self.n = ned.NED(pos=self.pos,verbose=self.verbose)
        
    def _get_mansi_gals(self,radius=5):
        self.mansi = ng.GalGetter(verbose=self.verbose)
        self.mansi.getgals(pos=self.pos,radius=float(radius)/60.,sort_by="phys",max_d=500.0)
        self.m = self.mansi.grab_rez()
     
    def set_probability(self):
        if self.val_add["nearest_type_from"] == "unset":
            ## there's no context
            self.val_add.update({"prob": {}})
            return

        if self.val_add["nearest_type"] == "unset":
            ## it's not in there, but in the footprint
            self.val_add.update({"prob": {'roid': 0.6, 'sn': 0.1, 'VarStar': {"prob": 0.2, 'low_mass_flare': 0.8}}})
            return
                            
        if self.val_add['nearest_type_from'] == "mansi" and self.val_add["nearest_type"] == "galaxy":
            ## could be a rather nearby galaxy. But's let's check to make sure it's not some 
            ## more distant galaxy in projection
            self.tmp = copy.copy(self.val_add)
            self.set_nearest_type(skip_mansi=True)
            ## if the mansi confidence is low and the sdss confidence is high, then set that
            if self.tmp["nearest_type_confidence"] <= 0.9 and \
                self.val_add["nearest_type"] == "galaxy" and \
                    self.val_add["nearest_type_confidence"] >= 0.60:
                ## we're good ... keep the val_add from sdss and note possible nearby big galaxy
                self.val_add.update({"possible_mansi_gal_nearby": True, 'possible_mansi_gal_mansi_pos': self.m['closest_in_light_galaxy_position']})
                ## call ourselves again...this time without the mansi galaxy
                self.set_probability()
            else:
                ## no, the SDSS looks to be tentative, revert back to Mansi
                self.val_add = self.tmp
            
            del self.tmp
            ## now we can really belive mansi
            if self.m['closest_in_light_physical_offset_in_kpc'] < 0.5:
                if self.m['closest_in_light_angular_offset_in_arcmin'] < self.seeing/60.0:
                    self.val_add.update({"apparently_nuclear": True})
                else:
                    # outside seeing disk
                    self.val_add.update({"apparently_circumnuclear": True})
            else:
                ## largert physical offset
                if self.m['closest_in_light_angular_offset_in_arcmin'] < self.seeing/60.0:
                    self.val_add.update({"apparently_circumnuclear": True})
                if self.m['closest_in_light_dm'] < 28.5:
                    ## this is a really nearby galaxy < 5 Mpc
                    self.val_add.update({"very_nearby_gal": True})
                    self.val_add.update({"prob": {"SN": 0.05, "Nova": 0.9}})
                    return
                else:
                    self.val_add.update({"outskirts_of_mansi_nearby_gal": True})
                    self.val_add.update({"prob": {"SN": 0.9}})
                    
                if "apparently_nuclear" in self.val_add:
                    if "prob" in self.val_add:
                        self.val_add['prob'].update({"SN": 0.1, "AGN": 0.85, "TDF": 0.05})
                    else:
                        self.val_add.update({"prob":{"SN": 0.1, "AGN": 0.85, "TDF": 0.05}})
                    return
                if "apparently_circumnuclear" in self.val_add:
                    self.val_add.update({"prob":{"SN": 0.95, "AGN": 0.05}})
        else:
            if self.val_add["nearest_type"] == "galaxy":
                if self.ss["dist_in_arcmin"] < self.seeing/60.0:
                    ## apparently right on top of the light centroid
                    if self.ss["dered_r"] > 21.0:
                        self.val_add.update({"prob":{"SN": 0.9, "AGN": 0.05}})
                    else:
                        # if it's bright and right on top...
                        self.val_add.update({"apparently_circumnuclear": True})
                        self.val_add.update({"prob":{"SN": 0.3, "AGN": 0.7}})
                    return
                else:
                    self.val_add.update({"prob":{"SN": 0.9}})
                    return
            elif self.val_add["nearest_type"] == "qso":
                if self.ss["dist_in_arcmin"] < self.seeing/60.0:
                    self.val_add.update({"prob":{"SN": 0.02, "AGN": 0.95}})
                    return
                else:
                    self.val_add.update({"prob":{"SN": 0.05, "AGN": 0.93}})
                    return
            else:
                ## a star, probably
                ## is it red?
                if self.ss["dered_r"] - self.ss["dered_i"] > 1.5:
                    self.val_add.update({"prob":{'VarStar': {"prob": 1.0, 'low_mass_flare': 0.8}}})
                    return
                # blue
                if self.ss["dered_r"] - self.ss["dered_i"] < 0.5 or self.val_add["nearest_type"] == "cv":
                    self.val_add.update({"prob":{'VarStar': {"prob": 1.0, 'CV': 0.8}}})
                    return
                if  self.ss["spectral_flag"] != None:
                    ## probably a white dwarf spectroscopically
                    if self.ss["spectral_flag"] in ['d','D']:
                        self.val_add.update({"prob":{'VarStar': {"prob": 1.0, 'CV': 0.8}}})
                        return
                # no idea
                self.val_add.update({"prob":{'VarStar': {"prob": 1.0}}})
                return
                    
    def set_nearest_type(self,skip_mansi=False):
        
        ## is it in the SDSS footprint or mani?
        if not self.s.in_footprint and "closest_in_light" not in self.m:
            self.val_add.update({'nearest_type_from': "unset", 'nearest_type': "not_in_footprint", "nearest_type_confidence": 1.0})
            return
        
        if not skip_mansi:    
            ## let's look at mansi's result for now
            if "closest_in_light" in self.m and 'closest_in_light_physical_offset_in_kpc' in self.m:
                ## decreasing confidence in this being a galaxy
                if self.m['closest_in_light_physical_offset_in_kpc'] < 3.0 and self.m['closest_in_light'] < 1.0:
                    self.val_add.update({'nearest_type': "galaxy", "nearest_type_confidence": 0.98})
                elif self.m['closest_in_light_physical_offset_in_kpc'] < 5.0 and self.m['closest_in_light'] < 2.0:
                    self.val_add.update({'nearest_type': "galaxy", "nearest_type_confidence": 0.9})                
                elif self.m['closest_in_light_physical_offset_in_kpc'] < 10.0 and self.m['closest_in_light'] < 3.0:
                    self.val_add.update({'nearest_type': "galaxy", "nearest_type_confidence": 0.8}) 
                elif self.m['closest_in_light_physical_offset_in_kpc'] < 15.0 and self.m['closest_in_light'] < 3.5:
                    self.val_add.update({'nearest_type': "galaxy", "nearest_type_confidence": 0.7})
                elif self.m['closest_in_light_physical_offset_in_kpc'] < 40.0 and self.m['closest_in_light'] < 5.0:
                    self.val_add.update({'nearest_type': "galaxy", "nearest_type_confidence": 0.6})
                else:
                    self.val_add.update({'nearest_type': "galaxy", "nearest_type_confidence": 0.55}) 
                                                   
                self.val_add.update({'nearest_type_from': 'mansi'})
                return

        ## let's look at SDSS
        self.ss = self.s.feature
        if "dist_in_arcmin" in self.ss:
            if self.ss["dist_in_arcmin"] > 0.12:
                ## this is pretty far away for a SDSS galaxy
                self.val_add.update({'nearest_type': "unset", "nearest_type_confidence": 0.5})
                self.val_add.update({'nearest_type_from': 'sdss'})
                return
        if "best_offset_in_kpc" in self.ss:
            if self.ss["best_offset_in_kpc"] > 100.0:
                ## this is pretty far away for a SDSS galaxy
                self.val_add.update({'nearest_type': "unset", "nearest_type_confidence": 0.5})
                self.val_add.update({'nearest_type_from': 'sdss'})
                return
        if "type" in self.ss:
            if self.ss['type'] == 'galaxy' or self.ss['classtype'] == 'gal':
                if "segue_class" in self.ss:
                    if self.ss['segue_class'] == 'galaxy':
                        if "spec_z" in self.ss and 'spec_confidence' in self.ss:
                            if self.ss['spec_z'] > 0.01 and self.ss['spec_confidence'] > 0.3:
                                if "best_offset_in_petro_g" in self.ss:
                                    if self.ss["best_offset_in_petro_g"] < 10.0:
                                        self.val_add.update({'nearest_type': "galaxy", "nearest_type_confidence": 1.0})
                                    else:
                                        self.val_add.update({'nearest_type': "galaxy", "nearest_type_confidence": 0.95})
                                else:
                                        self.val_add.update({'nearest_type': "galaxy", "nearest_type_confidence": 0.90})
                            else:
                                self.val_add.update({'nearest_type': "galaxy", "nearest_type_confidence": 0.85})
                    else:
                        self.val_add.update({'nearest_type': "galaxy", "nearest_type_confidence": 0.85})
                else:
                    self.val_add.update({'nearest_type': "galaxy", "nearest_type_confidence": 0.80})
            else:
                self.val_add.update({'nearest_type': "stellar", "nearest_type_confidence": 0.95})
        
        ## if the source is too faint, then it's hard to trust the classification
        if 'dered_r' in self.ss:
            if self.ss['dered_r'] > 21.5 and self.ss["spec_z"] is None:
                ## really hard to trust what's happening here.
                if self.ss['type'] == 'galaxy':
                    self.val_add.update({'nearest_type': "galaxy", "nearest_type_confidence": 0.55})
                else:
                    self.val_add.update({'nearest_type': "stellar", "nearest_type_confidence": 0.55})
                    
        if self.ss.get('spectral_flag','') in ['xxxx', 'nnbn', 'enbn', 'ecbn']:
            if "nearest_type_confidence" in self.val_add:
                if self.val_add["nearest_type_confidence"] < 0.9:
                    self.val_add.update({'nearest_type': "galaxy", "nearest_type_confidence": 0.9})
        if self.ss.get("classtype",'') == "qso":
            self.val_add.update({'nearest_type': "qso", "nearest_type_confidence": 0.70})
            if self.ss["segue_star_type"] == "broadline":   
                self.val_add.update({'nearest_type': "qso", "nearest_type_confidence": 0.95})
            if self.ss["spectral_stellar_type"] == "cv" or self.ss["spec_zWarning"] == "not_qso":
                self.val_add.update({'nearest_type': "cv", "nearest_type_confidence": 0.95})                                
        if self.ss.get("spectral_stellar_type",'') == 'qso' or (self.ss.get("bestz",'') > 0.6 and self.ss["bestz_err"] < 0.1):
            self.val_add.update({'nearest_type': "qso", "nearest_type_confidence": 0.95})
                 
        self.val_add.update({'nearest_type_from': 'sdss'})

        return
        
if __name__ == "__main__":
    #j = JDAC(seeing=2.5)
    j = JDAC(pos=(57.434622 , -3.264654  ))
    # try looking at j.p
    import pprint
    pprint.pprint(j.p)
