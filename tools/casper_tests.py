#!/usr/bin/env python

import subprocess
import glob
import os
import socket
import sys
import time
try:
    import http.client as http
except ImportError:
    import httplib as http

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
    os.environ["CESIUM_TEST_DB"] = "1"
    from cesium.Flask import flask_app
    flask_app.db_init(force=True)


if __name__ == '__main__':
    print('[test_frontend] Initialize test database')
    reset_db()

    env = os.environ.copy()
    web_client = subprocess.Popen(['make', 'monitor'], cwd=web_client_path,
                                  env=env)

    print('[test_frontend] Waiting for supervisord to launch all server processes...')

    try:
        timeout = 0
        while ((timeout < 5) and
               (not all([b'RUNNING' in line for line in supervisor_status()]))):
            time.sleep(1)
            timeout += 1

        if timeout == 5:
            print('[test_frontend] Could not launch server processes; terminating')
            sys.exit(-1)

        for timeout in range(10):
            conn = http.HTTPConnection("localhost", 5000)
            try:
                conn.request('HEAD', '/')
                status = conn.getresponse().status
                if status == 200:
                    break
            except socket.error:
                pass
            time.sleep(1)
        else:
            raise socket.error("Could not connect to localhost:5000.")

        if status != 200:
            print('[test_frontend] Server status is {} instead of 200'.format(
                status))
            sys.exit(-1)
        else:
            print('[test_frontend] Verified server availability')

        print('[test_frontend] Launching CasperJS...')
        tests = sorted(glob.glob(pjoin(parent_path, 'cesium/tests/frontend/*.js')))
        status = subprocess.call([casperjs_path, '--verbose',
                                 '--log-level=debug', 'test'] + tests,
                                 cwd=parent_path, env=env)
    finally:
        print('[test_frontend] Terminating supervisord...')
        web_client.terminate()

    sys.exit(status)
