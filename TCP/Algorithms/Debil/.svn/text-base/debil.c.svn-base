/******************************************************************************************
 *
 * Welcome to the DEBiL fitter  (Detached Eclipsing Binary Light-curve fitter)
 * Written by Jonathan Devor (CfA), 7 Oct. 2004
 *
 * This program fits a given light curve to a model of a binary star system
 * It uses the downhill simplex method (Nelder and Mead) with simulated annealing
 * for multidimensional continuous optimization (minimization)
 *
 * The fitter makes the following assumptions-
 *
 * 1. Both stars are spherical:
 *      - Detached binary system --> negligible tidal bulge (in Roche lobe)
 *      - Slow rotation --> negligible centripetal deformation
 *
 * 2. Both stars have a Sun-like photosphere:
 *      - Solar limb darkening --> proportional scaling in size and flux per area
 *         (from Astrophysical Quantities by C.W. Allen)
 *      - Detached binary system --> negligible gravity darkening
 *      - Homogeneous --> small star spots and flares
 *
 * Compile:  gcc debil.c -o debil -Wall -lm -O4
 * Run: debil p.txt p.out p.err
 *
 *******************************************************************************************/

#define VERSION "1.1"

// #define PLOT

#define GRAPHIC  // compile in graphic debugging mode (DOS)

#define WRITE_CURVE_FIT 500   // The number of fitted points to write

// Allow the period to be doubled (may cause erroneous fits with equal surface brightness)
#define DO_DOUBLE_PERIOD   

// If the period was doubled, assume that the dips are very similar and only fit r1<r2 (not r1>r2)
//#define DOUBLE_PERIOD_SHORTCUT

// Allocation of computational resources:
// The default number of iterations (used in amoeba(), greedyFit() and estimateError())
#define DEFAULT_NUM_ITERATIONS 10000
// In amoeba(), the last part of the convergence should have the best integration
#define MIN_STEP_ITERATION_FRACTION 0.2 // Fraction of simplex iterations
#define MIN_INTEGRATION_STEP 0.01  // This should be about 0.1 * sqrt(amp error)
// Should be much smaller than (KERNEL_HALF_WIDTH / size), especially when the fit is crude
#define SEARCH_STEP_SIZE  0.0001   

// Smoothing kernel parameter:
#define NUM_POINTS_HALF_KERNEL 8  // Must be smaller than a half a dip width, but at least 2

// Outlier identification parameter:
#define OUTLIER_VARIANCE_LIMIT 7.0  // "sigma clipping" 

//Eccentric anomaly calculation parameter:
#define ECC_ANOMALY_MAX_ERROR 1.0e-4  // Convergence threshold (average error is less than a third of this) 

// Eccentricity calculation parameter:
#define ECCENTRICITY_MAX_ERROR 1.0e-6   

// General bisection implementation parameter:
// only needed for pathological cases (e.g. overflows or huge roundoff errors)
#define BISECTION_SAFETY_MAX_ITERATIONS 1000 

// Quadratic limb darkening parameters:
#define DEFAULT_LIMB_QUAD_A 0.3542 // 0.282   [Claret 2003 // Claret 1998]
#define DEFAULT_LIMB_QUAD_B 0.1939 // 0.311

// Thermal fluctuation parameters:
#define INIT_TEMPERATURE 0.25  // Temperature (times Boltzmann's constant) at time=0
#define NUM_E_FOLD_COOL 15.0   // Final_temperature = INIT_TEMPERATURE * exp(-NUM_E_FOLD_COOL)

// "Greedy" fit parameters:
#define MAX_GREEDY_ITERATION_FRACTION 1.0 // Fraction of simplex iterations
#define GREEDY_CONVERGE_EPSILON 0.001
#define HALF_MAX_GREEDY_EPSILON 0.1

// Error estimation parameters:
#define MAX_ERROR_ESTIMATE_ITERATION_FRACTION 0.1 // Fraction of simplex iterations
#define ERROR_ESTIMATE_EPSILON 0.005   // Should be larger than GREEDY_CONVERGE_EPSILON

// Error thresholds:
#define MIN_STDDIV_BELOW_MEDIAN 0.0    // threshold for doubling the period (CAUTION)
#define MAX_STDDIV_ABOVE_MEDIAN 1.5    // warning only
// Minimum number of data points in the dips and in the plateau
#define MIN_NUM_DATA 5  // Must be at least a third of DIM

#define RANDOM_SEED 37435209

#define EPSILON 1.0e-9  // To avoid division by zero

// A useful constant for magnitude error conversion (2.5 / ln(10))
#define MAGNITUDE_ERROR_FACTOR 1.085736205

#ifdef GRAPHIC
#define PLOT_REFRESH_ITERATIONS 10
#endif

// ======================= Downhill simplex ================================

#define DIM 8  // The number of dimensions (don't change!)

// list of dimensions:
// physical-
#define D_ECC   0  // Eccentricity of orbit (e)
#define D_R1    1  // Star's radius (in units of the distance between them)
#define D_R2    2
#define D_B1    3  // Central surface brightness (flux per unit disk area)
#define D_B2    4
// orientation-
#define D_SIN_I 5  // sin(inclination)
#define D_TMO   6  // (time / 2) - (omega / 4pi)
#define D_TPO   7  // (time / 2) + (omega / 4pi)

// Time is the time (scan parameter) at perihelion and omega is the argument of perihelion
// (i.e. azimuth of eccentricity alignment
// Note that time and omega become degenerate for small eccentricities. For this
// reason I combined them into orthogonal parameters ,D_TMO and D_TPO, where at
// least the former can be accurately determined and therefor will probably converge
// much faster in the fitting algorithm.

// NOTE: [valid range of physical parameters]
//  0 <= time0 < 1       (not vital)
//  0 <= omega < 2*pi    (not vital)
//  0 < sin_i <= 1
//  0 <= e < 1           (closed orbit)
//  0 < r1 < 1-e         (prevent collisions)
//  0 < r2 < 1-e-r1      (prevent collisions)
//  0 < B1
//  0 < B2

// ==================== Includes ===================================

#include <math.h>
#include <stdio.h>  // For getc()
#include <stdlib.h> // For malloc() + qsort()
#include <values.h> // For MAXFLOAT
#include <float.h>
#include <string.h> // For memmove() + strlen() + strcmp()

#ifdef GRAPHIC
#ifdef PLOT
#include <graphics.h>
#include <conio.h> // For gotoxy()
#endif
#endif

// ================ General utility functions ======================


// Returns the square of a given x
double sqr (double x)
{
  return (x * x) ;
}

// Returns the cube of a given x
double cube (double x)
{
  return (x * x * x) ;
}


// Returns the modulo 1 value of x
double mod1 (double x)
{
  return (x - floor(x)) ;
}


// Swaps two given values
void swap (double *x1, double *x2)
{
  double tmp = *x1 ;
  *x1 = *x2 ;
  *x2 = tmp ;
}

// -----------------------

// Prints a given error message (errStr) reported by a given function (functionName) about a
// given light curve file (dataFilename). It is added to a given error repository file (errFilename)
// isFatal:  0 (a warning - try anyways)   1 (an error - go to next)
void printError (char *errFilename, int isFatal, char *dataFilename, char *functionName, char *errStr)
{
  FILE *ferr = fopen (errFilename, "at") ;

  if (!ferr)
    {
      printf ("%s: [ERROR] Couldn't open the output error file ('%s')\n", dataFilename, errFilename) ;
     
      if (isFatal)
	printf ("%s: [ERROR] %s - %s\n", dataFilename, functionName, errStr) ;
      else
	printf ("%s: [Warning] %s - %s\n", dataFilename, functionName, errStr) ;

      return ;
    }

  if (isFatal)
    fprintf (ferr, "%s: [ERROR] %s - %s\n", dataFilename, functionName, errStr) ;
  else
    fprintf (ferr, "%s: [Warning] %s - %s\n", dataFilename, functionName, errStr) ;

  fclose (ferr) ;
}


// =================== Removing outliers ==========================

// Performs one iteration of statistical summations
void updateVars (float x, float y,
		 double *A1, double *A2, double *A3, double *A4,
		 double *B0, double *B1, double *B2, double *C0)
{
  const double x2 = x * x ;

  (*A1) += x ;
  (*A2) += x2 ;
  (*A3) += x * x2 ;
  (*A4) += x2 * x2 ;
  (*B0) += y ;
  (*B1) += y * x ;
  (*B2) += y * x2 ;
  (*C0) += y * y ;
}


// Calculates a second order regression (parabola:  a*x^2 + b*x + c) fit to given data (time, amp)
// around a given instant (sampTime) going up and down by a certain number of data points
// to minimize round off errors, time[] is centered around sampTime and the results are corrected
// for the shift at the end.
// Assumes that the data are sorted in time
// Output: pointers to: a b c  and the variance around the fit (pVariance, if not null)
void regressionOrder2 (float sampTime, float *time, float *amp, int size, double *pa, double *pb, double *pc, double *pVariance)
{
  int i, indexDown = 0, indexUp = size - 1 ;
  int A0 = NUM_POINTS_HALF_KERNEL + NUM_POINTS_HALF_KERNEL ;
  double A1 = 0.0, A2 = 0.0, A3 = 0.0, A4 = 0.0 ;
  double B0 = 0.0, B1 = 0.0, B2 = 0.0, C0 = 0.0 ;
  double denom, a, b, c ;

  // Step 1: find the closes index above it
  // Step 1.1: run the bisection algorithm
  while ((indexDown + 1) < indexUp)
    {
      i = (indexDown + indexUp) / 2 ;

      if (time[i] > sampTime)
	indexUp = i ;
      else
	indexDown = i ;
    }

  // Step 1.2: take care of the ends
  if (time[indexDown] > sampTime)
    indexUp = 0 ;
  else
    if (time[indexUp] <= sampTime)
      indexDown = size - 1 ;


  // Step 2: do statistics
  if (indexUp < NUM_POINTS_HALF_KERNEL)
    {
      for (i = indexUp + size - NUM_POINTS_HALF_KERNEL ; i < size ; i++)
	updateVars (time[i] - 1.0 - sampTime, amp[i], &A1, &A2, &A3, &A4, &B0, &B1, &B2, &C0) ;

      for (i = 0 ; i < indexUp + NUM_POINTS_HALF_KERNEL ; i++)
	updateVars (time[i] - sampTime, amp[i], &A1, &A2, &A3, &A4, &B0, &B1, &B2, &C0) ;
    }
  else if (indexDown >= (size - NUM_POINTS_HALF_KERNEL))
    {
      for (i = indexDown + 1 - NUM_POINTS_HALF_KERNEL ; i < size ; i++)
	updateVars (time[i] - sampTime, amp[i], &A1, &A2, &A3, &A4, &B0, &B1, &B2, &C0) ;

      for (i = 0 ; i <= (indexDown + NUM_POINTS_HALF_KERNEL - size) ; i++)
	updateVars (time[i] + 1.0 - sampTime, amp[i], &A1, &A2, &A3, &A4, &B0, &B1, &B2, &C0) ;
    }
  else  // Normal case
    {
      for (i = indexUp - NUM_POINTS_HALF_KERNEL ; i < (indexUp + NUM_POINTS_HALF_KERNEL) ; i++)
	updateVars (time[i] - sampTime, amp[i], &A1, &A2, &A3, &A4, &B0, &B1, &B2, &C0) ;
    }

  denom = (A2 * ((A0*A4) + (2.0*A1*A3) - (A2*A2))) - (A0*A3*A3) - (A1*A1*A4) ;  // Denominator

  if (denom == 0.0)
    denom = EPSILON ;    // Prevents division by zero

  *pa = ((A0 * ((A2*B2) - (A3*B1))) + (A1 * ((A3*B0) - (A1*B2))) + (A2 * ((A1*B1) - (A2*B0)))) / denom ;
  *pb = ((A0 * ((A4*B1) - (A3*B2))) + (A1 * ((A2*B2) - (A4*B0))) + (A2 * ((A3*B0) - (A2*B1)))) / denom ;
  *pc = ((A1 * ((A3*B2) - (A4*B1))) + (A2 * ((A4*B0) - (A2*B2))) + (A3 * ((A2*B1) - (A3*B0)))) / denom ;

  if (pVariance)
    {
      a = *pa ;
      b = *pb ;
      c = *pc ;
      *pVariance = ((A4*a*a) + (2.0*a*b*A3) + (A2 * ((b*b) + (2.0*a*c))) + (2.0*b*c*A1) + (A0*c*c) - (2.0 * ((B2*a) + (B1*b) + (B0*c))) + C0) / (A0-3) ;
    }

  // Moves back the "zero point":  a(x-x0)^2 + b(x-x0) + c  -->  ax^2 + bx + c
  *pc += (((*pa) * sampTime * sampTime) - ((*pb) * sampTime)) ;
  *pb -= (2.0 * (*pa) * sampTime) ;
}


// Interpolates a 2nd order regression spline (parabola) and returns the amplitude at
// an arbitrary given value (sampTime)
// sampTime - moment to interpolate around (+/- kernelHalfWidth)
// time - input: array of time stamps (may be rearranged)
// amp - input: matching array of amplitudes (may be rearranged)
// size - size of input arrays
// Returns the 2nd order regression at the given point (sampTime)
double interpolateSmooth (double sampTime, float *time, float *amp, int size)
{
  double a, b, c ;

  regressionOrder2 (sampTime, time, amp, size, &a, &b, &c, 0) ;

  return ((a * sampTime * sampTime) + (b * sampTime) + c) ;
}



// Interpolates a 2nd order regression spline (fit to a parabola) and returns the
// time of a given amplitude (goal). It will return the closer (to sampTime) of the
// two solutions, as long as it's within SEARCH_STEP_SIZE
// sampTime - time to fit around
// time - input: array of time stamps (may be rearranged)
// amp - input: matching array of amplitudes (may be rearranged)
// size - size of input arrays
// Returns the nearest x-axis value of the fitted parabola for a given y-axis value
//  if it's out of range (sampTime +/- SEARCH_STEP_SIZE), returns sampTime
double findGoalSmooth (double sampTime, double goal, float *time, float *amp, int size)
{
  double a, b, c, D, x1, x2, x ;

  regressionOrder2 (sampTime, time, amp, size, &a, &b, &c, 0) ;

  D = (b*b) - (4.0 * a * (c - goal)) ;   // The determinant

  if ((D < 0.0) || (a == 0.0))
    return (sampTime) ;

  x1 = (-b + sqrt(D)) / (2.0 * a) ;
  x2 = (-b - sqrt(D)) / (2.0 * a) ;

  if (fabs(x1 - sampTime) < fabs(x2 - sampTime))
    x = x1 ;
  else
    x = x2 ;

  if (fabs(sampTime - x) > SEARCH_STEP_SIZE) // Should be less than half SEARCH_STEP_SIZE
    return (sampTime) ;

  return (mod1(x)) ;
}


// Removes the outliers from the input data array
// by comparing the data against a 2nd order regression spline.
// the data is assumed to be sorted by time (modulo period = phase)
// even when points are removes, the sorted order is maintained
// note that it will keep "lonely points" with no other data points near it
// time - input: array of time stamps
// amp - input: matching array of amplitudes
// size - size of input arrays
// *psize = outputs the new size of the array (will be reduced if outliers are found)
// Returns the chi2 around the spline (MAXFLOAT in case of error)
double ridOutliers (float *time, float *amp, float *err, int *psize)
{
  int index, doRid, numVariance ;
  double x, sumVariance, variance, varianceFit, sumChi2 ;
  double a, b, c ;

  do
    {
      doRid = 0 ;
      index = 0 ;
      numVariance = 0 ;
      sumVariance = 0.0 ;
      sumChi2 = 0.0 ;

      while (index < (*psize))
	{
	  x = time[index] ;

	  regressionOrder2 (x, time, amp, *psize, &a, &b, &c, &varianceFit) ;

	  variance = sqr((a * x * x) + (b * x) + c - amp[index]) ;

	  if (variance > (varianceFit * OUTLIER_VARIANCE_LIMIT))
	    {
	      doRid = 1 ;
	      (*psize)-- ;

	      if (index < (*psize))
		{
		  memmove (&time[index], &time[index+1], ((*psize) - index) * sizeof(float)) ;
		  memmove (&amp[index], &amp[index+1], ((*psize) - index) * sizeof(float)) ;
		  memmove (&err[index], &err[index+1], ((*psize) - index) * sizeof(float)) ;
		}
	    }
	  else
	    {
	      sumVariance += variance ;
	      sumChi2 += variance / sqr(err[index]) ;
	      numVariance++ ;
	      index++ ;
	    }
	}
    }
  while (doRid) ;

  if (numVariance == 0)
    return (MAXFLOAT) ;

  return (sumChi2 / numVariance) ;
}


// ============================ Chi2 of alternative models ==============================

// Returns the reduced chi2 of a flat amplitude model (at the average)
// Assumes: size > 1
double getAvrChi2 (float *amp, float *err, int size)
{
  double avrAmp = 0.0, sumChi2 = 0.0 ;
  int i ;

  for (i = 0 ; i < size ; i++)
    avrAmp += amp[i] ;

  avrAmp /= size ;

  for (i = 0 ; i < size ; i++)
    sumChi2 += sqr((amp[i] - avrAmp) / err[i]) ;

  return (sumChi2 / (size - 1)) ;
}


// Fits the given data to:  y = a * sin(2pi * m * x) + b * cos(2pi * m * x) + c
// In other words a sinusoidal perturbation with given amplitude, phase,
// mode (m) and DC component (c)
// The fit weights all the given data points equally.
// Assumes: size > 3
// Returns the reduced chi2 of the best fit (incorporating error information)
double getSinModeChi2 (float *time, float *amp, float *err, int size, double mode)
{
  const double w = 2.0 * M_PI * mode ;
  double A1=0.0, A2=0.0, A3=0.0, B1=0.0, B2=0.0, B3=0.0, C=0.0, D=0.0 ;
  double sinx, cosx, denom, a, b, c, chi2 = 0.0;
  int i ;

  for (i = 0 ; i < size ; i++)
    {
      sinx = sin (w * time[i]) ;
      cosx = cos (w * time[i]) ;

      A1 += sinx ;
      A2 += sinx * sinx ;
      A3 += amp[i] * sinx ;
      B1 += cosx ;
      B2 += cosx * cosx ;
      B3 += amp[i] * cosx ;
      C += amp[i] ;
      D += sinx * cosx ;
    }

  denom = (A1*((A1*B2) - (2.0*B1*D))) + (A2*((B1*B1) - (B2*size))) - (D*D*size) ;  // Denominator

  if (denom == 0.0)
    denom = EPSILON ;  // Prevents division by zero
  
  a = ((A1*((B2*C) - (B1*B3))) + (A3*((B1*B1) - (B2*size))) + (D*((B3*size) - (B1*C))))  / denom ;
  b = ((A1*((A1*B3) - (C*D)))  + (A2*((B1*C)  - (B3*size))) + (A3*((D*size) - (A1*B1)))) / denom ;
  c = ((A1*((A3*B2) - (B3*D))) + (A2*((B1*B3) - (B2*C)))    + (D*((C*D) - (A3*B1))))     / denom ;

  for (i = 0 ; i < size ; i++)
    {
      sinx = sin (w * time[i]) ;
      cosx = cos (w * time[i]) ;
      chi2 += sqr(((a * sinx) + (b * cosx) + c - amp[i]) / err[i]) ;
    }

  return (chi2 / (size - 3)) ;
}


// fits the given light curve to a sinusoidal with mode 1 and 2
// returns the best chi square result of the two
double getSinChi2 (float *time, float *amp, float *err, int size)
{
  double m1, m2 ;

  m1 = getSinModeChi2 (time, amp, err, size, 1.0) ;
  m2 = getSinModeChi2 (time, amp, err, size, 2.0) ;

  if (m1 <= m2)
    return (m1) ;

  return (m2) ;
}


//========================= Eccentricity ======================================

// Uses a combined Newton-Raphson + bisection method for finding the root (E) of:
//  M = E - (e * sin(E))     [Kepler's equation]
// Given: M = mean anomaly ; e = eccentricity of orbit (0 <= e < 1)
// Returns: E = Eccentric Anomaly
double eccentricAnomaly (double M, double e)
{
  int counter = BISECTION_SAFETY_MAX_ITERATIONS ;
  double Emin = M - 1.0, Emax = M + 1.0, E = M ;
  double f, dfm, dE ;

  do
    {
      f = M + (e * sin(E)) - E ;  // May be optimized by setting cos=sqrt(1-sin^2)
      dfm = 1.0 - (e * cos(E)) ;  // Minus differential of f (always non-negative)
      dE = dfm * ECC_ANOMALY_MAX_ERROR ;

      if (f > dE)
	{
	  Emin = E ;
	  dE = Emax - Emin ;

	  if ((dfm * dE) > f)
	    E += (f / dfm) ;
	  else
	    E = 0.5 * (Emax + Emin) ;
	}
      else if (f < (-dE))
	{
	  Emax = E ;
	  dE = Emax - Emin ;

	  if ((dfm * dE) > -f)
	    E += (f / dfm) ;
	  else
	    E = 0.5 * (Emax + Emin) ;
	}
      else return (E) ;
    }
  while ((dE > ECC_ANOMALY_MAX_ERROR) && ((--counter) > 0)) ;

  return (E) ;  // should almost never exits here
}



// Finds the eccentricity using simple bisection.
// Uses the fact that that tDiff is a monotonically decreasing function of e
// Y = e * sin(omega) ; from the dip widths
// tdiff = the difference between the dip times
double getEccentricity (double tDiff, double Y)
{
  const double Y2 = Y * Y ;
  int counter = BISECTION_SAFETY_MAX_ITERATIONS ;
  double e2, res, eMid, eMax = 1.0, eMin = fabs(Y) ;

  tDiff *= M_PI ;

  while (((eMax - eMin) > ECCENTRICITY_MAX_ERROR) && ((counter--) > 0))
    {
      eMid = 0.5 * (eMax + eMin) ;
      e2 = eMid * eMid ;

      res = acos(sqrt((e2 - Y2) / (1.0 - Y2))) - (sqrt((1.0 - e2) * (e2 - Y2)) / (1.0 - Y2)) ;

      if (res > tDiff)
	eMin = eMid ;
      else
	eMax = eMid ;
    }

  return (0.5 * (eMax + eMin)) ;
}


//========================== Limb Darkening ====================================

// Quadratic limb darkening coefficients for a solar-like star in I filter (Claret 1998)
// Note that a "square root" law give a better fit (especially for I filter),
// but the error in assuming a solar star, is much larger and the total CPU requirements
// would almost double (doing a linear fit, on the other hand, won't save much CPU).

static double limbConstA = 0.0 ;
static double limbConstB = 0.0 ;
static double limbConstC = 0.0 ;
static double limbConstD = 0.0 ;
static double limbConstE = 0.0 ;
static double limbConstF = 0.0 ;
static double limbConstG = 0.0 ;
static double limbConstH = 0.0 ;


// Sets the quadratic limb darkening parameters to arbitrary given values.
void setLimbDarkening (double quadA, double quadB)
{
  limbConstA = 1.0 - quadA - quadB ;
  limbConstB = quadA + quadB + quadB ;
  limbConstC = -quadB ;
  limbConstD = M_PI * (1.0 - quadA - quadB - quadB) ;
  limbConstE = 0.5 * M_PI * quadB ;
  limbConstF = 2.0 * M_PI * (quadA + quadB + quadB) / 3.0 ;
  limbConstG = M_PI * (1.0 - quadA - quadB) ;
  limbConstH = M_PI * (6.0 - quadA - quadA - quadB) / 6.0 ;
}

// cosAngle2 = the square of the cosine of the angle between the zenith of
// the star to the given point on the surface (relative to the star's center)
// Returns the solar limb darkening coefficient
// Note that it is normalized so that at the star's zenith (cosAngle2 = 1), it returns 1
double limbDarkening (double cosAngle2)
{
  return (limbConstA + (limbConstB * sqrt(cosAngle2)) + (limbConstC * cosAngle2)) ;
}


// Analytically integrates the limb darkened disk, from r=0 to r=rBack
// rBack = the full radius of the star's disk
double integrateWholeDisk (double rBack)
{
  return (limbConstH * rBack * rBack) ;
}


// Analytically integrates the limb darkened disk, from 0 to the given finish
// finish = where to end the integration
// rBack = the radius of the back star's disk (the one seen as a crescent)
double integrateDiskFromStart (double finish, double rBack)
{
  const double x = sqr(finish / rBack) ;

  return (rBack * rBack * (((limbConstD + (limbConstE * x)) * x) + (limbConstF * (1.0 - cube(sqrt(1.0 - x)))))) ;
}


// Analytically integrates the limb darkened disk, from the given start to rBack
// start = from where to begin the integration
// rBack = the radius of the back star's disk (the one seen as a crescent)
double integrateDiskToFinish (double start, double rBack)
{
  const double x = 1.0 - sqr(start / rBack) ;

  return (rBack * rBack * (((limbConstG - (limbConstE * x)) * x) + (limbConstF * cube(sqrt(x))))) ;
}


// Uses the Secant method (not the most efficient method, but is simple and robust)
// Uses the fact that the function grows monotonically
// Returns finish or -1.0 if error
double invIntegrateDiskFromStart (double S, double rBack)
{
  double r1 = 0.0, S1 = 0.0 ;
  double r2 = rBack, S2 = integrateWholeDisk(rBack) ;
  double rTry, STry ;

  if ((S < S1) || (S > S2) || ((S2 - S1) < EPSILON))
    return (-1.0) ;  // Error (out of bound)

  do
    {
      rTry = r1 + ((r2 - r1) * (S - S1) / (S2 - S1)) ;
      STry = integrateDiskFromStart (rTry, rBack) ;

      if (STry < S)
	{
	  r1 = rTry ;
	  S1 = STry ;
	}
      else
	{
	  r2 = rTry ;
	  S2 = STry ;
	}
    }
  while (fabs(S - STry) > EPSILON) ;

  return (rTry) ;
}


// Makes a simple trapezoid numerical integration with varying step size
// (smaller, the closer an asymptote) for finding the brightness of
// a partially hidden star. This method seems to works better than Simpson's.
// start = where to begin the integration
// finish = where to end the integration
// rFront = the radius of the front star's disk (the one seen as a disk)
// rBack = the radius of the back star's disk (the one seen as a crescent)
// D = the distance between the centers of the two stars
// dr0 = the infinitesimal integration step scale (unitless)
// Assumes:  D + rFront >= finish >= start >= |D - rFront| >= 0
// [num iterations] ~= 4 / dr0   ;  [abs. error] ~= 0.1 * rFront^2 * dr0^2
double integrateCrescent (double start, double finish, double rFront, double rBack,
			  double D, double dr0)
{
  const double rBack_m2 = 1.0 / (rBack * rBack) ;
  const double rFront2mD2 = (rFront * rFront) - (D * D) ;
  const double middle = 0.5 * (start + finish) ;
  const double D2 = 2.0 * D ;
  const double limitUp = (((D + rFront) < rBack) ? D + rFront : rBack) ;
  const double limitDown = fabs(D - rFront) ;
  double dr, r, r2, rStep, sum = 0.0 ;

  if (D < EPSILON)  // To avoid division by zero
    return (0.0) ;

  // Since dr0 is unitless and we want dr to have units of "distance" (1 = sum semi-major axes)
  dr0 *= sqrt(rFront) ;  

  // Step 1: integrate from middle up
  dr = dr0 * sqrt(limitUp - middle) ;
  for (rStep = middle + dr ; rStep < finish ; rStep += dr)
    {
      r = rStep - (0.5 * dr) ;
      r2 = r * r ;
      sum += (r * acos((rFront2mD2 - r2) / (D2 * r)) * limbDarkening(1.0 - (rBack_m2 * r2)) * dr) ;

      dr = dr0 * sqrt(limitUp - r) ;
    }

  // Step 2: add sliver at upper edge
  r = 0.5 * (finish + rStep - dr) ;
  r2 = r * r ;
  dr += (finish - rStep) ;
  sum += (r * acos((rFront2mD2 - r2) / (D2 * r)) * limbDarkening(1.0 - (rBack_m2 * r2)) * dr) ;

  // Step 3: integrate from middle down
  dr = dr0 * sqrt(middle - limitDown) ;
  for (rStep = middle - dr ; rStep > start ; rStep -= dr)
    {
      r = rStep + (0.5 * dr) ;
      r2 = r * r ;
      sum += (r * acos((rFront2mD2 - r2) / (D2 * r)) * limbDarkening(1.0 - (rBack_m2 * r2)) * dr) ;

      dr = dr0 * sqrt(r - limitDown) ;
    }

  // Step 4: add sliver at bottom edge
  r = 0.5 * (start + rStep + dr) ;
  r2 = r * r ;
  dr += (rStep - start) ;
  sum += (r * acos((rFront2mD2 - r2) / (D2 * r)) * limbDarkening(1.0 - (rBack_m2 * r2)) * dr) ;

  return (2.0 * sum) ;
}

// =============== Calculate the observed radiation flux from the binary system ===============

// Calculates the crescent of the back star, when it is partially eclipsed by the front star
// rFront = the radius of the star in front
// rBack = the radius of the star in back
// D = the distance between the centers of the two stars
// dr = the infinitesimal integration step
// Returns the relative brightness of the crescent of the back star
double integrateBackOverlap (double rFront, double rBack, double D, double dr)
{
  if (rFront < D)
    {
      if (rBack > (D + rFront))
	return (integrateDiskFromStart (D - rFront, rBack) +
		integrateCrescent (D - rFront, D + rFront, rFront, rBack, D, dr) +
		integrateDiskToFinish (D + rFront, rBack)) ;                  // E

      return (integrateDiskFromStart (D - rFront, rBack) +
	      integrateCrescent (D - rFront, rBack, rFront, rBack, D, dr)) ;  // B
    }

  if (rFront > (D + rBack))
    return (0.0) ;                                                            // D

  if (rBack > (D + rFront))
    return (integrateCrescent (rFront - D, rFront + D, rFront, rBack, D, dr) +
	    integrateDiskToFinish (rFront + D, rBack)) ;                      // F

  return (integrateCrescent (rFront - D, rBack, rFront, rBack, D, dr)) ;      // C
}


/******************************************************************
 * Returns the total flux from both stars of the binary.
 * Ignores limb darkening, gravity darkening, etc.
 * time = scan parameter 0 <= time < 1
 * p[DIM] = parameter vector
 * dr = the infinitesimal integration step
 * doB12max = 1:recalculate the light curve "plateau" brightness ; 0:don't
 *
 * NOTE: [definition of 1 unit distance]
 *  The physical distance between the stars at perihelion (minimal) is (1-e) units
 *  and the physical distance between the stars at aphelion (maximal) is (1+e) units
 *  so, 1 unit is the sum of the distances of the two semi-major axes
 *
 ******************************************************************/
double flux (double time, double p[DIM], double dr, int doB12max)
{
  static double B12max ;
  const double omega = 2.0 * M_PI * (p[D_TPO] - p[D_TMO]) ;
  const double meanAnomaly = 2.0 * M_PI * (time - p[D_TPO] - p[D_TMO]) ;  // 2pi * (t - t0)
  double D2, D, E ;

  if (doB12max)
    B12max = (p[D_B1] * integrateWholeDisk(p[D_R1])) + (p[D_B2] * integrateWholeDisk(p[D_R2])) ;

  E = eccentricAnomaly(meanAnomaly, p[D_ECC]) ;

  D2 = sqr(1.0 - (p[D_ECC] * cos(E))) - sqr((((cos(E) - p[D_ECC]) * sin(omega)) + (sqrt(1.0 - sqr(p[D_ECC])) * sin(E) * cos(omega))) * p[D_SIN_I]) ;

  if (D2 > (EPSILON * EPSILON))  // Prevents sqrt of negative or division by zero, later on
    D = sqrt (D2) ;
  else
    D = EPSILON ;

  if (D >= (p[D_R1] + p[D_R2]))   // Side by side (A)
    return (B12max) ;

  if (sin(E + omega) > 0.0)  // Is star 2 in front ?
    return ((p[D_B2] * integrateWholeDisk(p[D_R2])) + (p[D_B1] * integrateBackOverlap(p[D_R2], p[D_R1], D, dr))) ;

  // star 1 is in front
  return ((p[D_B1] * integrateWholeDisk(p[D_R1])) + (p[D_B2] * integrateBackOverlap(p[D_R1], p[D_R2], D, dr))) ;
}



// Returns the reduced chi squared of the model (a score for how good the fit is)
// If the parameter vector is out of range, returns MAXFLOAT
double scoreFit (double p[DIM], float *time, float *amp, float *err, int size, double dr)
{
  int i ;
  double score ;

  // Note that I use MAXFLOAT in a double since is may need to be increased by annealingFluctuation()
  if ((p[D_SIN_I] <= 0.0) || (p[D_SIN_I] > 1.0)) return (MAXFLOAT) ;                   // sin_i
  if ((p[D_ECC] < 0.0) || (p[D_ECC] >= 1.0)) return (MAXFLOAT) ;                       // e
  if ((p[D_R1] <= 0.0) || (p[D_R1] >= (1.0 - p[D_ECC]))) return (MAXFLOAT) ;           // r1
  if ((p[D_R2] <= 0.0) || (p[D_R2] >= (1.0 - p[D_ECC] - p[D_R1]))) return (MAXFLOAT) ; // r2
  if (p[D_B1] <= 0.0) return (MAXFLOAT) ;                                              // b1
  if (p[D_B2] <= 0.0) return (MAXFLOAT) ;                                              // b2

  score = sqr((amp[0] - flux(time[0], p, dr, 1)) / err[0]) ;

  for (i = 1 ; i < size ; i++)
    score += sqr((amp[i] - flux(time[i], p, dr, 0)) / err[i]) ;

  return (score / (size - DIM)) ;
}


// A statistical test
// Returns the correlation of a given residual with the previous residual
// this is to be used to distinguish between models that the mediocre throughout
// and models that are good in some places but very bad in others. My assumption is
// that the latter is far better situation than the former. In the extreme case of
// the latter, chi^2 should be 1, unless there is a problem with the error bars.
// Returns score in the range [-1, 1]  (Cauchy-Schwartz inequality)
//  A score of 1 means that the model is entirely above or entirely below the data
//  A score of 0 is ideal (should have chi^2 = 1)
//  A score below 0 is very suspect and probably unphysical
double midScatterScore (double p[DIM], float *time, float *amp, int size)
{
  int i ;
  double prevDelta, delta, sumWithPrev = 0.0, sumSqr = 0.0 ;

  // Note that I use MAXFLOAT in a double since is may need to be increased by annealingFluctuation()
  if ((p[D_SIN_I] <= 0.0) || (p[D_SIN_I] > 1.0)) return (MAXFLOAT) ;                   // sin_i
  if ((p[D_ECC] < 0.0) || (p[D_ECC] >= 1.0)) return (MAXFLOAT) ;                       // e
  if ((p[D_R1] <= 0.0) || (p[D_R1] >= (1.0 - p[D_ECC]))) return (MAXFLOAT) ;           // r1
  if ((p[D_R2] <= 0.0) || (p[D_R2] >= (1.0 - p[D_ECC] - p[D_R1]))) return (MAXFLOAT) ; // r2
  if (p[D_B1] <= 0.0) return (MAXFLOAT) ;                                              // b1
  if (p[D_B2] <= 0.0) return (MAXFLOAT) ;                                              // b2

  prevDelta = flux(time[size-1], p, MIN_INTEGRATION_STEP, 1) - amp[size-1] ;

  for (i = 0 ; i < size ; i++)
    {
      delta = flux(time[i], p, MIN_INTEGRATION_STEP, 0) - amp[i] ;

      sumWithPrev += (prevDelta * delta) ;
      sumSqr += (delta * delta) ;

      prevDelta = delta ;
    }

  if (sumSqr == 0.0)
    return (0.0) ;

  return (sumWithPrev / sumSqr) ;
}



#ifdef GRAPHIC
#ifdef PLOT
// Plot the light curve and the fit of the given parameters
// if (p == 0) then ignores the fit
// if (time == 0) then ignores the light curve data
// color = color of the model light curve plot
// if (doInterpol == 1) then plots the spline interpolation of the data
// checkVal = an arbitrary value the user wished to scale like the plot
// Returns the scales Y-axis pixel value which corresponds to (checkVal)
int plotFit (double p[DIM], float *time, float *amp, int size, int color, int doInterpol, double checkVal)
{
  double x, F, Fmin, Fmax ;
  int i, y ;

  if (p)
    {
      if ((p[D_SIN_I] <= 0.0) || (p[D_SIN_I] > 1.0)) return(-1) ;                   // sin_i
      if ((p[D_ECC] < 0.0) || (p[D_ECC] >= 1.0)) return(-2) ;                       // e
      if ((p[D_R1] <= 0.0) || (p[D_R1] >= (1.0 - p[D_ECC]))) return(-3) ;           // r1
      if ((p[D_R2] <= 0.0) || (p[D_R2] >= (1.0 - p[D_ECC] - p[D_R1]))) return(-4) ; // r2
      if (p[D_B1] <= 0.0) return(-5) ;                                              // b1
      if (p[D_B2] <= 0.0) return(-6) ;                                              // b2
    }

  Fmin = Fmax = amp[0] ;

  for (i = 1 ; i < size ; i++)
    {
      if (amp[i] < Fmin)
	Fmin = amp[i] ;
      else
	if (amp[i] > Fmax)
	  Fmax = amp[i] ;
    }

  if (p)
    for (x = 0.0 ; x < 1.0 ; x += 0.001)
      {
	F = flux (x, p, MIN_INTEGRATION_STEP, 1) ;

	y = 400 - (int)(250.0 * (F - Fmin) / (Fmax - Fmin)) ;
	if (y > 479) y = 479 ;
	if (y < 0) y = 0 ;

	putpixel ((int)(640 * x), y, color) ;
      }


  if (time && doInterpol)
    for (x = 0.0 ; x < 1.0 ; x += 0.001)
      {
	F = interpolateSmooth(x, time, amp, size) ;

	y = 400 - (int)(250.0 * (F - Fmin) / (Fmax - Fmin)) ;

	if ((y <= 479) && (y >= 0))
	  putpixel ((int)(640 * x), y, 5) ;
      }


  if (time)
    for (i = 0 ; i < size ; i++)
      {
	y = 400 - (int)(250.0 * (amp[i] - Fmin) / (Fmax - Fmin)) ;

	if ((y <= 479) && (y >= 0))
	  putpixel ((int)(640 * time[i]), y, 15) ;
      }

  return (400 - (int)(250.0 * (checkVal - Fmin) / (Fmax - Fmin))) ;
}
#endif
#endif


#ifdef WRITE_CURVE_FIT
// Writes to files - the raw data and the fitted curve
// Returns: 0 = success  otherwise failed
int writeCurveFit (double p[DIM], float *time, float *amp, float *err, int size, char *filename)
{
  FILE *fout ;
  char *localFilename, foutName[256] ;
  int i ;

  i = strlen(filename) ;
  for (i-- ; (i >= 0) && (filename[i] != '/') ; i--) ;  // goes to slash or -1
  localFilename =  &filename[i+1] ;

  //---------------------

  sprintf (foutName, "%s.data", localFilename) ;
  fout = fopen (foutName, "wt") ;
  if (!fout)
    return (1) ;

  for (i = 0 ; i < size ; i++)
    fprintf (fout, "%f %f %f %f\n", time[i], -2.5 * log10(amp[i]), MAGNITUDE_ERROR_FACTOR * err[i] / amp[i],
	     2.5 * log10(flux(time[i], p, MIN_INTEGRATION_STEP, 1) / amp[i])) ;
  fclose (fout) ;

  //---------------------

  sprintf (foutName, "%s.fit", localFilename) ;
  fout = fopen (foutName, "wt") ;
  if (!fout)
    return (2) ;

  for (i = 0 ; i < WRITE_CURVE_FIT ; i++)
    fprintf (fout, "%f %f\n", (float)i / WRITE_CURVE_FIT,
	     -2.5 * log10(flux ((float)i / WRITE_CURVE_FIT, p, MIN_INTEGRATION_STEP, 1))) ;

  fclose (fout) ;
  return (0) ;
}
#endif

//======================= Make a "first guess" for the initial parameters ===============================

// Data structure of a single light curve observation
struct LCdata
{
  float primary ;
  float secondary ;
  float tertiary ;
};


// A comparator for a pair-o-float
// Returns: -1 if x.primary < y.primary
//           0 if x.primary = y.primary
//           1 if x.primary > y.primary
int comparLCdata (const void *x, const void *y)
{
  if (((struct LCdata*)x)->primary < ((struct LCdata*)y)->primary)
    return (-1) ;
  else
    return (((struct LCdata*)x)->primary > ((struct LCdata*)y)->primary) ;
}


// Returns 0 = success ; 1 = failure (malloc)
int sortSamples (float *time, float *amp, float *err, int size)
{
  int i ;
  struct LCdata *arr = (struct LCdata*)malloc (size * sizeof(struct LCdata)) ;

  if (!arr)
    return (1) ;

  for (i = 0 ; i < size ; i++)
    {
      arr[i].primary = time[i] ;
      arr[i].secondary = amp[i] ;
      arr[i].tertiary = err[i] ;
    }

  qsort (arr, size, sizeof(struct LCdata), comparLCdata) ;

  for (i = 0 ; i < size ; i++)
    {
      time[i] = arr[i].primary ;
      amp[i] = arr[i].secondary ;
      err[i] = arr[i].tertiary ;
    }

  free (arr) ;
  return (0) ;
}


// A comparator function for sorting an array of floating point values
int comparFloat (const void *x, const void *y)
{
  if ((*((float*)x)) < (*((float*)y)))
    return (-1) ;
  else
    return ((*((float*)x)) > (*((float*)y))) ;
}



// Given a floating point array
// Returns the median amplitude  (or MAXFLOAT in case of error - malloc failure)
double getMedian (float *data, int size)
{
  double median ;
  float *arr = (float*)malloc (size * sizeof(float)) ;

  if (!arr)
    return (MAXFLOAT) ;

  memcpy (arr, data, size * sizeof(float)) ;

  qsort (arr, size, sizeof(float), comparFloat) ;

  if (size & 1)  // is odd
    median = arr[(size-1)/2] ;
  else           // is even
    median = 0.5 * (arr[size/2] + arr[(size/2)-1]) ;

  free (arr) ;
  return (median) ;
}



//----------------------- Find dips ------------------------------------

// Finds the two deepest minima of the light curve
// The primary minimum is simply at the smallest value
// The secondary minimum is the place that has the largest difference
// between the value itself and the maxima between it and the primary minimum
// Note: if a secondary minimum can't be found (very unusual), will set *pmin2Amp = MAXFLOAT
// May return an "edge minimum"- near (*pmin1Time + 0.5)
// *pmax1Amp >= *pmax2Amp >= *pmin1Amp ; *pmax1Amp >= *pmin2Amp >= *pmin1Amp
// ideally:  *pmax2Amp > *pmin2Amp  but there is no guarantee (can be used as a test)
void findDips (float *time, float *amp, int size,
	       double *pmin1Time, double *pmin2Time,
	       double *pmin1Amp, double *pmin2Amp)
{
  double maxAmp, min1TimePlusHalf ;
  double diff, sampTime, sampAmp ;

  // Step 1: search for the primary dip
  *pmin1Time = 0.0 ;
  *pmin1Amp = interpolateSmooth (0.0, time, amp, size) ;

  for (sampTime = SEARCH_STEP_SIZE ; sampTime < 1.0 ; sampTime += SEARCH_STEP_SIZE)
    {
      sampAmp = interpolateSmooth (sampTime, time, amp, size) ;

      if (*pmin1Amp > sampAmp)
	{
	  *pmin1Amp = sampAmp ;
	  *pmin1Time = sampTime ;
	}
    }

  // Step 2: search for the secondary dip min1TimePlusHalf = min1Time + 0.5 ;
  *pmin2Amp = MAXFLOAT ;
  min1TimePlusHalf = *pmin1Time + 0.5 ;
  maxAmp = *pmin1Amp ;
  diff = 0.0 ;

  if (min1TimePlusHalf < 1.0)
    {
      // 2.1: look up
      for (sampTime = *pmin1Time + SEARCH_STEP_SIZE ; sampTime <= min1TimePlusHalf ; sampTime += SEARCH_STEP_SIZE)
	{
	  sampAmp = interpolateSmooth(sampTime, time, amp, size) ;

	  if (maxAmp < sampAmp)
	    maxAmp = sampAmp ;

	  if (diff < maxAmp - sampAmp)
	    {
	      diff = maxAmp - sampAmp ;
	      *pmin2Time = sampTime ;
	      *pmin2Amp = sampAmp ;
	    }
	}

      // 2.2: look down
      maxAmp = *pmin1Amp ;

      for (sampTime = *pmin1Time - SEARCH_STEP_SIZE ; sampTime >= 0.0 ; sampTime -= SEARCH_STEP_SIZE)
	{
	  sampAmp = interpolateSmooth(sampTime, time, amp, size) ;

	  if (maxAmp < sampAmp)
	    maxAmp = sampAmp ;

	  if (diff < maxAmp - sampAmp)
	    {
	      diff = maxAmp - sampAmp ;
	      *pmin2Time = sampTime ;
	      *pmin2Amp = sampAmp ;
	    }
	}

      for (sampTime = 1.0 - SEARCH_STEP_SIZE ; sampTime >= min1TimePlusHalf ; sampTime -= SEARCH_STEP_SIZE)
	{
	  sampAmp = interpolateSmooth(sampTime, time, amp, size) ;

	  if (maxAmp < sampAmp)
	    maxAmp = sampAmp ;

	  if (diff < maxAmp - sampAmp)
	    {
	      diff = maxAmp - sampAmp ;
	      *pmin2Time = sampTime ;
	      *pmin2Amp = sampAmp ;
	    }
	}
    }
  else  // min1TimePlusHalf >= 1.0
    {
      min1TimePlusHalf -= 1.0 ;  // modulo 1.0

      // 2.1: look up
      for (sampTime = *pmin1Time + SEARCH_STEP_SIZE ; sampTime < 1.0 ; sampTime += SEARCH_STEP_SIZE)
	{
	  sampAmp = interpolateSmooth(sampTime, time, amp, size) ;

	  if (maxAmp < sampAmp)
	    maxAmp = sampAmp ;

	  if (diff < (maxAmp - sampAmp))
	    {
	      diff = maxAmp - sampAmp ;
	      *pmin2Time = sampTime ;
	      *pmin2Amp = sampAmp ;
	    }
	}

      for (sampTime = 0.0 ; sampTime <= min1TimePlusHalf ; sampTime += SEARCH_STEP_SIZE)
	{
	  sampAmp = interpolateSmooth(sampTime, time, amp, size) ;

	  if (maxAmp < sampAmp)
	    maxAmp = sampAmp ;

	  if (diff < maxAmp - sampAmp)
	    {
	      diff = maxAmp - sampAmp ;
	      *pmin2Time = sampTime ;
	      *pmin2Amp = sampAmp ;
	    }
	}

      // 2.2: look down
      maxAmp = *pmin1Amp ;

      for (sampTime = *pmin1Time - SEARCH_STEP_SIZE ; sampTime >= min1TimePlusHalf ; sampTime -= SEARCH_STEP_SIZE)
	{
	  sampAmp = interpolateSmooth(sampTime, time, amp, size) ;

	  if (maxAmp < sampAmp)
	    maxAmp = sampAmp ;

	  if (diff < (maxAmp - sampAmp))
	    {
	      diff = maxAmp - sampAmp ;
	      *pmin2Time = sampTime ;
	      *pmin2Amp = sampAmp ;
	    }
	}
    }
}


// Finds the values (should be about max) between the dips (pmax1Amp, pmax2Amp)
// given the average of the two dip times (min1Time, min2Time)
// Note that we can't use a simple max, since it may pick the interpolation
// overshoot at the edges of the dips. This approach is far more robust.
// Sets:  *pmax1Amp >= *pmax2Amp
void findMidMaxs (float *time, float *amp, int size, double avrTime, double *pmax1Amp, double *pmax2Amp)
{
  *pmax1Amp = interpolateSmooth(avrTime, time, amp, size) ;
  *pmax2Amp = interpolateSmooth(mod1(avrTime + 0.5), time, amp, size) ;

  if (*pmax1Amp < *pmax2Amp)
    swap(pmax1Amp, pmax2Amp) ;
}



// Assumed that goalAmp is larger than the amplitude at *pminTime
// Returns the half-width of the given dip, to the point it crosses a given goal amplitude (goalAmp)
// Returns 0.0 upon fatal error (couldn't reach goalAmp)
double findHalfWidth (float *time, float *amp, int size, double goalAmp, double *pminTime)
{
  double minTimePlusHalf = *pminTime + 0.5 ;
  double sampAmp, sampTime ;
  double limitUp = MAXFLOAT, limitDown = MAXFLOAT ;
  double limitUpFineTune, limitDownFineTune ;

  // Step 1: find dip edges
  if (minTimePlusHalf < 1.0)
    {
      // 1.1: look up
      for (sampTime = *pminTime + SEARCH_STEP_SIZE ; (limitUp == MAXFLOAT) && (sampTime <= minTimePlusHalf) ; sampTime += SEARCH_STEP_SIZE)
	{
	  sampAmp = interpolateSmooth(sampTime, time, amp, size) ;

	  if (sampAmp > goalAmp)
	    limitUp = sampTime ;
	}

      // 1.2: look down
      for (sampTime = *pminTime - SEARCH_STEP_SIZE ; (limitDown == MAXFLOAT) && (sampTime >= 0.0) ; sampTime -= SEARCH_STEP_SIZE)
	{
	  sampAmp = interpolateSmooth(sampTime, time, amp, size) ;

	  if (sampAmp > goalAmp)
	    limitDown = sampTime ;
	}

      for (sampTime = 1.0 - SEARCH_STEP_SIZE ; (limitDown == MAXFLOAT) && (sampTime >= minTimePlusHalf) ; sampTime -= SEARCH_STEP_SIZE)
	{
	  sampAmp = interpolateSmooth(sampTime, time, amp, size) ;

	  if (sampAmp > goalAmp)
	    limitDown = sampTime ;
	}
    }
  else  // minTimePlusHalf >= 1.0
    {
      minTimePlusHalf -= 1.0 ;  // modulo 1.0

      // 1.1: look up
      for (sampTime = *pminTime + SEARCH_STEP_SIZE ; (limitUp == MAXFLOAT) && (sampTime < 1.0) ; sampTime += SEARCH_STEP_SIZE)
	{
	  sampAmp = interpolateSmooth(sampTime, time, amp, size) ;

	  if (sampAmp > goalAmp)
	    limitUp = sampTime ;
	}

      for (sampTime = 0.0 ; (limitUp == MAXFLOAT) && (sampTime <= minTimePlusHalf) ; sampTime += SEARCH_STEP_SIZE)
	{
	  sampAmp = interpolateSmooth(sampTime, time, amp, size) ;

	  if (sampAmp > goalAmp)
	    limitUp = sampTime ;
	}

      // 1.2: look down
      for (sampTime = *pminTime - SEARCH_STEP_SIZE ; (limitDown == MAXFLOAT) && (sampTime >= minTimePlusHalf) ; sampTime -= SEARCH_STEP_SIZE)
	{
	  sampAmp = interpolateSmooth(sampTime, time, amp, size) ;

	  if (sampAmp > goalAmp)
	    limitDown = sampTime ;
	}
    }

  if ((limitUp == MAXFLOAT) || (limitDown == MAXFLOAT))
    return (0.0) ;  // Fatal error - couldn't reach goalAmp


  // Step 2: correct for the search overshoot:  (error <= 0.5)
  limitUp -= (0.5 * SEARCH_STEP_SIZE) ;
  if (limitUp < 0.0) limitUp += 1.0 ;

  limitDown += (0.5 * SEARCH_STEP_SIZE) ;
  if (limitDown >= 1.0) limitDown -= 1.0 ;

  // Step 3: fine tune output results:
  limitUpFineTune = findGoalSmooth (limitUp, goalAmp, time, amp, size) ;
  limitDownFineTune = findGoalSmooth (limitDown, goalAmp, time, amp, size) ;

  // Step 4: update minimum:  (especially important for square dips)
  if (limitDownFineTune < limitUpFineTune)
    {
      *pminTime = 0.5 * (limitUpFineTune + limitDownFineTune) ;

      return (0.5 * (limitUpFineTune - limitDownFineTune)) ;
    }

  *pminTime = 0.5 * (1.0 + limitUpFineTune + limitDownFineTune) ;

  if (*pminTime > 1.0)
    *pminTime -= 1.0 ;

  return (0.5 * (1.0 + limitUpFineTune - limitDownFineTune)) ;
}



// Outputs *pvarySin_i, a midway allowable variance for sin(i)
// when the returned value is close to the minimum *pvarySin_i become negative
// this is needed since if it is varied too much, the result will be only MAXFLOATs
// Given: Y = -e * sin(omega), for dip #1  and  e * sin(omega), for dip #2
// doShapeWarnings is for avoiding giving two warnings for the same problem (r1<r2 and r1>r2)
// Returns 1.0 or best guess upon error
double getSin_i (float *time, float *amp, int size, double e,
		 double Y, double Rmin, double Rmax, double *pvarySin_i,
		 double minTime, double minAmp, double medianAmp,
		 double halfWidth, char *filename, char *errFilename, int doShapeWarnings)
{
  double tmpMinTime, goalAmp, wideHalfWidth, narrowHalfWidth ;
  double q, p, H, widthMultiple, cosi2, res ;
  const double minSin_i = sqrt(1.0 - sqr(Rmin+Rmax)) ;  // the valid range is between this and 1.0

  *pvarySin_i = 0.5 * (1.0 - minSin_i) ;  // default value

  tmpMinTime = minTime ;
  goalAmp = (0.75 * medianAmp) + (0.25 * minAmp) ;
  wideHalfWidth = findHalfWidth(time, amp, size, goalAmp, &tmpMinTime) ;

  tmpMinTime = minTime ;
  goalAmp = (0.25 * medianAmp) + (0.75 * minAmp) ;
  narrowHalfWidth = findHalfWidth(time, amp, size, goalAmp, &tmpMinTime) ;


  if ((narrowHalfWidth >= halfWidth) || (narrowHalfWidth == 0.0) || (wideHalfWidth <= halfWidth))
    {
      if (doShapeWarnings)
	printError (errFilename, 0, filename, "getSin_i()", "Invalid slope") ;

      return (1.0) ;
    }

  if (wideHalfWidth >= 0.25)
    {
      if (doShapeWarnings)
	printError (errFilename, 0, filename, "getSin_i()", "Dip is too wide") ;

      return (1.0) ;
    }


  // Compensate for the widening of the ingress/egress by the smoothing kernel
  H = (double)NUM_POINTS_HALF_KERNEL / size ;
  q = 0.5 * (wideHalfWidth - narrowHalfWidth) / H ;

  if (q >= 1.0) p = 2.0 * q ;
  else if (q > 0.3232309) p = q + sqrt(1.8 - sqrt(3.84 - (3.2 * q))) ;
  else if (q > 0.2288838) p = sqrt(1.8 - (0.4 / q) - (q * q)) ;  // Rounded up to protect against sqrt of negative
  else return (1.0) ;

  widthMultiple = halfWidth / (p * H) ;

  if (widthMultiple > (Rmax / Rmin))
    {
      // This error is commented out because it is too common, especially when the (r1<r2) vs (r1>r2) guess is wrong
      // it could be, in principal, used to cancel the wrong guess, but it is simply too uncertain

      // printError (errFilename, 0, filename, "getSin_i()", "Invalid width multiple") ;
      return (1.0) ;
    }

  cosi2 = sqr(Rmax * (1.0 + Y) / (1.0 - (e * e))) * (1.0 - (widthMultiple * Rmin / Rmax)) ;

  if (cosi2 < 0.0)
    {
      printError (errFilename, 0, filename, "getSin_i()", "Negative cos(i)^2") ;
      return (1.0) ;
    }

  if ((cosi2 >= sqr(Rmin + Rmax)) || (cosi2 >= 1.0))  // The latter should never happen
    {
      printError (errFilename, 0, filename, "getSin_i()", "Sin(i) is too small") ;
      cosi2 = Rmax * Rmax ;
    }

  res = sqrt(1.0 - cosi2) ;

  if ((1.0 - res) <= (res - minSin_i))
    *pvarySin_i = 0.5 * (res - minSin_i) ; // Closer to max
  else
    *pvarySin_i = 0.5 * (res - 1.0) ;      // Closer to min - set a negative variance

  return (res) ;
}


// =============== Take dips into account =========================


// Returns 1 if t is in the given dip, otherwise returns 0
int isInDip (double t, double minTime, double halfWidth)
{
  double diff = fabs(t - minTime) ;

  return ((diff < halfWidth) || ((1.0 - diff) < halfWidth)) ;
}


// Makes sure that there is a sufficient amount of data to contain a given dip
// minTime = time of dip's minimum
// halfWidth = the dip's half width
// returns: 1 = OK, plenty of data for dip  ;  0 = bad, not enough data
int isEnoughDipData (float *time, int size, double minTime, double halfWidth)
{
  int i, dipDataNum = 0 ;

  for (i = 0 ; (dipDataNum < MIN_NUM_DATA) && (i < size) ; i++)
    if (isInDip (time[i], minTime, halfWidth))
      dipDataNum++ ;

  return (dipDataNum == MIN_NUM_DATA) ;
}


// This may only correct by a small amount. But it's very important to get the
// depth of the small dip as accurately as possible
// pPlateauStdDiv = (output pointer) the standard deviation of the plateau amplitudes
// pPlateauWaviness = (output pointer) a statistical measure for how wavy the plateau is.
//  The range is [-1,1], where 1 is very wavy and 0 is not wavy at all (negative values are unphysical).
// note that this is better than stddiv around a spline because a spline,
// has the nasty effect overshooting around the dips even worse, the spline stddiv is strongly
// determined by NUM_POINTS_HALF_KERNEL and might trace the deviations too closely (or not close enough)
// Returns: 0 = success ; 1 = malloc failure ; 2 = goal couldn't be reached ; 3 = not enough data in plateau ; 4 = zero variance
int findPlateauMedian (float *time, float *amp, int size, double min1Time, double min2Time,
		       double *pMedianAmp, double *pPlateauStdDiv, double *pPlateauWaviness)
{
  int i, reducedSize = 0 ;
  double min1HalfWidth, min2HalfWidth ;
  double sumVarianceAmp, sumNeighborVariance ;
  float *reducedAmp = (float*)malloc (size * sizeof(float)) ;

  if (!reducedAmp)
    return (1) ;

  min1HalfWidth = findHalfWidth(time, amp, size, *pMedianAmp, &min1Time) ;
  min2HalfWidth = findHalfWidth(time, amp, size, *pMedianAmp, &min2Time) ;

  if ((min1HalfWidth == 0.0) || (min2HalfWidth == 0.0))
    {
      free (reducedAmp) ;
      return (2) ;
    }

  for (i = 0 ; i < size ; i++)
    if (!isInDip (time[i], min1Time, min1HalfWidth) && !isInDip(time[i], min2Time, min2HalfWidth))
      {
	reducedAmp[reducedSize] = amp[i] ;
	reducedSize++ ;
      }

  // Check the number of data points in the plateau
  if (reducedSize < MIN_NUM_DATA)
    {
      free (reducedAmp) ;
      return (3) ;
    }

  *pMedianAmp = getMedian(reducedAmp, size) ;

  // Note that I'm calculating around the median, instead of the average, so to make it more robust
  // doing this will make the variance (or sumVarianceAmp) larger than it would have been otherwise.
  // but usually the average will be very close to the median, so the difference will be small.
  // Also note that I'm calculating the variance in this manner to reduce numerical errors, which
  // could become a serious problem.
  // Waviness measure - from the ratio of the mean square difference between neighbor to the variance
  sumVarianceAmp = sqr(reducedAmp[0] - (*pMedianAmp)) ;
  sumNeighborVariance = sqr(reducedAmp[size-1] - reducedAmp[0]) ;
  for (i = 1 ; i < reducedSize ; i++)
    {
      sumVarianceAmp += sqr(reducedAmp[i] - (*pMedianAmp)) ;
      sumNeighborVariance += sqr(reducedAmp[i-1] - reducedAmp[i]) ;
    }

  if (sumVarianceAmp <= 0.0)
    return (4) ;  // This should never happen

  *pPlateauStdDiv = sqrt(sumVarianceAmp / reducedSize) ;
  *pPlateauWaviness = 1.0 - (0.5 * sumNeighborVariance / sumVarianceAmp) ;

  free (reducedAmp) ;
  return (0) ;
}


//----------------------- Simplex + simulated annealing ------------------------------------------

// Calculates the annealing fluctuation. In converts a flatly distributed random
// variable rand() to a logarithmicly distributed one.
// The temperature (ignoring the Boltzmann's constant) multiplies this
// distribution to create a perturbation above 1.0

// Returns a random, logarithmicly distributed perturbation above 1.0
// probability:  p(x) = (1/t) * exp(-(x-1)/t)  ; where t = temperature
double annealingFluctuation (double temperature)
{  // May be optimize by subtracting a precalculated: log(1.0 + RAND_MAX)

  return (1.0 - (temperature * log((1.0 + rand()) / (1.0 + RAND_MAX)))) ;
}

// Part of the downhill simplex method with simulated annealing [press 2002]
// Checks out a given extrapolation factor for the highest point. If it is an improvement
// then it replaces the highest point (makes all the necessary updates).
// p[DIM+1][DIM] - a matrix of the (DIM+1) simplex points in the DIM-dimensional space
// y[DIM+1] - the score (function value) of the (DIM+1) simplex points
// psum[DIM] - the sum of the points' values in each of the DIM coordinates
// ihi - the index for the highest point
// yhi - the value the highest point
// fac - the factor for the highest point, where:
//  fac= 1   --> highest point
//  fac= 0   --> c.m. of the remaining points
//  fac= 0.5 --> mid point between the highest point and the c.m. of the remaining points
//  fac= -1  --> reflection of the highest point about the c.m. of the remaining points
// dr - the infinitesimal integration step
// Returns the score (function value) for the extrapolated point
// Note that the arrays: p, y, psum - may get updated
double amotry (double p[DIM+1][DIM], double y[DIM+1], double psum[DIM], int ihi, double *pyhi,
	       double fac, float *time, float *amp, float *err, int size, double dr, double temperature,
	       double pElite[DIM], double *pyElite, int *piElite)
{
  int j ;
  double ytry, yflu ;
  double ptry[DIM] ;
  double fac1 = (1.0 - fac) / DIM ;
  double fac2 = fac1 - fac ;

  for (j = 0 ; j < DIM ; j++)
    ptry[j] = (psum[j] * fac1) - (p[ihi][j] * fac2) ;

  ytry = scoreFit (ptry, time, amp, err, size, dr) ;

  yflu = ytry / annealingFluctuation(temperature) ; // with a random thermal fluctuation subtracted

  // Replaces the highest (worst) value with the new one. The new one will always
  // Get copied if it's better than the worst and sometimes even if it's not
  if (yflu < (*pyhi))
    {
      if (ytry <= (*pyElite))
	{
	  *pyElite = ytry ;
	  *piElite = ihi ;
	}
      else if (ihi == (*piElite))  // About to overwrite the elite
	{
	  memcpy (pElite, p[ihi], DIM * sizeof(double)) ;
	  *piElite = -1 ;
	}

      y[ihi] = ytry ;
      *pyhi = yflu ;

      for (j = 0 ; j < DIM ; j++)
	psum[j] += (ptry[j] - p[ihi][j]) ;

      memcpy (p[ihi], ptry, DIM * sizeof(double)) ;
    }

  return (yflu) ;
}


// Based on the downhill simplex method with simulated annealing [press 2002]
// includes Elite refresh [Aldous 1994], where you revert to the
// best fit found so far. This can be done every given number of iterations,
// or as I chose, a certain number of refreshes throughout the convergence
// p[DIM+1][DIM] - a matrix of the (DIM+1) simplex points in the DIM-dimensional space
// y[DIM+1] - the score (function value) of the (DIM+1) simplex points
// numIterations = number of iteration to run the convergence algorithm
// Returns the index for the lowest (best) point in the simplex
int amoeba (double p[DIM+1][DIM], double y[DIM+1], float *time, float *amp, float *err,
	    int size, long numIterations)
{
  int i, j ;      // Temporary
  int ilo, ihi ;  // Fluctuated
  int iElite ;    // Exact value
  double ytry, yhi, ylo, ynhi, ysave ;          // Fluctuated
  double sum, psum[DIM], pElite[DIM], yElite ;  // Exact values ; pElite is only used when the elite is overwritten (iElite == -1)
  double dr, temperature = INIT_TEMPERATURE ;   // Utilities
  const double coolingFactor = 1.0 - ((double)NUM_E_FOLD_COOL / numIterations) ;  // A good approximation, if near 1.0
  const long minStepIteration = (long)(numIterations * MIN_STEP_ITERATION_FRACTION) ;

  // Step 1: [elitism] backup the best candidate
  yElite = y[0] ;
  iElite = 0 ;
  for (i = 1 ; i <= DIM ; i++)
    if (y[i] < yElite)
      {
	yElite = y[i] ;
	iElite = i ;
      }


  // Step 2: initializes the sum of values in each coordinate
  //      (to be used later for calculating the average, or center of mass)
  for (j = 0 ; j < DIM ; j++)
    {
      sum = p[0][j] ;
      for (i = 1 ; i <= DIM ; i++)
	sum += p[i][j] ;

      psum[j] = sum ;
    }


  // The main loop
  while (numIterations > 0)
    {
      // Step 3: find-
      //  ihi  = index of highest (worst) value
      //  ilo  = index of lowest (best) value
      //  yhi  = highest (worst) value
      //  ynhi = second highest (worst) value
      //  ylo  = lowest (best) value

      // 3.1: sort the first two
      ynhi = ylo = y[0] * annealingFluctuation(temperature) ;
      yhi = y[1] * annealingFluctuation(temperature) ;

      if (ylo <= yhi)
	{
	  ihi = 1 ;
	  ilo = 0 ;
	}
      else
	{
	  ihi = 0 ;
	  ilo = 1 ;
	  ynhi = yhi ;  // Swap: ynhi=ylo <--> yhi
	  yhi = ylo ;
	  ylo = ynhi ;
	}

      // 3.2: sort the rest
      for (i = 2 ; i <= DIM ; i++)
	{
	  ytry = y[i] * annealingFluctuation(temperature) ;

	  if (ytry <= ylo)
	    {
	      ilo = i ;
	      ylo = ytry ;
	    }

	  if (ytry > yhi)
	    {
	      ihi = i ;
	      ynhi = yhi ;
	      yhi = ytry ;
	    }
	  else if (ytry > ynhi)
	    {
	      ynhi = ytry ;
	    }
	}


      // Step 4: integration step size
      if ((numIterations > minStepIteration) && (yElite > 1.0))
	dr = MIN_INTEGRATION_STEP * sqrt(sqrt(yElite)) ;
      else
	dr = MIN_INTEGRATION_STEP ;


      // Step 5: try various extrapolations (reflection, expansion and contraction)

      // 5.1: reflect the high point to the other side of the c.m. of the rest
      ytry = amotry(p, y, psum, ihi, &yhi, -1.0, time, amp, err, size, dr, temperature, pElite, &yElite, &iElite) ;
      numIterations-- ;

      if (ytry <= ylo)
	{
	  // 5.1.1: if the result was the lowest so far, expand it more
	  ytry = amotry(p, y, psum, ihi, &yhi, 2.0, time, amp, err, size, dr, temperature, pElite, &yElite, &iElite) ;
	  numIterations-- ;
	}
      else if (ytry >= ynhi)
	{
	  // 5.1.2: if the result is still the highest, try interpolating
	  ysave = yhi ;
	  ytry = amotry(p, y, psum, ihi, &yhi, 0.5, time, amp, err, size, dr, temperature, pElite, &yElite, &iElite) ;
	  numIterations-- ;

	  //  5.1.2.1: if the result is even worse, contract around the lowest (best) point
	  if (ytry >= ysave)
	    {
	      if ((iElite != -1) && (iElite != ilo))  // about to overwrite the elite
		{
		  memcpy (pElite, p[iElite], DIM * sizeof(double)) ;
		  iElite = -1 ;
		}

	      for (i = 0 ; i < (DIM+1) ; i++)
		if (i != ilo)
		  {
		    for (j = 0 ; j < DIM ; j++)
		      p[i][j] = 0.5 * (p[i][j] + p[ilo][j]) ;

		    y[i] = scoreFit(p[i], time, amp, err, size, dr) ;

		    if (y[i] < yElite)
		      {
			yElite = y[i] ;
			iElite = i ;
		      }
		  }
	      numIterations -= DIM ;

	      //  5.1.2.2: reinitialize the sum of values in each coordinate
	      for (j = 0 ; j < DIM ; j++)
		{
		  sum = 0.0 ;

		  for (i = 0 ; i <= DIM ; i++)
		    sum += p[i][j] ;

		  psum[j] = sum ;
		}
	    }
	}

      temperature *= coolingFactor ;

#ifdef GRAPHIC
#ifdef PLOT
      if ((numIterations % PLOT_REFRESH_ITERATIONS) == 0)
	{
	  cleardevice() ;
	  (void)plotFit (p[ihi], time, amp, size, 3, 0, 0.0) ;       // Worst - cyan

	  if (iElite == -1)
	    (void)plotFit (pElite, time, amp, size, 15, 0, 0.0) ;    // Elite (not in simplex) - white
	  else
	    (void)plotFit (p[iElite], time, amp, size, 14, 0, 0.0) ; // Elite (in simplex) - yellow
	}
#endif
#endif
    }

  // Step 6: [elitism] return the best result
  if (iElite == -1)
    {
      memcpy (p[0], pElite, DIM * sizeof(double)) ;
      iElite = 0 ;
    }

  return (iElite) ;
}



// This procedure attempts to fine tune the resulting model parameters.
// It tunes the parameters one at a time, shifting each one, in turn,
// a step up and a step down. This is repeated until the chi2 is no longer decreased.
// For error estimation purposes, one parameter p[paramConstNum] is not
// fit. By setting this parameters at a small offset from the optimal
// value, one can measure the chi2 sensitivity to it.
// Set paramConstNum to (-1) for a full greedy fit.
// Returns: 0 = converged ; 1 = didn't converge
int greedyFit(double p[DIM], double *py, float *time, float *amp, float *err,
	      int size, long numIterations, int paramConstNum)
{
  int i, doCopy, foundImprovement ;
  double yTmp, bestVal = 0.0 ;
  double paramBack, varyEpsilon = GREEDY_CONVERGE_EPSILON ;

  numIterations = (long)(numIterations * MAX_GREEDY_ITERATION_FRACTION) ;
  numIterations /= (2 * DIM) ;

  do
    {
      numIterations-- ;
      foundImprovement = 0 ;

      for (i = 0 ; i < DIM ; i++)
	if (i != paramConstNum)
	  {
	    doCopy = 0 ;
	    paramBack = p[i] ;

	    p[i] = paramBack * (1.0 - varyEpsilon) ;
	    yTmp = scoreFit(p, time, amp, err, size, MIN_INTEGRATION_STEP) ;
	    if (yTmp < (*py))
	      {
		*py = yTmp ;
		bestVal = p[i] ;
		doCopy = 1 ;
		foundImprovement = 1 ;
	      }

	    p[i] = paramBack * (1.0 + varyEpsilon) ;
	    yTmp = scoreFit(p, time, amp, err, size, MIN_INTEGRATION_STEP) ;
	    if (yTmp < (*py))
	      {
		*py = yTmp ;
		bestVal = p[i] ;
		doCopy = 1 ;
		foundImprovement = 1 ;
	      }

	    if (doCopy)
	      p[i] = bestVal ;
	    else
	      p[i] = paramBack ;
	  }

      if (foundImprovement)
	{
	  if (varyEpsilon <= HALF_MAX_GREEDY_EPSILON)
	    varyEpsilon *= 2.0 ;
	}
      else
	varyEpsilon *= 0.5 ;
    }
  while ((foundImprovement || (varyEpsilon > GREEDY_CONVERGE_EPSILON)) && (numIterations > 0)) ;

  return (foundImprovement || (varyEpsilon > GREEDY_CONVERGE_EPSILON)) ;
}



// Find the best fit for the given data, given initial values of the model parameters
// Returns the node index of the best fit
int runFit(double p[DIM+1][DIM], double y[DIM+1], float *time, float *amp, float *err,
	   int size, long numIterations, char *filename, char *errFilename)
{
  int best, isUnconverged ;

  best = amoeba(p, y, time, amp, err, size, numIterations) ;

  isUnconverged = greedyFit(p[best], &y[best], time, amp, err, size, numIterations, -1) ;

  if (isUnconverged)
    printError (errFilename, 0, filename, "runFit()", "greedyFit() didn't converge") ;


  // Takes care of the 180 degree turn degeneracy (makes sure that the R1 >= R2)
  if (p[best][D_R1] < p[best][D_R2])
    {
      swap (&p[best][D_R1], &p[best][D_R2]) ;
      swap (&p[best][D_B1], &p[best][D_B2]) ;
      p[best][D_TMO] -= 0.25 ;
      p[best][D_TPO] += 0.25 ;
    }

  return (best) ;
}

//---------------------- Post-analysis -------------------------------------

// Returns the estimated error of a given parameter p[paramNum]
// this is done by offsetting this parameter by a small amount (ERROR_ESTIMATE_EPSILON)
// and seeing how much the chi2 raised, after re-fitting the remaining parameters
// the estimated error is the extrapolated offset needed to double the chi2
// (compared to the minimum). We assume that the chi2 function is approximately a
// paraboloid around neat the minimum.
// p[DIM] = the given local best fit
// y = the chi2 of the given best fit
// isPhase = 0 for parameters whose error is proportional to their size
//           1 for phase-type parameters (modulo 1)
double estimateError (int paramNum, double p[DIM], double y, int isPhase,
		      float *time, float *amp, float *err, int size, long numIterations)
{
  double pOffset[DIM], yOffset1, yOffset2 ;

  numIterations = (long)(numIterations * MAX_ERROR_ESTIMATE_ITERATION_FRACTION) ;
  numIterations /= 2 ;

  memcpy (pOffset, p, DIM * sizeof(double)) ;
  pOffset[paramNum] *= (1.0 + ERROR_ESTIMATE_EPSILON) ;
  yOffset1 = scoreFit(pOffset, time, amp, err, size, MIN_INTEGRATION_STEP) ;
  greedyFit(pOffset, &yOffset1, time, amp, err, size, numIterations, paramNum) ;

  memcpy (pOffset, p, DIM * sizeof(double)) ;
  pOffset[paramNum] *= (1.0 - ERROR_ESTIMATE_EPSILON) ;
  yOffset2 = scoreFit(pOffset, time, amp, err, size, MIN_INTEGRATION_STEP) ;
  greedyFit(pOffset, &yOffset2, time, amp, err, size, numIterations, paramNum) ;

  if (yOffset1 > yOffset2)
    yOffset1 = yOffset2 ;   // Set yOffset1 as the minimum

  if (yOffset1 == y)  // This should almost never happen
    return (-1.0) ;

  if (yOffset1 < y)   // This shouldn't happen if greedyFit() converged
    swap (&yOffset1, &y) ;

  if (isPhase)
    return (ERROR_ESTIMATE_EPSILON * sqrt(y / (yOffset1 - y))) ;

  return (ERROR_ESTIMATE_EPSILON * fabs(p[paramNum]) * sqrt(y / (yOffset1 - y))) ;
}



// Given the period and the radii (in units of a)
// Returns the mean density of the binary system (or maximum if r1=0)
double meanDensity (double period, double r1, double r2)
{
  // 0.01893 = 3 * pi / (G * (seconds per day)^2)  [g/cm^3]
  return (0.01893 / ((cube(r1) + cube(r2)) * sqr(period))) ;
}


#ifdef GRAPHIC
#ifdef PLOT
// Plot the first guess with reference lines
void drawInitLines(double p[DIM+1][DIM], float *time, float *amp, int size,
		   double min1Time, double min2Time, double min1HalfWidth, double min2HalfWidth,
		   double min1Amp, double min2Amp, double medianAmp)
{
  int min1AmpPlot, min2AmpPlot, medianAmpPlot, goalAmpPlot ;

  min1AmpPlot = plotFit (0, time, amp, size, 14, 0, min1Amp) ;
  min2AmpPlot = plotFit (0, time, amp, size, 14, 0, min2Amp) ;
  medianAmpPlot = plotFit (p[0], time, amp, size, 14, 1, medianAmp) ;

  setcolor(7) ;
  line (0, medianAmpPlot, 639, medianAmpPlot) ;

  setcolor(5) ;
  line ((int)(640 * min1Time), min1AmpPlot-10, (int)(640 * min1Time), 450) ;
  line ((int)(640 * min1Time)-5, min1AmpPlot, (int)(640 * min1Time)+5, min1AmpPlot) ;

  setcolor(3) ;
  line ((int)(640 * min2Time), min2AmpPlot-10, (int)(640 * min2Time), 450) ;
  line ((int)(640 * min2Time)-5, min2AmpPlot, (int)(640 * min2Time)+5, min2AmpPlot) ;

  setcolor(4) ;
  goalAmpPlot = (medianAmpPlot + min1AmpPlot) / 2 ;
  line ((int)(640 * mod1(min1Time + min1HalfWidth)), goalAmpPlot, (int)(640 * mod1(min1Time + min1HalfWidth)), 450) ;
  line ((int)(640 * mod1(min1Time - min1HalfWidth)), goalAmpPlot, (int)(640 * mod1(min1Time - min1HalfWidth)), 450) ;

  goalAmpPlot = (medianAmpPlot + min2AmpPlot) / 2 ;
  line ((int)(640 * mod1(min2Time + min2HalfWidth)), goalAmpPlot, (int)(640 * mod1(min2Time + min2HalfWidth)), 450) ;
  line ((int)(640 * mod1(min2Time - min2HalfWidth)), goalAmpPlot, (int)(640 * mod1(min2Time - min2HalfWidth)), 450) ;

  //(void)getc (stdin) ;
}
#endif

// Prints the results of the fit onto the screen
// Note that I assume that p[D_R1] > p[D_R2] for calculating rhoMax
void printResultValue (double p[DIM], double y, float *time, float *amp, int size, int numRid,
		       double period, double avrChi2, double splineChi2, double sinChi2,
		       double sigmaMin2Amp, double sigmaMax1Amp, double sigmaMaxDiff, double plateauWaviness)
{
    #ifdef PLOT

  cleardevice() ;
  (void)plotFit (p, time, amp, size, 14, 1, 0.0) ;
  
  gotoxy (1,1) ;
  #endif
  
  
  printf ("period=%f  e=%f\n", period, p[D_ECC]) ;
  printf ("r1/a=%f r2/a=%f  B1=%f B2=%f\n", p[D_R1], p[D_R2],
	  -2.5 * log10(p[D_B1] * integrateWholeDisk(p[D_R1])),
	  -2.5 * log10(p[D_B2] * integrateWholeDisk(p[D_R2]))) ;
  printf ("sin(i)=%f  time0=%f  omega=%f  size=%d  numRid=%d\n", p[D_SIN_I], mod1(p[D_TPO] + p[D_TMO]),
	  360.0 * mod1(p[D_TPO] - p[D_TMO]), size, numRid) ;
  printf ("chi2=%f  avrChi2=%f splineChi2=%f sinChi2=%f\n", y, avrChi2, splineChi2, sinChi2) ;
  printf ("sig.min2=%.2f sig.max1=%.2f sig.maxDiff=%.2f waviness=%.2f\n", sigmaMin2Amp, sigmaMax1Amp, sigmaMaxDiff, plateauWaviness) ;
  printf ("midScatter=%f  ", midScatterScore (p, time, amp, size)) ;
  printf ("rhoMean=%f rhoMax=%f [g/cm^3]\n", meanDensity(period, p[D_R1], p[D_R2]), meanDensity(period, 0.0, p[D_R2])) ;
}
#endif



// Writes the final (best fit) results to a given file (fout)
void printFinalResult (double p[DIM], double y, float *time, float *amp, float *err, int size, int numRid, double period,
		       double avrChi2, double splineChi2, double sinChi2, double sigmaMin2Amp, double sigmaMax1Amp, 
		       double sigmaMaxDiff, double plateauWaviness, long numIterations, FILE *fout, char *filename, char *errFilename)
{
  int i ;
  double errR1, errR2, errTMPO, errB1, errB2 ;

  // Checks that all the values are valid (not Inf or NaN) - may cause problems in older compilers
  for (i = 0 ; (i < DIM) && (p[i] == p[i]) ; i++) ;

  if (i == DIM)
    {
      numIterations /= DIM ;

      errR1 = estimateError(D_R1, p, y, 0, time, amp, err, size, numIterations) ;
      errR2 = estimateError(D_R2, p, y, 0, time, amp, err, size, numIterations) ;
      errTMPO = sqrt(sqr(estimateError(D_TMO, p, y, 1, time, amp, err, size, numIterations)) +
		     sqr(estimateError(D_TPO, p, y, 1, time, amp, err, size, numIterations))) ;
      errB1 = sqrt(sqr(estimateError(D_B1, p, y, 0, time, amp, err, size, numIterations) / p[D_B1]) +
		   sqr(2.0 * errR1 / p[D_R1])) * MAGNITUDE_ERROR_FACTOR ;
      errB2 = sqrt(sqr(estimateError(D_B2, p, y, 0, time, amp, err, size, numIterations) / p[D_B2]) +
		   sqr(2.0 * errR2 / p[D_R2])) * MAGNITUDE_ERROR_FACTOR ;

      fprintf (fout, "%s %.12f ", filename, period) ;
      fprintf (fout, "%f %f ", p[D_ECC],
	       estimateError(D_ECC, p, y, 0, time, amp, err, size, numIterations)) ;
      fprintf (fout, "%f %f ", p[D_R1], errR1) ;
      fprintf (fout, "%f %f ", p[D_R2], errR2) ;
      fprintf (fout, "%f %f ", -2.5 * log10(p[D_B1] * integrateWholeDisk(p[D_R1])), errB1) ;
      fprintf (fout, "%f %f ", -2.5 * log10(p[D_B2] * integrateWholeDisk(p[D_R2])), errB2) ;
      fprintf (fout, "%f %f ", p[D_SIN_I],
	       estimateError(D_SIN_I, p, y, 0, time, amp, err, size, numIterations)) ;
      fprintf (fout, "%f %f ", mod1(p[D_TPO] + p[D_TMO]), errTMPO) ;
      fprintf (fout, "%f %f ", 360.0 * mod1(p[D_TPO] - p[D_TMO]), 360.0 * errTMPO) ;

      fprintf (fout, "%d %d %f %f %f %f ", size, numRid, y, avrChi2, splineChi2, sinChi2) ;
      fprintf (fout, "%f %f %f %f ", sigmaMin2Amp, sigmaMax1Amp, sigmaMaxDiff, plateauWaviness) ;
      fprintf (fout, "%f %f %f\n", midScatterScore (p, time, amp, size),
	       meanDensity(period, p[D_R1], p[D_R2]), meanDensity(period, 0.0, p[D_R2])) ;
    }
  else
    printError (errFilename, 0, filename, "printFinalResult()", "One of the fitted parameters is Inf or NaN") ;

#ifdef WRITE_CURVE_FIT
  i = writeCurveFit (p, time, amp, err, size, filename) ;
  
  if (i)
    printError (errFilename, 0, filename, "printFinalResult()", "Couldn't write a data or fit file") ;
#endif
  
  fflush(fout) ;
}


//-------------------------------------------------------

int main (int argc, char **argv)
{
  int i, isDoublePeriod, best, numRid, size, sizeOrig ;
  float *time, *amp, *err ;
  double tmpTime, tmpMag, tmpErr ;
  double min1Time, min2Time, tDiff, min1Amp, min2Amp, max1Amp, max2Amp ;
  double sin_i, r1, r2, B1, B2, e, period, omega, time0 ;
  double medianAmp, min1HalfWidth, min2HalfWidth, tmp, Y, varySin_i ;
  double goalAmp, plateauStdDiv, plateauWaviness, avrChi2, splineChi2, sinChi2 ;
  double sigmaMin1Amp, sigmaMin2Amp, sigmaMax1Amp, sigmaMaxDiff ;
  double p[DIM+1][DIM], pPrevBest[DIM], y[DIM+1], yPrevBest ;
  double quadA = DEFAULT_LIMB_QUAD_A, quadB = DEFAULT_LIMB_QUAD_B ;
  long numIterations = DEFAULT_NUM_ITERATIONS ;
  char filename[256], str[64] ;
  FILE *finLC, *fout, *finList ;

#ifdef GRAPHIC
#ifdef PLOT
  int ga = 0 , gb = 0 ;
  detectgraph (&ga, &gb) ;
  initgraph (&ga, &gb, "") ;
#endif

  //argc = 4 ;
  //argv[1] = "p.txt" ;
  //argv[2] = "pout.txt" ;
  //argv[3] = "perr.txt" ;

#endif


  if ((argc < 4) || (argc > 7))
    {
      printf ("\n Welcome to the DEBiL fitter ver %s  (DEBiL=Detached Eclipsing Binary Light-curve fitter)\n\n", VERSION) ;
      printf ("Usage: %s <input LC list filename> <output data file> <output error file>  [num iteration]  [<limb darkening A> <limb darkening B>]\n", argv[0]) ;
      printf (" Defaults: number of iterations = %d\n", DEFAULT_NUM_ITERATIONS) ;
      printf ("           quadratic limb darkening:  a=%f  b=%f\n", DEFAULT_LIMB_QUAD_A, DEFAULT_LIMB_QUAD_B) ;
      printf ("\n") ;
      return (1) ;
    }

  if (!strcmp(argv[1], argv[2]) ||
      !strcmp(argv[1], argv[3]) ||
      !strcmp(argv[2], argv[3]))
    {
      printf ("ERROR: all the input/output filenames must be different\n") ;
      return (2) ;
    }


  if (!(finList = fopen (argv[1], "rt")))
    {
      printf ("ERROR: couldn't open the input LC list file ('%s')\n", argv[1]) ;
      return (3) ;
    }

  if (!(fout = fopen (argv[2], "at")))
    {
      printf ("ERROR: couldn't open the output data file ('%s')\n", argv[2]) ;
      fclose (finList) ;
      return (4) ;
    }

  if ((argc == 5) || (argc == 7))
    numIterations = atol(argv[4]) ;

  if (numIterations < 0)
    {
      printf ("ERROR: invalid number of iteration (%ld)\n", numIterations) ;
      fclose (finList) ;
      fclose (fout) ;
      return (5) ;
    }

  if (argc == 6)
    {
      quadA = atof(argv[4]) ;
      quadB = atof(argv[5]) ;
    }
  else if (argc == 7)
    {
      quadA = atof(argv[5]) ;
      quadB = atof(argv[6]) ;
    }

  setLimbDarkening (quadA, quadB) ;

  printf (" Using settings: \n") ;
  printf ("  iterations = %ld\n", numIterations) ;
  printf ("  quadratic limb darkening params:  a=%f  b=%f\n", quadA, quadB) ;

  srand (RANDOM_SEED) ;

  //-----------------------------------------------------------------------

  while (2 == fscanf(finList, "%s %lf\n", filename, &period))
    {
      printf ("%s   P=%f\n", filename, period) ;
      isDoublePeriod = 0 ;

      if (period <= 0.0)
	{
	  printError (argv[3], 1, filename, "main()", "Invalid period") ;
	  continue ;
	}

      if (!(finLC = fopen (filename, "rt")))
	{
	  printError (argv[3], 1, filename, "main()", "Couldn't open the input LC file") ;
	  continue ;
	}

      //----------------------------------------------------------------

      sizeOrig = 0 ;
      while (1 == fscanf(finLC, "%*f %*f %lf\n", &tmpErr))
	if (tmpErr > 0.0)  // Sign of an invalid magnitude
	  sizeOrig++ ;

      if (sizeOrig < (3 * MIN_NUM_DATA))  // Need MIN_NUM_DATA for both the dips and the plateau
	{
	  printError (argv[3], 1, filename, "main()", "Not enough data points") ;
	  fclose (finLC) ;
	  continue ;
	}

      time = (float*)malloc (sizeOrig * sizeof(float)) ;
      amp = (float*)malloc (sizeOrig * sizeof(float)) ;
      err = (float*)malloc (sizeOrig * sizeof(float)) ;

      if ((!time) || (!amp) || (!err))
	{
	  if (time) free(time) ;
	  if (amp) free(amp) ;
	  if (err) free(err) ;

	  printError (argv[3], 1, filename, "main()", "Not enough memory") ;
	  fclose(finLC) ;
	  continue ;
	}

      //-------------------------

#ifdef DO_DOUBLE_PERIOD   
    MAKE_DOUBLE_PERIOD:
#endif
      rewind(finLC) ;
      size = sizeOrig ;  // size is reduced in ridOutliers() when doing a double-period loopback
      i = 0 ;

      while ((i < size) && (3 == fscanf(finLC, "%lf %lf %lf\n", &tmpTime, &tmpMag, &tmpErr)))
	if (tmpErr > 0.0)  // Sign of an invalid magnitude
	  {
	    time[i] = (float)mod1(tmpTime / period) ;
	    amp[i] = (float)pow(10.0, -0.4 * tmpMag) ;  // Convert magnitude (logarithmic) to amplitude (linear)
	    err[i] = (float)(amp[i] * tmpErr / MAGNITUDE_ERROR_FACTOR) ;  // Convert to absolute error
	    i++ ;
	  }

      if (i != size) 
	{
	  printError (argv[3], 1, filename, "main()", "Number mismatch") ;
	  goto ABORT_LIGHT_CURVE_FITTING ;
	}

      i = sortSamples(time, amp, err, size) ;
      if (i)
	{
	  printError (argv[3], 1, filename, "main()", "sortSamples() malloc failure") ;
	  goto ABORT_LIGHT_CURVE_FITTING ;
	}

#ifdef GRAPHIC
    #ifdef PLOT

      (void)plotFit (0, time, amp, size, 1, 1, 0.0) ;
      //(void)getc(stdin) ;
      cleardevice() ;
#endif
#endif
      splineChi2 = ridOutliers(time, amp, err, &size) ;
      numRid = sizeOrig - size ;

      if (size < (3 * MIN_NUM_DATA))  // Need MIN_NUM_DATA for both the dips and the plateau
	{
	  printError (argv[3], 1, filename, "main()", "Not enough non-outlier data points") ;
	  goto ABORT_LIGHT_CURVE_FITTING ;
	}

      //-------------------------------------------------

      // Find median:
      medianAmp = getMedian(amp, size) ;
      if (medianAmp == MAXFLOAT)
	{
	  printError (argv[3], 1, filename, "main()", "getMedian() malloc failure") ;
	  goto ABORT_LIGHT_CURVE_FITTING ;
	}

      //--------------------------------------------------
      // Get the location of the dips:

      // Coarse search (secondary may be an "edge minimum")
      findDips(time, amp, size, &min1Time, &min2Time, &min1Amp, &min2Amp) ;

      if (medianAmp < min2Amp)
	{
	  if (isDoublePeriod)
	    {                // This should never happen
	      printError (argv[3], 1, filename, "main()", "No secondary dip- double period was tried and failed (1)") ;
	      goto ABORT_LIGHT_CURVE_FITTING ;
	    }
	  else if ((2.0 * min1Amp) < medianAmp)
	    {
	      printError (argv[3], 1, filename, "main()", "No secondary dip- primary dip is too deep for doubling (1)") ;
	      goto ABORT_LIGHT_CURVE_FITTING ;
	    }
	  else  // isDoublePeriod = 0
	    {
#ifdef DO_DOUBLE_PERIOD
	      printError (argv[3], 0, filename, "main()", "No secondary dip- try double period (1)") ;
	      period *= 2.0 ;
	      isDoublePeriod = 1 ;
	      goto MAKE_DOUBLE_PERIOD ;
#else
	      printError (argv[3], 1, filename, "main()", "No secondary dip (1)") ;
	      goto ABORT_LIGHT_CURVE_FITTING ;
#endif
	    }
	}


      // Fine tune dips locations and finds their widths
      goalAmp = 0.5 * (medianAmp + min1Amp) ;  // Half width half min (coarse)
      (void)findHalfWidth(time, amp, size, goalAmp, &min1Time) ;
      min1Amp = interpolateSmooth (min1Time, time, amp, size) ;
      goalAmp = 0.5 * (medianAmp + min2Amp) ;  // Half width half min (coarse)
      (void)findHalfWidth(time, amp, size, goalAmp, &min2Time) ;
      min2Amp = interpolateSmooth (min2Time, time, amp, size) ;

      // find "maxs" midway between the dips
      findMidMaxs(time, amp, size, 0.5 * (min1Time + min2Time), &max1Amp, &max2Amp) ;

      // fine-tune median:
      i = findPlateauMedian(time, amp, size, min1Time, min2Time,
			    &medianAmp, &plateauStdDiv, &plateauWaviness) ;
      if (i)
	{
	  sprintf (str, "Error #%d in findPlateauMedian()", i) ;
	  printError (argv[3], 1, filename, "main()", str) ;
	  goto ABORT_LIGHT_CURVE_FITTING ;
	}

      goalAmp = 0.5 * (medianAmp + min1Amp) ;  // half width half min (fine tune)
      min1HalfWidth = findHalfWidth(time, amp, size, goalAmp, &min1Time) ;
      min1Amp = interpolateSmooth (min1Time, time, amp, size) ;
      goalAmp = 0.5 * (medianAmp + min2Amp) ;  // half width half min (fine tune)
      min2HalfWidth = findHalfWidth(time, amp, size, goalAmp, &min2Time) ;
      min2Amp = interpolateSmooth (min2Time, time, amp, size) ;

      sigmaMin1Amp = (medianAmp - min1Amp) / plateauStdDiv ;
      sigmaMin2Amp = (medianAmp - min2Amp) / plateauStdDiv ;
      sigmaMax1Amp = (max1Amp - medianAmp) / plateauStdDiv ;
      sigmaMaxDiff = (max1Amp - max2Amp) / plateauStdDiv ;

      //------------- Tests: ---------------------
      // Make sure that the dips are okay
      // I don't use err[] here, in case the data is inherently volatile

      if (sigmaMin1Amp < MIN_STDDIV_BELOW_MEDIAN)
	{
	  printError (argv[3], 1, filename, "main()", "Primary dip is too small") ;
	  goto ABORT_LIGHT_CURVE_FITTING ;
	}

      if (sigmaMax1Amp > MAX_STDDIV_ABOVE_MEDIAN)
	printError (argv[3], 0, filename, "main()", "Large hump at mid-plateau") ;

      if (sigmaMin2Amp < MIN_STDDIV_BELOW_MEDIAN)  // consider doubling the period
	{
	  if (isDoublePeriod)
	    {
	      printError (argv[3], 1, filename, "main()", "Secondary dip is too small- double period was tried and failed (2)") ;
	      goto ABORT_LIGHT_CURVE_FITTING ;
	    }
	  else if ((2.0 * min1Amp) < medianAmp)
	    {
	      printError (argv[3], 1, filename, "main()", "Secondary dip is too small- primary dip is too deep for doubling (2)") ;
	      goto ABORT_LIGHT_CURVE_FITTING ;
	    }
	  else  // isDoublePeriod = 0
	    {
#ifdef DO_DOUBLE_PERIOD
	      printError (argv[3], 0, filename, "main()", "Secondary dip is too small- try double period (2)") ;
	      period *= 2.0 ;
	      isDoublePeriod = 1 ;
	      goto MAKE_DOUBLE_PERIOD ;
#else
	      printError (argv[3], 1, filename, "main()", "No secondary dip (2)") ;
	      goto ABORT_LIGHT_CURVE_FITTING ;
#endif
	    }
	}

      if ((fabs(min1Time - min2Time) < (min1HalfWidth + min2HalfWidth)) ||
	  (fabs(min1Time - min2Time) > (1.0 - min1HalfWidth - min2HalfWidth)))
	{
	  if (isDoublePeriod)
	    {
	      printError (argv[3], 1, filename, "main()", "Dips are overlapping- double period was tried and failed (3)") ;
	      goto ABORT_LIGHT_CURVE_FITTING ;
	    }
	  else if ((2.0 * min1Amp) < medianAmp)
	    {
	      printError (argv[3], 1, filename, "main()", "Dips are overlapping- primary dip is too deep for doubling (3)") ;
	      goto ABORT_LIGHT_CURVE_FITTING ;
	    }
	  else  // isDoublePeriod = 0
	    {
#ifdef DO_DOUBLE_PERIOD
	      printError (argv[3], 0, filename, "main()", "Dips are overlapping- try double period (3)") ;
	      period *= 2.0 ;
	      isDoublePeriod = 1 ;
	      goto MAKE_DOUBLE_PERIOD ;
#else
	      printError (argv[3], 1, filename, "main()", "Dips are overlapping (3)") ;
	      goto ABORT_LIGHT_CURVE_FITTING ;
#endif
	    }
	}

      if ((min1HalfWidth == 0.0) || (min2HalfWidth == 0.0))
	{
	  printError (argv[3], 1, filename, "main()", "Couldn't reach goal amplitude") ;
	  goto ABORT_LIGHT_CURVE_FITTING ;
	}

      if ((min1HalfWidth >= 0.25) || (min2HalfWidth >= 0.25))
	{
	  printError (argv[3], 1, filename, "main()", "Out of range half width") ;
	  goto ABORT_LIGHT_CURVE_FITTING ;
	}

      if (!isEnoughDipData(time, size, min1Time, min1HalfWidth) ||
	  !isEnoughDipData(time, size, min2Time, min2HalfWidth))
	{
	  printError (argv[3], 1, filename, "main()", "Not enough data to constrain one of the dips") ;
	  goto ABORT_LIGHT_CURVE_FITTING ;
	}

      if ((min1Amp + min2Amp) < medianAmp)
	{
	  printError (argv[3], 1, filename, "main()", "The dips are too deep") ;
	  goto ABORT_LIGHT_CURVE_FITTING ;
	}

      // -----------------------------------------------------

      // Chi2 tests:

      avrChi2 = getAvrChi2 (amp, err, size) ;
      sinChi2 = getSinChi2 (time, amp, err, size) ;

      // Calculate the fitting starting point:

      tDiff = fabs(min2Time - min1Time) ;
      time0 = 0.5 * (min1Time + min2Time) ;  // part 1/3

      // Convert big-dip/small-dip into first-dip/second-dip  (i.e. before/after perihelion)
      if ((tDiff > 0.5) ^ (min1Time > min2Time))
	{
	  swap (&min1Time, &min2Time) ;
	  swap (&min1Amp, &min2Amp) ;
	  swap (&min1HalfWidth, &min2HalfWidth) ;
	}

      if (tDiff > 0.5)
	{
	  tDiff = 1.0 - tDiff ;
	  time0 += 0.5 ;  // part 2/3
	}

      //------------------

      // Y = e * sin(omega)
      Y = (min1HalfWidth - min2HalfWidth) / (min1HalfWidth + min2HalfWidth) ;
      e = getEccentricity(tDiff, Y) ;
      omega = asin(Y / e) ;

      tmp = acos(cos(omega) / sqrt(1.0 - (Y*Y))) ;
      if (omega < 0.0)
	tmp = -tmp ;

      tmp -= (e * sqrt(1.0 - (e*e)) * Y * cos(omega)) / (1.0 - (Y*Y)) ;

      time0 += (tmp / (2.0 * M_PI)) ;
      time0 = mod1(time0) ;

      //----------------------------------------

      if ((e < 0.0) || (e >= 1.0))
	{
	  printError (argv[3], 1, filename, "main()", "Out of range eccentricity") ;
	  goto ABORT_LIGHT_CURVE_FITTING ;
	}

      //------- [r1 < r2] ------------

      if (min1Amp < min2Amp)    // I chose robustness over accuracy
	r2 = sin(2.0 * M_PI * min1HalfWidth) ;
      else
	r2 = sin(2.0 * M_PI * min2HalfWidth) ;

      if (r2 > ((1.0 - e) / 2.1))  // In case of a large r  (must hold: r1+r2 < 1-e)
	r2 = (1.0 - e) / 2.1 ;     // Theoretically this should be 2.0, but I'm allowing some extra play

      B2 = min2Amp / integrateWholeDisk(r2) ;

      r1 = invIntegrateDiskFromStart((medianAmp - min1Amp) / B2, r2) ;
      if (r1 <= 0.0)
	{
	  printError (argv[3], 1, filename, "main()", "Out of bound r1") ;
	  yPrevBest = MAXFLOAT ;
	  goto SECOND_ORIENTATION_FITTING ;
	}

      B1 = (medianAmp - min2Amp) / integrateWholeDisk(r1) ;

      //-------------------------------------------------

      if (min1Amp < min2Amp)    // I chose robustness over accuracy
	sin_i = getSin_i (time, amp, size, e, -Y, r1, r2, &varySin_i,
			  min1Time, min1Amp, medianAmp, min1HalfWidth, filename, argv[3], 1) ;
      else
	sin_i = getSin_i (time, amp, size, e, Y, r1, r2, &varySin_i,
			  min2Time, min2Amp, medianAmp, min2HalfWidth, filename, argv[3], 1) ;

      //-------------------------------------------------
      // Fit I:
      for (i = 0 ; i < DIM+1 ; i++)
	{
	  p[i][D_ECC] = e - ((i == 1) * 0.01 * e) ;
	  p[i][D_R1] = r1 - ((i == 2) * 0.1 * r1) ;
	  p[i][D_R2] = r2 - ((i == 3) * 0.1 * r2) ;
	  p[i][D_B1] = B1 + ((i == 4) * 0.1 * B1) ;
	  p[i][D_B2] = B2 + ((i == 5) * 0.1 * B2) ;
	  p[i][D_SIN_I] = sin_i - ((i == 6) * varySin_i) ;
	  p[i][D_TMO] = (0.5 * time0) - (omega / (4.0 * M_PI)) + ((i == 7) * 0.01) ;
	  p[i][D_TPO] = (0.5 * time0) + (omega / (4.0 * M_PI)) + ((i == 8) * 0.1) ;

	  y[i] = scoreFit (p[i], time, amp, err, size, MIN_INTEGRATION_STEP) ;
	}

#ifdef GRAPHIC
    #ifdef PLOT

      drawInitLines(p, time, amp, size, min1Time, min2Time, min1HalfWidth, min2HalfWidth,
		    min1Amp, min2Amp, medianAmp) ;
#endif
#endif
      best = runFit(p, y, time, amp, err, size, numIterations, filename, argv[3]) ;

#ifdef GRAPHIC
      printResultValue (p[best], y[best], time, amp, size, numRid, period, avrChi2, splineChi2,
			sinChi2, sigmaMin2Amp, sigmaMax1Amp, sigmaMaxDiff, plateauWaviness) ;
#endif

#ifdef DOUBLE_PERIOD_SHORTCUT
      if (isDoublePeriod)   // If B1,B2 and r1,r2 are so close that they make only one minimum
	{
	  printFinalResult (p[best], y[best], time, amp, err, size, numRid, period, avrChi2, splineChi2, sinChi2,
			    sigmaMin2Amp, sigmaMax1Amp, sigmaMaxDiff, plateauWaviness, numIterations, fout, filename, argv[3]) ;
	  goto ABORT_LIGHT_CURVE_FITTING ;
	}
#endif

      for (i = 0 ; i < DIM ; i++)
	pPrevBest[i] = p[best][i] ;

      yPrevBest = y[best] ;

#ifdef GRAPHIC
      //(void)getc(stdin) ;
#endif

      //------------ [r1 > r2] -------------------------------------

    SECOND_ORIENTATION_FITTING:

      if (min1Amp < min2Amp)    // I chose robustness over accuracy
	r1 = sin(2.0 * M_PI * min1HalfWidth) ;
      else
	r1 = sin(2.0 * M_PI * min2HalfWidth) ;

      if (r1 > ((1.0 - e) / 2.1))  // In case of a large r  (must hold: r1+r2 < 1-e)
	r1 = (1.0 - e) / 2.1 ;     // Theoretically this should be 2.0, but I'm allowing some extra play

      B1 = min1Amp / integrateWholeDisk(r1) ;

      r2 = invIntegrateDiskFromStart((medianAmp - min2Amp) / B1, r1) ;
      if (r2 <= 0.0)
	{
	  printError (argv[3], 1, filename, "main()", "Out of bound r2") ;
	  goto ABORT_LIGHT_CURVE_FITTING ;
	}

      B2 = (medianAmp - min1Amp) / integrateWholeDisk(r2) ;

      //-------------------------------------------------

      if (min1Amp < min2Amp)    // I chose robustness over accuracy
	sin_i = getSin_i (time, amp, size, e, -Y, r2, r1, &varySin_i,
			  min1Time, min1Amp, medianAmp, min1HalfWidth, filename, argv[3], 0) ;
      else
	sin_i = getSin_i (time, amp, size, e, Y, r2, r1, &varySin_i,
			  min2Time, min2Amp, medianAmp, min2HalfWidth, filename, argv[3], 0) ;
      //-------------------------------------------------
      // Fit II:
      for (i = 0 ; i < (DIM+1) ; i++)
	{
	  p[i][D_ECC] = e - ((i == 1) * 0.01 * e) ;
	  p[i][D_R1] = r1 - ((i == 2) * 0.1 * r1) ;
	  p[i][D_R2] = r2 - ((i == 3) * 0.1 * r2) ;
	  p[i][D_B1] = B1 + ((i == 4) * 0.1 * B1) ;
	  p[i][D_B2] = B2 + ((i == 5) * 0.1 * B2) ;
	  p[i][D_SIN_I] = sin_i - ((i == 6) * varySin_i) ;
	  p[i][D_TMO] = (0.5 * time0) - (omega / (4.0 * M_PI)) + ((i == 7) * 0.01) ;
	  p[i][D_TPO] = (0.5 * time0) + (omega / (4.0 * M_PI)) + ((i == 8) * 0.1) ;

	  y[i] = scoreFit (p[i], time, amp, err, size, MIN_INTEGRATION_STEP) ;
	}


#ifdef GRAPHIC
    #ifdef PLOT

      drawInitLines(p, time, amp, size, min1Time, min2Time, min1HalfWidth, min2HalfWidth,
		    min1Amp, min2Amp, medianAmp) ;
#endif
#endif
      best = runFit(p, y, time, amp, err, size, numIterations, filename, argv[3]) ;

#ifdef GRAPHIC
      printResultValue (p[best], y[best], time, amp, size, numRid, period, avrChi2, splineChi2,
			sinChi2, sigmaMin2Amp, sigmaMax1Amp, sigmaMaxDiff, plateauWaviness) ;
#endif

      //------------------------------------------------      

      if (y[best] < yPrevBest)
	printFinalResult (p[best], y[best], time, amp, err, size, numRid, period, avrChi2, splineChi2, sinChi2,
			  sigmaMin2Amp, sigmaMax1Amp, sigmaMaxDiff, plateauWaviness, numIterations, fout, filename, argv[3]) ;
      else
	printFinalResult (pPrevBest, yPrevBest, time, amp, err, size, numRid, period, avrChi2, splineChi2, sinChi2,
			  sigmaMin2Amp, sigmaMax1Amp, sigmaMaxDiff, plateauWaviness, numIterations, fout, filename, argv[3]) ;

    ABORT_LIGHT_CURVE_FITTING:
      fclose (finLC) ;
      free (time) ;
      free (amp) ;
      free (err) ;

#ifdef GRAPHIC
      // (void)getc(stdin) ;
#endif
    }

  fclose (finList) ;
  fclose (fout) ;

  return (0) ;
}


/*
  To-do:
  1. find best cooling rate (dynamic mutation rate: as the solutions converges, raise the temperature ?)
  2. loop-around convergence for sin_i


  Note 1.
  Calculating the error of the parameters is problematic for two reasons. The first is that we
  must determine the size of perturbation that would make a "significant" change in the
  optimization score. It is not clear what this "significant" value is. The second, and
  probably more sever problem is that while changing each parameter in isolation will
  make a relatively large change in the score, there are pairs of parameters (e.g. for e=0, there
  is a degeneracy for 2*pi*time0 - omega = const). So lowering one while raising the other will
  have a very small change in the score.

  Note 2.
  Why does the dip separation vary even when the eccentricity is fixed?
  Because when omega = pi/2  (i.e. eclipses occur at perihelion and aphelion), the distance between eclipses
  will always be exactly half the period (perfectly symmetric). We assume here that omega = 0 (lower bound?).
  That means that from the time difference between dips we can only compute a minimum eccentricity.
*/
