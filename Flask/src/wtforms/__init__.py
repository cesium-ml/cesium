"""
WTForms
=======

WTForms is a flexible forms validation and rendering library for python web
development.

:copyright: Copyright (c) 2010 by Thomas Johansson, James Crasta and others.
:license: BSD, see LICENSE.txt for details.
"""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
from wtforms import validators, widgets
from wtforms.fields import *
from wtforms.form import Form
from wtforms.validators import ValidationError

__version__ = '1.0.1'
