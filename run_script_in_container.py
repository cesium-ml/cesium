from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
#!/usr/bin/python
# run_script_in_container.py

if __name__ == "__main__":
    # Run Cython setup script:
    from subprocess import call
    import os
    from mltsp import cfg
    path_to_cython_setup_script = os.path.join(
        cfg.MLTSP_PACKAGE_PATH,
        "TCP/setup.py")
    call(["python3", path_to_cython_setup_script, "build_ext", "-i"])

    import argparse
    parser = argparse.ArgumentParser(description='MLTSP Docker scripts')
    parser.add_argument('--extract_custom_feats', action='store_true')
    parser.add_argument('--featurize', action='store_true')
    parser.add_argument('--build_model', action='store_true')
    parser.add_argument('--predict', action='store_true')
    args = parser.parse_args()

    if args.extract_custom_feats:
        from mltsp.docker_scripts import docker_extract_custom_feats
        docker_extract_custom_feats.extract_custom_feats()
    elif args.featurize:
        from mltsp.docker_scripts import docker_featurize
        docker_featurize.featurize()
    elif args.build_model:
        from mltsp.docker_scripts import docker_build_model
        docker_build_model.build_model()
    elif args.predict:
        from mltsp.docker_scripts import docker_predict
        docker_predict.predict()
    else:
        raise Exception("No valid script parameter passed to "
                        "run_script_in_container.py call.")
