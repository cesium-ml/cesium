from scipy.special import erf
from numpy import array,matrix,arange,sqrt,exp,mean,sum,zeros,clip,fix,\
  cumsum,hstack,floor,ceil

### ### NEED A FEATURE-CHECKING FUNCTION ### ###

# (1) parse the XML

# sys.path.append(os.path.expandvars("$TCP_DIR/Software/feature_extract/Code")
# import vosource_parse, pprint
# fname = "test_feature_algorithms.VOSource.xml"
# v = vosource_parse.vosource_parser(fname)
# pprint(v.d)
# note that v is of type xmldict.XmlDictObject
# v.d['ts'] is the parsed timeseries as a list, usually with 4 entries (time, val, valerr, limit)
# it's up to the user to decide how to use those columns...there's almost no reformating
#


# from v I need to extract: 
# closest_in_light
# closest_in_light_ttype
# closest_in_light_dm
# sdss_best_offset_in_petro_g
# sdss_best_z + sdss_best_dz
# sdss_colors:
# 	sdss_photo_rest_ug
# 	sdss_photo_rest_gr
# 	sdss_photo_rest_ri
# 	sdss_photo_rest_iz


#(2) find host
# 
#defaults:
near_z=None
gal_type=0
sloan_colors=[]
near_z=0
near_dz=0.1
nearby=False
used_sdss_colors=False
used_z=False


light_threshold=1.5
if  (closest_in_light is not None) and (closest_in_light<light_threshold)
#    this is the host
	nearby=True
	if (closest_in_light_ttype is not None) 
		gal_type=closest_in_light_ttype
	else
		gal_type=4
		
	if closest_in_light_dm is not None
		H0=70;
		near_z=H0/30*10**(closest_in_light_dm/5-9)
		dm_err=0.4 # (about 20% in distance)
		near_dz=dm_err*H0/30*log(10)/5*10**(closest_in_light_dm/5-9)
		used_z=True

sdss_threshold=2
if (sdss_best_offset_in_petro_g is not None) and (sdss_nearest_obj_type is 'Galaxy' ) and (sdss_best_offset_in_petro_g<sdss_threshold) and 

	if (sdss_best_z is not None) and (near_z is None)
		z=sdss_best_z
		dz=sdss_best_dz
		used_z=True
	else
		z=near_z
		dz=near_dz
		used_sdss_colors=True
		
	if (sdss_photo_rest_ug is not None) and (sdss_photo_rest_gr is not None) and (sdss_photo_rest_ri is not None) and (sdss_photo_rest_iz is not None) 
		sloan_colors=[sdss_photo_rest_ug,sdss_photo_rest_gr,sdss_photo_rest_ri,sdss_photo_rest_iz]
		
#(3) run the classifier?
PTF_SN_classifier(z,dz,sloan_colors=sloan_colors,gal_type=gal_type)

	
	
# (4) add flags to the out_dict:
# {'name': "nearby",           'type': "bool", 'val': nearby, "comment": "Object has a host is in Nearby galaxies catalog"}],\
# {'name': "used_sdss_colors", 'type': "bool", 'val': used_sdss_colors, "comment": "Used sloan colors to derive host-galaxy type"}],\
# {'name': "used_z",           'type': "bool", 'val': used_z, "comment": "Used z of a putative host (from SDSS or nearby catalog) as a prior"}],\


def conf_interval(x1,x2,prob,conf=0.68):
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


def PTF_SN_classifier(z,dz=0.1,sloan_colors=[],sloan_type=4,gal_type=0):
  """
  Returns a dictionary:
  posterior probabilities for Ia and CC (all types) SNe for PTF
  sub-type CC probs. for IIp, Ibc, IIn for PTF
  1-sigma confidence intervals on z for Ia+CC,Ia, and CC
  1-sigma confidence intervals on z for CC types
  
  If gal_type>0, fix that gal_type, otherwise use Sloan colors
  (either input or defined via sloan type) and their associated
  uncertainty when mapping to types.  Fractional gal or sloan types
  are permitted.
  
  Sloan colors are [u-g , g-r , r-i , i-z].
  
  Galaxy Hubble types indexed according to:
  1=E,2=S0,3=Sa,4=Sb,5=Sc,6=Sd,7=Im .
  
  Setting sloan_type instead of gal_type is useful in that it provides
  a crude propagation of typing uncertainty."""
  
  
  #
  # observed rates
  #
  obs_rate_Ia = array([4.0018, 5.0504, 5.3397, 5.5446, 5.6459, 5.6683, 5.6113, 5.4954, 5.3387, 5.1593, 4.9450, 4.5844, 4.1014, 3.5384, 2.9377, 2.3418, 1.7929, 1.3334, 1.0057, 0.8486, 0.7604, 0.6771, 0.5985, 0.5249, 0.4561, 0.3922, 0.3331, 0.2790, 0.2297, 0.1854, 0.1459, 0.1113, 0.0816, 0.0569, 0.0370])
  
  obs_rate_cc = array([0.8428, 2.3028, 2.3755, 2.2226, 1.9121, 1.6182, 1.3255, 1.0246, 0.7579, 0.5679, 0.4743, 0.3968, 0.3245, 0.2583, 0.1993, 0.1483, 0.1065, 0.0746, 0.0538, 0.0448, 0.0402, 0.0358, 0.0316, 0.0277, 0.0241, 0.0207, 0.0176, 0.0147, 0.0121, 0.0098, 0.0077, 0.0058, 0.0043, 0.0029, 0.0019])
  
  obs_rate_IIp =array([0.3377, 0.7043, 0.7691, 0.7210, 0.6151, 0.5115, 0.4047, 0.2936, 0.1958, 0.1289, 0.1013, 0.0808, 0.0626, 0.0467, 0.0332, 0.0221, 0.0135, 0.0073, 0.0037, 0.0025, 0.0023, 0.0020, 0.0018, 0.0016, 0.0014, 0.0012, 0.0011, 0.0009, 0.0008, 0.0007, 0.0006, 0.0005, 0.0004, 0.0004, 0.0003])
  
  obs_rate_Ibc =array([0.4616, 1.4410, 1.3800, 1.2553, 1.0378, 0.8448, 0.6681, 0.4958, 0.3484, 0.2459, 0.1970, 0.1582, 0.1234, 0.0929, 0.0666, 0.0449, 0.0277, 0.0154, 0.0080, 0.0056, 0.0049, 0.0043, 0.0038, 0.0033, 0.0028, 0.0024, 0.0020, 0.0016, 0.0013, 0.0011, 0.0008, 0.0006, 0.0004, 0.0003, 0.0002])
  
  obs_rate_IIn =array([0.0435, 0.1575, 0.2265, 0.2463, 0.2592, 0.2620, 0.2527, 0.2351, 0.2137, 0.1930, 0.1760, 0.1578, 0.1384, 0.1187, 0.0994, 0.0813, 0.0652, 0.0519, 0.0422, 0.0367, 0.0329, 0.0294, 0.0260, 0.0228, 0.0199, 0.0171, 0.0145, 0.0121, 0.0100, 0.0080, 0.0063, 0.0047, 0.0034, 0.0023, 0.0014])
  
  # rates are defined on the following redshift grid
  nzbins = len(obs_rate_Ia)
  zbin=0.01
  z_grid = arange(nzbins)*zbin
  z_grid1 = z_grid - zbin/2.
  z_grid1[0] = z_grid[0]
  z_grid2 = z_grid + zbin/2.
  
  
  # only do the work if the input-z is in range of interest, otherwise
  #  we throw up a flag high_z=True
  nsig=2.
  if (z-nsig*dz<max(z_grid)):
    
    # normalize
    prior_Ia = sum(obs_rate_Ia*(z_grid2-z_grid1))
    prior_cc = sum(obs_rate_cc*(z_grid2-z_grid1))
    prior_IIp = sum(obs_rate_IIp*(z_grid2-z_grid1))
    prior_Ibc = sum(obs_rate_Ibc*(z_grid2-z_grid1))
    prior_IIn = sum(obs_rate_IIn*(z_grid2-z_grid1))
    obs_rate_Ia /= prior_Ia
    obs_rate_cc /= prior_cc
    obs_rate_IIp /= prior_IIp
    obs_rate_Ibc /= prior_Ibc
    obs_rate_IIn /= prior_IIn
    
    #z measurement
    z = clip(z,min(z_grid),max(z_grid))
    if (dz<=1.e-6): dz=1.e-6
    probz = ( erf((z_grid2-z)/sqrt(2)/dz) - erf((z_grid1-z)/sqrt(2)/dz) )/\
      (z_grid2-z_grid1)
    
    #
    # core-collapse enhancement by galaxy type (1-7)
    #  (E,S0,Sa,Sb,Sc,Sd,Im)
    #
    cc_enhance = array([0.0, 0.1, 0.5, 0.9, 1.7, 1.6, 1.0])
    
    #
    # sloan best-fit z=0 colors, by galaxy type
    #  umg     gmr     rmi     imz
    #
    c0=array([[1.73,0.77,0.39,0.18],[1.65,0.74,0.38,0.19],[1.50,0.68,0.35,0.18],\
       [1.33,0.60,0.31,0.15],[1.35,0.54,0.26,0.06],[1.18,0.47,0.16,0.01],\
       [1.15,0.36,0.09,-0.06]])
    dc0=array([[0.18,0.04,0.03,0.04],[0.21,0.07,0.04,0.05],[0.29,0.1,0.05,0.07],\
       [0.28,0.13,0.09,0.09],[0.26,0.10,0.08,0.13],[0.10,0.09,0.08,0.15],\
       [0.34,0.13,0.11,0.21]])
    
    # translate these to a posterior on galaxy type
    if (gal_type==0):
      
      if (sloan_colors==[]):
        sloan_type = clip(sloan_type,1,7)
        sdn = floor(sloan_type)
        sup = ceil(sloan_type)
        sloan_colors= 0.5*( c0[sdn-1,:] + c0[sup-1,:] )
      
      chi_type = sum( ( (c0 - sloan_colors)/dc0 )**2 ,axis=1 )
      prob_type = exp(-0.5*(chi_type-chi_type.min()))
    
    else:
      
      gal_type = clip(gal_type,1,7)
      gup = ceil(gal_type); gdn = floor(gal_type)
      prob_type = zeros(7,dtype='float32')
      if (gup==gdn): prob_type[gup-1] = 1.
      else:
        prob_type[gup-1] = (gup - gal_type)/(1.*gup-gdn)
        prob_type[gdn-1] = (gal_type - gdn)/(1.*gup-gdn)

    
    
    #
    # now calculate the posterior that this is a Ia (and not a CC)
    #
    # ignore dependence of type on z, so marginalization is 2x 1d sums
    #   (basically trapezoid rule integration)
    #
    posterior_Ia_z = obs_rate_Ia*probz
    posterior_Ia_type = 1./(1.+cc_enhance)*prob_type
    posterior_Ia = mean( posterior_Ia_z*(z_grid2-z_grid1) ) * \
      mean( posterior_Ia_type ) * prior_Ia
    #
    posterior_cc_z = obs_rate_cc*probz
    posterior_cc_type = cc_enhance/(1.+cc_enhance)*prob_type
    posterior_cc = mean( posterior_cc_z*(z_grid2-z_grid1) ) * \
      mean( posterior_cc_type ) * prior_cc
    #
    posterior_z = posterior_Ia_z*mean( posterior_Ia_type )*prior_Ia + \
      posterior_cc_z*mean( posterior_cc_type )*prior_cc
    
    # 1-sigma confidence intervals
    Ia_z_1sigma = conf_interval(z_grid1,z_grid2,posterior_Ia_z,0.68)
    cc_z_1sigma = conf_interval(z_grid1,z_grid2,posterior_cc_z,0.68)
    z_1sigma = conf_interval(z_grid1,z_grid2,posterior_z,0.68)
    
    #
    # now calculate the posterior among CC types
    #
    posterior_IIp_z = obs_rate_IIp*probz
    posterior_IIp_type = 1.*prob_type
    posterior_IIp = mean( posterior_IIp_z*(z_grid2-z_grid1) ) * \
      mean( posterior_IIp_type ) * prior_IIp
    #
    posterior_Ibc_z = obs_rate_Ibc*probz
    posterior_Ibc_type = 1.*prob_type
    posterior_Ibc = mean( posterior_Ibc_z*(z_grid2-z_grid1) ) * \
      mean( posterior_Ibc_type ) * prior_Ibc
    #
    posterior_IIn_z = obs_rate_IIn*probz
    posterior_IIn_type = 1.*prob_type
    posterior_IIn = mean( posterior_IIn_z*(z_grid2-z_grid1) ) * \
      mean( posterior_IIn_type ) * prior_IIn
    
    # 1-sigma confidence intervals
    IIp_z_1sigma = conf_interval(z_grid1,z_grid2,posterior_IIp_z,0.68)
    Ibc_z_1sigma = conf_interval(z_grid1,z_grid2,posterior_Ibc_z,0.68)
    IIn_z_1sigma = conf_interval(z_grid1,z_grid2,posterior_IIn_z,0.68)
    
    cc_type_norm = posterior_IIp + posterior_Ibc + posterior_IIn
    prob_IIp = fix(round(posterior_IIp/cc_type_norm*100))/100
    prob_Ibc = fix(round(posterior_Ibc/cc_type_norm*100))/100
    prob_IIn = 1. - prob_IIp - prob_Ibc
    
    sn_norm = posterior_Ia + posterior_cc
    prob_Ia = fix(round(posterior_Ia/(posterior_Ia + posterior_cc)*100))/100
    prob_CC = 1. - prob_Ia
    
    # return a dictionary of the results
    out_dict1 = {'high_z':False,\
      'Prob_Ia':prob_Ia,\
      'Prob_CC':prob_CC,\
      'Prob_IIp|CC':prob_IIp,\
      'Prob_Ibc|CC':prob_Ibc,\
      'Prob_IIn|CC':prob_IIn,\
      'z_1sigma':z_1sigma,'z_1sigma|Ia':Ia_z_1sigma,'z_1sigma|CC':cc_z_1sigma,\
      'z_1sigma|IIp':IIp_z_1sigma,'z_1sigma|Ibc':Ibc_z_1sigma,'z_1sigma|IIp':IIp_z_1sigma}
  
  else:
    #high-z
    
    zdn,zup = z,z
    if (dz>0):
      zdn = fix( round((z-dz)/dz) )*dz
      zup = fix( round((z+dz)/dz) )*dz
    
    z1sigma = (zdn,zup)
    out_dict1 = {'high_z':True,\
      'Prob_Ia':fix(0.99*100)/100,\
      'Prob_CC':fix(0.01*100)/100,\
      'Prob_IIp|CC':fix(0.34*100)/100,\
      'Prob_Ibc|CC':fix(0.33*100)/100,\
      'Prob_IIn|CC':fix(0.33*100)/100,\
      'z_1sigma':z1sigma,'z_1sigma|Ia':z1sigma,'z_1sigma|CC':z1sigma,\
      'z_1sigma|IIp':z1sigma,'z_1sigma|Ibc':z1sigma,'z_1sigma|IIp':z1sigma}
  
  
  out_dict={	'<SN classify Plugin v0.1>': { \
	  'class_results':{ \
	        'SN Ia':{'prob':  out_dict1['prob_Ia'],\
	                 'weight':1.0,\
	                 'TUTOR_name': "tia",\
	                 'comments': "No Ia subtypes",\
	                 'class_value_added_statements': {'name': "z_1sigma",'value' : out_dict1['Ia_z_1sigma'], 'comments': "This is the 1sigma redshift interval if it is a Ia"},\
	                 'subclass': { \
	                     '1991bg-like'  : {'prob': None, 'weight': 0.0, 'TUTOR-name': None},\
	                     'super-Chandra': {'prob': None, 'weight': 0.0, 'TUTOR-name': "tiasc"},\
	                     'Branch-Normal': {'prob': None, 'weight': 0.0, 'TUTOR-name': None},\
	                     'peculiar':      {'prob': None, 'weight': 0.0, 'TUTOR-name': None}}},
			'SN CC':{'prob':  out_dict1['prob_CC'],\
					'weight':1.0,\
					'TUTOR_name': "cc",\
					'comments': None,\
					'class_value_added_statements': {'name': "z_1sigma",'value' : out_dict1['cc_z_1sigma'], 'comments': "This is the 1sigma redshift interval if it is a CC-SN"}},
	        'SN Ibc':{'prob':  out_dict1['prob_Ibc'],\
	                 'weight':1.0,\
	                 'TUTOR_name': None,\
	                 'comments': "no Ib Ic differenciation",\
	                 'class_value_added_statements': {'name': "z_1sigma",'value' : out_dict1['Ibc_z_1sigma'], 'comments': "This is the 1sigma redshift interval if it is a Ibc"},\
	                 'subclass': { \
	                     'Ib'  : 	 {'prob': None, 'weight': 0.0, 'TUTOR-name': "tib"},\
	                     'Ic': 		 {'prob': None, 'weight': 0.0, 'TUTOR-name': "tic"},\
	                     'peculiar': {'prob': None, 'weight': 0.0, 'TUTOR-name': None}}},
	      'SN IIP':{'prob':  out_dict1['prob_IIp'],\
	                 'weight':1.0,\
	                 'TUTOR_name': "iip",\
	                 'comments': "Type II SNe are broken to IIP and IIn",\
	                 'class_value_added_statements': {'name': "z_1sigma",'value' : out_dict1['IIp_z_1sigma'], 'comments': "This is the 1sigma redshift interval if it is a IIp"},\
	                 'subclass': { \
	                     'IIP'  : 	 {'prob': None, 'weight': 0.0, 'TUTOR-name': "iip"},\
	                     'IIL': 		 {'prob': None, 'weight': 0.0, 'TUTOR-name': "iil"},\
	                     'IIb': 		 {'prob': None, 'weight': 0.0, 'TUTOR-name': "iib"},\
	                     'peculiar': {'prob': None, 'weight': 0.0, 'TUTOR-name': None}}},
	      'SN IIn':{'prob':  out_dict1['prob_IIn'],\
	                 'weight':1.0,\
	                 'TUTOR_name': "iin",\
	                 'comments': "Type II SNe are broken to IIP and IIn",\
	                 'class_value_added_statements': {'name': "z_1sigma",'value' : out_dict1['IIn_z_1sigma'], 'comments': "This is the 1sigma redshift interval if it is a IIn"}}},
	 'global_statements_and_flags': [\
	           {'name': "interesting_object", 'type': "bool", 'val': None, "comment": None},\
	           {'name': "high-z", 'type': "bool", 'val': out_dict1['high_z'], "comment": None}],\
	 'comments' : "in this version weights are 0 or 1, the first for unconstrained questions, the latter for any derived value.",\
	 'version': "v0.1"}}
  
  return out_dict
