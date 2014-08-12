	program rf5new
c
c	Copyright 2002-2003  Leo Breiman and Adele Cutler
c
c	This is free open source software but its use,in part or 
c	in whole,in any commercial product that is sold for profit 
c	is prohibited without the written consent of Leo Breiman 
c	and Adele Cutler.
c
c	We very much appreciate bug notices and suggested improvements.
c
c	leo@stat.berkeley.edu   adele@math.usu.edu
c
c	SET ALL PARAMETERS FIRST GROUP BELOW.  GENERALLY,
c	SETTING PARAMETERS TO ZERO TURNS THE CORRESPONDING
c	OPTION OFF. 
c
c	ALL RELEVANT OUTPUT FILES MUST BE GIVEN NAMES--SEE BELOW.
c
	integer mdim,ntrain,nclass,maxcat,ntest,
     &	labelts,labeltr,mtry0,ndsize,jbt,look,lookcls,
     &	jclasswt,mdim2nd,mselect,imp,interact,impn,
     &	nprox,nrnn,noutlier,nscale,nprot,missfill,iviz,
     &	isaverf,isavepar,isavefill,isaveprox,
     &  irunrf,ireadpar,ireadfill,ireadprox
	real code
c
c	-------------------------------------------------------
c	CONTROL PARAMETERS
c
	parameter(
c  		DESCRIBE DATA		
     1		mdim=9,ntrain=214,nclass=6,maxcat=1,
     1		ntest=0,labelts=0,labeltr=1,
c
c		SET RUN PARAMETERS
     2		mtry0=2,ndsize=1,jbt=500,look=100,lookcls=1,
     2		jclasswt=0,mdim2nd=0,mselect=0,
c
c		SET IMPORTANCE OPTIONS	
     3		imp=1,interact=0,impn=1,
c
c		SET PROXIMITY COMPUTATIONS
     4		nprox=1,nrnn=ntrain,
c
c		SET OPTIONS BASED ON PROXIMITIES
     5		noutlier=0,nscale=0,nprot=0,
c
c		REPLACE MISSING VALUES  
     6		code=-999,missfill=0,
c
c		GRAPHICS
     7		iviz=0,
c
c		SAVING A FOREST
     8		isaverf=0,isavepar=0,isavefill=0,isaveprox=0,
c
c		RUNNING A SAVED FOREST
     9		irunrf=0,ireadpar=0,ireadfill=0,ireadprox=0)
c
c	-------------------------------------------------------
c	OUTPUT CONTROLS	
c
	integer isumout,idataout,impfastout,impout,impnout,interout,
     &  iprotout,iproxout,iscaleout,ioutlierout
	parameter(
     &		isumout	= 	1,!0/1		1=summary to screen
     &		idataout=	0,!0/1/2	1=train,2=adds test(7)
     &		impfastout=	0,!0/1		1=gini fastimp	(8)
     &		impout=		0,!0/1/2 	1=imp,2=to screen(9)
     &		impnout=	0,!0/1		1=impn		(10)
     &		interout=	0,!0/1/2	1=interaction,2=screen(11)
     &		iprotout=	1,!0/1/2	1=prototypes,2=screen(12)
     &		iproxout=	1,!0/1/2	1=prox,2=adds test(13)
     &		iscaleout=	0,!0/1		1=scaling coors	(14)
     &		ioutlierout=	1) !0/1/2	1=train,2=adds test (15)
c
c	-------------------------------------------------------
c	DERIVED PARAMETERS (DO NOT CHANGE)
c
	integer nsample,nrnodes,mimp,near,
     &	ifprot,ifscale,iftest,mdim0,ntest0,nprot0,nscale0
	parameter(
     &  nsample=(2-labeltr)*ntrain,
     &  nrnodes=2*nsample+1,
     &  mimp=imp*(mdim-1)+1,
     &  ifprot=nprot/(nprot-.1),
     &  ifscale=nscale/(nscale-.1),
     &  iftest=ntest/(ntest-.1),
     &  nprot0=(1-ifprot)+nprot,
     &  nscale0=(1-ifscale)+nscale,
     &  ntest0=(1-iftest)+ntest,
     &  mdim0=interact*(mdim-1)+1,
     &  near=nprox*(nsample-1)+1)
C
c	-------------------------------------------------------
c	DIMENSIONING OF ARRAYS
c
	real x(mdim,nsample),xts(mdim,ntest0),v5(mdim),v95(mdim),
     &	tgini(mdim),zt(mdim),avgini(mdim),
     &	votes(mdim0,jbt),effect(mdim0,mdim0),teffect(mdim0,mdim0),
     &	hist(0:mdim0,mdim0),g(mdim0),fill(mdim),rinpop(near,jbt),
     &	dgini(nrnodes),xbestsplit(nrnodes),tnodewt(nrnodes),
     &	tw(nrnodes),tn(nrnodes),v(nsample),win(nsample),temp(nrnn),
     7	q(nclass,nsample),devout(nclass),classwt(nclass),wr(nclass),
     &	tmissts(nclass),tmiss(nclass),tclasspop(nclass),wl(nclass),
     &	rmedout(nclass),tclasscat(nclass,maxcat),qts(nclass,ntest0),
     &	classpop(nclass,nrnodes),signif(mimp),zscore(mimp),sqsd(mimp),
     &	avimp(mimp),qimp(nsample),qimpm(nsample,mimp),tout(near),
     &	outtr(near),xc(maxcat),dn(maxcat),cp(maxcat),cm(maxcat),
     &	votecat(maxcat),freq(maxcat),wc(nsample),outts(ntest0),
     &	popclass(nprot0,nclass),protlow(mdim,nprot0,nclass),
     &	prot(mdim,nprot0,nclass),prothigh(mdim,nprot0,nclass),
     &	protfreq(mdim,nprot0,nclass,maxcat),rpop(nrnodes),
     &	protv(mdim,nprot0,nclass),wtx(nsample),
     &	protvlow(mdim,nprot0,nclass),protvhigh(mdim,nprot0,nclass)

	integer cat(mdim),iv(mdim),msm(mdim),
     &  muse(mdim),irnk(mdim,jbt),missing(mdim,near),a(mdim,nsample),
     &	asave(mdim,nsample),b(mdim,nsample),
     &	cl(nsample),out(nsample),nodextr(nsample),nodexvr(nsample),
     &	jin(nsample),joob(nsample),pjoob(nsample),ndbegin(near,jbt),
     &	jvr(nsample),jtr(nsample),jest(nsample),ibest(nrnn),
     &	isort(nsample),loz(near,nrnn),
     &	ta(nsample),ncase(nsample),idmove(nsample),kpop(nrnodes),
     &	jests(ntest0),jts(ntest0),iwork(near),
     &	nodexts(ntest0),clts(ntest0),imax(ntest0),jinb(near,jbt),
     &	bestsplitnext(nrnodes),bestvar(nrnodes),bestsplit(nrnodes),
     &	nodestatus(nrnodes),nodepop(nrnodes),nodestart(nrnodes),
     &	nodeclass(nrnodes),parent(nrnodes),treemap(2,nrnodes),
     &	ncts(nclass),nc(nclass),mtab(nclass,nclass),ncn(near),
     &  its(nsample),jpur(nrnn),npend(nclass),inear(nrnn),
     &	nrcat(maxcat),kcat(maxcat),ncatsplit(maxcat),
     &	nbestcat(maxcat,nrnodes),ncp(near),nodexb(near,jbt),
     &	npcase(near,jbt),ncount(near,jbt),nod(nrnodes),nmfmax,
     &	ncsplit,ncmax,nmissfill,ndimreps,nmf,nmd,iseed
c
c	-------------------------------------------------------
c    	USED IN PROXIMITY AND SCALING
c
	double precision prox(near,nrnn),y(near),u(near),
     &	dl(nscale0),xsc(near,nscale0),red(near),ee(near),
     &	ev(near,nscale0),ppr(near)
c
	character*500 text
c
c	-------------------------------------------------------
c    	SCALAR DECLARATIONS
c
	real errtr,errts,tavg,er,randomu
c
	integer mtry,n,m,mdimt,k,j,i,m1,jb,nuse,ndbigtree,jj,mr,
     &	n0,n1,n2,n3,n4,n5,n6,n7
c
c	-------------------------------------------------------
c	READ OLD TREE STRUCTURE AND/OR PARAMETERS
c
 	if (irunrf.eq.1)
     &		open(1,file='savedforest',status='old')
	if (ireadpar.eq.1)
     &		open(2,file='savedparams',status='old')
	if (ireadfill.eq.1)
     &		open(3,file='savedmissfill',status='old')
 	if (ireadprox.eq.1)
     &		open(4,file='savedprox',status='old')
c
c	-------------------------------------------------------
c	NAME OUTPUT FILES FOR SAVING THE FOREST STRUCTURE
c
 	if (isaverf.eq.1)
     &		open(1,file='savedforest',status='new')
	if (isavepar.eq.1)
     &		open(2,file='savedparams',status='new')
	if (isavefill.eq.1)
     &		open(3,file='savedmissfill',status='new')
 	if (isaveprox.eq.1)
     &		open(4,file='savedprox',status='new')
c
c	-------------------------------------------------------
c	NAME OUTPUT FILES TO SAVE DATA FROM CURRENT RUN
c
	if (idataout.ge.1)
     &		open(7,file='save-data-from-run',status='new')
	if (impfastout.eq.1)
     &		open(8,file='save-impfast',status='new')
 	if (impout.eq.1)
     &		open(9,file='save-importance-data',status='new')
 	if (impnout.eq.1)
     &		open(10,file='save-caseimp-data',status='new')
	if (interout.eq.1)
     &		open(11,file='save-pairwise-effects',status='new')
	if (iprotout.eq.1)
     &		open(12,file='save-protos',status='new')
 	if (iproxout.ge.1)
     &		open(13,file='save-run-proximities',status='new')
	if (iscaleout.eq.1)
     &		open(14,file='save-scale',status='new')
	if (ioutlierout.ge.1)
     &		open(15,file='save-outliers',status='new')
	if(iviz.eq.1) then
c		the graphics program expects files to be named in the 
c		following way:	
		open(21,file='data.txt',status='new')
		open(22,file='imp.txt',status='new')
		open(23,file='info.txt',status='new')
		open(24,file='par.txt',status='new')
		open(25,file='scale.txt',status='new')
		if (iprotout.eq.1) then
			open(26,file='proto.txt',status='new')
			open(27,file='protinf.txt',status='new')
		endif
		if(interact.eq.1) open(28,file='inter.txt',status='new')
		if(iproxout.ge.1) open(29,file='prox.txt',status='new')
	endif
c
c	-------------------------------------------------------
c	READ IN DATA--SEE MANUAL FOR FORMAT
c
	open(16, file='data.train', status='old')
	do n=1,ntrain
		read(16,*) (x(m,n),m=1,mdim),cl(n)
	enddo
	close(16)
	if(ntest.gt.0) then
		open(17, file='data.test', status='old')
		if(labelts.ne.0) then
			do n=1,ntest0
				read(17,*) (xts(m,n),m=1,mdim),clts(n)
			enddo
		else
			do n=1,ntest0
				read(17,*) (xts(m,n),m=1,mdim)
			enddo
		endif
		close(17)
	endif
c
c	-------------------------------------------------------
c	SELECT SUBSET OF VARIABLES TO USE
c
	if(mselect.eq.0) then
		mdimt=mdim
		do k=1,mdim
			msm(k)=k
		enddo
	endif
	if (mselect.eq.1) then
c		fill in which variables 
c		mdimt=
c		msm(1)=
c		---
c		msm(mdimt)=
	endif
c
c	-------------------------------------------------------
c	SET CATEGORICAL VALUES
c
	do m=1,mdim
		cat(m)=1
	enddo
c	fill in cat(m) for all variables m for which cat(m)>1
c	do m=1,mdim
c		cat(m)=4
c	enddo
c
c	-------------------------------------------------------
c	SET CLASS WEIGHTS

	if(jclasswt.eq.0) then
		do j=1,nclass
			classwt(j)=1
		enddo
	endif
	if(jclasswt.eq.1) then
c		fill in classwt(j) for each j:
c		classwt(1)=1.
c		classwt(2)=10.
	endif
c
c	=======================================================
c	**************  END OF USER INPUT  ********************
c	=======================================================
c
c	-------------------------------------------------------
c	MISC PARAMETERS (SHOULD NOT USUALLY NEED ADJUSTMENT)
	iseed=4351
	call sgrnd(iseed)
	nmfmax = 5 	!number of iterations (iterative fillin)
	ncsplit = 25	!number of random splits (big categoricals)
	ncmax = 25	!big categorical has more than ncmax levels
c
c	-------------------------------------------------------
c	ERROR CHECKING
c
	call checkin(labelts,labeltr,nclass,lookcls,jclasswt,
     &	mselect,mdim2nd,mdim,imp,impn,interact,nprox,nrnn,
     &	nsample,noutlier,nscale,nprot,missfill,iviz,isaverf,
     &	irunrf,isavepar,ireadpar,isavefill,ireadfill,isaveprox,
     &	ireadprox,isumout,idataout,impfastout,impout,interout,
     &	iprotout,iproxout,iscaleout,ioutlierout,cat,maxcat,cl)
c
c	-------------------------------------------------------
c	SPECIAL CASES - QUERY PARAMETERS OR USE SAVED TREE
c		
c	query parameters
	if(ireadpar.eq.1) goto 888
c		
c	use saved tree
	if(irunrf.eq.1) goto 999
c	
c	-------------------------------------------------------
c	INITIALIZATION
c
c	mtry will change if mdim2nd>0, so make it a variable
	mtry=mtry0
c
c	nmissfill is the number of missing-value-fillin loops
	nmissfill=1
	if(missfill.eq.2) nmissfill=nmfmax
c
c	ndimreps is 2 if we want to do variable selection,
c	otherwise it's 1
	ndimreps=1
	if(mdim2nd.gt.0) ndimreps=2
c
c	assign weights for equal weighting case 
c	(use getweights for unequal weighting case)
	if(jclasswt.eq.0) then
		do k=1,nrnodes
			tnodewt(k)=1
		enddo
	endif
c
	if(labeltr.eq.1) then
		do n=1,nsample
			wtx(n)=classwt(cl(n))
		enddo
	else
		do n=1,nsample
			wtx(n)=1.0
		enddo
	endif
c
c	-------------------------------------------------------
c	IF DATA ARE UNLABELED, ADD A SYNTHETIC CLASS
c
	if(labeltr.eq.0) then
		call createclass(x,cl,ntrain,nsample,mdim)
	endif
c
c	-------------------------------------------------------
c	COUNT CLASS POPULATIONS
c
	call zerv(nc,nclass)
	do n=1,nsample
		nc(cl(n))=nc(cl(n))+1
	enddo
	if(ntest.gt.0.and.labelts.eq.1) then
		call zerv(ncts,nclass)
		do n=1,ntest0
			ncts(clts(n))=ncts(clts(n))+1
		enddo
	endif
c
c	-------------------------------------------------------
c	DO PRELIMINARY MISSING DATA
c
	if(missfill.eq.1) then
		call roughfix(x,v,ncase,mdim,nsample,
     &		cat,code,nrcat,maxcat,fill)
		if(ntest.gt.0) then
			call xfill(xts,ntest,mdim,fill,code)
		endif
	endif
	if(missfill.eq.2) then
		do n=1,near
			do m=1,mdim
				if(abs(code-x(m,n)).lt.8.232D-11) then
					missing(m,n)=1
				else 
					missing(m,n)=0
				endif
			enddo
		enddo
		call roughfix(x,v,ncase,mdim,nsample,
     &		cat,code,nrcat,maxcat,fill)
	endif
c
c	-------------------------------------------------------
c	TOP OF LOOP FOR ITERATIVE MISSING VALUE FILL OR SUBSET SELECTION
c
	do nmd=1,ndimreps

	if(imp.gt.0) then
		call zervr(sqsd,mimp)
		call zervr(avimp,mimp)
	endif
	call zervr(avgini,mdim)
	if(impn.eq.1) then
		call zervr(qimp,nsample)
		call zermr(qimpm,nsample,mdim)
	endif
	if(interact.eq.1) call zermr(votes,mdim,jbt)

	do nmf=1,nmissfill
c
c	-------------------------------------------------------
c	INITIALIZE FOR RUN
c
	call makea(x,mdim,nsample,cat,isort,v,asave,b,mdimt,
     &	msm,v5,v95,maxcat)
c
	call zermr(q,nclass,nsample)
	call zerv(out,nsample)
	if(nprox.gt.0) call zermd(prox,near,nrnn)
	if(ntest.gt.0) then
 		call zermr(qts,nclass,ntest)
	endif
c
c	=======================================================
c	**************  BEGIN MAIN LOOP  **********************
c	=======================================================
c
	do jb=1,jbt
c	
c	-------------------------------------------------------
c	INITIALIZE
c	
	call zervr(win,nsample)
	call zerv(jin,nsample)
	call zervr(tclasspop,nclass)
c
c	-------------------------------------------------------
c	TAKE A BOOTSTRAP SAMPLE 
c
	do n=1,nsample
		k=int(randomu()*nsample)
		if(k.lt.nsample) k=k+1
		win(k)=win(k)+classwt(cl(k))
		jin(k)=jin(k)+1
		tclasspop(cl(k))=tclasspop(cl(k))+classwt(cl(k))
	enddo
	do n=1,nsample
		if(jin(n).eq.0) out(n)=out(n)+1
c		out(n)=number of trees for which the nth 
c		obs has been out-of-bag
	enddo
c
c	-------------------------------------------------------
c	PREPARE TO BUILD TREE
c
	call moda(asave,a,nuse,nsample,mdim,cat,maxcat,ncase,
     &	jin,mdimt,msm)
c
c	-------------------------------------------------------
c	MAIN TREE-BUILDING 
c
	call buildtree(a,b,cl,cat,mdim,nsample,nclass,treemap,
     &  bestvar,bestsplit,bestsplitnext,dgini,nodestatus,nodepop,
     &	nodestart,classpop,tclasspop,tclasscat,ta,nrnodes,
     &	idmove,ndsize,ncase,parent,mtry,nodeclass,ndbigtree,
     &	win,wr,wl,nuse,kcat,ncatsplit,xc,dn,cp,cm,maxcat,
     &	nbestcat,msm,mdimt,iseed,ncsplit,ncmax)
c
c	-------------------------------------------------------
c	SPLIT X
c
	call xtranslate(x,mdim,nrnodes,nsample,bestvar,bestsplit,
     &  bestsplitnext,xbestsplit,nodestatus,cat,ndbigtree)
c
c	-------------------------------------------------------
c	ASSIGN CLASSWEIGHTS TO NODES
c
	if(jclasswt.eq.1) then
		call getweights(x,nsample,mdim,treemap,nodestatus,
     &		xbestsplit,bestvar,nrnodes,ndbigtree,
     &		cat,maxcat,nbestcat,jin,win,tw,tn,tnodewt)
	endif
c
c	-------------------------------------------------------
c	GET OUT-OF-BAG ESTIMATES
c
	call testreebag(x,nsample,mdim,treemap,nodestatus,
     &  xbestsplit,bestvar,nodeclass,nrnodes,ndbigtree,kpop,
     &	cat,jtr,nodextr,maxcat,nbestcat,rpop,dgini,tgini,jin,
     &	wtx)
	do n=1,nsample
		if(jin(n).eq.0) then
c		this case is out-of-bag
		q(jtr(n),n)=q(jtr(n),n)+tnodewt(nodextr(n))
		endif
	enddo
	do k=1,mdimt
		m=msm(k)
		avgini(m)=avgini(m)+tgini(m)
		if(interact.eq.1) votes(m,jb)=tgini(m)
	enddo
c	
c	-------------------------------------------------------
c	DO PRE-PROX COMPUTATION
c	
	if(nprox.eq.1) then
		call preprox(near,nrnodes,jbt,nodestatus,ncount,jb,
     &		nod,nodextr,nodexb,jin,jinb,ncn,ndbegin,kpop,rinpop,
     &		npcase,rpop,nsample)
	endif
c
c	-------------------------------------------------------
c	GET TEST SET ERROR ESTIMATES
c
	if(ntest.gt.0) then
		call testreelite(xts,ntest,mdim,treemap,nodestatus,
     &  	xbestsplit,bestvar,nodeclass,nrnodes,ndbigtree,
     &		cat,jts,maxcat,nbestcat,nodexts)
		do n=1,ntest0
			qts(jts(n),n)=qts(jts(n),n)+tnodewt(nodexts(n))
		enddo
	endif
c
c	-------------------------------------------------------
c	GIVE RUNNING OUTPUT
c
	if(lookcls.eq.1.and.jb.eq.1) then
		write(*,*) 'class counts-training data'
		write(*,*) (nc(j),j=1,nclass)
		if(ntest.gt.0.and.labelts.eq.1) then
			print*
			write(*,*) 'class counts-test data'
			write(*,*) (ncts(j),j=1,nclass)
		endif
	endif
	if(mod(jb,look).eq.0.or.jb.eq.jbt) then
		call comperrtr(q,cl,nsample,nclass,errtr,
     &  	tmiss,nc,jest,out)
		if(look.gt.0) then
		if(lookcls.eq.1) then
			write(*,'(i8,100f10.2)') 
     &			jb,100*errtr,(100*tmiss(j),j=1,nclass)
		else
			write(*,'(i8,2f10.2)') jb,100*errtr
		endif
		endif
		if(ntest.gt.0) then
			call comperrts(qts,clts,ntest,nclass,errts,
     & 			tmissts,ncts,jests,labelts)
			if(look.gt.0) then
			if(labelts.eq.1) then
			   if(lookcls.eq.1) then
				write(*,'(i8,20f10.2)') jb,100*errts,
     &				(100*tmissts(j),j=1,nclass)
			   else
				write(*,'(i8,2f10.2)') jb,100*errts
			   endif
			   print *
			endif
			endif
		endif
	endif
c	
c	-------------------------------------------------------
c	VARIABLE IMPORTANCE 
c
	if(imp.eq.1.and.nmf.eq.nmissfill) then
	call varimp(x,nsample,mdim,cl,nclass,jin,jtr,impn,
     &	interact,msm,mdimt,qimp,qimpm,avimp,sqsd,
     &	treemap,nodestatus,xbestsplit,bestvar,nodeclass,nrnodes,
     &	ndbigtree,cat,jvr,nodexvr,maxcat,nbestcat,tnodewt,
     &	nodextr,joob,pjoob,iv)
	endif
c
c	-------------------------------------------------------
c	SEND SAVETREE DATA TO FILE (IF THIS IS THE FINAL FOREST)
c
	if(isaverf.eq.1.and.nmd.eq.ndimreps.and.nmf.eq.nmissfill) then
		if(jb.eq.1) then
			write(1,*) (cat(m),m=1,mdim)
			if(missfill.ge.1) write(1,*) (fill(m),m=1,mdim)
		endif
		write(1,*) ndbigtree
   		do n=1,ndbigtree
			write(1,*) n,nodestatus(n),bestvar(n),treemap(1,n),
     &			treemap(2,n),nodeclass(n),xbestsplit(n),tnodewt(n),
     &			(nbestcat(k,n),k=1,maxcat)
		enddo
	endif
	
c	=======================================================
c	**************  END MAIN LOOP  ************************
c	=======================================================
	enddo !jb
c
c	-------------------------------------------------------
c	FIND PROXIMITIES, FILL IN MISSING VALUES AND ITERATE
c
	if(nmf.lt.nmissfill) then
		write(*,*) 'nrep',nmf
		
c		compute proximities between each obs in the training 
c		set and its nrnn closest neighbors
		
		call comprox(prox,nodexb,jinb,ndbegin,
     &		npcase,ppr,rinpop,near,jbt,noutlier,outtr,cl,
     &		loz,nrnn,wtx,nsample,iwork,ibest)
     
c		use proximities to impute missing values

		call impute(x,prox,near,mdim,
     &		maxcat,votecat,cat,nrnn,loz,missing)
	endif
	enddo !nmf
c
c	-------------------------------------------------------
c	COMPUTE IMPORTANCES, SELECT SUBSET AND LOOP BACK
c
	if(imp.eq.1) then
		call finishimp(mdim,sqsd,avimp,signif,
     &		zscore,jbt,mdimt,msm)
		do m=1,mdimt
c			zt(m) is the negative z-score for variable msm(m)
			zt(m)=-zscore(msm(m))
			muse(m)=msm(m)
		enddo
c		sort zt from smallest to largest,and sort muse accordingly
		call quicksort(zt,muse,1,mdimt,mdim)
c		muse(m) refers to the variable that has the mth-smallest zt
c		select the mdim2nd most important variables and iterate
		if(mdim2nd.gt.0) then
			mdimt=mdim2nd
			do m=1,mdimt
				msm(m)=muse(m)
			enddo
			mtry=nint(sqrt(real(mdimt)))
	   	endif
	endif
	enddo !nmd
c
c	-------------------------------------------------------
c	END OF ITERATIONS - NOW ENDGAME
c	-------------------------------------------------------
c
c	-------------------------------------------------------
c	NORMALIZE VOTES
c
	do j=1,nclass
		do n=1,nsample
			if(q(j,n).gt.0.0.and.out(n).gt.0) q(j,n)=q(j,n)/real(out(n))
		enddo
		if(ntest.gt.0) then
			do n=1,ntest0
				qts(j,n)=qts(j,n)/jbt
			enddo
		endif
	enddo
c
c	-------------------------------------------------------
c	COMPUTE PROXIMITIES AND SEND TO FILE
c
	if(nprox.ge.1) then
c		compute proximities between each obs in the training 
c		set and its nrnn closest neighbors
		
		call comprox(prox,nodexb,jinb,ndbegin,
     &		npcase,ppr,rinpop,near,jbt,noutlier,outtr,cl,
     &		loz,nrnn,wtx,nsample,iwork,ibest)
   
		if(iproxout.ge.1) then 
			do n=1,near
				write(13,'(i5,500(i5,f10.3))') n,(loz(n,k),
     &				prox(n,k),k=1,nrnn)
			enddo
		endif
	endif
	close(13)
c
c	-------------------------------------------------------
c	COMPUTE SCALING COORDINATES AND SEND TO FILE
c
	if(nprox.eq.1.and.nscale.gt.0) then
		call myscale(loz,prox,xsc,y,u,near,nscale,red,nrnn,
     &		ee,ev,dl)
		if(iscaleout.eq.1)then
			do n=1,nscale0
				write(14,'(i5,f10.3)') n,dl(n)
			enddo
			do n=1,near
				write(14,'(3i5,15f10.3)') n,cl(n),jest(n),
     &				(xsc(n,k),k=1,nscale0)
			enddo
			close(14)
		endif
	endif
c
c	-------------------------------------------------------
c	COMPUTE CASEWISE VARIABLE IMPORTANCE (FOR GRAPHICS)
c	AND SEND TO FILE
c
	if(impn.eq.1) then
		do n=1,nsample
			do m1=1,mdimt
				mr=msm(m1)
				qimpm(n,mr)=100*(qimp(n)-qimpm(n,mr))/jbt
			enddo
			if(impnout.eq.1) write(10,'(100f10.3)')
     &			(qimpm(n,msm(m1)),m1=1,mdimt)
		enddo
	endif
c
c	-------------------------------------------------------
c	SEND IMPORTANCES TO FILE OR SCREEN
c
	if(imp.eq.1) then
		do k=1,min0(mdimt,25)
			m=muse(k)
			if(impout.eq.1) write(9,'(i5,10f10.3)')m,100*avimp(m),
     &			zscore(m),signif(m)
			if(impout.eq.2) write(*,'(i5,10f10.3)')m,100*avimp(m),
     &			zscore(m),signif(m)
		enddo
		close(9)
	endif
c
c	-------------------------------------------------------
c	COMPUTE INTERACTIONS AND SEND TO FILE OR SCREEN
c
	if(interact.eq.1) then
		call compinteract(votes,effect,msm,mdim,mdimt,
     &		jbt,g,iv,irnk,hist,teffect)
		if(interout.eq.1) then
			write(11,*)'CODE'
			do i=1,mdimt
				write(11,*) i,msm(i)
			enddo
			print*
			do i=1,mdimt
				m=msm(i)
				effect(m,m)=0
				write(11,'(40i5)') i,
     &				(nint(effect(m,msm(j))),j=1,mdimt)
			enddo
			close(11)
		endif
		if(interout.eq.2) then
			write(*,*)'CODE'
			do i=1,mdimt
				write(*,*) i,msm(i)
			enddo
			print*
			do i=1,mdimt
				m=msm(i)
				effect(m,m)=0
				write(*,'(20i5)') i,
     &				(nint(effect(m,msm(j))),j=1,mdimt)
			enddo
		endif
	endif
c
c	-------------------------------------------------------
c	COMPUTE FASTIMP AND SEND TO FILE
c
	if(impfastout.eq.1) then
		tavg=0
		do k=1,mdimt
			m=msm(k)
			tavg=tavg+avgini(m)
		enddo
		tavg=tavg/mdimt
		do k=1,mdimt
			m=msm(k)
			write(8,*) m,avgini(m)/tavg
		enddo
		close(8)
	endif

c	-------------------------------------------------------
c	COMPUTE PROTOTYPES AND SEND TO FILE
c
	if(nprox.ge.1.and.nprot.gt.0) then
	 	call compprot(loz,nrnn,nsample,mdim,its,
     &		cl,wc,nclass,x,mdimt,msm,temp,cat,maxcat,
     & 		jpur,inear,nprot,protlow,prothigh,prot,protfreq,
     & 		protvlow,protvhigh,protv,
     &		popclass,npend,freq,v5,v95)
c	
		if (iprotout.eq.1) then
		write(12,'(a5,50i10)') '     ',(
     &	    	(nint(popclass(i,j)),i=1,npend(j)),j=1,nclass)
		write(12,'(a5,50i10)') '     ',(
     &	    	(i,i=1,npend(j)),j=1,nclass)
		write(12,'(a5,50i10)') '     ',(
     &	    	(j,i=1,npend(j)),j=1,nclass)
		do k=1,mdimt
			m=msm(k)
			if(cat(m).eq.1) then
	 			write(12,'(i5,50f10.3)') k,
     &		     	 	((prot(m,i,j),protlow(m,i,j),
     & 		 		prothigh(m,i,j),i=1,npend(j)),j=1,nclass)
			else 
	 			write(12,'(i5,50f10.3)') k,
     &		     	 	(((protfreq(m,i,j,jj),jj=1,cat(m)),
     &				i=1,npend(j)),j=1,nclass)
			endif
	 	enddo
    		endif
		close (12)
c
	 	if(iprotout.eq.2) then
	 	write(*,'(a5,50i10)') '     ',((nint(popclass(i,j)),
     &	    	i=1,npend(j)),j=1,nclass)
	 	do k=1,mdimt
	 		m=msm(k)
			if(cat(m).eq.1) then
				write(*,'(i5,50f10.3)') k,
     &				((prot(m,i,j),protlow(m,i,j),
     &				prothigh(m,i,j),i=1,npend(j)),j=1,nclass)
			else
	 			write(*,'(i5,50f10.3)') k,
     &		     	 	(((protfreq(m,i,j,jj),jj=1,cat(m)),
     &				i=1,npend(j)),j=1,nclass)
			endif
		enddo
	 	endif
	endif
c
c	-------------------------------------------------------
c	COMPUTE OUTLIER MEASURE AND SEND TO FILE
c
	if(noutlier.ge.1) then
		call locateout(cl,tout,outtr,ncp,isort,devout,
     &		near,nsample,nclass,rmedout)
		if(ioutlierout.ge.1) then
			do n=1,near
				write(15,'(2i5,f10.3)') n,cl(n),
     &				amax1(outtr(n),0.0)
			enddo
		endif
	endif
	
c	-------------------------------------------------------
c	SUMMARY OUTPUT
c
	if (isumout.eq.1) then
		write(*,*) 'final error rate %    ',100*errtr
		if(ntest.gt.0.and.labelts.ne.0)then
			write(*,*) 'final error test %    ',100*errts 
		endif 
		print *
		write(*,*) 'Training set confusion matrix (OOB):'
		call zerm(mtab,nclass,nclass)
		do n=1,nsample
			if(jest(n).gt.0) mtab(cl(n),jest(n))=mtab(cl(n),jest(n))+1
		enddo
		write(*,*) '	    true class '
		print *
		write(*,'(20i6)')  (i,i=1,nclass)
		print *
		do j=1,nclass
			write(*,'(20i6)')  j,(mtab(i,j),i=1,nclass)
		enddo
		print *
 		if(ntest.gt.0.and.labelts.ne.0) then
 		   call zerm(mtab,nclass,nclass)
 		   do n=1,ntest0
 			mtab(clts(n),jests(n))=mtab(clts(n),jests(n))+1
 		   enddo
 		   write(*,*) 'Test set confusion matrix:'
 		   write(*,*) '	    true class '
 		   print *
 		   write(*,'(20i6)')  (i,i=1,nclass)
 		   print *
 		   do j=1,nclass
 			write(*,'(20i6)')  j,(mtab(i,j),i=1,nclass)
 		   enddo
 		   print *
 		endif
	endif
c
c	-------------------------------------------------------
c	SEND INFO ON TRAINING AND/OR TEST SET DATA TO FILE 
c
	if(idataout.ge.1) then
		do n=1,nsample
			write(7,'(3i5,5000f10.3)') n,cl(n),jest(n),
     & 			(q(j,n),j=1,nclass),(x(m,n),m=1,mdim)
		enddo
	endif
	if(idataout.eq.2.and.ntest.gt.0) then
		if(labelts.eq.1) then
			do n=1,ntest0
				write(7,'(3i5,1000f10.3)') n,clts(n),jests(n),
     & 				(qts(j,n),j=1,nclass),(xts(m,n),m=1,mdim)
			enddo
		else
			do n=1,ntest0
				write(7,'(2i5,1000f10.3)') n,jests(n),
     & 				(qts(j,n),j=1,nclass),(xts(m,n),m=1,mdim)
			enddo
		endif
	endif
	close(7)
c
c	-------------------------------------------------------
c	SEND GRAPHICS INFO TO FILES 
c
	if(iviz.eq.1) then
		do n=1,nsample
			write(21,'(1000f10.3)') (x(msm(m),n),m=1,mdimt)
		enddo
		do n=1,nsample
			write(22,'(100f10.3)')(qimpm(n,msm(m1)),m1=1,mdimt)
		enddo
		do n=1,nsample
			write(23,'(3i5,5000f10.3)') n,cl(n),jest(n),
     & 			(q(j,n),j=1,nclass)
		enddo
		write(24,*) nsample,mdimt,nscale,nclass,mdimt,nprot,nrnn
		do n=1,near
			write(25,'(50f10.3)') (xsc(n,k),k=1,nscale0)
		enddo
		    if (iprotout.eq.1) then
		 		do j=1,nclass
		 			do i=1,npend(j)
					write(26,'(3i5,5000f10.3)') j,i,1,(protv(msm(m),i,j),m=1,mdimt)
					write(26,'(3i5,5000f10.3)') j,i,2,(protvlow(msm(m),i,j),m=1,mdimt)
					write(26,'(3i5,5000f10.3)') j,i,3,(protvhigh(msm(m),i,j),m=1,mdimt)
					write(27,'(i5)') nint(popclass(i,j))
				enddo
	 			enddo
    		endif
     		if(interact.eq.1) then
		    	do i=1,mdimt
				m=msm(i)
				effect(m,m)=0
				write(28,'(40i5)')
     &				(nint(effect(m,msm(j))),j=1,mdimt)
			enddo
		endif
		if(iproxout.ge.1) then 
			do n=1,nsample
c				write(29,'(5000(i5,f10.3))') (loz(n,k),prox(n,k),k=1,nrnn)
c				NEW???:
				write(29,'(5000(i5,f10.3))') (k,prox(n,k),k=1,nrnn)
			enddo
		endif
	endif
c
c	-------------------------------------------------------
c	SEND FILL TO FILE (ROUGH FILL ONLY)
c
	if(isavefill.eq.1.and.missfill.eq.1) then
		write(3,*) (fill(m),m=1,mdim)
	endif
c
c	-------------------------------------------------------
c	SEND RUN PARAMETERS TO FILE 
c
	if(isavepar.eq.1) then
		write(2,*) ntrain,mdim,maxcat,nclass,jbt,
     &		jclasswt,missfill,code,nrnodes,
     &		100*errtr
c
c		type in comments up to 500 characters long
c		between the ' ' in the line below.
c
		write(2,*) 'this is a test run to verify that my 
     &		descriptive output works.'
		close (2)
	endif
c
c	-------------------------------------------------------
c	END OF USUAL RUN
c
c
c	-------------------------------------------------------
c	READ RUN PARAMETERS AND PRINT TO SCREEN
c
888	if(ireadpar.eq.1) then
		read(2,*) n0,n1,n2,n3,n4,n5,n6,n7,er
		write(*,*) 'parameters'
		write(*,*) 'nsample=' ,n0
		write(*,*) 'mdim= ' ,n1
		write(*,*) 'maxcat=',n2
		write(*,*) 'nclass=',n3
		write(*,*) 'jbt=  ' ,n4
		write(*,*) 'jclasswt=',n5
		write(*,*) 'code='    ,n6
		write(*,*) 'nrnodes=' ,n7
		print *
		write(*,*) 'out-of-bag error=',er,'%'
		print *
		read(2,'(500a)') text
		write(*,*) text
c
		stop
c
	endif
c
c	-------------------------------------------------------
c	RERUN OLD RANDOM FOREST
c
999	if(irunrf.eq.1.and.ntest.gt.0) then
		call runforest(mdim,ntest,nclass,maxcat,nrnodes,
     &		labelts,jbt,clts,xts,xbestsplit,qts,treemap,nbestcat,
     &		nodestatus,cat,nodeclass,jts,jests,bestvar,tmissts,ncts,
     &		fill,missfill,code,errts,tnodewt,outts,idataout,imax,
     &		look,lookcls,nodexts,isumout,mtab) 
	endif
c
c	=======================================================
c	**************  END MAIN ******************************
c	=======================================================
c
	end
c
c	=======================================================
c	**************  SUBROUTINES AND FUNCTIONS  ************
c	=======================================================
c
c	-------------------------------------------------------
	subroutine runforest(mdim,ntest,nclass,maxcat,nrnodes,
     &	labelts,jbt,clts,xts,xbestsplit,qts,treemap,nbestcat,
     &	nodestatus,cat,nodeclass,jts,jests,bestvar,tmissts,ncts,
     &	fill,missfill,code,errts,tnodewt,outts,idataout,imax,
     &	look,lookcls,nodexts,isumout,mtab)
c
c	reads a forest file and runs new data through it
c
	real xts(mdim,ntest),xbestsplit(nrnodes),tmissts(nclass),
     &	qts(nclass,ntest),fill(mdim),tnodewt(nrnodes),outts(ntest)
c
	integer treemap(2,nrnodes),nodestatus(nrnodes),
     &	cat(mdim),nodeclass(nrnodes),jests(ntest),
     &	bestvar(nrnodes),jts(ntest),clts(ntest),nodexts(nrnodes),
     &	ncts(nclass),imax(ntest),nbestcat(maxcat,nrnodes),
     &	isumout,mtab(nclass,nclass)

c
	integer mdim,ntest,nclass,maxcat,nrnodes,labelts,
     &	jbt,missfill,look,lookcls,idataout
	real errts,code
	integer m,j,n,jb,ndbigtree,idummy
	call zermr(qts,nclass,ntest)
c
	read(1,*) (cat(m),m=1,mdim)
c
	if(missfill.eq.1) then
		read(1,*) (fill(m),m=1,mdim)
c		fast fix on the test data -
		call xfill(xts,ntest,mdim,fill,code)
	endif
c
	if(labelts.eq.1) then
		do n=1,ntest
			ncts(clts(n))=ncts(clts(n))+1
		enddo
	endif
c
c	START DOWN FOREST
c
	do jb=1,jbt
		read(1,*) ndbigtree
		do n=1,ndbigtree
			read(1,*) idummy,nodestatus(n),bestvar(n),
     &			treemap(1,n),treemap(2,n),nodeclass(n),
     &			xbestsplit(n),tnodewt(n),(nbestcat(j,n),j=1,maxcat)
    		enddo
		
		call testreelite(xts,ntest,mdim,treemap,nodestatus,
     &  	xbestsplit,bestvar,nodeclass,nrnodes,ndbigtree,
     &		cat,jts,maxcat,nbestcat,nodexts)
   		do n=1,ntest
			qts(jts(n),n)=qts(jts(n),n)+tnodewt(nodexts(n))
		enddo
		
		if(labelts.eq.1) then
			if(mod(jb,look).eq.0.and.jb.le.jbt) then
				call comperrts(qts,clts,ntest,nclass,errts,
     & 				tmissts,ncts,jests,labelts)
				if(lookcls.eq.1) then
					write(*,'(i8,100f10.2)') 
     &					jb,100*errts,(100*tmissts(j),j=1,nclass)
				else
					write(*,'(i8,2f10.2)') jb,100*errts
				endif
			endif
		endif
c
	enddo !jb
c
	if(idataout.eq.2) then
		if(labelts.eq.1) then
			do n=1,ntest
				write(7,'(3i5,1000f10.3)') n,clts(n),jests(n),
     & 				(qts(j,n),j=1,nclass),(xts(m,n),m=1,mdim)
			enddo
		else
			do n=1,ntest
				write(7,'(3i5,1000f10.3)') n,jests(n),
     & 				(qts(j,n),j=1,nclass),(xts(m,n),m=1,mdim)
			enddo
		endif
	endif
	close(7)
	if (isumout.eq.1) then
		if(labelts.eq.1)then
		   write(*,*) 'final error test %    ',100*errts 
 		   call zerm(mtab,nclass,nclass)
 		   do n=1,ntest
 			mtab(clts(n),jests(n))=mtab(clts(n),jests(n))+1
 		   enddo
 		   write(*,*) 'Test set confusion matrix:'
 		   write(*,*) '	    true class '
 		   print *
 		   write(*,'(20i6)')  (j,j=1,nclass)
 		   print *
 		   do n=1,nclass
 			write(*,'(20i6)')  n,(mtab(j,n),j=1,nclass)
 		   enddo
 		   print *
 		endif
	endif
	end
c
c	-------------------------------------------------------
	subroutine makea(x,mdim,nsample,cat,isort,v,asave,b,mdimt,
     &	msm,v5,v95,maxcat)
c
	real x(mdim,nsample),v(nsample),v5(mdim),v95(mdim)
	integer cat(mdim),isort(nsample),asave(mdim,nsample),
     &	b(mdim,nsample),msm(mdim)
	integer mdim,nsample,mdimt,maxcat
	integer k,mvar,n,n1,n2,ncat,jj
c
c	submakea constructs the mdim x nsample integer array a.
c	If there are less than 32,000 cases, this can be declared 
c	integer*2,otherwise integer*4. For each numerical variable 
c	with values x(m,n),n=1,...,nsample, the x-values are sorted 
c	from lowest to highest. Denote these by xs(m,n). 
c	Then asave(m,n) is the case  number in which 
c	xs(m,n) occurs. The b matrix is also constructed here. If the mth 
c	variable is categorical, then asave(m,n) is the category of the nth 
c	case number.  
c
c	input: x,cat
c	output: a,b
c	work: v,isort
c
	do k=1,mdimt
	  mvar=msm(k)
	  if (cat(mvar).eq.1) then
		do n=1,nsample
			v(n)=x(mvar,n)
			isort(n)=n
		enddo
		call quicksort(v,isort,1,nsample,nsample)
c		this sorts the v(n) in ascending order. isort(n) is the 
c		case number of that v(n) nth from the lowest (assume 
c		the original case numbers are 1,2,...).  
		n1=nint(.05*nsample)
		if(n1.lt.1) n1=1
		v5(mvar)=v(n1)
		n2=nint(.95*nsample)
		if(n2.gt.nsample) n2=nsample
		v95(mvar)=v(n2)
		do n=1,nsample-1
			n1=isort(n)
			n2=isort(n+1)
			asave(mvar,n)=n1
			if(n.eq.1) b(mvar,n1)=1
			if (v(n).lt.v(n+1)) then
				b(mvar,n2)=b(mvar,n1)+1
			else
				b(mvar,n2)=b(mvar,n1)
			endif
		enddo
		asave(mvar,nsample)=isort(nsample)
	  else
		do ncat=1,nsample
			jj=nint(x(mvar,ncat))
			asave(mvar,ncat)=jj
		enddo
	  endif
	enddo
c
	end
c
c	-------------------------------------------------------
	subroutine moda(asave,a,nuse,nsample,mdim,cat,maxcat,
     &	ncase,jin,mdimt,msm)
c
	integer asave(mdim,nsample),a(mdim,nsample),cat(mdim),
     &	jin(nsample),ncase(nsample),msm(mdim)
	integer nuse,nsample,mdim,mdimt,maxcat
	integer n,jj,m,k,nt,j
c
c	copy rows msm(1),...,msm(mdimt) of asave into the same 
c	rows of a
c
	nuse=0
	do n=1,nsample
		do k=1,mdimt
			m=msm(k)
			a(m,n)=asave(m,n)
		enddo
		if(jin(n).ge.1) nuse=nuse+1
	enddo
	do jj=1,mdimt
		m=msm(jj)
		k=1
		nt=1
		if(cat(m).eq.1) then
			do n=1,nsample
			if(k.gt.nsample) goto 37
			    if(jin(a(m,k)).ge.1) then
					a(m,nt)=a(m,k)
					k=k+1
				else
					do j=1,nsample-k
						if(jin(a(m,k+j)).ge.1) then
							a(m,nt)=a(m,k+j)
							k=k+j+1
							goto 28
						endif
					enddo
				endif
28				continue
				nt=nt+1
				if(nt.gt.nuse) goto 37
			enddo
37			continue
		endif
	enddo
	if(maxcat.gt.1) then
		k=1
		nt=1
		do n=1,nsample
			if(jin(k).ge.1) then
				ncase(nt)=k
				k=k+1
			else
				do jj=1,nsample-k
					if(jin(k+jj).ge.1) then
						ncase(nt)=k+jj
						k=k+jj+1
						goto 58
					endif
				enddo
			endif
58			continue
			nt=nt+1
			if(nt.gt.nuse) goto 85
		enddo
85		continue
	endif
	end
c
c	-------------------------------------------------------
	subroutine buildtree(a,b,cl,cat,mdim,nsample,nclass,treemap,
     &  bestvar,bestsplit,bestsplitnext,dgini,nodestatus,nodepop,
     &	nodestart,classpop,tclasspop,tclasscat,ta,nrnodes,
     &	idmove,ndsize,ncase,parent,mtry,nodeclass,ndbigtree,
     &	win,wr,wl,nuse,kcat,ncatsplit,xc,dn,cp,cm,maxcat,
     &	nbestcat,msm,mdimt,iseed,ncsplit,ncmax)
c
c	Buildtree consists of repeated calls to findbestsplit and movedata.
c	Findbestsplit does just that--it finds the best split of the current 
c	node. Movedata moves the data in the split node right and left so 
c	that the data corresponding to each child node is contiguous.  
c
c	The buildtree bookkeeping is different from that in Friedman's 
c	original CART program: 
c		ncur is the total number of nodes to date
c		nodestatus(k)=1 if the kth node has been split.
c		nodestatus(k)=2 if the node exists but has not yet been split
c			  and=-1 of the node is terminal.  
c	A node is terminal if its size is below a threshold value, or if it 
c	is all one class,or if all the x-values are equal. If the current 
c	node k is split,then its children are numbered ncur+1 (left), and 
c	ncur+2(right),ncur increases to ncur+2 and the next node to be split 
c	is numbered k+1. When no more nodes can be split,buildtree
c	returns to the main program.
c
	integer cl(nsample),cat(mdim),ncatsplit(maxcat),
     &  treemap(2,nrnodes),bestvar(nrnodes),nodeclass(nrnodes),
     &	bestsplit(nrnodes),nodestatus(nrnodes),ta(nsample),
     &  nodepop(nrnodes),nodestart(nrnodes),idmove(nsample),
     &	bestsplitnext(nrnodes),ncase(nsample),parent(nrnodes),
     &	kcat(maxcat),msm(mdim),iseed,ncsplit,ncmax
    	
	integer a(mdim,nsample),b(mdim,nsample)
	real tclasspop(nclass),classpop(nclass,nrnodes),
     &  tclasscat(nclass,maxcat),win(nsample),wr(nclass),
     &	wl(nclass),dgini(nrnodes),xc(maxcat),dn(maxcat),
     &	cp(maxcat),cm(maxcat)
	integer mdim,nsample,nclass,nrnodes,ndsize,
     &  mtry,ndbigtree,nuse,maxcat,mdimt,j,ncur,
     &	kbuild,ndstart,ndend,jstat
	integer msplit,nbest
	integer lcat,i,kn,k,n,ndendl,nc
	real decsplit,popt1,popt2,pp
	integer nbestcat(maxcat,nrnodes)
c
	call zerv(nodestatus,nrnodes)
	call zerv(nodestart,nrnodes)
	call zerv(nodepop,nrnodes)
	call zermr(classpop,nclass,nrnodes)
	call zerm(treemap,2,nrnodes)
	call zerm(nbestcat,maxcat,nrnodes)
	do j=1,nclass
		classpop(j,1)=tclasspop(j)
	enddo
c
	ncur=1
	nodestart(1)=1
	nodepop(1)=nuse
	nodestatus(1)=2
c	start main loop
c
	do 30 kbuild=1,nrnodes
		if (kbuild.gt.ncur) goto 50
		if (nodestatus(kbuild).ne.2) goto 30
c		initialize for next call to findbestsplit
c
		ndstart=nodestart(kbuild)
		ndend=ndstart+nodepop(kbuild)-1
		do j=1,nclass
			tclasspop(j)=classpop(j,kbuild)
		enddo
		jstat=0
c			
		call findbestsplit(a,b,cl,mdim,nsample,nclass,cat,
     &		ndstart,ndend,tclasspop,tclasscat,msplit,decsplit,nbest,
     &		ncase,jstat,mtry,win,wr,wl,kcat,ncatsplit,xc,dn,
     &		cp,cm,maxcat,msm,mdimt,iseed,ncsplit,ncmax)
c
		if(jstat.eq.1) then
			nodestatus(kbuild)=-1
			goto 30
		else
			bestvar(kbuild)=msplit
			dgini(kbuild)=decsplit
c			
			if (cat(msplit).eq.1) then
c				continuous
				bestsplit(kbuild)=a(msplit,nbest)
				bestsplitnext(kbuild)=a(msplit,nbest+1)
			else
c				categorical
				lcat=cat(msplit)
				do i=1,lcat
					nbestcat(i,kbuild)=ncatsplit(i)
				enddo
			endif
		endif
		call movedata(a,ta,mdim,nsample,ndstart,ndend,idmove,ncase,
     &		msplit,cat,nbest,ndendl,ncatsplit,maxcat,mdimt,msm)
c
c		leftnode no.=ncur+1,rightnode no.=ncur+2.
c
		nodepop(ncur+1)=ndendl-ndstart+1
		nodepop(ncur+2)=ndend-ndendl
		nodestart(ncur+1)=ndstart
		nodestart(ncur+2)=ndendl+1
c
c
c		find class populations in both nodes
		do n=ndstart,ndendl
			nc=ncase(n)
			j=cl(nc)
			classpop(j,ncur+1)=classpop(j,ncur+1)+win(nc)
		enddo
		do n=ndendl+1,ndend
			nc=ncase(n)
			j=cl(nc)
			classpop(j,ncur+2)=classpop(j,ncur+2)+win(nc)
		enddo
c
c		check on nodestatus
c
		nodestatus(ncur+1)=2
		nodestatus(ncur+2)=2
		if (nodepop(ncur+1).le.ndsize) nodestatus(ncur+1)=-1
		if (nodepop(ncur+2).le.ndsize) nodestatus(ncur+2)=-1
		popt1=0
		popt2=0
		do j=1,nclass
			popt1=popt1+classpop(j,ncur+1)
			popt2=popt2+classpop(j,ncur+2)
		enddo
		do j=1,nclass
			if (abs(classpop(j,ncur+1)-popt1)
     &			 .lt.8.232D-11) nodestatus(ncur+1)=-1
			if (abs(classpop(j,ncur+2)-popt2)
     &			 .lt.8.232D-11) nodestatus(ncur+2)=-1
		enddo
		treemap(1,kbuild)=ncur+1
		treemap(2,kbuild)=ncur+2
		parent(ncur+1)=kbuild
		parent(ncur+2)=kbuild
		nodestatus(kbuild)=1
		ncur=ncur+2
		if (ncur.ge.nrnodes) goto 50
30	continue
50	continue
	ndbigtree=nrnodes
	do k=nrnodes,1,-1
		if (nodestatus(k).eq.0) ndbigtree=ndbigtree-1
		if (nodestatus(k).eq.2) nodestatus(k)=-1
	enddo
	do kn=1,ndbigtree
		if(nodestatus(kn).eq.-1) then
			pp=0
			do j=1,nclass
				if(classpop(j,kn).gt.pp) then
					nodeclass(kn)=j
					pp=classpop(j,kn)
				endif
			enddo
		endif
	enddo
	end
c
c	-------------------------------------------------------
	subroutine findbestsplit(a,b,cl,mdim,nsample,nclass,cat,
     &  ndstart,ndend,tclasspop,tclasscat,msplit,decsplit,nbest,
     &  ncase,jstat,mtry,win,wr,wl,kcat,ncatsplit,xc,dn,
     &	cp,cm,maxcat,msm,mdimt,iseed,ncsplit,ncmax)
c
c	For the best split,msplit is the variable split on. decsplit is the dec. in impurity.
c	If msplit is numerical,nsplit is the case number of value of msplit split on,
c	and nsplitnext is the case number of the next larger value of msplit.  If msplit is
c	categorical,then nsplit is the coding into an integer of the categories going left.
c
	integer a(mdim,nsample),b(mdim,nsample),iseed,ncsplit,ncmax
c
	integer cl(nsample),cat(mdim),ncase(nsample),msm(mdim),
     &	kcat(maxcat),ncatsplit(maxcat),icat(32)
c
	integer mdim,nsample,nclass,ndstart,ndend,mdimt,mtry,
     &	msplit,nbest,jstat,maxcat,i,j,k,mv,mvar,nc,
     &	lcat,nnz,nhit,ncatsp,nsp
c
	real tclasspop(nclass),tclasscat(nclass,maxcat),
     &	win(nsample),wr(nclass),wl(nclass),xc(maxcat),
     &	dn(maxcat),cp(maxcat),cm(maxcat)
c
	real decsplit,pno,pdo,rrn,rrd,rln,rld,u,
     &	crit0,critmax,crit,su
c
	real randomu
c
	external unpack
c
c	compute initial values of numerator and denominator of Gini
	pno=0
	pdo=0
	do j=1,nclass
		pno=pno+tclasspop(j)*tclasspop(j)
		pdo=pdo+tclasspop(j)
	enddo
	crit0=pno/pdo
	jstat=0
c	start main loop through variables to find best split
	critmax=-1.0e20
c	
	do 20 mv=1,mtry
		k=int(mdimt*randomu())+1
		mvar=msm(k)
		    if(cat(mvar).eq.1) then
c			it's not a categorical variable:		
			rrn=pno
			rrd=pdo
			rln=0
			rld=0
			call zervr(wl,nclass)
			do j=1,nclass
				wr(j)=tclasspop(j)
			enddo
			do nsp=ndstart,ndend-1
				nc=a(mvar,nsp)
				u=win(nc)
				k=cl(nc)
				rln=rln+u*(2*wl(k)+u)
				rrn=rrn+u*(-2*wr(k)+u)
				rld=rld+u
				rrd=rrd-u
				wl(k)=wl(k)+u
				wr(k)=wr(k)-u
  				if (b(mvar,nc).lt.b(mvar,a(mvar,nsp+1))) then
					if(amin1(rrd,rld).gt.1.0e-5) then
						crit=(rln/rld)+(rrn/rrd)
						if (crit.gt.critmax) then
							nbest=nsp
							critmax=crit
							msplit=mvar
							
						endif
					endif
				endif
			enddo
			
 		else
c			it's a categorical variable:		
c			compute the decrease in impurity given by categorical splits
			lcat=cat(mvar)
			call zermr(tclasscat,nclass,maxcat)
			do nsp=ndstart,ndend
				nc=ncase(nsp)
				k=a(mvar,ncase(nsp))
				tclasscat(cl(nc),k)=tclasscat(cl(nc),k)+win(nc)
			enddo
			nnz=0
			do i=1,lcat
				su=0
				do j=1,nclass
					su=su+tclasscat(j,i)
				enddo
				dn(i)=su
				nnz=nnz+1
			enddo
			if (nnz.eq.1) then
				critmax=-1.0e25
				goto 20
			endif
			if(lcat.lt.ncmax) then
				call catmax(pdo,tclasscat,tclasspop,nclass,lcat,
     & 				ncatsp,critmax,nhit,maxcat)
				if(nhit.eq.1) then
					msplit=mvar
					call unpack(lcat,ncatsp,icat)
					call zerv(ncatsplit,maxcat)
					do k=1,lcat
						ncatsplit(k)=icat(k)
					enddo
				endif
			else 
				call catmaxr(ncsplit,tclasscat,tclasspop,icat,
     &				nclass,lcat,maxcat,ncatsplit,critmax,pdo,nhit,
     &				iseed)
				if(nhit.eq.1)then
					msplit=mvar
				endif
			endif
		endif !cat
20	continue
25	continue
	decsplit=critmax-crit0
	if (critmax.lt.-1.0e10) jstat=1
	end
c
c	-------------------------------------------------------
	subroutine catmaxr(ncsplit,tclasscat,tclasspop,icat,
     &	nclass,lcat,maxcat,ncatsplit,critmax,pdo,nhit,iseed)
c
c	this routine takes the best of ncsplit random splits
c
	real tclasscat(nclass,maxcat),tclasspop(nclass),tmpclass(100)
	real critmax,pdo
	integer icat(32),iseed
	integer ncsplit,nclass,lcat,maxcat,ncatsplit(maxcat),nhit
c
	integer irbit
	real pln,pld,prn,tdec
	integer j,n,i,k
c
	nhit=0
	do n=1,ncsplit
c		generate random split
		do k=1,lcat
			icat(k)=irbit(iseed)	!icat(k) is bernouilli
		enddo
		do j=1,nclass
			tmpclass(j)=0
			do k=1,lcat
				if(icat(k).eq.1) then
					tmpclass(j)=tmpclass(j)+tclasscat(j,k)
				endif
			enddo
		enddo
		pln=0
		pld=0
		do j=1,nclass
			pln=pln+tmpclass(j)*tmpclass(j)
			pld=pld+tmpclass(j)
		enddo
		prn=0
		do j=1,nclass
			tmpclass(j)=tclasspop(j)-tmpclass(j)
			prn=prn+tmpclass(j)*tmpclass(j)
		enddo
		tdec=(pln/pld)+(prn/(pdo-pld))
		if (tdec.gt.critmax) then
			critmax=tdec
			nhit=1
			do k=1,lcat
				ncatsplit(k)=icat(k)
			enddo
		endif
	enddo
	end
c
c	-------------------------------------------------------
	subroutine catmax(pdo,tclasscat,tclasspop,nclass,lcat,
     &  ncatsp,critmax,nhit,maxcat)
c
c	this finds the best split of a categorical variable
c	with lcat categories and nclass classes, where 
c	tclasscat(j,k) is the number of cases in
c	class j with category value k. The method uses an 
c	exhaustive search over all partitions of the category 
c	values. For the two class problem,there is a faster 
c	exact algorithm. If lcat.ge.10,the exhaustive search
c	gets slow and there is a faster iterative algorithm.
	real tclasscat(nclass,maxcat),tclasspop(nclass),tmpclass(100)
	integer icat(32),n,lcat,nhit,l,j,ncatsp,nclass,maxcat
	real critmax,pdo,pln,pld,prn,tdec
c
	external unpack
	nhit=0
	do n=1,(2**(lcat-1))-1
		call unpack(lcat,n,icat)
		do j=1,nclass
			tmpclass(j)=0
			do l=1,lcat
				if(icat(l).eq.1) then
					tmpclass(j)=tmpclass(j)+tclasscat(j,l)
				endif
			enddo
		enddo
		pln=0
		pld=0
		do j=1,nclass
			pln=pln+tmpclass(j)*tmpclass(j)
			pld=pld+tmpclass(j)
		enddo
		prn=0
		do j=1,nclass
			tmpclass(j)=tclasspop(j)-tmpclass(j)
			prn=prn+tmpclass(j)*tmpclass(j)
		enddo
		tdec=(pln/pld)+(prn/(pdo-pld))
		if (tdec.gt.critmax) then
			critmax=tdec
			ncatsp=n
			nhit=1
		endif
	enddo
	end
c
c	-------------------------------------------------------
	subroutine movedata(a,ta,mdim,nsample,ndstart,ndend,idmove,
     &  ncase,msplit,cat,nbest,ndendl,ncatsplit,maxcat,mdimt,msm)
c
c	movedata is the heart of the buildtree construction. 
c	Based on the best split the data corresponding to the 
c	current node is moved to the left if it belongs to the 
c	left child and right if it belongs to the right child.
	integer a(mdim,nsample),ta(nsample),idmove(nsample),
     &  ncase(ndend),cat(mdim),ncatsplit(maxcat),msm(mdimt)
	integer mdim,ndstart,ndend,nsample,msplit,nbest,ndendl
	integer maxcat,mdimt,nsp,nc,ms,msh,k,n,ih
c	compute idmove=indicator of case nos. going left
c
	if (cat(msplit).eq.1) then
		do nsp=ndstart,nbest
			nc=a(msplit,nsp)
			idmove(nc)=1
		enddo
		do nsp=nbest+1,ndend
			nc=a(msplit,nsp)
			idmove(nc)=0
		enddo
		ndendl=nbest
	else
		ndendl=ndstart-1
		do nsp=ndstart,ndend
			nc=ncase(nsp)
			if (ncatsplit(a(msplit,nc)).eq.1) then
				idmove(nc)=1
				ndendl=ndendl+1
			else
				idmove(nc)=0
			endif
		enddo
	endif
	
c	 shift case. nos. right and left for numerical variables.	
	
	do ms=1,mdimt
		msh=msm(ms)
		if (cat(msh).eq.1) then
			k=ndstart-1
			do n=ndstart,ndend
				ih=a(msh,n)
				if (idmove(ih).eq.1) then
					k=k+1
					ta(k)=a(msh,n)
				endif
			enddo
			do n=ndstart,ndend
				ih=a(msh,n)
				if (idmove(ih).eq.0) then 
					k=k+1
					ta(k)=a(msh,n)
				endif
			enddo
			do k=ndstart,ndend
				a(msh,k)=ta(k)
			enddo
		endif
	enddo

c	 compute case nos. for right and left nodes.
	
	if (cat(msplit).eq.1) then
		do n=ndstart,ndend
			ncase(n)=a(msplit,n)
		enddo
	else
		k=ndstart-1
		do n=ndstart,ndend
			if (idmove(ncase(n)).eq.1) then
				k=k+1
				ta(k)=ncase(n)
			endif
		enddo
		do n=ndstart,ndend
			if (idmove(ncase(n)).eq.0) then
				k=k+1
				ta(k)=ncase(n)
			endif
		enddo
		do k=ndstart,ndend
			ncase(k)=ta(k)
		enddo
	endif
	end

c
c	-------------------------------------------------------
	subroutine xtranslate(x,mdim,nrnodes,nsample,bestvar,
     &  bestsplit,bestsplitnext,xbestsplit,nodestatus,cat,
     &	ndbigtree)
c
c	xtranslate takes the splits on numerical variables and translates them
c	back into x-values.  It also unpacks each categorical split into a 32-
c	dimensional vector with components of zero or one--a one indicates 
c	that the corresponding category goes left in the split.
c
	integer cat(mdim),bestvar(nrnodes),bestsplitnext(nrnodes),
     &	nodestatus(nrnodes),bestsplit(nrnodes)
	real x(mdim,nsample),xbestsplit(nrnodes)
	integer mdim,nrnodes,nsample,ndbigtree,k,m
c
	do k=1,ndbigtree
		if (nodestatus(k).eq.1) then
			m=bestvar(k)
			if (cat(m).eq.1) then
				xbestsplit(k)=(x(m,bestsplit(k))+
     &				x(m,bestsplitnext(k)))/2
			else
				xbestsplit(k)=real(bestsplit(k))
			endif
		endif
	enddo
	end
c
c	-------------------------------------------------------
	subroutine getweights(x,nsample,mdim,treemap,nodestatus,
     &  xbestsplit,bestvar,nrnodes,ndbigtree,
     &	cat,maxcat,nbestcat,jin,win,tw,tn,tnodewt)
c
	real x(mdim,nsample),xbestsplit(nrnodes),
     &	win(nsample),tw(ndbigtree),tn(ndbigtree),tnodewt(ndbigtree)
	integer nsample,mdim,nrnodes,ndbigtree,maxcat
	integer treemap(2,nrnodes),bestvar(nrnodes),
     &  cat(mdim),nodestatus(nrnodes),jin(nsample)
c
	integer nbestcat(maxcat,nrnodes)
	integer jcat,n,kt,k,m
	call zervr(tw,ndbigtree)
	call zervr(tn,ndbigtree)
	do n=1,nsample
		if(jin(n).ge.1) then
			kt=1
			do k=1,ndbigtree
				if (nodestatus(kt).eq.-1) then
					tw(kt)=tw(kt)+win(n)
					tn(kt)=tn(kt)+jin(n)
					goto 100
				endif
				m=bestvar(kt)
				if (cat(m).eq.1) then
					if (x(m,n).le.xbestsplit(kt)) then 
						kt=treemap(1,kt)
					else
						kt=treemap(2,kt)
					endif
				else
					jcat=nint(x(m,n))
					if (nbestcat(jcat,kt).eq.1) then
						kt=treemap(1,kt)
					else
						kt=treemap(2,kt)
					endif
				endif
			enddo
100			continue
		endif
	enddo
	do n=1,ndbigtree
		if(nodestatus(n).eq.-1) tnodewt(n)=tw(n)/tn(n)
	enddo
	end
c
c	-------------------------------------------------------
	subroutine testreebag(x,nsample,mdim,treemap,nodestatus,
     &  xbestsplit,bestvar,nodeclass,nrnodes,ndbigtree,kpop,
     &	cat,jtr,nodextr,maxcat,nbestcat,rpop,dgini,tgini,jin,
     &	wtx)
c
c	predicts the class of all objects in x
c
c	input:
	real x(mdim,nsample),xbestsplit(nrnodes),dgini(nrnodes),
     &	rpop(nrnodes),wtx(nsample)
	integer treemap(2,nrnodes),bestvar(nrnodes),
     &  nodeclass(nrnodes),cat(mdim),nodestatus(nrnodes),
     &	nbestcat(maxcat,nrnodes),jin(nsample),kpop(nrnodes)
c
	integer nsample,mdim,nrnodes,ndbigtree,maxcat
c
c	output:
	real tgini(mdim)
	integer jtr(nsample),nodextr(nsample)
c
c	local
	integer n,kt,k,m,jcat
c
	call zerv(jtr,nsample)
	call zerv(nodextr,nsample)
	call zervr(tgini,mdim)
	call zervr(rpop,nrnodes)
	call zerv(kpop,nrnodes)
c
	n=1
903	kt=1
	do k=1,ndbigtree
		if (nodestatus(kt).eq.-1) then
			jtr(n)=nodeclass(kt)
			nodextr(n)=kt
			if(jin(n).gt.0)then
			rpop(kt)=rpop(kt)+jin(n)
			kpop(kt)=kpop(kt)+1
			endif
			goto 100
		endif
		m=bestvar(kt)
		tgini(m)=tgini(m)+dgini(kt)
		if (cat(m).eq.1) then
			if (x(m,n).le.xbestsplit(kt)) then 
				kt=treemap(1,kt)
			else
				kt=treemap(2,kt)
			endif
		endif
		if(cat(m).gt.1) then
			jcat=nint(x(m,n))
			if (nbestcat(jcat,kt).eq.1) then
				kt=treemap(1,kt)
			else
				kt=treemap(2,kt)
			endif
		endif
	enddo !k
100	n=n+1
	if(n.le.nsample) goto 903
	
	do m=1,mdim
		tgini(m)=tgini(m)/nsample
	enddo
	
	end
c	
c	-------------------------------------------------------
	subroutine testreelite(xts,ntest,mdim,treemap,nodestatus,
     &  xbestsplit,bestvar,nodeclass,nrnodes,ndbigtree,
     &	cat,jts,maxcat,nbestcat,nodexts)
c
c	predicts the class of all objects in xts
c
c	input:
	real xts(mdim,ntest),xbestsplit(nrnodes)
	integer treemap(2,nrnodes),bestvar(nrnodes),nodeclass(nrnodes),
     &	cat(mdim),nodestatus(nrnodes),nbestcat(maxcat,nrnodes)
	integer ntest,mdim,nrnodes,ndbigtree,maxcat
c
c	output: 
	integer jts(ntest),nodexts(ntest)
c
	integer n,kt,k,m,jcat
c
	n=1
903	kt=1
	do k=1,ndbigtree
		if (nodestatus(kt).eq.-1) then
			jts(n)=nodeclass(kt)
			nodexts(n)=kt
			goto 100
		endif
		m=bestvar(kt)
		if (cat(m).eq.1) then
			if (xts(m,n).le.xbestsplit(kt)) then 
				kt=treemap(1,kt)
			else
				kt=treemap(2,kt)
			endif
		endif
		if(cat(m).gt.1) then
			jcat=nint(xts(m,n))
			if (nbestcat(jcat,kt).eq.1) then
				kt=treemap(1,kt)
			else
				kt=treemap(2,kt)
			endif
		endif
	enddo !k
100	n=n+1
	if(n.le.ntest) goto 903
	end
c
c	-------------------------------------------------------
	subroutine testreeimp(x,nsample,mdim,joob,pjoob,nout,mr,
     &	treemap,nodestatus,xbestsplit,bestvar,nodeclass,nrnodes,
     &	ndbigtree,cat,jvr,nodexvr,maxcat,nbestcat)
c
c	predicts the class of out-of-bag-cases for variable importance
c	also computes nodexvr
c
c	input:
	real x(mdim,nsample),xbestsplit(nrnodes)
	integer treemap(2,nrnodes),bestvar(nrnodes),nodeclass(nrnodes),
     &	cat(mdim),nodestatus(nrnodes),nbestcat(maxcat,nrnodes),
     &	joob(nout),pjoob(nout)
	integer nsample,mdim,nout,mr,nrnodes,ndbigtree,maxcat
c
c	output:
	integer jvr(nout),nodexvr(nout)
c
	integer n,kt,k,m,jcat
	real xmn
c
	call permobmr(joob,pjoob,nout)
	n=1
904	kt=1
	do k=1,ndbigtree
		if (nodestatus(kt).eq.-1) then
			jvr(n)=nodeclass(kt)
			nodexvr(n)=kt
			goto 100
		endif
		m=bestvar(kt)
		if(m.eq.mr) then
			xmn=x(m,pjoob(n)) ! permuted value
		else
			xmn=x(m,joob(n))
		endif
		if (cat(m).eq.1) then
			if (xmn.le.xbestsplit(kt)) then 
				kt=treemap(1,kt)
			else
				kt=treemap(2,kt)
			endif
		endif
		if(cat(m).gt.1) then
			jcat=nint(xmn)
			if (nbestcat(jcat,kt).eq.1) then
				kt=treemap(1,kt)
			else
				kt=treemap(2,kt)
			endif
		endif
	enddo !k
100	n=n+1
	if(n.le.nout) goto 904
	end
c
c	-------------------------------------------------------
	subroutine permobmr(joob,pjoob,nout)
c
c	randomly permute the elements of joob and put them in pjoob
c
c	input:
	integer joob(nout),nout
c	output:
	integer pjoob(nout)
c	local:
	integer j,k,jt
	real rnd,randomu
c
	do j=1,nout
		pjoob(j)=joob(j)
	enddo 
	j=nout
11	rnd=randomu()
	k=int(j*rnd)
	if(k.lt.j) k=k+1
c	switch j and k
	jt=pjoob(j)
	pjoob(j)=pjoob(k)
	pjoob(k)=jt
	j=j-1
	if(j.gt.1) go to 11
	end
c
c	-------------------------------------------------------
	subroutine comperrtr(q,cl,nsample,nclass,errtr,
     &  tmiss,nc,jest,out)
c
	integer cl(nsample),nc(nclass),jest(nsample),out(nsample)
	real q(nclass,nsample),tmiss(nclass),errtr
	integer nsample,nclass
	real cmax,ctemp
	integer n,j,jmax
	call zervr(tmiss,nclass)
	errtr=0
	do n=1,nsample
		cmax=0
		if(out(n).gt.0) then
		do j=1,nclass
			ctemp=q(j,n)/out(n)
			if(ctemp.gt.cmax) then
				jmax=j
				cmax=ctemp
			endif
		enddo
		else
		jmax=1
		endif
		jest(n)=jmax
		if (jmax.ne.cl(n)) then
			tmiss(cl(n))=tmiss(cl(n))+1
			errtr=errtr+1
		endif
	enddo
	errtr=errtr/nsample
	do j=1,nclass
		tmiss(j)=tmiss(j)/nc(j)
	enddo
	end
c
c	-------------------------------------------------------
	subroutine comperrts(qts,clts,ntest,nclass,errts,
     &  tmissts,ncts,jests,labelts)
c
c
	integer clts(ntest),ncts(nclass),jests(ntest)
	real qts(nclass,ntest),tmissts(nclass)
	integer ntest,nclass,labelts
	real errts,cmax
	integer n,j,jmax
	call zervr(tmissts,nclass)
	errts=0
	do n=1,ntest
		cmax=0
		do j=1,nclass
			if (qts(j,n).gt.cmax) then
				jmax=j
				cmax=qts(j,n)
			endif
		enddo
		jests(n)=jmax
		if(labelts.eq.1) then
			if (jmax.ne.clts(n)) then
				tmissts(clts(n))=tmissts(clts(n))+1
				errts=errts+1
			endif
		endif
	enddo
	if(labelts.eq.1) then
		errts=errts/ntest
		do j=1,nclass
			tmissts(j)=tmissts(j)/ncts(j)
		enddo
	endif
	end
c
c	-------------------------------------------------------
	subroutine createclass(x,cl,ns,nsample,mdim)
c
	real x(mdim,nsample)
	integer cl(nsample)
	integer ns,nsample,mdim
	real randomu
	integer n,m,k
c
	do n=1,ns
		cl(n)=1
	enddo
	do n=ns+1,nsample
		cl(n)=2
	enddo
	do n=ns+1,nsample
		do m=1,mdim
			k=int(randomu()*ns)
			if(k.lt.ns) k=k+1
			x(m,n)=x(m,k)
		enddo
	enddo
	end
c
c	-------------------------------------------------------
	subroutine varimp(x,nsample,mdim,cl,nclass,jin,jtr,impn,
     &	interact,msm,mdimt,qimp,qimpm,avimp,sqsd,
     &	treemap,nodestatus,xbestsplit,bestvar,nodeclass,nrnodes,
     &	ndbigtree,cat,jvr,nodexvr,maxcat,nbestcat,tnodewt,
     &	nodextr,joob,pjoob,iv)
c
	real x(mdim,nsample),xbestsplit(nrnodes),
     &	avimp(mdim),sqsd(mdim),
     &	qimp(nsample),qimpm(nsample,mdim),tnodewt(nrnodes)
	integer cl(nsample),jin(nsample),jtr(nsample),
     &	msm(mdimt),treemap(2,nrnodes),nodestatus(nrnodes),
     &	bestvar(nrnodes),nodeclass(nrnodes),cat(mdim),jvr(nsample),
     &	nodexvr(nsample),nbestcat(maxcat,nrnodes),
     &	nodextr(nsample),joob(nsample),pjoob(nsample),iv(mdim)
	integer nsample,mdim,nrnodes,ndbigtree,maxcat,
     &	nclass,impn,interact,mdimt
	integer nout,mr,nn,n,jj,k
	real right,rightimp
c
	nout=0
	right=0
	do n=1,nsample
	if(jin(n).eq.0) then
c		this case is out-of-bag
c		update count of correct oob classifications
c		(jtr(n)=cl(n) if case n is correctly classified)
		if(jtr(n).eq.cl(n)) right=right+tnodewt(nodextr(n))
c		nout=number of obs out-of-bag for THIS tree
		nout=nout+1
		joob(nout)=n
	endif
	enddo
	if(impn.eq.1) then
		do n=1,nout
			nn=joob(n)
			if(jtr(nn).eq.cl(nn)) then
			qimp(nn)=qimp(nn)+tnodewt(nodextr(nn))/nout
			endif
		enddo
	endif
	call zerv(iv,mdim)
	do jj=1,ndbigtree
c		iv(j)=1 if variable j was used to split on
		if(nodestatus(jj).ne.-1) iv(bestvar(jj))=1
	enddo
	do k=1,mdimt
		mr=msm(k)
c		choose only those that used a split on variable mr 
		if(iv(mr).eq.1) then
			call testreeimp(x,nsample,mdim,joob,pjoob,nout,mr,
     &			treemap,nodestatus,xbestsplit,bestvar,nodeclass,nrnodes,
     &			ndbigtree,cat,jvr,nodexvr,maxcat,nbestcat)
			rightimp=0
			do n=1,nout
c				the nth out-of-bag case is the nnth original case
				nn=joob(n)
				if(impn.eq.1) then
					if(jvr(n).eq.cl(nn)) then
						qimpm(nn,mr)=qimpm(nn,mr)+
     &						tnodewt(nodexvr(n))/nout
					endif
				endif
				if(jvr(n).eq.cl(nn)) rightimp=rightimp+
     &						tnodewt(nodexvr(n))
			enddo
			avimp(mr)=avimp(mr)+(right-rightimp)/nout
			sqsd(mr)=sqsd(mr)+((right-rightimp)**2)/(nout**2)
		else
			do n=1,nout
c				the nth out-of-bag case is 
c				the nnth original case
				nn=joob(n)
				if(impn.eq.1) then
					if(jtr(nn).eq.cl(nn)) then
						qimpm(nn,mr)=qimpm(nn,mr)+
     &						tnodewt(nodextr(nn))/nout
					endif
				endif
			enddo
		endif
	enddo !k
	end
c
c	-------------------------------------------------------
	subroutine finishimp(mdim,sqsd,avimp,signif,zscore,
     &	jbt,mdimt,msm)
c
	real sqsd(mdim),avimp(mdim),zscore(mdim),signif(mdim)
   	integer msm(mdim)
	integer mdim,mdimt,k,m1,jbt
	real v,av,se
	real erfcc
	do k=1,mdimt
		m1=msm(k)
		avimp(m1)=avimp(m1)/jbt
		av=avimp(m1)
		se=(sqsd(m1)/jbt)-av*av
		se=sqrt(se/jbt)
		if(se.gt.0.0) then
			zscore(m1)=avimp(m1)/se
			v=zscore(m1)
			signif(m1)=erfcc(v)
		else
			zscore(m1)=-5
			signif(m1)=1
		endif
	enddo
	end
c
c	-------------------------------------------------------
	subroutine compinteract(votes,effect,msm,mdim,mdimt,
     &	jbt,g,iv,irnk,hist,teffect)
c
	real votes(mdim,jbt),effect(mdim,mdim),g(mdim),
     &	hist(0:mdim,mdim),teffect(mdim,mdim)
	integer msm(mdimt),iv(mdim),irnk(mdim,jbt)
	integer mdim,mdimt,jbt,jb,i,nt,irk,j,ii,
     &  jj,ij,mmin,m,k
	real gmin,rcor
	do jb=1,jbt
		nt=0
		call zerv(iv,mdim)
		do i=1,mdimt
			m=msm(i)
			g(m)=votes(m,jb)
			if(abs(g(m)).lt.8.232D-11) then
				irnk(m,jb)=0
				iv(m)=1
				nt=nt+1
			endif
		enddo
		irk=0
		do j=1,8000
			gmin=10000
			do i=1,mdimt
				m=msm(i)
				if(iv(m).eq.0.and.g(m).lt.gmin) then
					gmin=g(m)
					mmin=m
				endif
			enddo
			iv(mmin)=1
			irk=irk+1
			irnk(mmin,jb)=irk
			nt=nt+1
			if(nt.ge.mdimt) goto 79
		enddo !j
79		continue
	enddo !jb
	do j=0,mdimt
		do i=1,mdimt
			m=msm(i)
			hist(j,m)=0
		enddo
	enddo
	do i=1,mdimt
		m=msm(i)
		do jb=1,jbt
			hist(irnk(m,jb),m)=hist(irnk(m,jb),m)+1
		enddo
		do j=0,mdimt
			hist(j,m)=hist(j,m)/jbt
		enddo
	enddo !m
	
	call zermr(effect,mdim,mdim)
	do i=1,mdimt
		do j=1,mdimt
			m=msm(i)
			k=msm(j)
			do jb=1,jbt
				effect(m,k)=effect(m,k)+iabs(irnk(m,jb)-irnk(k,jb))
			enddo
			effect(m,k)=effect(m,k)/jbt
		enddo
	enddo
	call zermr(teffect,mdim,mdim)
	do i=1,mdimt
		do j=1,mdimt
			m=msm(i)
			k=msm(j)
			do ii=0,mdimt
				do jj=0,mdimt
					teffect(m,k)=teffect(m,k)+abs(ii-jj)*hist(jj,m)*hist(ii,k)
				enddo
			enddo
			rcor=0
			do ij=1,mdimt
				rcor=rcor+hist(ij,m)*hist(ij,k)
			enddo
			teffect(m,k)=teffect(m,k)/(1-rcor)
		enddo
	enddo

	do i=1,mdimt
		do j=1,mdimt
			m=msm(i)
			k=msm(j)
			effect(m,k)=100*(effect(m,k)-teffect(m,k))
		enddo
	enddo
	end
c
c	-------------------------------------------------------
	subroutine compprot(loz,nrnn,ns,mdim,its,
     & 	jest,wc,nclass,x,mdimt,msm,temp,cat,maxcat,
     & 	jpur,inear,nprot,protlow,prothigh,prot,protfreq,
     & 	protvlow,protvhigh,protv,popclass,npend,freq,v5,v95)
c
	integer nrnn,ns,mdim,nclass,mdimt,nprot,maxcat
	integer loz(ns,nrnn),jest(ns),msm(mdim),its(ns),
     & 	jpur(nrnn),inear(nrnn),npend(nclass),cat(mdim)
	real wc(ns),prot(mdim,nprot,nclass),
     & 	protlow(mdim,nprot,nclass),prothigh(mdim,nprot,nclass),
     &	protfreq(mdim,nprot,nclass,maxcat),
     & 	protvlow(mdim,nprot,nclass),protvhigh(mdim,nprot,nclass),
     &	x(mdim,ns),temp(nrnn),protv(mdim,nprot,nclass),
     & 	popclass(nprot,nclass),freq(maxcat),v5(mdim),v95(mdim)
	integer ii,i,k,n,jp,npu,mm,m,nclose,jj,ll,jmax,nn
	real fmax,dt


	do jp=1,nclass
		call zerv(its,ns)
c		we try to find nprot prototypes for this class:
		npend(jp)=nprot
		do i=1,nprot
			call zervr(wc,ns)
			do n=1,ns
				if(its(n).eq.0) then
c					wc(n) is the number of unseen neighbors 
c					of case n that are predicted to be 
c					in class jp
c					loz(n,1),...,loz(n,nrnn) point to 
c					the nrnn nearest neighbors of 
c					case n 
					do k=1,nrnn
						nn=loz(n,k)
						if(its(nn).eq.0) then
							ii=jest(nn)
							if(ii.eq.jp) wc(n)=wc(n)+1
						endif
					enddo
				endif
			enddo
c			find the unseen case with the largest number 
c			of unseen predicted-class-jp neighbors
			nclose=0
			npu=0
			do n=1,ns
				if(wc(n).ge.nclose.and.its(n).eq.0) then
					npu=n
					nclose=wc(n)
				endif
			enddo
c			if nclose=0,no case has any unseen predicted-class-jp neighbors
c			can't find another prototype for this class - reduce npend by 1 and
c			start finding prototypes for the next class
			if(nclose.eq.0) then
				npend(jp)=i-1
				goto 93
			endif
c			case npu has the largest number 
c			of unseen predicted-class-jp neighbors
c			put these neighbors in a list of length nclose
			ii=0	
			do k=1,nrnn
				nn=loz(npu,k)
				if(its(nn).eq.0.and.jest(nn).eq.jp) then
					ii=ii+1
					inear(ii)=nn	
				endif
			enddo
c			popclass is a measure of the size of the cluster around 
c			this prototype
			popclass(i,jp)=nclose
			do mm=1,mdimt
c				m is the index of the mmth variable
				m=msm(mm)	
				if(cat(m).eq.1) then
					dt=v95(m)-v5(m)
					do ii=1,nclose
c						put the value of the mmth variable into the list
						temp(ii)=x(m,inear(ii))
					enddo !ii
c					sort the list
					call quicksort(temp,jpur,1,nclose,nclose)
					ii=nclose/4
					if(ii.eq.0) ii=1
c					find the 25th percentile
					protvlow(m,i,jp)=temp(ii)
					protlow(m,i,jp)=(temp(ii)-v5(m))/dt
					ii=nclose/4
					ii=(3*nclose)/4
					if(ii.eq.0) ii=1
c					find the 75th percentile
					protvhigh(m,i,jp)=temp(ii)
					prothigh(m,i,jp)=(temp(ii)-v5(m))/dt
					ii=nclose/2
					if(ii.eq.0) ii=1
c					find the median
					protv(m,i,jp)=temp(ii)
					prot(m,i,jp)=(temp(ii)-v5(m))/dt
				endif	
				if(cat(m).ge.2) then
c					for categorical variables,choose the most frequent class
					call zervr(freq,maxcat)	
					do k=1,nclose
						jj=nint(x(m,loz(npu,k)))	
						freq(jj)=freq(jj)+1
					enddo	
					jmax=1
					fmax=freq(1)
					do ll=2,cat(m)
						if(freq(ll).gt.fmax) then
							jmax=ll
							fmax=freq(ll)
						endif
					enddo	
					protv(m,i,jp)=jmax
					protvlow(m,i,jp)=jmax
					protvhigh(m,i,jp)=jmax
					do ll=1,cat(m)
						protfreq(m,i,jp,ll)=freq(ll)
					enddo
				endif
			enddo !m
c			record that npu and it's neighbors have been 'seen'
			its(npu)=1
			do k=1,nclose
				nn=loz(npu,k)
				its(nn)=1
			enddo
		enddo !nprot
93		continue
	enddo !jp

	end
c
c	-------------------------------------------------------
	subroutine preprox(near,nrnodes,jbt,nodestatus,ncount,jb,
     &	nod,nodextr,nodexb,jin,jinb,ncn,ndbegin,kpop,rinpop,npcase,
     &	rpop,nsample)
c
     	integer near,nrnodes,jbt,jb,nsample,
     &	nodestatus(nrnodes),ncount(near,jbt),nod(nrnodes),
     &	nodextr(near),nodexb(near,jbt),jin(nsample),jinb(near,jbt),
     &	ncn(near),kpop(near),npcase(near,jbt),ndbegin(near,jbt)
     	real rpop(near),rinpop(near,jbt)
	integer n, ntt, k, nterm, kn
	
	do n=1,near
		ncount(n,jb)=0
		ndbegin(n,jb)=0
	enddo
	ntt=0
	do k=1,nrnodes
		if(nodestatus(k).eq.-1) then
			ntt=ntt+1
			nod(k)=ntt
		endif
	enddo
	nterm=ntt
	do n=1,near
		rinpop(n,jb)=rpop(nodextr(n))
		nodexb(n,jb)=nod(nodextr(n))
		jinb(n,jb)=jin(n)
		k=nodexb(n,jb)
		ncount(k,jb)=ncount(k,jb)+1
		ncn(n)=ncount(k,jb)
	enddo
	ndbegin(1,jb)=1
	do k=2,nterm+1
		ndbegin(k,jb)=ndbegin(k-1,jb)+ncount(k-1,jb)
	enddo
	do n=1,near
		kn=ndbegin(nodexb(n,jb),jb)+ncn(n)-1
		npcase(kn,jb)=n
	enddo
	end
c
c	-------------------------------------------------------
	subroutine comprox(prox,nodexb,jinb,ndbegin,
     &	npcase,ppr,rinpop,near,jbt,noutlier,outtr,cl,
     &	loz,nrnn,wtx,nsample,iwork,ibest)
c
	double precision prox(near,nrnn),ppr(near)
	real outtr(near),rinpop(near,jbt),wtx(nsample)
	integer nodexb(near,jbt),jinb(near,jbt),
     &	ndbegin(near,jbt),npcase(near,jbt),cl(nsample),
     &	loz(near,nrnn),iwork(near),ibest(nrnn),
     &	near,jbt,noutlier,nrnn,nsample
	integer n,jb,k,j,kk
	real rsq
c
	do n=1,near
		call zervd(ppr,near)
		do jb=1,jbt
			k=nodexb(n,jb)
			if(jinb(n,jb).gt.0) then
				do j=ndbegin(k,jb),ndbegin(k+1,jb)-1
					kk=npcase(j,jb)
					if(jinb(kk,jb).eq.0) then
					ppr(kk)=ppr(kk)+(wtx(n)/rinpop(n,jb))
					endif
     				enddo
			endif
			if(jinb(n,jb).eq.0) then
				do j=ndbegin(k,jb),ndbegin(k+1,jb)-1
					kk=npcase(j,jb)
					if(jinb(kk,jb).gt.0) then
					ppr(kk)=ppr(kk)+(wtx(kk)/rinpop(kk,jb))
					endif
     				enddo
			endif
		enddo !jbt
		if(noutlier.eq.1) then
			rsq=0
			do k=1,near
			if(ppr(k).gt.0.and.cl(k).eq.cl(n)) rsq=rsq+ppr(k)*ppr(k)
			enddo
			if(rsq.eq.0) rsq=1
			outtr(n)=near/rsq
		endif
	
		if(nrnn.eq.near) then
			do k=1,near
				prox(n,k)=ppr(k)
				loz(n,k)=k
			enddo
		else
			call biggest(ppr,near,nrnn,ibest,iwork)
			do k=1,nrnn
				prox(n,k)=ppr(ibest(k))
				loz(n,k)=ibest(k)
			enddo
		endif
	enddo !n
	end
c
c	------------------------------------------------------
	subroutine biggest(x,n,nrnn,ibest,iwork)
c
	double precision x(n)
	integer n,nrnn,ibest(nrnn),iwork(n)
	integer i,j,ihalfn,jsave
c
c	finds the nrnn largest values in the vector x and 
c	returns their positions in the vector ibest(1),...,ibest(nrnn):
c		x(ibest(1)) is the largest
c		...
c		x(ibest(nrnn)) is the nrnn-th-largest
c	the vector x is not disturbed 
c	the vector iwork is used as workspace
c
	ihalfn=int(n/2)
	do i=1,n
		iwork(i)=i
	enddo
	do j=1,ihalfn
		i=ihalfn + 1 - j
		call sift(x,iwork,n,n,i)
	enddo
	do j=1,nrnn-1
		i=n-j+1
		ibest(j)=iwork(1)
		jsave=iwork(i)
		iwork(i)=iwork(1)
		iwork(1)=jsave
		call sift(x,iwork,n,n-j,1)
	enddo
	ibest(nrnn)=iwork(1)
	end
c
c	------------------------------------------------------
	subroutine sift(x,iwork,n,m,i)
c
	double precision x(n)
	integer iwork(m),n,m,i
	real xsave
	integer j,k,jsave,ksave
c
c	used by subroutine biggest,to bring the largest element to the 
c	top of the heap
c
	xsave=x(iwork(i))
	ksave=iwork(i)
	jsave=i
	j=i + i
	do k=1,m
		if( j.gt.m ) goto 10
		if( j.lt.m ) then
			if( x(iwork(j)).lt.x(iwork(j+1)) ) j=j + 1
		endif
		if( xsave.ge.x(iwork(j)) ) goto 10
		iwork(jsave)=iwork(j)
		jsave=j
		j=j + j
	enddo
10	continue
	iwork(jsave)=ksave
	return
	end
c
c	------------------------------------------------------
	subroutine locateout(cl,tout,outtr,ncp,isort,devout,
     &	near,nsample,nclass,rmedout)
c
	real outtr(near),tout(near),devout(nclass),rmedout(nclass)
     	integer cl(nsample),isort(nsample),ncp(near),near,nsample,
     &	nclass
	real rmed, dev
	integer jp,nt,n,i
     
	do jp=1,nclass
		nt=0
		do n=1,near
			if(cl(n).eq.jp) then
				nt=nt+1
				tout(nt)=outtr(n)
				ncp(nt)=n
			endif
		enddo
		call quicksort(tout,isort,1,nt,nsample)
		rmed=tout((1+nt)/2)
		dev=0
		do i=1,nt
			dev=dev+amin1(abs(tout(i)-rmed),5*rmed)
		enddo
		dev=dev/nt
		devout(jp)=dev
		rmedout(jp)=rmed
		do i=1,nt
			outtr(ncp(i))=amin1((outtr(ncp(i))-rmed)/dev,20.0)
		enddo
	enddo !jp
	end

c	-------------------------------------------------------
	subroutine myscale(loz,prox,xsc,y,u,near,nscale,red,nrnn,
     &	ee,ev,dl)
c
	double precision prox(near,nrnn),y(near),u(near),dl(nscale),
     &	xsc(near,nscale),red(near),ee(near),ev(near,nscale),bl(10)
	integer loz(near,nrnn)
c
	integer near,nscale,nrnn,j,i,it,n,jit,k
	double precision dotd,y2,sred,eu,ru,ra,ynorm,sa
	do j=1,near
		ee(j)=dble(1.)
	enddo
c
	do j=1,near
		red(j)=0
		do i=1,nrnn
			red(j)=red(j)+prox(j,i)
		enddo
		red(j)=red(j)/near
	enddo
	sred=dotd(ee,red,near)
	sred=sred/near
	do it=1,nscale
		do n=1,near
			if(mod(n,2).eq.0) then
				y(n)=1
			else
				y(n)=-1
			endif
		enddo
		do jit=1,1000
			y2=dotd(y,y,near)
			y2=dsqrt(y2)
			do n=1,near
				u(n)=y(n)/y2
			enddo
			do n=1,near
				y(n)=0
				do k=1,nrnn
					y(n)=y(n)+prox(n,k)*u(loz(n,k))
				enddo
			enddo
			eu=dotd(ee,u,near)
			ru=dotd(red,u,near)
			do n=1,near
				y(n)=y(n)-(red(n)-sred)*eu-ru
				y(n)=.5*y(n)
			enddo
			if(it.gt.1) then
				do j=1,it-1
					bl(j)=0
					do n=1,near
						bl(j)=bl(j)+ev(n,j)*u(n)
					enddo
					do n=1,near
						y(n)=y(n)-bl(j)*dl(j)*ev(n,j)
					enddo
				enddo
			endif
			ra=dotd(y,u,near)
			ynorm=0
			do n=1,near
				ynorm=ynorm+(y(n)-ra*u(n))**2
			enddo
			sa=dabs(ra)
			if(ynorm.lt.sa*1.0e-7)then
				do n=1,near
					xsc(n,it)=(dsqrt(sa))*u(n)
					ev(n,it)=u(n)
				enddo
				dl(it)=ra
				goto 101
			endif
		enddo
101		continue
	enddo !nn
	end
c
c	-------------------------------------------------------

	subroutine xfill(x,nsample,mdim,fill,code)
c	
c	input:
	real code,fill(mdim)
	integer mdim,nsample
c	output:
	real x(mdim,nsample)
c	local:
	integer n,m
	do n=1,nsample
		do m=1,mdim
			if(abs(x(m,n)-code).lt.8.232D-11) 
     &				x(m,n)=fill(m)
		enddo !m
	enddo
	end
c
c	-------------------------------------------------------
	subroutine roughfix(x,v,ncase,mdim,nsample,cat,code,
     &	nrcat,maxcat,fill)
c
	real x(mdim,nsample),v(nsample),fill(mdim),code
	  integer ncase(nsample),cat(mdim),nrcat(maxcat)
	integer mdim,nsample,maxcat
	integer m,n,nt,j,jmax,lcat,nmax
	real rmed
c
	do m=1,mdim
		if(cat(m).eq.1) then
c			continuous variable
			nt=0
			do n=1,nsample
				if(abs(x(m,n)-code).ge.8.232D-11) then
					nt=nt+1
					v(nt)=x(m,n)
				endif
			enddo
	   		call quicksort (v,ncase,1,nt,nsample)
			if(nt.gt.0) then
				rmed=v((nt+1)/2)
			else
				rmed=0
			endif
			fill(m)=rmed
		else
c			categorical variable
			lcat=cat(m)
			call zerv(nrcat,maxcat)
			do n=1,nsample
				if(abs(x(m,n)-code).ge.8.232D-11) then
					j=nint(x(m,n))
					nrcat(j)=nrcat(j)+1
				endif
			enddo
			nmax=0
			jmax=1
			do j=1,lcat
				if(nrcat(j).gt.nmax) then
					nmax=nrcat(j)
					jmax=j
				endif
			enddo
			fill(m)=real(jmax)
		endif
	enddo !m
	do n=1,nsample
		do m=1,mdim
			if(abs(x(m,n)-code).lt.8.232D-11) x(m,n)=fill(m)
		enddo
	enddo
	end

c	-------------------------------------------------------
	subroutine impute(x,prox,near,mdim,
     &	maxcat,votecat,cat,nrnn,loz,missing)
c
	real x(mdim,near),votecat(maxcat)
	double precision  prox(near,nrnn)
	integer near,mdim,maxcat,nrnn
	integer cat(mdim),loz(near,nrnn),
     &	missing(mdim,near)
	integer i,j,jmax,m,n,k
	real sx,dt,rmax
c
	do m=1,mdim
		if(cat(m).eq.1) then
			do n=1,near
				if(missing(m,n).eq.1) then
					sx=0
					dt=0
					do k=1,nrnn
						if(missing(m,loz(n,k)).ne.1) then
							sx=sx+real(prox(n,k))*x(m,loz(n,k))
							dt=dt+real(prox(n,k))
						endif
					enddo
					if(dt.gt.0) x(m,n)=sx/dt
				endif
			enddo !n
		endif
	enddo !m
	do m=1,mdim
		if(cat(m).gt.1) then
			do n=1,near
				if(missing(m,n).eq.1) then
					call zervr(votecat,maxcat)
					do k=1,nrnn
						if (missing(m,loz(n,k)).ne.1) then
							j=nint(x(m,loz(n,k)))
							votecat(j)=votecat(j)+real(prox(n,k))
						endif
					enddo !k
					rmax=-1
					do i=1,cat(m)
						if(votecat(i).gt.rmax) then
							rmax=votecat(i)
							jmax=i
						endif
					enddo
					x(m,n)=real(jmax)
				endif
			enddo !n
		endif
	enddo !m
	end
c
c	-------------------------------------------------------
	subroutine checkin(labelts,labeltr,nclass,lookcls,jclasswt,
     &	mselect,mdim2nd,mdim,imp,impn,interact,nprox,nrnn,
     &	nsample,noutlier,nscale,nprot,missfill,iviz,isaverf,
     &	irunrf,isavepar,ireadpar,isavefill,ireadfill,isaveprox,
     &	ireadprox,isumout,idataout,impfastout,impout,interout,
     &	iprotout,iproxout,iscaleout,ioutlierout,cat,maxcat,cl)
c
	integer labelts,labeltr,nclass,lookcls,jclasswt,mselect,
     &	mdim2nd,mdim,imp,impn,interact,nprox,nrnn,nsample,noutlier,
     &	nscale,nprot,missfill,iviz,isaverf,irunrf,isavepar,ireadpar,
     &	isavefill,ireadfill,isaveprox,ireadprox,isumout,idataout,
     &	impfastout,impout,interout,iprotout,iproxout,iscaleout,
     &	ioutlierout,cat(mdim),maxcat,cl(nsample)
c
	integer n,m
c
	if(labelts.ne.0.and.labelts.ne.1) then
		write(*,*) 'error labelts',labelts
		stop
	endif
	if(labeltr.ne.0.and.labeltr.ne.1) then
		write(*,*) 'error labeltr',labeltr
		stop
	endif
	if(labeltr.eq.0.and.nclass.ne.2) then
		write(*,*) 'error,nclass should be 2 if labeltr=0'
		stop
	endif
	if(lookcls.ne.0.and.lookcls.ne.1) then
		write(*,*) 'error lookcls',lookcls
		stop
	endif
	if(jclasswt.ne.0.and.jclasswt.ne.1) then
		write(*,*) 'error jclasswt',jclasswt
		stop
	endif
	if(mselect.ne.0.and.mselect.ne.1) then
		write(*,*) 'error mselect',mselect
		stop
	endif
	if(mdim2nd.lt.0.or.mdim2nd.gt.mdim) then
		write(*,*) 'error mdim2nd',mdim2nd
		stop
	endif
	if(imp.ne.0.and.imp.ne.1) then
		write(*,*) 'error imp',imp
		stop
	endif
	if(impn.ne.0.and.impn.ne.1) then
		write(*,*) 'error impn',impn
		stop
	endif
	if(interact.ne.0.and.interact.ne.1) then
		write(*,*) 'error interact',interact
		stop
	endif
	if(nprox.lt.0.or.nprox.gt.1) then
		write(*,*) 'error nprox',nprox
		stop
	endif
	if(nrnn.lt.0.or.nrnn.gt.nsample) then
		write(*,*) 'error - nrnn',nrnn
		stop
	endif
	if(noutlier.lt.0.or.noutlier.gt.2) then
		write(*,*) 'error - noutlier',noutlier
		stop
	endif
	if(nscale.lt.0.or.nscale.gt.mdim) then
		write(*,*) 'error - nscale',nscale
		stop
	endif
	if(nprot.lt.0.or.nprot.gt.nsample) then
		write(*,*) 'error - nprot',nprot
		stop
	endif
	if(missfill.lt.0.or.missfill.gt.2) then
		write(*,*) 'error missfill',missfill
		stop
	endif
	if(iviz.ne.0.and.iviz.ne.1) then
		write(*,*) 'error iviz',iviz
		stop
	endif
	if(iviz.eq.1.and.impn.ne.1) then
		write(*,*) 'error iviz=1 and impn=',impn
		stop
	endif
	if(iviz.eq.1.and.imp.ne.1) then
		write(*,*) 'error iviz=1 and imp=',imp
		stop
	endif
	if(iviz.eq.1.and.nprox.ne.1) then
		write(*,*) 'error iviz=1 and nprox=',nprox
		stop
	endif
	if(iviz.eq.1.and.nscale.ne.3) then
		write(*,*) 'error iviz=1 and nscale=',nscale
		stop
	endif
	if(isaverf.ne.0.and.isaverf.ne.1) then
		write(*,*) 'error isaverf',isaverf
		stop
	endif
	if(isaverf.eq.1.and.missfill.eq.2) then
		write(*,*) 'error - only rough fix can be saved'
		stop
	endif
	if(irunrf.ne.0.and.irunrf.ne.1) then
		write(*,*) 'error irunrf',irunrf
		stop
	endif
	if(isavepar.ne.0.and.isavepar.ne.1) then
		write(*,*) 'error isavepar',isavepar
		stop
	endif
	if(ireadpar.ne.0.and.ireadpar.ne.1) then
		write(*,*) 'error ireadpar',ireadpar
		stop
	endif
	if(isavefill.ne.0.and.isavefill.ne.1) then
		write(*,*) 'error isavefill',isavefill
		stop
	endif
	if(ireadfill.ne.0.and.ireadfill.ne.1) then
		write(*,*) 'error ireadfill',ireadfill
		stop
	endif
	if(isaveprox.ne.0.and.isaveprox.ne.1) then
		write(*,*) 'error isaveprox',isaveprox
		stop
	endif
	if(ireadprox.ne.0.and.ireadprox.ne.1) then
		write(*,*) 'error ireadprox',ireadprox
		stop
	endif
	if(isumout.lt.0.or.isumout.gt.1) then
		write(*,*) 'error isumout',isumout
		stop
	endif
	if(idataout.lt.0.or.idataout.gt.2) then
		write(*,*) 'error idataout',idataout
		stop
	endif
	if(impfastout.lt.0.or.impfastout.gt.1) then
		write(*,*) 'error impfastout',impfastout
		stop
	endif
	if(impout.lt.0.or.impout.gt.2) then
		write(*,*) 'error impout',impout
		stop
	endif
	if(interout.lt.0.or.interout.gt.2) then
		write(*,*) 'error interout',interout
		stop
	endif
	if(iprotout.lt.0.or.iprotout.gt.2) then
		write(*,*) 'error iprotout',iprotout
		stop
	endif
	if(iproxout.lt.0.or.iproxout.gt.2) then
		write(*,*) 'error iproxout',iproxout
		stop
	endif
	if(iscaleout.lt.0.or.iscaleout.gt.1) then
		write(*,*) 'error iscaleout',iscaleout
		stop
	endif
	if(ioutlierout.lt.0.or.ioutlierout.gt.2) then
		write(*,*) 'error ioutlierout',ioutlierout
		stop
	endif
	if(noutlier.gt.0.and.nprox.eq.0) then
		write(*,*) 'error - noutlier>0 and nprox=0'
		stop
	endif
	if(nscale.gt.0.and.nprox.eq.0) then
		write(*,*) 'error - nscale>0 and nprox=0'
		stop
	endif
	if(nprot.gt.0.and.nprox.eq.0) then
		write(*,*) 'error - nprot>0 and nprox=0'
		stop
	endif
	if(mdim2nd.gt.0.and.imp.eq.0) then
		write(*,*) 'error - mdim2nd>0 and imp=0'
		stop
	endif
	if(impn.gt.0.and.imp.eq.0) then
		write(*,*) 'error - impn>0 and imp=0'
		stop
	endif
	do m=1,mdim
		if(cat(m).gt.maxcat) then
			write(*,*) 'error in cat',m,cat(m)
			stop
		endif
	enddo
	if(labeltr.eq.1) then
		do n=1,nsample
			if(cl(n).lt.1.or.cl(n).gt.nclass) then 
				write(*,*) 'error in class label',n,cl(n)
				stop
			endif
		enddo
	endif
	return
	end
c
c	-------------------------------------------------------
	subroutine quicksort(v,iperm,ii,jj,kk)
c
c	puts into iperm the permutation vector which sorts v into
c	increasing order.  only elementest from ii to jj are considered.
c	array iu(k) and array il(k) permit sorting up to 2**(k+1)-1 elements
c
c	this is a modification of acm algorithm #347 by r. c. singleton,
c	which is a modified hoare quicksort.
c
	real v(kk),vt,vtt
	integer t,tt,iperm(kk),iu(32),il(32)
	integer ii,jj,kk,m,i,j,k,ij,l
c
	m=1
	i=ii
	j=jj
 10   	if (i.ge.j) go to 80
 20   	k=i
	ij=(j+i)/2
	t=iperm(ij)
	vt=v(ij)
	if (v(i).le.vt) go to 30
	iperm(ij)=iperm(i)
	iperm(i)=t
	t=iperm(ij)
	v(ij)=v(i)
	v(i)=vt
	vt=v(ij)
 30   	l=j
	if (v(j).ge.vt) go to 50
	iperm(ij)=iperm(j)
	iperm(j)=t
	t=iperm(ij)
	v(ij)=v(j)
	v(j)=vt
	vt=v(ij)
	if (v(i).le.vt) go to 50
	iperm(ij)=iperm(i)
	iperm(i)=t
	t=iperm(ij)
	v(ij)=v(i)
	v(i)=vt
	vt=v(ij)
	go to 50
 40   	iperm(l)=iperm(k)
	iperm(k)=tt
	v(l)=v(k)
	v(k)=vtt
 50   	l=l-1
	if (v(l).gt.vt) go to 50
	tt=iperm(l)
	vtt=v(l)
 60   	k=k+1
	if (v(k).lt.vt) go to 60
	if (k.le.l) go to 40
	if (l-i.le.j-k) go to 70
	il(m)=i
	iu(m)=l
	i=k
	m=m+1
	go to 90
 70   	il(m)=k
	iu(m)=j
	j=l
	m=m+1
	go to 90
 80   	m=m-1
	if (m.eq.0) return
	i=il(m)
	j=iu(m)
 90   	if (j-i.gt.10) go to 20
	if (i.eq.ii) go to 10
	i=i-1
 100  	i=i+1
	if (i.eq.j) go to 80
	t=iperm(i+1)
	vt=v(i+1)
	if (v(i).le.vt) go to 100
	k=i
 110  	iperm(k+1)=iperm(k)
	v(k+1)=v(k)
	k=k-1
	if (vt.lt.v(k)) go to 110
	iperm(k+1)=t
	v(k+1)=vt
	go to 100
	end
c
c	-------------------------------------------------------
	subroutine unpack(l,npack,icat)
c
	integer icat(32),npack,l,j,n,k
	if(l.gt.32) then
		write(*,*) 'error in unpack,l=',l
		stop
	endif
	do j=1,32
		icat(j)=0
	enddo
	n=npack
	icat(1)=mod(n,2)
	do k=2,l
		n=(n-icat(k-1))/2
		icat(k)=mod(n,2)
	enddo
	end
c
c	-------------------------------------------------------
	subroutine zerv(ix,m1)
c
	integer ix(m1),m1,n
	do n=1,m1
		ix(n)=0
	enddo
	end
c
c	-------------------------------------------------------
	subroutine zervr(rx,m1)
c
	real rx(m1)
	integer m1,n
	do n=1,m1
		rx(n)=0
	enddo
	end
c
c	-------------------------------------------------------

	subroutine zervd(rx,m1)
c
	double precision rx(m1)
	integer m1,n
	do n=1,m1
		rx(n)=0
	enddo
	end
c	
c	________________________________________________________

	subroutine zerm(mx,m1,m2)
c
	integer mx(m1,m2),m1,m2,i,j
	do j=1,m2
		do i=1,m1
			mx(i,j)=0
		enddo
	enddo
	end
c
c	-------------------------------------------------------
	subroutine zermr(rx,m1,m2)
c
	real rx(m1,m2)
	integer m1,m2,i,j
	do j=1,m2
		do i=1,m1
			rx(i,j)=0
		enddo
	enddo
	end
c
c	-------------------------------------------------------
	subroutine zermd(rx,m1,m2)
c
	double precision rx(m1,m2)
	integer m1,m2,i,j
	do j=1,m2
		do i=1,m1
			rx(i,j)=0
		enddo
	enddo
	end
c
c	-------------------------------------------------------
	real function erfcc(x)
c
	real x,t,z
	z=abs(x)/1.41421356
	t=1./(1.+0.5*z)
	erfcc=t*exp(-z*z-1.26551223+t*(1.00002368+t*(.37409196+t*
     *	(.09678418+t*(-.18628806+t*(.27886807+t*(-1.13520398+t*
     *	(1.48851587+t*(-.82215223+t*.17087277)))))))))
	erfcc=erfcc/2
	if (x.lt.0.) erfcc=2.-erfcc
	return
	end
c
c	-------------------------------------------------------
	integer function irbit(iseed)
c
	integer iseed, ib1, ib2, ib5, ib18, mask
	parameter(ib1=1,ib2=2,ib5=16,ib18=131072,mask=ib1+ib2+ib5)
	if(iand(iseed,ib18).ne.0) then
		iseed=ior(ishft(ieor(iseed,mask),1),ib1)
		irbit=1
	else
		iseed=iand(ishft(iseed,1),not(ib1))
		irbit=0
	endif
	return
	end
c
c	-------------------------------------------------------
	real function randomu()
c
	double precision grnd,u
	u=grnd()
	randomu=real(u)
	end
c
c	-------------------------------------------------------
	real function rnorm(i)
c
	integer i
	real randomu
	rnorm=sqrt(-2*log(randomu()))*cos(6.283185*randomu())
	end
c
c	-------------------------------------------------------
	double precision function dotd(u,v,ns)
c
c	computes the inner product
c	input:
	double precision u(ns),v(ns)
	integer ns
c	local:
	integer n
	dotd=dble(0.0)
	do n=1,ns
		dotd=dotd+u(n)*v(n)
	enddo
	end
C**************************************************************************
* A C-program for MT19937: Real number version
*   genrand() generates one pseudorandom real number (double)
* which is uniformly distributed on [0,1]-interval,for each
* call. sgenrand(seed) set initial values to the working area
* of 624 words. Before genrand(),sgenrand(seed) must be
* called once. (seed is any 32-bit integer except for 0).
* Integer generator is obtained by modifying two lines.
*   Coded by Takuji Nishimura,considering the suggestions by
* Topher Cooper and Marc Rieffel in July-Aug. 1997.
*
* This library is free software; you can redistribute it and/or
* modify it under the terms of the GNU Library General Public
* License as published by the Free Software Foundation; either
* version 2 of the License,or (at your option) any later
* version.
* This library is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
* See the GNU Library General Public License for more details.
* You should have received a copy of the GNU Library General
* Public License along with this library; if not,write to the
* Free Foundation,Inc.,59 Temple Place,Suite 330,Boston,MA
* 02111-1307  USA
*
* Copyright (C) 1997 Makoto Matsumoto and Takuji Nishimura.
* When you use this,send an email to: matumoto@math.keio.ac.jp
* with an appropriate reference to your work.
*
* Fortran translation by Hiroshi Takano.  Jan. 13,1999.
************************************************************************
* This program uses the following non-standard intrinsics.
*   ishft(i,n): If n>0,shifts bits in i by n positions to left.
*		   If n<0,shifts bits in i by n positions to right.
*   iand (i,j): Performs logical AND on corresponding bits of i and j.
*   ior  (i,j): Performs inclusive OR on corresponding bits of i and j.
*   ieor (i,j): Performs exclusive OR on corresponding bits of i and j.
*
************************************************************************
	subroutine sgrnd(seed)
*
	implicit integer(a-z)
*
* 	Period parameters
	parameter(n    = 624)
*
	dimension mt(0:n-1)
*			   the array for the state vector
	common /block/mti,mt
	save   /block/
*
*	setting initial seeds to mt[n] using
*	the generator Line 25 of Table 1 in
*	[KNUTH 1981,The Art of Computer Programming
*	   Vol. 2 (2nd Ed.),pp102]
*
	mt(0)=iand(seed,-1)
	do 1000 mti=1,n-1
	  mt(mti)=iand(69069 * mt(mti-1),-1)
1000 	continue
*
	return
	end
************************************************************************
	double precision function grnd()
*
	implicit integer(a-z)
*
* 	Period parameters
	parameter(n    = 624)
	parameter(n1   = n+1)
	parameter(m    = 397)
	parameter(mata =-1727483681)
*						constant vector a
	parameter(umask=-2147483648)
*						most significant w-r bits
	parameter(lmask= 2147483647)
*						least significant r bits
* Tempering parameters
	parameter(tmaskb=-1658038656)
	parameter(tmaskc=-272236544)
*
	dimension mt(0:n-1)
*			   the array for the state vector
	common /block/mti,mt
	save   /block/
	data   mti/n1/
*			   mti==n+1 means mt[n] is not initialized
*
	dimension mag01(0:1)
	data mag01/0,mata/
	save mag01
*				mag01(x)=x * mata for x=0,1
*
	TSHFTU(y)=ishft(y,-11)
	TSHFTS(y)=ishft(y,7)
	TSHFTT(y)=ishft(y,15)
	TSHFTL(y)=ishft(y,-18)
*
	if(mti.ge.n) then
*			     generate n words at one time
	  if(mti.eq.n+1) then
*				    if sgrnd() has not been called,
	    call sgrnd(4357)
*					a default initial seed is used
	  endif
*
	  do 1000 kk=0,n-m-1
		y=ior(iand(mt(kk),umask),iand(mt(kk+1),lmask))
		mt(kk)=ieor(ieor(mt(kk+m),ishft(y,-1)),mag01(iand(y,1)))
 1000   continue
	  do 1100 kk=n-m,n-2
		y=ior(iand(mt(kk),umask),iand(mt(kk+1),lmask))
		mt(kk)=ieor(ieor(mt(kk+(m-n)),ishft(y,-1)),mag01(iand(y,1)))
 1100   continue
	  y=ior(iand(mt(n-1),umask),iand(mt(0),lmask))
	  mt(n-1)=ieor(ieor(mt(m-1),ishft(y,-1)),mag01(iand(y,1)))
	  mti=0
	endif
*
	y=mt(mti)
	mti=mti+1
	y=ieor(y,TSHFTU(y))
	y=ieor(y,iand(TSHFTS(y),tmaskb))
	y=ieor(y,iand(TSHFTT(y),tmaskc))
	y=ieor(y,TSHFTL(y))
*
	if(y.lt.0) then
		grnd=(dble(y)+2.0d0**32)/(2.0d0**32-1.0d0)
	else
		grnd=dble(y)/(2.0d0**32-1.0d0)
	endif
*
	return
	end
