#!/usr/bin/env python

import multiprocessing
import subprocess
import glob
import os
import sys
import time


web_client_path = os.path.join(os.path.dirname(__file__), '../web_client')


def supervisor_status():
    """
    Return output from supervisorctl
    """
    return subprocess.check_output(['supervisorctl', 'status'],
                                   cwd=web_client_path).split(b'\n')[:-1]


def reset_db():
    """
    Re-initialize all tables in the test database
    """
    os.environ["MLTSP_TEST_DB"] = "1"
    from mltsp.Flask import flask_app
    flask_app.db_init(force=True)


if __name__ == '__main__':
    reset_db()

    web_client = subprocess.Popen('make', cwd=web_client_path)

    print('[test_frontend] Waiting for supervisord to launch all server processes...')

    timeout = 0
    while (timeout < 5) and
          (not all([b'RUNNING' in line for line in supervisor_status()])):
        time.sleep(1)
        timeout += 1

    if timeout == 5:
        print('[test_frontend] Could not launch server processes; terminating')
        sys.exit(-1)

    print('[test_frontend] Launching CasperJS...')
    tests = sorted(glob.glob('mltsp/tests/frontend/*.js'))
    subprocess.call(['external/casperjs/bin/casperjs', '--verbose',
                     '--log-level=debug', 'test'] + tests)

    print('[test_frontend] Terminating supervisord...')
    web_client.terminate()

    sys.exit(status)
