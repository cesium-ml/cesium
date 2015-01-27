from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import *
from future import standard_library
standard_library.install_aliases()
import os, sys
import numpy
from numpy import *

avtype = [('extname','S100'), ('extractor',object_), ('active',bool_)]

class FeatureInterface(object):
    """This serves as an interface between signals and extractors.
    An instance of this object is generated when the module is imported
    """
    def __init__(self):
        # 20081216: dstarr sees that we keep on appending signals here (and growing memory) when he thinks only one signal is needed in self.subscribing_signals[] to do the feature extractions for a source. : (original function == True):
        self.debug__original_do_append_signals_to_subscribing_signals = False
        self.subscribing_signals = []
        self.available_extractors = empty(0,avtype) # declare the recipient numpy array for extractors

    def register_signal(self,signal, list_of_extractors, initialize = True):
        """ initialize determines whether all the active extractors are immediately applied to the signal """
        if self.debug__original_do_append_signals_to_subscribing_signals:
            self.subscribing_signals.append(signal)
        else:
            # 20081216: dstarr sees that we keep on appending signals here (and growing memory) when he thinks only one signal is needed in self.subscribing_signals[] to do the feature extractions for a source.
            self.subscribing_signals = [signal]
        if initialize: # check that we want to initialize the signal
            for an_extractor in self.available_extractors[self.available_extractors['active']]: # loop through all active extractors
                #print "Now I'm doing " + str(an_extractor['extname'])
                #if str(an_extractor['extname']) == 'lomb_scargle':
                #       print 'yo'
                extractor_obj = an_extractor['extractor']() # instantiate
                signal.update(extractor_obj)

    def register_extractor(self,extractor):
        self.available_extractors = append(self.available_extractors, \
                                 array((extractor.extname, extractor, \
                                        extractor.active),avtype)) # append a tuple of format avtype containing (extname, extractor object, active)
        if extractor.active: self.notify(extractor)


    def notify(self,extractor):
        #print "New active extractor available!"
        for signal in self.subscribing_signals:
            signal.update(extractor())


    def remove_signal(self,signal):
        self.subscribing_signals.remove(signal)


    def remove_extractor(self,extractor):
        """ Remove an extractor from the available extractor list.
        Input is a type. To remove by name, using remove_extname """
        sizebeforeremoving = self.available_extractors.size
        self.available_extractors = self.available_extractors[ where( \
                   self.available_extractors['extractor'] != extractor)] # slice off the corresponding extractor
        sizeafterremoving = self.available_extractors.size
        if sizebeforeremoving == sizeafterremoving:
            print("Key does not exist, can't be removed from active list", extractor.extname)


    def remove_extname(self,extname):
        """ Remove an extractor from the available extractor list by
        its name. Input is a string.
        To remove by type, using remove_extractor """
        sizebeforeremoving = self.available_extractors.size
        self.available_extractors = self.available_extractors[ where( \
                       self.available_extractors['extname'] != extname)] # slice off the corresponding extractor
        sizeafterremoving = self.available_extractors.size
        if sizebeforeremoving == sizeafterremoving:
            print("Key does not exist, can't be removed from active list", extractor.extname)


    def switch_extname(self,extractor_name,activate=False,deactivate=False):
        extractor_index = self.find_extname(extractor_name, index=True)
        if extractor_index: # check that find_extname worked
            extractor_row = self.available_extractors[\
                                                    extractor_index]
            active = extractor_row['active']
            print("This extractor %s was in state %s" % (\
                                             extractor_name, active))
            if activate:
                active = True
            elif deactivate:
                active = False
            else:
                active = not active
            print("This extractor %s is now in state %s" % (\
                                              extractor_name,active))
            self.available_extractors[extractor_index] = array(\
                    (extractor_row['extname'][0], \
                     extractor_row['extractor'][0], active),avtype)
            return "done"
        else:
            return False


    def find_extname(self, extractor_name, index = False): # linked if want to modify the array directly
        extractors = self.available_extractors['extname'].tolist()

        try:
            ix = extractors.index(extractor_name.encode('utf-8'))
        except ValueError:
            print("find_extname couldn't find extractor %s" % \
                                                    (extractor_name))
            return False # if we didn't find the object

        if index:
            return ix

        extractor_row = self.available_extractors[ix] # return the corresponding extractor row (extname, extractor and active)
        return extractor_row


    def request_extractor(self,extractor_name):
        extractor_row = self.find_extname(extractor_name)
        if extractor_row: # check that find_extname worked
            return extractor_row['extractor']
        else:
            return False


feature_interface = FeatureInterface()


def initialize(list_of_extractors):
    #sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
    #                                               'Software/ingest_tools'))
    from ...ingest_tools import feature_extraction_interface
    fs = feature_extraction_interface.Internal_Feature_Extractors()
    for key_name in fs.feature_ordered_keys:
        list_of_extractors.append(key_name)
    list_of_extractor_objects = []

    from . import extractors

    for extractor_name in list_of_extractors:
        d = {}
        extractor = getattr(extractors, extractor_name + '_extractor')
        list_of_extractor_objects.append(extractor)
        if isinstance(extractor,type):
            instance = extractor()
            try:
                # TODO: Figure out why we have to register the extractor
                # both on the extractor and the feature_interface instance
                instance.register_extractor()
                feature_interface.register_extractor(type(instance))
            except Exception as e:
                raise(e)
                print("Could not register extractor", extractor_name)
                print(e.msg)
        else:
            pass
    return list_of_extractor_objects


def fetch_extract(extractor_name,properties,band=None):
    """ we want the result of this extractor """
    extractor = feature_interface.request_extractor(extractor_name)
    result = extractor.extr(properties,band=band)
    return result


global_list_of_extractors = initialize([])
