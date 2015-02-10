#!/usr/bin/python
# run_script_in_container.py

if __name__ == "__main__":
    # Run Cython setup script:
    # from subprocess import call
    # from mltsp import cfg
    # call(["%s/make" % cfg.PROJECT_PATH])

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
