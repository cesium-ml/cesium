#!/usr/bin/env python
"""
plugin_classifier.py

   v0.1 Given a list of VOSource XML strings, or filepaths,
        this generates classifications by calling WEKA and other classifier
        code.  Returns information in classification dictionaries.


"""
import sys, os
import copy
sys.path.append(os.environ.get("TCP_DIR") + '/Software/feature_extract/Code/extractors')
import mlens3  # for microlensing classification
import sn_classifier

sys.path.append(os.environ.get("TCP_DIR") + '/Software/feature_extract/MLData')
import arffify


# KLUDGE: this is ugly (importing ptf_master.py from within here.)  the Diff_Obj_Source_Populator
#           class should exist in a seperate module / file:
import ptf_master # required by tions_for_tcp_marked_variables.get_overall_classification_without_repopulation()
import ingest_tools
try:
    import get_classifications_for_caltechid
except:
    pass
try:
    import get_classifications_for_tcp_marked_variables # required by tions_for_tcp_marked_variables.get_overall_classification_without_repopulation()
except:
    pass


try:
    import jpype
except:
    print "EXCEPT: plugin_classifier.py.  Possibly on a development system without Java Weka of JPype installed."
    pass # KLUDGE: This would except on a development system without Java Weka of JPype installed.
import weka_classifier
os.environ["JAVA_HOME"] = '/usr/lib/jvm/java-6-sun-1.6.0.03'
os.environ["CLASSPATH"] += os.path.expandvars(':$TCP_DIR/Software/ingest_tools')

class PluginClassifier:
    """ Given a list of VOSource XML strings, or filepaths,
        this generates classifications by calling WEKA and other classifier
        code.  Returns information in classification dictionaries.
    """
    def __init__(self, class_schema_definition_dicts={}, class_abrv_lookup={}, \
                 use_weka_jvm=True, training_arff_features_list=[]):
        self.class_schema_definition_dicts = class_schema_definition_dicts
        self.training_arff_features_list = training_arff_features_list
        self.arffmaker = arffify.Maker(search=[], \
                                skip_class=True, local_xmls=True, dorun=False, \
                                class_abrv_lookup=class_abrv_lookup)
        if use_weka_jvm:
            # TODO/NOTE: I think a WekaClassifier() class needs to be
            #       instantiated for each WEKA classification instance 
            #       which uses a different .model and/or training .arff
            # We initialize a Java virtual machine for Weka classifications
            #try:
            if not jpype.isJVMStarted():
                #TODO / DEBUG: disable the next line for speed-ups once stable?
            	_jvmArgs = ["-ea"] # enable assertions
            	_jvmArgs.append("-Djava.class.path=" + \
                                    os.environ["CLASSPATH"])
            	###20091905 dstarr comments out:
                #_jvmArgs.append("-Xmx1000m")
            	_jvmArgs.append("-Xmx12000m") # 4000 & 5000m works, 3500m doesnt for some WEKA .models
            	jpype.startJVM(jpype.getDefaultJVMPath(), *_jvmArgs)

            class_schema_name_list = self.class_schema_definition_dicts.keys()
            class_schema_name_list.remove('mlens3 MicroLens')
            class_schema_name_list.remove('Dovi SN')
            class_schema_name_list.remove('General')
            self.wc = {}
            for class_schema_name in class_schema_name_list:
                class_schema_dict = self.class_schema_definition_dicts[class_schema_name]
                weka_training_model_fpath = class_schema_dict['weka_training_model_fpath']
                weka_training_arff_fpath = class_schema_dict['weka_training_arff_fpath']
                self.wc[class_schema_name] = weka_classifier.WekaClassifier( \
                                      weka_training_model_fpath, weka_training_arff_fpath)
            #except:
            #    print "EXCEPT: most likely (javac JPypeObjectInputStream.java) has not been done.  See header of weka_classifier.py"


    def get_class_probs_using_jvm_weka_instance(self, vosource_list, \
                                                plugin_name='default plugin name'):
        """ Use an already-instantiated Java JVM to run weka classification.
        Format the results.

        RETURN:
        out_plugin_classification_dict[src_id][plugin_name]
        class_probs_dict = {} # {src_id:[{'schema_id':'', 'class_id':'', 'prob':'', 'class_rank':'', 'prob_weight':''}]}
        """
        #self.arffmaker.populate_features_and_classes_using_local_xmls(\
        #                                     srcid_xml_tuple_list=vosource_list)
        out_plugin_classification_dict = {}
        new_master_features_list = []
        master_features_dict = dict(self.arffmaker.master_features) # NOTE: I believe the features in .master_features are the features found in the current source's vosurce-xml-string.  # KLUDGE: this makes a dictionary from a list of tuples.
        #for feat_name in self.training_arff_features_list:
        for feat_name in self.class_schema_definition_dicts[plugin_name]['features_list']:
            new_master_features_list.append((feat_name,
                                             master_features_dict[feat_name]))
        ### This doesn't preserve the feature list order in the training .arff:
        #for feat_name,feat_type in self.arffmaker.master_features:
        #    if feat_name in self.training_arff_features_list:
        #        new_master_features_list.append((feat_name,feat_type))
        #stored_arffmaker_master_features = copy.deepcopy(self.arffmaker.master_features)
        #self.arffmaker.master_features = new_master_features_list
        # TODO: extract these features from the vosource:
        #      (should be similar to methods used when makeing a temp .arff file)
        #arff_record = [0.65815,3.518955,0.334025,0.79653,44.230391,3.163003,0.025275,0.004501,0.295447,-0.133333,3.144411,-0.65161,None,None]
        #classified_result = self.wc.get_class_distribution(arff_record)
        #print classified_result

        prob_weight = 1.0 # This property may be used in Nat/Dovi to represent
        #             science classes which are known to be non applicable (0.0)
        class_probs_dict = {}
        for obj in self.arffmaker.master_list:
            #if remove_sparse_classes:
            #    if not obj.get('class','') in self.arffmaker.master_classes:
            #    continue # skip this object due to being in a sparse class
            #tmp = []
            src_id = obj['num']
            class_probs_dict[src_id] = []
            arff_record = []

	    for fea in new_master_features_list:
	    	val = None
	    	if obj['features'].has_key(fea):
	    		str_fea_val = str(obj['features'][fea])
	    		if ((str_fea_val == "False") or 
	    		    (str_fea_val == "inf") or
	    		    (str_fea_val == "nan") or
	    		    (str_fea_val == "None")):
	    			val = None
	    		elif fea[1] == 'float':
	    			val = obj['features'][fea] # str_fea_val
	    		else:
	    			val = "%s" % str_fea_val # """'%s'""" % str_fea_val
                arff_record.append(val)

            # 20090130 old:
            #for fea in self.arffmaker.master_features:
            #    val = None # "?"
            #    if obj['features'].has_key(fea):
            #        if fea[1] == 'float':
            #            if ((obj['features'][fea] == "False") or 
            #                (str(obj['features'][fea]) == "inf") or
            #                (str(obj['features'][fea]) == "nan")):
            #                val = None # "?"
            #            elif obj['features'][fea] != None:
            #                val = obj['features'][fea] #val = str(obj['features'][fea])
            #        else:
            #            val = """'%s'""" % str(obj['features'][fea])
            #    arff_record.append(val)

            classified_result = self.wc[plugin_name].get_class_distribution(arff_record)

            out_plugin_classification_dict[src_id] = {plugin_name:{'probabilities':{}}}
            for i, (class_name,class_prob) in enumerate(classified_result[:3]):
                class_id = self.class_schema_definition_dicts[plugin_name] \
                                                  ['class_name_id_dict'][class_name]
                class_probs_dict[src_id].append(\
                                 {'schema_id':self.class_schema_definition_dicts\
                                                   [plugin_name]['schema_id'],
                                  'class_id':class_id,
                                  'class_name':class_name,
                                  'prob':class_prob,
                                  'class_rank':i,
                                  'prob_weight':prob_weight})
                out_plugin_classification_dict[src_id][plugin_name] \
                                  ['probabilities'][class_name] = {'prob':class_prob, \
                                                                   'prob_weight':1.0} # WEKA default KLUDGE
                # # # # # # #
                # TODO: eventually add WEKA ['value_added_properties'] to the returned dict
        return out_plugin_classification_dict # class_probs_dict


    def do_classification(self, vosource_list, class_schema_definition_dicts, do_logging=False):
        """ Given a list of VOSource XML strings, or filepaths,
        this generates classifications by calling WEKA and other classifier
        code.  Returns information in classification dictionaries.

        TODO: maybe only do vosource XML parsing once

        TODO: DiffObjSourcePopulator usage is very KLUDGY since
             - it opens an rdt connection
             - it imports many modules,
             - etc
             ->  so, we shoud find a better way to pass in/reference  a static object which has
             access to all this stuff.

        """
        if len(vosource_list) == 0:
            return ({},{})

        plugin_classification_dict = {}  # This is returned.
        for src_id,vosource_xml_str in vosource_list:
            plugin_classification_dict[src_id] = {}

        ##### Weka Classification:
        # TODO: run a full WEKA .model classification
        #       as well as a couple tailored n_epochs .model classification
        # TODO: Maybe pass in a .model into this function:
        if do_logging:
            print "before: self.arffmaker.populate_features_and_classes_using_local_xmls()"

        self.arffmaker.populate_features_and_classes_using_local_xmls(\
                                             srcid_xml_tuple_list=vosource_list)
        try:
            n_epochs_fromfeats = self.arffmaker.master_list[0]['features'][('n_points', 'float')]
        except:
            print "EXCEPT: self.arffmaker.master_list[0]['features'][('n_points', 'float')] : Empty array?"
            n_epochs_fromfeats = 0

        if do_logging:
            print "before: n_epochs_fromfeats > 1.0 try/except"

        if n_epochs_fromfeats > 1.0:
            class_schema_name_list = self.class_schema_definition_dicts.keys()
            class_schema_name_list.remove('mlens3 MicroLens')
            class_schema_name_list.remove('Dovi SN')
            class_schema_name_list.remove('General')
            for class_schema_name in class_schema_name_list:
                #if 1:
                try:
                    plugin_classification_dict__general = \
                                         self.get_class_probs_using_jvm_weka_instance( \
                                                 vosource_list, plugin_name=class_schema_name)
                    for src_id, plugin_dict in plugin_classification_dict__general.\
                                                                            iteritems():
                        plugin_classification_dict[src_id].update(plugin_dict)
                except:
                    print "EXCEPT: Calling get_class_probs_using_jvm_weka_instance()"
        if do_logging:
            print "after: n_epochs_fromfeats > 1.0 try/except"

        #DEBUG# return ({},{})
        ##### Microlensing classification:
        #class_probs_dict__mlens = {}
        for src_id,vosource_xml_str in vosource_list:
            ##########s_fp = cStringIO.StringIO(vosource_xml_str)
            # TODO: I need to create google-pseudo-fp for this string:
            if do_logging:
                print "before: mlens3.EventData(vosource_xml_str)"
 	    d = mlens3.EventData(vosource_xml_str)
            ##########del s_fp #.close()

            if do_logging:
                print "before: mlens3.Mlens(datamodel=d,doplot=False)"
 	    ## run the fitter (turn off doplot for running without pylab)
 	    m = mlens3.Mlens(datamodel=d,doplot=False)#,doplot=True)
 	    ### prob_mlens should be between 0 and 1...anything above 0.8 is pretty sure bet
 	    #prob_mlens =  m.final_results["probabilities"]["single-lens"]
            plugin_classification_dict[src_id]['mlens3 MicroLens'] = m.final_results

            ##### Nat/Dovi case:
            if do_logging:
                print "before: sn_classifier.Dovi_SN(datamodel=d,doplot=False)"
 	    sn = sn_classifier.Dovi_SN(datamodel=d,doplot=False)#,doplot=True)
            plugin_classification_dict[src_id]['Dovi SN'] = sn.final_results
            #import pprint
            #pprint.pprint(plugin_classification_dict[src_id]['Dovi SN'].get('probabilities',{}))
            #print 'yo'
        if do_logging:
            print "after: for src_id,vosource_xml_str in vosource_list"


        ##### Combined / Final Classification:

        # # # # # # # #
        # # # TODO: if mlens prob >= 0.8 and weka_prob[0] < 0.8 : mlens is primary class (otherwise incorperate it by probability if mlens >= 0.6 as either 2nd or 3rd)
        # TODO: combine info from previous classifications to make a final classification
        #    i.e.: Use plugin_classification_dict{} to make a 3 element class_probs_dict{<srcid>:[1,2,3]}
        # TODO: get class_id for mlens3

        # NOTE: class_probs_dict is used by generate_insert_classification_using_vosource_list() to INSERT classifications into RDB
        #class_probs_dict = class_probs_dict__weka # TODO: extend this when other classification modules are used as well.

        class_probs_dict = {}
        for src_id,a_dict in plugin_classification_dict.iteritems():
            #prob_list = []
            class_probs_dict[src_id] = []
            for plugin_name,plugin_dict in a_dict.iteritems():
                prob_list = []
                for class_name,class_dict in plugin_dict.get('probabilities',{}).iteritems():
                    class_id = self.class_schema_definition_dicts[plugin_name]['class_name_id_dict'][class_name] # TODO: get the MLENS class_id from somewhere!!!
                
                    temp_dict = {'schema_id':self.class_schema_definition_dicts[plugin_name]['schema_id'],
                                 'class_id':class_id,
                                 'class_name':class_name,
                                 'plugin_name':plugin_name,
                                 'prob':class_dict['prob'],
                                 'prob_weight':class_dict['prob_weight']}

                    prob_list.append((class_dict['prob'],temp_dict))
                    #? OBSOLETE ? : source_class_probs_list.append(temp_dict)

                #NOTE: for WEKA case, we generate class_ranks 1,2,3.  Otherwise, we just pass on probability as class rank=1
                if self.class_schema_definition_dicts[plugin_name]['predicts_multiple_classes']:
                    prob_list.sort(reverse=True)

                    #NOTE: for WEKA case, we generate class_ranks 1,2,3.  Otherwise, we just pass on probability as class rank=1
                    for i,(prob_float,prob_dict) in enumerate(prob_list[:3]):
                        prob_dict['class_rank'] = i
                        class_probs_dict[src_id].append(prob_dict)
                else:
                    for i,(prob_float,prob_dict) in enumerate(prob_list):
                        prob_dict['class_rank'] = i
                        class_probs_dict[src_id].append(prob_dict)


        # 2) step in and make sure general_classif_dict{} is created below:
        # 3) make sure classification & schema TABLE can take the new general/overview class & schema (update ingest.pars)
        # 4) TEST and migrate changes to ipengine nodes.  Then run for recent PTF night.
        
        #########
        # KLUDGE: this is ugly (importing ptf_master.py from within here.)  the Diff_Obj_Source_Populator
        #           class should exist in a seperate module / file:

        if do_logging:
            print "before: DiffObjSourcePopulator = ptf_master.Diff_Obj_Source_Populator"

        DiffObjSourcePopulator = ptf_master.Diff_Obj_Source_Populator(use_postgre_ptf=False) #True)

        if do_logging:
            print "after: DiffObjSourcePopulator = ptf_master.Diff_Obj_Source_Populator"

        src_id = int(vosource_list[0][0]) # we can assume at this point that len(vosource_list) > 0

        select_str = """SELECT id, realbogus, ujd, source_test_db.srcid_lookup.ra, source_test_db.srcid_lookup.decl FROM object_test_db.obj_srcid_lookup JOIN object_test_db.ptf_events ON (object_test_db.ptf_events.id = object_test_db.obj_srcid_lookup.obj_id) JOIN source_test_db.srcid_lookup USING (src_id) where survey_id=3 AND src_id=%d""" % (src_id)
        if do_logging:
            print select_str

        DiffObjSourcePopulator.rdbt.cursor.execute(select_str)
        rdb_rows = DiffObjSourcePopulator.rdbt.cursor.fetchall()
        if do_logging:
            print "after select .execute()"
        general_classif_source_dict = {'obj_id':[],
                                       'realbogus':[],                        
                                       'ujd':[],
                                       'ra': rdb_rows[0][3],
                                       'dec':rdb_rows[0][4],
                                       'src_id':src_id}
        for row in rdb_rows:
            general_classif_source_dict['obj_id'].append(row[0])
            general_classif_source_dict['realbogus'].append(row[1])
            general_classif_source_dict['ujd'].append(row[2])

        if do_logging:
            print "before: Get_Classifications_For_Ptfid = get_classifications_for_caltechid.GetClassifications"

        #PTFPostgreServer = ptf_master.PTF_Postgre_Server(pars=ingest_tools.pars, \
        #                                                 rdbt=DiffObjSourcePopulator.rdbt)
        PTFPostgreServer = None
        Get_Classifications_For_Ptfid = get_classifications_for_caltechid.GetClassificationsForPtfid(rdbt=DiffObjSourcePopulator.rdbt)
        if do_logging:
            print "before: general_classif_dict = get_classifications_for_tcp_marked_variables.get_overall"

        general_classif_dict = get_classifications_for_tcp_marked_variables.get_overall_classification_without_repopulation(DiffObjSourcePopulator, PTFPostgreServer, Get_Classifications_For_Ptfid, Caltech_DB=None, matching_source_dict=general_classif_source_dict)

        if do_logging:
            print "after: general_classif_dict = get_classifications_for_tcp_marked_variables.get_overall"

        DiffObjSourcePopulator.rdbt.cursor.close()

        if general_classif_dict.has_key('science_class'):
            class_type = general_classif_dict['science_class']
        else:
            class_type = general_classif_dict['overall_type']

        try:
            table_class_id = class_schema_definition_dicts['General']['class_list'].index(class_type)
        except:
            table_class_id = 0 # This is the "other" class, which may represent new periodic classes which havent been added to ingest_tools.py..pars['class_schema_definition_dicts']['General']['class_list']
            
        class_probs_dict[src_id].append({'class_id': table_class_id,
                                 'class_name': general_classif_dict['overall_type'],
                                 'class_rank': 0,
                                 'plugin_name': 'General',
                                 'prob': general_classif_dict.get('class_prob',1.0),
                                 'prob_weight': 1.0,
                                 'schema_id': class_schema_definition_dicts['General']['schema_id']})

        # how do I add

        # TODO: then update the (class_probs_dict, plugin_classification_dict) information so that
        #       these classifications can be INSERTED into MySQL table
        # TODO: new schema will need to be defined, which will allow INSERT of new classification schema.


        #######################
        #  - this will eventually be called 1 stack up, using the singly passed:
        #                plugin_classification_dict{}
        ##### DEBUG:
        #print class_probs_dict
        if do_logging:
            print "(end of) do_classification()"
        return (class_probs_dict, plugin_classification_dict)


if __name__ == '__main__':
    pass
