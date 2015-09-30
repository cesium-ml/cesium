
# load data
path = "/Users/jwrichar/Documents/CDI/TCP/debosscher/"
#path = "/accounts/gen/vis/jwrichar/debosscher/"
#.libPaths("/accounts/gen/vis/jwrichar/Rlib")

source(paste(path,"R/utils_classify.R",sep=""))
source(paste(path,"R/class_cv.R",sep=""))
                                        # load in features & classes
data = load.data(path)
features = data$features
classes = data$classes
ID = data$ID
features = featureConvert(features) # convert freq / amp to ratios to first freq / amp

features = features[,-which(names(features)=='freq_nharm')] # remove freq_nharm
features = features[,-which(names(features)=='stetson_mean')] # remove stet mean
features = features[,-which(names(features)=='kurtosis')] # remove kurtosis
features = features[,-which(names(features)=='freq_harmonics_offset')] # remove time offset
features = features[,-which(names(features)=='freq_amplitude_ratio_21')] # remove time offset
features = features[,-which(names(features)=='freq_amplitude_ratio_31')] # remove time offset
features = features[,-which(names(features)=='freq_frequency_ratio_21')] # remove time offset
features = features[,-which(names(features)=='freq_frequency_ratio_31')] # remove time offset
classes.mat = class.hier(classes)
n = length(classes)
print(paste("Number of sources analyzed:",n))

# feature importance (to screen features for SVM)
library(randomForest)
rf.outinit = randomForest(features,classes,nfolds=10)
featimp = rf.outinit$importance
featimp.q = quantile(featimp,0.7)


####################
# initialize error-rate + computation time matrix
err.rates = matrix(0,10,10)
bad = (costMat(10)==10) # define bad misclassifications
err.rates.bad = matrix(0,10,10)
row.names(err.rates) = c("CART","C4.5","RF","Boost","CART.pw","RF.pw","Boost.pw","SVM.pw","HSC-RF","HMC-RF")
row.names(err.rates.bad) = c("CART","C4.5","RF","Boost","CART.pw","RF.pw","Boost.pw","SVM.pw","HSC-RF","HMC-RF")
comp.times = matrix(0,10,10)
row.names(comp.times) = c("CART","C4.5","RF","Boost","CART.pw","RF.pw","Boost.pw","SVM.pw","HSC-RF","HMC-RF")

for(ii in 1:10){
#for(ii in 1:1){
  # keep track of all classifications (to see which sources are hard)
  predictions = matrix(0,10,length(classes))

  seed = sample(1:10^6,1)

  print(err.rates)
  print(err.rates.bad)
  print(comp.times)
  
# CART
  t.st = proc.time()[3]
  tree.out = rpart.cv(features,classes,nfolds=10,method="gini",seed=seed)
  comp.times[1,ii] = proc.time()[3]-t.st
  err.rates[1,ii] = tree.out$err.rate
  err.rates.bad[1,ii] = sum(tree.out$confmat*bad)/n
  predictions[1,] = tree.out$predclass

# C4.5
  t.st = proc.time()[3]
  tree.out = rpart.cv(features,classes,nfolds=10,method="information",seed=seed)
  comp.times[2,ii] = proc.time()[3]-t.st
  err.rates[2,ii] = tree.out$err.rate
  err.rates.bad[2,ii] = sum(tree.out$confmat*bad)/n
  predictions[2,] = tree.out$predclass
 
# RF
  t.st = proc.time()[3]
  rf.out = rf.cv(features,classes,n.trees=1000,mtry=15,nfolds=10,seed=seed)
  comp.times[3,ii] = proc.time()[3]-t.st
  err.rates[3,ii] = rf.out$err.rate
  err.rates.bad[3,ii] = sum(rf.out$confmat*bad)/n
  predictions[3,] = rf.out$predclass

# Boosting
  t.st = proc.time()[3]
  boost.out = boostTree.cv(features,classes,n.trees=50,depth=15,rate="Breiman",nfolds=5,seed=seed)
  comp.times[4,ii] = proc.time()[3]-t.st
  err.rates[4,ii] = boost.out$err.rate
  err.rates.bad[4,ii] = sum(boost.out$confmat*bad)/n
  predictions[4,] = boost.out$predclass

# CART pw vote
# CART pw meta-vote
  t.st = proc.time()[3]
  cart.pw = vote.pairwise(features,classes,nfolds=10,method='cart',k.meta=10,seed=seed)
  comp.times[5,ii] = proc.time()[3]-t.st
  err.rates[5,ii] = cart.pw$err.rate.prob
  err.rates.bad[5,ii] = sum(cart.pw$confmat.prob*bad)/n
  predictions[5,] = cart.pw$predclass.prob
  if(ii==1){
    postscript(paste(path,"plots/featImportance_pwCart.ps",sep=""),horizontal=TRUE)
    plot.featImp(cart.pw$FeatImp)
    dev.off()
  }

# RF pw vote
# RF pw meta-vote
  t.st = proc.time()[3]
  rf.pw = vote.pairwise(features,classes,nfolds=10,method='rf',n.tree=100,mtry=10,k.meta=10,seed=seed)
  comp.times[6,ii] = proc.time()[3]-t.st
  err.rates[6,ii] = rf.pw$err.rate.prob
  err.rates.bad[6,ii] = sum(rf.pw$confmat.prob*bad)/n
  predictions[6,] = rf.pw$predclass.prob
   if(ii==1){
    pdf(paste(path,"plots/featImportance_pwRF.pdf",sep=""),height=8,width=10)
#   plot.featImp(t(t(rf.pw$FeatImp)/colSums(rf.pw$FeatImp))) # regular
    plot.featImp(t(t(sqrt(rf.pw$FeatImp))/colSums(sqrt(rf.pw$FeatImp)))) # square-root (better)
    dev.off()
  }

  #  Boosting pairwise voting
  t.st = proc.time()[3]
  boost.pw = vote.pairwise(features,classes,nfolds=5,n.tree=50,shrinkage=.05,method='boost',k.meta=10,seed=seed)
  comp.times[7,ii] = proc.time()[3]-t.st
  err.rates[7,ii] = boost.pw$err.rate.prob
  err.rates.bad[7,ii] = sum(boost.pw$confmat.prob*bad)/n
  predictions[7,] = boost.pw$predclass.prob

# SVM pw vote
# SVM pw meta-vote
  t.st = proc.time()[3]
  svm.pw = vote.pairwise(features[,which(featimp>20)],classes,nfolds=10,method='svm',svmsig=0.05,k.meta=10,seed=seed)
  comp.times[8,ii] = proc.time()[3]-t.st
  err.rates[8,ii] = svm.pw$err.rate
  err.rates.bad[8,ii] = sum(svm.pw$confmat*bad)/n
  predictions[8,] = svm.pw$predclass

 ## HSC
  t.st = proc.time()[3]
  hsc.out = rf.hsc(features,classes.mat,classes,nfolds=10,seed=seed,n.trees=1000,mtry=25)
  comp.times[9,ii] = proc.time()[3]-t.st
  err.rates[9,ii] = hsc.out$err.rate
  err.rates.bad[9,ii] = sum(hsc.out$confmat*bad)/n
  predictions[9,] = hsc.out$predclass

  # HMC
#  t.st = proc.time()[3]
#  hmc.run(out = "hmc1.s",n.trees=500,mtry=25,w0=0.5,seed=seed,path=paste(path,"clus/",sep=""))
#  hmc.out = hmc.read(classes,classes.mat$class,file=paste(path,"clus/hmc1.test.pred.arff",sep=""))
#  comp.times[10,ii] = proc.time()[3]-t.st
#  err.rates[10,ii] = hmc.out$err.rate
#  err.rates.bad[10,ii] = sum(hmc.out$confmat*bad)/n
#  predictions[10,] = hmc.out$predclass



  superClass = factor(levels(classes)[apply(apply(predictions,2,tabulate,nbins=length(table(classes))),2,which.max)])
  superconfmat = fixconfmat(table(superClass,classes),levels(superClass),levels(classes))
  print(paste("Super-classifier mis-class rate:",1-sum(diag(superconfmat))/length(classes)))
  # 23.0%

  
  if(ii==1){
    periods = 1/features[,"freq1_harmonics_freq_0"]
    wrong.all = which(apply(as.numeric(classes)==t(predictions),1,sum)==0) # which sources always misclassified?
    # plot folded LCs w/ spline fits for those that are always misclassified
    postscript(paste(path,"plots/LCfold_misclass.ps",sep=""),horizontal=F)
    par(mfrow=c(4,1),mar=c(0,4,0,.3))  
    for(indbad in 1:length(wrong.all)){
      # read in folded LC plus spline fit
      perLC = read.table(paste(path,"LC_timefold/deboss_pf",ID[wrong.all[indbad]],".dat",sep=""))
      perFit = read.table(paste(path,"LC_timefold/deboss_spline",ID[wrong.all[indbad]],".dat",sep=""))

      plot(perLC[,1],perLC[,2],pch=20,cex=.5,xlim=c(0,1),ylim=range(perLC[,2])[2:1],ylab="mag",xaxt='n')
      arrows(perLC[,1],perLC[,2]+perLC[,3],perLC[,1],perLC[,2]-perLC[,3],length=0)
      lines(perFit[,1],perFit[,2],col=2,lwd=2)
      lines(perFit[,1],perFit[,2]-perFit[,3],col=4,lty=3,lwd=1.5)
      lines(perFit[,1],perFit[,2]+perFit[,3],col=4,lty=3,lwd=1.5)
      text(0.5,min(perLC[,2]),paste("ID",ID[wrong.all[indbad]],":",classes[wrong.all[indbad]]),pos=1,col="darkred",cex=1.5)
      text(1,max(perLC[,2]),paste("Classify as:",superClass[wrong.all[indbad]]),cex=1.5,col="darkblue",pos=2)
      text(0,max(perLC[,2]),paste("Period =",signif(periods[wrong.all[indbad]],2),"days"),cex=1.5,col="darkblue",pos=4)
      axis(1,labels=FALSE)
      if(indbad %% 4 == 0){
        axis(1,padj=-3.5,cex.axis=1)
      }    
    }
    dev.off()
  }

    print(paste(ii,"of 10 done!"))
}
#boxplot(err.rates~row.names(err.rates))

write(t(err.rates),paste(path,"out/errorRates.dat",sep=""),ncolumns=10)
write(t(err.rates.bad),paste(path,"out/errorRates_bad.dat",sep=""),ncolumns=10)
write(t(comp.times),paste(path,"out/compTimes.dat",sep=""),ncolumns=10)

round(cbind(apply(err.rates,1,mean)*100,
apply(err.rates.bad,1,mean)*100,apply(comp.times,1,mean)),1)

## CART     32.2 13.7  10.6
## C4.5     29.8 12.7  14.4
## RF       22.8  8.0 117.6
## Boost    25.0  9.9 466.5
## CART.pw  25.8  8.7 323.2
## RF.pw    23.4  8.0 290.3
## Boost.pw 24.1  8.2 301.5
## SVM.pw   25.3  8.4 273.0
## HSC-RF   23.5  7.8 230.9
## HMC-RF   23.4  8.2 946.0 


# hmc :0.23365759   0.08171206 945.96260000

##              [,1]        [,2]        [,3]         [,4]         [,5]
## [1,]   0.23151751   0.2341115   0.2392996   0.23281453 2.360571e-01
## [2,]   0.08106355   0.0843061   0.0843061   0.08236057 8.171206e-02
## [3,] 940.91800000 901.4580000 888.7930000 958.16100000 1.028320e+03
##              [,6]         [,7]         [,8]         [,9]        [,10]
## [1,]   0.23281453 2.347601e-01   0.23994812   0.22827497   0.22697795
## [2,]   0.08236057 8.106355e-02   0.08041505   0.07782101   0.08171206
## [3,] 918.74900000 1.001902e+03 898.06400000 964.22500000 959.03600000


# SECOND PART:
# take a couple classifiers and apply to debosscher's features
feat.deb = read.table(paste(path,"debos_features.dat",sep=""))
# hipparcos
ind.hip = read.table("/Users/jwrichar/Documents/CDI/TCP/debosscher/hipparcos_hipind.dat")[,1]
names.deb = paste(feat.deb[,1])
feat.deb=feat.deb[-which(duplicated(names.deb)),]
names.deb = names.deb[-which(duplicated(names.deb,fromLast=TRUE))]
names.hip = strsplit(paste(read.table("/Users/jwrichar/Documents/CDI/TCP/debosscher/J_A+A_475_1159_list.dat.txt",skip=4,sep="|",strip.white=TRUE)[ind.hip,5]),split=" ")
subset = NULL
for(ii in 1:length(names.hip)){
  subset = c(subset,which(names.deb==names.hip[[ii]][1]))
}
feat.hip = feat.deb[subset,]
 duplic = c("c-25473.hip","c-26304.hip","c-33165.hip","c-34042.hip","c-36750.hip","c-39009.hip","c-53461.hip","c-57812.hip","c-58907.hip","c-75377.hip","c-104029.hip")
   hip.out = which(feat.hip[,31]=="ROAP" | feat.hip[,31]=="XB" | feat.hip[,31]=="SXPHE" | feat.hip[,1] %in% duplic)
feat.hip = feat.hip[-hip.out,]
class.hip = class.debos(feat.hip[,31])
feat.hip = feat.hip[,-c(1,31)]
# ogle
feat.ogle = feat.deb[c(which(substr(names.deb,1,4)=="OGLE"),1251:1345),-c(1,31)]
class.ogle = class.debos(feat.deb[c(which(substr(names.deb,1,4)=="OGLE"),1251:1345),31])

features.deb = rbind(feat.hip,feat.ogle)
class.deb = factor(c(paste(class.hip),paste(class.ogle)))
class.deb.mat = class.hier(class.deb)

err.deb = matrix(0,3,10)
for(ii in 1:10){
  seed = sample(1:10^6,1)
# RF 
  rf.deb = rf.cv(features.deb,class.deb,nfolds=10,n.trees=1000,mtry=10,seed=seed)
  err.deb[1,ii] = rf.deb$err.rate #26.4%

# RF-pw
  rfpw.deb = vote.pairwise(features.deb,class.deb,nfolds=10,method='rf',n.tree=100,k.meta=10,seed=seed)
  err.deb[2,ii] = rfpw.deb$err.rate.prob #29.0%

  # HSC-RF
  hsc.deb = rf.hsc(features.deb,class.deb.mat,class.deb,nfolds=10,seed=seed,n.trees=1000,mtry=10)
  err.deb[3,ii] = hsc.deb$err.rate # 28.3%
  
  print(err.deb)
}
row.names(err.deb)=c("RF","RF.pw","HSC-RF")
write(t(err.deb),paste(path,"out/errorRates_debFeatures.dat",sep=""),ncolumns=10)

## >  apply(err.deb,1,mean)
##        RF     RF.pw    HSC-RF 
## 0.2669464 0.2891543 0.2812782 

# THIRD PART:
# 
#  run our algorithms on only our LS features
features.ls = features[which(substr(names(features),1,4)=="freq")]

err.ls = matrix(0,3,10)

for(ii in 1:10){
  seed = sample(1:10^6,1)
# RF 
  rf.ls = rf.cv(features.ls,classes,nfolds=10,n.trees=1000,mtry=10,seed=seed)
  err.ls[1,ii] = rf.ls$err.rate #26.4%

# RF-pw
  rfpw.ls = vote.pairwise(features.ls,classes,nfolds=10,method='rf',n.tree=100,k.meta=10,seed=seed)
  err.ls[2,ii] = rfpw.ls$err.rate.prob #29.0%

  # HSC-RF
  hsc.ls = rf.hsc(features.ls,classes.mat,classes,nfolds=10,seed=seed,n.trees=1000,mtry=10)
  err.ls[3,ii] = hsc.ls$err.rate # 28.3%
  
  print(err.ls)
}
row.names(err.ls)=c("RF","RF.pw","HSC-RF")

write(t(err.ls),paste(path,"out/errorRates_LSFeatures.dat",sep=""),ncolumns=10)

## > apply(err.ls,1,mean)
##        RF     RF.pw    HSC-RF 
## 0.2378080 0.2634890 0.2459144 

# FOURTH PART:
# 
#  run our algorithms on only our non-LS features
features.nls = features[which(substr(names(features),1,4)!="freq")]

err.nls = matrix(0,3,10)

for(ii in 1:10){
  seed = sample(1:10^6,1)
# RF 
  rf.nls = rf.cv(features.nls,classes,nfolds=10,n.trees=1000,mtry=7,seed=seed)
  err.nls[1,ii] = rf.nls$err.rate #26.4%

# RF-pw
  rfpw.nls = vote.pairwise(features.nls,classes,nfolds=10,method='rf',n.tree=100,k.meta=10,seed=seed)
  err.nls[2,ii] = rfpw.nls$err.rate.prob #29.0%

  # HSC-RF
  hsc.nls = rf.hsc(features.nls,classes.mat,classes,nfolds=10,seed=seed,n.trees=1000,mtry=7)
  err.nls[3,ii] = hsc.nls$err.rate # 28.3%
  
  print(err.nls)
}
row.names(err.nls)=c("RF","RF.pw","HSC-RF")

write(t(err.nls),paste(path,"out/errorRates_NLSFeatures.dat",sep=""),ncolumns=10)

## > apply(err.nls,1,mean)
##        RF     RF.pw    HSC-RF 
## 0.2763294 0.2855383 0.2783398 


# Debosscher results:
# Gaussian Mixture Model: 31%
# Bayes avg. of ANN: 30%
# 3-dependent Bayesian Network: 34%
# SVM: 50%

err.rates = read.table(paste(path,"out/errorRates.dat",sep=""))
row.names(err.rates) = c("CART","C4.5","RF","Boost","CART.pw","RF.pw","Boost.pw","SVM.pw","HSC-RF","HMC-RF")
err.deb = read.table(paste(path,"out/errorRates_debFeatures.dat",sep=""))
row.names(err.deb)=c("RF","RF.pw","HSC-RF")
err.ls = read.table(paste(path,"out/errorRates_LSFeatures.dat",sep=""))
row.names(err.ls)=c("RF","RF.pw","HSC-RF")
err.nls = read.table(paste(path,"out/errorRates_NLSFeatures.dat",sep=""))
row.names(err.nls)=c("RF","RF.pw","HSC-RF")


# plot boxplot
Errors = rbind(err.rates,err.deb,err.ls,err.nls)

pdf(paste(path,"plots/misclassRates.pdf",sep=""),width=12,height=8)
par(mar=c(5,4.5,.5,.3))  
boxplot(t(Errors),range=0,names=c(row.names(err.rates),row.names(err.deb),row.names(err.ls),row.names(err.nls)),ylab="Mis-classification Rate",cex.lab=1.5,xaxt="n",boxwex=.5,ylim=c(.21,.3375))
axis(1,labels=c(row.names(err.rates),row.names(err.deb),row.names(err.ls),row.names(err.nls)),at=1:dim(Errors)[1],las=2,cex.axis= 1,padj=0.5,tick=TRUE)
abline(.3,0,col=2,lty=2,lwd=2.5)
abline(v=c(10.5,13.5,16.5),lwd=2)
legend("topleft","Debosscher et al. (2007)",lwd=2.5,lty=2,col=2,cex=1.45,bty='n')
text(5.5,.215,"LS + non-LS Features\n(this work)",cex=1.25,col='darkblue')
text(12,.215,"LS Features\n(Debosscher)",cex=1.25,col='darkblue')
text(15,.215,"LS Features\n(this work)",cex=1.25,col='darkblue')
text(18.5,.215,"non-LS Feat.\n(this work)",cex=1.25,col='darkblue')
dev.off()
