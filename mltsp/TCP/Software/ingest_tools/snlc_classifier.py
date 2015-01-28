#!/usr/bin/env python
"""
   v0.1 Dovi/Nat SN light curve classifier, built upon PTF_SN_classifier.py

"""
import os, sys
from scipy.special import erf
from numpy import array,matrix,arange,sqrt,exp,mean,sum,zeros,clip,fix,\
    cumsum,hstack,floor,ceil,log, float32

class Dovi_SN:
    """ This class wraps Dovi/Nat SN classification algorithms
    
    """
    def __init__(self,datamodel=None,doplot=True,verbose=False, x_sdict=None):
        self.doplot = doplot
        self.verbose = verbose
        self.x_sdict = x_sdict
        if self.doplot:
            cla()
        #if datamodel is None:
        #    self.test()
        else:
            self.data = datamodel
            self.run()

    def run(self):
        """ This does the SN classification.

        NOTE: Featue data is located in:
        self.data.feat_dict['multiband'].keys()
        

        TODO: This method populates a classification result structure/dict:
              self.final_results
                -> this is placed into ation_dict[src_id]['mlens3 MicroLens']

        TODO: have feature structure/dict populated such as:
            <...>['freq3_harmonics_peak2peak_flux_error']['val'] = ... #flt/str
            <...>['freq3_harmonics_peak2peak_flux_error']['val_type'] # str
            <...>['freq3_harmonics_peak2peak_flux_error']['err'] # flt/None

        self.data.fname # This is the full XML string
        self.data.filts = ['ptf_r']
        self.data.t(f)
        self.data.flux_err(f)
        self.data.flux('ptf_r') = [ 2969458.46304646 .. ]

        print self.data.data['ts']['ptf_r'] = [{'name': 't', 'val': array([ 441.7975]), 'datatype': 'float', 'ID': 'col1', 'unit': 'day', 'system': 'TIMESYS'}, {'ucd': 'phot.mag;em.opt.ptf_r', 'name': 'm', 'val': array([ 0.01111]), 'datatype': 'float', 'ID': 'col2', 'unit': 'mag'}, {'ucd': 'stat.error;phot.mag;em.opt.ptf_r', 'name': 'm_err', 'val': array([ 0.]), 'datatype': 'float', 'ID': 'col3', 'unit': 'mag'}, {'datatype': 'string', 'ucd': 'stat.max;stat.min', 'ID': 'col4', 'val': array(['false'], ... dtype='|S5'), 'name': 'limit'}]

        self.data.data['VOSOURCE']['Features']['feature'][0].keys()
            ['origin', 'name', 'err', 'filter', 'val', 'description']
        self.data.data['VOSOURCE']['Features']['feature'][0]['name']
            sdss_dered_i

        """
        #print self.data.feat_dict['multiband'].keys() # TEST
        self.main() # TODO: or something like this...


    def conf_interval(self, x1,x2,prob,conf=0.68):
        """return conf (default 1-sigma) confidence interval in x for prob"""
        
        cprob = cumsum(prob*(x2-x1))
        cprob = hstack((0.,cprob))
        mcprob = max(cprob)
        
        lx=len(x1)
        
        x10=min(x1); x20=max(x2);
        delta0=x20-x10
        for i in xrange(lx-2):
          for j0 in xrange(lx-i):
            j = j0 + i
            delta = x2[j] - x1[i]
            if (cprob[j+1]-cprob[i]>=conf*mcprob and delta<delta0):
              x10=x1[i]; x20=x2[j]; delta0=delta
      
        return (x10,x20)



    def PTF_LCSN_classifier(self, data, z=0, dz=0.1):
        """
        Returns a dictionary:
        posterior probabilities for Ia or not-Ia  SNe for PTF
        
        1-sigma confidence intervals on z for Ia."""
        
        #
	# read in the model, has keys: ['phot','days','z', 'filters', 'Av']
	#   w/ dimensions: phot (58, 31, 9, 11)
	#                  days 58
	#                  z 31
	#                  filters 9
	#                  Av 11
	#
        import scipy.io
	from scipy.io import loadmat
        fpath = 'Iamodel_v6.mat'
        if not os.path.exists(fpath):
            fpath = os.path.expandvars('$TCP_DIR/Data/Iamodel_v6.mat')
	model = loadmat(fpath)

        # dstarr: looks like we want a list with each filter character as an element.
        #   currently it looks like: print model['filters'][0] = 'RugrizJHK'
        new_filt_list = []
        for i_filt in xrange(len(model['filters'][0])):
            new_filt_list.append(model['filters'][0][i_filt])
        model['filters'] = new_filt_list

        # # # # # # #
        # TODO:   use xml file's upper limits, if it has them
        # # # # # # #
        

	#data={}
        # # # dstarr NOTE: typlical values: data['filters'] = ['z:table15393', 'R:table15103', 'G:table14958', 'U:table14813', 'I:table15248', 'combo_band']
        
	i=0
	for filt in data['filters']:
	  #data[filt] = {'time':[0.,0.], 'mag':[0.,1.],'err':[0.,3.],'is_limit':[True,False]}
	  # just set it using the model for now
	  # data[filt] = {'time':model['days'], 'mag':model['phot'][:,10,i,0],'err':zeros(len(model['days']))+0.1,'is_limit':zeros(len(model['days']),dtype=bool)}
	  # keep track of minimum, and maximum? time with a detection
          # # # It seems that t0 is just the min(t[<where is_limits>]) 
          # # # It seems that t1 is just the max(t[<all>]) 
	  #accept = where( logical_xor( data[filt]['is_limit'] , True ) )[0]
	  #t0 = min( atleast_1d(data[filt]['time'][accept]) )
	  #t1 = max( atleast_1d(data[filt]['time']) )
          if (len(data[filt]['time']) == 0) or (len(data[filt]['limitmags']['t']) == 0):
              continue # skip this filter
          tmax_data = max(data[filt]['time'])
          tmax_lims = min(data[filt]['limitmags']['t'])
          t1 = tmax_data
          if tmax_lims > tmax_data:
              t1 = tmax_lims
          t0 = min(data[filt]['limitmags']['t'])

	  if (i==0):
	      tmin = t0
	      tmax = t1
	  else:
	      if ( t0<tmin ): tmin = t0
	      if ( t1>tmax ): tmax = t1
	  i=i+1


	delta_time = 1.
	offset = arange(tmin,tmax+delta_time,delta_time,dtype=float32)

	from scipy.interpolate import interp1d
	import string

	#prior on z
	z0=0.2
	dz0=0.2
	nzsig = 3.

	#prior on Av
	Av0=0.
	dAv0=0.1
	nAsig = 3.

	chi = zeros((len(offset),len(model['z']),len(model['filters']),len(model['Av'])),dtype=float32) + 999.

	i=0
	for z in model['z']:
	  i+=1
	  if ( abs(z-z0) < nzsig*dz0 ):

	    for filt in data.keys():
               # j = string.find( model['filters'] , filt )
               # dstarr thinks this is what was intended in the above line:
               if (filt == 'combo_band') or (filt == 'filters'):
                   # KLUDGE: it appears we probably shouldnt have data['filters'] in the structure
                   continue # skip this combined filter case
               for i_filt, name_filt in enumerate(model['filters']):
                   if name_filt in filt:
                       j = i_filt
                       break
	       k=0
	       for Av in model['Av']:
	         if ( abs(Av-Av0) < nAsig*dAv0 ):

	           k+=1
	           def chi_func(offset=[]):
                     # dstarr: originally, model['days']=[[ 0],[ 1],[ 2]....
                     #    we want a single dimension array
                     if len(model['days'].shape) == 2:
                         new_arr = []
                         for elem in model['days']:
                             new_arr.append(elem[0])
                         model['days'] = array(new_arr)

	             interp_func = interp1d( model['days'], model['phot'][:,i-1,j,k-1], bounds_error=False, fill_value=0. )
	             resid = ( data[filt]['mag'] - interp_func(data[filt]['time'] - offset) ) / data[filt]['err']
	             return sum(resid**2) + ((z-z0)/dz0)**2 + ((Av-Av0)/dAv0)**2

	           #chi[:,i-1,j,k-1] = map(chi_func,offset)
                   ### dstarr translates the above non-python syntax into:
                   intermed_array = []
                   for elem in offset:
                       intermed_array.append(chi_func(elem)[0])
                   chi[:,i-1,j,k-1] = array(intermed_array)


        # So, on my test run, these filters have calculated ch data (R, z):
        #   chi[:,:,0,:]  chi[:,:,5,:] = [[....]]
	chi_best = chi.min()
	prob = exp(-0.5*(chi-chi_best))

	# marginalize over filter
	prob = prob.sum(axis=2)
	#posterior on offset
	prob_offset = prob.sum(axis=1).sum(axis=1)
	#posterior on redshift
	prob_redshift = prob.sum(axis=0).sum(axis=1)
	#posterior on Av
	prob_Av = prob.sum(axis=0).sum(axis=0)
		
		
		
        out_dict={	'<SNLC classify Plugin v0.1>': {'class_results':{ 'SN Ia':{'prob':  prob, 'weight':1.0,'TUTOR_name': "tia",'comments': "No Ia subtypes",\
		                 'class_value_added_statements': {'name': "z_1sigma",'value' : prob_redshift, 'comments': "This is the best fit  redshift, if it is a Ia"},\
		                 'class_value_added_statements': {'name': "z_1sigma",'value' : prob_offset, 'comments': "This is the best fit  age, if it is a Ia"},\
						 'class_value_added_statements': {'name': "z_1sigma",'value' : prob_Av, 'comments': "This is the best fit  A_V, if it is a Ia"}}}}}
        return out_dict


    def main(self):
        """ The original __main__ from Dovi/Nat PTF_SN_classifiers.py
        """

        feat_dict = self.data.feat_dict['multiband']

        """
        try:
            closest_in_light = float(str(\
                feat_dict.get('closest_in_light',{}).get('val',None).))
        except:
            closest_in_light = None
        try:
            closest_in_light_dm = float(str(\
                feat_dict.get('closest_light_dm',{}).get('val',None)))
        except:
            closest_in_light_dm = None
        try:
            sdss_best_offset_in_petro_g = float(str(\
                feat_dict.get('sdss_best_offset_in_petro_g',{}).get('val',None)))
        except:
            sdss_best_offset_in_petro_g = None
        try:
            sdss_best_z = float(str(\
                feat_dict.get('sdss_best_z',{}).get('val',None)))
        except:
            sdss_best_z = None
        try:
            sdss_best_dz = float(str(\
                feat_dict.get('sdss_best_zerr',{}).get('val',None)))
        except:
            sdss_best_dz = None
		
        sdss_nearest_obj_type = str(\
            feat_dict.get('sdss_nearest_obj_type',{}).get('val',''))
        """

            # NOTE: "closest_*" features come from ng.py & 200MpcGalaxyCatalog (Mansi?), so it is independent of SDSS retrieved features, and thus may contain None while SDSS contains something (or vice-versa)
        try:
            closest_in_light = float(str(\
                feat_dict.get('closest_in_light',{}).get('val',{}).get('_text',None)))
        except:
            closest_in_light = None
        try:
            closest_in_light_dm = float(str(\
                feat_dict.get('closest_light_dm',{}).get('val',{}).get('_text',None)))
        except:
            closest_in_light_dm = None
        try:
            sdss_best_offset_in_petro_g = float(str(\
                feat_dict.get('sdss_best_offset_in_petro_g',{}).get('val',{}).get('_text',None)))
        except:
            sdss_best_offset_in_petro_g = None
        try:
            sdss_best_z = float(str(\
                feat_dict.get('sdss_best_z',{}).get('val',{}).get('_text',None)))
        except:
            sdss_best_z = None
        try:
            sdss_best_dz = float(str(\
                feat_dict.get('sdss_best_zerr',{}).get('val',{}).get('_text',None)))
        except:
            sdss_best_dz = None
		
        sdss_nearest_obj_type = str(\
            feat_dict.get('sdss_nearest_obj_type',{}).get('val',{}).get('_text',''))
       

        self.debug_feat_tup = (closest_in_light,closest_in_light_dm,sdss_best_offset_in_petro_g,sdss_best_z,sdss_best_dz,sdss_nearest_obj_type)
		
		
		
		# NEED TO EXTRACT THE LIGHTCURVE INTO "phot"
		
		
        # NOT used since all features are in ['multiband']:
        """
        #print self.data.feat_dict['multiband'].keys()
        filter_list = self.data.feat_dict.keys()
        filter_list.remove('multiband')
        default_filter = filter_list[0] # KLUDGE: Assuming there is at least
        #                       one non-multiband filter.
        # TODO: maybe eventually try for V or v first.
        feat_dict = self.data.feat_dict[default_filter]
        """



        #(2) find host
        # 
        #defaults:
        z=0
        dz=0.1
        near_z=0
        near_dz=0.1

        light_threshold=1.5
        if  (closest_in_light is not None):
            if (closest_in_light < light_threshold):
                #    this is the host
                if closest_in_light_dm is not None:
                    H0=70;
                    near_z=H0/30*10**(closest_in_light_dm/5-9)
                    dm_err=0.4 # (about 20% in distance)
                    near_dz=dm_err*H0/30*log(10)/5*10**(closest_in_light_dm/5-9)

        sdss_threshold=2
        if (sdss_best_offset_in_petro_g is not None) and \
           (sdss_nearest_obj_type.lower() == 'galaxy' ) and \
           (sdss_best_offset_in_petro_g<sdss_threshold):

            if (sdss_best_z is not None) and (near_z==0):
                z=sdss_best_z
                dz=sdss_best_dz
         
            else:
                z=near_z
                dz=near_dz
        

        # Make a dictionary that PTF_LCSN_classifier() wants:
        ###WANT:# data['filters'] = [<filter names, ...>]
        ###WANT:# data[<filt name>] = [filt]{'time':[], 'mag':[], 'err':[]     ...}
        data = {}
        data['filters'] = self.x_sdict['ts'].keys()

        for filter_name in data['filters']:
            data[filter_name] = {}
            data[filter_name]['time'] = self.x_sdict['ts'][filter_name]['t']
            data[filter_name]['mag'] = self.x_sdict['ts'][filter_name]['m']
            data[filter_name]['err'] = self.x_sdict['ts'][filter_name]['m_err']
            data[filter_name]['limitmags'] = self.x_sdict['ts'][filter_name]['limitmags'] # {'lmt_mg':, 't':}


            



        # XXX Dan        
   		# extract light curve data from vosource
		# a dictionary, for each band with vectors 'time' 'mag' 'err' and 'is_limit' that is boolean, one for upper limits zero for detections.
		# data[filt] = {'time':model['days'], 'mag':model['phot'][:,10,i,0],'err':zeros(len(model['days']))+0.1,'is_limit':zeros(len(model['days']),dtype=bool)}
		# note that the light curves had J. dates 2450,000+ and sometimes 50,000+ IS THE SAME FILE. 
		# need to merge same-band data. P48 or P60 in the g is g. The classifier shouldn't care about the source, or deal with it.
		# 
        #(3) run the classifier
        #try:
        if 1:
            result_dict = self.PTF_LCSN_classifier(data, z=z, dz=dz)
        #except:
        #    result_dict = {}
        self.final_results = result_dict
            
            
       
if __name__ == '__main__':


    ##### To (re)generate features for given vosource.xml, it's easiest to use db_importer.py:
    #     The result from this (among other things) is a feature-added xml_string
    sys.path.append(os.environ.get("TCP_DIR") + '/Software/feature_extract')
    sys.path.append(os.environ.get("TCP_DIR") + '/Software/feature_extract/Code')
    #import db_importer
    from Code import generators_importers
    signals_list = []
    gen = generators_importers.from_xml(signals_list)
    gen.generate(xml_handle=os.path.expandvars("$HOME/scratch/sn_tutor_vosource_xmls/vosource_21293.xml"))
    gen.sig.add_features_to_xml_string(gen.signals_list)
    #NOTE: this is a string:   gen.sig.xml_string


    # For TESTING:
    
    sys.path.append(os.environ.get("TCP_DIR") + '/Software/feature_extract/Code/extractors')
    import mlens3  # for microlensing classification
    #d = mlens3.EventData(os.path.abspath(os.environ.get("TCP_DIR") + "/Data/vosource_tutor12881.xml"))
    #d = mlens3.EventData(os.path.abspath(os.environ.get("TCP_DIR") + "/Data/vosource_sn_withsdssfeats_2004az.xml"))
    d = mlens3.EventData(gen.sig.xml_string)
    #d = mlens3.EventData(os.path.abspath("/tmp/test_feature_algorithms.VOSource.xml"))
    ####NOTE: more correctly, the 'datamodel' doesnt need to come from mlens3,
    #         but can come directly from vosource_parse.py:
    #sys.path.append(os.environ.get("TCP_DIR") + '/Software/feature_extract/Code/extractors')
    #import vosource_parse
    #v = vosource_parse.vosource_parser(os.path.expandvars("$HOME/scratch/sn_tutor_vosource_xmls/vosource_21293.xml"))
    #import pprint
    #pprint.pprint(v.d)


    #gen.sig.write_xml(out_xml_fpath=new_xml_fpath)

    #(Pdb) print gen.sig.x_sdict.keys()
    #['feat_gen_date', 'src_id', 'ra', 'features', 'feature_docs', 'dec', 'dec_rms', 'class', 'ra_rms', 'ts']


    #new_xml_str = <source>.normalize_vosource_tags(xml_str)
    #self.elemtree = ElementTree.fromstring(new_xml_str)
    #xmld_data = xmldict.ConvertXmlToDict(self.elemtree)
    
    #gen.sig.feat_dict = gen.sig.x_sdict['features']

    ## run the fitter (turn off doplot for running without pylab)
    #sn =  Dovi_SN(datamodel=v.d,doplot=False)#,doplot=True)
    sn =  Dovi_SN(datamodel=d,x_sdict=gen.sig.x_sdict,doplot=False)#,doplot=True)

    ## print the results
    import pprint
    pprint.pprint(sn.final_results)


    # TODO: eventually write a test function which
    #       loads a vosource.xml into vosource_pars.py dict/structire
    #       and then passes this to sn_classifier.py algorithms which classify.
    #    - Then prints out final SN classification.
