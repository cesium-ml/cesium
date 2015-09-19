import os, glob, sys, types
#ext1 = os.environ.get('TCP_DIR') + 'Software/feature_extract/Code/extractors/'

#20101207#from chi2_per_deg_extractor  import chi2_per_deg_extractor
#20101207#from chi2extractor  import chi2extractor
#20101207#from dc_extractor  import dc_extractor
from .dist_from_u_extractor  import dist_from_u_extractor
from .fourier_extractor  import fourier_extractor
from .linear_extractor  import linear_extractor
from .max_slope_extractor  import max_slope_extractor
from .median_extractor  import median_extractor
from .beyond1std_extractor  import beyond1std_extractor
from .stdvs_from_u_extractor  import stdvs_from_u_extractor
#from old_dcextractor  import old_dcextractor
# # # 20100912 disabled due to lomb() call# from power_spectrum_extractor  import power_spectrum_extractor
# # # 20100912 disabled due to lomb() call# from power_extractor import power_extractor
#20080614#from montecarlo_extractor import montecarlo_extractor
#20080614#from pct_montecarlo_extractor import pct_80_montecarlo_extractor, pct_90_montecarlo_extractor, pct_95_montecarlo_extractor, pct_99_montecarlo_extractor
#20080614#from significant_power_extractor import significant_80_power_extractor, significant_90_power_extractor, significant_95_power_extractor, significant_99_power_extractor
#20080614#from first_freq_extractor  import first_freq_extractor
from .sine_fit_extractor  import sine_fit_extractor
from .sine_leastsq_extractor  import sine_leastsq_extractor
from .skew_extractor  import skew_extractor
#from kurtosis_extractor  import kurtosis_extractor #20101121 joey recommends disabling since it is very similar to small_kurtosis_extractor
from .s_extractor import s_extractor
#from small_kurtosis_extractor  import small_kurtosis_extractor
from .std_extractor  import std_extractor
from .median_absolute_deviation_extractor import median_absolute_deviation_extractor
from .wei_av_uncertainty_extractor  import wei_av_uncertainty_extractor
from .weighted_average_extractor  import weighted_average_extractor
# # # 20100912 disabled due to lomb() call# from lomb_extractor  import lomb_extractor
# # # 20100912 disabled due to lomb() call# from first_lomb_extractor  import first_lomb_extractor
# # # 20100912 disabled due to lomb() call# from sine_lomb_extractor  import sine_lomb_extractor
#20080614#from second_extractor  import second_extractor, third_extractor
# # # 20100912 disabled due to lomb() call# from second_lomb_extractor import second_lomb_extractor
# # # 20100912 disabled due to lomb() call# from frequency_ratio_extractor import ratio21, ratio31, ratio32
#from example_extractor  import example_extractor
from .n_points_extractor import n_points_extractor

#from position_intermediate_extractor import position_intermediate_extractor
#20101207#from galb_extractor import galb_extractor
#20101207#from ecpb_extractor import ecpb_extractor
#20101207#from ecpl_extractor import ecpl_extractor
#20101207#from gall_extractor import gall_extractor
#from tmpned_extractor import tmpned_extractor # 20100914: dstarr disables this for now since running on non lyra LAN clusters, and we dont care about context features at the moment.
#from ratioRUfirst_extractor import ratioRUfirst_extractor
#20101207#from distance_in_kpc_to_nearest_galaxy import distance_in_kpc_to_nearest_galaxy
#20101207#from distance_in_arcmin_to_nearest_galaxy import distance_in_arcmin_to_nearest_galaxy
#20101121commentedout# from lomb_scargle_extractor import lomb_scargle_extractor, freq1_harmonics_amplitude_0_extractor, freq1_harmonics_amplitude_error_0_extractor, freq1_harmonics_freq_0_extractor, freq1_harmonics_moments_0_extractor, freq1_harmonics_moments_err_0_extractor, freq1_harmonics_peak2peak_flux_extractor, freq1_harmonics_peak2peak_flux_error_extractor, freq1_harmonics_rel_phase_0_extractor, freq1_harmonics_rel_phase_error_0_extractor, freq2_harmonics_amplitude_0_extractor, freq2_harmonics_amplitude_error_0_extractor, freq2_harmonics_freq_0_extractor, freq2_harmonics_moments_0_extractor, freq2_harmonics_moments_err_0_extractor, freq2_harmonics_rel_phase_0_extractor, freq2_harmonics_rel_phase_error_0_extractor, freq3_harmonics_amplitude_0_extractor, freq3_harmonics_amplitude_error_0_extractor, freq3_harmonics_freq_0_extractor, freq3_harmonics_moments_0_extractor, freq3_harmonics_moments_err_0_extractor, freq3_harmonics_rel_phase_0_extractor, freq3_harmonics_rel_phase_error_0_extractor, freq_harmonics_offset_extractor, freq_y_offset_extractor, freq_signif_extractor, freq_nharm_extractor, freq1_harmonics_amplitude_1_extractor, freq1_harmonics_amplitude_2_extractor, freq1_harmonics_amplitude_3_extractor, freq1_harmonics_rel_phase_1_extractor, freq1_harmonics_rel_phase_2_extractor, freq1_harmonics_rel_phase_3_extractor, freq1_harmonics_moments_1_extractor, freq1_harmonics_moments_2_extractor, freq1_harmonics_moments_3_extractor, freq2_harmonics_amplitude_1_extractor, freq2_harmonics_amplitude_2_extractor, freq2_harmonics_amplitude_3_extractor, freq2_harmonics_rel_phase_1_extractor, freq2_harmonics_rel_phase_2_extractor, freq2_harmonics_rel_phase_3_extractor, freq2_harmonics_moments_1_extractor, freq2_harmonics_moments_2_extractor, freq2_harmonics_moments_3_extractor, freq3_harmonics_amplitude_1_extractor, freq3_harmonics_amplitude_2_extractor, freq3_harmonics_amplitude_3_extractor, freq3_harmonics_rel_phase_1_extractor, freq3_harmonics_rel_phase_2_extractor, freq3_harmonics_rel_phase_3_extractor, freq3_harmonics_moments_1_extractor, freq3_harmonics_moments_2_extractor, freq3_harmonics_moments_3_extractor, linear_trend_extractor, freq_varrat_extractor, freq_signif_ratio_21_extractor, freq_signif_ratio_31_extractor, freq_frequency_ratio_21_extractor, freq_frequency_ratio_31_extractor, freq_amplitude_ratio_21_extractor, freq_amplitude_ratio_31_extractor


from .lomb_scargle_extractor import lomb_scargle_extractor, freq1_harmonics_amplitude_0_extractor, freq1_harmonics_freq_0_extractor, freq1_harmonics_rel_phase_0_extractor, freq2_harmonics_amplitude_0_extractor, freq2_harmonics_freq_0_extractor, freq2_harmonics_rel_phase_0_extractor, freq3_harmonics_amplitude_0_extractor, freq3_harmonics_freq_0_extractor, freq3_harmonics_rel_phase_0_extractor, freq_y_offset_extractor, freq_signif_extractor, freq1_harmonics_amplitude_1_extractor, freq1_harmonics_amplitude_2_extractor, freq1_harmonics_amplitude_3_extractor, freq1_harmonics_rel_phase_1_extractor, freq1_harmonics_rel_phase_2_extractor, freq1_harmonics_rel_phase_3_extractor, freq2_harmonics_amplitude_1_extractor, freq2_harmonics_amplitude_2_extractor, freq2_harmonics_amplitude_3_extractor, freq2_harmonics_rel_phase_1_extractor, freq2_harmonics_rel_phase_2_extractor, freq2_harmonics_rel_phase_3_extractor, freq3_harmonics_amplitude_1_extractor, freq3_harmonics_amplitude_2_extractor, freq3_harmonics_amplitude_3_extractor, freq3_harmonics_rel_phase_1_extractor, freq3_harmonics_rel_phase_2_extractor, freq3_harmonics_rel_phase_3_extractor, linear_trend_extractor, freq_varrat_extractor, freq_signif_ratio_21_extractor, freq_signif_ratio_31_extractor, freq_frequency_ratio_21_extractor, freq_frequency_ratio_31_extractor, freq_amplitude_ratio_21_extractor, freq_amplitude_ratio_31_extractor, p2p_scatter_2praw_extractor, p2p_scatter_over_mad_extractor, p2p_scatter_pfold_over_mad_extractor, medperc90_2p_p_extractor, p2p_ssqr_diff_over_var_extractor, fold2P_slope_10percentile_extractor, fold2P_slope_90percentile_extractor, freq_n_alias_extractor, freq_model_phi1_phi2_extractor, freq_model_min_delta_mags_extractor, freq_model_max_delta_mags_extractor, freq1_lambda_extractor

from .scatter_res_raw_extractor import scatter_res_raw_extractor
#from psd_example_extractor import psd_example_extractor
from .gskew_extractor import gskew_extractor
# ishivvers additions:
from .phase_dispersion_extractor import phase_dispersion_freq0_extractor, ratio_PDM_LS_freq0_extractor
from .delta_phase_2minima_extractor import delta_phase_2minima_extractor

#from eclipse_poly_extractor import eclipse_poly_extractor, eclpoly_best_orb_chi2_extractor, eclpoly_best_orb_period_extractor, eclpoly_15_ratio_diff_extractor, eclpoly_20_ratio_diff_extractor, eclpoly_30_ratio_diff_extractor, eclpoly_5_ratio_diff_extractor, eclpoly_8_ratio_diff_extractor, eclpoly_is_suspect_extractor, eclpoly_orb_signif_extractor, eclpoly_final_period_ratio_extractor
#20120130, eclpoly_p_pulse_extractor, eclpoly_p_pulse_initial_extractor

#20100518 added this line:
from .watt_per_m2_flux_extractor import watt_per_m2_flux_extractor

from .min_max_extractor import min_extractor, max_extractor
from .amplitude_extractor import amplitude_extractor, percent_amplitude_extractor, percent_difference_flux_percentile_extractor, flux_percentile_ratio_mid20_extractor, flux_percentile_ratio_mid35_extractor, flux_percentile_ratio_mid50_extractor, flux_percentile_ratio_mid65_extractor, flux_percentile_ratio_mid80_extractor
#20101124 disable for now since single band is similar to other features.  revisit this when we have multibands# from ws_variability_extractor import ws_variability_self_extractor,ws_variability_bv_extractor, ws_variability_ru_extractor,ws_variability_ug_extractor,ws_variability_gr_extractor,ws_variability_ri_extractor,ws_variability_iz_extractor
from .median_buffer_range_percentage_extractor import median_buffer_range_percentage_extractor
#from lomb_scargle_extractor import ex2_extractor
###from example_extractor  import example_extractor
#20110204 comment out since needs reqork to be generally applicable#from pair_slope_trend_extractor import pair_slope_trend_extractor
#ignores = ["min_max_extractor"]  ## broken module names should be put here.
# NOTE: qso_extractor: This is not active, and is only used below (if it was active, it would returna a dictionary)
from .qso_extractor import qso_extractor
#from qso_extractor import qso_lvar_extractor, qso_ltau_extractor, qso_chi2nu_extractor, qso_chi2_qsonu_extractor, qso_chi2_qso_nu_NULL_extractor, qso_signif_qso_extractor, qso_signif_not_qso_extractor, qso_signif_vary_extractor, qso_chi2qso_nu_nuNULL_ratio_extractor
from .qso_extractor import qso_log_chi2_qsonu_extractor, qso_log_chi2nuNULL_chi2nu_extractor
from .stetson_extractor import stetson_j_extractor, stetson_k_extractor
#stetson_mean_extractor, # this is essentially the mean lightcurve magnitude

#from .color_diff_extractor import static_colors_extractor, color_diff_jh_extractor, color_diff_hk_extractor, color_diff_bj_extractor, color_diff_vj_extractor, color_diff_rj_extractor, color_bv_extinction_extractor

from .lcmodel_extractor import lcmodel_extractor, lcmodel_pos_mag_ratio_extractor, lcmodel_pos_n_ratio_extractor, lcmodel_median_n_per_day_extractor, lcmodel_pos_n_per_day_extractor, lcmodel_neg_n_per_day_extractor, lcmodel_pos_area_ratio_extractor

from .ar_is_extractor import ar_is_theta_extractor, ar_is_sigma_extractor

## JSB additions
from .interng_extractor import interng_extractor


from .old_dc_extractor import old_dc_extractor
#20101207#from closest_in_light import closest_in_light
#20101207#from closest_in_light_absolute_bmag import closest_in_light_absolute_bmag
#20101207#from closest_in_light_angle_from_major_axis import closest_in_light_angle_from_major_axis
#20101207#from closest_in_light_angular_offset_in_arcmin import closest_in_light_angular_offset_in_arcmin
#20101207#from closest_in_light_dm import closest_in_light_dm
#20101207#from closest_in_light_physical_offset_in_kpc import closest_in_light_physical_offset_in_kpc
#20101207#from closest_in_light_ttype import closest_in_light_ttype

#20101207#from intersdss_extractor import intersdss_extractor
#20101207#from sdss_dist_arcmin import sdss_dist_arcmin
#20101207#from sdss_best_dm import sdss_best_dm
#20101207#from sdss_best_z import sdss_best_z
#20101207#from sdss_best_zerr import sdss_best_zerr
#20101207#from sdss_photo_z_pztype import sdss_photo_z_pztype
#20101207#from sdss_chicago_class import sdss_chicago_class
#20101207#from sdss_best_offset_in_kpc import sdss_best_offset_in_kpc
#20101207#from sdss_best_z import sdss_best_z
#20101207#from sdss_best_zerr import sdss_best_zerr
#20101207#from sdss_dered_g import sdss_dered_g
#20101207#from sdss_dered_i import sdss_dered_i
#20101207#from sdss_dered_z import sdss_dered_z
#20101207#from sdss_dered_r import sdss_dered_r
#20101207#from sdss_dered_u import sdss_dered_u
#20101207#from sdss_in_footprint import sdss_in_footprint
#20101207#from sdss_nearest_obj_type import sdss_nearest_obj_type
#20101207#from sdss_spec_confidence import sdss_spec_confidence

#20101207#from sdss_photo_rest_abs_g import sdss_photo_rest_abs_g
#20101207#from sdss_photo_rest_abs_i import sdss_photo_rest_abs_i
#20101207#from sdss_photo_rest_abs_r import sdss_photo_rest_abs_r
#20101207#from sdss_photo_rest_abs_u import  sdss_photo_rest_abs_u
#20101207#from sdss_photo_rest_abs_z import sdss_photo_rest_abs_z
#20101207#from sdss_photo_rest_gr import sdss_photo_rest_gr
#20101207#from sdss_photo_rest_iz import sdss_photo_rest_iz
#20101207#from sdss_photo_rest_ri import sdss_photo_rest_ri
#20101207#from sdss_photo_rest_ug import sdss_photo_rest_ug
#20101207#from sdss_best_offset_in_petro_g import sdss_best_offset_in_petro_g
#20101207#from  sdss_petro_radius_g import sdss_petro_radius_g
#20101207#from  sdss_petro_radius_g_err import sdss_petro_radius_g_err

#20101207#from sdss_first_flux_in_mjy import sdss_first_flux_in_mjy
#20101207#from sdss_first_offset_in_arcsec import sdss_first_offset_in_arcsec
#20101207#from sdss_rosat_flux_in_mJy import sdss_rosat_flux_in_mJy
#20101207#from sdss_rosat_log_xray_luminosity import sdss_rosat_log_xray_luminosity
#20101207#from sdss_rosat_offset_in_arcsec import sdss_rosat_offset_in_arcsec
#20101207#from sdss_rosat_offset_in_sigma import sdss_rosat_offset_in_sigma

#tmp = glob.glob(ext1 + "*extract*.py")
#tmp = [os.path.basename(x).split(".py")[0] for x in tmp]
#for i in ignores:
#     if i in tmp:
#         tmp.remove(i)

#for n in tmp:
#       try:
#               print "import %s" %n
#               exec "import %s" % n
#               ## get all the classes from this module
#               tmp = \
#"""zclass = []
#f = %s.__file__.replace(".pyc",".py")
#tmp = open(f,"r")
#ff = tmp.readlines()
#tmp.close()
#for l in ff:
#    if l[:15].find("class ") != -1:
#         zclass.append(l.split("class ")[1].split("(")[0])
#if len(zclass) > 0:
#    tmp = "from %s import " + ", ".join([x for x in zclass])
#    exec tmp""" % (n,n)
#               exec tmp
#       except:
#               print "could not import %s" % n



#__all__=["chi2extractor","dc_extractor","dist_from_u_extractor","fourierextractor","linear_extractor","max_slope_extractor","medianextractor","beyond1std_extractor","stdvs_from_u_extractor","old_dcextractor","power_spectrum_extractor","power_extractor","pct_80_montecarlo_extractor","pct_90_montecarlo_extractor","pct_95_montecarlo_extractor","pct_99_montecarlo_extractor","significant_80_power_extractor","significant_90_power_extractor","significant_95_power_extractor","significant_99_power_extractor","first_freq_extractor","sine_fit_extractor","sine_leastsq_extractor","skew_extractor","stdextractor","wei_av_uncertainty_extractor","weighted_average_extractor","lomb_extractor","first_lomb_extractor","sine_lomb_extractor","second_extractor","third_extractor","second_lomb_extractor"]
