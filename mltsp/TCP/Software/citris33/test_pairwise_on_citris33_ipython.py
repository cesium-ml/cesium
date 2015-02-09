#!/usr/bin/env python
"""
Do this in different screens on citirs33 head node  (in this order):

### (within a seperate screen)
ipcontroller

### (within a seperate screen)
qsub start_ipengines.qsub

   (wait 60 seconds for cluster to show SessID in "qstat -a")


### (within a seperate screen)
module load gcc


/global/home/users/dstarr/src/install/epd-6.2-2-rh5-x86_64/lib/python2.6/pdb.py test_pairwise_on_citris33_ipython.py --pairwise_classifier_pkl_fpath=$HOME/scratch/pairwise_classifier__debosscher_table3.pkl.gz --use_hardcoded_sciclass_lookup

NOTE: If we wish to flush an existing queue of Ipython tasks, without killing the qsub cluster & ipcontroller,
      do within a fresh python shell:

from IPython.kernel import client
tc = client.TaskClient()
tc.task_controller.clear()

      Then you can restart test_pairwise_on_citris33_ipythonpy and it will reset mec() and start normally.


"""
from __future__ import print_function

import sys, os
import cPickle
import time
import gzip
import copy
from optparse import OptionParser

#import generators_importers
#from generators_importers import from_xml

sys.path.append(os.path.abspath(os.environ.get('TCP_DIR') + 'Software/ingest_tools'))
#import pairwise_classification

"""
TODO: this is to be called by something like analysis_deboss_tcp_source_compare.py
 - this is to be run on Citris33 ipython cluster
 - this does what ./generate_weka_classifiers.py --train_mode     does
 - this does what ./pairwise_classification.py --deboss_percentage_exclude_analysis   does    (the classification part)
 - although the final plot generation of ./pairwise_classification.py --deboss_percentage_exclude_analysis   is done somewhere else

TODO: resample vosource
   -> do analysis_deboss_tcp_source_compare.py --> perc_subset_worker()
        tasks on the per srcid level (do for a bunch of percents
   -> thus only one srcid xml is needed to be loaded.
   
TODO: for each resampled & refeatured xml_string at perc, srcid, generate arffline :

                exec_str = "out_dict = a.generate_arff_line_for_vosourcexml(num="%s", xml_fpath="%s")
                " % (str(num), xml_fpath)
                #print exec_str
                try:
                    taskid = self.tc.run(client.StringTask(exec_str, \
                                            pull='out_dict', retries=3))


TODO: pairwise classify at 



This will be called / run in a couple ways:
 - On an Ipython client:
     a_class.a_method(srcid=srcid, perc=perc, n_iters=n_iters, classifier_id=?)
     -> INPUT: srcid could be a INT or list
     -> INPUT: perc could be a FLOAT or list
     -> INPUT: classifier_id :: This would be used for identifying crossvalid-fold
     -> returns: classified results in a dict?  like an ipython task of:
             pairwise_classification.py --deboss_percentage_exclude_analysis
 - via command line :for testing or even simple parallelization (--flags)

"""

deboss_srcid_list = [148841, 148865, 148864, 148863, 148862, 148861, 148860, 148859, 148858, 148857, 148856, 148855, 148854, 148853, 148852, 148851, 148850, 148849, 148848, 148847, 148846, 148845, 148844, 148843, 148842, 148392, 148415, 148416, 148419, 148435, 148440, 148443, 148472, 148483, 148514, 148516, 148531, 148540, 148544, 148575, 148583, 161328, 148590, 148600, 148604, 148619, 148650, 148655, 148660, 148763, 148767, 148780, 148083, 148794, 148835, 148092, 148101, 148137, 161330, 148026, 148103, 148027, 148117, 148151, 148155, 148153, 148163, 161331, 148173, 148192, 148032, 148203, 148208, 148225, 148230, 148242, 148243, 148244, 148267, 148290, 148293, 148303, 148325, 148335, 148345, 148346, 148371, 148374, 148707, 148708, 148709, 148710, 148711, 148712, 148713, 148715, 148716, 148717, 148718, 148719, 148720, 148721, 148722, 148723, 148724, 148725, 148726, 148727, 148728, 148729, 148730, 148731, 148732, 148733, 148734, 148735, 148736, 148737, 148738, 148739, 148740, 148741, 148742, 148743, 148744, 148745, 148746, 148061, 148747, 148748, 148749, 148750, 148751, 148752, 148753, 148754, 148755, 148756, 148757, 148758, 148759, 148760, 148761, 148762, 148764, 148765, 148766, 148768, 148769, 148770, 148771, 148772, 148773, 148774, 148775, 148776, 148777, 148778, 148779, 148781, 148782, 148062, 148783, 148784, 148785, 148786, 148787, 148063, 148064, 148788, 148789, 148790, 148791, 148792, 148793, 148065, 148795, 148796, 148797, 148798, 148799, 148800, 148801, 148802, 148803, 148804, 148805, 148806, 148807, 148808, 148809, 148810, 148066, 148811, 148812, 148813, 148814, 148815, 148067, 148816, 148817, 148818, 148819, 148820, 148821, 148822, 148823, 148824, 148825, 148826, 148827, 148828, 148829, 148830, 148831, 148832, 148833, 148834, 148836, 148068, 148837, 148838, 148839, 148840, 148069, 148714, 148017, 148070, 148018, 148071, 148072, 148073, 148074, 148075, 148076, 148077, 148078, 148079, 148080, 148081, 148082, 148011, 148084, 148085, 148086, 148087, 148088, 148089, 148019, 148090, 148091, 148093, 148094, 148095, 148020, 148096, 148021, 148097, 148098, 148099, 148100, 148022, 148102, 148104, 148023, 148105, 148106, 148107, 148108, 148109, 148110, 148111, 148112, 148113, 148115, 148114, 148116, 148118, 148119, 148120, 148121, 148122, 148123, 148124, 148125, 148126, 148127, 148128, 148012, 148129, 148130, 148131, 148024, 148132, 148133, 148134, 148135, 148136, 148025, 148138, 148139, 148140, 148141, 148142, 148143, 148144, 148145, 148146, 148147, 148148, 148149, 148150, 148152, 148154, 148156, 148157, 148158, 148159, 148160, 148161, 148162, 148164, 148165, 148166, 148167, 148168, 148169, 148170, 148171, 148172, 148174, 161337, 148028, 148175, 148176, 148177, 148178, 148179, 148180, 148181, 148182, 148183, 148184, 148185, 148186, 148187, 148188, 148189, 148190, 148191, 148193, 148194, 148195, 148196, 148197, 148198, 148199, 148200, 148201, 148202, 148204, 148205, 148206, 148207, 148209, 148210, 161336, 148211, 148029, 148030, 148212, 148213, 148214, 148215, 148216, 148217, 148218, 148219, 148220, 148221, 148222, 148223, 148224, 148226, 148227, 148228, 148229, 161334, 148231, 148232, 148233, 148234, 148235, 148236, 148237, 148238, 148239, 148240, 148241, 148245, 148246, 148247, 148248, 148249, 148031, 148250, 148251, 148252, 148253, 161333, 148254, 148255, 148256, 148257, 148258, 148259, 148260, 148261, 148262, 148263, 148264, 148265, 148266, 148268, 148269, 148270, 148271, 148272, 148273, 148274, 148275, 148276, 148277, 148278, 148279, 148280, 148281, 148282, 148033, 148283, 148284, 148285, 148286, 148287, 148288, 148289, 148291, 148292, 148294, 148295, 148296, 148297, 148298, 148299, 148300, 148301, 148034, 148302, 148304, 148035, 148305, 148306, 148307, 148308, 148309, 148310, 148311, 148312, 148036, 148313, 148314, 148315, 148316, 148317, 148318, 148319, 148320, 148321, 148322, 148323, 148324, 148326, 148327, 148328, 148329, 148330, 148331, 148332, 148333, 148334, 148336, 148337, 148338, 148339, 148340, 148341, 148342, 148037, 148013, 148343, 148344, 148347, 148348, 148349, 148350, 148351, 148352, 148353, 148354, 148355, 148356, 148038, 161329, 148357, 148358, 148359, 148360, 148361, 148362, 148363, 148364, 148365, 148366, 148367, 148368, 148369, 148370, 148039, 148372, 148373, 148375, 161335, 148376, 148040, 148377, 148378, 148379, 148380, 148381, 148382, 148383, 148384, 148385, 148386, 148041, 148387, 148388, 148389, 148042, 148390, 148391, 148393, 148394, 148395, 161332, 148396, 148397, 148043, 148398, 148399, 148400, 148044, 148401, 148402, 161338, 148403, 148404, 148405, 148406, 148407, 148408, 148409, 148410, 148411, 148412, 148413, 148414, 148045, 148417, 148418, 148046, 148420, 148421, 148422, 148423, 148424, 148425, 148426, 148427, 148428, 148429, 148430, 148431, 148432, 148433, 148434, 148010, 148047, 148436, 148437, 148438, 148439, 148441, 148442, 148444, 148445, 148446, 148447, 148448, 148449, 148450, 148451, 148048, 148452, 148453, 148454, 148455, 148456, 148457, 148458, 148459, 148460, 148461, 148462, 148463, 148464, 148465, 148466, 148467, 148468, 148469, 148470, 148471, 148473, 148474, 148475, 148476, 148477, 148478, 148479, 148480, 148481, 148014, 148482, 148484, 148485, 148486, 148487, 148488, 148489, 148490, 148491, 148049, 148492, 148493, 148494, 148495, 148496, 148497, 148498, 148499, 148500, 148501, 148502, 148503, 148504, 148505, 148015, 148506, 148507, 148508, 148509, 148510, 148511, 148512, 148513, 148515, 148050, 148517, 148518, 148519, 148520, 148521, 148522, 148523, 148051, 148524, 148525, 148526, 148527, 148528, 148529, 148530, 148532, 148533, 148534, 148016, 148535, 148536, 148537, 148538, 148539, 148541, 148542, 148543, 148545, 148546, 148547, 148548, 148549, 148550, 148551, 148552, 148553, 148052, 148554, 148555, 148556, 148557, 148558, 148559, 148560, 148561, 148562, 148563, 148564, 148565, 148566, 148567, 148568, 148569, 148570, 148571, 148572, 148573, 148574, 148576, 148577, 148578, 148579, 148580, 148053, 148054, 148581, 148582, 148584, 148585, 148586, 148587, 148588, 148589, 148591, 148592, 148593, 148594, 148595, 148596, 148597, 148598, 148599, 148601, 148602, 148603, 148605, 148606, 148608, 148607, 148609, 148055, 148610, 148611, 148612, 148056, 148613, 148614, 161327, 148615, 161326, 148616, 148617, 148618, 148057, 148620, 148621, 148622, 148623, 148624, 148625, 148626, 148627, 148628, 148629, 148630, 148631, 148632, 148633, 148634, 148635, 148636, 148637, 148638, 148639, 148640, 148641, 148642, 148643, 148644, 148645, 148646, 148647, 148648, 148649, 148651, 148652, 148653, 148654, 148656, 148657, 148658, 148659, 148661, 148662, 148663, 148664, 148665, 148666, 148667, 148668, 148669, 148670, 148671, 148672, 148673, 148674, 148675, 148676, 148677, 148678, 148679, 148058, 148680, 148681, 148682, 148683, 148684, 148685, 148686, 148687, 148688, 148689, 148690, 148691, 148692, 148693, 148694, 148695, 148696, 148697, 148059, 148060, 148698, 148699, 148700, 148701, 148702, 148703, 148704, 148705, 148706, 148869, 148871, 148874, 149005, 149009, 149008, 149004, 149011, 149010, 149007, 149015, 148878, 148877, 148882, 148881, 148886, 148888, 148900, 148895, 148896, 148911, 148908, 148912, 148910, 148909, 148913, 148917, 148918, 148919, 148922, 148916, 148920, 148915, 148921, 148902, 148906, 148904, 148907, 148901, 148903, 148928, 148927, 148929, 148925, 148931, 148938, 148934, 148936, 148943, 148940, 148937, 148944, 148939, 148941, 148924, 148926, 148952, 148950, 148949, 148958, 148957, 148954, 148956, 148955, 148962, 148963, 148948, 148946, 148972, 148973, 148974, 148976, 148975, 148979, 148966, 148969, 148971, 148967, 148970, 148984, 148989, 148988, 148992, 148991, 148982, 148981, 148980, 148985, 148983, 148986, 148998, 148997, 148995, 149001, 148866, 148870, 148867, 148868, 148872, 148873, 148875, 148876, 148879, 148880, 148883, 148884, 148885, 148887, 148889, 148891, 148890, 148892, 148893, 148894, 148897, 148898, 148899, 148905, 148914, 148923, 148930, 148932, 148933, 148935, 148942, 148945, 148947, 148951, 148953, 148960, 148959, 148961, 148964, 148965, 148968, 148977, 148978, 148987, 148990, 148993, 148994, 148996, 148999, 149000, 149002, 149003, 149006, 149012, 149013, 149014, 149016, 149017, 149018, 149019, 149020, 149021, 149022, 149023, 149024, 149025, 149026, 149027, 149028, 149029, 149030, 149031, 149033, 149032, 149034, 149035, 149036, 149037, 149038, 149039, 149040, 149041, 149042, 149043, 149044, 149045, 149046, 149047, 149048, 149049, 149050, 149051, 149054, 149053, 149052, 149056, 149057, 149058, 149055, 149060, 149059, 149065, 149061, 149062, 149063, 149064, 149067, 149069, 149066, 149068, 149072, 149070, 149073, 149071, 149074, 149079, 149075, 149076, 149078, 149077, 149080, 149081, 149082, 149083, 149084, 149088, 149087, 149085, 149086, 149089, 149090, 149091, 149092, 149093, 149094, 149095, 149096, 149097, 149100, 149098, 149099, 149101, 149103, 149102, 149104, 149105, 149106, 149107, 149108, 149109, 149112, 149110, 149111, 149113, 149115, 149114, 149116, 149117, 149118, 149119, 149120, 149121, 149122, 149123, 149124, 149126, 149125, 149127, 149128, 149129, 149131, 149130, 149132, 149133, 149135, 149136, 149134, 149138, 149137, 149139, 149140, 149141, 149142, 149143, 149145, 149144, 149146, 149147, 149148, 149149, 149150, 149151, 149152, 149153, 149154, 149156, 149155, 149159, 149158, 149157, 149160, 149161, 149162, 149163, 149164, 149165, 149167, 149166, 149168, 149169, 149170, 149171, 149172, 149173, 149174, 149175, 149176, 149177, 149178, 149179, 149180, 149181, 149182, 149183, 149184, 149185, 149188, 149186, 149187, 149189, 149190, 149192, 149191, 149193, 149195, 149196, 149194, 149198, 149200, 149199, 149197, 149202, 149201, 149204, 149203, 149205, 149206, 149207, 149208, 149210, 149209, 149211, 149212, 149213, 149214, 149215, 149216, 149217, 149222, 149219, 149218, 149220, 149221, 149223, 149229, 149224, 149228, 149225, 149226, 149227, 149230, 149231, 149241, 149232, 149237, 149233, 149234, 149235, 149236, 149238, 149240, 149239, 149243, 149242, 149244, 149245, 149246, 149247, 149248, 149249, 149252, 149251, 149250, 149253, 149254, 149255, 149265, 149257, 149256, 149258, 149259, 149261, 149260, 149262, 149263, 149264, 149266, 149267, 149268, 149269, 149270, 149272, 149271, 149275, 149274, 149273, 149280, 149276, 149277, 149278, 149279, 149281, 149282, 149283, 149284, 149285, 149286, 149287, 149289, 149288, 149290, 149291, 149292, 149293, 149301, 149302, 149294, 149295, 149296, 149297, 149298, 149299, 149300, 149303, 149304, 149305, 149306, 149307, 149308, 149309, 149310, 149312, 149311, 149314, 149313, 149315, 149316, 149317, 149318, 149319, 149320, 149322, 149321, 149323, 149324, 149327, 149325, 149326, 149328, 149329, 149333, 149330, 149332, 149331, 149334, 149335, 149336, 149337, 149340, 149339, 149338, 149341, 149342, 149343, 149344, 149346, 149345, 149347, 149348, 149349, 149350, 149351, 149352, 149353, 149355, 149354, 149356, 149357, 149358, 149359, 149361, 149360, 149362, 149363, 149364, 149366, 149365, 149367, 149368, 149369, 149370, 149371, 149373, 149372, 149374, 149376, 149377, 149375, 149378, 149379, 149380, 149382, 149381, 149383, 149384, 149385, 149387, 149386, 149388] # this is just 1392 sources which are retrieved from dotastro's projid=122
sciclass_lookup = {'classid_shortname': {0: '_varstar_',
                       1: 'GCVS',
                       2: 'Eruptive',
                       3: 'FU',
                       4: 'GCAS',
                       5: 'I',
                       6: 'IA',
                       7: 'IB',
                       8: 'IN',
                       9: 'INA',
                       10: 'INB',
                       11: 'INT',
                       12: 'IN(YY)',
                       13: 'IS',
                       14: 'ISA',
                       16: 'ISB',
                       17: 'RCB',
                       18: 'RS',
                       19: 'SDOR',
                       20: 'UV',
                       21: 'UVN',
                       22: 'WR',
                       23: 'Pulsating',
                       24: 'ACYG',
                       25: 'BCEP',
                       26: 'BCEPS',
                       27: 'CEP',
                       28: 'CEP(B)',
                       29: 'CW',
                       30: 'CWA',
                       31: 'CWB',
                       32: 'DCEP',
                       33: 'DCEPS',
                       34: 'DSCT',
                       35: 'DSCTC',
                       36: 'L',
                       37: 'LB',
                       38: 'LC',
                       39: 'M',
                       40: 'PVTEL',
                       41: 'RR',
                       42: 'RR(B)',
                       43: 'RRAB',
                       44: 'RRC',
                       45: 'RV',
                       46: 'RVA',
                       47: 'RVB',
                       48: 'SR',
                       49: 'SRA',
                       50: 'SRB',
                       51: 'SRC',
                       52: 'SRD',
                       53: 'SXPHE',
                       54: 'ZZ',
                       55: 'ZZA',
                       56: 'ZZB',
                       57: 'Rotating',
                       58: 'ACV',
                       59: 'ACVO',
                       60: 'BY',
                       61: 'ELL',
                       62: 'FKCOM',
                       63: 'PSR',
                       64: 'SXARI',
                       65: 'Cataclysmic',
                       66: 'N',
                       67: 'NA',
                       68: 'NB',
                       69: 'NC',
                       70: 'NL',
                       71: 'NR',
                       72: 'SN',
                       73: 'SNI',
                       74: 'SNII',
                       75: 'UG',
                       76: 'UGSS',
                       77: 'UGSU',
                       78: 'UGZ',
                       79: 'ZAND',
                       80: 'Eclipsing',
                       82: 'E',
                       83: 'EA',
                       84: 'EB',
                       85: 'EW',
                       86: 'GS',
                       87: 'PN',
                       88: 'RS',
                       89: 'WD',
                       90: 'WR(1)',
                       91: 'AR',
                       92: 'D',
                       93: 'DM',
                       94: 'DS',
                       95: 'DW',
                       96: 'K',
                       97: 'KE',
                       98: 'KW',
                       99: 'SD',
                       100: 'SNIa',
                       101: 'SNIb',
                       102: 'SNIc',
                       103: 'SNIIP',
                       104: 'SNIIN',
                       105: 'SNIIL',
                       106: 'SNIa-sc',
                       107: 'Nonstellar',
                       109: 'GalNuclei',
                       110: 'AGN',
                       111: 'TDE',
                       112: 'DrkMatterA',
                       113: 'GRB',
                       114: 'SHB',
                       115: 'LSB',
                       116: 'SGR',
                       117: 'X',
                       118: 'XB',
                       119: 'XF',
                       120: 'XI',
                       121: 'XJ',
                       122: 'XND',
                       123: 'XNG',
                       124: 'XP',
                       125: 'XPR',
                       126: 'XPRM',
                       127: 'XRM',
                       128: 'ZZO',
                       129: 'NEW',
                       130: 'AM',
                       131: 'R',
                       132: 'BE',
                       133: 'EP',
                       134: 'SRS',
                       135: 'GDOR',
                       136: 'RPHS',
                       137: 'LPB',
                       138: 'BLBOO',
                       139: 'BL-Lac',
                       140: 'RRcl',
                       141: 'RRe',
                       142: 'SNIa-pec',
                       143: 'SNIc-pec',
                       145: 'ML',
                       149: 'UXUma',
                       150: 'Polars',
                       151: 'DQ',
                       152: 'EWa',
                       153: 'EWs',
                       154: 'vs',
                       157: 'cv',
                       158: 'nov',
                       159: 'cn',
                       160: 'n-l',
                       161: 'sw',
                       162: 'vy',
                       163: 'ux',
                       164: 'amcvn',
                       165: 'p',
                       166: 'am',
                       167: 'dqh',
                       168: 'ug',
                       169: 'su',
                       170: 'er',
                       171: 'wz',
                       172: 'zc',
                       173: 'ssc',
                       174: 'rn',
                       175: 'sv',
                       176: 'grb',
                       177: 'lgrb',
                       178: 'sgrb',
                       179: 'srgrb',
                       180: 'sne',
                       181: 'cc',
                       182: 'tia',
                       183: 'tib',
                       184: 'tic',
                       185: 'tsnii',
                       186: 'pi',
                       187: 'tsni',
                       188: 'ev',
                       189: 'rscvn',
                       190: 'uv',
                       191: 'sdorad',
                       192: 'wr',
                       193: 'gc',
                       194: 'fuor',
                       195: 'ov',
                       196: 'rcb',
                       197: 'haebe',
                       198: 'be',
                       199: 'shs',
                       200: 'tt',
                       201: 'ttc',
                       202: 'ttw',
                       203: 'puls',
                       204: 'gd',
                       205: 'sx',
                       206: 'rr-lyr',
                       207: 'ac',
                       208: 'mira',
                       209: 'pwd',
                       211: 'ds',
                       212: 'pvt',
                       213: 'bc',
                       214: 'sreg',
                       215: 'rv',
                       216: 'piic',
                       217: 'c',
                       218: 'rr-ab',
                       219: 'rr-c',
                       220: 'rr-d',
                       221: 'rr-e',
                       222: 'rr-cl',
                       223: 'zz',
                       224: 'zzh',
                       225: 'zzhe',
                       226: 'zzheii',
                       227: 'gw',
                       228: 'sr-a',
                       229: 'sr-b',
                       230: 'sr-c',
                       231: 'sr-d',
                       232: 'rvc',
                       233: 'rvv',
                       234: 'bl',
                       235: 'wv',
                       236: 'ca',
                       237: 'cm',
                       238: 'dc',
                       239: 'sdc',
                       240: 'rot',
                       241: 'sxari',
                       242: 'aii',
                       243: 'fk',
                       244: 'plsr',
                       245: 'by',
                       246: 'ell',
                       247: 'msv',
                       248: 'b',
                       249: 'iii',
                       250: 'xrb',
                       251: 'bly',
                       252: 'wu',
                       253: 'alg',
                       254: 'psys',
                       255: 'SSO',
                       256: 'BLZ',
                       257: 'OVV',
                       258: 'dsm',
                       259: 'lamb',
                       260: 'xrbin',
                       261: 'lboo',
                       262: 'qso',
                       263: 'seyf',
                       265: 'fsrq',
                       266: 'iin',
                       267: 'hae',
                       268: 'tiapec',
                       269: 'tiasc',
                       270: 'iil',
                       271: 'iip',
                       272: 'iib',
                       273: 'ticpec',
                       274: 'maser',
                       275: 'moving',
                       276: 'ast',
                       277: 'comet',
                       278: 'hpm',
                       279: 'eclipsing',
                       280: 'k',
                       281: 'd',
                       282: 'sd',
                       283: 'unclass',
                       284: 'pvsg',
                       285: 'cp',
                       286: 'spb',
                       287: 'sdbv',
                       1000000: 'Chemically Peculiar Stars'},
 'longname_shortname': {'AM Canum Venaticorum': 'amcvn',
                        'AM Her': 'AM',
                        'AM Herculis (True Polar)': 'am',
                        'Active Galactic Nuclei': 'AGN',
                        'Algol (Beta Persei)': 'alg',
                        'Alpha Cygni': 'ac',
                        'Alpha2 CVn - Rapily Oscillating': 'ACVO',
                        'Alpha2 Canum Venaticorum': 'aii',
                        'Anomalous Cepheids': 'BLBOO',
                        'Anomolous Cepheid': 'ca',
                        'Asteroid': 'ast',
                        'BL Lac': 'BL-Lac',
                        'BY Draconis': 'by',
                        'Be Star': 'be',
                        'Be star': 'BE',
                        'Beta Cephei': 'bc',
                        'Beta Cephei - Short Period': 'BCEPS',
                        'Beta Lyrae': 'bly',
                        'Binary': 'b',
                        'Blazar': 'BLZ',
                        'Cataclysmic (Explosive and Novalike) Variable Stars': 'Cataclysmic',
                        'Cataclysmic Variable': 'cv',
                        'Cepheid Variable': 'c',
                        'Cepheids': 'CEP',
                        'Cepheids - Multiple Modes': 'CEP(B)',
                        'Chemically Peculiar Stars': 'CP',
                        'Classical Cepheid': 'dc',
                        'Classical Novae': 'cn',
                        'Classical T Tauri': 'ttc',
                        'Close Binary Eclipsing Systems': 'eclipsing',
                        'Close Binary with Reflection': 'R',
                        'Comet': 'comet',
                        'Contact Systems': 'k',
                        'Contact Systems - Early (O-A)': 'KE',
                        'Contact Systems - W Ursa Majoris': 'KW',
                        'Core Collapse Supernovae': 'cc',
                        'DQ Herculis (Intermdiate Polars)': 'dqh',
                        'DQ Herculis Variable (Intermediate Polars)': 'DQ',
                        'Dark Matter Anniliation Event': 'DrkMatterA',
                        'Delta Cep': 'DCEP',
                        'Delta Cep - Symmetrical': 'DCEPS',
                        'Delta Scuti': 'ds',
                        'Delta Scuti - Low Amplitude': 'DSCTC',
                        'Delta Scuti - Multiple Modes': 'dsm',
                        'Detached': 'd',
                        'Detached - AR Lacertae': 'AR',
                        'Detached - Main Sequence': 'DM',
                        'Detached - With Subgiant': 'DS',
                        'ER Ursae Majoris': 'er',
                        'Eclipsed by Planets': 'EP',
                        'Eclipsing Binary Systems': 'E',
                        'Ellipsoidal': 'ell',
                        'Eruptive Variable': 'ev',
                        'Eruptive Variable Stars': 'Eruptive',
                        'Eruptive Wolf-Rayet': 'WR',
                        'FK Comae Berenices': 'fk',
                        'FU Orionis': 'fuor',
                        'Fast Novae': 'NA',
                        'Flaring Orion Variables': 'UVN',
                        'Flat Spectrum Radio Quasar': 'fsrq',
                        'Fluctuating X-Ray Systems': 'XF',
                        'GW Virginis': 'gw',
                        'Galaxy Nuclei ': 'GalNuclei',
                        'Gamma Cas': 'GCAS',
                        'Gamma Cassiopeiae': 'gc',
                        'Gamma Doradus': 'gd',
                        'Gamma Ray Burst': 'grb',
                        'Gamma-ray Bursts': 'GRB',
                        'Herbig AE': 'hae',
                        'Herbig AE/BE Star': 'haebe',
                        'High Proper Motion Star': 'hpm',
                        'Irregular': 'I',
                        'Irregular Early O-A': 'IA',
                        'Irregular Intermediate F-M': 'IB',
                        'Irregular Supergiants': 'LC',
                        'Lambda Bootis Variable': 'lboo',
                        'Lambda Eridani': 'lamb',
                        'Long GRB': 'lgrb',
                        'Long Gamma-ray Burst': 'LSB',
                        'Long Period (W Virginis)': 'wv',
                        'Long Period B': 'LPB',
                        'Maser': 'maser',
                        'Microlensing Event': 'ML',
                        'Mira': 'mira',
                        'Moving Source': 'moving',
                        'Multiple Mode Cepheid': 'cm',
                        'Multiple Star Variables': 'msv',
                        'New Variability Types': 'NEW',
                        'Novae': 'nov',
                        'Novalike': 'n-l',
                        'Novalike Variables': 'NL',
                        'Optically Variable Pulsars': 'PSR',
                        'Optically Violent Variable Quasar (OVV)': 'OVV',
                        'Orion': 'IN',
                        'Orion Early Types (B-A or Ae)': 'INA',
                        'Orion Intermediate Types (F-M or Fe-Me)': 'INB',
                        'Orion T Tauri': 'INT',
                        'Orion Variable': 'ov',
                        'Orion with Absorption': 'IN(YY)',
                        'PV Telescopii': 'pvt',
                        'Pair Instability Supernovae': 'pi',
                        'Peculiar Type Ia SN': 'tiapec',
                        'Peculiar Type Ia Supernovae': 'SNIa-pec',
                        'Peculiar Type Ic Supernovae': 'SNIc-pec',
                        'Periodically variable supergiants': 'pvsg',
                        'Polars': 'p',
                        'Population II Cepheid': 'piic',
                        'Pulsar': 'plsr',
                        'Pulsating Variable': 'puls',
                        'Pulsating Variable Stars': 'Pulsating',
                        'Pulsating White Dwarf': 'pwd',
                        'Pulsating subdwarf B-stars': 'sdbv',
                        'QSO': 'qso',
                        'R Coronae Borealis': 'rcb',
                        'RR Lyrae': 'rr-lyr',
                        'RR Lyrae - Asymmetric': 'RRAB',
                        'RR Lyrae - Dual Mode': 'RR(B)',
                        'RR Lyrae - Near Symmetric': 'RRC',
                        'RR Lyrae -- Closely Spaced Modes': 'RRcl',
                        'RR Lyrae -- Second Overtone Pulsations': 'RRe',
                        'RR Lyrae, Closely Spaced Modes': 'rr-cl',
                        'RR Lyrae, Double Mode': 'rr-d',
                        'RR Lyrae, First Overtone': 'rr-c',
                        'RR Lyrae, Fundamental Mode': 'rr-ab',
                        'RR Lyrae, Second Overtone': 'rr-e',
                        'RS Canum Venaticorum': 'rscvn',
                        'RV Tauri': 'rv',
                        'RV Tauri - Constant Mean Magnitude': 'RVA',
                        'RV Tauri - Variable Mean Magnitude': 'RVB',
                        'RV Tauri, Constant Mean Brightness': 'rvc',
                        'RV Tauri, Variable Mean Brightness': 'rvv',
                        'Rapid Irregular': 'IS',
                        'Rapid Irregular Early Types (B-A or Ae)': 'ISA',
                        'Rapid Irregular Intermediate to Late (F-M and Fe-Me)': 'ISB',
                        'Recurrent Novae': 'rn',
                        'Rotating Ellipsoidal': 'ELL',
                        'Rotating Variable': 'rot',
                        'Rotating Variable Stars': 'Rotating',
                        'S Doradus': 'sdorad',
                        'SRa (Z Aquarii)': 'sr-a',
                        'SRb': 'sr-b',
                        'SRc': 'sr-c',
                        'SRd': 'sr-d',
                        'SS Cygni': 'ssc',
                        'SU Ursae Majoris': 'su',
                        'SW Sextantis': 'sw',
                        'SX Arietis': 'sxari',
                        'SX Phoenicis': 'sx',
                        'SX Phoenicis  - Pulsating Subdwarfs': 'SXPHE',
                        'Semidetached': 'sd',
                        'Semiregular': 'SR',
                        'Semiregular - Persistent Periodicity': 'SRA',
                        'Semiregular - Poorly Defined Periodicity': 'SRB',
                        'Semiregular F, G, or K': 'SRD',
                        'Semiregular Pulsating Red Giants': 'SRS',
                        'Semiregular Pulsating Variable': 'sreg',
                        'Semiregular Supergiants': 'SRC',
                        'Seyfert': 'seyf',
                        'Shell Star': 'shs',
                        'Short GRB': 'sgrb',
                        'Short Gamma-ray Burst': 'SHB',
                        'Short period (BL Herculis)': 'bl',
                        'Slow Irregular': 'L',
                        'Slow Irregular - Late Spectral Type (K, M, C, S)': 'LB',
                        'Slow Novae': 'NB',
                        'Slowly Pulsating B-stars': 'spb',
                        'Soft Gamma Ray Repeater': 'srgrb',
                        'Soft Gamma-ray Repeater': 'SGR',
                        'Solar System Object': 'SSO',
                        'Super-chandra Ia supernova': 'SNIa-sc',
                        'Super-chandra Type Ia SN': 'tiasc',
                        'Supernovae': 'sne',
                        'Symbiotic Variable': 'sv',
                        'Symbiotic Variables': 'ZAND',
                        'Symmetrical': 'sdc',
                        'Systems with Planetary Nebulae': 'PN',
                        'Systems with Planets': 'psys',
                        'Systems with Supergiant(s)': 'GS',
                        'Systems with White Dwarfs': 'WD',
                        'Systems with Wolf-Rayet Stars': 'WR(1)',
                        'T Tauri': 'tt',
                        'Three or More Stars': 'iii',
                        'Tidal Disruption Event': 'TDE',
                        'Type I Supernovae': 'tsni',
                        'Type II L supernova': 'iil',
                        'Type II N Supernova': 'iin',
                        'Type II P supernova': 'iip',
                        'Type II Supernovae': 'tsnii',
                        'Type II b Supernova': 'iib',
                        'Type II-L': 'SNIIL',
                        'Type IIN': 'SNIIN',
                        'Type IIP': 'SNIIP',
                        'Type Ia': 'SNIa',
                        'Type Ia Supernovae': 'tia',
                        'Type Ib': 'SNIb',
                        'Type Ib Supernovae': 'tib',
                        'Type Ic': 'SNIc',
                        'Type Ic Supernovae': 'tic',
                        'Type Ic peculiar': 'ticpec',
                        'U Geminorum': 'ug',
                        'UV Ceti': 'UV',
                        'UV Ceti Variable': 'uv',
                        'UX Uma': 'UXUma',
                        'UX Ursae Majoris': 'ux',
                        'Unclassified': 'unclass',
                        'VY Scl': 'vy',
                        'Variable Sources (Non-stellar)': 'Nonstellar',
                        'Variable Stars': 'GCVS',
                        'Variable Stars [Alt]': 'vs',
                        'Very Rapidly Pulsating Hot (subdwarf B)': 'RPHS',
                        'Very Slow Novae': 'NC',
                        'W Ursa Majoris': 'DW',
                        'W Ursae Majoris': 'wu',
                        'W Ursae Majoris -  W UMa': 'EW',
                        'W Ursae Majoris- a': 'EWa',
                        'W Ursae Majoris- s': 'EWs',
                        'W Virginis': 'CW',
                        'W Virginis - Long Period': 'CWA',
                        'W Virigins - Short Period': 'CWB',
                        'WZ Sagittae': 'wz',
                        'Weak-lined T Tauri': 'ttw',
                        'Wolf-Rayet': 'wr',
                        'X Ray Binary': 'xrbin',
                        'X Ray Burster': 'xrb',
                        'X-Ray Binaries with Jets': 'XJ',
                        'X-Ray Bursters': 'XB',
                        'X-Ray Pulsar': 'XP',
                        'X-Ray Pulsar with late-type dwarf': 'XPRM',
                        'X-Ray Pulsar, with Reflection': 'XPR',
                        'X-Ray Sources, Optically Variable': 'X',
                        'X-Ray with late-type dwarf, un-observed pulsar': 'XRM',
                        'X-Ray, Novalike': 'XND',
                        'X-Ray, Novalike with Early Type supergiant or giant': 'XNG',
                        'X-ray Irregulars': 'XI',
                        'Z Camelopardalis': 'zc',
                        'ZZ Ceti': 'zz',
                        'ZZ Ceti - Only H Absorption': 'ZZA',
                        'ZZ Ceti - Only He Absorption': 'ZZB',
                        'ZZ Ceti showing HeII': 'ZZO',
                        'ZZ Ceti, H Absorption Only': 'zzh',
                        'ZZ Ceti, He Absorption Only': 'zzhe',
                        'ZZ Ceti, With He-II': 'zzheii',
                        '_varstar_': '_varstar_'},
 'shortname_isactive': {'ACVO': 'Yes',
                        'AGN': 'Yes',
                        'AR': 'Yes',
                        'BCEPS': 'Yes',
                        'BL-Lac': 'Yes',
                        'BLZ': 'Yes',
                        'CP': 'No',
                        'CW': 'Yes',
                        'CWA': 'Yes',
                        'CWB': 'Yes',
                        'D': 'Yes',
                        'DCEP': 'Yes',
                        'DCEPS': 'Yes',
                        'DM': 'Yes',
                        'DS': 'Yes',
                        'DSCTC': 'Yes',
                        'DrkMatterA': 'Yes',
                        'E': 'Yes',
                        'ELL': 'Yes',
                        'EP': 'Yes',
                        'EWa': 'Yes',
                        'EWs': 'Yes',
                        'Eclipsing': 'Yes',
                        'GS': 'Yes',
                        'GalNuclei': 'Yes',
                        'I': 'Yes',
                        'IA': 'Yes',
                        'IB': 'Yes',
                        'IN(YY)': 'Yes',
                        'INA': 'Yes',
                        'INB': 'Yes',
                        'IS': 'Yes',
                        'ISA': 'Yes',
                        'ISB': 'Yes',
                        'K': 'Yes',
                        'KE': 'Yes',
                        'KW': 'Yes',
                        'L': 'Yes',
                        'LB': 'Yes',
                        'LC': 'Yes',
                        'LPB': 'Yes',
                        'ML': 'Yes',
                        'NA': 'Yes',
                        'NB': 'Yes',
                        'NC': 'Yes',
                        'NEW': 'Yes',
                        'Nonstellar': 'Yes',
                        'OVV': 'Yes',
                        'PN': 'Yes',
                        'PSR': 'Yes',
                        'R': 'Yes',
                        'RPHS': 'Yes',
                        'RR(B)': 'Yes',
                        'RRAB': 'Yes',
                        'RRC': 'Yes',
                        'SD': 'Yes',
                        'SNIc-pec': 'Yes',
                        'SRA': 'Yes',
                        'SRB': 'Yes',
                        'SRC': 'Yes',
                        'SRD': 'Yes',
                        'SRS': 'Yes',
                        'SSO': 'Yes',
                        'TDE': 'Yes',
                        'UVN': 'Yes',
                        'WD': 'Yes',
                        'WR(1)': 'Yes',
                        'X': 'Yes',
                        'XF': 'Yes',
                        'XI': 'Yes',
                        'XJ': 'Yes',
                        'XND': 'Yes',
                        'XNG': 'Yes',
                        'XP': 'Yes',
                        'XPR': 'Yes',
                        'XPRM': 'Yes',
                        'XRM': 'Yes',
                        '_varstar_': 'No',
                        'ac': 'Yes',
                        'aii': 'Yes',
                        'alg': 'Yes',
                        'am': 'Yes',
                        'amcvn': 'Yes',
                        'ast': 'Yes',
                        'b': 'Yes',
                        'bc': 'Yes',
                        'be': 'Yes',
                        'bl': 'Yes',
                        'bly': 'Yes',
                        'by': 'Yes',
                        'c': 'Yes',
                        'ca': 'Yes',
                        'cc': 'Yes',
                        'cm': 'Yes',
                        'cn': 'Yes',
                        'comet': 'Yes',
                        'cp': 'Yes',
                        'cv': 'Yes',
                        'd': 'Yes',
                        'dc': 'Yes',
                        'dqh': 'Yes',
                        'ds': 'Yes',
                        'dsm': 'Yes',
                        'eclipsing': 'Yes',
                        'ell': 'Yes',
                        'er': 'Yes',
                        'ev': 'Yes',
                        'fk': 'Yes',
                        'fsrq': 'Yes',
                        'fuor': 'Yes',
                        'gc': 'Yes',
                        'gd': 'Yes',
                        'grb': 'Yes',
                        'gw': 'Yes',
                        'hae': 'Yes',
                        'haebe': 'Yes',
                        'hpm': 'Yes',
                        'iib': 'Yes',
                        'iii': 'Yes',
                        'iil': 'Yes',
                        'iin': 'Yes',
                        'iip': 'Yes',
                        'k': 'Yes',
                        'lamb': 'Yes',
                        'lboo': 'Yes',
                        'lgrb': 'Yes',
                        'maser': 'Yes',
                        'mira': 'Yes',
                        'moving': 'Yes',
                        'msv': 'Yes',
                        'n-l': 'Yes',
                        'nov': 'Yes',
                        'ov': 'Yes',
                        'p': 'Yes',
                        'pi': 'Yes',
                        'piic': 'Yes',
                        'plsr': 'Yes',
                        'psys': 'Yes',
                        'puls': 'Yes',
                        'pvsg': 'Yes',
                        'pvt': 'Yes',
                        'pwd': 'Yes',
                        'qso': 'Yes',
                        'rcb': 'Yes',
                        'rn': 'Yes',
                        'rot': 'Yes',
                        'rr-ab': 'Yes',
                        'rr-c': 'Yes',
                        'rr-cl': 'Yes',
                        'rr-d': 'Yes',
                        'rr-e': 'Yes',
                        'rr-lyr': 'Yes',
                        'rscvn': 'Yes',
                        'rv': 'Yes',
                        'rvc': 'Yes',
                        'rvv': 'Yes',
                        'sd': 'Yes',
                        'sdbv': 'Yes',
                        'sdc': 'Yes',
                        'sdorad': 'Yes',
                        'seyf': 'Yes',
                        'sgrb': 'Yes',
                        'shs': 'Yes',
                        'sne': 'Yes',
                        'spb': 'Yes',
                        'sr-a': 'Yes',
                        'sr-b': 'Yes',
                        'sr-c': 'Yes',
                        'sr-d': 'Yes',
                        'sreg': 'Yes',
                        'srgrb': 'Yes',
                        'ssc': 'Yes',
                        'su': 'Yes',
                        'sv': 'Yes',
                        'sw': 'Yes',
                        'sx': 'Yes',
                        'sxari': 'Yes',
                        'tia': 'Yes',
                        'tiapec': 'Yes',
                        'tiasc': 'Yes',
                        'tib': 'Yes',
                        'tic': 'Yes',
                        'ticpec': 'Yes',
                        'tsni': 'Yes',
                        'tsnii': 'Yes',
                        'tt': 'Yes',
                        'ttc': 'Yes',
                        'ttw': 'Yes',
                        'ug': 'Yes',
                        'unclass': 'Yes',
                        'uv': 'Yes',
                        'ux': 'Yes',
                        'vs': 'Yes',
                        'vy': 'Yes',
                        'wr': 'Yes',
                        'wu': 'Yes',
                        'wv': 'Yes',
                        'wz': 'Yes',
                        'xrb': 'Yes',
                        'xrbin': 'Yes',
                        'zc': 'Yes',
                        'zz': 'Yes',
                        'zzh': 'Yes',
                        'zzhe': 'Yes',
                        'zzheii': 'Yes'},
 'shortname_ispublic': {'ACVO': 'No',
                        'AGN': 'Yes',
                        'AR': 'No',
                        'BCEPS': 'No',
                        'BL-Lac': 'Yes',
                        'BLZ': 'Yes',
                        'CP': 'No',
                        'CW': 'No',
                        'CWA': 'No',
                        'CWB': 'No',
                        'D': 'No',
                        'DCEP': 'No',
                        'DCEPS': 'No',
                        'DM': 'No',
                        'DS': 'No',
                        'DSCTC': 'No',
                        'DrkMatterA': 'Yes',
                        'E': 'No',
                        'ELL': 'No',
                        'EP': 'No',
                        'EWa': 'No',
                        'EWs': 'No',
                        'Eclipsing': 'No',
                        'GS': 'No',
                        'GalNuclei': 'Yes',
                        'I': 'No',
                        'IA': 'No',
                        'IB': 'No',
                        'IN(YY)': 'No',
                        'INA': 'No',
                        'INB': 'No',
                        'IS': 'No',
                        'ISA': 'No',
                        'ISB': 'No',
                        'K': 'No',
                        'KE': 'No',
                        'KW': 'No',
                        'L': 'No',
                        'LB': 'No',
                        'LC': 'No',
                        'LPB': 'No',
                        'ML': 'Yes',
                        'NA': 'No',
                        'NB': 'No',
                        'NC': 'No',
                        'NEW': 'No',
                        'Nonstellar': 'Yes',
                        'OVV': 'Yes',
                        'PN': 'No',
                        'PSR': 'No',
                        'R': 'No',
                        'RPHS': 'No',
                        'RR(B)': 'No',
                        'RRAB': 'No',
                        'RRC': 'No',
                        'SD': 'No',
                        'SNIc-pec': 'No',
                        'SRA': 'No',
                        'SRB': 'No',
                        'SRC': 'No',
                        'SRD': 'No',
                        'SRS': 'No',
                        'SSO': 'Yes',
                        'TDE': 'Yes',
                        'UVN': 'No',
                        'WD': 'No',
                        'WR(1)': 'No',
                        'X': 'No',
                        'XF': 'No',
                        'XI': 'No',
                        'XJ': 'No',
                        'XND': 'No',
                        'XNG': 'No',
                        'XP': 'No',
                        'XPR': 'No',
                        'XPRM': 'No',
                        'XRM': 'No',
                        '_varstar_': 'No',
                        'ac': 'Yes',
                        'aii': 'Yes',
                        'alg': 'Yes',
                        'am': 'Yes',
                        'amcvn': 'Yes',
                        'ast': 'Yes',
                        'b': 'Yes',
                        'bc': 'Yes',
                        'be': 'Yes',
                        'bl': 'Yes',
                        'bly': 'Yes',
                        'by': 'Yes',
                        'c': 'Yes',
                        'ca': 'Yes',
                        'cc': 'Yes',
                        'cm': 'Yes',
                        'cn': 'Yes',
                        'comet': 'Yes',
                        'cp': 'Yes',
                        'cv': 'Yes',
                        'd': 'Yes',
                        'dc': 'Yes',
                        'dqh': 'Yes',
                        'ds': 'Yes',
                        'dsm': 'Yes',
                        'eclipsing': 'No',
                        'ell': 'Yes',
                        'er': 'Yes',
                        'ev': 'Yes',
                        'fk': 'Yes',
                        'fsrq': 'Yes',
                        'fuor': 'Yes',
                        'gc': 'Yes',
                        'gd': 'Yes',
                        'grb': 'Yes',
                        'gw': 'Yes',
                        'hae': 'Yes',
                        'haebe': 'Yes',
                        'hpm': 'Yes',
                        'iib': 'Yes',
                        'iii': 'Yes',
                        'iil': 'Yes',
                        'iin': 'Yes',
                        'iip': 'Yes',
                        'k': 'No',
                        'lamb': 'Yes',
                        'lboo': 'Yes',
                        'lgrb': 'Yes',
                        'maser': 'Yes',
                        'mira': 'Yes',
                        'moving': 'Yes',
                        'msv': 'Yes',
                        'n-l': 'Yes',
                        'nov': 'Yes',
                        'ov': 'Yes',
                        'p': 'Yes',
                        'pi': 'Yes',
                        'piic': 'Yes',
                        'plsr': 'Yes',
                        'psys': 'Yes',
                        'puls': 'Yes',
                        'pvsg': 'Yes',
                        'pvt': 'Yes',
                        'pwd': 'Yes',
                        'qso': 'Yes',
                        'rcb': 'Yes',
                        'rn': 'Yes',
                        'rot': 'Yes',
                        'rr-ab': 'Yes',
                        'rr-c': 'Yes',
                        'rr-cl': 'Yes',
                        'rr-d': 'Yes',
                        'rr-e': 'Yes',
                        'rr-lyr': 'Yes',
                        'rscvn': 'Yes',
                        'rv': 'Yes',
                        'rvc': 'Yes',
                        'rvv': 'Yes',
                        'sd': 'No',
                        'sdbv': 'Yes',
                        'sdc': 'Yes',
                        'sdorad': 'Yes',
                        'seyf': 'Yes',
                        'sgrb': 'Yes',
                        'shs': 'Yes',
                        'sne': 'Yes',
                        'spb': 'Yes',
                        'sr-a': 'Yes',
                        'sr-b': 'Yes',
                        'sr-c': 'Yes',
                        'sr-d': 'Yes',
                        'sreg': 'Yes',
                        'srgrb': 'Yes',
                        'ssc': 'Yes',
                        'su': 'Yes',
                        'sv': 'Yes',
                        'sw': 'Yes',
                        'sx': 'Yes',
                        'sxari': 'Yes',
                        'tia': 'Yes',
                        'tiapec': 'Yes',
                        'tiasc': 'Yes',
                        'tib': 'Yes',
                        'tic': 'Yes',
                        'ticpec': 'Yes',
                        'tsni': 'Yes',
                        'tsnii': 'Yes',
                        'tt': 'Yes',
                        'ttc': 'Yes',
                        'ttw': 'Yes',
                        'ug': 'Yes',
                        'unclass': 'Yes',
                        'uv': 'Yes',
                        'ux': 'Yes',
                        'vs': 'Yes',
                        'vy': 'Yes',
                        'wr': 'Yes',
                        'wu': 'Yes',
                        'wv': 'Yes',
                        'wz': 'Yes',
                        'xrb': 'Yes',
                        'xrbin': 'Yes',
                        'zc': 'Yes',
                        'zz': 'Yes',
                        'zzh': 'Yes',
                        'zzhe': 'Yes',
                        'zzheii': 'Yes'},
 'shortname_longname': {'ACVO': 'Alpha2 CVn - Rapily Oscillating',
                        'AGN': 'Active Galactic Nuclei',
                        'AR': 'Detached - AR Lacertae',
                        'BCEPS': 'Beta Cephei - Short Period',
                        'BL-Lac': 'BL Lac',
                        'BLZ': 'Blazar',
                        'CP': 'Chemically Peculiar Stars',
                        'CW': 'W Virginis',
                        'CWA': 'W Virginis - Long Period',
                        'CWB': 'W Virigins - Short Period',
                        'D': 'Detached',
                        'DCEP': 'Delta Cep',
                        'DCEPS': 'Delta Cep - Symmetrical',
                        'DM': 'Detached - Main Sequence',
                        'DS': 'Detached - With Subgiant',
                        'DSCTC': 'Delta Scuti - Low Amplitude',
                        'DrkMatterA': 'Dark Matter Anniliation Event',
                        'E': 'Eclipsing Binary Systems',
                        'ELL': 'Rotating Ellipsoidal',
                        'EP': 'Eclipsed by Planets',
                        'EWa': 'W Ursae Majoris- a',
                        'EWs': 'W Ursae Majoris- s',
                        'Eclipsing': 'Close Binary Eclipsing Systems',
                        'GS': 'Systems with Supergiant(s)',
                        'GalNuclei': 'Galaxy Nuclei ',
                        'I': 'Irregular',
                        'IA': 'Irregular Early O-A',
                        'IB': 'Irregular Intermediate F-M',
                        'IN(YY)': 'Orion with Absorption',
                        'INA': 'Orion Early Types (B-A or Ae)',
                        'INB': 'Orion Intermediate Types (F-M or Fe-Me)',
                        'IS': 'Rapid Irregular',
                        'ISA': 'Rapid Irregular Early Types (B-A or Ae)',
                        'ISB': 'Rapid Irregular Intermediate to Late (F-M and Fe-Me)',
                        'K': 'Contact Systems',
                        'KE': 'Contact Systems - Early (O-A)',
                        'KW': 'Contact Systems - W Ursa Majoris',
                        'L': 'Slow Irregular',
                        'LB': 'Slow Irregular - Late Spectral Type (K, M, C, S)',
                        'LC': 'Irregular Supergiants',
                        'LPB': 'Long Period B',
                        'ML': 'Microlensing Event',
                        'NA': 'Fast Novae',
                        'NB': 'Slow Novae',
                        'NC': 'Very Slow Novae',
                        'NEW': 'New Variability Types',
                        'Nonstellar': 'Variable Sources (Non-stellar)',
                        'OVV': 'Optically Violent Variable Quasar (OVV)',
                        'PN': 'Systems with Planetary Nebulae',
                        'PSR': 'Optically Variable Pulsars',
                        'R': 'Close Binary with Reflection',
                        'RPHS': 'Very Rapidly Pulsating Hot (subdwarf B)',
                        'RR(B)': 'RR Lyrae - Dual Mode',
                        'RRAB': 'RR Lyrae - Asymmetric',
                        'RRC': 'RR Lyrae - Near Symmetric',
                        'SD': 'Semidetached',
                        'SNIc-pec': 'Peculiar Type Ic Supernovae',
                        'SRA': 'Semiregular - Persistent Periodicity',
                        'SRB': 'Semiregular - Poorly Defined Periodicity',
                        'SRC': 'Semiregular Supergiants',
                        'SRD': 'Semiregular F, G, or K',
                        'SRS': 'Semiregular Pulsating Red Giants',
                        'SSO': 'Solar System Object',
                        'TDE': 'Tidal Disruption Event',
                        'UVN': 'Flaring Orion Variables',
                        'WD': 'Systems with White Dwarfs',
                        'WR(1)': 'Systems with Wolf-Rayet Stars',
                        'X': 'X-Ray Sources, Optically Variable',
                        'XF': 'Fluctuating X-Ray Systems',
                        'XI': 'X-ray Irregulars',
                        'XJ': 'X-Ray Binaries with Jets',
                        'XND': 'X-Ray, Novalike',
                        'XNG': 'X-Ray, Novalike with Early Type supergiant or giant',
                        'XP': 'X-Ray Pulsar',
                        'XPR': 'X-Ray Pulsar, with Reflection',
                        'XPRM': 'X-Ray Pulsar with late-type dwarf',
                        'XRM': 'X-Ray with late-type dwarf, un-observed pulsar',
                        '_varstar_': '_varstar_',
                        'ac': 'Alpha Cygni',
                        'aii': 'Alpha2 Canum Venaticorum',
                        'alg': 'Algol (Beta Persei)',
                        'am': 'AM Herculis (True Polar)',
                        'amcvn': 'AM Canum Venaticorum',
                        'ast': 'Asteroid',
                        'b': 'Binary',
                        'bc': 'Beta Cephei',
                        'be': 'Be Star',
                        'bl': 'Short period (BL Herculis)',
                        'bly': 'Beta Lyrae',
                        'by': 'BY Draconis',
                        'c': 'Cepheid Variable',
                        'ca': 'Anomolous Cepheid',
                        'cc': 'Core Collapse Supernovae',
                        'cm': 'Multiple Mode Cepheid',
                        'cn': 'Classical Novae',
                        'comet': 'Comet',
                        'cp': 'Chemically Peculiar Stars',
                        'cv': 'Cataclysmic Variable',
                        'd': 'Detached',
                        'dc': 'Classical Cepheid',
                        'dqh': 'DQ Herculis (Intermdiate Polars)',
                        'ds': 'Delta Scuti',
                        'dsm': 'Delta Scuti - Multiple Modes',
                        'eclipsing': 'Close Binary Eclipsing Systems',
                        'ell': 'Ellipsoidal',
                        'er': 'ER Ursae Majoris',
                        'ev': 'Eruptive Variable',
                        'fk': 'FK Comae Berenices',
                        'fsrq': 'Flat Spectrum Radio Quasar',
                        'fuor': 'FU Orionis',
                        'gc': 'Gamma Cassiopeiae',
                        'gd': 'Gamma Doradus',
                        'grb': 'Gamma Ray Burst',
                        'gw': 'GW Virginis',
                        'hae': 'Herbig AE',
                        'haebe': 'Herbig AE/BE Star',
                        'hpm': 'High Proper Motion Star',
                        'iib': 'Type II b Supernova',
                        'iii': 'Three or More Stars',
                        'iil': 'Type II L supernova',
                        'iin': 'Type II N Supernova',
                        'iip': 'Type II P supernova',
                        'k': 'Contact Systems',
                        'lamb': 'Lambda Eridani',
                        'lboo': 'Lambda Bootis Variable',
                        'lgrb': 'Long GRB',
                        'maser': 'Maser',
                        'mira': 'Mira',
                        'moving': 'Moving Source',
                        'msv': 'Multiple Star Variables',
                        'n-l': 'Novalike',
                        'nov': 'Novae',
                        'ov': 'Orion Variable',
                        'p': 'Polars',
                        'pi': 'Pair Instability Supernovae',
                        'piic': 'Population II Cepheid',
                        'plsr': 'Pulsar',
                        'psys': 'Systems with Planets',
                        'puls': 'Pulsating Variable',
                        'pvsg': 'Periodically variable supergiants',
                        'pvt': 'PV Telescopii',
                        'pwd': 'Pulsating White Dwarf',
                        'qso': 'QSO',
                        'rcb': 'R Coronae Borealis',
                        'rn': 'Recurrent Novae',
                        'rot': 'Rotating Variable',
                        'rr-ab': 'RR Lyrae, Fundamental Mode',
                        'rr-c': 'RR Lyrae, First Overtone',
                        'rr-cl': 'RR Lyrae, Closely Spaced Modes',
                        'rr-d': 'RR Lyrae, Double Mode',
                        'rr-e': 'RR Lyrae, Second Overtone',
                        'rr-lyr': 'RR Lyrae',
                        'rscvn': 'RS Canum Venaticorum',
                        'rv': 'RV Tauri',
                        'rvc': 'RV Tauri, Constant Mean Brightness',
                        'rvv': 'RV Tauri, Variable Mean Brightness',
                        'sd': 'Semidetached',
                        'sdbv': 'Pulsating subdwarf B-stars',
                        'sdc': 'Symmetrical',
                        'sdorad': 'S Doradus',
                        'seyf': 'Seyfert',
                        'sgrb': 'Short GRB',
                        'shs': 'Shell Star',
                        'sne': 'Supernovae',
                        'spb': 'Slowly Pulsating B-stars',
                        'sr-a': 'SRa (Z Aquarii)',
                        'sr-b': 'SRb',
                        'sr-c': 'SRc',
                        'sr-d': 'SRd',
                        'sreg': 'Semiregular Pulsating Variable',
                        'srgrb': 'Soft Gamma Ray Repeater',
                        'ssc': 'SS Cygni',
                        'su': 'SU Ursae Majoris',
                        'sv': 'Symbiotic Variable',
                        'sw': 'SW Sextantis',
                        'sx': 'SX Phoenicis',
                        'sxari': 'SX Arietis',
                        'tia': 'Type Ia Supernovae',
                        'tiapec': 'Peculiar Type Ia SN',
                        'tiasc': 'Super-chandra Type Ia SN',
                        'tib': 'Type Ib Supernovae',
                        'tic': 'Type Ic Supernovae',
                        'ticpec': 'Type Ic peculiar',
                        'tsni': 'Type I Supernovae',
                        'tsnii': 'Type II Supernovae',
                        'tt': 'T Tauri',
                        'ttc': 'Classical T Tauri',
                        'ttw': 'Weak-lined T Tauri',
                        'ug': 'U Geminorum',
                        'unclass': 'Unclassified',
                        'uv': 'UV Ceti Variable',
                        'ux': 'UX Ursae Majoris',
                        'vs': 'Variable Stars [Alt]',
                        'vy': 'VY Scl',
                        'wr': 'Wolf-Rayet',
                        'wu': 'W Ursae Majoris',
                        'wv': 'Long Period (W Virginis)',
                        'wz': 'WZ Sagittae',
                        'xrb': 'X Ray Burster',
                        'xrbin': 'X Ray Binary',
                        'zc': 'Z Camelopardalis',
                        'zz': 'ZZ Ceti',
                        'zzh': 'ZZ Ceti, H Absorption Only',
                        'zzhe': 'ZZ Ceti, He Absorption Only',
                        'zzheii': 'ZZ Ceti, With He-II'},
 'shortname_nsrcs': {'ACV': 0,
                     'ACVO': 0,
                     'ACYG': 0,
                     'AGN': 57,
                     'AM': 0,
                     'AR': 0,
                     'BCEP': 0,
                     'BCEPS': 0,
                     'BE': 0,
                     'BL-Lac': 46,
                     'BLBOO': 0,
                     'BLZ': 24,
                     'BY': 0,
                     'CEP': 5,
                     'CEP(B)': 0,
                     'CP': 0,
                     'CW': 0,
                     'CWA': 0,
                     'CWB': 0,
                     'Cataclysmic': 0,
                     'Chemically Peculiar Stars': 0,
                     'D': 2,
                     'DCEP': 0,
                     'DCEPS': 0,
                     'DM': 0,
                     'DQ': 0,
                     'DS': 0,
                     'DSCT': 149,
                     'DSCTC': 0,
                     'DW': 0,
                     'DrkMatterA': 0,
                     'E': 3,
                     'EA': 260,
                     'EB': 67,
                     'ELL': 0,
                     'EP': 0,
                     'EW': 891,
                     'EWa': 0,
                     'EWs': 0,
                     'Eclipsing': 0,
                     'Eruptive': 0,
                     'FKCOM': 0,
                     'FU': 0,
                     'GCAS': 0,
                     'GCVS': 712,
                     'GDOR': 15,
                     'GRB': 0,
                     'GS': 0,
                     'GalNuclei': 0,
                     'I': 0,
                     'IA': 0,
                     'IB': 0,
                     'IN': 0,
                     'IN(YY)': 0,
                     'INA': 0,
                     'INB': 0,
                     'INT': 0,
                     'IS': 0,
                     'ISA': 0,
                     'ISB': 0,
                     'K': 0,
                     'KE': 0,
                     'KW': 0,
                     'L': 0,
                     'LB': 0,
                     'LC': 1,
                     'LPB': 1,
                     'LSB': 0,
                     'M': 11,
                     'ML': 658,
                     'N': 1,
                     'NA': 0,
                     'NB': 0,
                     'NC': 0,
                     'NEW': 0,
                     'NL': 3,
                     'NR': 0,
                     'Nonstellar': 0,
                     'OVV': 0,
                     'PN': 0,
                     'PSR': 0,
                     'PVTEL': 0,
                     'Polars': 0,
                     'Pulsating': 1,
                     'R': 0,
                     'RCB': 0,
                     'RPHS': 0,
                     'RR': 9,
                     'RR(B)': 0,
                     'RRAB': 31,
                     'RRC': 15,
                     'RRcl': 0,
                     'RRe': 0,
                     'RS': 0,
                     'RV': 0,
                     'RVA': 0,
                     'RVB': 0,
                     'Rotating': 0,
                     'SD': 0,
                     'SDOR': 0,
                     'SGR': 0,
                     'SHB': 0,
                     'SN': 0,
                     'SNI': 0,
                     'SNII': 0,
                     'SNIIL': 0,
                     'SNIIN': 1,
                     'SNIIP': 0,
                     'SNIa': 0,
                     'SNIa-pec': 0,
                     'SNIa-sc': 0,
                     'SNIb': 0,
                     'SNIc': 0,
                     'SNIc-pec': 0,
                     'SR': 0,
                     'SRA': 0,
                     'SRB': 0,
                     'SRC': 0,
                     'SRD': 0,
                     'SRS': 14,
                     'SSO': 0,
                     'SXARI': 0,
                     'SXPHE': 7,
                     'TDE': 0,
                     'UG': 3,
                     'UGSS': 0,
                     'UGSU': 0,
                     'UGZ': 1,
                     'UV': 0,
                     'UVN': 0,
                     'UXUma': 0,
                     'WD': 0,
                     'WR': 173,
                     'WR(1)': 0,
                     'X': 0,
                     'XB': 0,
                     'XF': 0,
                     'XI': 0,
                     'XJ': 0,
                     'XND': 0,
                     'XNG': 0,
                     'XP': 0,
                     'XPR': 0,
                     'XPRM': 0,
                     'XRM': 0,
                     'ZAND': 0,
                     'ZZ': 0,
                     'ZZA': 0,
                     'ZZB': 0,
                     'ZZO': 0,
                     '_varstar_': 0,
                     'ac': 0,
                     'aii': 81,
                     'alg': 732,
                     'am': 5,
                     'amcvn': 0,
                     'ast': 93,
                     'b': 53,
                     'bc': 84,
                     'be': 47,
                     'bl': 14,
                     'bly': 403,
                     'by': 0,
                     'c': 329,
                     'ca': 7,
                     'cc': 58,
                     'cm': 202,
                     'cn': 1,
                     'comet': 3,
                     'cp': 49,
                     'cv': 193,
                     'd': 2270,
                     'dc': 865,
                     'dqh': 5,
                     'ds': 845,
                     'dsm': 1,
                     'eclipsing': 2934,
                     'ell': 17,
                     'er': 0,
                     'ev': 0,
                     'fk': 1,
                     'fsrq': 3,
                     'fuor': 4,
                     'gc': 0,
                     'gd': 73,
                     'grb': 0,
                     'gw': 2,
                     'hae': 1,
                     'haebe': 28,
                     'hpm': 4,
                     'iib': 27,
                     'iii': 0,
                     'iil': 0,
                     'iin': 111,
                     'iip': 74,
                     'k': 2758,
                     'lamb': 1,
                     'lboo': 26,
                     'lgrb': 1,
                     'maser': 1,
                     'mira': 3048,
                     'moving': 0,
                     'msv': 0,
                     'n-l': 3,
                     'nov': 3,
                     'ov': 0,
                     'p': 0,
                     'pi': 0,
                     'piic': 41,
                     'plsr': 0,
                     'psys': 3,
                     'puls': 250,
                     'pvsg': 0,
                     'pvt': 0,
                     'pwd': 3,
                     'qso': 6307,
                     'rcb': 2,
                     'rn': 0,
                     'rot': 4,
                     'rr-ab': 1706,
                     'rr-c': 452,
                     'rr-cl': 13,
                     'rr-d': 168,
                     'rr-e': 0,
                     'rr-lyr': 16,
                     'rscvn': 1,
                     'rv': 11,
                     'rvc': 1,
                     'rvv': 0,
                     'sd': 879,
                     'sdbv': 0,
                     'sdc': 53,
                     'sdorad': 21,
                     'seyf': 0,
                     'sgrb': 0,
                     'shs': 0,
                     'sne': 619,
                     'spb': 0,
                     'sr-a': 2,
                     'sr-b': 2,
                     'sr-c': 2,
                     'sr-d': 3,
                     'sreg': 76,
                     'srgrb': 0,
                     'ssc': 3,
                     'su': 3,
                     'sv': 0,
                     'sw': 1,
                     'sx': 28,
                     'sxari': 0,
                     'tia': 2176,
                     'tiapec': 35,
                     'tiasc': 0,
                     'tib': 68,
                     'tic': 124,
                     'ticpec': 5,
                     'tsni': 48,
                     'tsnii': 749,
                     'tt': 32,
                     'ttc': 2,
                     'ttw': 0,
                     'ug': 3,
                     'unclass': 61200,
                     'uv': 0,
                     'ux': 2,
                     'vs': 774,
                     'vy': 1,
                     'wr': 219,
                     'wu': 1075,
                     'wv': 35,
                     'wz': 0,
                     'xrb': 0,
                     'xrbin': 14,
                     'zc': 3,
                     'zz': 0,
                     'zzh': 0,
                     'zzhe': 0,
                     'zzheii': 0},
 'shortname_parent_id': {'ACVO': 58,
                         'AGN': 109,
                         'AR': 80,
                         'BCEPS': 25,
                         'BL-Lac': 256,
                         'BLZ': 110,
                         'CP': 0,
                         'CW': 23,
                         'CWA': 29,
                         'CWB': 29,
                         'D': 80,
                         'DCEP': 23,
                         'DCEPS': 32,
                         'DM': 92,
                         'DS': 92,
                         'DSCTC': 34,
                         'DrkMatterA': 107,
                         'E': 80,
                         'ELL': 57,
                         'EP': 129,
                         'EWa': 85,
                         'EWs': 85,
                         'Eclipsing': 1,
                         'GS': 80,
                         'GalNuclei': 107,
                         'I': 2,
                         'IA': 2,
                         'IB': 2,
                         'IN(YY)': 8,
                         'INA': 8,
                         'INB': 8,
                         'IS': 2,
                         'ISA': 2,
                         'ISB': 13,
                         'K': 80,
                         'KE': 96,
                         'KW': 96,
                         'L': 23,
                         'LB': 36,
                         'LC': 36,
                         'LPB': 129,
                         'ML': 107,
                         'NA': 66,
                         'NB': 66,
                         'NC': 66,
                         'NEW': 1,
                         'Nonstellar': 0,
                         'OVV': 256,
                         'PN': 80,
                         'PSR': 57,
                         'R': 129,
                         'RPHS': 129,
                         'RR(B)': 41,
                         'RRAB': 41,
                         'RRC': 41,
                         'SD': 80,
                         'SNIc-pec': 102,
                         'SRA': 48,
                         'SRB': 48,
                         'SRC': 48,
                         'SRD': 48,
                         'SRS': 129,
                         'SSO': 107,
                         'TDE': 109,
                         'UVN': 2,
                         'WD': 80,
                         'WR(1)': 80,
                         'X': 1,
                         'XF': 117,
                         'XI': 117,
                         'XJ': 117,
                         'XND': 117,
                         'XNG': 117,
                         'XP': 117,
                         'XPR': 124,
                         'XPRM': 124,
                         'XRM': 124,
                         'ac': 203,
                         'aii': 240,
                         'alg': 248,
                         'am': 165,
                         'amcvn': 160,
                         'ast': 275,
                         'b': 247,
                         'bc': 203,
                         'be': 193,
                         'bl': 216,
                         'bly': 248,
                         'by': 240,
                         'c': 203,
                         'ca': 217,
                         'cc': 180,
                         'cm': 217,
                         'cn': 158,
                         'comet': 275,
                         'cp': 154,
                         'cv': 154,
                         'd': 279,
                         'dc': 217,
                         'dqh': 165,
                         'ds': 203,
                         'dsm': 211,
                         'eclipsing': 154,
                         'ell': 240,
                         'er': 169,
                         'ev': 154,
                         'fk': 240,
                         'fsrq': 256,
                         'fuor': 195,
                         'gc': 188,
                         'gd': 203,
                         'grb': 157,
                         'gw': 209,
                         'hae': 197,
                         'haebe': 188,
                         'hpm': 275,
                         'iib': 185,
                         'iii': 247,
                         'iil': 185,
                         'iin': 185,
                         'iip': 185,
                         'k': 279,
                         'lamb': 198,
                         'lboo': 203,
                         'lgrb': 176,
                         'maser': 107,
                         'mira': 203,
                         'moving': 0,
                         'msv': 154,
                         'n-l': 158,
                         'nov': 157,
                         'ov': 188,
                         'p': 158,
                         'pi': 181,
                         'piic': 203,
                         'plsr': 240,
                         'psys': 248,
                         'puls': 154,
                         'pvsg': 154,
                         'pvt': 203,
                         'pwd': 203,
                         'qso': 110,
                         'rcb': 188,
                         'rn': 158,
                         'rot': 154,
                         'rr-ab': 206,
                         'rr-c': 206,
                         'rr-cl': 206,
                         'rr-d': 206,
                         'rr-e': 206,
                         'rr-lyr': 203,
                         'rscvn': 188,
                         'rv': 203,
                         'rvc': 215,
                         'rvv': 215,
                         'sd': 279,
                         'sdbv': 203,
                         'sdc': 238,
                         'sdorad': 188,
                         'seyf': 110,
                         'sgrb': 176,
                         'shs': 193,
                         'sne': 157,
                         'spb': 203,
                         'sr-a': 214,
                         'sr-b': 214,
                         'sr-c': 214,
                         'sr-d': 214,
                         'sreg': 203,
                         'srgrb': 176,
                         'ssc': 168,
                         'su': 168,
                         'sv': 157,
                         'sw': 160,
                         'sx': 203,
                         'sxari': 240,
                         'tia': 180,
                         'tiapec': 182,
                         'tiasc': 182,
                         'tib': 181,
                         'tic': 181,
                         'ticpec': 184,
                         'tsni': 180,
                         'tsnii': 181,
                         'tt': 195,
                         'ttc': 200,
                         'ttw': 200,
                         'ug': 158,
                         'unclass': 154,
                         'uv': 188,
                         'ux': 160,
                         'vs': 0,
                         'vy': 160,
                         'wr': 188,
                         'wu': 248,
                         'wv': 216,
                         'wz': 169,
                         'xrb': 260,
                         'xrbin': 248,
                         'zc': 168,
                         'zz': 209,
                         'zzh': 223,
                         'zzhe': 223,
                         'zzheii': 223},
 'shortname_parentshortname': {'ACVO': 'aii',
                               'AGN': 'GalNuclei',
                               'AR': 'Eclipsing',
                               'BCEPS': 'bc',
                               'BL-Lac': 'BLZ',
                               'BLZ': 'AGN',
                               'CP': '_varstar_',
                               'CW': 'puls',
                               'CWA': 'CW',
                               'CWB': 'CW',
                               'D': 'Eclipsing',
                               'DCEP': 'puls',
                               'DCEPS': 'DCEP',
                               'DM': 'D',
                               'DS': 'D',
                               'DSCTC': 'ds',
                               'DrkMatterA': 'Nonstellar',
                               'E': 'Eclipsing',
                               'ELL': 'rot',
                               'EP': 'NEW',
                               'EWa': 'wu',
                               'EWs': 'wu',
                               'Eclipsing': 'vs',
                               'GS': 'Eclipsing',
                               'GalNuclei': 'Nonstellar',
                               'I': 'ev',
                               'IA': 'ev',
                               'IB': 'ev',
                               'IN(YY)': 'ov',
                               'INA': 'ov',
                               'INB': 'ov',
                               'IS': 'ev',
                               'ISA': 'ev',
                               'ISB': 'IS',
                               'K': 'Eclipsing',
                               'KE': 'K',
                               'KW': 'K',
                               'L': 'puls',
                               'LB': 'L',
                               'LC': 'L',
                               'LPB': 'NEW',
                               'ML': 'Nonstellar',
                               'NA': 'nov',
                               'NB': 'nov',
                               'NC': 'nov',
                               'NEW': 'vs',
                               'Nonstellar': '_varstar_',
                               'OVV': 'BLZ',
                               'PN': 'Eclipsing',
                               'PSR': 'rot',
                               'R': 'NEW',
                               'RPHS': 'NEW',
                               'RR(B)': 'rr-lyr',
                               'RRAB': 'rr-lyr',
                               'RRC': 'rr-lyr',
                               'SD': 'Eclipsing',
                               'SNIc-pec': 'tic',
                               'SRA': 'sreg',
                               'SRB': 'sreg',
                               'SRC': 'sreg',
                               'SRD': 'sreg',
                               'SRS': 'NEW',
                               'SSO': 'Nonstellar',
                               'TDE': 'GalNuclei',
                               'UVN': 'ev',
                               'WD': 'Eclipsing',
                               'WR(1)': 'Eclipsing',
                               'X': 'vs',
                               'XF': 'X',
                               'XI': 'X',
                               'XJ': 'X',
                               'XND': 'X',
                               'XNG': 'X',
                               'XP': 'X',
                               'XPR': 'XP',
                               'XPRM': 'XP',
                               'XRM': 'XP',
                               'ac': 'puls',
                               'aii': 'rot',
                               'alg': 'b',
                               'am': 'p',
                               'amcvn': 'n-l',
                               'ast': 'moving',
                               'b': 'msv',
                               'bc': 'puls',
                               'be': 'gc',
                               'bl': 'piic',
                               'bly': 'b',
                               'by': 'rot',
                               'c': 'puls',
                               'ca': 'c',
                               'cc': 'sne',
                               'cm': 'c',
                               'cn': 'nov',
                               'comet': 'moving',
                               'cp': 'vs',
                               'cv': 'vs',
                               'd': 'eclipsing',
                               'dc': 'c',
                               'dqh': 'p',
                               'ds': 'puls',
                               'dsm': 'ds',
                               'eclipsing': 'vs',
                               'ell': 'rot',
                               'er': 'su',
                               'ev': 'vs',
                               'fk': 'rot',
                               'fsrq': 'BLZ',
                               'fuor': 'ov',
                               'gc': 'ev',
                               'gd': 'puls',
                               'grb': 'cv',
                               'gw': 'pwd',
                               'hae': 'haebe',
                               'haebe': 'ev',
                               'hpm': 'moving',
                               'iib': 'tsnii',
                               'iii': 'msv',
                               'iil': 'tsnii',
                               'iin': 'tsnii',
                               'iip': 'tsnii',
                               'k': 'eclipsing',
                               'lamb': 'be',
                               'lboo': 'puls',
                               'lgrb': 'grb',
                               'maser': 'Nonstellar',
                               'mira': 'puls',
                               'moving': '_varstar_',
                               'msv': 'vs',
                               'n-l': 'nov',
                               'nov': 'cv',
                               'ov': 'ev',
                               'p': 'nov',
                               'pi': 'cc',
                               'piic': 'puls',
                               'plsr': 'rot',
                               'psys': 'b',
                               'puls': 'vs',
                               'pvsg': 'vs',
                               'pvt': 'puls',
                               'pwd': 'puls',
                               'qso': 'AGN',
                               'rcb': 'ev',
                               'rn': 'nov',
                               'rot': 'vs',
                               'rr-ab': 'rr-lyr',
                               'rr-c': 'rr-lyr',
                               'rr-cl': 'rr-lyr',
                               'rr-d': 'rr-lyr',
                               'rr-e': 'rr-lyr',
                               'rr-lyr': 'puls',
                               'rscvn': 'ev',
                               'rv': 'puls',
                               'rvc': 'rv',
                               'rvv': 'rv',
                               'sd': 'eclipsing',
                               'sdbv': 'puls',
                               'sdc': 'dc',
                               'sdorad': 'ev',
                               'seyf': 'AGN',
                               'sgrb': 'grb',
                               'shs': 'gc',
                               'sne': 'cv',
                               'spb': 'puls',
                               'sr-a': 'sreg',
                               'sr-b': 'sreg',
                               'sr-c': 'sreg',
                               'sr-d': 'sreg',
                               'sreg': 'puls',
                               'srgrb': 'grb',
                               'ssc': 'ug',
                               'su': 'ug',
                               'sv': 'cv',
                               'sw': 'n-l',
                               'sx': 'puls',
                               'sxari': 'rot',
                               'tia': 'sne',
                               'tiapec': 'tia',
                               'tiasc': 'tia',
                               'tib': 'cc',
                               'tic': 'cc',
                               'ticpec': 'tic',
                               'tsni': 'sne',
                               'tsnii': 'cc',
                               'tt': 'ov',
                               'ttc': 'tt',
                               'ttw': 'tt',
                               'ug': 'nov',
                               'unclass': 'vs',
                               'uv': 'ev',
                               'ux': 'n-l',
                               'vs': '_varstar_',
                               'vy': 'n-l',
                               'wr': 'ev',
                               'wu': 'b',
                               'wv': 'piic',
                               'wz': 'su',
                               'xrb': 'xrbin',
                               'xrbin': 'b',
                               'zc': 'ug',
                               'zz': 'pwd',
                               'zzh': 'zz',
                               'zzhe': 'zz',
                               'zzheii': 'zz'}}


def parse_options():
    """ Deal with parsing command line options & --help.  Return options object.
    """
    parser = OptionParser(usage="usage: %prog cmd [options]")
    parser.add_option("-a","--srcid",
                      dest="srcid", \
                      action="store", \
                      default="", \
                      help="single srcid (to specify a list, edit pars{})")
    parser.add_option("-b","--percent",
                      dest="percent", \
                      action="store", \
                      default="", \
                      help="single sampling-percent (to specify a list, edit pars{})")
    parser.add_option("-c","--niters",
                      dest="niters", \
                      action="store", \
                      default="", \
                      help="Number of iterations to generate for a srcid, percent-sampling")
    parser.add_option("-d","--pairwise_classifier_pkl_fpath",
                      dest="pairwise_classifier_pkl_fpath", \
                      action="store", \
                      default="", \
                      help="Location of pairwise_classifier__debosscher_table3.pkl.gz")
    parser.add_option("-e","--use_hardcoded_sciclass_lookup",
                      dest="use_hardcoded_sciclass_lookup", \
                      action="store_true", default=False, \
                      help="Use hardcoded sciclass_lookup dict (generally on non-mysql cluster)")

    (options, args) = parser.parse_args()
    print("For help use flag:  --help") # KLUDGE since always: len(args) == 0
    return options


def update_combo_results(combo_results_dict={}, ipython_return_dict={}):
    """ Update combined dict which will be used by plot_percent_tally_summary_dict()
    """
    for class_name in ipython_return_dict.keys():
        if class_name not in combo_results_dict:
            combo_results_dict[class_name] = {}
        for r_clfr_name in ipython_return_dict[class_name].keys():
            if r_clfr_name not in combo_results_dict[class_name]:
                combo_results_dict[class_name][r_clfr_name] = {}
            for i_set in ipython_return_dict[class_name][r_clfr_name].keys():
                if i_set not in combo_results_dict[class_name][r_clfr_name]:
                    combo_results_dict[class_name][r_clfr_name][i_set] = { \
                                                       'count_total': [],
                                                       'count_true': [],
                                                       'percent_false_list': [],
                                                       'sampling_percent_list': []}
                combo_results_dict[class_name][r_clfr_name][i_set]['count_total'].extend( \
                     ipython_return_dict[class_name][r_clfr_name][i_set]['count_total'])
                combo_results_dict[class_name][r_clfr_name][i_set]['count_true'].extend( \
                     ipython_return_dict[class_name][r_clfr_name][i_set]['count_true'])
                combo_results_dict[class_name][r_clfr_name][i_set]['percent_false_list'].extend( \
                     ipython_return_dict[class_name][r_clfr_name][i_set]['percent_false_list'])
                combo_results_dict[class_name][r_clfr_name][i_set]['sampling_percent_list'].extend( \
                     ipython_return_dict[class_name][r_clfr_name][i_set]['sampling_percent_list'])




def massage_types(src_id='', percent='', niters=''):
    """
    """
    if type(src_id) == type(''):
        srcid_list = [int(src_id)]
    elif type(src_id) == type(1):
        srcid_list = [src_id]
    elif type(src_id) == type([]):
        srcid_list = []
        for elem in src_id:
            srcid_list.append(int(elem))
    else:
        raise "src_id of an unexpected type"

    # We are assuming we want dotastro 100123456 style srcids:
    if srcid_list[0] < 100000000:
        for i in xrange(len(srcid_list)):
            srcid_list[i] += 100000000

    if type(percent) == type(''):
        percent_list = [float(percent)]
    elif type(percent) == type(1.0):
        percent_list = [percent]
    elif type(percent) == type([]):
        percent_list = []
        for elem in percent:
            percent_list.append(float(elem))
    else:
        raise "percent of an unexpected type"

    if type(niters) == type(''):
        niters = [int(niters)]
    elif type(niters) == type(1):
        niters = [niters]
    elif type(niters) == type([]):
        niters_list = []
        for elem in niters:
            niters_list.append(int(elem))
        niters = niters_list
    else: 
        raise "niters of an unexpected type"

    #if type(niters) == type(''):
    #    niters = int(niters)
    #elif type(niters) == type(1):
    #    pass # keep same
    #else: 
    #    raise "niters of an unexpected type"

    return (srcid_list, percent_list, niters)


def get_perc_subset(srcid_list=[], percent_list=[], niters=1):
    """ Adapted from:
      - analysis_deboss_tcp_source_compare.py::perc_subset_worker()
      - generate_weka_classifiers.py --train_mode :
             spawn_off_arff_line_tasks()

    # TODO: might need to convert ids into 100000000 + ids

    # TODO: currently this generates xml-strings with features,
          - we eventually want arff rows which can be classified
              (ala generate_weka_classifiers.py --train_mode)
              ... condense_task_results_and_form_arff()

    """
    import copy
    import random
    import io
    sys.path.append(os.environ.get('TCP_DIR') + '/Software/feature_extract/MLData')
    #sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + '/Software/feature_extract/Code/extractors'))
    #print os.environ.get("TCP_DIR")
    #import mlens3
    import arffify

    sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                  'Software/feature_extract/Code'))
    import db_importer
    sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                  'Software/feature_extract'))
    from Code import generators_importers

    #out_arff_row_dict = {}

    master_list = []
    master_features_dict = {}
    all_class_list = []
    master_classes_dict = {}

    new_srcid_list = []
    for src_id in srcid_list:

        xml_fpath = os.path.expandvars("$HOME/scratch/vosource_xml_writedir/%d.xml" % (src_id))

        signals_list = []
        gen_orig = generators_importers.from_xml(signals_list)
        gen_orig.signalgen = {}
        gen_orig.sig = db_importer.Source(xml_handle=xml_fpath, doplot=False, make_xml_if_given_dict=True)
        gen_orig.sdict = gen_orig.sig.x_sdict
        gen_orig.set_outputs() # this adds/fills self.signalgen[<filters>,multiband]{'input':{filled},'features':{empty},'inter':{empty}}

        signals_list_temp = []
        gen_temp = copy.deepcopy(gen_orig)
        for perc in percent_list:
            ### We generate several random, percent-subsampled vosource in order to include error info:
            #if 1:
            #    i = niters # this should just be a single (integer) subset number/iteration index
            #for i in xrange(niters):
            for i in niters:
                new_srcid = "%d_%2.2f_%d" % (src_id, perc, i)
                new_srcid_list.append(new_srcid)

                dbi_src = db_importer.Source(make_dict_if_given_xml=False)
                for band, band_dict in gen_orig.sig.x_sdict['ts'].iteritems():
                    i_start = int(((len(band_dict['m'])+1) * (1 - perc)) * random.random())
                    i_end = i_start + int(perc * (len(band_dict['m'])+1))
                    gen_temp.sig.x_sdict['ts'][band]['m'] = band_dict['m'][i_start:i_end]
                    gen_temp.sig.x_sdict['ts'][band]['m_err'] = band_dict['m_err'][i_start:i_end]
                    gen_temp.sig.x_sdict['ts'][band]['t'] = band_dict['t'][i_start:i_end]
                dbi_src.source_dict_to_xml(gen_temp.sig.x_sdict)
                write_xml_str = dbi_src.xml_string

                signals_list = []
                gen = generators_importers.from_xml(signals_list)
                gen.generate(xml_handle=write_xml_str)
                gen.sig.add_features_to_xml_string(signals_list)                
                gen.sig.x_sdict['src_id'] = new_srcid
                dbi_src.source_dict_to_xml(gen.sig.x_sdict)

                xml_fpath = dbi_src.xml_string

                a = arffify.Maker(search=[], skip_class=False, local_xmls=True, convert_class_abrvs_to_names=False, flag_retrieve_class_abrvs_from_TUTOR=False, dorun=False)
                out_dict = a.generate_arff_line_for_vosourcexml(num=new_srcid, xml_fpath=xml_fpath)

                #out_arff_row_dict[(src_id, perc, i)] = out_dict # ??? TODO: just arff rows?
                # dbi_src.xml_string
    	        master_list.append(out_dict)
    	        all_class_list.append(out_dict['class'])
                master_classes_dict[out_dict['class']] = 0
    	        for feat_tup in out_dict['features']:
    	            master_features_dict[feat_tup] = 0 # just make sure there is this key in the dict.  0 is filler

    master_features = master_features_dict.keys()
    master_classes = master_classes_dict.keys()
    a = arffify.Maker(search=[], skip_class=False, local_xmls=True, 
                      convert_class_abrvs_to_names=False,
                      flag_retrieve_class_abrvs_from_TUTOR=False,
                      dorun=False, add_srcid_to_arff=True)
    a.master_features = master_features
    a.all_class_list = all_class_list
    a.master_classes = master_classes
    a.master_list = master_list
    # # # TODO: ideally just the arff lines / strings will be used
    #        - although it might be nice to have a disk copy of the arff rows for record, passing to others.
    fp_strio = io.StringIO()
    a.write_arff(outfile=fp_strio, \
                 remove_sparse_classes=True, \
                 n_sources_needed_for_class_inclusion=1)#, classes_arff_str='', remove_sparse_classes=False)

    arff_row_list = []
    out_dict = {}
    arff_rows_str = fp_strio.getvalue()

    # See pairwise_classification.py 2550
    #Pairwise_Classification   parse_arff(self, arff_has_ids=False, arff_has_classes=True, has_srcid=False, get_features=False):
    """
    arff_rows = []
    for a_str in arff_rows_str.split('\n'):
        if len(a_str) == 0:
            continue
        if a_str[0] == '@':
            continue
        if a_str[0] == '%':
            continue
        arff_rows.append(a_str)

    assert(len(all_class_list) == len(arff_rows))

    for i, arff_row in enumerate(arff_rows):
        class_name = all_class_list[i]

        if not out_dict.has_key(class_name):
            out_dict[class_name] = {'srcid_list':[],
                                    'count':0,
                                    'arffrow_wo_classnames':[],
                                    }
        out_dict[class_name]['srcid_list'].append(new_srcid_list[i])
        out_dict[class_name]['count'] += 1
        out_dict[class_name]['arffrow_wo_classnames'].append( \
                  arff_row[:arff_row.rindex("'", 0,arff_row.rindex("'")) - 1])

    return out_dict # out_dict[class_name][arffrow_wo_classnames:[], count:1, srcid_list:[] ### exclude:'arffrow_with_classnames:[]

    """

    return arff_rows_str


def parse_src_perc_iter_from_arffstr(arff_str):
    """ Parse srcid, poercent, niter from arff strings like:   149049_1.00_0,0.2995,0.0,...
    """
    src_perc_iter_dict = {'srcids':[],
                          'percents':[],
                          'iters':[]}
    for row in arff_str.split('\n'):
        if len(row) < 5:
            continue
        if ((row[0] == '%') or
            (row[0] == '@')):
            continue
        sub_str = row[:row.find(',')]
        tups = sub_str.split('_')
        srcid = int(tups[0])
        perc = float(tups[1])
        niter = int(tups[2])
        src_perc_iter_dict['srcids'].append(srcid)
        src_perc_iter_dict['percents'].append(perc)
        src_perc_iter_dict['iters'].append(niter)

    return src_perc_iter_dict



class Resample_Pairwise_Classify:
    """
    """
    def __init__(self, pars):
        from pairwise_classification import Weka_Pairwise_Classification, Pairwise_Classification

        self.pars = pars
        
        self.WekaPairwiseClassification = Weka_Pairwise_Classification(pars=self.pars)
        self.WekaPairwiseClassification.fp_cyto_nodeattrib = None
        self.WekaPairwiseClassification.fp_cyto_network = None

        self.PairwiseClassification = Pairwise_Classification(self.pars)


    def load_pairwise_classifier(self, fpath='', pair_path_replace_tup=None):
        """ Load the pairwise classifier pkl.gz dictionary
        """
        fp=open(fpath,'rb')
        self.pairwise_classifier_dict=cPickle.load(fp)
        fp.close()

        self.WekaPairwiseClassification.load_weka_classifiers(classifier_dict=self.pairwise_classifier_dict, 
                                                              pair_path_replace_tup=pair_path_replace_tup)

    def reload_pairwise_classifier(self, fpath='', pair_path_replace_tup=None):
        """ Load the pairwise classifier pkl.gz dictionary
        """
        fp=open(fpath,'rb')
        self.pairwise_classifier_dict=cPickle.load(fp)
        fp.close()

        self.WekaPairwiseClassification.reload_weka_classifiers(classifier_dict=self.pairwise_classifier_dict, 
                                                              pair_path_replace_tup=pair_path_replace_tup)


    def make_pairwise_classifications(self, arff_row_dict={}, store_confids=True):
        """ Using arff rows, generate pairwise classifications using WEKA classifier and confidence voting.

        Adapted from do_pairwise_classification()

        """
        classif_summary_dict = self.WekaPairwiseClassification.do_pairwise_classification( \
                                        classifier_dict=self.pairwise_classifier_dict,
                                        pairwise_pruned_dict=arff_row_dict,
                                        set_num=None, store_confids=store_confids)

        return classif_summary_dict


        """ WHERE:
        {out_dict'classif_summary_dict':classif_summary_dict,
                'percent':percent,
                'set_num':set_num}
                """


    def organize_sciclassdict_by_percent_niters(self, arff_sciclass_dict):
        """
        # NOTE: Kludgey, since arff_sciclass_dict is just organized by sciclass only and not percent or niters
        #       - although it is easiest for self.get_perc_subset() to just generate a arff with all percent, niters, srcids combined (in its current function form)
        """
        perc_niter_sciclassdict = {}
        for class_name, class_dict in arff_sciclass_dict.iteritems():
            for i, src_combo_str in enumerate(class_dict['srcid_list']):
                src_combo_list = src_combo_str.split('_')
                perc = src_combo_list[1]
                niter = int(src_combo_list[2])
                if perc not in perc_niter_sciclassdict:
                    perc_niter_sciclassdict[perc] = {}
                if niter not in perc_niter_sciclassdict[perc]:
                    perc_niter_sciclassdict[perc][niter] = {}
                if class_name not in perc_niter_sciclassdict[perc][niter]:
                    perc_niter_sciclassdict[perc][niter][class_name] = { \
                                                            'arffrow_with_classnames':[],
                                                            'arffrow_wo_classnames':[],
                                                            'count':0,
                                                            'feat_lists':[],
                                                            'srcid_list':[]}
                perc_niter_sciclassdict[perc][niter][class_name]['arffrow_with_classnames'].append( \
                                          class_dict['arffrow_with_classnames'][i])
                perc_niter_sciclassdict[perc][niter][class_name]['arffrow_wo_classnames'].append( \
                                          class_dict['arffrow_wo_classnames'][i])
                perc_niter_sciclassdict[perc][niter][class_name]['srcid_list'].append(src_combo_str)
                perc_niter_sciclassdict[perc][niter][class_name]['count'] += 1

        return perc_niter_sciclassdict


    def ipython_task(self, src_id='', percent='', niters='', store_confids=True, 
                     use_r_classifier=True):
        """
        NOTE: this should be runnable on an IPython client

     -> returns: classified results in a dict?  like an ipython task of:
             pairwise_classification.py --deboss_percentage_exclude_analysis
        """

        (srcid_list, percent_list, niters) = massage_types(src_id=src_id, percent=percent, niters=niters)

        arff_str = get_perc_subset(srcid_list, percent_list, niters)

        if use_r_classifier:
            # # # # Insert R classifier here...  replace the following couple functions...
            sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Algorithms/'))
            import rpy2_classifiers
            rc = rpy2_classifiers.Rpy2Classifier()
            do_ignore_NA_features = False

            data_dict = rc.parse_full_arff(arff_str=arff_str)


            classifier_fpath = os.path.expandvars("$HOME/scratch/test_RF_classifier.rdata")
            r_name='rf_clfr'
            classifier_dict = {'r_name':r_name}
            rc.load_classifier(r_name=r_name,
                           fpath=classifier_fpath)
            classif_results = rc.apply_randomforest(classifier_dict=classifier_dict,
                                            data_dict=data_dict,
                                            do_ignore_NA_features=do_ignore_NA_features)
            # TODO: need to format/retrieve expected prediction structures
            import pdb; pdb.set_trace()
            print()
            return_dict = {}
            for perc, perc_dict in perc_niter_sciclassdict.iteritems():
                if perc not in return_dict:
                    return_dict[perc] = {}
                for niter, sciclassdict in perc_dict.iteritems():
                    ### NOTE: The return_dict output should be something like this:
                    ### ? what is the most important part of this dict?

                    #return_dict[perc][niter] = self.make_pairwise_classifications(arff_row_dict=sciclassdict, store_confids=store_confids)
                    return_dict[perc][niter] = \
                        {'confusion_matrix':confusion_matrix,
                         'confusion_matrix_index_class_dict':confusion_matrix_index_class_dict,
                         'confusion_matrix_index_list':class_shortname_list,
                         'srcid_classif_summary':srcid_classif_summary}

            
        else:
            arff_sciclass_dict = self.PairwiseClassification.parse_arff(has_srcid=True,
                                                                        arff_str=arff_str,
                                                                        write_pkl=False)

            # NOTE: Kludgey, since arff_sciclass_dict is just organized by sciclass only and not percent or niters
            #       - although it is easiest for self.get_perc_subset() to just generate a arff with all percent, niters, srcids combined (in its current function form)
            perc_niter_sciclassdict = self.organize_sciclassdict_by_percent_niters(arff_sciclass_dict)

            # I want classif_summary_dict to be a dict divided by percent, setnum/n_iters
            #     so that the dict{} can be pulled out of IPython client and then
            #    tally_correctly_classified_for_percent() can make use of the dict in the controlling script.
            return_dict = {}
            for perc, perc_dict in perc_niter_sciclassdict.iteritems():
                if perc not in return_dict:
                    return_dict[perc] = {}
                for niter, sciclassdict in perc_dict.iteritems():
                    #print perc, niter, "make_pairwise_classifications()"
                    return_dict[perc][niter] = self.make_pairwise_classifications(arff_row_dict=sciclassdict,
                                                                                  store_confids=store_confids)
        return return_dict






def non_ipython_main(pars, pwiseclass_id_pklfpath={}):
    """ To be used for testing / debugging:
    """
    ### KLUDGE: this needs to be done in non-ipython case:
    pars['niters'] = range(int(pars['niters']))
    ###

    # TODO: iterate over pwiseclass_id_pklfpath
    import pprint
    pprint.pprint(pwiseclass_id_pklfpath)
    
    percent_tally_summary_dict = {}
    classifier_confidence_analysis_dict = {}
    for pw_classifier_name, pw_classifier_dict in pwiseclass_id_pklfpath.iteritems():

        # TODO: In ipython_main(): will need to mec() the following class initializations:

        rcp = Resample_Pairwise_Classify(pars=pars)

        if 0: 
            # 20101213 dstarr disables while trying out R code without ipython:
            rcp.load_pairwise_classifier(fpath=pw_classifier_dict['pairwise_classifier_pkl_fpath'],
                                     pair_path_replace_tup=pw_classifier_dict['pair_path_replace_tup'])
        ### This is to be done on IPython tc() node:
        #     -> No duplicate [perc][niter] should be done on different nodes (niter should be different)
        perc_niter_classif_dict = rcp.ipython_task(src_id=pars['src_id'],
                                                   percent=pars['percent'],
                                                   niters=pars['niters'],
                                                   store_confids=False)

        ### This is to be done on the master, once all of the IPython out_dict{} have been pulled:
        #          perc_niter_classifdict[perc][niter]
        from pairwise_classification import Weka_Pairwise_Classification
        WekaPairwiseClassification = Weka_Pairwise_Classification(pars=pars)


        for perc, perc_dict in perc_niter_classif_dict.iteritems():
            for niter, classif_dict in perc_dict.iteritems():
                WekaPairwiseClassification.tally_correctly_classified_for_percent(perc, niter,
                                                classif_dict,
                                                percent_tally_summary_dict,
                                                classifier_confidence_analysis_dict=classifier_confidence_analysis_dict)


    #classifier_confidence_analysis_fpath = '/home/pteluser/scratch/classifier_confidence_analysis.pkl.gz'
    #if os.path.exists(classifier_confidence_analysis_fpath):
    #    os.system('rm ' + classifier_confidence_analysis_fpath)
    #fp = gzip.open(classifier_confidence_analysis_fpath,'wb')
    #cPickle.dump(classifier_confidence_analysis_dict,fp,1) # ,1) means a binary pkl is used.
    #fp.close()

    percent_plot_local_fpath = os.path.expandvars('$HOME/scratch/xmls_deboss_percentage_exclude.ps')
    WekaPairwiseClassification.plot_percent_tally_summary_dict(percent_tally_summary_dict,
                                     img_fpath=percent_plot_local_fpath)

    os.system('cp %s /home/pteluser/Dropbox/work/' % (percent_plot_local_fpath))

    ###### For debugging:
    #import pprint
    #for class_name, class_dict in percent_tally_summary_dict.iteritems():
    #    for set_num, set_dict in class_dict.iteritems():
    #        if len(set_dict['count_total']) > 0:
    #            pprint.pprint((class_name, set_num, set_dict))



def ipython_main(pars, pwiseclass_id_pklfpath={}, apply_classifier_to_all_srcids=True):
    """ To be used for testing / debugging:
    """
    import datetime
    try:
        from IPython.kernel import client
    except:
        pass

    mec = client.MultiEngineClient()
    mec.reset(targets=mec.get_ids()) # Reset the namespaces of all engines
    tc = client.TaskClient()

    percent_tally_summary_dict = {}
    classifier_confidence_analysis_dict = {}
    pw_all_classif_dict = {}
    first_time = True
    for pw_classifier_name, pw_classifier_dict in pwiseclass_id_pklfpath.iteritems():

        ##### This determines src_ids which will have the classifier applied to:
        if (len(pars['crossvalid_pairwise_classif_dirpath']) == 0) or (apply_classifier_to_all_srcids):
            ### This chooses all src_ids, which the classifier will be applied to.
            to_classify_srcids = pars['src_id']
        else:
            ### This chooses src_ids which were not used for training the classifier
            pairwise_trainset_fpath = "%s/pairwise_trainset.pkl.gz" % (pw_classifier_dict['pairwise_classifier_pkl_fpath'][:pw_classifier_dict['pairwise_classifier_pkl_fpath'].rfind('/')])
            pairwise_trainset = cPickle.load(gzip.open(pairwise_trainset_fpath))
            classifier_srcid_list = []
            for class_name, class_dict in pairwise_trainset.iteritems():
                for src_id in class_dict['srcid_list']:
                    if not src_id in classifier_srcid_list:
                        classifier_srcid_list.append(src_id)
            to_classify_srcids = []
            for src_id in pars['src_id']:
                if not str(src_id) in classifier_srcid_list:
                    to_classify_srcids.append(int(src_id))
            print("n_src trained classifer=%d  to_classify=%d  total_possible=%d, srcids=%s" % (len(classifier_srcid_list), len(to_classify_srcids), len(pars['src_id']), str(to_classify_srcids[:3])))
        #####


        # # # #mec = client.MultiEngineClient()
        # # # # # # # # # # # mec.reset(targets=mec.get_ids()) # Reset the namespaces of all engines
        # # # #tc = client.TaskClient()
        task_id_list = []

        #sys.path.append(os.path.abspath(os.environ.get('TCP_DIR') + 'Software/ingest_tools'))
        #sys.path.append(os.path.abspath(os.environ.get('TCP_DIR') + 'Software/citris33'))
        #from test_pairwise_on_citris33_ipython import Resample_Pairwise_Classify
        # rcp.load_pairwise_classifier(fpath=pars['pairwise_classifier_pkl_fpath'])

        
        mec.push({'pars':pars})

        first_time_mec_exec_str = """
import sys, os
sys.path.append(os.path.abspath('/global/home/users/dstarr/src/TCP/Software/ingest_tools'))
sys.path.append(os.path.abspath('/global/home/users/dstarr/src/TCP/Software/citris33'))

import jpype
os.environ["JAVA_HOME"] = '/global/home/users/dstarr/src/install/jdk1.6.0_03'
os.environ["CLASSPATH"] += ':/global/home/users/dstarr/src/TCP/Software/ingest_tools'
if not jpype.isJVMStarted():
    _jvmArgs = ["-ea"] # enable assertions
    _jvmArgs.append("-Djava.class.path=" + os.environ["CLASSPATH"])
    _jvmArgs.append("-Xmx1500m") # 4000 & 5000m works, 3500m doesnt for some WEKA .models
    jpype.startJVM(jpype.getDefaultJVMPath(), *_jvmArgs)


import test_pairwise_on_citris33_ipython

rcp = test_pairwise_on_citris33_ipython.Resample_Pairwise_Classify(pars=pars)
try:
    rcp.load_pairwise_classifier(fpath="%s",
                             pair_path_replace_tup=%s)
except:
    print "EXCEPT: rcp.load_pairwise_classifier(%s, %s)"
            """ % (pw_classifier_dict['pairwise_classifier_pkl_fpath'], 
                   str(pw_classifier_dict['pair_path_replace_tup']),
                   pw_classifier_dict['pairwise_classifier_pkl_fpath'], 
                   str(pw_classifier_dict['pair_path_replace_tup']))
        if first_time:
            mec_exec_str = first_time_mec_exec_str
        else:
            tc.task_controller.clear()
            mec.clear_queue()
            mec.clear_pending_results()
            mec_exec_str = """
rcp.pars = pars
try:
    rcp.reload_pairwise_classifier(fpath="%s",
                             pair_path_replace_tup=%s)
except:
    print "EXCEPT: rcp.load_pairwise_classifier(%s, %s)"
            """ % (pw_classifier_dict['pairwise_classifier_pkl_fpath'], 
                   str(pw_classifier_dict['pair_path_replace_tup']),
                   pw_classifier_dict['pairwise_classifier_pkl_fpath'], 
                   str(pw_classifier_dict['pair_path_replace_tup']))

        print('before mec()')
        #print mec_exec_str
        #import pdb; pdb.set_trace()
        engine_ids = mec.get_ids()
        pending_result_dict = {}
        for engine_id in engine_ids:
            pending_result_dict[engine_id] = mec.execute(mec_exec_str, targets=[engine_id], block=False)
            
        n_pending = len(pending_result_dict)
        i_count = 0
        while n_pending > 0:
            still_pending_dict = {}
            for engine_id, pending_result in pending_result_dict.iteritems():
                result_val = pending_result.get_result(block=False)
                if result_val is None:
                    print("Still pending on engine: %d" % (engine_id))
                    still_pending_dict[engine_id] = pending_result
            if i_count > 10:
                mec.clear_pending_results()
                pending_result_dict = {}
                mec.reset(targets=still_pending_dict.keys())
                for engine_id in still_pending_dict.keys():
                    pending_result_dict[engine_id] = mec.execute(mec_exec_str, targets=[engine_id], block=False)
                ###
                time.sleep(20) # hack
                pending_result_dict = [] # hack
                ###
                i_count = 0
            else:
                print("sleeping...")
                time.sleep(5)
                pending_result_dict = still_pending_dict
            n_pending = len(pending_result_dict)
            i_count += 1

        print('after mec()')
        time.sleep(5) # This may be needed, although mec() seems to wait for all the Ipython clients to finish
        print('after sleep()')

        # Right now we will do a specific perc, niter/set on each node, although a list of these can be given to each node, as well.
        #     -> No duplicate [perc][niter] should be done on different nodes (niter should be different)
        for perc in pars['percent']:
            for set_num in xrange(int(pars['niters'])):
                # it is ok if set_num is str or int
                tc_exec_str = "perc_niter_classif_dict = rcp.ipython_task(src_id=srcid_list, percent=perc_list, niters=niters, store_confids=False)"
                #print '!!!!', set_num, perc, tc_exec_str
                taskid = tc.run(client.StringTask(tc_exec_str,
                                                       push={'srcid_list':to_classify_srcids,
                                                             'perc_list':[perc],
                                                             'niters':set_num},
                                                       pull='perc_niter_classif_dict', retries=3))
                #taskid = tc.run(client.StringTask(tc_exec_str,push={'srcid_list':pars['src_id'],'perc_list':[perc],'niters':set_num},pull='perc_niter_classif_dict', retries=3))
                task_id_list.append(taskid)

        pw_all_classif_dict[pw_classifier_name] = {}
        all_classif_dict = pw_all_classif_dict[pw_classifier_name]
        while ((tc.queue_status()['scheduled'] > 0) or
               (tc.queue_status()['pending'] > 0)):
            tasks_to_pop = []
            for task_id in task_id_list:
                temp = tc.get_task_result(task_id, block=False)
                if temp is None:
                    continue
                temp2 = temp.results
                if temp2 is None:
                    continue
                results = temp2.get('perc_niter_classif_dict',None)
                if results is None:
                    continue # skip these sources (I think generally UNKNOWN ... science classes)
                if len(results) > 0:
                    tasks_to_pop.append(task_id)
                    perc_niter_classif_dict = results
                    for perc, perc_dict in perc_niter_classif_dict.iteritems():
                        for set_num, set_dict in perc_dict.iteritems():
                            #print '111 set_num=', set_num, 'perc=', perc
                            if perc not in all_classif_dict:
                                all_classif_dict[perc] = {}
                            if set_num not in all_classif_dict[perc]:
                                # NOTE: I think this should always be the case
                                all_classif_dict[perc][set_num] = set_dict
                            
            for task_id in tasks_to_pop:
                task_id_list.remove(task_id)
            print(tc.queue_status())
            print('Sleep... 20 in test_pairwise_on_citris33_ipython::ipython_main()', datetime.datetime.utcnow())
            time.sleep(20)
        # IN CASE THERE are still tasks which have not been pulled/retrieved:
        for task_id in task_id_list:
            for task_id in task_id_list:
                temp = tc.get_task_result(task_id, block=False)
                if temp is None:
                    continue
                temp2 = temp.results
                if temp2 is None:
                    continue
                results = temp2.get('perc_niter_classif_dict',None)
                if results is None:
                    continue # skip these sources (I think generally UNKNOWN ... science classes)
                if len(results) > 0:
                    perc_niter_classif_dict = results
                    for perc, perc_dict in perc_niter_classif_dict.iteritems():
                        for set_num, set_dict in perc_dict.iteritems():
                            #print '222 set_num=', set_num, 'perc=', perc
                            if perc not in all_classif_dict:
                                all_classif_dict[perc] = {}
                            if set_num not in all_classif_dict[perc]:
                                # NOTE: I think this should always be the case
                                all_classif_dict[perc][set_num] = set_dict
        first_time = False

    ### This is to be done on the master, once all of the IPython out_dict{} have been pulled:
    #          perc_niter_classifdict[perc][niter]
    from pairwise_classification import Weka_Pairwise_Classification
    WekaPairwiseClassification = Weka_Pairwise_Classification(pars=pars)

    for pw_classifier_name, all_classif_dict in pw_all_classif_dict.iteritems():
        for perc, perc_dict in all_classif_dict.iteritems():
            for niter, classif_dict in perc_dict.iteritems():
                WekaPairwiseClassification.tally_correctly_classified_for_percent(perc, niter, 
                                                                                  pw_classifier_name,
                                                classif_dict,
                                                percent_tally_summary_dict,
                                                classifier_confidence_analysis_dict=classifier_confidence_analysis_dict)
    ###### For debugging:
    #import pprint
    #for class_name, class_dict in percent_tally_summary_dict.iteritems():
    #    for set_num, set_dict in class_dict.iteritems():
    #        if len(set_dict['count_total']) > 0:
    #            pprint.pprint((class_name, set_num, set_dict))
    #        print

    #classifier_confidence_analysis_fpath = '/home/pteluser/scratch/classifier_confidence_analysis.pkl.gz'
    #if os.path.exists(classifier_confidence_analysis_fpath):
    #    os.system('rm ' + classifier_confidence_analysis_fpath)
    #fp = gzip.open(classifier_confidence_analysis_fpath,'wb')
    #cPickle.dump(classifier_confidence_analysis_dict,fp,1) # ,1) means a binary pkl is used.
    #fp.close()

    percent_plot_local_fpath = os.path.expandvars('$HOME/scratch/xmls_deboss_percentage_exclude.ps')
    if os.path.exists(percent_plot_local_fpath):
        os.system('rm ' + percent_plot_local_fpath)

    WekaPairwiseClassification.plot_percent_tally_summary_dict(percent_tally_summary_dict,
                                     img_fpath=percent_plot_local_fpath)

    os.system('cp %s /home/pteluser/Dropbox/work/' % (percent_plot_local_fpath))

    ###### For debugging:
    import pprint
    for class_name, class_dict in percent_tally_summary_dict.iteritems():
        for pw_class, pw_dict in class_dict.iteritems():
            for set_num, set_dict in pw_dict.iteritems():
                if len(set_dict['count_total']) > 0:
                    pprint.pprint((class_name, pw_class, set_num, set_dict))
    import pdb; pdb.set_trace()


class R_Task_Controllers:
    """ Main corolling methods for Non-ipython and Ipython_parallel cases.
    """
    sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Algorithms/'))
    import rpy2_classifiers
    rc = rpy2_classifiers.Rpy2Classifier()


    def load_R_classifier(self, class_name='', rdata_fpath=''):
        """ This loads one or more R classifiers for classification use.

        TODO: This will eventually load a list of R classifiers into VM

        """
        self.rc.load_classifier(r_name=class_name,
                                fpath=rdata_fpath)


    def massage_classif_results(self, classif_results, 
                                classifier_name='',
                                percent_tally_summary_dict={},
                                src_perc_iter_dict=[], 
                                toclassif_data={},
                                srcid_list=[], percent=0, set_num=0, pars={}):
        """ Parse the R object into something expected by existing 
        test_pairwise_on_citris33_ipython.py pairwise plotting code.
        """
        # TODO: want to have the original classifications for each source-id
        # TODO: I think I want a list of (set, perc, niter) passed in...
        # TODO: probably need to have a dict which translates R-classes to TUTOR-classnames
        from numpy import array, sum
        
        #print classif_results['robj_confusion_matrix']
        #print toclassif_data['class_list']
        #print classif_results['predicted_classes']
        #import pprint
        #pprint.pprint(toclassif_data)

        conf_matrix = array(classif_results['robj_confusion_matrix'])

        for i, confuse_row in enumerate(conf_matrix):
            row_class_r = classif_results['confusion_matrix_axis_pred'][i]
            row_class = pars['R_class_lookup'][row_class_r]

            count_total = sum(confuse_row)

            if row_class_r in classif_results['confusion_matrix_axis_y']:
                i_y_class = classif_results['confusion_matrix_axis_y'].index(row_class_r)
                count_true = confuse_row[i_y_class]
            else:
                count_true = 0.0

            if count_total == 0:
                percent_false = 0.0
            else:
                percent_false = (count_total - count_true) / float(count_total)
            #print '!!!!!', percent_false
            #row_class_r = classif_results['confusion_matrix_axes_classes'][i]
            ###print i, row_class, '!', classif_results['confusion_matrix_axes_classes']

            summary_dict = percent_tally_summary_dict[row_class][classifier_name]
            summary_dict[set_num]['sampling_percent_list'].append(percent)
            summary_dict[set_num]['count_total'].append(count_total)
            summary_dict[set_num]['count_true'].append(count_true)
            summary_dict[set_num]['percent_false_list'].append(percent_false)
            # # # # #
            # ??? set_num ??? the confusion matrix has all of the sets
            #     - which might be ok in thend, but not the way the dict was orig intended
            #     - need to use set in the above ....function
            
            # count_total and count_true just come from confusion matrix in other examples

            #import pdb; pdb.set_trace()
            #print


        #### WANT:
        # percent_tally_summary_dict[pw_classifier_name]
        #                                               [set_num]['percent_false_list']#len() == 0
        #                                               [set_num]['sampling_percent_list']# to be float()
        #                                               [set_num]['count_total'][j_perc]
        #                                               [set_num]['count_true'][j_perc]


    def R_non_ipython_main(self, pars, r_classifiers={}, classifier_name='',
                           srcid_list=[], percent_list=[], iter_list=[],
                           rclass_name='', rdata_fpath=''):
        """ 
        Non Ipython-parallel R-based classifier version.

        To be used for testing.

        NOTE: The functionality is initially adapted after non_ipython_main()

        NOTE: This is now called so that this will be run on an ipython engine

        """
        # NOTE: I think this code will require only a single percentage per arff_str
        #    - this would be less nessiccary if we have  the source-ids contain percent info
        #       - but that would require more modifications.
        #MAYBE NOT NEEDED:# assert(len(percent_list) == 1)

        # # # arff_str = get_perc_subset(srcid_list, percent_list, iter_list) #TO BE parallelized (extracts features)
        #fp = open(os.path.expandvars('$HOME/scratch/full_deboss_20101220.arff'), 'w')
        #fp.write(arff_str)
        #fp.close() # # # # # temporary
        #import pdb; pdb.set_trace()
        # # #src_perc_iter_dict = parse_src_perc_iter_from_arffstr(arff_str)

        # TODO: If I can, I want only one classifeir on each R-VM, to conserve memory
        # # #data_dict = self.rc.parse_full_arff(arff_str=arff_str)

        # This loads classifiers into R-VM:
        self.load_R_classifier(class_name=rclass_name,
                               rdata_fpath=rdata_fpath)

        percent_tally_summary_dict = {}
        classifier_confidence_analysis_dict = {}
        for classifier_dict in r_classifiers:
            for set_num in iter_list:
                sub_iter_list = [set_num]
                for perc in percent_list:
                    sub_perc_list = [perc]
                    arff_str = get_perc_subset(srcid_list, sub_perc_list, sub_iter_list) #TO BE parallelized (extracts features)
                    src_perc_iter_dict = parse_src_perc_iter_from_arffstr(arff_str)
                    data_dict = self.rc.parse_full_arff(arff_str=arff_str, 
                                                        skip_missingval_lines=True)
                    ### NOTE: each classifier_name corresponds to a different trained classifier
                    classif_results = self.rc.apply_randomforest(classifier_dict=classifier_dict,
                                                    data_dict=data_dict,
                                                    do_ignore_NA_features=False)

                    if len(percent_tally_summary_dict.keys()) == 0:
                        # KLUDGEY: This could be set up earlier if the R-classifier's possible_classes is known previously.  Could these possible classes vary for different classifiers?  probably not...
                        for r_class_name in classif_results['possible_classes']:
                            class_name = pars['R_class_lookup'][r_class_name]
                            percent_tally_summary_dict[class_name] = {}
                            for a_dict in r_classifiers:
                                 percent_tally_summary_dict[class_name][classifier_name] = {}
                                 for a_set_num in iter_list:
                                     percent_tally_summary_dict[class_name][classifier_name] \
                                              [a_set_num] = {'percent_false_list':[],
                                                             'sampling_percent_list':[],
                                                             'count_total':[],
                                                             'count_true':[]}
                                              #               'count_total':{},
                                              #               'count_true':{}}
                    # # # TODO: push the classif_results into something which can
                    #     be passed out of the IPython engine
                    #percent_tally_summary_dict[classifier_dict['class_name']] = \
                    self.massage_classif_results(classif_results, 
                                                 classifier_name=classifier_name,
                                                 percent_tally_summary_dict=percent_tally_summary_dict,
                                                 toclassif_data=data_dict,
                                                 src_perc_iter_dict=src_perc_iter_dict,
                                                 srcid_list=srcid_list, 
                                                 percent=perc, 
                                                 set_num=set_num,
                                                 pars=pars)
                
        return percent_tally_summary_dict

        #### WANT:
        # percent_tally_summary_dict[pw_classifier_name]
        #                                               [set_num]['percent_false_list']#len() == 0
        #                                               [set_num]['sampling_percent_list']# to be float()
        #                                               [set_num]['count_total'][j_perc]
        #                                               [set_num]['count_true'][j_perc]
        ##### I think this is used by: ???? HTML visualization?
        # classifier_confidence_analysis_dict[percent][set_num]['confids']
        #                                                      ['confusion_matrix']
        #                                                      ['confusion_matrix_index_class_dict']
        #                                                      ['confusion_matrix_index_list']

        #### TODO:
        #percent_plot_local_fpath = os.path.expandvars('$HOME/scratch/xmls_deboss_percentage_exclude.ps')
        #WekaPairwiseClassification.plot_percent_tally_summary_dict(percent_tally_summary_dict,
        #                                                           img_fpath=percent_plot_local_fpath)
        #os.system('cp %s /home/pteluser/Dropbox/work/' % (percent_plot_local_fpath))




def master_ipython_R_classifiers(pars={},
                                 classifier_info_dicts={}, 
                                 percent_list=[],
                                 iter_list=[]):
    """ Master controlling script which initializes Ipython mec(), spawns tasks, 
    collect results, and finally generate plots.

    Adapted from ipython_main()
    """
    import datetime
    import time
    import cPickle
    try:
        from IPython.kernel import client
    except:
        pass

    mec = client.MultiEngineClient()
    mec.reset(targets=mec.get_ids()) # Reset the namespaces of all engines
    tc = client.TaskClient()

    mec_exec_str = """
import sys, os
import copy
sys.path.append(os.path.abspath('/global/home/users/dstarr/src/TCP/Software/ingest_tools'))
sys.path.append(os.path.abspath('/global/home/users/dstarr/src/TCP/Software/citris33'))
import test_pairwise_on_citris33_ipython
RTaskControllers = test_pairwise_on_citris33_ipython.R_Task_Controllers()"""

    print('before mec()')
    #print mec_exec_str
    #import pdb; pdb.set_trace()
    engine_ids = mec.get_ids()
    pending_result_dict = {}
    for engine_id in engine_ids:
        pending_result_dict[engine_id] = mec.execute(mec_exec_str, targets=[engine_id], block=False)
    n_pending = len(pending_result_dict)
    i_count = 0
    while n_pending > 0:
        still_pending_dict = {}
        for engine_id, pending_result in pending_result_dict.iteritems():
            try:
                result_val = pending_result.get_result(block=False)
            except:
                print("get_result() Except. Still pending on engine: %d" % (engine_id))
                still_pending_dict[engine_id] = pending_result
                result_val = None # 20110105 added
            if result_val is None:
                print("Still pending on engine: %d" % (engine_id))
                still_pending_dict[engine_id] = pending_result
        if i_count > 10:
            mec.clear_pending_results()
            pending_result_dict = {}
            mec.reset(targets=still_pending_dict.keys())
            for engine_id in still_pending_dict.keys():
                pending_result_dict[engine_id] = mec.execute(mec_exec_str, targets=[engine_id], block=False)
            ###
            time.sleep(20) # hack
            pending_result_dict = [] # hack
            ###
            i_count = 0
        else:
            print("sleeping...")
            time.sleep(5)
            pending_result_dict = still_pending_dict
        n_pending = len(pending_result_dict)
        i_count += 1

    print('after mec()')
    time.sleep(5) # This may be needed, although mec() seems to wait for all the Ipython clients to finish
    #print 'after sleep()'
    #import pdb; pdb.set_trace()
    task_id_list = []
    for classifier_name, classifier_dict in classifier_info_dicts.iteritems():
        fp = open(classifier_dict['srclist_fpath'], 'rb')
        temp_dict = cPickle.load(fp)
        fp.close()
        srcid_list = temp_dict['srcid_list']

        #import random
        #random.shuffle(srcid_list) # For Testing only:
        srcid_list_new = []
        #srcid_list_sdoradus = ['164015', '163676', '163566', '164082', '163764', '164084', '163781']
        #for srcid in srcid_list_sdoradus:
        #    if srcid in srcid_list:
        #        srcid_list_new.append(int(srcid) + 100000000)
        #for srcid in srcid_list[:5]:
        #    srcid_list_new.append(int(srcid) + 100000000)

        #for srcid in srcid_list:
        #for srcid in srcid_list[:200]:
        for srcid in srcid_list:
            srcid_list_new.append(int(srcid) + 100000000)

        srcid_list = srcid_list_new
        #print srcid_list
        #import pdb; pdb.set_trace()

        for a_iter in iter_list:
            for a_percent in percent_list:
                ##### FOR DEBUGGING:
                #test_RTaskControllers = R_Task_Controllers()
                #ipython_return_dict = test_RTaskControllers.R_non_ipython_main(pars, 
                #                            r_classifiers=[classifier_dict], 
                #                            classifier_name=classifier_name,
                #                            srcid_list=srcid_list,
                #                            percent_list=[a_percent],
                #                            iter_list=[a_iter],
                #                            rclass_name=classifier_dict['class_name'],
                #                            rdata_fpath=classifier_dict['rdata_fpath'])
                #import pdb; pdb.set_trace()
                #print
                #####
                tc_exec_str__oldworks = """ipython_return_dict = RTaskControllers.R_non_ipython_main(pars, 
                                            r_classifiers=r_classifiers, 
                                            classifier_name=classifier_name,
                                            srcid_list=srcid_list,
                                            percent_list=percent_list,
                                            iter_list=iter_list,
                                            rclass_name=class_name,
                                            rdata_fpath=rdata_fpath)"""

                ### 20110106: This doesn't seem to solve the ipcontroller memory error, but works:
                tc_exec_str = """ipython_return_dict_temp = RTaskControllers.R_non_ipython_main(pars, 
                                            r_classifiers=r_classifiers, 
                                            classifier_name=classifier_name,
                                            srcid_list=srcid_list,
                                            percent_list=percent_list,
                                            iter_list=iter_list,
                                            rclass_name=class_name,
                                            rdata_fpath=rdata_fpath)
ipython_return_dict = copy.deepcopy(ipython_return_dict_temp)
del ipython_return_dict_temp
del pars
del r_classifiers
del classifier_name
del srcid_list
del percent_list
del iter_list
del class_name
del rdata_fpath
"""
                taskid = tc.run(client.StringTask(tc_exec_str,
                                                  push={'pars':pars,
                                                        'r_classifiers':[classifier_dict],
                                                        'classifier_name':classifier_name,
                                                        'srcid_list':srcid_list,
                                                        'percent_list':[a_percent],
                                                        'iter_list':[a_iter],
                                                        'class_name':classifier_dict['class_name'],
                                                        'rdata_fpath':classifier_dict['rdata_fpath']},
                                                  pull='ipython_return_dict', 
                                                  retries=3))
                task_id_list.append(taskid)
    #import pdb; pdb.set_trace()
    ####
    combo_results_dict = {}
    while ((tc.queue_status()['scheduled'] > 0) or
           (tc.queue_status()['pending'] > 0)):
        tasks_to_pop = []
        for task_id in task_id_list:
            temp = tc.get_task_result(task_id, block=False)
            if temp is None:
                continue
            temp2 = temp.results
            if temp2 is None:
                continue
            results = temp2.get('ipython_return_dict',None)
            if results is None:
                continue # skip some kind of NULL result
            if len(results) > 0:
                tasks_to_pop.append(task_id)
                ipython_return_dict = results
                update_combo_results(combo_results_dict=combo_results_dict,
                                     ipython_return_dict=copy.deepcopy(ipython_return_dict))
        for task_id in tasks_to_pop:
            task_id_list.remove(task_id)
        print(tc.queue_status())
        print('Sleep... 20 in test_pairwise_on_citris33_ipython::master_ipython_R_classifiers()', datetime.datetime.utcnow())
        time.sleep(20)
    # IN CASE THERE are still tasks which have not been pulled/retrieved:
    for task_id in task_id_list:
        for task_id in task_id_list:
            temp = tc.get_task_result(task_id, block=False)
            if temp is None:
                continue
            temp2 = temp.results
            if temp2 is None:
                continue
            results = temp2.get('ipython_return_dict',None)
            if results is None:
                continue #skip some kind of NULL result
            if len(results) > 0:
                tasks_to_pop.append(task_id)
                ipython_return_dict = results
                update_combo_results(combo_results_dict=combo_results_dict,
                                     ipython_return_dict=copy.deepcopy(ipython_return_dict))
    ####
    return combo_results_dict



if __name__ == '__main__':

    from numpy import arange, array
    #perc_arr = array(list(arange(0.02, 0.7, 0.02)) + 
    #                  list(arange(0.7, 1.01, 0.01)))
    perc_arr = array(list(arange(0.2, 0.6, 0.01)))


    # TODO: specify xmls dirpath
    pars = {'src_id':deboss_srcid_list, #['148875', '148723', '148420', '149144', '149049'], #deboss_srcid_list,#['148875', '148723', '148420', '149144', '149049'], #deboss_srcid_list, #['149144', '149049', '149338', '149049', '149338','149182','149108'],
            'percent':[str(elem) for elem in perc_arr], #[str(elem) for elem in arange(0.90, 1.0, 0.01)], # [str(elem) for elem in arange(0.58, 1.0, 0.01)]#[str(elem) for elem in arange(0.01, 1.01, 0.01)], #[str(elem) for elem in arange(0.8, 1.0, 0.10)], #['0.8', '0.86', '0.88', '0.9', '0.95', '1.0'],
            'niters':'7', #'5', #'6',#'12', # Not a list, string value, will be used to generate list: range(niters)
            'pairwise_classifier_pkl_fpath':"/home/pteluser/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher/pairwise_classifier__debosscher_table3.pkl.gz", # This is just debosscher data
            'crossvalid_pairwise_classif_dirpath':'/global/home/users/dstarr/scratch/crossvalid/pairwise_scratch_20101109_4060nostratif_2qso', # NOTE: set to '' if want to do non-crossvalid-folded classifiers
            'taxonomy_prune_defs':{'terminating_classes':['mira', 'sreg', 'rv', 'dc', 'piic', 'cm', 'rr-ab', 'rr-c', 'rr-d', 'ds', 'lboo', 'bc', 'spb', 'gd', 'be', 'pvsg', 'CP', 'wr', 'tt', 'haebe', 'sdorad', 'ell', 'alg', 'bly', 'wu']},
            'plot_symb':['o','s','v','d','<'], # ,'+','x','.', ,'>','^'
            'feat_distrib_colors':['#000000',
                                   '#ff3366',
                                   '#660000',
                                   '#aa0000',
                                   '#ff0000',
                                   '#ff6600',
                                   '#996600',
                                   '#cc9900',
                                   '#ffff00',
                                   '#ffcc33',
                                   '#ffff99',
                                   '#99ff99',
                                   '#666600',
                                   '#99cc00',
                                   '#00cc00',
                                   '#006600',
                                   '#339966',
                                   '#33ff99',
                                   '#006666',
                                   '#66ffff',
                                   '#0066ff',
                                   '#0000cc',
                                   '#660099',
                                   '#993366',
                                   '#ff99ff',
                                   '#440044'],
            'R_class_lookup':{ \
                'X Ray Binary':'xrbin',
                'a. Mira':'mira',
                'b. Semireg PV':'sreg',
                'c. RV Tauri':'rv',
                'd. Classical Cepheid':'dc',
                'e. Pop. II Cepheid':'piic',
                'f. Multi. Mode Cepheid':'cm',
                'g. RR Lyrae, FM':'rr-ab',
                'h. RR Lyrae, FO':'rr-c',
                'i. RR Lyrae, DM':'rr-d',
                'j. Delta Scuti':'ds',
                'k. Lambda Bootis':'lboo',
                'l. Beta Cephei':'bc',
                'm. Slowly Puls. B':'spb',
                'n. Gamma Doradus':'gd',
                'o. Pulsating Be':'be',
                'p. Per. Var. SG':'pvsg',
                'q. Chem. Peculiar':'CP',
                'r. Wolf-Rayet':'wr',
                's. T Tauri':'tt',
                't. Herbig AE/BE':'haebe',
                'u. S Doradus':'sdorad',
                'v. Ellipsoidal':'ell',
                'w. Beta Persei':'alg',
                'x. Beta Lyrae':'bly',
                'y. W Ursae Maj.':'wu',
                },
            'R_class_lookup__old':{ \
                'X Ray Binary':'xrbin',
                'a. Mira':'mira',
                'b. semireg PV':'sreg',
                'c. RV Tauri':'rv',
                'd. Classical Cepheid':'dc',
                'e. Pop. II Cepheid':'piic',
                'f. Multi. Mode Cepheid':'cm',
                'g. RR Lyrae, FM':'rr-ab',
                'h. RR Lyrae, FO':'rr-c',
                'i. RR Lyrae, DM':'rr-d',
                'j. Delta Scuti':'ds',
                'k. Lambda Bootis':'lboo',
                'l. Beta Cephei':'bc',
                'm. Slowly Puls. B':'spb',
                'n. Gamma Doradus':'gd',
                'o. BE':'be',
                'p. Per. Var. SG':'pvsg',
                'q. Chem. Peculiar':'CP',
                'r. Wolf-Rayet':'wr',
                's. T Tauri':'tt',
                't. Herbig AE/BE':'haebe',
                'u. S Doradus':'sdorad',
                'v. Ellipsoidal':'ell',
                'w. Beta Persei':'alg',
                'x. Beta Lyrae':'bly',
                'y. W Ursae Maj.':'wu',
                },
            }
    # 'srcid':[],
    # 'percent'[]
    options = parse_options()
    if options.srcid != '':
        pars['src_id'] = options.srcid
    if options.percent != '':
        pars['percent'] = options.percent
    if options.niters != '':
        pars['niters'] = options.niters
    if options.pairwise_classifier_pkl_fpath != '':
        pars['pairwise_classifier_pkl_fpath'] = os.path.expandvars(options.pairwise_classifier_pkl_fpath)
    if options.use_hardcoded_sciclass_lookup == True:
        pars['sciclass_lookup'] = sciclass_lookup
    pars['num_percent_epoch_error_iterations'] = int(pars['niters'])



    ### TODO: this extra loop will have to be impleemented in the ipython-version:
    if len(pars.get('crossvalid_pairwise_classif_dirpath','')) > 0:
        dir_names = os.listdir(pars['crossvalid_pairwise_classif_dirpath'])
        pwiseclass_id_pklfpath = {}
        for dirname in dir_names:
            if not 'node_' in dirname:
                continue
            # TODO: do  the full node_5... string repace
            pwiseclass_id_pklfpath[dirname] = {'pairwise_classifier_pkl_fpath': \
                                                    "%s/%s/pairwise_classifier.pkl.gz" % ( \
                                                     pars['crossvalid_pairwise_classif_dirpath'], dirname),
                                               'pair_path_replace_tup':('/media/raid_0/pairwise_scratch',
                                                                    pars['crossvalid_pairwise_classif_dirpath'])}

            
    else:
        pwiseclass_id_pklfpath = {'only_one':{'pairwise_classifier_pkl_fpath': \
                                                      pars['pairwise_classifier_pkl_fpath'],
                                              'pair_path_replace_tup':('/home/pteluser','/global/home/users/dstarr')}}



    ### KLUDGE: this needs to be done in non-ipython case:
    pars['niters'] = range(int(pars['niters']))
    ###

    (srcid_list, percent_list, niters) = massage_types(src_id=pars['src_id'], percent=pars['percent'], niters=pars['niters'])

    ########## These R classifiers are created using: rpy2_classifiers.py:__main__()
    #classifier_info_dicts = {'rf_clfr':{'class_name':'rf_clfr',
    #                                    'rdata_fpath':os.path.expandvars("$HOME/scratch/test_RF_classifier.rdata")}}
    classifier_info_dicts = {}
    for i_classifier in range(10):
        classifier_name = 'rf_%d' % (i_classifier)
        classifier_info_dicts[classifier_name] = {'class_name':'rf_clfr',### the classifier name used in the .rdata file
                                               'rdata_fpath':os.path.expandvars( 
                                                  "$HOME/scratch/classifier_deboss_RF_%d.rdata" % (i_classifier)),
                                               'srclist_fpath':os.path.expandvars(  
                                               "$HOME/scratch/classifier_deboss_RF_%d.srcs.pkl" % (i_classifier)),
                                               }

    if 0:
        ### Just for combining result .pkls to generate a final plot:

        combo_results_dict = {}
        perc_plot_result = cPickle.load(gzip.open('/global/home/users/dstarr/scratch/perc_plot_results__20110105_0to20at1_7set.pkl.gz'))
        update_combo_results(combo_results_dict=combo_results_dict,
                                 ipython_return_dict=perc_plot_result)

        perc_plot_result = cPickle.load(gzip.open('/global/home/users/dstarr/scratch/perc_plot_results__20110105_20to60at1_7set.pkl.gz'))
        update_combo_results(combo_results_dict=combo_results_dict,
                                 ipython_return_dict=perc_plot_result)


        perc_plot_result = cPickle.load(gzip.open('/global/home/users/dstarr/scratch/perc_plot_results__20110105_60to100at1_7set.pkl.gz'))
        update_combo_results(combo_results_dict=combo_results_dict,
                                 ipython_return_dict=perc_plot_result)


        from pairwise_classification import Weka_Pairwise_Classification
        WekaPairwiseClassification = Weka_Pairwise_Classification(pars=pars)
        #import pdb; pdb.set_trace()

        percent_plot_local_fpath = os.path.expandvars('$HOME/scratch/R_xmls_deboss_percentage_exclude.ps')
        #import pdb; pdb.set_trace()
        WekaPairwiseClassification.plot_percent_tally_summary_dict(combo_results_dict,
                                     img_fpath=percent_plot_local_fpath)

        sys.exit()

    if 1:
        ### 2011-01-11 Used for normal citris33 parallel run
        ### Ipython-parallel R-classifier mode:
        combo_results_dict = master_ipython_R_classifiers(pars=pars,
                                                          classifier_info_dicts=classifier_info_dicts, 
                                                          percent_list=percent_list,
                                                          iter_list=niters)
    else:
        ### Single-mode R-classifier mode (for testing / debugging):
        combo_results_dict = {}
        ### Here we task off classifiers, sets, percentages to different nodes.
        for classifier_name, classifier_dict in classifier_info_dicts.iteritems():
            ### Can do the following on a seperate Ipython engine... just break up the lists:
            ### - I think these should be done for a single percentage and classifier
            RTaskControllers = R_Task_Controllers()
            #r_classifiers = [r_classifier] # I want the next function to be able to use several classifiers

            if 'srclist_fpath' in classifier_dict:
                import cPickle
                fp = open(classifier_dict['srclist_fpath'], 'rb')
                temp_dict = cPickle.load(fp)
                fp.close()
                srcid_list = temp_dict['srcid_list']

            ##### 
            #import random
            #random.shuffle(srcid_list) # For Testing only:
            srcid_list_new = []
            #srcid_list_sdoradus = ['164015', '163676', '163566', '164082', '163764', '164084', '163781']
            for srcid in srcid_list:
                srcid_list_new.append(int(srcid) + 100000000)
            srcid_list = srcid_list_new
            #####

            ipython_return_dict = RTaskControllers.R_non_ipython_main(pars, 
                                                r_classifiers=[classifier_dict], 
                                                classifier_name=classifier_name,
                                                srcid_list=srcid_list,
                                                percent_list=percent_list,
                                                iter_list=niters,
                                                rclass_name=classifier_dict['class_name'],
                                                rdata_fpath=classifier_dict['rdata_fpath'])

            update_combo_results(combo_results_dict=combo_results_dict,
                                 ipython_return_dict=ipython_return_dict)
                             

    import cPickle
    import gzip
    results_pkl_fpath = os.path.expandvars("$HOME/scratch/perc_plot_results.pkl.gz")
    if os.path.exists(results_pkl_fpath):
        os.system('rm ' + results_pkl_fpath)
    fp = gzip.open(results_pkl_fpath, 'wb')
    cPickle.dump(combo_results_dict, fp, 1)
    fp.close()
    
    # # # TODO: I may want to abstrat plot_percent_tally_summary_dict() out of 
    #         Weka_Pairwise_classification if JPype and other things are loaded...
    from pairwise_classification import Weka_Pairwise_Classification
    WekaPairwiseClassification = Weka_Pairwise_Classification(pars=pars)
    #import pdb; pdb.set_trace()

    percent_plot_local_fpath = os.path.expandvars('$HOME/scratch/R_xmls_deboss_percentage_exclude.ps')
    #import pdb; pdb.set_trace()
    WekaPairwiseClassification.plot_percent_tally_summary_dict(combo_results_dict,
                                 img_fpath=percent_plot_local_fpath)

    #os.system('cp %s /home/pteluser/Dropbox/work/' % (percent_plot_local_fpath))
    import datetime
    print(datetime.datetime.now())

    import pdb; pdb.set_trace()
    print()

    print("EXITING...")
    sys.exit()


    non_ipython_main(pars, pwiseclass_id_pklfpath=pwiseclass_id_pklfpath) # For Testing / Debugging
    ## #  # ipython_main(pars, pwiseclass_id_pklfpath=pwiseclass_id_pklfpath, apply_classifier_to_all_srcids=False)
    
    ##### Only for testing arff_string without ipython:
    
    rcp = Resample_Pairwise_Classify(pars=pars)
    #(srcid_list, percent_list, niters) = massage_types(src_id='149384', percent='0.9', niters='2')
    #arff_str = get_perc_subset(srcid_list, percent_list, niters)
    #arff_str = rcp.get_perc_subset([100148276, 100148555, 100148834, 100149113, 100149384,100148220, 100148499, 100148778, 100149057, 100149336], [0.9], [2])
    arff_str = get_perc_subset([100148276, 100148555], [0.7, 0.9], [2])
    import pdb; pdb.set_trace()
    print(arff_str)
    ##### Only needed for old weka pairwise classifier:
    #arff_sciclass_dict = rcp.PairwiseClassification.parse_arff(has_srcid=True,
    #                                                                arff_str=arff_str,
    #                                                                write_pkl=False)
    #perc_niter_sciclassdict = rcp.organize_sciclassdict_by_percent_niters(arff_sciclass_dict)

