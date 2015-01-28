#!/usr/bin/env python 
"""
   v0.1 create duplicate entries for clases with few entries, so that they are as populated as mos populated classes (its 3am).

NOTE: MUST MAKE SURE THAT INPUT .arff FILE HAS an extra blank line at end of file.
"""
import sys, os

class_num_rows_dict = {\
    'Algol (Beta Persei)':518,
    'Beta Lyrae':240,
    'W Ursae Majoris':1011,
    'Binary':55,
    'T Tauri':15,
    'Wolf-Rayet':34,
    'Type Ia Supernovae':52,
    'BL Lac':28,
    'Microlensing Event':590,
    'Semiregular Pulsating Red Giants':14,
    'Semiregular Pulsating Variable':34,
    'Short period (BL Herculis)':14,
    'Population II Cepheid':17,
    'Classical Cepheid':921,
    'Symmetrical':48,
    'Multiple Mode Cepheid':107,
    'RR Lyrae - Asymmetric':31,
    'RR Lyrae, Double Mode':111,
    'RR Lyrae':16,
    'RR Lyrae, Fundamental Mode':291,
    'RR Lyrae - Near Symmetric':15,
    'RR Lyrae, Closely Spaced Modes':13,
    'Pulsating Variable':111,
    'Beta Cephei':33,
    'Gamma Doradus':41,
    'Lambda Bootis Variable':13,
    'Delta Scuti':150,
    'SX Phoenicis':14,
    'Long Period (W Virginis)':34,
    'Mira':113}

if __name__ == '__main__':

    arff_fpath = "/home/pteluser/scratch/train_output_allclass_14feat_to_have_nrows_scaled.arff"

    out_arff_fpath = "/home/pteluser/scratch/train_output_allclass_14feat_class_scaled.arff"
    os.system("rm " + out_arff_fpath)
    fp_out = open(out_arff_fpath, 'w')
    
    class_name_to_arff_lines_list = {}
    for class_name in class_num_rows_dict.keys():
        class_name_to_arff_lines_list[class_name] = []

    lines = open(arff_fpath).readlines()

    for i in xrange(len(lines)):
        fp_out.write(lines[i])
        if "@data" in lines[i]:
            break

    # KLUDGE : here we make an asumption in parsing that science class names do not have "." in them. (they do have "," though.
    for line in lines[i+1:]:
        # KLUDGE: (it's 3:35 am):
        i_list = [line.rfind('.'), line.rfind('?'), line.rfind('-1')]
        i = max(i_list)
        line_a = line[i:]
        line_class = line_a[line_a.find(',')+1:]
        line_class_stripped = line_class.strip().strip("'")
        class_name_to_arff_lines_list[line_class_stripped].append(line)

    # now we have a dict with a bunch of lines representing each class.  It's a big dict.

    # Next we generate fake rows for every science class, up to max-n-rows.

    max_n_rows = max(class_num_rows_dict.values())

    for class_name, n_rows in class_num_rows_dict.iteritems():
        if n_rows == max_n_rows:
            for line in class_name_to_arff_lines_list[class_name]:
                fp_out.write(line)
            continue
        i = 0
        while i < (max_n_rows - n_rows):
            for line in class_name_to_arff_lines_list[class_name]:
                #if "0.426,2.410946,0.065327,0.281546,3.092307,5.834638,0.007759,0.060579,0.37931,-0.066667,3.246999,0.818523,50870.251189,'Pulsating Variable'" in line:
                #    print 'yo'
                #print line
                fp_out.write(line)
                i += 1
                if i >= (max_n_rows - n_rows):
                    break

    fp_out.close()
