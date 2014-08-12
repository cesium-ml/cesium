#!/usr/bin/env python
"""
Adapted from test_pairwise_on_citris33_ipython.py

./arff_generation_master.py
scp -P 10322 ~/scratch/out.arff pteluser@lyra.berkeley.edu:/tmp/citris33_asas.arff

"""
import sys, os
import cPickle
import time
import gzip
import copy
import glob
import matplotlib
matplotlib.use('agg') # just needed for lightcurve.py::lomb_code() PSD.png plotting without X11

from optparse import OptionParser

sys.path.append(os.path.abspath(os.environ.get('TCP_DIR') + 'Software/ingest_tools'))

sciclass_lookup = {'classid_shortname': {0L: '_varstar_',
                       1L: 'GCVS',
                       2L: 'Eruptive',
                       3L: 'FU',
                       4L: 'GCAS',
                       5L: 'I',
                       6L: 'IA',
                       7L: 'IB',
                       8L: 'IN',
                       9L: 'INA',
                       10L: 'INB',
                       11L: 'INT',
                       12L: 'IN(YY)',
                       13L: 'IS',
                       14L: 'ISA',
                       16L: 'ISB',
                       17L: 'RCB',
                       18L: 'RS',
                       19L: 'SDOR',
                       20L: 'UV',
                       21L: 'UVN',
                       22L: 'WR',
                       23L: 'Pulsating',
                       24L: 'ACYG',
                       25L: 'BCEP',
                       26L: 'BCEPS',
                       27L: 'CEP',
                       28L: 'CEP(B)',
                       29L: 'CW',
                       30L: 'CWA',
                       31L: 'CWB',
                       32L: 'DCEP',
                       33L: 'DCEPS',
                       34L: 'DSCT',
                       35L: 'DSCTC',
                       36L: 'L',
                       37L: 'LB',
                       38L: 'LC',
                       39L: 'M',
                       40L: 'PVTEL',
                       41L: 'RR',
                       42L: 'RR(B)',
                       43L: 'RRAB',
                       44L: 'RRC',
                       45L: 'RV',
                       46L: 'RVA',
                       47L: 'RVB',
                       48L: 'SR',
                       49L: 'SRA',
                       50L: 'SRB',
                       51L: 'SRC',
                       52L: 'SRD',
                       53L: 'SXPHE',
                       54L: 'ZZ',
                       55L: 'ZZA',
                       56L: 'ZZB',
                       57L: 'Rotating',
                       58L: 'ACV',
                       59L: 'ACVO',
                       60L: 'BY',
                       61L: 'ELL',
                       62L: 'FKCOM',
                       63L: 'PSR',
                       64L: 'SXARI',
                       65L: 'Cataclysmic',
                       66L: 'N',
                       67L: 'NA',
                       68L: 'NB',
                       69L: 'NC',
                       70L: 'NL',
                       71L: 'NR',
                       72L: 'SN',
                       73L: 'SNI',
                       74L: 'SNII',
                       75L: 'UG',
                       76L: 'UGSS',
                       77L: 'UGSU',
                       78L: 'UGZ',
                       79L: 'ZAND',
                       80L: 'Eclipsing',
                       82L: 'E',
                       83L: 'EA',
                       84L: 'EB',
                       85L: 'EW',
                       86L: 'GS',
                       87L: 'PN',
                       88L: 'RS',
                       89L: 'WD',
                       90L: 'WR(1)',
                       91L: 'AR',
                       92L: 'D',
                       93L: 'DM',
                       94L: 'DS',
                       95L: 'DW',
                       96L: 'K',
                       97L: 'KE',
                       98L: 'KW',
                       99L: 'SD',
                       100L: 'SNIa',
                       101L: 'SNIb',
                       102L: 'SNIc',
                       103L: 'SNIIP',
                       104L: 'SNIIN',
                       105L: 'SNIIL',
                       106L: 'SNIa-sc',
                       107L: 'Nonstellar',
                       109L: 'GalNuclei',
                       110L: 'AGN',
                       111L: 'TDE',
                       112L: 'DrkMatterA',
                       113L: 'GRB',
                       114L: 'SHB',
                       115L: 'LSB',
                       116L: 'SGR',
                       117L: 'X',
                       118L: 'XB',
                       119L: 'XF',
                       120L: 'XI',
                       121L: 'XJ',
                       122L: 'XND',
                       123L: 'XNG',
                       124L: 'XP',
                       125L: 'XPR',
                       126L: 'XPRM',
                       127L: 'XRM',
                       128L: 'ZZO',
                       129L: 'NEW',
                       130L: 'AM',
                       131L: 'R',
                       132L: 'BE',
                       133L: 'EP',
                       134L: 'SRS',
                       135L: 'GDOR',
                       136L: 'RPHS',
                       137L: 'LPB',
                       138L: 'BLBOO',
                       139L: 'BL-Lac',
                       140L: 'RRcl',
                       141L: 'RRe',
                       142L: 'SNIa-pec',
                       143L: 'SNIc-pec',
                       145L: 'ML',
                       149L: 'UXUma',
                       150L: 'Polars',
                       151L: 'DQ',
                       152L: 'EWa',
                       153L: 'EWs',
                       154L: 'vs',
                       157L: 'cv',
                       158L: 'nov',
                       159L: 'cn',
                       160L: 'n-l',
                       161L: 'sw',
                       162L: 'vy',
                       163L: 'ux',
                       164L: 'amcvn',
                       165L: 'p',
                       166L: 'am',
                       167L: 'dqh',
                       168L: 'ug',
                       169L: 'su',
                       170L: 'er',
                       171L: 'wz',
                       172L: 'zc',
                       173L: 'ssc',
                       174L: 'rn',
                       175L: 'sv',
                       176L: 'grb',
                       177L: 'lgrb',
                       178L: 'sgrb',
                       179L: 'srgrb',
                       180L: 'sne',
                       181L: 'cc',
                       182L: 'tia',
                       183L: 'tib',
                       184L: 'tic',
                       185L: 'tsnii',
                       186L: 'pi',
                       187L: 'tsni',
                       188L: 'ev',
                       189L: 'rscvn',
                       190L: 'uv',
                       191L: 'sdorad',
                       192L: 'wr',
                       193L: 'gc',
                       194L: 'fuor',
                       195L: 'ov',
                       196L: 'rcb',
                       197L: 'haebe',
                       198L: 'be',
                       199L: 'shs',
                       200L: 'tt',
                       201L: 'ttc',
                       202L: 'ttw',
                       203L: 'puls',
                       204L: 'gd',
                       205L: 'sx',
                       206L: 'rr-lyr',
                       207L: 'ac',
                       208L: 'mira',
                       209L: 'pwd',
                       211L: 'ds',
                       212L: 'pvt',
                       213L: 'bc',
                       214L: 'sreg',
                       215L: 'rv',
                       216L: 'piic',
                       217L: 'c',
                       218L: 'rr-ab',
                       219L: 'rr-c',
                       220L: 'rr-d',
                       221L: 'rr-e',
                       222L: 'rr-cl',
                       223L: 'zz',
                       224L: 'zzh',
                       225L: 'zzhe',
                       226L: 'zzheii',
                       227L: 'gw',
                       228L: 'sr-a',
                       229L: 'sr-b',
                       230L: 'sr-c',
                       231L: 'sr-d',
                       232L: 'rvc',
                       233L: 'rvv',
                       234L: 'bl',
                       235L: 'wv',
                       236L: 'ca',
                       237L: 'cm',
                       238L: 'dc',
                       239L: 'sdc',
                       240L: 'rot',
                       241L: 'sxari',
                       242L: 'aii',
                       243L: 'fk',
                       244L: 'plsr',
                       245L: 'by',
                       246L: 'ell',
                       247L: 'msv',
                       248L: 'b',
                       249L: 'iii',
                       250L: 'xrb',
                       251L: 'bly',
                       252L: 'wu',
                       253L: 'alg',
                       254L: 'psys',
                       255L: 'SSO',
                       256L: 'BLZ',
                       257L: 'OVV',
                       258L: 'dsm',
                       259L: 'lamb',
                       260L: 'xrbin',
                       261L: 'lboo',
                       262L: 'qso',
                       263L: 'seyf',
                       265L: 'fsrq',
                       266L: 'iin',
                       267L: 'hae',
                       268L: 'tiapec',
                       269L: 'tiasc',
                       270L: 'iil',
                       271L: 'iip',
                       272L: 'iib',
                       273L: 'ticpec',
                       274L: 'maser',
                       275L: 'moving',
                       276L: 'ast',
                       277L: 'comet',
                       278L: 'hpm',
                       279L: 'eclipsing',
                       280L: 'k',
                       281L: 'd',
                       282L: 'sd',
                       283L: 'unclass',
                       284L: 'pvsg',
                       285L: 'cp',
                       286L: 'spb',
                       287L: 'sdbv',
                       1000000L: 'Chemically Peculiar Stars'},
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
 'shortname_nsrcs': {'ACV': 0L,
                     'ACVO': 0L,
                     'ACYG': 0L,
                     'AGN': 57L,
                     'AM': 0L,
                     'AR': 0L,
                     'BCEP': 0L,
                     'BCEPS': 0L,
                     'BE': 0L,
                     'BL-Lac': 46L,
                     'BLBOO': 0L,
                     'BLZ': 24L,
                     'BY': 0L,
                     'CEP': 5L,
                     'CEP(B)': 0L,
                     'CP': 0,
                     'CW': 0L,
                     'CWA': 0L,
                     'CWB': 0L,
                     'Cataclysmic': 0L,
                     'Chemically Peculiar Stars': 0L,
                     'D': 2L,
                     'DCEP': 0L,
                     'DCEPS': 0L,
                     'DM': 0L,
                     'DQ': 0L,
                     'DS': 0L,
                     'DSCT': 149L,
                     'DSCTC': 0L,
                     'DW': 0L,
                     'DrkMatterA': 0L,
                     'E': 3L,
                     'EA': 260L,
                     'EB': 67L,
                     'ELL': 0L,
                     'EP': 0L,
                     'EW': 891L,
                     'EWa': 0L,
                     'EWs': 0L,
                     'Eclipsing': 0L,
                     'Eruptive': 0L,
                     'FKCOM': 0L,
                     'FU': 0L,
                     'GCAS': 0L,
                     'GCVS': 712L,
                     'GDOR': 15L,
                     'GRB': 0L,
                     'GS': 0L,
                     'GalNuclei': 0L,
                     'I': 0L,
                     'IA': 0L,
                     'IB': 0L,
                     'IN': 0L,
                     'IN(YY)': 0L,
                     'INA': 0L,
                     'INB': 0L,
                     'INT': 0L,
                     'IS': 0L,
                     'ISA': 0L,
                     'ISB': 0L,
                     'K': 0L,
                     'KE': 0L,
                     'KW': 0L,
                     'L': 0L,
                     'LB': 0L,
                     'LC': 1L,
                     'LPB': 1L,
                     'LSB': 0L,
                     'M': 11L,
                     'ML': 658L,
                     'N': 1L,
                     'NA': 0L,
                     'NB': 0L,
                     'NC': 0L,
                     'NEW': 0L,
                     'NL': 3L,
                     'NR': 0L,
                     'Nonstellar': 0L,
                     'OVV': 0L,
                     'PN': 0L,
                     'PSR': 0L,
                     'PVTEL': 0L,
                     'Polars': 0L,
                     'Pulsating': 1L,
                     'R': 0L,
                     'RCB': 0L,
                     'RPHS': 0L,
                     'RR': 9L,
                     'RR(B)': 0L,
                     'RRAB': 31L,
                     'RRC': 15L,
                     'RRcl': 0L,
                     'RRe': 0L,
                     'RS': 0L,
                     'RV': 0L,
                     'RVA': 0L,
                     'RVB': 0L,
                     'Rotating': 0L,
                     'SD': 0L,
                     'SDOR': 0L,
                     'SGR': 0L,
                     'SHB': 0L,
                     'SN': 0L,
                     'SNI': 0L,
                     'SNII': 0L,
                     'SNIIL': 0L,
                     'SNIIN': 1L,
                     'SNIIP': 0L,
                     'SNIa': 0L,
                     'SNIa-pec': 0L,
                     'SNIa-sc': 0L,
                     'SNIb': 0L,
                     'SNIc': 0L,
                     'SNIc-pec': 0L,
                     'SR': 0L,
                     'SRA': 0L,
                     'SRB': 0L,
                     'SRC': 0L,
                     'SRD': 0L,
                     'SRS': 14L,
                     'SSO': 0L,
                     'SXARI': 0L,
                     'SXPHE': 7L,
                     'TDE': 0L,
                     'UG': 3L,
                     'UGSS': 0L,
                     'UGSU': 0L,
                     'UGZ': 1L,
                     'UV': 0L,
                     'UVN': 0L,
                     'UXUma': 0L,
                     'WD': 0L,
                     'WR': 173L,
                     'WR(1)': 0L,
                     'X': 0L,
                     'XB': 0L,
                     'XF': 0L,
                     'XI': 0L,
                     'XJ': 0L,
                     'XND': 0L,
                     'XNG': 0L,
                     'XP': 0L,
                     'XPR': 0L,
                     'XPRM': 0L,
                     'XRM': 0L,
                     'ZAND': 0L,
                     'ZZ': 0L,
                     'ZZA': 0L,
                     'ZZB': 0L,
                     'ZZO': 0L,
                     '_varstar_': 0,
                     'ac': 0L,
                     'aii': 81L,
                     'alg': 732L,
                     'am': 5L,
                     'amcvn': 0L,
                     'ast': 93L,
                     'b': 53L,
                     'bc': 84L,
                     'be': 47L,
                     'bl': 14L,
                     'bly': 403L,
                     'by': 0L,
                     'c': 329L,
                     'ca': 7L,
                     'cc': 58L,
                     'cm': 202L,
                     'cn': 1L,
                     'comet': 3L,
                     'cp': 49L,
                     'cv': 193L,
                     'd': 2270L,
                     'dc': 865L,
                     'dqh': 5L,
                     'ds': 845L,
                     'dsm': 1L,
                     'eclipsing': 2934L,
                     'ell': 17L,
                     'er': 0L,
                     'ev': 0L,
                     'fk': 1L,
                     'fsrq': 3L,
                     'fuor': 4L,
                     'gc': 0L,
                     'gd': 73L,
                     'grb': 0L,
                     'gw': 2L,
                     'hae': 1L,
                     'haebe': 28L,
                     'hpm': 4L,
                     'iib': 27L,
                     'iii': 0L,
                     'iil': 0L,
                     'iin': 111L,
                     'iip': 74L,
                     'k': 2758L,
                     'lamb': 1L,
                     'lboo': 26L,
                     'lgrb': 1L,
                     'maser': 1L,
                     'mira': 3048L,
                     'moving': 0L,
                     'msv': 0L,
                     'n-l': 3L,
                     'nov': 3L,
                     'ov': 0L,
                     'p': 0L,
                     'pi': 0L,
                     'piic': 41L,
                     'plsr': 0L,
                     'psys': 3L,
                     'puls': 250L,
                     'pvsg': 0L,
                     'pvt': 0L,
                     'pwd': 3L,
                     'qso': 6307L,
                     'rcb': 2L,
                     'rn': 0L,
                     'rot': 4L,
                     'rr-ab': 1706L,
                     'rr-c': 452L,
                     'rr-cl': 13L,
                     'rr-d': 168L,
                     'rr-e': 0L,
                     'rr-lyr': 16L,
                     'rscvn': 1L,
                     'rv': 11L,
                     'rvc': 1L,
                     'rvv': 0L,
                     'sd': 879L,
                     'sdbv': 0L,
                     'sdc': 53L,
                     'sdorad': 21L,
                     'seyf': 0L,
                     'sgrb': 0L,
                     'shs': 0L,
                     'sne': 619L,
                     'spb': 0L,
                     'sr-a': 2L,
                     'sr-b': 2L,
                     'sr-c': 2L,
                     'sr-d': 3L,
                     'sreg': 76L,
                     'srgrb': 0L,
                     'ssc': 3L,
                     'su': 3L,
                     'sv': 0L,
                     'sw': 1L,
                     'sx': 28L,
                     'sxari': 0L,
                     'tia': 2176L,
                     'tiapec': 35L,
                     'tiasc': 0L,
                     'tib': 68L,
                     'tic': 124L,
                     'ticpec': 5L,
                     'tsni': 48L,
                     'tsnii': 749L,
                     'tt': 32L,
                     'ttc': 2L,
                     'ttw': 0L,
                     'ug': 3L,
                     'unclass': 61200L,
                     'uv': 0L,
                     'ux': 2L,
                     'vs': 774L,
                     'vy': 1L,
                     'wr': 219L,
                     'wu': 1075L,
                     'wv': 35L,
                     'wz': 0L,
                     'xrb': 0L,
                     'xrbin': 14L,
                     'zc': 3L,
                     'zz': 0L,
                     'zzh': 0L,
                     'zzhe': 0L,
                     'zzheii': 0L},
 'shortname_parent_id': {'ACVO': 58L,
                         'AGN': 109L,
                         'AR': 80L,
                         'BCEPS': 25L,
                         'BL-Lac': 256L,
                         'BLZ': 110L,
                         'CP': 0L,
                         'CW': 23L,
                         'CWA': 29L,
                         'CWB': 29L,
                         'D': 80L,
                         'DCEP': 23L,
                         'DCEPS': 32L,
                         'DM': 92L,
                         'DS': 92L,
                         'DSCTC': 34L,
                         'DrkMatterA': 107L,
                         'E': 80L,
                         'ELL': 57L,
                         'EP': 129L,
                         'EWa': 85L,
                         'EWs': 85L,
                         'Eclipsing': 1L,
                         'GS': 80L,
                         'GalNuclei': 107L,
                         'I': 2L,
                         'IA': 2L,
                         'IB': 2L,
                         'IN(YY)': 8L,
                         'INA': 8L,
                         'INB': 8L,
                         'IS': 2L,
                         'ISA': 2L,
                         'ISB': 13L,
                         'K': 80L,
                         'KE': 96L,
                         'KW': 96L,
                         'L': 23L,
                         'LB': 36L,
                         'LC': 36L,
                         'LPB': 129L,
                         'ML': 107L,
                         'NA': 66L,
                         'NB': 66L,
                         'NC': 66L,
                         'NEW': 1L,
                         'Nonstellar': 0L,
                         'OVV': 256L,
                         'PN': 80L,
                         'PSR': 57L,
                         'R': 129L,
                         'RPHS': 129L,
                         'RR(B)': 41L,
                         'RRAB': 41L,
                         'RRC': 41L,
                         'SD': 80L,
                         'SNIc-pec': 102L,
                         'SRA': 48L,
                         'SRB': 48L,
                         'SRC': 48L,
                         'SRD': 48L,
                         'SRS': 129L,
                         'SSO': 107L,
                         'TDE': 109L,
                         'UVN': 2L,
                         'WD': 80L,
                         'WR(1)': 80L,
                         'X': 1L,
                         'XF': 117L,
                         'XI': 117L,
                         'XJ': 117L,
                         'XND': 117L,
                         'XNG': 117L,
                         'XP': 117L,
                         'XPR': 124L,
                         'XPRM': 124L,
                         'XRM': 124L,
                         'ac': 203L,
                         'aii': 240L,
                         'alg': 248L,
                         'am': 165L,
                         'amcvn': 160L,
                         'ast': 275L,
                         'b': 247L,
                         'bc': 203L,
                         'be': 193L,
                         'bl': 216L,
                         'bly': 248L,
                         'by': 240L,
                         'c': 203L,
                         'ca': 217L,
                         'cc': 180L,
                         'cm': 217L,
                         'cn': 158L,
                         'comet': 275L,
                         'cp': 154L,
                         'cv': 154L,
                         'd': 279L,
                         'dc': 217L,
                         'dqh': 165L,
                         'ds': 203L,
                         'dsm': 211L,
                         'eclipsing': 154L,
                         'ell': 240L,
                         'er': 169L,
                         'ev': 154L,
                         'fk': 240L,
                         'fsrq': 256L,
                         'fuor': 195L,
                         'gc': 188L,
                         'gd': 203L,
                         'grb': 157L,
                         'gw': 209L,
                         'hae': 197L,
                         'haebe': 188L,
                         'hpm': 275L,
                         'iib': 185L,
                         'iii': 247L,
                         'iil': 185L,
                         'iin': 185L,
                         'iip': 185L,
                         'k': 279L,
                         'lamb': 198L,
                         'lboo': 203L,
                         'lgrb': 176L,
                         'maser': 107L,
                         'mira': 203L,
                         'moving': 0L,
                         'msv': 154L,
                         'n-l': 158L,
                         'nov': 157L,
                         'ov': 188L,
                         'p': 158L,
                         'pi': 181L,
                         'piic': 203L,
                         'plsr': 240L,
                         'psys': 248L,
                         'puls': 154L,
                         'pvsg': 154L,
                         'pvt': 203L,
                         'pwd': 203L,
                         'qso': 110L,
                         'rcb': 188L,
                         'rn': 158L,
                         'rot': 154L,
                         'rr-ab': 206L,
                         'rr-c': 206L,
                         'rr-cl': 206L,
                         'rr-d': 206L,
                         'rr-e': 206L,
                         'rr-lyr': 203L,
                         'rscvn': 188L,
                         'rv': 203L,
                         'rvc': 215L,
                         'rvv': 215L,
                         'sd': 279L,
                         'sdbv': 203L,
                         'sdc': 238L,
                         'sdorad': 188L,
                         'seyf': 110L,
                         'sgrb': 176L,
                         'shs': 193L,
                         'sne': 157L,
                         'spb': 203L,
                         'sr-a': 214L,
                         'sr-b': 214L,
                         'sr-c': 214L,
                         'sr-d': 214L,
                         'sreg': 203L,
                         'srgrb': 176L,
                         'ssc': 168L,
                         'su': 168L,
                         'sv': 157L,
                         'sw': 160L,
                         'sx': 203L,
                         'sxari': 240L,
                         'tia': 180L,
                         'tiapec': 182L,
                         'tiasc': 182L,
                         'tib': 181L,
                         'tic': 181L,
                         'ticpec': 184L,
                         'tsni': 180L,
                         'tsnii': 181L,
                         'tt': 195L,
                         'ttc': 200L,
                         'ttw': 200L,
                         'ug': 158L,
                         'unclass': 154L,
                         'uv': 188L,
                         'ux': 160L,
                         'vs': 0L,
                         'vy': 160L,
                         'wr': 188L,
                         'wu': 248L,
                         'wv': 216L,
                         'wz': 169L,
                         'xrb': 260L,
                         'xrbin': 248L,
                         'zc': 168L,
                         'zz': 209L,
                         'zzh': 223L,
                         'zzhe': 223L,
                         'zzheii': 223L},
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


head_str = """<?xml version="1.0"?>
<VOSOURCE version="0.04">
	<COOSYS ID="J2000" equinox="J2000." epoch="J2000." system="eq_FK5"/>
  <history>
    <created datetime="2009-12-02 20:56:18.880560" codebase="db_importer.pyc" codebase_version="9-Aug-2007"/>
  </history>
  <ID>6930531</ID>
  <WhereWhen>
    <Description>Best positional information of the source</Description>
    <Position2D unit="deg">
      <Value2>
        <c1>323.47114731</c1>
        <c2>-0.79916734036</c2>
      </Value2>
      <Error2>
        <c1>0.000277777777778</c1>
        <c2>0.000277777777778</c2>
      </Error2>
    </Position2D>
  </WhereWhen>
  <VOTimeseries version="0.04">
    <TIMESYS>
			<TimeType ucd="frame.time.system?">MJD</TimeType> 
			<TimeZero ucd="frame.time.zero">0.0 </TimeZero>
			<TimeSystem ucd="frame.time.scale">UTC</TimeSystem> 
			<TimeRefPos ucd="pos;frame.time">TOPOCENTER</TimeRefPos>
		</TIMESYS>

    <Resource name="db photometry">
        <TABLE name="v">
          <FIELD name="t" ID="col1" system="TIMESYS" datatype="float" unit="day"/>
          <FIELD name="m" ID="col2" ucd="phot.mag;em.opt.v" datatype="float" unit="mag"/>
          <FIELD name="m_err" ID="col3" ucd="stat.error;phot.mag;em.opt.v" datatype="float" unit="mag"/>
          <DATA>
            <TABLEDATA>
"""

tail_str = """              </TABLEDATA>
            </DATA>
          </TABLE>
        </Resource>
      </VOTimeseries>
</VOSOURCE>"""



def generate_xml_str_using_lsd_ts(dat_fpath):
    """ Adapted from format_csv_getfeats.py
    For converting Ben's generated RRLyrae/eclips lightcurve .dat files

    """
    import csv

    data_str_list = []

    rows = csv.reader(open(dat_fpath), delimiter=' ')
    
    t_list = []
    m_list = []
    merr_list = []
    for i,row in enumerate(rows):
        t = float(row[0])
        m = float(row[1])
        m_err = float(row[2])
        data_str = '              <TR row="%d"><TD>%lf</TD><TD>%lf</TD><TD>%lf</TD></TR>' % \
                                  (i, t, m, m_err)
        data_str_list.append(data_str)
        t_list.append(t)
        m_list.append(m)
        merr_list.append(m_err)

    all_data_str = '\n'.join(data_str_list)

    out_xml = head_str + all_data_str + tail_str

    return out_xml


def get_perc_subset(srcid_list=[], percent_list=[], niters=1, xml_dirpath='', include_header=True, 
                    write_multiinfo_srcids=True, source_xml_dict={}, ParseNomadColorsList=None, use_mtmerr_ts_files=False, do_sigmaclip=True):
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
    import cStringIO
    sys.path.append(os.environ.get('TCP_DIR') + '/Software/feature_extract/MLData')
    #sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + '/Software/feature_extract/Code/extractors'))
    #print os.environ.get("TCP_DIR")
    #import mlens3
    import arffify

    sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                  'Software/feature_extract/Code'))
    import db_importer
    from data_cleaning import sigmaclip_sdict_ts
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

        if use_mtmerr_ts_files:
            ### Then we want to generate some pseudo XML using the timeseries column file (with lines like: "55243.43624000 19.36500000 ......")
            new_xml_str = generate_xml_str_using_lsd_ts(source_xml_dict[src_id])
        else:

            #20120130#tutor_src_id = src_id - 100000000
            tutor_src_id = src_id
            if len(source_xml_dict) > 0:
                #20120130#xml_fpath = source_xml_dict[str(tutor_src_id)]
                xml_fpath = source_xml_dict[tutor_src_id]
            else:
                xml_fpath = os.path.expandvars("%s/%d.xml" % (xml_dirpath, src_id))

            xml_str = open(xml_fpath).read()
            new_xml_str = ParseNomadColorsList.get_colors_for_srcid(xml_str=xml_str, srcid=tutor_src_id - 100000000) #, srcid=tutor_src_id)

        signals_list = []
        gen_orig = generators_importers.from_xml(signals_list)
        gen_orig.signalgen = {}
        gen_orig.sig = db_importer.Source(xml_handle=new_xml_str, doplot=False, make_xml_if_given_dict=True)
        gen_orig.sdict = gen_orig.sig.x_sdict
        gen_orig.set_outputs() # this adds/fills self.signalgen[<filters>,multiband]{'input':{filled},'features':{empty},'inter':{empty}}

        signals_list_temp = []
        #import pdb; pdb.set_trace()
        #print

        if do_sigmaclip:
            try:
                ### Do some sigma clipping (Ex: for ASAS data)
                sigmaclip_sdict_ts(gen_orig.sig.x_sdict['ts'], sigma_low=4.0, sigma_high=4.0)
            except:
                continue # probably doesnt have a gen_orig.sig.x_sdict['ts'][<band>]['m']

        gen_temp = copy.deepcopy(gen_orig)
        for perc in percent_list:
            ### We generate several random, percent-subsampled vosource in order to include error info:
            #if 1:
            #    i = niters # this should just be a single (integer) subset number/iteration index
            #for i in xrange(niters):
            for i in niters:
                if write_multiinfo_srcids:
                    new_srcid = "%d_%2.2f_%d" % (src_id, perc, i)
                else:
                    if type(src_id) == type(12):
                        new_srcid = "%d" % (src_id)
                    else:
                        new_srcid = src_id

                new_srcid_list.append(new_srcid)

                dbi_src = db_importer.Source(make_dict_if_given_xml=False)
                
                for band, band_dict in gen_orig.sig.x_sdict['ts'].iteritems():
                    if ":NOMAD" in band:
                        i_start = 0
                        i_end = len(band_dict['m'])
                    else:
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
                #import pdb; pdb.set_trace()
                #print

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
    fp_strio = cStringIO.StringIO()
    a.write_arff(outfile=fp_strio, \
                 remove_sparse_classes=True, \
                 n_sources_needed_for_class_inclusion=1,
                 include_header=include_header)#, classes_arff_str='', remove_sparse_classes=False)

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


class Arff_Generation_Engine_Tasks:
    """ Class contains methods that will be used for arff lines generation
    """

    def task_generate_feature_arff_lines(self, pars, srcid_list=[], xml_dirpath='', include_header=True,
                                         write_multiinfo_srcids=True, source_xml_dict={}, 
                                         ParseNomadColorsList=None,
                                         use_mtmerr_ts_files=False,
                                         do_sigmaclip=True):
        """ Given a sourceid list, generate features and the resulting ARFF lines.

        """
        #perc_arr = array(list(arange(0.2, 0.6, 0.01)))
        #'percent':[str(elem) for elem in perc_arr]
        sub_perc_list = [1.0]
        sub_iter_list = [1]
        #debug = 'hi3'
        #import traceback
        #try:
        arff_str = get_perc_subset(srcid_list, sub_perc_list, sub_iter_list, xml_dirpath=xml_dirpath,
                                   include_header=include_header,
                                   source_xml_dict=source_xml_dict,
                                   write_multiinfo_srcids=write_multiinfo_srcids,
                                   ParseNomadColorsList=ParseNomadColorsList,
                                   use_mtmerr_ts_files=use_mtmerr_ts_files,
                                   do_sigmaclip=do_sigmaclip)
        #except:
        #    debug = traceback.format_exc()
        #return {'test':debug, 'arff_rows':[1,2,3,4,5]}
        arff_rows = []
        class_list = []
        for row in arff_str.split('\n'):
            if len(row) == 0:
                continue
            elif row[:5] == '@data':
                continue
            elif row[:16] == '@ATTRIBUTE class':
                class_str = row[row.rfind("{'") + 2: row.rfind("'}")]
                class_list = class_str.split("','")
            else:
                arff_rows.append(row)

        return {'arff_rows':arff_rows, 'class_list':class_list}



def master_ipython_arff_generation(pars={}, write_multiinfo_srcids=True, source_xml_dict={}, use_mtmerr_ts_files=False, do_sigmaclip=True):
    """ Main code which controls ipython nodes when generating 

This is the task which will be called on ipengines by this function:

task_generate_feature_arff_lines(pars, srcid_list=[])

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
import matplotlib
matplotlib.use('agg')
sys.path.append(os.path.abspath('/global/home/users/dstarr/src/TCP/Software/ingest_tools'))
sys.path.append(os.path.abspath('/global/home/users/dstarr/src/TCP/Software/citris33'))
from get_colors_for_tutor_sources import Parse_Nomad_Colors_List
ParseNomadColorsList = Parse_Nomad_Colors_List(fpath='/global/home/users/dstarr/src/TCP/Data/best_nomad_src_list')
import arff_generation_master
ArffEngineTasks = arff_generation_master.Arff_Generation_Engine_Tasks()"""

    print 'before mec()'
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
                print "get_result() Except. Still pending on engine: %d" % (engine_id)
                still_pending_dict[engine_id] = pending_result
                result_val = None # 20110105 added
            if result_val == None:
                print "Still pending on engine: %d" % (engine_id)
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
            print "sleeping..."
            time.sleep(5)
            pending_result_dict = still_pending_dict
        n_pending = len(pending_result_dict)
        i_count += 1

    print 'after mec()'
    time.sleep(5) # This may be needed, although mec() seems to wait for all the Ipython clients to finish
    print 'after sleep()'
    #import pdb; pdb.set_trace()

    # todo: fill a dict and write to pickle: of srcid:xml_filepath
    srcid_list = pars['src_id']

    task_id_list = []
    class_list = []

    #if use_mtmerr_ts_files:
    #    ### This case is used when source timeseries is not stored in XMLs, but rather files with lines like: "55243.43624000 19.36500000 ......"
    #    return # TODO want to have an else below...

    #for srcid in srcid_list[:4]:
    if use_mtmerr_ts_files:
        srcid_list_new = srcid_list
    else:
        srcid_list_new = []
        for srcid in srcid_list:
            ##20120130disable: #srcid_list_new.append(int(srcid) + 100000000) 
            srcid_list_new.append(srcid)
            #junktry#srcid_list_new.append(str(srcid)) # late we expect this to be a string, non +100000000

    ### 20110622: I believe this is just a quick run-through of code in non-parallel mode, for one source:
    result_arff_list = []
    from get_colors_for_tutor_sources import Parse_Nomad_Colors_List
    ParseNomadColorsList = Parse_Nomad_Colors_List(fpath='/global/home/users/dstarr/src/TCP/Data/best_nomad_src_list')
    ArffEngineTasks = Arff_Generation_Engine_Tasks()
    out_dict = ArffEngineTasks.task_generate_feature_arff_lines(pars, srcid_list=srcid_list_new[:1], xml_dirpath=pars['xml_dirpath'], include_header=True, write_multiinfo_srcids=write_multiinfo_srcids, source_xml_dict=source_xml_dict, ParseNomadColorsList=ParseNomadColorsList, use_mtmerr_ts_files=use_mtmerr_ts_files, do_sigmaclip=do_sigmaclip)
    #out_dict = ArffEngineTasks.task_generate_feature_arff_lines(pars, srcid_list=srcid_list_new, xml_dirpath=pars['xml_dirpath'], include_header=True, write_multiinfo_srcids=write_multiinfo_srcids, source_xml_dict=source_xml_dict, ParseNomadColorsList=ParseNomadColorsList)
    ### KLUDGE leave out the last row since it will be reprocessed below:
    result_arff_list.extend(out_dict['arff_rows'][:-1])
    #import pdb; pdb.set_trace()
    #print


    n_src_per_task = 10 # 10 # NOTE: is generating PSD(freq) plots within lightcurve.py, should use n_src_per_task = 1, and all tasks should finish.# for ALL_TUTOR, =1 ipcontroller uses 99% memory, so maybe =3? (NOTE: cant do =10 since some TUTOR sources fail)

    imin_list = range(0, len(srcid_list_new), n_src_per_task)

    for i_min in imin_list:
        srcid_sublist = srcid_list_new[i_min: i_min + n_src_per_task]
        sub_source_xml_dict = {}
        if len(source_xml_dict) > 0:
            for sid in srcid_sublist:
                sub_source_xml_dict[sid] = source_xml_dict[sid]

        #print srcid_list
        #import pdb; pdb.set_trace()
        #print
        ##### FOR DEBUGGING:
        #####    - NOTE: will use up memory if run for ~100 iterations
        #ArffEngineTasks = Arff_Generation_Engine_Tasks()
        #out_dict = ArffEngineTasks.task_generate_feature_arff_lines(pars, srcid_list=srcid_sublist, xml_dirpath=pars['xml_dirpath'], include_header=False, write_multiinfo_srcids=write_multiinfo_srcids, ParseNomadColorsList=ParseNomadColorsList)
        #import pdb; pdb.set_trace()
        #print
        #####
        ### 20110106: This doesn't seem to solve the ipcontroller memory error, but works:
        tc_exec_str = """
tmp_stdout = sys.stdout
sys.stdout = open(os.devnull, 'w')
#os.system('touch /global/home/groups/dstarr/debug_started/%s' % (str(srcid_list[0])))
out_dict = ArffEngineTasks.task_generate_feature_arff_lines(pars, srcid_list=srcid_list, xml_dirpath=xml_dirpath, include_header=include_header, write_multiinfo_srcids=write_multiinfo_srcids, source_xml_dict=source_xml_dict, ParseNomadColorsList=ParseNomadColorsList, use_mtmerr_ts_files=use_mtmerr_ts_files, do_sigmaclip=do_sigmaclip)
#os.system('touch /global/home/groups/dstarr/debug/%s' % (str(srcid_list[0])))
sys.stdout.close()
sys.stdout = tmp_stdout

        """

        if 1:
            taskid = tc.run(client.StringTask(tc_exec_str,
                                          push={'pars':pars,
                                                'srcid_list':srcid_sublist,
                                                'xml_dirpath':pars['xml_dirpath'],
                                                'include_header':False,
                                                'source_xml_dict':sub_source_xml_dict,
                                                'write_multiinfo_srcids':write_multiinfo_srcids,
                                                'use_mtmerr_ts_files':use_mtmerr_ts_files,
                                                'do_sigmaclip':do_sigmaclip},
                                          pull='out_dict', 
                                          retries=3)) # 3
            task_id_list.append(taskid)
        #import pdb; pdb.set_trace()
        #print  # print tc.get_task_result(0, block=False).results
    #import pdb; pdb.set_trace()
    ####
    #combo_results_dict = {}
    dtime_pending_1 = None
    while ((tc.queue_status()['scheduled'] > 0) or
           (tc.queue_status()['pending'] > 0)):
        tasks_to_pop = []
        for task_id in task_id_list:
            temp = tc.get_task_result(task_id, block=False)
            if temp == None:
                continue
            temp2 = temp.results
            if temp2 == None:
                continue
            results = temp2.get('out_dict',None)
            if results == None:
                continue # skip some kind of NULL result
            if len(results) > 0:
                tasks_to_pop.append(task_id)
                result_arff_list.extend(results['arff_rows'])
                for a_class in results['class_list']:
                    if not a_class in class_list:
                        class_list.append(a_class)
                #ipython_return_dict = results
                #update_combo_results(combo_results_dict=combo_results_dict,
                #                     ipython_return_dict=copy.deepcopy(ipython_return_dict))
        for task_id in tasks_to_pop:
            task_id_list.remove(task_id)

            
        #    (tc.queue_status()['pending'] <= 64)):
        #       if ((now - dtime_pending_1) >= datetime.timedelta(seconds=300)):
        if ((tc.queue_status()['scheduled'] == 0) and 
            (tc.queue_status()['pending'] <= 7)):
           if dtime_pending_1 == None:
               dtime_pending_1 = datetime.datetime.now()
           else:
               now = datetime.datetime.now()
               if ((now - dtime_pending_1) >= datetime.timedelta(seconds=1200)):
                   print "dtime_pending=1 timeout break!"
                   break
        print tc.queue_status()
        print 'Sleep... 60 in test_pairwise_on_citris33_ipython::master_ipython_R_classifiers()', datetime.datetime.utcnow()
        time.sleep(60)
    # IN CASE THERE are still tasks which have not been pulled/retrieved:
    for task_id in task_id_list:
        temp = tc.get_task_result(task_id, block=False)
        if temp == None:
            continue
        temp2 = temp.results
        if temp2 == None:
            continue
        results = temp2.get('out_dict',None)
        if results == None:
            continue #skip some kind of NULL result
        if len(results) > 0:
            tasks_to_pop.append(task_id)
            result_arff_list.extend(results['arff_rows'])
            for a_class in results['class_list']:
                if not a_class in class_list:
                    class_list.append(a_class)
            #ipython_return_dict = results
            #update_combo_results(combo_results_dict=combo_results_dict,
            #                     ipython_return_dict=copy.deepcopy(ipython_return_dict))
    ####
    print tc.queue_status()
    return {'result_arff_list':result_arff_list, 
            'class_list':class_list}



def do_branimir_ptf_timeseries(pars={}):
    """ Use Branimir's RRLyrae PTF timeseries files:
    TODO: need to create a dict of {srcid:path}
       - store this in a .pkl
    """
    # TODO: load filename
    #20110125#src_list_fpath = "/global/home/users/dstarr/500GB/branimir/IPAC_lightcurves"
    src_list_fpath = "/global/home/users/dstarr/500GB/branimir/linear_rr_in_ptf_lightcurves"
    fpaths_unstripped = open(src_list_fpath).readlines()

    source_fpath_dict = {}
    for fpath_unstripped in fpaths_unstripped:
        fpath = fpath_unstripped.strip().replace('/home/bsesar/projects/rrlyr','/global/home/users/dstarr/500GB/branimir')
        #src_name = fpath[fpath.rfind('lightcurves') + 12:].replace('_','/')
        src_name = fpath[fpath.rfind('_') + 1:] # dstarr has checked that these src_name are all unique and no source is weing overwritten
        #if src_name != '6094056391088054904':
        if src_name != '6941401624103488574':
            continue
        source_fpath_dict[src_name] = fpath

    pars['src_id'] = source_fpath_dict.keys()
    pars['xml_dirpath'] = None # not needed in our case
    out_dict = master_ipython_arff_generation(pars=pars, 
                                              source_xml_dict=source_fpath_dict,
                                              write_multiinfo_srcids=False,
                                              use_mtmerr_ts_files=True,
                                              do_sigmaclip=False,
                                              ) #write_multiinfo_srcids=False:only srcid in output arff; True when doing several percent/subset arff rows
    result_arff_list = out_dict['result_arff_list']

    ### Need to find the last ATTRIBUTE in the header, so the classes can be inserted:
    in_attibs = False
    for i, elem in enumerate(out_dict['result_arff_list']):
        if len(elem) == 0:
            continue
        elif elem[0] == "%":
            continue
        elif elem[:10] == "@ATTRIBUTE":
            in_attibs = True
        elif in_attibs:
            ### Now we are done parsing the @ATTRIBUTES
            class_str = "@ATTRIBUTE class {'%s'}" % ("','".join(out_dict['class_list']))
            out_dict['result_arff_list'].insert(i, class_str)
            ### Also want to insert @DATA before the data starts.
            out_dict['result_arff_list'].insert(i + 1, '@DATA')
            break

    fp = open(os.path.expandvars("$HOME/scratch/out.arff"), 'w')
    fp.write('\n'.join(result_arff_list))
    fp.close()
    import datetime
    print datetime.datetime.now()
    import pdb; pdb.set_trace()
    print

       



if __name__ == '__main__':

    pars = {'src_id':[], #deboss_srcid_list, #['148875', '148723', '148420', '149144', '149049'], #deboss_srcid_list,#['148875', '148723', '148420', '149144', '149049'], #deboss_srcid_list, #['149144', '149049', '149338', '149049', '149338','149182','149108'],
            'percent':[], #[str(elem) for elem in perc_arr], #[str(elem) for elem in arange(0.90, 1.0, 0.01)], # [str(elem) for elem in arange(0.58, 1.0, 0.01)]#[str(elem) for elem in arange(0.01, 1.01, 0.01)], #[str(elem) for elem in arange(0.8, 1.0, 0.10)], #['0.8', '0.86', '0.88', '0.9', '0.95', '1.0'],
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
    #if options.srcid != '':
    #    pars['src_id'] = options.srcid

    ### Use Branimir's RRLyrae PTF timeseries files:
    # TODO: need to create a dict of {srcid:path}
    #   - store this in a .pkl
    if 0:
        ### 20120126 Use Branimir's RRLyrae PTF timeseries files:
        do_branimir_ptf_timeseries(pars=pars)
        sys.exit()


    if 0:
        ### OBSOLETE
        ### all_tutor_xmls: Many tutor project_ids case:
        pars['xml_dirpath'] = '/global/home/users/dstarr/500GB/all_tutor_xmls_flat'
        xmls_dict_pkl_fpath = '/global/home/users/dstarr/500GB/all_tutor_xmls_dict.pkl'
        glob_str = '%s/*/*' % (pars['xml_dirpath'])

        if os.path.exists(xmls_dict_pkl_fpath):
            source_xml_dict = cPickle.load(open(xmls_dict_pkl_fpath))
        else:
            #import pdb; pdb.set_trace()
            #print

            source_xml_dict = {}
            dirs = os.listdir(pars['xml_dirpath'])
            for dir in dirs:
                dirpath = "%s/%s" % (pars['xml_dirpath'], dir)
                glob_str = '%s/*' % (dirpath)

                xml_fpaths = glob.glob(glob_str)
                
                for xml_fpath in xml_fpaths:
                    print xml_fpath
                    num_str = xml_fpath[xml_fpath.rfind('/') + 1:xml_fpath.rfind('.')]
                    srcid = int(num_str)# - 100000000
                    source_xml_dict[str(srcid)] = xml_fpath


            fp = open(xmls_dict_pkl_fpath, 'wb')
            cPickle.dump(source_xml_dict,fp,1) # ,1) means a binary pkl is used.
            fp.close()


    else:
        ### Most other TUTOR projects:
        #pars['xml_dirpath'] = '/global/home/users/dstarr/500GB/all_tutor_xmls_flat'
        #xmls_dict_pkl_fpath = '/global/home/users/dstarr/500GB/all_tutor_xmls_dict.pkl'
        #glob_str = '%s/*' % (pars['xml_dirpath'])


        ###  ASAS configs pre20120221 #(?pre 20110511?):
        #pars['xml_dirpath'] = '/global/home/users/dstarr/500GB/xmls/proj_126/xmls'
        #xmls_dict_pkl_fpath = '/global/home/users/dstarr/500GB/xmls/proj_126/xmls_dict.pkl'

        ###  ASAS configs (pre 20110511):
        pars['xml_dirpath'] = '/global/home/users/dstarr/500GB/xmls/proj_126/asas_ACVS_50k_new_aper_20120221'
        xmls_dict_pkl_fpath = '/global/home/users/dstarr/500GB/xmls/proj_126/asas_ACVS_50k_new_aper_20120221_xmls_dict.pkl'

        ### stipe82 SDSS:
        #pars['xml_dirpath'] = '/global/home/groups/dstarr/tutor_121_xmls'
        #xmls_dict_pkl_fpath = '/global/home/groups/dstarr/tutor_121_xmls/xmls_dict.pkl'
        
        glob_str = '%s/*' % (pars['xml_dirpath'])


        if os.path.exists(xmls_dict_pkl_fpath):
            source_xml_dict = cPickle.load(open(xmls_dict_pkl_fpath))
        else:
            xml_fpaths = glob.glob(glob_str)
            
            source_xml_dict = {}
            for xml_fpath in xml_fpaths:
                #print xml_fpath
                num_str = xml_fpath[xml_fpath.rfind('/') + 1:xml_fpath.rfind('.')]
                #20120130#srcid = int(num_str) - 100000000
                #20120130#source_xml_dict[str(srcid)] = xml_fpath
                source_xml_dict[int(num_str)] = xml_fpath
            fp = open(xmls_dict_pkl_fpath, 'wb')
            cPickle.dump(source_xml_dict,fp,1) # ,1) means a binary pkl is used.
            fp.close()

    #import pdb; pdb.set_trace()
    #print
    pars['src_id'] = source_xml_dict.keys()

    #import pdb; pdb.set_trace()
    #print
    out_dict = master_ipython_arff_generation(pars=pars, 
                                              source_xml_dict=source_xml_dict,
                                              write_multiinfo_srcids=False) #False:only srcid in output arff; True when doing several percent/subset arff rows
    #print result_arff_list
    result_arff_list = out_dict['result_arff_list']

    ### Need to find the last ATTRIBUTE in the header, so the classes can be inserted:
    in_attibs = False
    for i, elem in enumerate(out_dict['result_arff_list']):
        if len(elem) == 0:
            continue
        elif elem[0] == "%":
            continue
        elif elem[:10] == "@ATTRIBUTE":
            in_attibs = True
        elif in_attibs:
            ### Now we are done parsing the @ATTRIBUTES
            class_str = "@ATTRIBUTE class {'%s'}" % ("','".join(out_dict['class_list']))
            out_dict['result_arff_list'].insert(i, class_str)
            ### Also want to insert @DATA before the data starts.
            out_dict['result_arff_list'].insert(i + 1, '@DATA')
            break

    if 0:
        # pre 20120220
        # This section is for recording which LS params were changed for each arff.
        #    ('nharm', 8),
        # ? want to vary the sigmaclipping?
        arff_pars = [ \
            ('f_max', 33.0),
            ('df_factor', 0.8),
            ('nharm', 8),
            ('tone_control',5.0),
            ('dtrend_order',1)]
        fp_dat = open('/global/home/users/dstarr/500GB/LS_param_explore_arffs/LS_param_explore_arffs.dat','a')
        arff_fname = "/global/home/users/dstarr/500GB/LS_param_explore_arffs/%f_%f_%d_%f_%d.arff" % ( \
            arff_pars[0][1],
            arff_pars[1][1],
            arff_pars[2][1],
            arff_pars[3][1],
            arff_pars[4][1])

        fp_dat.write("%s %f %f %d %f %d\n" % (arff_fname,
            arff_pars[0][1],
            arff_pars[1][1],
            arff_pars[2][1],
            arff_pars[3][1],
            arff_pars[4][1]))
        fp_dat.close()

        fp = open(arff_fname, 'w')
        fp.write('\n'.join(result_arff_list))
        fp.close()

    else:
        fp = open(os.path.expandvars("$HOME/scratch/out.arff"), 'w')
        fp.write('\n'.join(result_arff_list))
        fp.close()
    import datetime
    print datetime.datetime.now()
    import pdb; pdb.set_trace()
    print
