import os
import numpy as np
from Cython.Build import cythonize

base_path = os.path.abspath(os.path.dirname(__file__))


def configuration(parent_package='', top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('features', parent_package, top_path)

    cythonize(os.path.join(base_path, '_lomb_scargle.pyx'))

    config.add_extension('_lomb_scargle', '_lomb_scargle.c',
                         include_dirs=[np.get_include()])

    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())
