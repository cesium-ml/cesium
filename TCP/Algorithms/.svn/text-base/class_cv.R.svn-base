
# CART
rpart.cv = function(x,y,nfolds=5,method="gini",loss=NULL,prior=NULL,seed=sample(1:10^5,1)){
  require(rpart)
  set.seed(seed)

  n = length(y)
  p = length(table(y))
  folds = sample(1:nfolds,n,replace=TRUE)
  predictions = matrix(0,nrow=n,ncol=p)

  # default loss function
  if(is.null(loss)){
    loss = matrix(1,p,p)
    diag(loss) = rep(0,p)}

  # default prior: prop. to observed class rates
  if(is.null(prior)){
    prior = table(y)/n
  }

  prior = prior / sum(prior)
    
  for(ii in 1:nfolds){
    print(paste("fold",ii,"of",nfolds))
    leaveout = which(folds==ii)
    # fit tree
    y.in = y[-leaveout]
    tree.fit = rpart(y.in~.,data=data.frame(x[-leaveout,]),parms=list(split=method,loss=loss,prior=prior),control=rpart.control(minsplit=2,minbucket=1,cp=.001,xval=2))
    if(dim(tree.fit$cptable)[2] < 4) {
      print("tree is a stump, skip pruning")
      tree.prune  = tree.fit }
    else {
    #  print(tree.fit$cptable[which.min(tree.fit$cptable[,"xerror"]),"CP"])
      tree.prune = try(prune(tree.fit,cp=tree.fit$cptable[which.min(tree.fit$cptable[,"xerror"]),"CP"]))
      if(length(tree.prune)==1) {tree.prune = prune(tree.fit,cp=2*tree.fit$cptable[which.min(tree.fit$cptable[,"xerror"]),"CP"]) }
    }
    predictions[leaveout,] = predict(tree.prune,newdata=data.frame(x[leaveout,]),type="prob")
  }
  pred = levels(y)[apply(predictions,1,which.max)]
  pred = factor(pred,levels=levels(y))
  confmat = fixconfmat(table(pred,y),levels(pred),levels(y))
  err.rate = 1-sum(diag(confmat))/n
  return(list(predclass=pred,predprob=predictions,confmat=confmat,err.rate=err.rate))
}


### Random Forest
rf.cv = function(x,y,nfolds=5,testset=NULL,prior=NULL,mtry=NULL,n.trees=500,seed=sample(1:10^5,1)){
  # don't train on any of the data in testset
  # this is to use in the hierarchical classifier
  require(randomForest)
  set.seed(seed)
  
  n = length(y)
  p = length(table(y))
  folds = sample(1:nfolds,n,replace=TRUE)
  predictions = matrix(0,nrow=n,ncol=p)

  if(is.null(mtry)){
    mtry = ceiling(sqrt(dim(x)[2]))
  }
  # default prior: prop. to observed class rates
   if(is.null(prior)){
    prior = table(y)/n
  }
  
  for(ii in 1:nfolds){
    print(paste("fold",ii,"of",nfolds))
    leaveout = which(folds==ii)
    rf.tmp = randomForest(x=as.matrix(x[-union(leaveout,testset),]),y=y[-union(leaveout,testset)],classwt=prior,mtry=mtry,ntree=n.trees,nodesize=5)
    predictions[leaveout,] = predict(rf.tmp,newdata=x[leaveout,],type='prob')
  }
  pred = levels(y)[apply(predictions,1,which.max)]
  pred = factor(pred,levels=levels(y))
  confmat = fixconfmat(table(pred,y),levels(pred),names(table(y)))
  err.rate = 1-sum(diag(confmat))/n

  return(list(predclass=pred,predprob=predictions,confmat=confmat,err.rate=err.rate))
}




### Random Forest (party)
rfc.cv = function(x,y,nfolds=5,testset=NULL,mtry=NULL,weights=NULL,n.trees=500,seed=sample(1:10^5,1)){
  # don't train on any of the data in testset
  # this is to use in the hierarchical classifier
  require(party)
  set.seed(seed)
  
  n = length(y)
  p = length(table(y))
  folds = sample(1:nfolds,n,replace=TRUE)
  predictions = matrix(0,nrow=n,ncol=p)

  if(is.null(mtry)){
    mtry = ceiling(sqrt(dim(x)[2]))
  }

  for(ii in 1:nfolds){
    print(paste("fold",ii,"of",nfolds))
    leaveout = which(folds==ii)
    train = cbind(y[-union(leaveout,testset)],x[-union(leaveout,testset),])
    test = cbind(y[leaveout],x[leaveout,])
    names(train)[1] = names(test)[1] = "y"
    rf.tmp = cforest(y~.,data=train,weights=weights[-leaveout],controls=cforest_classical(mtry=mtry,ntree=n.trees))
    predictions[leaveout,] = matrix(unlist(treeresponse(rf.tmp,newdata=test)),length(leaveout),p,byrow=T)
  }
  pred = levels(y)[apply(predictions,1,which.max)]
  pred = factor(pred,levels=levels(y))
  confmat = fixconfmat(table(pred,y),levels(pred),names(table(y)))
  err.rate = 1-sum(diag(confmat))/n

  return(list(predclass=pred,predprob=predictions,confmat=confmat,err.rate=err.rate))
}


### Random Forest with MetaCost wrapper
rfMetaCost.cv = function(x,y,nfolds=5,cost=costMat(2),prior=NULL,mtry=NULL,n.trees=500,seed=sample(1:10^5,1)){
  require(randomForest)
  set.seed(seed)
  
  n = length(y)
  p = length(table(y))
  folds = sample(1:nfolds,n,replace=TRUE)
  predictions = matrix(0,nrow=n,ncol=p)

  if(is.null(mtry)){
    mtry = ceiling(sqrt(dim(x)[2]))
  }
  # default prior: prop. to observed class rates
   if(is.null(prior)){
    prior = table(y)/n
  }
  
  for(ii in 1:nfolds){
    print(paste("fold",ii,"of",nfolds))
    leaveout = which(folds==ii)
    rf.init = randomForest(x=as.matrix(x[-leaveout,]),y=y[-leaveout],classwt=prior,mtry=mtry,ntree=n.trees,nodesize=5)
    y.adj = factor(apply(rf.init$votes%*%cost,1,which.min))
    rf.adj = randomForest(x=as.matrix(x[-leaveout,]),y=y.adj,mtry=mtry,ntree=n.trees,nodesize=5)
    predictions[leaveout] = as.numeric(paste(predict(rf.adj,newdata=x[leaveout,],type='class')))
  }
  pred = factor(levels(y)[predictions],levels=levels(y))
  confmat = fixconfmat(table(pred,y),levels(pred),names(table(y)))
  err.rate = 1-sum(diag(confmat))/n

  return(list(predclass=pred,predprob=predictions,confmat=confmat,err.rate=err.rate))
}

# ############## HSC
# Random Forest hierarchical single class.
rf.hsc = function(x,ymat,y,nfolds=5,mtry=NULL,weights=NULL,n.trees=100,seed=sample(1:10^5,1)){
  require(randomForest)
  depth = ymat$depth
  ymat = ymat$class

  n = length(ymat[,1])
  p = length(colnames(ymat)[colnames(ymat)==substr(colnames(ymat),1,1)])
  y.hat = matrix(0,nrow=n,ncol=length(ymat[1,]))
  predictions = matrix(0,nrow=n,ncol=p)
  if(is.null(mtry)){
    mtry = ceiling(sqrt(dim(x)[2]))
  }

  print("Classifying at top level")
  class.top = factor(colnames(ymat)[depth==1][apply(ymat[,depth==1]==1,1,which)])
  # random forest on top level
  rftop = rf.cv(x,class.top,n.trees=n.trees,nfolds=nfolds,mtry=mtry,seed=seed)
  y.hat[,depth==1] = rftop$predprob

  print("Classifying within subtrees:")
  # go down in the class hierarchy
  # do classification at each level within each subtree
  for(jj in 2:max(depth)){
    up = which(depth==jj-1)
    for(kk in 1:length(up)){
      subtree = up[kk]:min(up[kk+1],length(depth),na.rm=T)
      if(sum(depth[subtree]==jj)>0){ # check if the subtree goes deeper
      elem.sub = which(ymat[,up[kk]]==1)
      out = (1:n)[-elem.sub]
      class.sub = rep(NA,n)
      class.sub[elem.sub] = colnames(ymat)[depth==jj][apply(ymat[elem.sub,depth==jj]==1,1,which)]
      class.sub = factor(class.sub)
      rftmp = rf.cv(x,class.sub,testset=out,n.trees=n.trees,mtry=mtry,nfolds=nfolds,seed=seed)
      y.hat[,subtree[depth[subtree]==jj]] = rftmp$predprob
    }
    }
  }

  # turn y.hat tree probability estimates into class prob. estimates
  kk=0
  for(ii in 1:length(depth)){
    if(ii == 1){ isdeep = (depth[ii] == depth[ii+1])
    } else if(ii == length(depth)){ isdeep = (depth[ii] == depth[ii-1])
    } else { isdeep = depth[ii] == depth[ii-1] | depth[ii] == depth[ii+1]}
    if(isdeep){
      kk = kk+1
      tmp = y.hat[,ii]
      for(jj in (depth[ii]-1):1){
        ind = which(depth==jj) 
        tmp = tmp * y.hat[,max(ind[ind<ii])]
      }
      predictions[,kk] = tmp
    }
  }

  pred = levels(y)[apply(predictions,1,which.max)]
  pred = factor(pred,levels=levels(y))
  confmat = fixconfmat(table(pred,y),levels(pred),names(table(y)))
  err.rate = 1-sum(diag(confmat))/n

  return(list(predclass=pred,predprob=predictions,confmat=confmat,err.rate=err.rate))
}

# Random Forest hierarchical single class, using party
rf1.hsc = function(x,ymat,y,nfolds=5,mtry=NULL,weights=NULL,n.trees=100,seed=sample(1:10^5,1)){
  require(party)
  depth = ymat$depth
  ymat = ymat$class

  n = length(ymat[,1])
  p = length(colnames(ymat)[colnames(ymat)==substr(colnames(ymat),1,1)])
  y.hat = matrix(0,nrow=n,ncol=length(ymat[1,]))
  predictions = matrix(0,nrow=n,ncol=p)
  if(is.null(mtry)){
    mtry = ceiling(sqrt(dim(x)[2]))
  }

  print("Classifying at top level")
  class.top = factor(colnames(ymat)[depth==1][apply(ymat[,depth==1]==1,1,which)])
  # random forest on top level
  rftop = rfc.cv(x,class.top,n.trees=n.trees,nfolds=nfolds,mtry=mtry,seed=seed)
  y.hat[,depth==1] = rftop$predprob

  print("Classifying within subtrees:")
  # go down in the class hierarchy
  # do classification at each level within each subtree
  for(jj in 2:max(depth)){
    up = which(depth==jj-1)
    for(kk in 1:length(up)){
      subtree = up[kk]:min(up[kk+1],length(depth),na.rm=T)
      if(sum(depth[subtree]==jj)>0){ # check if the subtree goes deeper
      elem.sub = which(ymat[,up[kk]]==1)
      out = (1:n)[-elem.sub]
      class.sub = rep(NA,n)
      class.sub[elem.sub] = colnames(ymat)[depth==jj][apply(ymat[elem.sub,depth==jj]==1,1,which)]
      class.sub = factor(class.sub)
      rftmp = rfc.cv(x,class.sub,testset=out,n.trees=n.trees,mtry=mtry,nfolds=nfolds,seed=seed)
      y.hat[,subtree[depth[subtree]==jj]] = rftmp$predprob
    }
    }
  }

  # turn y.hat tree probability estimates into class prob. estimates
  kk=0
  for(ii in 1:length(depth)){
    if(ii == 1){ isdeep = (depth[ii] == depth[ii+1])
    } else if(ii == length(depth)){ isdeep = (depth[ii] == depth[ii-1])
    } else { isdeep = depth[ii] == depth[ii-1] | depth[ii] == depth[ii+1]}
    if(isdeep){
      kk = kk+1
      tmp = y.hat[,ii]
      for(jj in (depth[ii]-1):1){
        ind = which(depth==jj) 
        tmp = tmp * y.hat[,max(ind[ind<ii])]
      }
      predictions[,kk] = tmp
    }
  }

  pred = levels(y)[apply(predictions,1,which.max)]
  pred = factor(pred,levels=levels(y))
  confmat = fixconfmat(table(pred,y),levels(pred),names(table(y)))
  err.rate = 1-sum(diag(confmat))/n

  return(list(predclass=pred,predprob=predictions,confmat=confmat,err.rate=err.rate))
}


# ############## HMC
# Random Forest hierarchical multi-class. Uses Clus software
hmc.make = function(x,ymat,y,file='/Users/jwrichar/Documents/CDI/TCP/debosscher/clus/hmc.arff'){
  require(foreign)
  hclass = factor(sapply(sapply(apply(ymat==1,1,which),names),paste,collapse='/'))
  data = cbind(x,hclass)
  write.arff(data,file = file)
}

hmc.run = function(out = "hmc1.s",n.trees=500,mtry=25,w0=.75,seed=sample(1:10^5,1),path = "/Users/jwrichar/Documents/CDI/TCP/debosscher/clus/",jarpath ="/Users/jwrichar/Documents/CDI/Clus/" ,target=54){
  text = paste("[General]
Verbose = 0
Compatibility = Latest
RandomSeed =",seed,"
ResourceInfoLoaded = No

[Data]
File = hmc.arff
XVal = 10

[Attributes]
Target = ",target,"

[Constraints]
MaxSize = Infinity
MaxError = 0.0
MaxDepth = Infinity

[Output]
TrainErrors = Yes
ValidErrors = Yes
TestErrors = Yes
AllFoldModels = Yes
AllFoldErrors = No
AllFoldDatasets = No
BranchFrequency = No
ShowInfo = {Count}
PrintModelAndExamples = No
WriteErrorFile = No
WritePredictions = {Test}
ModelIDFiles = No
WriteCurves = No
OutputPythonModel = No
OutputDatabaseQueries = No

[Nominal]
MEstimate = 1.0

[Model]
MinimalWeight = 1.0
MinimalNumberExamples = 0
MinimalKnownWeight = 0.0
ParamTuneNumberFolds = 10
ClassWeights = 0.0
NominalSubsetTests = Yes

[Tree]
Heuristic = VarianceReduction
PruningMethod = None
FTest = 1.0
BinarySplit = Yes
ConvertToRules = No
AlternativeSplits = No
Optimize = {}
MSENominal = No

[Ensemble]
Iterations = ",n.trees,"
EnsembleMethod = RForest
SelectRandomSubspaces = ",mtry,"
VotingType = ProbabilityDistribution
Optimize = Yes
	
[Hierarchical]
Type = Tree
Distance = WeightedEuclidean
WType = ExpAvgParentWeight
WParam = ",w0,"
HSeparator = /
EmptySetIndicator = 0
OptimizeErrorMeasure = PooledAUPRC
DefinitionFile = None
NoRootPredictions = No
PruneInSig = 0.0
Bonferroni = No
SingleLabel = No
CalculateErrors = Yes
ClassificationThreshold = None
RecallValues = None
EvalClasses = None

",sep="")

 cat(text,file=paste(path,out,sep=""))
setwd(path)
system(paste("java -Xmx2000m -jar ",jarpath,"Clus.jar -xval -forest ",out,sep=""))
}

hmc.read = function(y,ymat,file="/Users/jwrichar/Documents/CDI/TCP/debosscher/clus/hmc.test.pred.arff"){
  test = read.table(file=file,comment.char='!',skip=70,sep=",")
  n = length(test[,1])
  node=test[,which(colnames(ymat)==substr(colnames(ymat),1,1))+33]
  top=test[,c(1,21,28)+33]
  pred = factor(levels(y)[apply(node,1,which.max)])
  true = factor(levels(y)[as.numeric(test[,1])])
  confmat = fixconfmat(table(pred,true),levels(pred),levels(true))
  err.rate = 1 - sum(diag(confmat))/n
  return(list(predclass=pred,confmat=confmat,err.rate=err.rate))
}



###  boosting with trees
boostTree.cv = function(x,y,nfolds=5,depth=10,n.trees=100,rate="Breiman",seed=sample(1:10^5,1)){
  require(adabag)
  set.seed(seed)
  
  n = length(y)
  p = length(table(y))
  folds = sample(1:nfolds,n,replace=TRUE)
  pred = rep(0,n)
  
 for(ii in 1:nfolds){
    print(paste("fold",ii,"of",nfolds))
    leaveout = which(folds==ii)
    train = cbind(y[-leaveout],x[-leaveout,])
    test = cbind(y[leaveout],x[leaveout,])
    names(train)[1] = names(test)[1] = "y"
    boost.tmp = adaboost.M1(y~.,data=train,maxdepth=depth,mfinal=n.trees,coeflearn=rate) # maxdepth chosen using CV
    pred[leaveout] = predict.boosting(boost.tmp,newdata=test)$class
  }

  pred = factor(pred,levels=levels(y))
  confmat = fixconfmat(table(pred,y),levels(pred),names(table(y)))
  err.rate = 1-sum(diag(confmat))/n

  return(list(predclass=pred,confmat=confmat,err.rate=err.rate))
}



### K nearest neighbors
knn.cv = function(x,y,nfolds=5,k=1,seed=sample(1:10^5,1)){
  require(class)
  set.seed(seed)

  n = length(y)
  p = length(table(y))
  folds = sample(1:nfolds,n,replace=TRUE)
  pred = rep(0,n)

  for(ii in 1:nfolds){
    print(paste("fold",ii,"of",nfolds))
    leaveout = which(folds==ii)
    pred[leaveout] = knn(x[-leaveout,],x[leaveout,],y[-leaveout],k=k)
  }
  pred = factor(levels(y)[pred],levels=levels(y))
  confmat = fixconfmat(table(pred,y),levels(pred),levels(y))
  err.rate = 1-sum(diag(confmat))/n
  return(list(predclass=pred,confmat=confmat,err.rate=err.rate))
}

### support vector machine
svm.cv = function(x,y,nfolds=5,seed=sample(1:10^5,1)){
  require(kernlab)
  set.seed(seed)

  n = length(y)
  p = length(table(y))
  folds = sample(1:nfolds,n,replace=TRUE)
  pred = rep(0,n)

  for(ii in 1:nfolds){
    print(paste("fold",ii,"of",nfolds))
    leaveout = which(folds==ii)
    svm.tmp = ksvm(x=as.matrix(x[-leaveout,]),y=y[-leaveout],kernel='rbfdot')
    pred[leaveout] = predict(svm.tmp,newdata=x[leaveout,])
  }
  pred = factor(levels(y)[pred],levels=levels(y))
  confmat = fixconfmat(table(pred,y),levels(pred),names(table(y)))
  err.rate = 1-sum(diag(confmat))/n
  return(list(predclass=pred,confmat=confmat,err.rate=err.rate))
}

### Neural Nets
nnet.cv = function(x,y,nfolds=5,seed=sample(1:10^5,1)){
  require(nnet)
  set.seed(seed)

  n = length(y)
  p = length(table(y))
  folds = sample(1:nfolds,n,replace=TRUE)
  pred = rep(0,n)

  for(ii in 1:nfolds){
    print(paste("fold",ii,"of",nfolds))
    leaveout = which(folds==ii)
    y.in = y[-leaveout]
    nnet.tmp = nnet(y.in~.,data=cbind(y.in,x[-leaveout,]),size=5,maxit=5000)
    pred[leaveout] = apply(predict(nnet.tmp,newdata=x[leaveout,]),1,which.max)
  }
  pred = factor(levels(y)[pred],levels=levels(y))
  confmat = fixconfmat(table(pred,y),levels(pred),names(table(y)))
  err.rate = 1-sum(diag(confmat))/n
  return(list(predclass=pred,confmat=confmat,err.rate=err.rate))
}


###################
#### pairwise voting, use method = "cart", "svn", "rf","boost"

# to do: add in non-uniform loss function, prior
vote.pairwise = function(x,y,nfolds=10,method="cart",k.meta=5,n.tree=50,mtry=NULL,shrinkage=.001,svmsig=NULL,seed=sample(1:10^6,1)){
  require(kernlab)
  require(nnet)
  require(randomForest)
  require(rpart)
  require(gbm)
  set.seed(seed)

  n = length(y)
  y.names = levels(y)
  p = length(y.names)
  folds = sample(1:nfolds,n,replace=TRUE)
  method = tolower(method)
  
  # initialize predictions (vote & meta)
  votes.pred = matrix(0,n,p*(p-1)/2)
  prob.pred = votes.pred
  pred.meta = rep(0,n)

  if(method=="cart" | method=="rf") {
    FeatImp = matrix(0,dim(x)[2],p)
    row.names(FeatImp)=colnames(x)
    colnames(FeatImp) = y.names
    if(is.null(mtry)){
      mtry = ceiling(sqrt(dim(x)[2]))
    }
  }
  
  for(ii in 1:nfolds){
    print(paste("fold",ii,"of",nfolds))
    leaveout = which(folds==ii)
    n.in = n-length(leaveout)
    x.in = x[-leaveout,]
    y.in = y[-leaveout]
    ind.pair = 0 # index for filling in votes.pred
    votes.meta = matrix(0,n.in,p*(p-1)/2) # initialize meta matrix
    for(jj in 1:(p-1)){
      for(kk in (jj+1):p){
        ind.pair = ind.pair+1
        pair = which(y.in==y.names[jj] | y.in == y.names[kk]) # choose pair of classes
        names.pair = levels(factor(y.in[pair]))
        # fit model
        if(method=="svm"){
 #         svm.fit = ksvm(x=as.matrix(x.in[pair,]),y=factor(y.in[pair]),kernel='rbfdot',type='C-svc',prob.model=TRUE)
          if(is.null(svmsig)){
            svm.fit = ksvm(x=as.matrix(x.in[pair,]),y=factor(y.in[pair]),kernel='rbfdot',type='C-svc')
          } else {
            svm.fit = ksvm(x=as.matrix(x.in[pair,]),y=factor(y.in[pair]),kernel='rbfdot',type='C-svc',kpar=list(sigma=svmsig))#,prob.model=TRUE)
          }
          votes.pred[leaveout,ind.pair] = factor(predict(svm.fit,newdata=x[leaveout,]),levels=y.names)
       #   prob.pred[leaveout,ind.pair] = predict(svm.fit,newdata=x[leaveout,],type='probabilities')[,1]
        # votes for ALL training data to be used in meta-predictor
          votes.meta[,ind.pair] = factor(predict(svm.fit,newdata=x[-leaveout,]),levels=y.names)
        }
        if(method=="boost"){
          #### optimize CV risk over shrinkange & n.trees (interaction.depth??)
          y.boost = ifelse(as.numeric(y.in[pair])==jj,0,1)
          gb.fit = gbm.fit(x=as.matrix(x.in[pair,]),y.boost,distribution="bernoulli",verbose=FALSE,interaction.depth=3,bag.fraction=1,n.minobsinnode=2,shrinkage=shrinkage,n.trees=n.tree)
          votes.pred[leaveout,ind.pair] = factor(names.pair[round(predict(gb.fit,newdata=x[leaveout,],n.trees=n.tree,type='response'))+1],levels=y.names)
           prob.pred[leaveout,ind.pair] = 1-predict(gb.fit,newdata=x[leaveout,],n.trees=n.tree,type='response')
        # votes for ALL training data to be used in meta-predictor
          votes.meta[,ind.pair] = factor(names.pair[round(predict(gb.fit,newdata=x[-leaveout,],n.trees=n.tree,type='response'))+1],levels=y.names)
        }
        if(method=="rf"){
          rf.tmp = randomForest(x=as.matrix(x.in[pair,]),y=factor(y.in[pair]),ntree=n.tree,mtry=mtry)
        # vote for all left out data
          votes.pred[leaveout,ind.pair] = factor(predict(rf.tmp,newdata=x[leaveout,]),levels=y.names)
          prob.pred[leaveout,ind.pair] = predict(rf.tmp,newdata=x[leaveout,],type='prob')[,1]
      # votes for ALL training data to be used in meta-predictor
          votes.meta[,ind.pair] = factor(predict(rf.tmp,newdata=x[-leaveout,]),levels=y.names)
          FeatImp[,jj] = FeatImp[,jj]+rf.tmp$importance
          FeatImp[,kk] = FeatImp[,kk]+rf.tmp$importance
        }
        if(method=="cart"){
          tree.fit = rpart(factor(y.in[pair])~.,data=data.frame(x.in[pair,]),control=rpart.control(minsplit=2,minbucket=1,cp=.001))
          if(dim(tree.fit$cptable)[1] <= 1) {
            print("tree is a stump, skip pruning")
             tree.prune  = tree.fit }
          else {
            tree.prune = prune(tree.fit,cp=tree.fit$cptable[which.min(tree.fit$cptable[,"xerror"]),"CP"])}
          # keep track if features was used
          FeatImp[unique(row.names(tree.prune$splits)),jj] = FeatImp[unique(row.names(tree.prune$splits)),jj]+1
          FeatImp[unique(row.names(tree.prune$splits)),kk] = FeatImp[unique(row.names(tree.prune$splits)),kk]+1
                                        # vote for all left out data
          votes.pred[leaveout,ind.pair] = factor(predict(tree.prune, newdata = data.frame(x[leaveout,]),type="class"),levels=y.names)
          prob.pred[leaveout,ind.pair] = predict(tree.prune,newdata=data.frame(x[leaveout,]),type='prob')[,1]
        # votes for ALL training data to be used in meta-predictor
          votes.meta[,ind.pair] = factor(predict(tree.prune,newdata = data.frame(x[-leaveout,]),type="class"),levels=y.names)
        }
        
      }      
    }

         # use votes.meta & y.in to build 1NN classifier (thru dist. matrix)
      # predict pred.meta using 1NN model on votes.pred[leaveout,]
    D.meta = matrix(0,n-n.in,n.in) # distance matrix
    for(jj in 1:(n-n.in)){
      for(kk in 1:n.in){
        tmp = sum(votes.pred[leaveout[jj],]!=votes.meta[kk,])
        D.meta[jj,kk] = tmp
      }
    }

    # K nearest-neighbor prediction (weighted votes)
    class.wt = sqrt(length(y.in)/table(y.in))
    metaVote = NULL
    for(kk in 1:k.meta){
      minInd = apply(D.meta,1,which.is.min)
      metaVote = cbind(metaVote, y.in[minInd])
      ind.rm = cbind(1:dim(D.meta)[1],minInd)
      D.meta[ind.rm] = 10^6
    }
    # un-weighted kNN vote
    meta.tab = apply(metaVote,1,tabulate)
    pred.meta[leaveout] = unlist(lapply(meta.tab,which.is.max))
#    # weighted kNN vote
#    for(ind in 1:length(meta.tab)){
#      pred.meta.knn1[leaveout[ind]] = which.is.max(meta.tab[[ind]]*class.wt[1:length(meta.tab[[ind]])])
#    }
  }

  pred = apply(apply(votes.pred,1,tabulate,nbins=p),2,which.max)
#  pred = unlist(lapply(apply(votes.pred,1,tabulate),which.max))
  pred = factor(levels(y)[pred],levels=levels(y))
  prob = couple1(prob.pred,coupler="minpair1")
  pred.prob = factor(levels(y)[apply(prob,1,which.max)],levels=levels(y))
  pred.meta = factor(levels(y)[pred.meta],levels=levels(y))
  # pred.meta.knn1 = factor(levels(y)[pred.meta.knn1],levels=levels(y))
  
  confmat = fixconfmat(table(pred,y),levels(pred),levels(y))
  confmat.prob = fixconfmat(table(pred.prob,y),levels(pred.prob),levels(y))
  confmat.meta = fixconfmat(table(pred.meta,y),levels(pred.meta),levels(y))
  # confmat.meta.knn1 = fixconfmat(table(pred.meta.knn1,y),levels(pred.meta.knn1),levels(y))
  
  err.rate = 1-sum(diag(confmat))/n
  err.rate.prob = 1-sum(diag(confmat.prob))/n
  err.rate.meta = 1-sum(diag(confmat.meta))/n
  # err.rate.meta.knn1 = 1-sum(diag(confmat.meta.knn1))/n

  if(method=="cart" | method=="rf"){
    return(list(predclass=pred,predprob=prob,predvotes=votes.pred,confmat=confmat,err.rate=err.rate,predclass.meta=pred.meta,confmat.meta=confmat.meta,err.rate.meta=err.rate.meta,confmat.prob=confmat.prob,err.rate.prob=err.rate.prob,predclass.prob=pred.prob,FeatImp=FeatImp))
  } else {
    return(list(predclass=pred,predprob=prob,predvotes=votes.pred,confmat=confmat,err.rate=err.rate,predclass.meta=pred.meta,confmat.meta=confmat.meta,err.rate.meta=err.rate.meta,confmat.prob=confmat.prob,err.rate.prob=err.rate.prob,predclass.prob=pred.prob))
  }
}


which.is.min = function (x) # use this to break ties at random
{
    y <- seq_along(x)[x == min(x)]
    if (length(y) > 1L) 
        sample(y, 1L)
    else y
}

which.is.min.big = function (x,y.in) # break ties to bigger class
{
    y <- seq_along(x)[x == min(x)]
    if (length(y) > 1L)
      y[which.max(tabulate(y.in)[y.in[y]])]
    else y
}

# pair-wise probability-calculating routines


minpair1 <- function(probin)
  {  ## Count number of classes and construct prob. matrix
    nclass <- (1+sqrt(1 + 8*length(probin)))/2
    if(nclass%%1 != 0) stop("Vector has wrong length only one against one problems supported")
    probim <- matrix(0, nclass, nclass)
    probim[lower.tri(probim)] <- probin
    probim = t(probim)
    probim[lower.tri(probim)] <- 1 - probin
    
    sum <- colSums(probim^2)
    Q <- diag(sum)
    Q[upper.tri(Q)] <- - probin*(1 - probin)
    Q[lower.tri(Q)] <- - probin*(1 - probin)
    SQ <- matrix(0,nclass +1, nclass +1)
    SQ[1:(nclass+1) <= nclass, 1:(nclass+1) <= nclass] <- Q
    SQ[1:(nclass+1) > nclass, 1:(nclass+1) <= nclass] <- rep(1,nclass)
    SQ[1:(nclass+1) <= nclass, 1:(nclass+1) > nclass] <- rep(1,nclass)
    
    rhs <- rep(0,nclass+1)
    rhs[nclass + 1] <- 1

    p <- solve(SQ,rhs)

    p <- p[-(nclass+1)]/sum(p[-(nclass+1)])
    return(p)
  }


couple1 <- function(probin, coupler = "minpair1")
{
  if(is.vector(probin))
    probin <- matrix(probin,1)
    m <- dim(probin)[1]
  
  coupler <- match.arg(coupler, c("minpair1", "pkpd", "vote", "ht"))

#  if(coupler == "ht")
#    multiprob <- sapply(1:m, function(x) do.call(coupler, list(probin[x ,], clscnt))) 
#  else
    multiprob <- sapply(1:m, function(x) do.call(coupler, list(probin[x ,])))    

  return(t(multiprob))
}


