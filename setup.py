#! /usr/bin/env python

descr = """Machine Learning Time Series Platform

https://github.com/cesium

"""

DISTNAME            = 'cesium'
DESCRIPTION         = 'Machine Learning Time-Series Platform'
LONG_DESCRIPTION    = descr
MAINTAINER          = 'cesium Team'
MAINTAINER_EMAIL    = 'stefanv@berkeley.edu'
URL                 = 'http://cesium.ml'
LICENSE             = 'Modified BSD'
DOWNLOAD_URL        = 'https://github.com/cesium-ml/cesium'
PYTHON_VERSION      = (3, 4)

import os
import sys

import setuptools
from distutils.command.build_py import build_py


def configuration(parent_package='', top_path=None):
    if os.path.exists('MANIFEST'):
         os.remove('MANIFEST')

    from numpy.distutils.misc_util import Configuration
    config = Configuration(None, parent_package, top_path)

    config.set_options(
            ignore_setup_xxx_py=True,
            assume_default_configuration=True,
            delegate_options_to_subpackages=True,
            quiet=True)

    config.add_subpackage('cesium')

    return config


with open('cesium/version.py') as fid:
    for line in fid:
        if line.startswith('version'):
            VERSION = line.strip().split('=')[-1][1:-1]
            break

with open('requirements.txt') as fid:
    INSTALL_REQUIRES = [l.split('#')[0].strip() for l in fid.readlines() if l
                        and not l.startswith('git')]
    INSTALL_REQUIRES = [pkg.replace('-', '_') for pkg in INSTALL_REQUIRES]


# requirements for those browsing PyPI
REQUIRES = [r.replace('>=', ' (>= ') + ')' if '=' in r else r
            for r in INSTALL_REQUIRES]
REQUIRES = [r.replace('==', ' (== ') for r in REQUIRES]


if __name__ == "__main__":
    try:
        from numpy.distutils.core import setup
        extra = {'configuration': configuration}
        # do not risk updating numpy
        INSTALL_REQUIRES = [r for r in INSTALL_REQUIRES if 'numpy' not in r]
    except ImportError:
        if len(sys.argv) >= 2 and ('--help' in sys.argv[1:] or
                                   sys.argv[1] in ('--help-commands',
                                                   'egg_info',
                                                   '--version',
                                                   'clean')):
            # For these actions, NumPy is not required.
            #
            # They are required to succeed without Numpy for example when
            # pip is used to install cesium when Numpy is not yet
            # present in the system.
            try:
                from setuptools import setup
            except ImportError:
                from distutils.core import setup
        else:
            print('To install cesium from source, you will need numpy.\n' +
                  'Install numpy with pip:\n' +
                  '  pip install numpy\n'
                  'Or using conda:\n'
                  '  conda install numpy\n'
                  'or use your operating system package manager.')
            sys.exit(1)

    setup(
        name=DISTNAME,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        maintainer=MAINTAINER,
        maintainer_email=MAINTAINER_EMAIL,
        url=URL,
        license=LICENSE,
        download_url=DOWNLOAD_URL,
        version=VERSION,

        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: BSD License',
            'Programming Language :: C',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 3',
            'Topic :: Scientific/Engineering',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX',
            'Operating System :: Unix',
            'Operating System :: MacOS',
        ],

        install_requires=INSTALL_REQUIRES,
        setup_requires=['cython>=0.21'],
        requires=REQUIRES,
        configuration=configuration,
        packages=setuptools.find_packages(exclude=['doc']),
        include_package_data=True,
        zip_safe=False,
        cmdclass={'build_py': build_py},
    )
