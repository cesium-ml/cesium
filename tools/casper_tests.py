#!/usr/bin/env python

import multiprocessing
import subprocess
import glob
import os
import sys


if __name__ == "__main__":
    os.environ["MLTSP_TEST_DB"] = "1"
    from mltsp.Flask import flask_app
    flask_app.db_init(force=True)
    from mltsp.Flask.flask_app import app

    p = multiprocessing.Process(target=app.run)
    p.start()

    tests = sorted(glob.glob('mltsp/tests/frontend/*.js'))
    status = subprocess.call(['external/casperjs/bin/casperjs', '--verbose',
                              '--log-level=debug', 'test'] + tests)

    p.terminate()

    sys.exit(status)

