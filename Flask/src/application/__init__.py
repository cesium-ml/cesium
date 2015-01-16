"""
Initialize Flask app

"""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *

from flask import Flask

app = Flask('application')
app.config.from_object('application.settings')

from . import urls
