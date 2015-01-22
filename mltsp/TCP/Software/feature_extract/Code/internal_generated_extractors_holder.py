from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
from builtins import object
glob_internally_generated_extractors = {} # 20080508: dstarr KLUDGE.  Nat's Lomb Scargle algorithms generate a bunch of features, which due to the current architecture, must be represented in seperate extractor objects that are available many stacks higher (to be added to a "signal_list").  Existing architecture assumed all extractors are explicitly defined (listed as ordered __init__.py imports), but this dynamic feature-extractor generation breaks this assumption.  So, I must use a global list which is accessible by signals_list related methods, and still updateable by the Nat-Lomb_scargle feature extractor.
class Internal_Gen_Extractors_Accessor(object):
    """ Used only to allow access to a global list, by a
    class which does:    import feature_interfaces

    KLUDGE.
    """
    def __init__(self):
        global glob_internally_generated_extractors
        self.glob_internally_generated_extractors = glob_internally_generated_extractors
    def main(self):
        pass
