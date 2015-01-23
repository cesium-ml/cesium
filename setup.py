#! /usr/bin/env python

descr = """Machine Learning Time Series Platform

https://github.com/mltsp

"""

DISTNAME            = 'mltsp'
DESCRIPTION         = 'Machine Learning Time Series Platform'
LONG_DESCRIPTION    = descr
MAINTAINER          = 'MLTSP Team'
MAINTAINER_EMAIL    = 'stefanv@berkeley.edu'
URL                 = 'https://github.com/mltsp'
LICENSE             = 'Modified BSD'
DOWNLOAD_URL        = 'https://github.com/mltsp/mltsp'
VERSION             = '0.1dev'
PYTHON_VERSION      = (3, 4)

import os

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

    config.add_subpackage('TCP')

    return config


def write_version_py(filename='version.py'):
    template = """# THIS FILE IS GENERATED FROM THE MLTSP SETUP.PY
version='%s'
"""

    vfile = open(os.path.join(os.path.dirname(__file__),
                              filename), 'w')

    try:
        vfile.write(template % VERSION)
    finally:
        vfile.close()


def get_package_version(package):
    for version_attr in ('__version__', 'VERSION', 'version'):
        version_info = getattr(package, version_attr, None)
        if version_info and str(version_attr) == version_attr:
            return str(version_info)

if __name__ == "__main__":
    write_version_py()

    from numpy.distutils.core import setup
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
            'Programming Language :: Python :: 3',
            'Topic :: Scientific/Engineering',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX',
            'Operating System :: Unix',
            'Operating System :: MacOS',
        ],

        configuration=configuration,
        packages=setuptools.find_packages(),
        include_package_data=True,
        zip_safe=False,
        cmdclass={'build_py': build_py},
    )
