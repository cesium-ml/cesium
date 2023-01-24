#! /usr/bin/env python

import sys

import setuptools
from setuptools.command.build_ext import build_ext
from Cython.Build import cythonize


def extensions():
    cython_exts = cythonize("cesium/features/_lomb_scargle.pyx")
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

    try:
        import numpy as np  # noqa: F401
    except ImportError:
        print("\nPlease install numpy before building cesium.\n")
        sys.exit(1)

    setuptools.setup(**metadata)
