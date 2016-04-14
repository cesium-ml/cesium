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
casperjs_path = os.path.abspath(pjoin(parent_path, 'external/casperjs/bin/casperjs'))


def supervisor_status():
    """
    Return output from supervisorctl
    """
    return subprocess.check_output(['supervisorctl', 'status'],
                                   cwd=parent_path).split(b'\n')[:-1]


def reset_db():
    """
    Re-initialize all tables in the test database
    """
    os.environ["CESIUM_TEST_DB"] = "1"
    from cesium_app import flask_app
    flask_app.db_init(force=True)


if __name__ == '__main__':
    print('[test_frontend] Initialize test database')
    reset_db()

    env = os.environ.copy()
    web_client = subprocess.Popen(['make', 'monitor'], cwd=parent_path,
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

        from cesium_app.config import cfg
        docker_flag = '--docker=1' if cfg['docker']['enabled'] else \
                      '--docker=0'

        import cesium
        sample_data = pjoin(os.path.dirname(cesium.__file__),
                            'data/sample_data')
        data_flag = '--data-path={}'.format(sample_data)

        print('[test_frontend] Launching CasperJS...')
        tests = sorted(glob.glob(pjoin(parent_path, 'cesium_app/tests/frontend/*.js')))

        args = [casperjs_path, '--verbose', '--log-level=debug',
                'test'] + tests + [docker_flag, data_flag]
        print(' '.join(args))
        status = subprocess.call(args, cwd=parent_path, env=env)
    finally:
        print('[test_frontend] Terminating supervisord...')
        web_client.terminate()

    sys.exit(status)
