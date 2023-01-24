#! /usr/bin/env python

import sys

try:
    import numpy as np
    from Cython.Build import cythonize
except ImportError:
    print("\nPlease install numpy before building cesium.\n")
    sys.exit(1)

import setuptools
from setuptools.command.build_ext import build_ext


def extensions():
    np_inc = np.get_include()
    cython_exts = cythonize("cesium/features/_lomb_scargle.pyx", include_path=[np_inc])
    return cython_exts


if __name__ == "__main__":
    metadata = dict(
        name="cesium",
        packages=setuptools.find_packages(
            include=["cesium*"],
        ),
        cmdclass={"build_ext": build_ext},
        ext_modules=extensions(),
    )

    setuptools.setup(**metadata)
