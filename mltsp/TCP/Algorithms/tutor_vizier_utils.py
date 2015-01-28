#!/usr/bin/env python 
"""  Scripts for retrieving vizier.cfa.harvard.edu data and then
importing into TUTOR database via web-interface.

Vizier page:

    http://vizier.cfa.harvard.edu/viz-bin/VizieR?-source=J/A+A/461/183

Select:
    "Max. Entries:   9999"
    "Output layout": "tab -Seperated-Values"
    *** also "show" the "recno" column, which gives a source-id

 - This downloads a .tsv file of just source info, filenames, ...


NOTE: will need to place timeseries data files in lyr3 directory using:

    

"""
from __future__ import print_function
import sys, os 

def parse_tsv(tsv_fpath):
    """ Parse a tsv ';' seperated file which was downloaded from vizier
    """
    out_dict = {'data_lists':{},
                'data_units_dict':{}}
    icol_to_colname = {}
    lines = open(tsv_fpath)
    i_signif_line = 0
    for line_raw in lines:
        line = line_raw.strip()
        if len(line) == 0:
            continue
        elif line[0] == '#':
            continue
        elif i_signif_line == 0:
            # _RAJ2000;_DEJ2000;Name;RAJ2000;DEJ2000;Bmag;Vmag;SpType;FileName
            col_names = line.split(';')
            for i, col_name in enumerate(col_names):
                out_dict['data_lists'][col_name] = []
                icol_to_colname[i] = col_name
        elif i_signif_line == 1:
            unit_str_list = line.split(';')
            for i, unit_str in enumerate(unit_str_list):
                out_dict['data_units_dict'][icol_to_colname[i]] = unit_str
        elif i_signif_line == 2:
            pass # skip this but also increment i_signif_line below
        else:
            elems = line.split(';')
            for i, elem in enumerate(elems):
                out_dict['data_lists'][icol_to_colname[i]].append(elem)
        i_signif_line += 1
    return out_dict


def get_timeseries_files_using_tsv(tsv_fpath='', 
                                   data_url_prefix='',
                                   data_url_suffix='',
                                   data_download_dirpath=''):
    """
http://vizier.cfa.harvard.edu/viz-bin/nph-Plot/Vgraph/txt?J/A%2bA/461/183/./phot/aaori.dat&P=0&-y&-&-&-
    """
    if not os.path.exists(data_download_dirpath):
        os.system('mkdir -p %s' % (data_download_dirpath))
    
    data_dict = parse_tsv(tsv_fpath)
    print(data_dict['data_lists'].keys())
    print('FileName', data_dict['data_lists']['FileName'][10])
    print('RAJ2000', data_dict['data_lists']['RAJ2000'][10])

    for fname in data_dict['data_lists']['FileName']:
        #get_str = "curl -O %s%s%s" % (data_url_prefix, fname, data_url_suffix)
        get_str = 'curl "%s%s%s" > "%s/%s"' % (data_url_prefix, fname, data_url_suffix, 
                                               data_download_dirpath, fname)
        os.system(get_str)

    print("TSV file:\n\t", tsv_fpath)
    print("Timeseries dat downloaded to:\n\t", data_download_dirpath)





if __name__ == '__main__':
    get_timeseries_files_using_tsv(tsv_fpath='/Users/dstarr/Downloads/asu (2).tsv', 
                                   data_url_prefix='http://vizier.cfa.harvard.edu/viz-bin/nph-Plot/Vgraph/txt?J/A%2bA/461/183/./phot/',
                                   data_url_suffix='&P=0&-y&-&-&-',
                                   data_download_dirpath='/Users/dstarr/analysis/tutor124ttauri')
