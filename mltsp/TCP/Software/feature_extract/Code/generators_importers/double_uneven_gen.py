from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
import numpy
from .storage import storage

from .uneven_sine_gen import uneven_sine_gen
from .double_ind_gen import double_ind_gen

class double_uneven_gen(uneven_sine_gen,double_ind_gen):
    name = 'unevenly sampled, double signal (two sine waves), uneven noise'
