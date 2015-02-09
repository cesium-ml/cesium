#!/usr/bin/env python
"""
   v0.1 Generate Weka classification model using a set of VOSource.xmls and a
        prefered classifier type.  Should also classify another set of
        VOSource.xmls using the new or a passed-in trained classification model.


NOTE: Should have ipcluster/ipengines running:
      ./ipython_cluster_setup.py

NOTE: There should be a GridWeka2 client instance running to allow fast "folding"
      cd ~/src/install           # where GridWeka2.jar exists
      /usr/lib/jvm/java-6-sun-1.6.0.03/bin/java -Xmx16000m -cp GridWeka2.jar weka.ucd.WekaServer 6714 10
  - Can make use of this with GUI Weka by using:
      cd ~/src/install           # where GridWeka2.jar exists
      /usr/lib/jvm/java-6-sun-1.6.0.03/bin/java -Xmx12000m -cp GridWeka2.jar weka.gui.GUIChooser

##### Modes: #####
     1) Generate .model using training VOSource.xmls and a chosen classifier
       -t train_xml_dir=<path>   weka_classifier=<string> weka_model_path=<path>
     2) Classify VOSource.xmls using trained Weka classifier
       -c classif_xml_dir=<path> weka_classifier=<string> weka_model_path=<path>
     3) Do 1 & 2 using training vosource.xmls, to-classify xmls and
                  chosen classifier.
       -a train_xml_dir=<path>   weka_classifier=<string> weka_model_path=<path>
          classif_xml_dir=<path>

##### Current Params: #####
Usage: generate_weka_classifiers.py cmd [options]

Options:
  -h, --help            show this help message and exit
  -f, --make_feats_for_tutor      Retrieve VOSource.XML from TUTOR and generates
                        features.  Takes several hours to execute on single
                        core machines.  Generally run on 8-core transx.  This
                        places new xml in $TCP_DATA_DIR/.  Requires prior
                        execution of testsute.py.
  -t, --train_mode      Generate Weka .arff using training VOSource.xmls.
  -c, --classify_mode   Classify VOSource.xmls using trained Weka classifier
                        .model.  Requires: -y -x
  -g, --generate_model  Generate Weka .model using training training .arff and
                        a chosen classifier.
  -w WEKA_CLASSIFIER, --weka_classifier=WEKA_CLASSIFIER
                        Weka classifier name(s)
  -x TRAIN_XML_DIR, --train_xml_dir=TRAIN_XML_DIR
                        Dirpath to VOSource xmls for classifier training
  -y CLASSIF_XML_DIR, --classif_xml_dir=CLASSIF_XML_DIR
                        Dirpath to VOSource xmls for classification
  -m WEKA_MODEL_PATH, --weka_model_path=WEKA_MODEL_PATH
                        Dirpath to Weka trained .model file
  -o TRAIN_ARFF_PATH, --train_arff_path=TRAIN_ARFF_PATH
                        Filepath to write training set .arff file

##### Example Usage: #####

### Generate .model using trainig .arff:
./generate_weka_classifiers.py -g -m /home/dstarr/scratch/train_all_31class_100feat_4650source__weka.classifiers.trees.J48.model -o /home/dstarr/scratch/train_all_31class_100feat_4650source.arff

# # # # #
### LCOGT cch1 generation of noisified based classifier using TUTOR data:
#    -> this requires a manual PDB hack to spawn off bpsh tasks on cch1 cluster
./generate_weka_classifiers.py -u frq17.9  --n_noisified_per_orig_vosource=50 --n_epochs=20 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --generate_noisified --regenerate_features 

# do PDB cch1 parallel bpsh spawning trick... 
# Afterwards (1-2 hrs) run:   (below takes 5 mins)
./generate_weka_classifiers.py -u frq17.9  --n_noisified_per_orig_vosource=50 --n_epochs=20 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --train_mode --generate_model
# # # # #


"""
from __future__ import print_function
from __future__ import absolute_import
import sys, os
from optparse import OptionParser
import time
import glob
import copy
import random

sys.path.append(os.environ.get("TCP_DIR") + '/Software/feature_extract/MLData')
import arffify

try:
    from IPython.kernel import client
except:
    pass

default_model_fpath = os.path.expandvars("$TCP_DATA_DIR/trained_weka.model")


def parse_options():
    """ Deal with parsing command line options & --help.  Return options object.
    """
    parser = OptionParser(usage="usage: %prog cmd [options]")
    parser.add_option("-f","--make_feats_for_tutor",
                      dest="make_feats_for_tutor", \
                      action="store_true", default=False, \
                      help="Retrieve VOSource.XML from TUTOR and generates features.  Takes several hours to execute on single core machines.  Generally run on 8-core transx.  This places new xml in $TCP_DATA_DIR/.  Requires prior execution of testsuite.py.")
    parser.add_option("-u","--using_pars_dirname",
                      dest="using_pars_dirname", \
                      action="store", default=None, \
                      help="Given a name for a new scratch directory, do: Noisify, Generate features and Weka .arff using hardcoded parameters.")
    parser.add_option("-n","--generate_noisified",
                      dest="generate_noisified", \
                      action="store_true", default=False, \
                      help="Generate noisified vosource.xmls (with no feats) using example vosource.xmls")
    parser.add_option("-r","--regenerate_features",
                      dest="regenerate_features", \
                      action="store_true", default=False, \
                      help="Re-generate VOSource.xmls residing in (-2) dirpath")
    parser.add_option("-t","--train_mode",
                      dest="train_mode", \
                      action="store_true", default=False, \
                      help="Generate Weka .arff using training VOSource.xmls.")
    parser.add_option("-c","--classify_mode",
                      dest="classify_mode", \
                      action="store_true", default=False, \
                      help="Classify VOSource.xmls using trained Weka classifier .model.  Requires: -y -x")
    parser.add_option("-g","--generate_model",
                      dest="generate_model", \
                      action="store_true", default=False, \
                      help="Generate Weka .model using training training .arff and a chosen classifier.")
    parser.add_option("-w","--weka_classifier",
                      dest="weka_classifier", \
                      action="store", default=False, \
                      help="Weka classifier name(s)")
    parser.add_option("-x","--train_xml_dir",
                      dest="train_xml_dir", \
                      action="store", \
                      default=os.path.expandvars("$TCP_DATA_DIR/"), \
                      help="Dirpath to VOSource xmls for classifier training")
    parser.add_option("-z","--unfeat_xml_dir",
                      dest="unfeat_xml_dir", \
                      action="store", \
                      default=os.path.expandvars("$TCP_DATA_DIR/generated_vosource"), \
                      help="Dirpath to where raw unfeatured VOSource xmls exist")
    parser.add_option("-y","--classif_xml_dir",
                      dest="classif_xml_dir", \
                      action="store", default=False, \
                      help="Dirpath to VOSource xmls for classification")
    parser.add_option("-m","--weka_model_path",
                      dest="weka_model_path", \
                      action="store", default=default_model_fpath, \
                      help="Dirpath to Weka trained .model file")
    parser.add_option("-o","--train_arff_path",
                      dest="train_arff_path", \
                      action="store", default="/tmp/train_output.arff", \
                      help="Filepath to write training set .arff file")
    parser.add_option("-1","--n_epochs",
                      dest="n_epochs", \
                      action="store", default=None, \
                      help="")
    parser.add_option("-2","--n_noisified_per_orig_vosource",
                      dest="n_noisified_per_orig_vosource", \
                      action="store", default=None, \
                      help="")
    parser.add_option("-3","--n_sources_needed_for_class_inclusion",
                      dest="n_sources_needed_for_class_inclusion", \
                      action="store", default=None, \
                      help="")
    parser.add_option("-4","--fit_metric_cutoff",
                      dest="fit_metric_cutoff", \
                      action="store", default=None, \
                      help="")
    parser.add_option("-s","--use_srcid_times",
                      dest="use_srcid_times", 
                      action="store", default=None,
                      help="The srcid whose time array will be used for noisification cadence, rather than using a generated cadence")

    (options, args) = parser.parse_args()
    print("For help use flag:  --help") # KLUDGE since always: len(args) == 0
    return options


def parse_confuse_matrix_generate_costmatrix(weka_ZeroR_confuse_matrix_outfpath, cost_matrix_fpath):
    """ Using the ZeroR classifier stdio output, generates a cost_matrix,
    which is written to file for more complex classifier's use.
    """
    lines = open(weka_ZeroR_confuse_matrix_outfpath).readlines()
    i_begin = 0
    i_final = 0
    for i,line in enumerate(lines):
        if ('=== Confusion Matrix ===' in line) and (i_begin == 0):
            i_begin = i + 1
        elif '=== Stratified cross-validation ===' in line:
            i_final = i - 1

    temp_fpath = weka_ZeroR_confuse_matrix_outfpath + '.tmp'
    fp = open(temp_fpath, 'w')
    #for line in lines[i_begin:i_final]:
    fp.writelines(lines[i_begin:i_final])
    fp.close()
    exec_str = os.path.expandvars("$TCP_DIR/Software/feature_extract/MLData/heatmap_confustion_matrix.py %s %s" % \
                                  (temp_fpath, cost_matrix_fpath))
    os.system(exec_str)
    

class Parallel_Arff_Maker:
    """ Class which spawns off ipengine tasks similar to arffify.Maker.run(),
    whose results are then combined to create a single .arrf file which
    represents the features in the given vosource.xml files. 

    """

    def __init__(self, pars={}):
        self.pars = pars
        # TODO:             - initialize ipython modules
        self.mec = client.MultiEngineClient()
        #self.mec.reset(targets=self.mec.get_ids()) # Reset the namespaces of all engines
        self.tc = client.TaskClient()
	self.task_id_list = []

        #### 2011-01-21 added:
        self.mec.reset(targets=self.mec.get_ids())
        self.mec.clear_queue()
        self.mec.clear_pending_results()
        self.tc.task_controller.clear()


    def initialize_clients(self):
        """ Instantiate ipython1 clients, import all module dependencies.
        """
	#task_str = """cat = os.getpid()"""
	#taskid = self.tc.run(client.StringTask(task_str, pull="cat"))
	#time.sleep(2)
	#print self.tc.get_task_result(taskid, block=False).results
	#print 'hey'


        # 20090815(before): a = arffify.Maker(search=[], skip_class=False, local_xmls=True, convert_class_abrvs_to_names=False, flag_retrieve_class_abrvs_from_TUTOR=True, dorun=False)

        exec_str = """
import sys, os
sys.path.append(os.environ.get('TCP_DIR') + '/Software/feature_extract/MLData')
import arffify
a = arffify.Maker(search=[], skip_class=False, local_xmls=True, convert_class_abrvs_to_names=False, flag_retrieve_class_abrvs_from_TUTOR=False, dorun=False)
"""
	###
	###a = arffify.Maker(dorun=False)
	###a = arffify.Maker(search=[], skip_class=False, local_xmls=True, convert_class_abrvs_to_names=False,flag_retrieve_class_abrvs_from_TUTOR=True,dorun=False)
        #print exec_str
        self.mec.execute(exec_str)
	time.sleep(2) # This may be needed.

	# testing:
	#task_str = """cat = os.getpid()"""
	#taskid = self.tc.run(client.StringTask(task_str, pull="cat"))
	#time.sleep(1)
	#print self.tc.get_task_result(taskid, block=False).results
	#print 'yo'


    def spawn_off_arff_line_tasks(self, vosource_xml_dirpath):
        """ This spawns off ipython task clients which
	take vosource.xml fpaths and generate feature/class structure
	which will be used to create a .arff line.
	The task results should be 'pulled' and then inserted into a final
	Weka .arff file.
	"""
        ##### For testing:
        skipped_deb_srcids = ['12645', '12646', '12649', '12653', '12655', '12656', '12658', '12660', '12670', '12675', '12700', '12745', '12766', '12797', '12798', '12806', '12841', '12847', '12849', '12850', '12851', '12852', '12853', '12854', '12856', '12858', '12861', '12864', '12868', '12869', '12870', '12875', '12879', '12882', '12885', '12886', '12888', '12890', '12891', '12893', '12895', '12901', '12904', '12907', '12909', '12914', '12915', '12921', '12923', '12924', '12928', '12930', '12932', '12933', '12934', '12936', '12941', '12948', '12950', '12957', '12958', '12960', '12961', '12970', '13007', '13024', '13034', '13059', '13076', '13078', '13091', '13094', '13119', '13122', '13128', '13156', '13170', '13172', '13239', '13242', '13246', '13247', '13261', '13268', '13280', '13324', '13333', '13354', '13360', '13362', '13369', '13374', '13402', '13418', '13420', '13421', '13423', '13424', '13425', '13427', '13429', '13432', '13433', '13439', '13440', '13442', '13443', '13444', '13448', '13458', '13462', '13465', '13466', '13469', '13471', '13476', '13477', '13478', '13480', '13481', '13483', '13484', '13491', '13493', '13495', '13500', '13502', '13505', '13511', '13519', '13520', '13521', '13530', '13535', '13543', '13544', '13552', '13553', '13560', '13561', '13564', '13565', '13571', '13573', '13577', '13580', '13582', '13591', '13594', '13596', '13602', '13607', '13608', '13616', '13618', '13622', '13623', '13625', '13630', '13632', '13638', '13642', '13646', '13647', '13650', '13656', '13657', '13668', '13676', '13678', '13680', '13686', '13687', '13689', '13690', '13692', '13694', '13695', '13698', '13701', '13703', '13704', '13708', '13712', '13716', '13717', '13718', '13719', '13722', '13723', '13731', '13733', '13739', '13740', '13743', '13744', '13747', '13748', '13750', '13760', '13763', '13774', '13776', '13777', '13780', '13782', '13783', '13784', '13786', '13788', '13793', '13800', '13804', '13806', '13810', '13814', '13815', '13819', '13824', '13826', '13832', '13833', '13838', '13843', '13847', '13851', '13854', '13858', '13860', '13869', '13873', '13881', '13882', '13885', '13888', '13889', '13890', '13892', '13893', '13894', '13896', '13898', '13900', '13906', '13911', '13922', '13927', '13928', '13929', '13936', '13938', '13942', '13944', '13951', '13955', '13957', '13958', '13959', '13962', '13965', '13972', '13974', '13988', '13989', '13996', '13997', '13998', '14004', '14006', '14009', '14010', '14017', '14018', '14024', '14025', '14028', '14029', '14032', '14035', '14043', '14047', '14048', '14051', '14055', '14056', '14065', '14066', '14070', '14071', '14072', '14087', '14088', '14089', '14093', '14095', '14104', '14108', '14109', '14113', '14117', '14120', '14122', '14125', '14129', '14133', '14136', '14137', '14151', '14155', '14157', '14163', '14166', '14167', '14168', '14174', '14175', '14181', '14182', '14186', '14191', '14194', '14198', '14205', '14206', '14216', '14218', '14219', '14225', '14226', '14234', '14239', '14243', '14244', '14246', '14247', '14248', '14250', '14251', '14255', '14256', '14263', '14269', '14275', '14280', '14282']
        from . import dotastro_sciclass_tools
        dst = dotastro_sciclass_tools.Dotastro_Sciclass_Tools()
        dst.make_tutor_db_connection()
        #####

        xml_fpath_list = glob.glob(vosource_xml_dirpath + '/*xml')
        # KLUDGE: This can potentially load a lot of xml-strings into memory:
        for xml_fpath in xml_fpath_list:
	    fname = xml_fpath[xml_fpath.rfind('/')+1:xml_fpath.rfind('.')]
            num = fname # Seems OK: ?CAN I just use the filename rather than the sourceid?  # xml_fname[:xml_fname.rfind('.')]
            #srcid_xml_tuple_list.append((num, xml_fpath))

	    #task_str = """cat = os.getpid()"""
	    #taskid = self.tc.run(client.StringTask(task_str, pull="cat"))
	    #time.sleep(1)
	    #print self.tc.get_task_result(taskid, block=False).results
	    #print 'yo'

            ##### For testing:
            #if "100017522.xml" in xml_fpath:
            #    print "yo"
            if 0:
                import pdb; pdb.set_trace()
                print()
                num_orig_str = str(int(num) - 100000000)
                if num_orig_str in skipped_deb_srcids:
                    #print num_orig_str
                    select_str = "select sources.source_id, sources.project_id, sources.source_name, sources.class_id, sources.pclass_id, project_classes.pclass_name, project_classes.pclass_short_name from Sources join project_classes using (pclass_id) where source_id = %s" % (num_orig_str)
                    dst.cursor.execute(select_str)
                    results = dst.cursor.fetchall()

                    a = arffify.Maker(search=[], skip_class=False, local_xmls=True, convert_class_abrvs_to_names=False, flag_retrieve_class_abrvs_from_TUTOR=False, dorun=False)
                    out_dict = a.generate_arff_line_for_vosourcexml(num=str(num), xml_fpath=xml_fpath)
                    print('!!!', results[0])
                else:
                    try:
                        a = arffify.Maker(search=[], skip_class=False, local_xmls=True, convert_class_abrvs_to_names=False, flag_retrieve_class_abrvs_from_TUTOR=False, dorun=False)
                        out_dict = a.generate_arff_line_for_vosourcexml(num=str(num), xml_fpath=xml_fpath)
                    except:
                        print("barf on some xml:", xml_fpath)
                    
                
            #print xml_fpath
            #continue
            #####

            if 1:
                exec_str = """out_dict = a.generate_arff_line_for_vosourcexml(num="%s", xml_fpath="%s")
                """ % (str(num), xml_fpath)
                #print exec_str
                try:
                    taskid = self.tc.run(client.StringTask(exec_str, \
                                            pull='out_dict', retries=3))
                    self.task_id_list.append(taskid)
                except:
                    print("EXCEPT!: taskid=", taskid, exec_str)

	    #task_str = """cat = os.getpid()"""
	    #taskid = self.tc.run(client.StringTask(task_str, pull="cat"))
	    ##time.sleep(1)
	    #print self.tc.get_task_result(taskid, block=False).results
	    #print 'yo'


    def condense_task_results_and_form_arff(self):
        """
	"""
	master_list = []
	master_features_dict = {}
	all_class_list = []
        master_classes_dict = {}
	
	while ((self.tc.queue_status()['scheduled'] > 0) or
 	       (self.tc.queue_status()['pending'] > 0)):
            tasks_to_pop = []
	    for task_id in self.task_id_list:
	        temp = self.tc.get_task_result(task_id, block=False)
                if temp is None:
                    continue
                temp2 = temp.results
                if temp2 is None:
                    continue
                results = temp2.get('out_dict',None)
                if results is None:
                    continue # skip these sources (I think generally UNKNOWN ... science classes)
                out_dict = results
		if len(out_dict) > 0:
		    tasks_to_pop.append(task_id)
		    master_list.append(out_dict)
		    all_class_list.append(out_dict['class'])
                    master_classes_dict[out_dict['class']] = 0
		    for feat_tup in out_dict['features']:
		        master_features_dict[feat_tup] = 0 # just make sure there is this key in the dict.  0 is filler
	    for task_id in tasks_to_pop:
	        self.task_id_list.remove(task_id)
            print(self.tc.queue_status())
            print('Sleep... 3  in generate_weka_classifiers.py')
	    time.sleep(3)

        #for i in self.task_id_list:
        #    print i, type(self.tc.get_task_result(i, block=False).results.get('out_dict',{}))

        if len(master_list) < self.tc.queue_status()['succeeded']:
            tasks_to_pop = []
	    for task_id in self.task_id_list:
	        # TODO: try/except this: ???
	        temp = self.tc.get_task_result(task_id, block=False)
                if temp is None:
                    continue
                temp2 = temp.results
                if temp2 is None:
                    continue
                results = temp2.get('out_dict',None)
                #results = temp.results.get('out_dict',None)
                if results is None:
                    continue # skip these sources (I think generally UNKNOWN ... science classes)
                out_dict = results
		if len(out_dict) > 0:
		    tasks_to_pop.append(task_id)
		    master_list.append(out_dict)
		    all_class_list.append(out_dict['class'])
                    master_classes_dict[out_dict['class']] = 0
		    for feat_tup in out_dict['features']:
		        master_features_dict[feat_tup] = 0 # just make sure there is this key in the dict.  0 is filler

        master_features = master_features_dict.keys()
        master_classes = master_classes_dict.keys()
	# master_classes
	# master_list
	return (master_features, all_class_list, master_classes, master_list)

    
    def write_arff_using_Maker(self, master_features, all_class_list, \
			       master_classes, master_list, \
			       out_arff_fpath='', \
                               n_sources_needed_for_class_inclusion=10):
        """ Use arffify.py method to write a .arrf file.
	"""
	a = arffify.Maker(search=[], skip_class=False, local_xmls=True, 
                          convert_class_abrvs_to_names=False,
                          flag_retrieve_class_abrvs_from_TUTOR=False,
                          dorun=False, add_srcid_to_arff=True)
	a.master_features = master_features
	a.all_class_list = all_class_list
	a.master_classes = master_classes
	a.master_list = master_list
	a.write_arff(outfile=out_arff_fpath, \
                     remove_sparse_classes=True, \
                     n_sources_needed_for_class_inclusion=n_sources_needed_for_class_inclusion)#, classes_arff_str='', remove_sparse_classes=False)
	

    def generate_arff_using_xmls(self, vosource_xml_dirpath='', out_arff_fpath='', \
                                 n_sources_needed_for_class_inclusion=10):
        """ Spawn off ipengine tasks similar to arffify.Maker.run(),
    whose results are then combined to create a single .arrf file which
    represents the features in the given vosource.xml files.
        """
	self.initialize_clients()
	self.spawn_off_arff_line_tasks(vosource_xml_dirpath)
	(master_features, all_class_list, master_classes, master_list) = \
			        self.condense_task_results_and_form_arff()
	self.write_arff_using_Maker(master_features, all_class_list, \
				    master_classes, master_list, \
				    out_arff_fpath=out_arff_fpath, \
                                    n_sources_needed_for_class_inclusion=n_sources_needed_for_class_inclusion)


if __name__ == '__main__':

    options = parse_options()
    pars = { \
        'archive_dirpath':os.path.expandvars("$HOME/scratch/Noisification"), # where all run dirs are contained.
        'reference_xml_dir':os.path.expandvars("$HOME/scratch/vosource_xml_writedir"),
        'gridweka2_jar_dirpath':os.path.expandvars("$HOME/src/install/"),
        'weka_ZeroR_confuse_matrix_outfpath':'/tmp/tcp.weka_ZeroR_confuse_matrix.out',
        'n_epochs_in_vosource':50,
        'n_noisified_per_orig_vosource':5,
        'n_sources_needed_for_class_inclusion': 5 * 3, # e.g.: 5 noisified versions of 10 sources
        'fit_metric_cutoff':0.15, # metric Chris Klein uses where smaller means noisified models
        'tmpfile_suffix':str(random.randint(0,1000000000))
        }
    if options.n_epochs != None:
        pars['n_epochs_in_vosource'] = int(options.n_epochs)
    if options.n_noisified_per_orig_vosource != None:
        pars['n_noisified_per_orig_vosource'] = int(options.n_noisified_per_orig_vosource)
    if options.n_sources_needed_for_class_inclusion != None:
        pars['n_sources_needed_for_class_inclusion'] = int(options.n_sources_needed_for_class_inclusion)
    if options.fit_metric_cutoff != None:
        pars['fit_metric_cutoff'] = float(options.fit_metric_cutoff)

    if options.using_pars_dirname:

        run_name = "%0.2dnois_%0.2depch_%0.3dneed_%0.3fmtrc_%s" % (\
                          int(options.n_noisified_per_orig_vosource),
                          int(options.n_epochs),
                          int(options.n_sources_needed_for_class_inclusion),
                          float(options.fit_metric_cutoff),
                          options.using_pars_dirname)

        run_dirpath = pars['archive_dirpath'] + '/' + run_name
        os.system("mkdir -p %s" % (run_dirpath))
        # TODO: the following uption may be a dir in some other non run_dirpath? :
        options.reference_xml_dir = pars['reference_xml_dir'] # contains xmls which are to be noisified
        options.unfeat_xml_dir = run_dirpath + '/generated_vosource' # contains noisified xmls which need to be feat'd
        options.train_xml_dir = run_dirpath + '/featured_vosource' # contains feat'd xmls used to generate .arff file
        options.train_arff_path = run_dirpath + '/noisified_for_training.arff'
        options.weka_model_path = run_dirpath + '/' + run_name + '.model'
        options.n_epochs = pars['n_epochs_in_vosource']
        options.archive_dirpath = run_dirpath
        options.archive_dirpath = pars['archive_dirpath'] + '/' + run_name
        options.n_sources_needed_for_class_inclusion = pars['n_sources_needed_for_class_inclusion']
        options.cost_matrix_fpath = run_dirpath + '/cost_matrix.cost'
        options.progenitor_class_list_fpath = os.path.expandvars("$HOME/src/TCP/Software/Noisification/all_progenitor_class_list.txt") #"$HOME/scratch/noise_progenitor_lists/all_progenitor_class_list.txt.ok_and_good.noskipclasses")
        #options.generate_noisified =  True
        #options.regenerate_features = False # True
        #options.train_mode =          False #True  # This is where the .arff is generated
        #options.generate_model =      False #True


    if options.generate_noisified:
        # TODO: pass in : (prefered filter)
        if options.use_srcid_times != None:
            use_srcid_times_str = "--use_srcid_times=%s" % (options.use_srcid_times)
        else:
            use_srcid_times_str = ""
        exec_str = os.path.expandvars("${TCP_DIR}Software/Noisification/generate_noisy_tutor.py --reference_xml_dir=%s --n_noisified_per_orig_vosource=%d --noisified_xml_final_dirpath=%s --n_epochs_in_vosource=%d --archive_dirpath=%s --progenitor_class_list_fpath=%s --fit_metric_cutoff=%s %s") % ( \
            options.reference_xml_dir,
            pars['n_noisified_per_orig_vosource'],
            options.unfeat_xml_dir,
            options.n_epochs,
            options.archive_dirpath,
            options.progenitor_class_list_fpath,
            pars['fit_metric_cutoff'],
            use_srcid_times_str)
        os.system(exec_str)

    # OBSOLETE: since doesnt use "noisification", just raw TUTOR vosources:
    if options.make_feats_for_tutor:
        # Here we retrieve Vosource.xmls from TUTOR & generate new XML with
        #    current features.
        options.train_xml_dir = os.path.expandvars("$TCP_DATA_DIR/") # This path is hardcoded in ingest_tools.py
        #os.system("./populate_feat_db_using_TCPTUTOR_sources.py")

    # TODO: Vosource regeneration (with features):
    if options.regenerate_features:
        # Here we (re)generate features for each vosource.xml in given dirpath
        ###exec_str = "/home/dstarr/src/install/epd_py25-4.1.30101-rh3-amd64/bin/python ${TCP_DIR}Software/ingest_tools/regenerate_vosource_xmls.py --old_xmls_dirpath=%s --new_xmls_dirpath=%s " % \
        exec_str = os.path.expandvars("${TCP_DIR}Software/ingest_tools/regenerate_vosource_xmls.py --old_xmls_dirpath=%s --new_xmls_dirpath=%s " % \
                                      (options.unfeat_xml_dir, options.train_xml_dir))
        os.system(exec_str)
        #print "PLEASE RUN THIS IN PDB TO ENSURE TASKING ONTO BEOWULF NODES:"
        print(exec_str)
        #pass
        
    if options.train_mode:
        # This generates /tmp/train_output.arff using VOSource.xmls:
        
        ParallelArffMaker = Parallel_Arff_Maker(pars={})
        ParallelArffMaker.generate_arff_using_xmls( \
                 vosource_xml_dirpath=options.train_xml_dir, \
                 out_arff_fpath=options.train_arff_path, \
                 n_sources_needed_for_class_inclusion= \
                       options.n_sources_needed_for_class_inclusion)

        # NON-PARALLEL:
        #a = arffify.Maker(search=[], outfile=options.train_arff_path, \
        #                  skip_class=False, local_xmls=True, 
        #                  convert_class_abrvs_to_names=False,
        #                  flag_retrieve_class_abrvs_from_TUTOR=True,
        #                  local_xmls_fpath=options.train_xml_dir) 
        #a = arffify.Maker(search=["Cepheids","RR Lyrae - Asymmetric","Mira","W Ursae Majoris",]) # search[] Allows just a couple science classes to be used

    # TODO: it might be nice to generate a simple cost-matrix using weka output & heat_map...py


    # TODO: Automate the Metacost(RandomForest) execution via shell execution :
    if options.generate_model:
        # This generates a Weka .model using .arff and Classifier name
        #exec_str = "java weka.classifiers.trees.J48 -t /home/dstarr/src/TCP/Data/TUTOR_sources_20080708_45class.arff -d test-J48.model"
        os.chdir(pars['gridweka2_jar_dirpath'])

        # NOTE: first generate a summary confusion matrix using a simple classifier (ZeroR):
        #exec_str = "/usr/lib/jvm/java-6-sun-1.6.0.03/bin/java -Xmx3000m -cp GridWeka2.jar weka.classifiers.rules.ZeroR -t %s > %s" % (options.train_arff_path, pars['weka_ZeroR_confuse_matrix_outfpath'])
        #exec_str = "/home/dstarr/src/install/jdk1.6.0_03/bin/java -Xmx3000m -cp GridWeka2.jar weka.classifiers.rules.ZeroR -t %s > %s" % (options.train_arff_path, pars['weka_ZeroR_confuse_matrix_outfpath'])
        exec_str = "/usr/lib/jvm/java-6-sun-1.6.0.03/bin/java -Xmx3000m weka.classifiers.rules.ZeroR -t %s > %s.%s" % (options.train_arff_path, pars['weka_ZeroR_confuse_matrix_outfpath'], pars['tmpfile_suffix'])
        os.system(exec_str)

        parse_confuse_matrix_generate_costmatrix("%s.%s" % (pars['weka_ZeroR_confuse_matrix_outfpath'], \
                                                            pars['tmpfile_suffix']), options.cost_matrix_fpath)

        os.system("rm %s.%s" % (pars['weka_ZeroR_confuse_matrix_outfpath'], \
                                                            pars['tmpfile_suffix']))
        #"""
        # NOTE: do final classification using cost matrix
        #exec_str = "/usr/lib/jvm/java-6-sun-1.6.0.03/bin/java -Xmx12000m -cp GridWeka2.jar weka.classifiers.meta.MetaCost  -t %s -d %s -I 10 -P 100 -S 1 -C %s -W weka.classifiers.trees.RandomForest -- -I 25 -K 0 -S 1" % \
        #               (options.train_arff_path, options.weka_model_path, options.cost_matrix_fpath)
        #exec_str = "/usr/lib/jvm/java-6-sun-1.6.0.03/bin/java -Xmx12000m weka.classifiers.meta.MetaCost  -t %s -d %s -I 10 -P 100 -S 1 -C %s -W weka.classifiers.trees.RandomForest -- -I 25 -K 0 -S 1" % \

        ### 20091014: dstarr comments out (before using J48 rather than the older randomforest):
        #exec_str = "/usr/lib/jvm/java-6-sun-1.6.0.03/bin/java -Xmx12000m weka.classifiers.meta.MetaCost  -t %s -d %s -I 10 -P 100 -S 1 -C %s -W weka.classifiers.trees.RandomForest -- -I 25 -K 0 -S 1" % \
        #               (options.train_arff_path, options.weka_model_path, options.cost_matrix_fpath)

        exec_str = "/usr/lib/jvm/java-6-sun-1.6.0.03/bin/java -Xmx10000m weka.classifiers.meta.MetaCost  -t %s -d %s -I 10 -P 100 -S 1 -C %s -W weka.classifiers.trees.J48 -- -C 0.25 -M 2" % \
                       (options.train_arff_path, options.weka_model_path, options.cost_matrix_fpath)
        (a,b,c) = os.popen3(exec_str)
        a.close()
        c.close()
        lines = b.read()
        b.close()
        results_fpath = options.archive_dirpath + '/metacost.results'
        fp = open(results_fpath, 'w')
        fp.write(lines)
        fp.close()
        #"""
        ###exec_str = "/usr/lib/jvm/java-6-sun-1.6.0.03/bin/java -Xmx12000m -cp GridWeka2.jar weka.classifiers.trees.J48 -C 0.25 -M 2 -t %s -d %s" % \
        ###               (options.train_arff_path, options.weka_model_path)
        #print exec_str

