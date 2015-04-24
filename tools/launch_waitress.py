#!/usr/bin/env python
from mltsp.Flask.flask_app import app
from waitress import serve

serve(app, host='0.0.0.0', port=5000)

