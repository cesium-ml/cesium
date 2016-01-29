#!/usr/bin/env python

import subprocess
import glob
import os
import sys
import time

from os.path import join as pjoin

parent_path = os.path.abspath(pjoin(os.path.dirname(__file__), '..'))
web_client_path = os.path.abspath(pjoin(parent_path, 'web_client'))
casperjs_path = os.path.abspath(pjoin(parent_path, 'external/casperjs/bin/casperjs'))


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
    print('[test_frontend] Initialize test database')
    reset_db()

    subprocess.Popen(['mkdir', '-p', 'log'])
    subprocess.Popen('tail -f log/*.log', cwd=web_client_path, shell=True)
    web_client = subprocess.Popen('make', cwd=web_client_path)

    print('[test_frontend] Waiting for supervisord to launch all server processes...')

    timeout = 0
    while ((timeout < 5) and
           (not all([b'RUNNING' in line for line in supervisor_status()]))):
        time.sleep(1)
        timeout += 1

    if timeout == 5:
        print('[test_frontend] Could not launch server processes; terminating')
        sys.exit(-1)

    print('[test_frontend] Launching CasperJS...')
    tests = sorted(glob.glob(pjoin(parent_path, 'mltsp/tests/frontend/*.js')))
    status = subprocess.call([casperjs_path, '--verbose',
                             '--log-level=debug', 'test'] + tests, cwd=parent_path)

    print('[test_frontend] Terminating supervisord...')
    web_client.terminate()

    sys.exit(status)
