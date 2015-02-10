#!/usr/bin/python
# start_mltsp.py

from mltsp.Flask import flask_app as fa

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='MLTSP web server')
    parser.add_argument('--port', type=int, default=8000,
                        help='Port number (default 8000)')
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help='Address to listen on (default 127.0.0.1)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debugging (default: False)')
    parser.add_argument('--db-init', action='store_true',
                        help='Initialize the database')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()

    fa.run_main(args)
