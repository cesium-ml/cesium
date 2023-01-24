#! /usr/bin/env python

import sys

try:
    import numpy as np
except ImportError:
    print("\nPlease install numpy before building cesium.\n")
    sys.exit(1)

try:
    from Cython.Build import cythonize
except ImportError:
    print("\nPlease install Cython before building cesium.\n")
    sys.exit(1)

try:
    import setuptools_scm  # noqa: F401
except ImportError:
    print("\nPlease install setuptools_scm before building cesium.")
    sys.exit(1)

from setuptools import Extension, find_namespace_packages, setup
from setuptools.command.build_ext import build_ext


def extensions():
    np_inc = np.get_include()
    cython_exts = cythonize(
        Extension(
            "cesium.features._lomb_scargle",
            sources=["cesium/features/_lomb_scargle.pyx"],
            include_dirs=[np_inc],
        ),
        include_path=["cesium/features"],
    )
    return cython_exts


if __name__ == "__main__":
    metadata = dict(
        name="cesium",
        packages=find_namespace_packages(
            include=["cesium*"],
        ),
        cmdclass={"build_ext": build_ext},
        ext_modules=extensions(),
    )

    setup(**metadata)
