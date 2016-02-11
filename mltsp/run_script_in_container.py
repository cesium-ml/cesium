#!/usr/bin/python
# run_script_in_container.py
# Will be run inside Docker container

if __name__ == "__main__":
    # Run Cython setup script:
    # from subprocess import call
    # from mltsp.cfg import config
    # call(["%s/make" % config['paths']['project_path']])

    import argparse
    parser = argparse.ArgumentParser(description='MLTSP Docker scripts')
    parser.add_argument('--extract_custom_feats', action='store_true')
    parser.add_argument('--tmp_dir', dest='tmp_dir', action='store', type=str)
    args = parser.parse_args()

    import sys
    import os
    sys.path.append(args.tmp_dir)
    # Append mltsp package directory to path so it can be imported below
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    if args.extract_custom_feats:
        from mltsp.docker_scripts import docker_extract_custom_feats
        docker_extract_custom_feats.extract_custom_feats(args.tmp_dir)
    else:
        raise Exception("No valid script parameter passed to "
                        "run_script_in_container")
