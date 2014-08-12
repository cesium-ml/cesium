# disco_test.py

from operator import itemgetter
#from rpy2.robjects.packages import importr
#from rpy2 import robjects
import shutil
import sklearn as skl
from sklearn.ensemble import RandomForestClassifier as RFC
from sklearn.externals import joblib

import cPickle
import lc_tools
import sys, os
import cfg

import numpy as np
import datetime
import pytz
import tarfile
import glob
import tarfile
import disco_tools

try:
	from disco.core import Job, result_iterator
	from disco.util import kvgroup
	DISCO_INSTALLED = True
except Exception as theError:
	DISCO_INSTALLED = False

sys.path.append(cfg.TCP_INGEST_TOOLS_PATH)

import generate_science_features
import build_rf_model
import predict_class as predict



def map(fname_and_class, params):
	'''Generator, map procedure used for feature generation process (as opposed to feature generation to be used for model predictions). Yields a (file name, class name) tuple.
	'''
	fname, class_name = fname_and_class.strip("\n").strip().split(",")
	yield fname, class_name









def pred_map(fname, params):
	'''Generator, map procedure for feature generation in model predictions. Yields a (file name, unused random string) tuple.
	'''
	fname, junk = fname.strip("\n").strip().split(",")
	yield fname, junk





























def pred_featurize_reduce(iter, params):
	'''Generator, implementation of reduce stage in map-reduce process, for model prediction feature generation of time series data. iter is an iterable of tuples containing the file name of a time series data file to be used for featurization, and an unused placeholder string. Yields a two-element tuple containing the file name of the time series data set, and a two-element list containing the extracted features and the original time series data. 
	'''
	from copy import deepcopy
	featset_key = params['featset_key']
	sep = params['sep']
	custom_features_script = params['custom_features_script']
	meta_features = params['meta_features']
	
	import sys, os
	from disco.util import kvgroup
	
	import os
	import sys
	PATH_TO_PROJECT_DIRECTORY = os.path.join(os.path.expanduser("~"), "Dropbox/work_etc/mlweb")
	sys.path.append(PATH_TO_PROJECT_DIRECTORY)
	import cfg
	sys.path.append(cfg.TCP_INGEST_TOOLS_PATH)
	
	import generate_science_features
	import predict_class as predict
	import build_rf_model
	import lc_tools
	import custom_feature_tools as cft


	
	for fname,junk in kvgroup(sorted(iter)):
		if os.path.isfile(fname):
			f = open(fname)
		elif os.path.isfile(os.path.join(cfg.UPLOAD_FOLDER, fname)):
			f = open(os.path.join(cfg.UPLOAD_FOLDER, fname))
		else:
			print (fname if cfg.UPLOAD_FOLDER in fname else os.path.join(cfg.UPLOAD_FOLDER,fname)) + " is not a file..."
			if os.path.exists(os.path.join(cfg.UPLOAD_FOLDER, fname)) or os.path.exists(fname):
				print "But it does exist on the disk."
			else:
				print "and in fact it doesn't even exist."
			continue
		
		lines=f.readlines()
		f.close()
		ts_data = []
		for i in range(len(lines)):
			ts_data.append(lines[i].strip("\n").strip().split(sep))
			if len(ts_data[i]) < len(lines[i].strip("\n").strip().split(",")):
				ts_data[i] = lines[i].strip("\n").strip().split(",")
			if len(ts_data[i]) < len(lines[i].strip("\n").strip().split(" ")):
				ts_data[i] = lines[i].strip("\n").strip().split(" ")
			if len(ts_data[i]) < len(lines[i].strip("\n").strip().split("\t")):
				ts_data[i] = lines[i].strip("\n").strip().split("\t")
			
			for j in range(len(ts_data[i])):
				ts_data[i][j] = float(ts_data[i][j])
		del lines
		f = open(os.path.join(cfg.FEATURES_FOLDER,"%s_features.csv" % featset_key))
		features_in_model = f.readline().strip().split(',')
		f.close()
		
		features_to_use = features_in_model
		
		## generate features:
		if len(list(set(features_to_use) & set(cfg.features_list))) > 0:
			timeseries_features = lc_tools.generate_timeseries_features(deepcopy(ts_data),sep=sep,ts_data_passed_directly=True)
		else:
			timeseries_features = {}
		if len(list(set(features_to_use) & set(cfg.features_list_science))) > 0:
			science_features = generate_science_features.generate(ts_data=deepcopy(ts_data))
		else:
			science_features = {}
		if custom_features_script:
			custom_features = cft.generate_custom_features(custom_script_path=custom_features_script,path_to_csv=None,features_already_known=dict(timeseries_features.items() + science_features.items() + meta_features.items()),ts_data=deepcopy(ts_data))
		else:
			custom_features = {}
		
		all_features = dict(timeseries_features.items() + science_features.items() + custom_features.items() + meta_features.items())
		
		
		yield fname, [all_features, ts_data]











def featurize_reduce(iter, params):
	'''Generator, implementation of reduce stage in map-reduce process, for feature generation of time series data. iter is an iterable of tuples containing the file name of a time series data file to be used for featurization, and the associated class or type name. Yields a two-element tuple containing the file name of the time series data set, and dict of the extracted features. 
	'''
	from disco.util import kvgroup
	
	for fname,class_name in kvgroup(sorted(iter)):
		class_names = []
		for classname in class_name:
			class_names.append(classname)
		if len(class_names)==1:
			class_name = str(class_names[0])
		elif len(class_names)==0:
			print "CLASS_NAMES: " + str(class_names) + "\n" + "CLASS_NAME: " + str(class_name)
			yield "",""
		else:
			print "CLASS_NAMES: " + str(class_names) + "\n" + "CLASS_NAME: " + str(class_name) + "  - Choosing first class name in list."
			class_name = str(class_names[0])
		
		print "fname: " + fname + ", class_name: " + class_name
		import os
		import sys
		PATH_TO_PROJECT_DIRECTORY = os.path.join(os.path.expanduser("~"), "Dropbox/work_etc/mlweb")
		sys.path.append(PATH_TO_PROJECT_DIRECTORY)
		import cfg
		sys.path.append(cfg.TCP_INGEST_TOOLS_PATH)
		
		import generate_science_features
		import build_rf_model
		import lc_tools
		import custom_feature_tools as cft
		
		short_fname = fname.split("/")[-1].replace(("."+fname.split(".")[-1] if "." in fname.split("/")[-1] else ""),"")
		path_to_csv = os.path.join(cfg.UPLOAD_FOLDER, os.path.join("unzipped",fname))
		all_features = {}
		print "path_to_csv: " + path_to_csv
		if os.path.isfile(path_to_csv):
			print "Extracting features for " + fname
		
			## generate features:
			if len(list(set(params['features_to_use']) & set(cfg.features_list))) > 0:
				timeseries_features = lc_tools.generate_timeseries_features(path_to_csv,classname=class_name,sep=',')
			else:
				timeseries_features = {}
			if len(list(set(params['features_to_use']) & set(cfg.features_list_science))) > 0:
				science_features = generate_science_features.generate(path_to_csv=path_to_csv)
			else:
				science_features = {}
			if params['custom_script_path']:
				custom_features = cft.generate_custom_features(custom_script_path=params['custom_script_path'],path_to_csv=path_to_csv,features_already_known=dict(timeseries_features.items() + science_features.items() + (params['meta_features'][fname].items() if fname in params['meta_features'] else {}.items())))
			else:
				custom_features = {}
			
			all_features = dict(timeseries_features.items() + science_features.items() + custom_features.items() + [("class",class_name)])
		
		else:
			print fname + " is not a file."
			yield "", ""
		
		
		
		
		yield short_fname, all_features





def process_featurization_with_disco(input_list,params,partitions=4):
	'''
	Called from within featurize_in_parallel.
	Returns disco.core.result_iterator
	Arguments:
		input_list: path to file listing filename,class_name for each individual time series data file.
		params: dictionary of parameters to be passed to each map & reduce function.
		partitions: Number of nodes/partitions in system.
	'''
	from disco.core import Job, result_iterator
	job = Job().run(input=input_list,
					map=map,
					partitions=partitions,
					reduce=featurize_reduce,
					params=params)
	
	result = result_iterator(job.wait(show=True))
	return result






def process_prediction_data_featurization_with_disco(input_list,params,partitions=4):
	'''
	Called from within featurize_prediction_data_in_parallel
	Returns disco.core.result_iterator
	Arguments:
		input_list: path to file listing filename,unused_string for each individual time series data file.
		params: dictionary of parameters to be passed to each map & reduce function.
		partitions: Number of nodes/partitions in system.
	'''
	from disco.core import Job, result_iterator
	job = Job().run(input=input_list,
					map=pred_map,
					partitions=partitions,
					reduce=pred_featurize_reduce,
					params=params)
	
	result = result_iterator(job.wait(show=True))
	return result






def featurize_prediction_data_in_parallel(newpred_file_path,featset_key,sep=',',custom_features_script=None,meta_features={}):
	'''Utilizes Disco's map-reduce framework to generate features on multiple time series data files in parallel. The generated features are returned, along with the time series data, in a dict (with file names as keys). 
	Required arguments:
		newpred_file_path: path to the zip file containing time series data files to be featurized
		featset_key: (str) rethinkDB key of the feature set associated with the model to be used in prediction
	Keyword arguments: 
		sep: string (default = ",") - value-delimiter in time series data files
		custom_features_script: path to custom features script to be used in feature generation, else None
		meta_features: dict of associated meta features
	'''
	print "FEATURIZE_PRED_DATA_IN_PARALLEL: newpred_file_path =", newpred_file_path
	the_tarfile = tarfile.open(newpred_file_path)
	the_tarfile.extractall(path=newpred_file_path.replace(newpred_file_path.split("/")[-1],""))
	all_fnames = the_tarfile.getnames()
	print "ALL_FNAMES:", all_fnames
	
	big_features_and_tsdata_dict = {}
	
	params={"featset_key":featset_key,"sep":sep,"custom_features_script":custom_features_script,"meta_features":meta_features}
	
	with open(os.path.join(cfg.UPLOAD_FOLDER,"disco_temp_inputfile.txt"),"w") as f:
		for fname in all_fnames:
			f.write(fname+",unknown\n")
	
	disco_iterator = process_prediction_data_featurization_with_disco(input_list=[f.name],params=params,partitions=4)
	
	for k,v in disco_iterator:
		fname = k
		features_dict, ts_data = v
		if fname != "":
			big_features_and_tsdata_dict[fname] = {"features_dict":features_dict, "ts_data":ts_data}
	
	
	print "DONE!!!"
	os.remove(f.name)
	
	return big_features_and_tsdata_dict










def featurize_in_parallel(headerfile_path, zipfile_path, features_to_use = [], is_test = False, custom_script_path = None, meta_features={}):
	'''Utilizes Disco's map-reduce framework to generate features on multiple time series data files in parallel. The generated features are returned in a dict (with file names as keys). 
	Required arguments:
		headerfile_path: path to header file containing file names, class names, and meta data
		zipfile_path: path to the tarball of individual time series files to be used for feature generation
	Keyword arguments: 
		features_to_use: list of feature names to be generated. Default is an empty list, which results in all available features being used
		is_test: boolean indicating whether to do a test run of only the first five time-series files. Defaults to False
		custom_script_path: path to Python script containing methods for the generation of any custom features
		meta_features: dict of associated meta features
	'''
	
	all_features_list = cfg.features_list[:] + cfg.features_list_science[:]
	
	
	if len(features_to_use)==0:
		features_to_use = all_features_list
	
	headerfile = open(headerfile_path,'r')
	fname_class_dict = {}
	objects = []
	line_no = 0
	for line in headerfile:
		if len(line)>1 and line[0] not in ["#","\n"] and line_no > 0 and not line.isspace():
			if len(line.split(',')) >= 2:
				fname,class_name = line.strip('\n').split(',')[:2]
				fname_class_dict[fname] = class_name
		line_no += 1
	headerfile.close()
	
	zipfile = tarfile.open(zipfile_path)
	zipfile.extractall(path=os.path.join(cfg.UPLOAD_FOLDER,"unzipped"))
	all_fnames = zipfile.getnames()
	num_objs = len(fname_class_dict)
	zipfile_name = zipfile_path.split("/")[-1]
	
	count=0
	print "Generating science features..."
	
	
	fname_class_list = list(fname_class_dict.iteritems())
	input_fname_list = all_fnames
	longfname_class_list = []
	if is_test:
		all_fnames = all_fnames[:4]
	for i in range(len(all_fnames)):
		short_fname = all_fnames[i].replace("."+all_fnames[i].split(".")[-1],"").split("/")[-1].replace("."+all_fnames[i].split(".")[-1],"").strip()
		if short_fname in fname_class_dict:
			longfname_class_list.append([all_fnames[i],fname_class_dict[short_fname]])
		elif all_fnames[i] in fname_class_dict:
			longfname_class_list.append([all_fnames[i],fname_class_dict[all_fnames[i]]])
	with open(cfg.PATH_TO_PROJECT_DIRECTORY+"/disco_inputfile.txt","w") as f:
		for fname_classname in longfname_class_list:
			f.write(",".join(fname_classname)+"\n")
	
	
	params = {}
	params['fname_class_dict'] = fname_class_dict
	params['features_to_use'] = features_to_use
	params['meta_features'] = meta_features
	params['custom_script_path'] = custom_script_path
	
	disco_results = process_featurization_with_disco(input_list=[f.name],params=params)
	
	fname_features_dict = {}
	for k,v in disco_results:
		fname_features_dict[k] = v
	
	os.remove(f.name)
	print "Done."
	
	return fname_features_dict
	






## the test version:
def featurize_in_parallel_newtest(headerfile_path, zipfile_path, features_to_use = [], is_test = False, custom_script_path = None, meta_features={}):
	'''Utilizes Disco's map-reduce framework to generate features on multiple time series data files in parallel. The generated features are returned in a dict (with file names as keys). 
	Required arguments:
		headerfile_path: path to header file containing file names, class names, and meta data
		zipfile_path: path to the tarball of individual time series files to be used for feature generation
	Keyword arguments: 
		features_to_use: list of feature names to be generated. Default is an empty list, which results in all available features being used
		is_test: boolean indicating whether to do a test run of only the first five time-series files. Defaults to False
		custom_script_path: path to Python script containing methods for the generation of any custom features
		meta_features: dict of associated meta features
	'''
	
	all_features_list = cfg.features_list[:] + cfg.features_list_science[:]
	
	
	if len(features_to_use)==0:
		features_to_use = all_features_list
	
	headerfile = open(headerfile_path,'r')
	fname_class_dict = {}
	objects = []
	line_no = 0
	for line in headerfile:
		if len(line)>1 and line[0] not in ["#","\n"] and line_no > 0 and not line.isspace():
			if len(line.split(',')) >= 2:
				fname,class_name = line.strip('\n').split(',')[:2]
				fname_class_dict[fname] = class_name
		line_no += 1
	headerfile.close()
	
	zipfile = tarfile.open(zipfile_path)
	zipfile.extractall(path=os.path.join(cfg.UPLOAD_FOLDER,"unzipped"))
	all_fnames = zipfile.getnames()
	num_objs = len(fname_class_dict)
	zipfile_name = zipfile_path.split("/")[-1]
	
	count=0
	print "Generating science features..."
	
	
	from disco.core import DDFS
	# push to ddfs
	print "Pushing all files to DDFS..."
	
	
	
	
	print "Done pushing files to DDFS."
	
	# pass tags (or urls?) as input_list
	
	
	'''
	fname_class_list = list(fname_class_dict.iteritems())
	input_fname_list = all_fnames
	longfname_class_list = []
	if is_test:
		all_fnames = all_fnames[:4]
	for i in range(len(all_fnames)):
		short_fname = all_fnames[i].replace("."+all_fnames[i].split(".")[-1],"").split("/")[-1].replace("."+all_fnames[i].split(".")[-1],"").strip()
		if short_fname in fname_class_dict:
			longfname_class_list.append([all_fnames[i],fname_class_dict[short_fname]])
		elif all_fnames[i] in fname_class_dict:
			longfname_class_list.append([all_fnames[i],fname_class_dict[all_fnames[i]]])
	with open(cfg.PATH_TO_PROJECT_DIRECTORY+"/disco_inputfile.txt","w") as f:
		for fname_classname in longfname_class_list:
			f.write(",".join(fname_classname)+"\n")
	'''
	
	params = {}
	params['fname_class_dict'] = fname_class_dict
	params['features_to_use'] = features_to_use
	params['meta_features'] = meta_features
	params['custom_script_path'] = custom_script_path
	
	disco_results = process_featurization_with_disco(input_list=[f.name],params=params)
	
	fname_features_dict = {}
	for k,v in disco_results:
		fname_features_dict[k] = v
	
	os.remove(f.name)
	print "Done."
	
	return fname_features_dict
	
