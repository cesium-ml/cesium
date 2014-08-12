#####################################################################
##### run this script to create MACC classification catalog for ASAS
## and save all relevant output, classifications + performance metrics
######################################################################
n = dim(feat.debos)[1]

############################
# load ASAS data
asasdat=read.arff(file=asas_test_arff_fpath) 
feat.tmp = data.frame(asasdat)
feat.asas = matrix(0,dim(feat.tmp)[1],dim(feat.debos)[2])
for(ii in 1:dim(feat.debos)[2]){
  feat.asas[,ii]= feat.tmp[,names(feat.tmp)==names(feat.debos)[ii]]
}
colnames(feat.asas) = names(feat.debos)
feat.asas = data.frame(feat.asas)
class.asas = paste(asasdat$class) # this throws double & low-confidence labels into MISC
class.asas[class.asas=="UNKNOWN"] = "MISC"
class.asas = class.debos(class.asas)
ID.asas = asasdat$source_id
n.epochs.asas = read.table(paste(path,"data/n_epochs_asas.dat",sep=""))[,1]
N = dim(feat.asas)[1]

### 20120810 dstarr commends out:
## add RRLd feature (0.0035 chosen by considering f2/f1 of known RRd)
#feat.debos$freq_rrd = ifelse(abs(feat.debos$freq_frequency_ratio_21 - 0.746) < 0.0035 | abs(feat.debos$freq_frequency_ratio_31 - 0.746) < 0.0035, 1,0)
#feat.asas$freq_rrd = ifelse(abs(feat.asas$freq_frequency_ratio_21 - 0.746) < 0.0035 | abs(feat.asas$freq_frequency_ratio_31 - 0.746) < 0.0035, 1,0)



## ASAS ACVS classes (as of ACTA ASTRONOMICA Vol. 55 (2005) pp. 275–301):
# to obtain all ACVS classifications (not throwing double labels into MISC)
acvs = read.table(paste(path,"data/ACVS.1.1",sep=""))
# positional information for ASAS and debosscher
ra.dec.asas = read.table(paste(path,"data/ra_dec.csv",sep=""),sep=";")
ra.dec.deb = read.table(paste(path,"data/ra_dec_deb.csv",sep=""),sep=";")

# fix order of acvs table to be same as our ARFF file (ordered by dotAstro ID)
fix.class = NULL
for(ii in 1:N){ # fix order of class.asas vector
  fix.class = c(fix.class,which(ra.dec.asas[,1]==ID.asas[ii])) 
}
acvs = acvs[fix.class,]
ra.dec.asas = ra.dec.asas[fix.class,]


## sum(acvs[,1]==ra.dec.asas[,9]) # 50124


# # # # # # # # # 
# Joey's original asas_catalog.R:
# # # # # # # # # 

feat.train = feat.debos
class.train = class.deb
ID.train = ID

# keep track of which ASAS data are in training set
intrain = rep("",length(ID.asas))

####################################################
## REMOVE THE FOLLOWING LOW-AMPLITUDE CLASSES:
## k. Lambda Bootis, m. Slowly Puls. B, n. Gamma Doradus, r. Wolf-Rayet
cat("Removing low-amplitude classes\n")
lowamp.rem = c('k. Lambda Bootis', 'm. Slowly Puls. B', 'n. Gamma Doradus', 'r. Wolf-Rayet')
remove = which(class.train %in% lowamp.rem)
feat.train = feat.train[-remove,]
class.train = factor(class.train[-remove])
ID.train = ID.train[-remove]


####################################################
## add ASAS - debosscher overlap data to training set
# for each match, replace Hipparcos/OGLE features with ASAS features
cat("Adding ASAS training objects that overlap with Debosscher\n")
counter = 0
for(ii in 1:dim(ra.dec.deb)[1]){
  # kludgey match criterion: rounded versions of RA & Dec both match
  ind = which(round(ra.dec.asas[,10],2)==round(ra.dec.deb[ii,10],2) &
    round(ra.dec.asas[,12],2)==round(ra.dec.deb[ii,12],2))
  if(length(ind)>0){
    ind1 = which(ID.asas == ra.dec.asas[ind,1])
    ind2 = which(ID == ra.dec.deb[ii,1])
    ind3 = which(ID.train == ra.dec.deb[ii,1])
    if(length(ind2)==1){
      counter = counter+1
      ## remove old Hipparcos data
      feat.train = feat.train[-ind3,]
      class.train = class.train[-ind3]
      ID.train = ID.train[-ind3]
      ## add new ASAS data
      feat.train = rbind(feat.train,feat.asas[ind1,])
      class.train = c(paste(class.train),paste(class.deb[ind2]))
      ID.train = c(ID.train,ID.asas[ind1])
      intrain[ind1] = paste(class.deb[ind2])
    }
  }
}
class.train = factor(class.train)
nn = length(class.train)
# total size: 
print(table(class.train[(nn-counter+1):nn])[table(class.train[(nn-counter+1):nn])>0])
 ##              a. Mira        b1. Semireg PV           c. RV Tauri 
 ##                   71                     9                     5 
 ## d. Classical Cepheid    e. Pop. II Cepheid       g. RR Lyrae, FM 
 ##                   76                     9                    62 
 ##      h. RR Lyrae, FO        j. Delta Scuti            j1. SX Phe 
 ##                   15                     9                     1 
 ##       l. Beta Cephei       o. Pulsating Be       p. Per. Var. SG 
 ##                    2                     1                     2 
 ##   s1. Class. T Tauri s2. Weak-line T Tauri       t. Herbig AE/BE 
 ##                    1                     2                     1 
 ##         u. S Doradus        v. Ellipsoidal 
 ##                    1                     1 
cat("number added:",counter,"\n")
# 268


## ####################################################
## ####################################################
## # RF classifier fit on Debosscher data (OGLE, Hip, ASAS):
## cat("Fitting Original RF on Deb data\n")
## rf.deb = randomForest(x=as.matrix(feat.train),y=class.train,mtry=15,ntree=1000,nodesize=1)
## pred.asas.0 = predict(rf.deb,newdata = feat.asas)
## pred.asas.prob.0 = predict(rf.deb,newdata = feat.asas,type='prob')
## # agreement w/ acvs labels
## par(mar=c(1.5,9,9,1.95))
## asas.tab = table(pred.asas.0,class.asas)
## asas.tab = asas.tab[,c(1:8,10:13,9)]
## plot.table(asas.tab,title="",cexprob=1,cexaxis=1.22)
## abline(h=1/24,lwd=4,col=4)
## mtext("ACVS Class",2,padj=-6.05,cex=2)
## mtext("RF Predicted Class",3,padj=-5.8,cex=2)

## ###### performance metrics ##########
## agree.acvs = sum(paste(pred.asas.0)==paste(class.asas))/sum(class.asas!="MISC")
## p.hat.0 = apply(pred.asas.prob.0,1,max)
## mean.p.hat = mean(p.hat.0)
## perc.conf = sum(p.hat.0>0.5)/N


####################################################
####################################################
# add AL sources to training set
cat("Adding AL data to training set\n")
m=9 # number of AL steps
#### loop through the steps
for(step in 1:m){
  cat("Step",step,"of",m,"\n")
  # these files are also in: trunk/Data/allstars/
  instep = read.table(paste(path,"data/AL_addToTrain_",step,".dat",sep=""))
  
  for(kk in 1:length(instep[,1])){
    if(length(intersect(ID.asas[which(ID.asas==instep[kk,1])],ID.train))==0){ # only add items that are not already included
      feat.train = rbind(feat.train,feat.asas[which(ID.asas==instep[kk,1]),])
      class.train = c(paste(class.train),paste(class.debos(instep[kk,2])))
      ID.train = c(ID.train,ID.asas[which(ID.asas==instep[kk,1])])
      intrain[which(ID.asas==instep[kk,1])] = paste(class.debos(instep[kk,2]))
    }
    else{ cat(ID.asas[which(ID.asas==instep[kk,1])]," already added\n")}
  }
  class.train = factor(class.train)
}
cat("New training set size:",dim(feat.train)[1],"\n")
cat("Number of unique sources:",length(ID.train),"\n")


####################################################
####################################################
## add selected SIMBAD confirmed training sources
cat("Adding SIMBAD confirmed sources\n")
# this file is also in: trunk/Data/allstars/
instep = read.table(paste(path,"data/AL_SIMBAD_confirmed.dat",sep=""))# 94 sources
instep = instep[instep[,1] %in% setdiff(instep[,1],ID.train),] # 80 sources

### removed symbiotics on 20120310; they are only identifiable spectroscopically (AAM)
#symbiotics = read.table("/Users/jwrichar/Documents/CDI/TCP/trunk/Data/allstars/symbiotics_munari_2002_catalog.dat")
#instep = rbind(instep,symbiotics)

# loop through SIMBAD-confirmed sources & add to training set
for(kk in 1:length(instep[,1])){
  if(length(intersect(ID.asas[which(ID.asas==instep[kk,1])],ID.train))==0){ # only add items that are not already included
    feat.train = rbind(feat.train,feat.asas[which(ID.asas==instep[kk,1]),])
    class.train = c(paste(class.train),paste(class.debos(instep[kk,2])))
    ID.train = c(ID.train,ID.asas[which(ID.asas==instep[kk,1])])
    intrain[which(ID.asas==instep[kk,1])] = paste(class.debos(instep[kk,2]))
  }
  else{cat("already in training set\n")}
}
class.train = factor(class.train)

### add more known RCBs:
new.RCB = c(250762, 257713, 251489, 256221, 247066)
for(kk in 1:length(new.RCB)){
  feat.train = rbind(feat.train,feat.asas[which(ID.asas==new.RCB[kk]),])
  class.train = factor(c(paste(class.train),"r1. RCB"))
  ID.train = c(ID.train,new.RCB[kk])
  intrain[which(ID.asas==new.RCB[kk])] = c("r1. RCB")
}





################################################################################
## ADD RS CVn and BY Dra training objects from Strassmeier 1988
################
##  RS CVn
rscvn = read.table(paste(path,"data/RS_CVn_ra_dec_training.dat",sep=""),sep=" ")
rscvn.result = NULL
for(ii in 1:length(rscvn[,1])){
  ind = which(substr(ra.dec.asas[,9],1,4)==paste(substr(rscvn[ii,1],1,2),substr(rscvn[ii,1],4,5),sep="") & substr(ra.dec.asas[,9],7,11)==paste(substr(rscvn[ii,2],1,3),substr(rscvn[ii,2],5,6),sep=""))
  if(length(ind)==1){
    if(length(intersect(ID.asas[which(ID.asas==ra.dec.asas[ind,1])],ID.train))==0){ # only add items that are not already included
      # add to training set
      feat.train = rbind(feat.train,feat.asas[which(ID.asas==ra.dec.asas[ind,1]),])
      class.train = c(paste(class.train),"s3. RS CVn")
      ID.train = c(ID.train,ID.asas[which(ID.asas==ra.dec.asas[ind,1])])
      intrain[which(ID.asas==ra.dec.asas[ind,1])] = "s3. RS CVn"
    }
  }
}
class.train = factor(class.train)

################
##  BY Dra (added as RS CVn; no point in making an extra class for 1 object)
bydra = read.table(paste(path,"data/BY_Dra_ra_dec_training.dat",sep=""),sep=" ")
bydra.result = NULL
for(ii in 1:length(bydra[,1])){
  ind = which(substr(ra.dec.asas[,9],1,4)==paste(substr(bydra[ii,1],1,2),substr(bydra[ii,1],4,5),sep="") & substr(ra.dec.asas[,9],7,11)==paste(substr(bydra[ii,2],1,3),substr(bydra[ii,2],5,6),sep=""))
  if(length(ind)==1){
    if(length(intersect(ID.asas[which(ID.asas==ra.dec.asas[ind,1])],ID.train))==0){ # only add items that are not already included
      # add to training set
      feat.train = rbind(feat.train,feat.asas[which(ID.asas==ra.dec.asas[ind,1]),])
      class.train = c(paste(class.train),"s3. RS CVn")
      ID.train = c(ID.train,ID.asas[which(ID.asas==ra.dec.asas[ind,1])])
      intrain[which(ID.asas==ra.dec.asas[ind,1])] = "s3. RS CVn"
    }
  }
}
class.train = factor(class.train)


N.train = length(ID.train)


################################################
################################################
# now fit classifier on combined training set
################################################

# output ASAS training set IDs and classes
write( rbind(ID.train, paste(class.train)),paste(path,"tables/training_set_id_class.dat",sep=""),ncolumns=2,sep=",\t")

cat("Final training set size:",dim(feat.train)[1],"\n") 
cat("Number of unique sources:",length(unique(ID.train)),"\n")

################################################
# tune RF parameters (uncomment below to run, is expensive to run grid search)
################################################
#source(paste(path,"R/tune_asas_RF.R",sep=""))
#tuneparam = tuneRF(feat.train, class.train, cv = 5, asas = which(ID.train > 200000),ntree=c(5000),mtry=seq(15,21,2),nodesize=2)
## ntree = 5000 mtry = 17 nodesize = 1 :
##   CV Error = 0.1915
################################################

# fit the RF with optimal tuning parameters on entire training set
cat("Fitting Final Random Forest\n")
rf.tr = randomForest(x=as.matrix(feat.train),y=class.train,mtry=17,ntree=5000,nodesize=1)
pred.asas.AL = predict(rf.tr,newdata = feat.asas)
pred.asas.prob.AL = predict(rf.tr,newdata = feat.asas,type='prob')

# save RF object 
#save(rf.tr,file=paste(path,"data/asas_randomForest.Rdat",sep=""))
save(rf.tr,file=rf_clfr_fpath)

agree.acvs = sum(paste(pred.asas.AL)==paste(class.asas))/sum(class.asas!="MISC")
p.hat.AL = apply(pred.asas.prob.AL,1,max)
mean.p.hat = mean(p.hat.AL)
perc.conf = sum(p.hat.AL>0.5)/N

#  performance metrics
cat("Final performance metrics:\n")
cat("Agreement w/ ACVS:",agree.acvs,"\n")
cat("Mean max p-hat:",mean.p.hat,"\n")
cat("Percent w/ prob > 0.5:",perc.conf,"\n")
# Agreement w/ ACVS: 0.8080446 

# plot confusion matrix w/ ACVS
par(mar=c(1.5,9,9,1.95))
asas.tab = table(pred.asas.AL,class.asas)
asas.tab = asas.tab[,c(1:8,10:13,9)]
plot.table(asas.tab,title="",cexprob=1,cexaxis=1.06)
abline(h=1/24,lwd=4,col=4)
mtext("ACVS Class",2,padj=-6.05,cex=2)
mtext("RF Predicted Class",3,padj=-5.8,cex=2)


########
## plot feature importance (average over 5 repetitions)
plotfi = FALSE
if(plotfi){        
  featimp = matrix(0,length(rf.tr$importance),5)
  rownames(featimp) = rownames(rf.tr$importance)
  featimp[,1] = rf.tr$importance
  for(ii in 2:5){
    rf.tmp =  randomForest(x=as.matrix(feat.train),y=class.train,mtry=17,ntree=5000,nodesize=1)
    featimp[,ii] = rf.tmp$importance
  }
  featimp.mean = apply(featimp,1,mean)
  featimp.sd = apply(featimp,1,sd)

  featimp.sort = featimp.mean[sort(featimp.mean,index.return=TRUE,decreasing=T)$ix]
  featimp.sdsort = featimp.sd[sort(featimp.mean,index.return=TRUE,decreasing=T)$ix]

  pdf(paste(path,"plots/asas_rf_imp.pdf",sep=""),height=6,width=9)
  par(mar=c(5,14,1,1))
  barplot(featimp.sort[20:1],horiz=TRUE,xlab="Mean Gini Decrease",names.arg=rep("",20),space=0.2,lwd=2,col=2,xlim=c(0,150))
  axis(2,labels=names(featimp.sort)[20:1],at=0.7+(0:19)*1.2,tick=FALSE,las=2)
  arrows(featimp.sort[20:1] - featimp.sdsort[20:1], 0.7+(0:19)*1.2, featimp.sort[20:1] + featimp.sdsort[20:1], 0.7+(0:19)*1.2, code=3, angle=90, length=0.05,lwd=2)
  legend('bottomright',"Feature Importance",cex=2,bty="n",text.col=1)
  dev.off()
}


######################################################
# compute outlier measure
######################################################

## DO DISTANCE-BASED OUTLIER MEASURE
# set to TRUE if you want to compute it, else read it in from file
compoutlier = FALSE
source(paste(path,"R/compute_outlier.R",sep=""))
if(compoutlier){
  cat("Computing classifier confidence values\n")
  outlier.score = anomScore(feat.train,class.train, feat.asas, ntree=500, knn=2, metric="rf")
  write(outlier.score,paste(path,"data/outScore_asas_class.dat",sep=""),ncolumns=1)

  # find optimal threshold using cross-validation on training set
  source(paste(path,"R/confidence_findThresh.R",sep=""))
} else {
  outlier.score = read.table(paste(path,"data/outScore_asas_class.dat",sep=""))[,1]
  out.thresh = 10.0
}

  # plot outliers on P-A plot
## pdf(paste(path,"plots/outlier_per_amp.pdf",sep=""),height=8,width=8)
## par(mar=c(5,5,2,1))
## plot(1/feat.train$freq1_harmonics_freq_0, feat.train$freq1_harmonics_amplitude_0[],pch=19,col="#00000070",log='xy',ylim=c(.003,4),xlab="Period (days)", ylab="Amplitude (V mag)",cex.lab=1.5)
## out.size = (outlier.score[outlier.score >= out.thresh])/5 - 1.5
## # col.size = paste("#FF0000",ifelse(out.size >= 3, 99, round(out.size/2 * 100)),sep="")
## points(1/feat.asas$freq1_harmonics_freq_0[outlier.score >= out.thresh], feat.asas$freq1_harmonics_amplitude_0[outlier.score >= out.thresh],pch=17,col="#FF000070",cex=out.size)
## legend('topleft',c('Training Set','ASAS Outliers'),col=1:2,pch=c(19,17),cex=1.25)
## dev.off()
  
  ## plot(feat.train$color_diff_bj, feat.train$skew,pch=19,col="#00000030",xlab="Skew", ylab="Signif. of Period (# of sigma)")
  ## points(feat.asas$color_diff_bj[catalog.table$Anomaly >= out.thresh], feat.asas$skew[catalog.table$Anomaly >= out.thresh],pch=17,col="#FF000050")
  ## legend('topleft',c('Training Set','ASAS Outliers'),col=1:2,pch=c(19,17))





######################################################
######################################################


###########################
##########################
# Check probability calibration on AL training data
###########################
###########################
# set this to TRUE if you want to fit calibration parameters
# and produce reliability plots (else uses parameter ab.opt below)
checkcalib = FALSE
if(checkcalib){
  cat("Checking Classifier Calibration\n")
  source(paste(path,"R/check_calibration.R",sep="")) # run calibration routine
  pred.asas.prob.final = calibrate.sigmoid(pred.asas.prob.AL,ab.opt[1],ab.opt[2])
} else {
  ab.opt = c(-5.270766,  1.754329) # use hard-coded values found from calib. routine
  pred.asas.prob.final = calibrate.sigmoid(pred.asas.prob.AL,ab.opt[1],ab.opt[2])
}
pred.asas.final = pred.asas.AL



#####################################################
# CORRECT THE PERIODS OF THE ECLIPSING SOURCES
###########################
Periods = 1/feat.asas$freq1_harmonics_freq_0

# fit RF to set of confirmed eclipsing sources where we are correct and off by factor of 2
periodic = which(class.asas != "MISC")
half.ID = read.table(paste(path,"data/P_half_ACVS_followup.txt",sep=""),sep=",",header=TRUE)[,1]
same = which( (abs(acvs[periodic,2] - (Periods[periodic])) / acvs[periodic,2]) < .1)
ecl = which(substr(pred.asas.final,1,1) %in% c('w','x','y'))
same.ID = c(ID.asas[intersect(ecl,periodic[same])[1:150]],216273,216323)
feat.half = feat.asas[ID.asas %in% half.ID,]
feat.same = feat.asas[ID.asas %in% same.ID,]
correctP = factor(c(rep("n",length(half.ID)),rep("y",length(same.ID))))
rf.period = randomForest(rbind(feat.half,feat.same),correctP,ntree=500) # RF

ecl1 = which(substr(class.asas,1,1) %in% c('w','x','y'))
ecl2 = union(ecl,ecl1)
pred.corP = predict(rf.period,feat.asas[ecl2,])
Periods[ecl2] =((pred.corP=='n')+1)/feat.asas$freq1_harmonics_freq_0[ecl2] # correct periods

sum( (abs(acvs[ecl1,2] - (1/feat.asas$freq1_harmonics_freq_0[ecl1])) / acvs[ecl1,2]) < .1)
sum( (abs(acvs[ecl1,2] - Periods[ecl1]) / acvs[ecl1,2]) < .1)

same = sum(abs(( acvs[periodic,2] - (Periods[periodic])) / acvs[periodic,2]) < .1) / length(periodic)
# 0.7598, up from 0.5386
half = sum(abs(( acvs[periodic,2] - (2*Periods[periodic])) / acvs[periodic,2]) < .1) / length(periodic)
# 0.152, down from 0.380996
any = ( sum(abs(( acvs[periodic,2] - (Periods[periodic])) / acvs[periodic,2]) < .1) +
       sum(abs(( acvs[periodic,2] - (2*Periods[periodic])) / acvs[periodic,2]) < .1) +
       sum(abs(( acvs[periodic,2] - (.5*Periods[periodic])) / acvs[periodic,2]) < .1) )/ length(periodic)
# 0.9287142
cat("Period Agreement Rate: ",same,", ",half,", ",any,"\n")



######################################################
#####################################################
# WRITE OUT FINAL CATALOG
###########################
###########################

# get class names into easily readable format
class.names = unlist(lapply(lapply(levels(pred.asas.final),strsplit,split=". ",fixed=TRUE),function(x) paste(x[[1]][-1],collapse="")))
class.names = unlist(lapply(lapply(class.names,strsplit,split=",",fixed=TRUE),function(x) paste(x[[1]],collapse="")))
class.names = unlist(lapply(lapply(class.names,strsplit,split="/",fixed=TRUE),function(x) paste(x[[1]],collapse="")))
class.names = unlist(lapply(lapply(class.names,strsplit,split="-",fixed=TRUE),function(x) paste(x[[1]],collapse="")))
class.names = unlist(lapply(lapply(class.names,strsplit,split=".",fixed=TRUE),function(x) paste(x[[1]],collapse="")))
class.names = unlist(lapply(lapply(class.names,strsplit,split=" ",fixed=TRUE),function(x) paste(x[[1]],collapse="_")))

intrain.readable = unlist(lapply(lapply(paste(intrain),strsplit,split=". ",fixed=TRUE),function(x) paste(x[[1]][-1],collapse="")))
intrain.readable = unlist(lapply(lapply(intrain.readable,strsplit,split=",",fixed=TRUE),function(x) paste(x[[1]],collapse="")))
intrain.readable = unlist(lapply(lapply(intrain.readable,strsplit,split="/",fixed=TRUE),function(x) paste(x[[1]],collapse="")))
intrain.readable = unlist(lapply(lapply(intrain.readable,strsplit,split="-",fixed=TRUE),function(x) paste(x[[1]],collapse="")))
intrain.readable = unlist(lapply(lapply(intrain.readable,strsplit,split=".",fixed=TRUE),function(x) paste(x[[1]],collapse="")))
intrain.readable = unlist(lapply(lapply(intrain.readable,strsplit,split=" ",fixed=TRUE),function(x) paste(x[[1]],collapse="_")))


# save training set table
class.names.space = unlist(lapply(lapply(class.names,strsplit,split="_",fixed=TRUE),function(x) paste(x[[1]],collapse=" ")))
write.table(cbind(class.names.space,table(class.train),round(table(class.train)/length(class.train),4)),file=paste(path,"tables/training_set.dat",sep=""),quote=FALSE,row.names=FALSE,sep=" & ",eol="\\\\\n",col.names=FALSE)


# store RF output with readable class names
pred.asas.final1 = factor(class.names[apply(pred.asas.prob.final,1,which.max)])
pred.asas.prob.final1 = pred.asas.prob.final
colnames(pred.asas.prob.final1) = class.names

# add some other important features to the catalog:
catalog.table = cbind(acvs[,1],ID.asas,ra.dec.asas[,c(10,12)],paste(pred.asas.final1),apply(pred.asas.prob.final,1,max),outlier.score,acvs[,6],intrain.readable,pred.asas.prob.final,Periods,feat.asas$freq_signif,n.epochs.asas,acvs[,4],feat.asas$amplitude)
colnames(catalog.table) = c("ASAS_ID","dotAstro_ID","RA","DEC","Class","P_Class","Anomaly","ACVS_Class","Train_Class",class.names,"P","P_signif","N_epochs","V","deltaV")

#### set this to TRUE if you want to write catalog
write.catalog = TRUE

if(write.catalog){
  cat("Writing out Catalog\n")
  save(pred.asas.final,pred.asas.prob.final,file=paste(path,"data/asas_pred_final_v2_3.Rdat",sep=""))

  write.table(catalog.table,file=paste(path,"catalog/asas_class_catalog_v2_3.dat",sep=""),sep=',',quote=FALSE,row.names=FALSE)

  ### write out latex table to be included in paper
  N.table = 40
  catalog.paper = cbind(catalog.table[1:N.table,1:5],round(catalog.table[1:N.table,6:7],3),catalog.table[1:N.table,8:9],round(catalog.table[1:N.table,10],3),rep(" ... ",N.table),round(catalog.table[1:N.table,37:42],3))
  write.table(catalog.paper,file=paste(path,"tables/asas_catalog.dat",sep=""),quote=FALSE,row.names=FALSE,sep=" & ",eol="\\\\\n")


#### plot correspondence between us & ACVS
  pdf(paste(path,"plots/catalog_rf_acvs.pdf",sep=""),height=8,width=12)
  par(mar=c(3,9,9.5,2.75))
  asas.tab = table(pred.asas.final,class.asas)
  asas.tab = asas.tab[,c(1:8,10:13,9)]
  plot.table(asas.tab,title="",cexprob=0.95,cexaxis=1.35)
  abline(h=1/24,lwd=4,col=4)
  mtext("ACVS Class",2,padj=-6.05,cex=2)
  mtext("MACC Class",3,padj=-6.3,cex=2)
  dev.off()

  ### correspondence for confident sources
  pdf(paste(path,"plots/catalog_rf_acvs_conf.pdf",sep=""),height=8,width=12)
  par(mar=c(3,9,9.5,2.75))
  conf = which(outlier.score < 3)
  asas.tab = table(pred.asas.final[conf],class.asas[conf])
  asas.tab = asas.tab[,c(1:8,10:13,9)]
  plot.table(asas.tab,title="",cexprob=0.95,cexaxis=1.35)
  abline(h=1/24,lwd=4,col=4)
  mtext("ACVS Class",2,padj=-6.05,cex=2)
  dev.off()

cat("ACVS agreement rate:",sum(paste(pred.asas.final)==paste(class.asas))/sum(class.asas!="MISC"),"\n")
#ACVS agreement rate: 0.8052965

cat("ACVS agreement rate for confident sources:",sum(paste(pred.asas.final[conf])==paste(class.asas[conf]))/sum(class.asas[conf]!="MISC"),"\n")
# ACVS agreement rate for confident sources: 0.9162604 
## length(conf)
## [1] 25158
}

###########################################################################
###########################
###########################
# Compare with other papers
###########################
# set this to TRUE if you want to generate comparison tables
docompare = FALSE
if(docompare){
  cat("Comparing classifications to other ASAS papers\n")
  source(paste(path,"R/compare_asas_papers.R",sep=""))
}



####################################################
# plot period-period relationship ACVS vs this work
####################################################
plotper = FALSE # set to TRUE if you want to generate period plot
if(plotper){
  pdf(paste(path,"plots/period_acvs_us.pdf",sep=""),height=7,width=7)
  par(mar=c(5,5,2,1),mfrow=c(1,1))
 # plot(acvs[,2],Periods,log='xy',col="#00000007",pch=20,xlim=c(.03,3000),ylim=c(.03,3000),xlab="Period (ACVS)",ylab="Period (this work)",cex.lab=1.5,cex.axis=1)
 # abline(0,1,col=2,lty=3,lwd=2)
 # legend('bottomright',"All Sources",cex=1.5,bty="n",text.col=4)
  periodic = which(class.asas != "MISC")
#periodic = which(substr(acvs[,6],1,4)!="MISC")
  plot(acvs[periodic,2],Periods[periodic],log='xy',col="#00000010",pch=20,xlim=c(.03,1000),ylim=c(.03,1000),xlab="Period (ACVS)",ylab="Period (this work)",cex.lab=1.5,cex.axis=1,cex=1.25)
  abline(0,1,col=2,lty=1,lwd=1)
  legend('bottomright',"ACVS Periodic Sources",cex=2,bty="n",text.col=4)
  legend('topleft',paste("Agreement Rate: ",round(same,3)*100,"%",sep=""),cex=2,bty="n",text.col=2)
  dev.off()

  ## half = which( (abs(acvs[periodic,2] - (2/feat.asas$freq1_harmonics_freq_0[periodic])) / acvs[periodic,2]) < .1)
  ## half.tab = cbind(catalog.table[periodic[half[1:150]],c(2,5:6,42)], acvs[periodic[half[1:150]],2])
  ## colnames(half.tab)[5] = "P_ACVS"
  ## write.table(half.tab, "tables/P_half_ACVS_followup.dat", row.names=FALSE,sep=",",quote=FALSE)
  
}
