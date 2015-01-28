#!/usr/bin/env python
""" This is intended to be an example which can be emulated / copied in other code.

Given a directory with some vosource xmls (which have features generated),
generate a WEKA style .arff file.

You should be able to run this using:

       python generate_arff_using_xml.py

NOTE: ASSUMES that the correct directory path pointing to the xmls is defined in this file.

NOTE: ASSUMES that environment variable TCP_DIR has been defined and works (can be printed/found in os.environ).
"""
import os, sys
import glob

sys.path.append(os.environ.get("TCP_DIR") + '/Software/feature_extract/MLData')
import arffify




if __name__ == '__main__':
    ### NOTE: this __main__ section will only be executed when the python script is called like:
    ###   python generate_arff_using_xml.py
    ###         or
    ###   ./generate_arff_using_xml.py


    xml_dirpath = "/home/dstarr/scratch/xml_list"
    out_arff_filepath = "/tmp/gen.arff" # to be written

    filepaths = glob.glob("%s/*xml" % (xml_dirpath))

    vosource_list = []
    for num, fpath in enumerate(filepaths):
        ### NOTE: I'm using 'num' as a psedudo source-id for identification in the .arff file.
        vosource_list.append((str(num), fpath))   # NOTE: a tuple of this form is needed.


    a = arffify.Maker(search=[], skip_class=False, local_xmls=True, 
                          convert_class_abrvs_to_names=False,
                          flag_retrieve_class_abrvs_from_TUTOR=False,
                          dorun=False, add_srcid_to_arff=True)
    a.pars['skip_sci_class_list'] = [] # NOTE: this means that all sources will be added to the .arff, regardless of how ambigous the classification is.
    a.populate_features_and_classes_using_local_xmls(srcid_xml_tuple_list=vosource_list)
    a.write_arff(outfile=out_arff_filepath, \
                     remove_sparse_classes=False)#, remove_sparse_classes=True, n_sources_needed_for_class_inclusion=10) # this parameter allows you to exclude science-classes from the .arff by requiring a certain number of examples to exist.
