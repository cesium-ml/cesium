# -*- coding: utf-8 -*-
"""
    werkzeug.testsuite.contrib
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests the contrib modules.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
import unittest
from werkzeug.testsuite import iter_suites


def suite():
    suite = unittest.TestSuite()
    for other_suite in iter_suites(__name__):
        suite.addTest(other_suite)
    return suite
