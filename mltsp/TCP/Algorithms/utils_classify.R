
# plots confusion matrix as a heat map
plot.confusion = function(confmat,title="Confusion Matrix",cexprob=0.5,cexaxis=1){
  n = dim(confmat)[1]
  err.rate = round(1-sum(diag(confmat))/sum(confmat),4)
  # flip confusion matrix for plotting
  confmat = confmat[,n:1]
  confmat.prob = confmat/rowSums(confmat)
  
  par(mar=c(5,7,5,.5))
  image(matrix(sqrt(confmat.prob),nrow=n,ncol=n),xlab=paste("True Class, Error Rate:",err.rate),xaxt="n",yaxt="n",main=title,cex.lab= 1.5,col=heat.colors(128))
  axis(2,labels=row.names(confmat),at=seq(1,0,length.out=n),las=2,cex.axis= 0.7*cexaxis)
  axis(3,labels=substr(colnames(confmat),1,1),at=seq(1,0,length.out=n),las=1,cex.axis= 0.7*cexaxis,padj=2/cexaxis,tick=FALSE)  
  axis(1,labels=paste(rowSums(confmat)),at=seq(0,1,length.out=n),las=1,cex.axis=.5*cexaxis,tick=F,padj=-4/cexaxis)
  abline(v=seq(-1./((n-1)*2),1-1./((n-1)*2),length.out= n))
  abline(h=seq(-1./((n-1)*2),1-1./((n-1)*2),length.out= n))
  for(ii in 1:n){
    for(jj in 1:n){
      if(confmat.prob[ii,jj]>0.005){
        if(confmat.prob[ii,jj]>=0.1){
          text((ii-1)*(1/(n-1)),(jj-1)*(1/(n-1)),round(confmat.prob[ii,jj],2),cex=cexprob,col='blue')
        }
        else {
          text((ii-1)*(1/(n-1)),(jj-1)*(1/(n-1)),round(confmat.prob[ii,jj],2),cex=cexprob,col='white')         
        }
      }
    }
  }
}

# set up Debossher classes as factor vector (to compare w/ their work)
class.debos = function(class){
  class.new = paste(class)
  class.new[class=="Mira" | class=="MIRA"] = "a. Mira"
  class.new[class=="Semiregular Pulsating Variable" | class=="SR"] = "b. Semireg PV"
  class.new[class=="RV Tauri" | class=="RVTAU"] = "c. RV Tauri"
  class.new[class=="Classical Cepheid" | class=="CLCEP"] = "d. Classical Cepheid"
  class.new[class=="Population II Cepheid" | class=="PTCEP"] = "e. Pop. II Cepheid"
  class.new[class=="Multiple Mode Cepheid" | class=="DMCEP"] = "f. Multi. Mode Cepheid"
  class.new[class=="RR Lyrae, Fundamental Mode" | class=="RRAB"] = "g. RR Lyrae, FM"
  class.new[class=="RR Lyrae, First Overtone" | class=="RRC"] = "h. RR Lyrae, FO"
  class.new[class=="RR Lyrae, Double Mode" | class=="RRD"] = "i. RR Lyrae, DM"
  class.new[class=="Delta Scuti" | class=="DSCUT"] = "j. Delta Scuti"
  class.new[class=="Lambda Bootis Variable" | class=="LBOO"] = "k. Lambda Bootis"
  class.new[class=="Beta Cephei" | class=="BCEP"] = "l. Beta Cephei"
  class.new[class=="Slowly Pulsating B-stars" | class=="SPB"] = "m. Slowly Puls. B"
  class.new[class=="Gamma Doradus" | class=="GDOR"] = "n. Gamma Doradus"
  class.new[class=="Be Star"] = "o. Pulsating Be"
  class.new[class=="Periodically variable supergiants" | class=="PVSG"] = "p. Per. Var. SG"
  class.new[class=="Chemically Peculiar Stars" | class=="CP"] = "q. Chem. Peculiar"
  class.new[class=="Wolf-Rayet" | class=="WR"] = "r. Wolf-Rayet"
  class.new[class=="T Tauri"| class=="TTAU"] = "s. T Tauri"
  class.new[class=="Herbig AE/BE Star" | class=="HAEBE"] = "t. Herbig AE/BE"
  class.new[class=="S Doradus" | class=="LBV"] = "u. S Doradus"
  class.new[class=="Ellipsoidal" | class=="ELL"] = "v. Ellipsoidal"
  class.new[class=="Beta Persei" | class=="EA"] = "w. Beta Persei"
  class.new[class=="Beta Lyrae" | class=="EB"] = "x. Beta Lyrae"
  class.new[class=="W Ursae Majoris" | class=="EW"] = "y. W Ursae Maj."
  class.new[class=="Algol (Beta Persei)" | class=="EA"] = "w. Beta Persei"

  class.new = factor(class.new)
#  levels(class.new) = sort(c(levels(class.new),"o. BE Star"))
  return(class.new)
}

# straighten out doubly-labeled data
class.double = function(class,ID){
  class[ID==148137] = "u. S Doradus"
  class[ID==148583] = "u. S Doradus"
  class[ID==148614] = "u. S Doradus"
  class[ID==148615] = "u. S Doradus"
  class[ID==148038] = "u. S Doradus"
  class[ID==148174] = "t. Herbig AE/BE"
  class[ID==148375] = "t. Herbig AE/BE"
  return(factor(class))
}

# loads in OGLE + HIPPARCOS data
load.data = function(path){
  
### HIPPARCOS
  hip.ID = read.table(paste(path,"hipparcos_hipIDs.dat",sep=""))[,1]
  hip.classes = read.table(paste(path,"hipparcos_classes.dat",sep=""))[[1]]
  throwout = c("25473","26304","33165","34042","36750","39009","53461","57812","58907","75377","104029")
#old:   "25473", "34042","36750","39009","57812","58907","104029")
  hip.out = which(hip.classes=="ROAP" | hip.classes=="XB" | hip.classes=="SXPHE" | hip.ID %in% throwout)

  hip.classes = hip.classes[-hip.out]
  hip.ID = hip.ID[-hip.out]
  hip.features = read.table(paste(path,"hipparcos_features.dat",sep=""),header=TRUE)[-hip.out,]
#  sortfeat = sort(names(hip.features),index.return=TRUE)
#  hip.features = hip.features[,sortfeat$ix]
# fix doubly-labeled sources
  hip.classes[hip.ID=="5267"] = "LBV"
  hip.classes[hip.ID=="23428"] = "LBV"
  hip.classes[hip.ID=="26403"] = "HAEBE"
  hip.classes[hip.ID=="54413"] = "HAEBE"
  hip.classes[hip.ID=="86624"] = "LBV"   
  hip.classes[hip.ID=="89956"] = "LBV"   
  hip.classes[hip.ID=="89963"] = "LBV"   
  ## new double-labels:
  hip.classes[hip.ID=="27400"] = "DSCUT"
  hip.classes[hip.ID=="30326"] = "MIRA"
  hip.classes[hip.ID=="54283"] = "WR"
  hip.classes[hip.ID=="84757"] = "WR"
  hip.classes[hip.ID=="88856"] = "WR"
  hip.classes[hip.ID=="99252"] = "DSCUT"
  hip.classes[hip.ID=="109306"] = "LBOO"
  hip.classes = class.debos(hip.classes)

## OGLE
  ID = read.table(paste(path,"R/IDs.dat",sep=""))[,1]
  features = read.table(paste(path,"R/features.dat",sep=""),header=T)
  features = as.data.frame(features[,-which(substr(names(features),1,4)=="sdss" | substr(names(features),1,3)=="ws_")]) # take out sdss & ws features
  classes = (read.table(paste(path,"R/class.dat",sep=""),sep="\n"))[[1]]
  ogle = which(classes=="W Ursae Majoris" | classes=="RR Lyrae, Double Mode" | classes == "Multiple Mode Cepheid" | classes == "Beta Lyrae" | classes == "Beta Persei")
  ogl.features = features[ogle,]
  ogl.classes = class.debos(classes[ogle])
  ogl.ID = ID[ogle]

  hip1.features=NULL
  for(ii in 1:length(names(ogl.features))){
    ind = which(names(hip.features)==names(ogl.features)[ii])
    hip1.features = cbind(hip1.features,hip.features[,ind])
    }
  colnames(hip1.features) = colnames(ogl.features)
  hip.features = as.data.frame(hip1.features)
  
 # hip.features = hip.features[,which(names(hip.features) %in% names(ogl.features))]
  
  classes = factor(c(paste(hip.classes),paste(ogl.classes)))
  features = rbind(hip.features,ogl.features)
  names(features)[54:55]= c("QSO","non_QSO")
  ID = c(hip.ID,ogl.ID)
  return(list(features=features,classes=classes,ID=ID))
}

## fixes a confusion matrix w/ too few classes
fixconfmat = function(confmat,pred.names,y.names){
  p = dim(confmat)[2]
  
  # find which class names are missing
  var.LO = setdiff(y.names,pred.names)
  var.LOind = sort(which(y.names%in%var.LO))
  len.LO = length(var.LO)
  if(len.LO>0){
    cm.tmp = confmat[1:(var.LOind[1]-1),]
    for(ii in 1:len.LO){
      cm.tmp = rbind(cm.tmp,rep(0,p))

      nadd = ifelse(is.na(var.LOind[ii+1]),p-var.LOind[ii],var.LOind[ii+1]-var.LOind[ii]-1)
      if(nadd>0){
        cm.tmp = rbind(cm.tmp,confmat[(var.LOind[ii]-ii+1):(var.LOind[ii]-ii+nadd),])
      }
    }
    confmat = cm.tmp
    row.names(confmat) = y.names
  }
  confmat = t(confmat)
  return(confmat)
}
  
# plots feature importance matrix (from pairwise CART)
plot.featImp = function(mat,sortLS = TRUE){
  n = dim(mat)
  # put LS features first
  featNames = row.names(mat)
  if(sortLS){
    feat.LS = which(substr(featNames,1,4)=="freq")
    mat = rbind(mat[feat.LS,],mat[-feat.LS,])
    featNames = c(featNames[feat.LS],featNames[-feat.LS])
  }
  # plot
  par(mar=c(11,7,.3,.5))
  image(mat[,n[2]:1],xlab="",xaxt="n",yaxt="n",cex.lab= 1,col=heat.colors(64))
  axis(2,labels=colnames(mat),at=seq(1,0,length.out=n[2]),las=2,cex.axis= 0.7)
  axis(1,labels=row.names(mat),at=seq(0,1,length.out=n[1]),las=2,cex.axis= 0.75,padj=0.5,tick=TRUE)
  if(sortLS){
    abline(v=(length(feat.LS)-.5)/(n[1]-1),lwd=3,col='darkblue') }
 # abline(v=(length(feat.LS)-.5)/(n[1]-1),lwd=2,col=4)
 # axis(1,labels=paste(rowSums(mat)),at=seq(0,1,length.out=n[2]),las=1,cex.axis=.5,tick=F,padj=-4)
#  abline(v=seq(-1./((n[1]-1)*2),1-1./((n-1)*2),length.out= n[1]))
#  abline(h=seq(-1./((n[2]-1)*2),1-1./((n-1)*2),length.out= n[2]))
}

########
### create class hierarchy from varstar classes
class.hier = function(class){
  hier = c('1 pv','.1 giant','a','b','c','.2 cepheid','d','e','f','.3 rrl','g','h','i','.4 other','j','k','l','m','n','o','2 ev','p','q','r','s','t','u','3 msv','v','w','x','y')
  depth = c(1,2,rep(3,3),2,rep(3,3),2,rep(3,3),2,rep(3,6),1,rep(2,6),1,rep(2,4))
  node = which(substr(hier,1,1)==hier)
  intern = which(substr(hier,1,1)!=hier)
  top = which(depth==1)
  class = factor(substr(paste(class),1,1))
  class.boo = matrix(0,length(class),length(hier))
  class.boo[cbind(1:length(class),node[as.numeric(class)])] = 1
  for(ii in 1:length(class)){
    class.boo[ii,max(intern[intern < node[as.numeric(class)[ii]]])] = 1
    class.boo[ii,max(top[top < node[as.numeric(class)[ii]]])] = 1
  }
  colnames(class.boo) = hier
  return(list(class=class.boo,depth=depth))
}




# construct cost matrix for classifier
costMat = function(val=2){
  p = 25
  cost = matrix(0,p,p)
  tax1 = c(rep("pv",15),rep("ev",6),rep("msv",4))
  tax2 = c(rep("giant",3),rep("ceph",3),rep("rrl",3),"ds","lb","bc","spb","gd","be","pvsg","cp","wr","tt","haebe","sd","ell","bp","bl","wum")
  
  
  for(ii in 1:(p-1)){
    for(jj in (ii+1):p){
      if(tax1[ii]==tax1[jj]){
        if(tax2[ii]==tax2[jj]){
          cost[ii,jj] = cost[jj,ii] = .5
        } else {
          cost[ii,jj] = cost[jj,ii] = 1
        }
      }
      else {
        cost[ii,jj] = cost[jj,ii] = val
      }
    }
  }
  return(cost)
}

# compute class weights using rescaling approach to cost matrix
costWeights = function(y,cost=costMat(2)){
  n = table(y)
  eps = rowSums(cost)
  w = (sum(n)*eps)/sum(n*eps)
  return(w)
}

# take ratios of frequencies & amplitudes
featureConvert = function(features){
  
  freq1 = features[,"freq1_harmonics_freq_0"]
  features[,"freq2_harmonics_freq_0"] = features[,"freq2_harmonics_freq_0"]/freq1
  features[,"freq3_harmonics_freq_0"] = features[,"freq3_harmonics_freq_0"]/freq1

  amp1 = features[,"freq1_harmonics_amplitude_0"]
  features[,"freq1_harmonics_amplitude_1"] = features[,"freq1_harmonics_amplitude_1"]/amp1
  features[,"freq1_harmonics_amplitude_2"] = features[,"freq1_harmonics_amplitude_2"]/amp1
  features[,"freq1_harmonics_amplitude_3"] = features[,"freq1_harmonics_amplitude_3"]/amp1
  features[,"freq2_harmonics_amplitude_0"] = features[,"freq2_harmonics_amplitude_0"]/amp1
  features[,"freq2_harmonics_amplitude_1"] = features[,"freq2_harmonics_amplitude_1"]/amp1
  features[,"freq2_harmonics_amplitude_2"] = features[,"freq2_harmonics_amplitude_2"]/amp1
  features[,"freq2_harmonics_amplitude_3"] = features[,"freq2_harmonics_amplitude_3"]/amp1
  features[,"freq3_harmonics_amplitude_0"] = features[,"freq3_harmonics_amplitude_0"]/amp1
  features[,"freq3_harmonics_amplitude_1"] = features[,"freq3_harmonics_amplitude_1"]/amp1
  features[,"freq3_harmonics_amplitude_2"] = features[,"freq3_harmonics_amplitude_2"]/amp1
  features[,"freq3_harmonics_amplitude_3"] = features[,"freq3_harmonics_amplitude_3"]/amp1

  return(features)
}


# plot prob(correct) for each source, by class
probPlot = function(probMat,pred,classes,thresh = NULL){

  n = length(classes)
  y.names = levels(classes)
  p = length(y.names)
  probCor = probMat[cbind(1:n,as.numeric(classes))]

#  if(is.null(thresh)) { thresh = rep(1/p,p)}
  
  par(mar=c(8.75,4,.5,.5))
  # correct class vs. not
  col.cor = ifelse(pred==classes,"#00800070",'red')
  pch.cor = ifelse(pred==classes,19,4)
  # second place
  sortProb = apply(probMat,1,sort,decreasing=TRUE)
  first = which(probCor==sortProb[1,])
  second = which(probCor==sortProb[2,])
  col.cor[second] = "#00008B70"
  pch.cor[second] = 17
  lwd.cor = rep(1.5,n)
  lwd.cor[c(first,second)] = 0
  
  plot(as.numeric(classes)+runif(n,-.2,.2),probCor,xaxt='n',xlab="",ylab="Pr(Correct Class)",col=col.cor,pch=pch.cor,xlim = c(-.5,p),ylim=c(-.15,1),lwd=lwd.cor)
  abline(v=0:length(y.names)+.5)
  abline(h=c(0,1),lty=2)
  axis(1,labels=y.names,at=1:length(y.names),las=2,cex.axis=.9,padj=0.5,tick=TRUE)
  
  first.class = tabulate(classes[first])/tabulate(classes)
  if(length(tabulate(classes[first])) < length(tabulate(classes))){
    first.class[(length(tabulate(classes[first]))+1) : p] = 0 }
  second.class = tabulate(classes[second])/tabulate(classes)
  if(length(tabulate(classes[second])) < length(tabulate(classes))){
    second.class[(length(tabulate(classes[second]))+1) : p] = 0 }
  none.class = rep(1,p) - first.class - second.class
  for(jj in 1:p){
    text(jj,-.05,round(first.class[jj]*100,1),cex=.8,col='darkgreen')
    text(jj,-.1,round(second.class[jj]*100,1),cex=.8,col='darkblue')
    text(jj,-.15,round(none.class[jj]*100,1),cex=.8,col='red')
  }
  text(0.5,-.05,"Top (%)",pos=2)
  text(0.5,-.1,"2nd (%)",pos=2)
  text(0.5,-.15,"X (%)",pos=2)
}

# plot prob(class) for each source / class
probPlot1 = function(probMat,pred,classes){

  n = length(classes)
  y.names = levels(classes)
  m = length(y.names)
  par(mar=c(8.75,4,.5,.5))
  plot(rep(1,n)+runif(n,-.2,.2),probMat[,1],xlim=c(1,m),xaxt='n',xlab="",ylab="Pr(Class)",col=ifelse(classes==y.names[1],'blue','grey'),pch=ifelse(classes==y.names[1],20,3),cex=.7,ylim=c(0,1))
  for(ii in 2:length(y.names)){
    points(rep(ii,n)+runif(n,-.2,.2),probMat[,ii],col=ifelse(classes==y.names[ii],'blue','grey'),pch=ifelse(classes==y.names[ii],20,3),cex=.7)
  }
  abline(v=0:length(y.names)+.5)
  abline(h=c(0,1),lty=2)
  axis(1,labels=y.names,at=1:length(y.names),las=2,cex.axis=.9,padj=0.5,tick=TRUE)
  
}
