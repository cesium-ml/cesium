#!/usr/bin/env python
# Parameter Tool
#    v0.1 : initial implementation
# Author: dstarr
# To wrap parameter getting functions, for simple parameter maintainance

# Requires:
#  1) Parameter file which contains the dictionary:
#       parameters = {}
#  2) Any additional command line arguments should be of the form:
#       ./<some_script.py> <param_name>=<some_value>
#     where (currently) <param_name> and <some_value>
#        should not contain any spaces.
#          eg.: ./blah_script.py fav_animal=cow
#     and <param_name> matches a 'dictionary key' in the parameter file.

# Invoked using:
#   import param_tool
#   pars = param_tool.get_pars('Some param file path')

# NOTE: if "os.environ['BLAH_ENV_VAR']" is used in the param file,
#       then "import os" needs to exist at the head of the param file.
#

# TODO: Note: This probably forces all command line param values into
#               string form.
import sys, os

def read_pars_from_file(par_file_path):
    f = open(par_file_path)
    exec f
    f.close()
    return parameters

def add_command_args(pars, verbose):
    if (len(sys.argv) > 1):
        for elem in sys.argv:
            if (elem.count('=') >= 1):
                # This looks like a parameter definition
                i_sep = elem.find('=')
                first_half_raw = elem[0:(i_sep)]
                par_name = first_half_raw.lstrip().rstrip()
                last_half_raw = elem[(i_sep+1):]
                par_value = last_half_raw.lstrip().rstrip()
                if (pars.has_key(par_name)):
                    pars.update({par_name:par_value})
                else:
                    if (verbose == 1):
                        print "I don't think \"", par_name,"\" is a parameter!"
    return pars

def print_params(pars):
    print "----- Parameters Used:"
    for k, v in pars.iteritems():
	print str(k), ':', v
    print "---------------------"

def get_pars(par_file_path, verbose=1):
    """ Main function, will get parameters from file, and from arguments
    stated in the command line call.
    """
    pars = read_pars_from_file(par_file_path)
    pars = add_command_args(pars, verbose)
    if (verbose == 1):
        print_params(pars)
    return pars
