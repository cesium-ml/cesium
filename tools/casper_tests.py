#!/usr/bin/env python

import multiprocessing
import subprocess
import glob


if __name__ == "__main__":
    from mltsp.Flask.flask_app import app

    p = multiprocessing.Process(target=app.run)
    p.start()

    tests = glob.glob('mltsp/tests/frontend/*.js')
    subprocess.call(['external/casperjs/bin/casperjs', '--verbose',
                     '--log-level=warning', 'test'] + tests)

    p.terminate()

