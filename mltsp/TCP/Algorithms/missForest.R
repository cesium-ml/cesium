##
## MissForest - nonparametric missing value imputation for mixed-type data
##
## This R script contains the necessary functions for performing imputation
## using the missForest algorithm in the statistical software R.
##
## An R package 'missForest' will be made available as soon as possible. 
##
## Author: D.Stekhoven, stekhoven@stat.math.ethz.ch
##############################################################################


missForest <- function(xmis, maxiter = 10,
                       decreasing = FALSE,
                       verbose = FALSE,
                       mtry = floor(sqrt(ncol(xmis))),
                       ntree = 100, xtrue = NA)
{ ## ----------------------------------------------------------------------
  ## Arguments:
  ## xmis       = data matrix with missing values
  ## maxiter    = stop after how many iterations (default = 10)
  ## decreasing = (boolean) if TRUE the columns are sorted with decreasing
  ##              amount of missing values
  ## verbose    = (boolean) if TRUE then missForest returns error estimates,
  ##              runtime and if available true error during iterations
  ## mtry       = how many variables should be tried randomly at each node
  ## ntree      = how many trees are grown in the forest
  ## xtrue      = complete data matrix
  ##
  ## ----------------------------------------------------------------------
  ## Author: Daniel Stekhoven, stekhoven@stat.math.ethz.ch

  n <- nrow(xmis)
  p <- ncol(xmis)
  
  ## perform initial guess on xmis
  ximp <- xmis
  xAttrib <- lapply(xmis, attributes)
  varType <- character(p)
  for (t.co in 1:p){
    if (is.null(xAttrib[[t.co]])){
      varType[t.co] <- 'numeric'
      ximp[is.na(xmis[,t.co]),t.co] <- mean(xmis[,t.co], na.rm = TRUE)
    } else {
      varType[t.co] <- xAttrib[[t.co]]$class
      ## take the level which is more 'likely' (majority vote)
      max.level <- max(table(ximp[,t.co]))
      ## if there are several classes which are major, sample one at random
      class.assign <- sample(names(which(max.level == summary(ximp[,t.co]))), 1)
      ## it shouldn't be the NA class
      if (class.assign != "NA's"){
        ximp[is.na(xmis[,t.co]),t.co] <- class.assign
      } else {
        while (class.assign == "NA's"){
          class.assign <- sample(names(which(max.level ==
                                             summary(ximp[,t.co]))), 1)
        }
        ximp[is.na(xmis[,t.co]),t.co] <- class.assign
      }
    }
  }
  
  ## extract missingness pattern
  NAloc <- is.na(xmis)            # where are missings
  noNAvar <- apply(NAloc, 2, sum) # how many are missing in the vars
  sort.j <- order(noNAvar) # indices of increasing amount of NA in vars
  if (decreasing)
    sort.j <- rev(sort.j)
  sort.noNAvar <- noNAvar[sort.j]
   
  ## output
  Ximp <- vector('list', maxiter)
  
  ## initialize parameters of interest
  iter <- 0
  k <- length(unique(varType))
  convNew <- rep(0, k)
  convOld <- rep(Inf, k)
  OOBerror <- numeric(p)
  names(OOBerror) <- varType

  ## setup convergence variables w.r.t. variable types
  if (k == 1){
    if (unique(varType) == 'numeric'){
      names(convNew) <- c('numeric')
    } else {
      names(convNew) <- c('factor')
    }
    convergence <- c()
    OOBerr <- numeric(1)
  } else {
    names(convNew) <- c('numeric', 'factor')
    convergence <- matrix(NA, ncol = 2)
    OOBerr <- numeric(2)
  }

  ## function to yield the stopping criterion in the following 'while' loop
  stopCriterion <- function(varType, convNew, convOld, iter, maxiter){
    k <- length(unique(varType))
    if (k == 1){
        (convNew < convOld) & (iter < maxiter)
    } else {
      ((convNew[1] < convOld[1]) | (convNew[2] < convOld[2])) & (iter < maxiter)
    }
  }

  ## iterate missForest
  while (stopCriterion(varType, convNew, convOld, iter, maxiter)){
    if (iter != 0){
      convOld <- convNew
      OOBerrOld <- OOBerr
    }
    cat("  missForest iteration", iter+1, "in progress...")
    t.start <- proc.time()
    ximp.old <- ximp
    for (s in 1:p){
      varInd <- sort.j[s]
      if (noNAvar[[varInd]] != 0){
        obsi <- !NAloc[,varInd] # which i's are observed
        misi <- NAloc[,varInd] # which i's are missing
        obsY <- ximp[obsi, varInd] # training response
        obsX <- ximp[obsi, seq(1, p)[-varInd]] # training variables
        misX <- ximp[misi, seq(1, p)[-varInd]] # prediction variables
        typeY <- varType[varInd]
        if (typeY == 'numeric'){
          ## train random forest on observed data
          RF <- randomForest(x = obsX, y = obsY, ntree = ntree)
          ## record out-of-bag error
          OOBerror[varInd] <- RF$mse[ntree]
          ## predict missing values in column varInd
          misY <- predict(RF, misX)
        } else { # if Y is categorical          
          obsY <- factor(obsY) ## remove empty classes
          summarY <- summary(obsY)
          if (length(summarY) == 1){ ## if there is only one level left
            misY <- factor(rep(names(summarY), sum(misi)))
          } else {
            ## train random forest on observed data
            RF <- randomForest(x = obsX, y = obsY, ntree = ntree)
            ## record out-of-bag error
            OOBerror[varInd] <- RF$err.rate[[ntree,1]]
            ## predict missing values in column varInd
            misY <- predict(RF, misX)
          }
        }
        
        ## replace old imputed value with prediction
        ximp[misi, varInd] <- misY
      }
    }
    cat('done!\n')

    iter <- iter+1
    Ximp[[iter]] <- ximp
    
    t.co2 <- 1
    ## check the difference between iteration steps
    for (t.type in names(convNew)){
      t.ind <- which(varType == t.type)
      if (t.type == "numeric"){
        convNew[t.co2] <- sum((ximp[,t.ind]-ximp.old[,t.ind])^2)/sum(ximp[,t.ind]^2)
      } else {
        dist <- sum(as.character(as.matrix(ximp[,t.ind])) != as.character(as.matrix(ximp.old[,t.ind])))
        convNew[t.co2] <- dist / (n * sum(varType == 'factor'))
      }
      t.co2 <- t.co2 + 1
    }

    ## compute estimated imputation error
    NRMSE <- sqrt(mean(OOBerror[varType=='numeric'])/var(as.vector(as.matrix(xmis[,varType=='numeric'])), na.rm = TRUE))
    PFC <- mean(OOBerror[varType=='factor'])
    if (k==1){
      if (unique(varType)=='numeric'){
        OOBerr <- NRMSE
        names(OOBerr) <- 'NRMSE'
      } else {
        OOBerr <- PFC
        names(OOBerr) <- 'PFC'
      }
    } else {
      OOBerr <- c(NRMSE, PFC)
      names(OOBerr) <- c('NRMSE', 'PFC')
    }

    ## return status output, if desired
    if (verbose){
      delta.start <- proc.time() - t.start
      if (any(!is.na(xtrue))){
        err <- mixError(ximp, xmis, xtrue)
        cat("    error(s):", err, "\n")
      }
      cat("    estimated error(s):", OOBerr, "\n")
      cat("    convergence:", convNew, "\n")
      cat("    time:", delta.start[3], "seconds\n\n")
    }
  }#end while((convNew<convOld)&(iter<maxiter)){

  ## produce output w.r.t. stopping rule
  if (iter == maxiter){
    out <- list(Ximp = Ximp[[iter]], error = OOBerr)
  } else {
    out <- list(Ximp = Ximp[[iter-1]], error = OOBerrOld)
  }
  return(out)
}


varClass <- function(x){
  xAttrib <- lapply(x, attributes)
  p <- ncol(x)
  x.types <- character(p)
  for (t.co in 1:p){
    if (is.null(xAttrib[[t.co]])){
      x.types[t.co] <- 'numeric'
    } else {
      x.types[t.co] <- xAttrib[[t.co]]$class
    }
  }
  return(x.types)
}


mixError <- function(ximp, xmis, xtrue)
{
  ## Purpose:
  ## Calculates the difference between to matrices. For all numeric
  ## variables the NRMSE is used and for all categorical variables
  ## the relative number of false entries is returned.
  ## ----------------------------------------------------------------------
  ## Arguments:
  ## ximp      = (imputed) matrix
  ## xmis      = matrix with missing values
  ## xtrue     = true matrix (or any matrix to be compared with ximp)
  ## ----------------------------------------------------------------------
  ## Author: Daniel Stekhoven, Date: 26 Jul 2010, 10:10

  x.types <- varClass(ximp)
  n <- nrow(ximp)
  k <- length(unique(x.types))
  err <- rep(Inf, k)
  t.co <- 1
  if (k == 1){
    if (unique(x.types) == 'numeric'){
      names(err) <- c('numeric')
    } else {
      names(err) <- c('factor')
      t.co <- 1
    }
  } else {
    names(err) <- c('numeric', 'factor')
    t.co <- 2
  }
  for (t.type in names(err)){
    t.ind <- which(x.types == t.type)
    if (t.type == "numeric"){
      err[1] <- nrmse(ximp[,t.ind], xmis[,t.ind], xtrue[,t.ind])
    } else {
      dist <- sum(as.character(as.matrix(ximp[,t.ind])) != as.character(as.matrix(xtrue[,t.ind])))
      no.na <- sum(is.na(xmis[,x.types == 'factor']))
      if (no.na == 0){
        err[t.co] <- 0
      } else {
        err[t.co] <- dist / no.na
      }
    }
  }
  return(err)
}


nrmse <- function(ximp, xmis, xtrue){
  mis <- is.na(xmis)
  sqrt(mean((ximp[mis]-xtrue[mis])^{2})/var(xtrue[mis]))
}


prodNA <- function(x, noNA = 0.1){
  n <- nrow(x)
  p <- ncol(x)
  NAloc <- rep(FALSE, n*p)
  NAloc[sample(n*p, floor(n*p*noNA))] <- TRUE
  x[matrix(NAloc, nrow = n, ncol = p)] <- NA
  return(x)
}
