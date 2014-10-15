# docker_featurize.py

# to be run from INSIDE a docker container


import subprocess
import sys,os
sys.path.append("/home/mltp")
import custom_feature_tools as cft
import build_rf_model


from subprocess import Popen, PIPE, call
import cPickle

def build_model():
	# load pickled ts_data and known features
	with open("/home/mltp/copied_data_files/function_args.pkl","rb") as f:
		function_args = cPickle.load(f)
	
	results_str = build_rf_model.build_model(featureset_name=function_args["featureset_name"],featureset_key=function_args["featureset_key"],model_type=function_args["model_type"],in_docker_container=True)
	
	
	return results_str









if __name__=="__main__":
	
	results_str = build_model()
	print results_str
