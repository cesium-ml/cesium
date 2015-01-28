""" dstarr NOTES for python-weka
ORIGINAL FILES (downloaded):
    weka-python_weka_classifier.py
    weka-python_JPypeObjectInputStream.java

TO INSTALL:

  > apt-get install sun-java6-jdk

  - Download, install JPype-0.5.3
  - edit JPype-0.5.3/setup.py to include the correct JAVA_HOME ~L48:
             self.javaHome = '/usr/lib/jvm/java-6-sun-1.6.0.03'
  
  > sudo python setup.py install

- TEST Jpype is installed:
     > ipython
     > import jpype

- RENAMEs, MAKE JPypeObjectInputStream.class:
  >  cp weka-python_JPypeObjectInputStream.java JPypeObjectInputStream.java 
  >  javac JPypeObjectInputStream.java
  >  cp weka-python_weka_classifier.py weka_classifier.py

"""
#import inspect #dstarr added

import os
try:
    import jpype
    from jpype import java
except:
    print "EXCEPT: plugin_classifier.py.  Possibly on a development system without Java Weka of JPype installed."
    pass # KLUDGE: This would except on a development system without Java Weka of JPype installed.

class WekaClassifier(object):
	""" I think this class should be instantiated for each WEKA classification
	instance which uses a different .model and/or training .arff
	"""
	def __init__(self, modelFilename, datasetFilename):
		weka = jpype.JPackage("weka")
		self.JPypeObjectInputStream = jpype.JClass("JPypeObjectInputStream")

		self.dataset = weka.core.Instances(
			java.io.FileReader(datasetFilename))
		self.dataset.setClassIndex(self.dataset.numAttributes() - 1)

		self.instance = weka.core.Instance(self.dataset.numAttributes())
		self.instance.setDataset(self.dataset)

		ois = self.JPypeObjectInputStream(
			java.io.FileInputStream(modelFilename))
		self.model = ois.readObject()


        def reload_model_for_same_classes(self, modelFilename):
            """ Attempt to load a new .model file while keeping self.dataset, self.instance objects in place.
            """
            try:
                del self.model
            except:
                pass
            ois = self.JPypeObjectInputStream(
                java.io.FileInputStream(modelFilename))
            self.model = ois.readObject()



	def classify(self, record):
		for i, v in enumerate(record):
			if v is None:
				self.instance.setMissing(i)
			else:
				self.instance.setValue(i, v)
		return self.dataset.classAttribute().value(
			int(self.model.classifyInstance(self.instance)))

	def get_class_distribution(self, record):
		""" Return a list of tups, ordered with most probable
		classifications first:  [(class_name,probability), ...]

		A dstarr created method.
		"""
		for i, v in enumerate(record):
			if v is None:
				self.instance.setMissing(i)
			else:
				self.instance.setValue(i, v)

		temp_index_list = []
		for i, v in enumerate(self.model.distributionForInstance(self.instance)):
			temp_index_list.append((v,i))
		out_list = []
		temp_index_list.sort(reverse=True)
		for perc,ind in temp_index_list:
			class_name = self.dataset.classAttribute().value(ind)
			#print class_name, '\n\t\t', perc
			out_list.append((class_name,perc))
		return out_list


if __name__ == '__main__':

    # 20081209: dstarr hardcodes:
    os.environ["JAVA_HOME"] = '/usr/lib/jvm/java-6-sun-1.6.0.03'
    os.environ["CLASSPATH"] += ':/home/pteluser/src/TCP/Software/ingest_tools'
    if not jpype.isJVMStarted():
    	_jvmArgs = ["-ea"] # enable assertions
    	_jvmArgs.append("-Djava.class.path="+os.environ["CLASSPATH"])
    	jpype.startJVM(jpype.getDefaultJVMPath(), *_jvmArgs)

    weka_training_model_fpath = os.path.expandvars('$TCP_DIR/Data/26sciclass_metacost_bagged_randomforest.model')
    weka_training_arff_fpath = os.path.expandvars('$TCP_DIR/Data/train_14feat_fewer_classes.arff')

    #weka = jpype.JPackage("weka")
    #JPypeObjectInputStream = jpype.JClass("JPypeObjectInputStream")


    wc = WekaClassifier(weka_training_model_fpath, weka_training_arff_fpath)

    #arff_record = "0.65815,3.518955,0.334025,0.79653,44.230391,3.163003,0.025275,0.004501,0.295447,-0.133333,3.144411,-0.65161,?,'RR Lyrae, Fundamental Mode'"
    #arff_record = [0.65815,3.518955,0.334025,0.79653,44.230391,3.163003,0.025275,0.004501,0.295447,-0.133333,3.144411,-0.65161,None,'RR Lyrae, Fundamental Mode']
    arff_record = [0.65815,3.518955,0.334025,0.79653,44.230391,3.163003,0.025275,0.004501,0.295447,-0.133333,3.144411,-0.65161,None,None]

    #classified_result = wc.classify(arff_record)
    classified_result = wc.get_class_distribution(arff_record)
    print classified_result

    # TODO: replace classificatioN_interface.py ' arf writing & weka calling.

    #jpype.shutdownJVM() is not called ATM


    print 'done'


#######################
"""(Pdb) for x,y in inspect.getmembers(wc.model): print "wc.model.%s\n\t\t\t%s\n" % (x,str(y))
wc.model.__class__
			<class 'jpype._jclass.weka.classifiers.meta.MetaCost'>

wc.model.__delattr__
			<method-wrapper '__delattr__' of weka.classifiers.meta.MetaCost object at 0x813110>

wc.model.__dict__
			{'__javaobject__': <PyCObject object at 0x2b1cb2d3f210>}

wc.model.__doc__
			None

wc.model.__eq__
			<bound method weka.classifiers.meta.MetaCost.<lambda> of <jpype._jclass.weka.classifiers.meta.MetaCost object at 0x813110>>

wc.model.__getattribute__
			<bound method weka.classifiers.meta.MetaCost._javaGetAttr of <jpype._jclass.weka.classifiers.meta.MetaCost object at 0x813110>>

wc.model.__hash__
			<bound method weka.classifiers.meta.MetaCost.<lambda> of <jpype._jclass.weka.classifiers.meta.MetaCost object at 0x813110>>

wc.model.__init__
			<bound method weka.classifiers.meta.MetaCost._javaInit of <jpype._jclass.weka.classifiers.meta.MetaCost object at 0x813110>>

wc.model.__javaclass__
			<JavaClass object at 0x80b828>

wc.model.__javaobject__
			<PyCObject object at 0x2b1cb2d3f210>

wc.model.__metaclass__
			<class 'jpype._jclass.weka.classifiers.meta.MetaCost$$Static'>

wc.model.__module__
			jpype._jclass

wc.model.__ne__
			<bound method weka.classifiers.meta.MetaCost.<lambda> of <jpype._jclass.weka.classifiers.meta.MetaCost object at 0x813110>>

wc.model.__new__
			<built-in method __new__ of type object at 0x730880>

wc.model.__reduce__
			<built-in method __reduce__ of weka.classifiers.meta.MetaCost object at 0x813110>

wc.model.__reduce_ex__
			<built-in method __reduce_ex__ of weka.classifiers.meta.MetaCost object at 0x813110>

wc.model.__repr__
			<method-wrapper '__repr__' of weka.classifiers.meta.MetaCost object at 0x813110>

wc.model.__setattr__
			<method-wrapper '__setattr__' of weka.classifiers.meta.MetaCost object at 0x813110>

wc.model.__str__
			<bound method weka.classifiers.meta.MetaCost.<lambda> of <jpype._jclass.weka.classifiers.meta.MetaCost object at 0x813110>>

wc.model.__weakref__
			None

wc.model.bagSizePercent
			100

wc.model.bagSizePercentTipText
			<bound method java.lang.Class.bagSizePercentTipText>

wc.model.buildClassifier
			<bound method java.lang.Class.buildClassifier>

wc.model.capabilities
			Capabilities: [Nominal attributes, Binary attributes, Unary attributes, Empty nominal attributes, Numeric attributes, Date attributes, Missing values, Nominal class, Binary class, Missing class values]
Dependencies: [Nominal attributes, Binary attributes, Unary attributes, Empty nominal attributes, Numeric attributes, Date attributes, String attributes, Relational attributes, Missing values, No class, Missing class values, Only multi-Instance data]
min # Instance: 1


wc.model.classifier
			Random forest of 25 trees, each constructed while considering 4 random features.
Out of bag error: 0.2054



wc.model.classifierTipText
			<bound method java.lang.Class.classifierTipText>

wc.model.classifyInstance
			<bound method java.lang.Class.classifyInstance>

wc.model.costMatrix
			  0     0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35
  0.75  0     0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75
  0.18  0.18  0     0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18
  3.28  3.28  3.28  0     3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28
 12.01 12.01 12.01 12.01  0    12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01
  5.3   5.3   5.3   5.3   5.3   0     5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3 
  3.46  3.46  3.46  3.46  3.46  3.46  0     3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46
  6.43  6.43  6.43  6.43  6.43  6.43  6.43  0     6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43
  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0     0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31
 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87  0    12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87
  5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   0     5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3 
 10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6   0    10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6 
 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87  0    12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87
  0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0     0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2 
  5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   0     5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3 
  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  0     3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75
  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  0     1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68
  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  0     5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81
  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  0     1.62  1.62  1.62  1.62  1.62  1.62  1.62
 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26  0    11.26 11.26 11.26 11.26 11.26 11.26
  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0     0.62  0.62  0.62  0.62  0.62
 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01  0    12.01 12.01 12.01 12.01
 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86  0    13.86 13.86 13.86
  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0     0.52  0.52
 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87  0    12.87
  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  0   


wc.model.costMatrixSource
			2

wc.model.costMatrixSourceTipText
			<bound method java.lang.Class.costMatrixSourceTipText>

wc.model.costMatrixTipText
			<bound method java.lang.Class.costMatrixTipText>

wc.model.debug
			0

wc.model.debugTipText
			<bound method java.lang.Class.debugTipText>

wc.model.distributionForInstance
			<bound method java.lang.Class.distributionForInstance>

wc.model.equals
			<bound method java.lang.Class.equals>

wc.model.forName
			<bound method java.lang.Class.forName>

wc.model.getBagSizePercent
			<bound method java.lang.Class.getBagSizePercent>

wc.model.getCapabilities
			<bound method java.lang.Class.getCapabilities>

wc.model.getClass
			<bound method java.lang.Class.getClass>

wc.model.getClassifier
			<bound method java.lang.Class.getClassifier>

wc.model.getCostMatrix
			<bound method java.lang.Class.getCostMatrix>

wc.model.getCostMatrixSource
			<bound method java.lang.Class.getCostMatrixSource>

wc.model.getDebug
			<bound method java.lang.Class.getDebug>

wc.model.getNumIterations
			<bound method java.lang.Class.getNumIterations>

wc.model.getOnDemandDirectory
			<bound method java.lang.Class.getOnDemandDirectory>

wc.model.getOptions
			<bound method java.lang.Class.getOptions>

wc.model.getSeed
			<bound method java.lang.Class.getSeed>

wc.model.getTechnicalInformation
			<bound method java.lang.Class.getTechnicalInformation>

wc.model.globalInfo
			<bound method java.lang.Class.globalInfo>

wc.model.hashCode
			<bound method java.lang.Class.hashCode>

wc.model.listOptions
			<bound method java.lang.Class.listOptions>

wc.model.m_BagSizePercent
			100

wc.model.m_Classifier
			Random forest of 25 trees, each constructed while considering 4 random features.
Out of bag error: 0.2054



wc.model.m_CostFile
			None

wc.model.m_CostMatrix
			  0     0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35
  0.75  0     0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75  0.75
  0.18  0.18  0     0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18  0.18
  3.28  3.28  3.28  0     3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28  3.28
 12.01 12.01 12.01 12.01  0    12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01
  5.3   5.3   5.3   5.3   5.3   0     5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3 
  3.46  3.46  3.46  3.46  3.46  3.46  0     3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46  3.46
  6.43  6.43  6.43  6.43  6.43  6.43  6.43  0     6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43  6.43
  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0     0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31  0.31
 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87  0    12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87
  5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   0     5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3 
 10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6   0    10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6  10.6 
 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87  0    12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87
  0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0     0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2   0.2 
  5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   0     5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3   5.3 
  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  0     3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75  3.75
  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  0     1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68  1.68
  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81  0     5.81  5.81  5.81  5.81  5.81  5.81  5.81  5.81
  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  1.62  0     1.62  1.62  1.62  1.62  1.62  1.62  1.62
 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26  0    11.26 11.26 11.26 11.26 11.26 11.26
  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0.62  0     0.62  0.62  0.62  0.62  0.62
 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01  0    12.01 12.01 12.01 12.01
 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86 13.86  0    13.86 13.86 13.86
  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0.52  0     0.52  0.52
 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87 12.87  0    12.87
  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  1.59  0   


wc.model.m_Debug
			0

wc.model.m_MatrixSource
			2

wc.model.m_NumIterations
			10

wc.model.m_OnDemandDirectory
			/home/pteluser

wc.model.m_Seed
			1

wc.model.main
			<bound method java.lang.Class.main>

wc.model.makeCopies
			<bound method java.lang.Class.makeCopies>

wc.model.makeCopy
			<bound method java.lang.Class.makeCopy>

wc.model.notify
			<bound method java.lang.Class.notify>

wc.model.notifyAll
			<bound method java.lang.Class.notifyAll>

wc.model.numIterations
			10

wc.model.numIterationsTipText
			<bound method java.lang.Class.numIterationsTipText>

wc.model.onDemandDirectory
			/home/pteluser

wc.model.onDemandDirectoryTipText
			<bound method java.lang.Class.onDemandDirectoryTipText>

wc.model.options
			(u'-cost-matrix', u'[0.0 0.348 0.348 0.348 0.348 0.348 0.348 0.348 0.348 0.348 0.348 0.348 0.348 0.348 0.348 0.348 0.348 0.348 0.348 0.348 0.348 0.348 0.348 0.348 0.348 0.348; 0.751 0.0 0.751 0.751 0.751 0.751 0.751 0.751 0.751 0.751 0.751 0.751 0.751 0.751 0.751 0.751 0.751 0.751 0.751 0.751 0.751 0.751 0.751 0.751 0.751 0.751; 0.178 0.178 0.0 0.178 0.178 0.178 0.178 0.178 0.178 0.178 0.178 0.178 0.178 0.178 0.178 0.178 0.178 0.178 0.178 0.178 0.178 0.178 0.178 0.178 0.178 0.178; 3.276 3.276 3.276 0.0 3.276 3.276 3.276 3.276 3.276 3.276 3.276 3.276 3.276 3.276 3.276 3.276 3.276 3.276 3.276 3.276 3.276 3.276 3.276 3.276 3.276 3.276; 12.01 12.01 12.01 12.01 0.0 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01; 5.299 5.299 5.299 5.299 5.299 0.0 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299; 3.464 3.464 3.464 3.464 3.464 3.464 0.0 3.464 3.464 3.464 3.464 3.464 3.464 3.464 3.464 3.464 3.464 3.464 3.464 3.464 3.464 3.464 3.464 3.464 3.464 3.464; 6.434 6.434 6.434 6.434 6.434 6.434 6.434 0.0 6.434 6.434 6.434 6.434 6.434 6.434 6.434 6.434 6.434 6.434 6.434 6.434 6.434 6.434 6.434 6.434 6.434 6.434; 0.305 0.305 0.305 0.305 0.305 0.305 0.305 0.305 0.0 0.305 0.305 0.305 0.305 0.305 0.305 0.305 0.305 0.305 0.305 0.305 0.305 0.305 0.305 0.305 0.305 0.305; 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 0.0 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868; 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 0.0 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299; 10.597 10.597 10.597 10.597 10.597 10.597 10.597 10.597 10.597 10.597 10.597 0.0 10.597 10.597 10.597 10.597 10.597 10.597 10.597 10.597 10.597 10.597 10.597 10.597 10.597 10.597; 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 0.0 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868; 0.196 0.196 0.196 0.196 0.196 0.196 0.196 0.196 0.196 0.196 0.196 0.196 0.196 0.0 0.196 0.196 0.196 0.196 0.196 0.196 0.196 0.196 0.196 0.196 0.196 0.196; 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 0.0 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299 5.299; 3.753 3.753 3.753 3.753 3.753 3.753 3.753 3.753 3.753 3.753 3.753 3.753 3.753 3.753 3.753 0.0 3.753 3.753 3.753 3.753 3.753 3.753 3.753 3.753 3.753 3.753; 1.684 1.684 1.684 1.684 1.684 1.684 1.684 1.684 1.684 1.684 1.684 1.684 1.684 1.684 1.684 1.684 0.0 1.684 1.684 1.684 1.684 1.684 1.684 1.684 1.684 1.684; 5.811 5.811 5.811 5.811 5.811 5.811 5.811 5.811 5.811 5.811 5.811 5.811 5.811 5.811 5.811 5.811 5.811 0.0 5.811 5.811 5.811 5.811 5.811 5.811 5.811 5.811; 1.623 1.623 1.623 1.623 1.623 1.623 1.623 1.623 1.623 1.623 1.623 1.623 1.623 1.623 1.623 1.623 1.623 1.623 0.0 1.623 1.623 1.623 1.623 1.623 1.623 1.623; 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 11.26 0.0 11.26 11.26 11.26 11.26 11.26 11.26; 0.619 0.619 0.619 0.619 0.619 0.619 0.619 0.619 0.619 0.619 0.619 0.619 0.619 0.619 0.619 0.619 0.619 0.619 0.619 0.619 0.0 0.619 0.619 0.619 0.619 0.619; 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 12.01 0.0 12.01 12.01 12.01 12.01; 13.858 13.858 13.858 13.858 13.858 13.858 13.858 13.858 13.858 13.858 13.858 13.858 13.858 13.858 13.858 13.858 13.858 13.858 13.858 13.858 13.858 13.858 0.0 13.858 13.858 13.858; 0.518 0.518 0.518 0.518 0.518 0.518 0.518 0.518 0.518 0.518 0.518 0.518 0.518 0.518 0.518 0.518 0.518 0.518 0.518 0.518 0.518 0.518 0.518 0.0 0.518 0.518; 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 12.868 0.0 12.868; 1.594 1.594 1.594 1.594 1.594 1.594 1.594 1.594 1.594 1.594 1.594 1.594 1.594 1.594 1.594 1.594 1.594 1.594 1.594 1.594 1.594 1.594 1.594 1.594 1.594 0.0]', u'-I', u'10', u'-P', u'100', u'-S', u'1', u'-W', u'weka.classifiers.trees.RandomForest', u'--', u'-I', u'25', u'-K', u'0', u'-S', u'1')

wc.model.seed
			1

wc.model.seedTipText
			<bound method java.lang.Class.seedTipText>

wc.model.setBagSizePercent
			<bound method java.lang.Class.setBagSizePercent>

wc.model.setClassifier
			<bound method java.lang.Class.setClassifier>

wc.model.setCostMatrix
			<bound method java.lang.Class.setCostMatrix>

wc.model.setCostMatrixSource
			<bound method java.lang.Class.setCostMatrixSource>

wc.model.setDebug
			<bound method java.lang.Class.setDebug>

wc.model.setNumIterations
			<bound method java.lang.Class.setNumIterations>

wc.model.setOnDemandDirectory
			<bound method java.lang.Class.setOnDemandDirectory>

wc.model.setOptions
			<bound method java.lang.Class.setOptions>

wc.model.setSeed
			<bound method java.lang.Class.setSeed>

wc.model.technicalInformation
			Pedro Domingos: MetaCost: A general method for making classifiers cost-sensitive. In: Fifth International Conference on Knowledge Discovery and Data Mining, 155-164, 1999.

wc.model.toString
			<bound method java.lang.Class.toString>

wc.model.wait
			<bound method java.lang.Class.wait>
"""
