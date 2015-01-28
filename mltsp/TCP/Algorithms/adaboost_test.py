#!/usr/bin/env python
"""
Script for testing out basic functionality of Eads' adaboost implementation.

Software dependencies can be found at:

    svn checkout http://svn.eadsware.com/tinyboost
    svn checkout http://convert-xy.googlecode.com/svn/trunk/ convert-xy-read-only/

##### help(tiny_boost) :



               X:          A M by N array of N examples in M dimensions
               ks:         The feature indices of the weak hypotheses.
               alphas:     The alphas/weights of the weak hypotheses.
               thresholds: The thresholds of the decision stumps of the weak hypotheses.
               directions: The directions of the decision stumps of the weak hypotheses.

sum(alphas) :: total weights

preds / sum(alphas)  :: normalized predictions, range: [-1..1]


"""
import sys, os




if __name__ == '__main__':

    import tiny_boost

    os.chdir('/home/pteluser/src/tinyboost')

    import numpy
    X = numpy.loadtxt("iono.txt",delimiter=",")
    Y=X[:,-1]   ## Last column are the labels
    X=X[:,:-1]   # Everything but the last column are the feature vectors

    # NOTE: the training function requires the feature vectors to be columns of the matrix.  Each row is the entire dataset wrt to a single feeature.  X is M by N where M=number of features and N=number of training examples.

    # NOTE: The 3rd argument (100 in this example) is the number of rounds of boosting to run.  If the labels are in the set {-1, 1}, then this is a traditional AdaBoost.  If the labels are in the interval [-1, 1] then it uses an adaption of AdaBoost which Eads came up with.
    
    (k, alphas, thresholds, directions) = tiny_boost.adaboost_train(X.T, Y, 100)

    ##### Generate predictions using the trained classifier and the training set:
    preds = tiny_boost.adaboost_apply(X.T,k, alphas, thresholds, directions)

    alphas_sum = numpy.sum(alphas)
    
    normalized_preds = preds / alphas_sum

    for i, pred in enumerate(normalized_preds):
        confidence = numpy.abs(pred)
        prediction = numpy.sign(pred)
        orig_int_classif = int(Y[i])
        note = 'match'
        if prediction != orig_int_classif:
            note = 'misclassified'
        print "i=%4d  conf=%lf  pred=%2d  orig=%2d %s" % (i, confidence, prediction, orig_int_classif, note)

    print
