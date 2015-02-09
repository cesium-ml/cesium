#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#include <gsl/gsl_vector.h>
#include <gsl/gsl_matrix.h>
#include <gsl/gsl_multifit.h>
#include <gsl/gsl_rng.h>

void *phoebe_malloc (size_t size);
/* #include <phoebe/phoebe.h> */
#include "polyfit.h"

#define DEBUG 0
#define LCPOINTS 400

void *phoebe_malloc (size_t size)
{
  /**
   * phoebe_malloc:
   *
   * Allocates the space with the check whether the memory was exhausted.
   */
  register void *value = malloc (size);
  if (value == 0)
    {
      printf ("Virtual memory exhauseted.\n");
      exit (-1);
    }
  return value;
}


polyfit_options *polyfit_options_default ()
{
	polyfit_options *options = phoebe_malloc (sizeof (*options));

	options->polyorder    = 2;
	options->iters        = 10000;
	options->step_size    = 0.001;
	options->knots        = 4;
	options->find_knots   = FALSE;
	options->find_step    = TRUE;
	options->chain_length = 10;
	options->ann_compat   = FALSE;

	return options;
}

int polyfit_options_free (polyfit_options *options)
{
	free (options);

	return SUCCESS;
}

polyfit_solution *polyfit_solution_init (polyfit_options *options)
{
	polyfit_solution *solution = phoebe_malloc (sizeof (*solution));
	int k;

	solution->knots = phoebe_malloc (options->knots * sizeof (*(solution->knots)));

	solution->ck = phoebe_malloc (options->knots * sizeof (*(solution->ck)));
	for (k = 0; k < options->knots; k++)
		solution->ck[k] = phoebe_malloc ((options->polyorder+1) * sizeof (**(solution->ck)));

	solution->npts = phoebe_malloc (options->knots * sizeof (*(solution->npts)));

	return solution;
}

int polyfit_solution_free (polyfit_solution *solution, polyfit_options *options)
{
	int k;

	free (solution->knots);
	for (k = 0; k < options->knots; k++)
		free (solution->ck[k]);
	free (solution->ck);
	free (solution);

	return SUCCESS;
}

/* Maximum number of observed data points: */
#define NMAX 10000

int polyfit_sort_by_phase (const void *a, const void *b)
{
	const polyfit_triplet *da = (const polyfit_triplet *) a;
	const polyfit_triplet *db = (const polyfit_triplet *) b;

	return (da->x > db->x) - (da->x < db->x);
}

int polyfit_sort_by_value (const void *a, const void *b)
{
	const double *da = (const double *) a;
	const double *db = (const double *) b;

	return (*da > *db) - (*da < *db);
}

int polyfit_find_knots (polyfit_triplet *data, int nobs, double **knots, polyfit_options *options)
{
	int i, j;
	double average = 0.0;
	int chain_too_short;
	int chain_wrapped = 0;

	int chains = 0;
	struct {
		int len;
		int start;
		int end;
	} chain[2];

	for (i = 0; i < nobs; i++)
		average += data[i].y;
	average /= (double) nobs;

	if (!options->ann_compat) {
		printf ("# searching for knots automatically:\n");
		printf ("# * average value of the flux: %lf\n", average);
	}

	/* To allow wrapping of the phase interval, skip the first chain: */
	i = 0;
	while (data[i].y < average) {
		if (DEBUG)
			printf ("# delaying point  %8.4lf (%3d): %lf < %lf\n", data[i].x, i, data[i].y, average);
		i++;
	}

	for ( ; i < nobs; i++) {
		if (data[i].y > average) {
			if (DEBUG)
				printf ("# skipping point  %8.4lf (%3d): %lf > %lf\n", data[i].x, i, data[i].y, average);
			continue;
		}

		/* Check if the chain is at least CHAIN_LENGTH long: */
		chain_too_short = 0;
		if (DEBUG)
			printf ("# chain starts at %8.4lf (%3d): %lf < %lf\n", data[i].x, i, data[i].y, average);
		for (j = 1; j < options->chain_length; j++) {
			if (i+j == nobs) {
				i = -j;
				chain_wrapped = 1;
			}
			if (data[i+j].y > average) {
				if (DEBUG)
					printf ("# chain broken at %8.4lf (%3d): %lf > %lf\n", data[i+j].x, i+j, data[i+j].y, average);
				i += j;
				chain_too_short = 1;
				break;
			}
			else
				if (DEBUG)
					printf ("# chain cont'd at %8.4lf (%3d): %lf < %lf\n", data[i+j].x, i+j, data[i+j].y, average);
		}
		
		if (chain_wrapped && chain_too_short) break;
		if (chain_too_short) continue;

		while (data[i+j].y < average) {
			if (i+j == nobs) {
				i = -j;
				chain_wrapped = 1;
			}
			if (DEBUG)
				printf ("# chain cont'd at %8.4lf (%3d): %lf < %lf\n", data[i+j].x, i+j, data[i+j].y, average);
			j++;
		}

		if (chains < 2) {
			chains++;
			chain[chains-1].len = j-1;
			chain[chains-1].start = chain_wrapped*nobs + i;
			chain[chains-1].end = i+j-1;
		}
		else {
			chains++; /* Just to count all chains */
			if (j-1 > chain[0].len) {
				if (chain[0].len > chain[1].len) {
					chain[1].len = chain[0].len;
					chain[1].start = chain[0].start;
					chain[1].end = chain[0].end;
				}
				chain[0].len = j-1;
				chain[0].start = chain_wrapped*nobs + i;
				chain[0].end = i+j-1;
			}
			else if (j-1 > chain[1].len) {
				chain[1].len = j-1;
				chain[1].start = chain_wrapped*nobs + i;
				chain[1].end = i+j-1;
			}
			/* else drop through without recording it because it is shorter. */
		}

		if (!options->ann_compat)
			printf ("# * found a chain from %lf (index %d/%d) to %lf (index %d/%d)\n", data[chain_wrapped*nobs+i].x, chain_wrapped*nobs+i, nobs-1, data[i+j-1].x, i+j-1, nobs-1);
		i += j-1;
		if (chain_wrapped) break;
	}

	if (!options->ann_compat)
		printf ("# * total number of chains found: %d\n", chains);

	/* If the number of chains is less than 2, the search for knots failed. */
	if (chains < 2)
		return -1;

	options->knots = 4;
	*knots = malloc (options->knots * sizeof (**knots));
	(*knots)[0] = data[chain[0].start].x; (*knots)[1] = data[chain[0].end].x;
	(*knots)[2] = data[chain[1].start].x; (*knots)[3] = data[chain[1].end].x;

	return 0;
}

int polyfit (polyfit_solution *result, polyfit_triplet *data, int nobs, double *knots, int PRINT, polyfit_options *options)
{
	int i, j, k, intervals, kfinal, cum, int1index;
	double chisq, chi2tot, knot, dknot;

	gsl_vector **x, **y, **w, **c;
	gsl_matrix **A, **cov;
	gsl_multifit_linear_workspace **mw;

	for (k = 0; k < options->knots; k++) {
		result->knots[k] = knots[k];
		result->npts[k] = 0;
	}

	/* Fast-forward to the first knot: */
	i = 0; cum = 0;
	while (data[i].x < knots[0]) { i++; cum++; }
	result->npts[options->knots-1] = i;
	int1index = cum;

	for (j = 0; j < options->knots-1; j++) {
		while (data[i].x < knots[j+1] && i < nobs) i++;
		result->npts[j] += i-cum; /* we need += because of the wrapped interval */
		if (result->npts[j] <= options->polyorder) {
			/* The intervals between knots don't have enough points; bail out. */
			result->chi2 = 1e10;
			return -1;
		}
		cum += result->npts[j];
	}

	/* Add post-last knot data to the last interval: */
	result->npts[j] += nobs-cum;
	if (result->npts[j] <= options->polyorder) {
		/* The intervals between knots don't have enough points; bail out. */
		result->chi2 = 1e10;
		return -1;
	}

	/* Allocate arrays of vectors of interval data: */
	x = malloc (options->knots * sizeof (*x));
	y = malloc (options->knots * sizeof (*y));
	w = malloc (options->knots * sizeof (*w));

	for (j = 0; j < options->knots; j++) {
		x[j] = gsl_vector_alloc (result->npts[j]);
		y[j] = gsl_vector_alloc (result->npts[j]);
		w[j] = gsl_vector_alloc (result->npts[j]);
	}

	/* Copy the (phase-shifted) data to these vectors: */
	cum = 0;
	for (j = 0; j < options->knots-1; j++) {
		for (i = 0; i < result->npts[j]; i++) {
			gsl_vector_set (x[j], i, data[int1index+cum+i].x - knots[j]);
			gsl_vector_set (y[j], i, data[int1index+cum+i].y);
			gsl_vector_set (w[j], i, data[int1index+cum+i].z);
			if (DEBUG)
				printf ("%d: %lf\t%lf\t%lf\n", j, data[int1index+cum+i].x - knots[j], data[int1index+cum+i].y, data[int1index+cum+i].z);
		}
		cum += result->npts[j];
	}

	/* Copy the wrapped interval data to these vectors: */
	knot = knots[j];
	for (i = 0; i < result->npts[j]; i++) {
		if (int1index+cum+i == nobs) {
			cum = -int1index-i;
			knot -= 1.0;
		}
		gsl_vector_set (x[j], i, data[int1index+cum+i].x - knot);
		gsl_vector_set (y[j], i, data[int1index+cum+i].y);
		gsl_vector_set (w[j], i, data[int1index+cum+i].z);
		if (DEBUG)
			printf ("%d: %lf\t%lf\t%lf\n", j, data[int1index+cum+i].x - knot, data[int1index+cum+i].y, data[int1index+cum+i].z);
	}

	/* If polynomial order is 1, the last interval is determined by constraints: */
	if (options->polyorder == 1) intervals = options->knots-1; else intervals = options->knots;

	/* Allocate all vectors and matrices: */
	A   = malloc (intervals * sizeof (*A));
	c   = malloc (intervals * sizeof (*c));
	cov = malloc (intervals * sizeof (*cov));
	mw  = malloc (intervals * sizeof (*mw));

	/* The first interval has all polynomial coefficients free. */
	A[0]   = gsl_matrix_alloc (result->npts[0], options->polyorder+1);
	c[0]   = gsl_vector_alloc (options->polyorder+1);
	cov[0] = gsl_matrix_alloc (options->polyorder+1, options->polyorder+1);
	mw[0]  = gsl_multifit_linear_alloc (result->npts[0], options->polyorder+1);

	/* Intervals 1...(N-1) are constrained by the connectivity constraint. */
	for (j = 1; j < options->knots-1; j++) {
		A[j]   = gsl_matrix_alloc (result->npts[j], options->polyorder);
		c[j]   = gsl_vector_alloc (options->polyorder);
		cov[j] = gsl_matrix_alloc (options->polyorder, options->polyorder);
		mw[j]  = gsl_multifit_linear_alloc (result->npts[j], options->polyorder);
	}

	/* The last interval has two constraints (connectivity and periodicity). */
	if (j < intervals) {
		A[j]   = gsl_matrix_alloc (result->npts[j], options->polyorder-1);
		c[j]   = gsl_vector_alloc (options->polyorder-1);
		cov[j] = gsl_matrix_alloc (options->polyorder-1, options->polyorder-1);
		mw[j]  = gsl_multifit_linear_alloc (result->npts[j], options->polyorder-1);
	}

	/* Set all elements to all matrices: */
	for (j = 0; j < intervals; j++) {
		if      (j == 0)       kfinal = options->polyorder+1;
		else if (j == options->knots-1) kfinal = options->polyorder-1;
		else                   kfinal = options->polyorder;
		for (i = 0; i < result->npts[j]; i++)
			for (k = 0; k < kfinal; k++)
				gsl_matrix_set (A[j], i, k, pow (gsl_vector_get (x[j], i), options->polyorder-k));
	}

	/*********************   FITTING THE 1ST INTERVAL:   **********************/

	gsl_multifit_wlinear (A[0], w[0], y[0], c[0], cov[0], &chisq, mw[0]);

	for (k = 0; k < options->polyorder+1; k++)
		result->ck[0][k] = gsl_vector_get (c[0], k);
	chi2tot = chisq;

	/********************   FITTING INTERVALS 2-(N-1):   **********************/

	for (j = 1; j < options->knots-1; j++) {
		/* Satisfy the connectivity constraint: */
		result->ck[j][options->polyorder] = result->ck[j-1][options->polyorder];
		for (k = 0; k < options->polyorder; k++)
			result->ck[j][options->polyorder] += result->ck[j-1][k] * pow (knots[j]-knots[j-1], options->polyorder-k);

		/* Apply the connectivity constraint: */
		for (i = 0; i < result->npts[j]; i++)
			gsl_vector_set (y[j], i, gsl_vector_get (y[j], i) - result->ck[j][options->polyorder]);

		gsl_multifit_wlinear (A[j], w[j], y[j], c[j], cov[j], &chisq, mw[j]);
		chi2tot += chisq;

		for (k = 0; k < options->polyorder; k++)
			result->ck[j][k] = gsl_vector_get (c[j], k);
	}

	/********************   FITTING THE LAST INTERVAL:   **********************/

	/* Satisfy the connectivity constraint: */
	result->ck[j][options->polyorder] = result->ck[j-1][options->polyorder];
	for (k = 0; k < options->polyorder; k++)
		result->ck[j][options->polyorder] += result->ck[j-1][k] * pow (knots[j]-knots[j-1], options->polyorder-k);

	/* Satisfy the periodicity constraint: */
	result->ck[j][options->polyorder-1] = (result->ck[0][options->polyorder]-result->ck[j][options->polyorder])/(knots[0]-knots[j]+1.0);

	/* Apply both constraints: */
	for (i = 0; i < result->npts[j]; i++)
		gsl_vector_set (y[j], i, gsl_vector_get (y[j], i) - result->ck[j][options->polyorder] - result->ck[j][options->polyorder-1] * gsl_vector_get (x[j], i));

	if (options->polyorder > 1) {
		for (k = 0; k < options->polyorder-1; k++)
			for (i = 0; i < result->npts[j]; i++)
				gsl_matrix_set (A[j], i, k, gsl_matrix_get (A[j], i, k) - gsl_vector_get (x[j], i) * pow(knots[0]-knots[j]+1, options->polyorder-k-1));

		gsl_multifit_wlinear (A[j], w[j], y[j], c[j], cov[j], &chisq, mw[j]);

		for (k = 0; k < options->polyorder-1; k++)
			result->ck[j][k] = gsl_vector_get (c[j], k);
		chi2tot += chisq;
	}
	else {
		/*
		 * If we are fitting linear polynomials, there's nothing to fit here
		 * because both knots are constrained (connectivity and periodicity).
		 * However, we still need to traverse data points to get chi2.
		 */

		chisq = 0.0;
		for (i = 0; i < result->npts[j]; i++)
			chisq += gsl_vector_get (w[j], i) * gsl_vector_get (y[j], i) * gsl_vector_get (y[j], i);
		chi2tot += chisq;
	}

	result->chi2  = chi2tot;

	/* Done! Wrap it up: */
	for (i = 0; i < options->knots-1; i++) {
		gsl_vector_free (x[i]);
		gsl_vector_free (y[i]);
		gsl_vector_free (w[i]);
	}

	free (x);
	free (y);
	free (w);

	for (i = 0; i < intervals; i++) {
		gsl_vector_free (c[i]);
		gsl_matrix_free (A[i]);
		gsl_matrix_free (cov[i]);
		gsl_multifit_linear_free (mw[i]);
	}

	free (c);
	free (A);
	free (cov);
	free (mw);

	return SUCCESS;
}

int polyfit_print (polyfit_solution *result, polyfit_options *options, int VERBOSE, int PRINT_SOLUTION)
{
	int i, j, k;
	double knot, dknot;

	if (VERBOSE && !options->ann_compat) {
		printf ("# Phase space partitioning:\n# \n");
		for (k = 0; k < options->knots-1; k++)
			printf ("#   interval %2d: [% 3.3lf, % 3.3lf), %3d data points\n", k, result->knots[k], result->knots[k+1], result->npts[k]);
		printf ("#   interval %2d: [% 3.3lf, % 3.3lf), %3d data points\n", k, result->knots[k], result->knots[0], result->npts[k]);
	}

	/* Write out a header: */
	if (VERBOSE && !options->ann_compat) {
		printf ("# \n# Weighted least-squares solution of the polyfit:\n# \n");
		printf ("#    knot\t");
		for (k = 0; k < options->polyorder+1; k++)
			printf ("   c[%d]\t\t", k);
		printf ("\n");
	}

	if (VERBOSE) {
		if (options->ann_compat)
			printf ("%lf\n", result->knots[0]);
		else
			printf ("# % lf\t", result->knots[0]);
		for (k = 0; k < options->polyorder+1; k++) {
			if (options->ann_compat)
				printf ("%lf\n", result->ck[0][options->polyorder-k]);
			else
				printf ("% lf\t", result->ck[0][options->polyorder-k]);
		}
		if (!options->ann_compat)
			printf ("\n");
	}

	for (j = 1; j < options->knots-1; j++) {
		if (VERBOSE) {
			if (options->ann_compat)
				printf ("%lf\n", result->knots[j]);
			else
				printf ("# % lf\t", result->knots[j]);
			for (k = 0; k < options->polyorder+1; k++) {
				if (options->ann_compat)
					printf ("%lf\n", result->ck[j][options->polyorder-k]);
				else
					printf ("% lf\t", result->ck[j][options->polyorder-k]);
			}
			if (!options->ann_compat)
				printf ("\n");
		}
	}

	if (VERBOSE) {
		if (options->ann_compat)
			printf ("%lf\n", result->knots[j]);
		else
			printf ("# % lf\t", result->knots[j]);
		for (k = 0; k < options->polyorder+1; k++) {
			if (options->ann_compat)
				printf ("%lf\n", result->ck[j][options->polyorder-k]);
			else
				printf ("% lf\t", result->ck[j][options->polyorder-k]);
		}
		if (!options->ann_compat)
			printf ("\n");
	}

	if (!options->ann_compat && PRINT_SOLUTION) {
		double phase, flux;
		printf ("# \n# Theoretical light curve:\n# \n   Phase\t   Flux\n");
		for (i = 0; i <= LCPOINTS; i++) {
            phase = -0.5 + (double) i / (double) LCPOINTS;
			flux = polyfit_compute (result, options, phase);
			printf ("  % lf\t% lf\n", phase, flux);
		}
	}
}

double polyfit_compute (polyfit_solution *result, polyfit_options *options, double phase)
{
	int j, k;
	double knot, dknot, flux;

	if (phase < result->knots[0]) {
		j = options->knots-1;
		knot = result->knots[j]-1.0;
		dknot = result->knots[0]-result->knots[options->knots-1]+1.0;
	}
	else if (phase > result->knots[options->knots-1]) {
		j = options->knots-1;
		knot = result->knots[j];
		dknot = result->knots[0]-result->knots[options->knots-1]+1.0;
	}
	else {
		j = 0;
		while (result->knots[j+1] < phase && j < options->knots-1) j++;
		knot = result->knots[j];
		dknot = result->knots[j+1]-result->knots[j];
	}

	flux = result->ck[j][options->polyorder];
	for (k = 0; k < options->polyorder; k++) {
		flux += result->ck[j][k] * pow (phase-knot, options->polyorder-k);
		if (j == options->knots-1 && k < options->polyorder-1)
			flux -= result->ck[j][k] * (phase-knot) * pow (dknot, options->polyorder-k-1);
	}

	return flux;
}




int main (int argc, char **argv)
{
	int i, nobs, iter, status;
	polyfit_triplet *data;
	FILE *in;
	double col1, col2, col3, chi2, chi2test, u;
	char line[255];

	double *knots = NULL;
	double *test;

	polyfit_options *options;
    polyfit_solution *result;
    
    
	gsl_rng *r;

	if (argc < 2) {
		printf ("Usage: ./polyfit [options] lc.dat\n\n");
		printf ("File lc.dat can have 1 column (equidistant fluxes), 2 columns (phase and flux),\n");
		printf ("or 3 columns (phase, flux, and standard deviation)\n\n");
		printf ("Options:\n\n");
		printf ("  -o order          ..  fitting polynomial order (default: 2)\n");
		printf ("  -i iters          ..  number of iterations (default: 10000)\n");
		printf ("  -s step           ..  step for random knot displacement (default: 0.01)\n");
		printf ("  -k k1 k2 ... kN   ..  explicit list of knots\n");
		printf ("  --find-knots      ..  attempt to find knots automatically\n");
		printf ("  --find-step       ..  attempt to find step automatically\n");
		printf ("  --chain-length    ..  minimum chain length for automatic knot search\n");
		printf ("  --ann-compatible  ..  make output ANN-compatible\n\n");
		exit (0);
	}

	options = polyfit_options_default ();
    options->find_knots = FALSE;
    
	for (i = 1; i < argc; i++) {
		if (strcmp (argv[i], "-o") == 0)
			options->polyorder = atoi (argv[++i]);
		if (strcmp (argv[i], "-i") == 0)
			options->iters = atoi (argv[++i]);
		if (strcmp (argv[i], "-s") == 0)
			options->step_size = atof (argv[++i]);
		if (strcmp (argv[i], "-k") == 0) {
			double knot;
			i++;
			options->knots = 0;
			while (sscanf (argv[i], "%lf", &knot) == 1) {
				options->knots++;
				knots = realloc (knots, options->knots * sizeof (*knots));
				knots[options->knots-1] = knot;
				i++;
			}
			i--;
		}
		if (strcmp (argv[i], "--find-knots") == 0)
			options->find_knots = TRUE;
		if (strcmp (argv[i], "--find-step") == 0)
			options->find_step = 1;
		if (strcmp (argv[i], "--chain-length") == 0)
			options->chain_length = atoi (argv[++i]);
		if (strcmp (argv[i], "--ann-compatible") == 0)
			options->ann_compat = 1;
	}

	in = fopen (argv[argc-1], "r");
	if (!in) {
		printf ("file %s not found, aborting.\n", argv[argc-1]);
		exit (0);
	}

	/* Read the input data: */

	data = malloc (NMAX * sizeof (*data));
	i = 0;
	while (!feof (in)) {
		if (!fgets (line, 255, in)) break;
		if (feof (in)) break;
		if (line[0] == '\n') break;
		if (1 <= (status = sscanf (line, "%lf\t%lf\t%lf\n", &col1, &col2, &col3))) {
			switch (status) {
				case 1:
					data[i].x = -0.5 + (double) i / (double) LCPOINTS;
					data[i].y = col1;
					data[i].z = 1.0;
				break;
				case 2:
					data[i].x = col1;
					data[i].y = col2;
					data[i].z = 1.0;
				break;
				case 3:
					data[i].x = col1;
					data[i].y = col2;
					data[i].z = 1e-3/col3/col3;
				break;
				default:

					/* can't ever get here */

				break;
			}
			i++;
		}
	}
	fclose (in);
	nobs = i;

	if (!options->ann_compat)
		printf ("# %d data points read in from %s.\n# \n", nobs, argv[argc-1]);

	/* Sort the data by phase: */

	qsort (data, nobs, sizeof (*data), polyfit_sort_by_phase);

	if (options->find_knots) {
		status = polyfit_find_knots (data, nobs, &knots, options);
		if (!options->ann_compat) {
			if (status != 0)
				printf ("# * automatic search for knots failed, reverting to defaults.\n");
			else
				printf ("# * automatic search for knots successful.\n");
			printf ("# \n");
		}
	}

	/* The initial phase intervals for knots: */

	if (!knots) {
		knots = malloc (options->knots * sizeof (*knots));
        knots[0] = -0.4; knots[1] = -0.1; knots[2] = 0.2; knots[3] = 0.4; 
        /* knots[4] = 0.45; 
        knots[5] = 0.48; */
	}

	/* Sort the knots in ascending order: */
	qsort (knots, options->knots, sizeof (*knots), polyfit_sort_by_value);

	if (options->find_step) {
		double diff;
		/* Step size would be the minimum width between two knots / 5: */
		diff = fabs (knots[1]-knots[0]);
		for (i = 1; i < options->knots-1; i++)
			if (fabs (knots[i+1]-knots[i]) < diff)
				diff = fabs (knots[i+1]-knots[i]);
		if (fabs (knots[i+1]-knots[0]) < diff)
			diff = fabs (knots[i+1]-knots[0]);

		options->step_size = diff / 5.0;
	}

	if (!options->ann_compat) {
		printf ("# Fitting polynomial order: %d\n", options->polyorder);
		printf ("# Initial set of knots: {");
		for (i = 0; i < options->knots-1; i++)
			printf ("%lf, ", knots[i]);
		printf ("%lf}\n", knots[i]);
		printf ("# Number of iterations for knot search: %d\n", options->iters);
		printf ("# Step size for knot search: %lf\n# \n", options->step_size);
	}
	
	r = gsl_rng_alloc (gsl_rng_mt19937);
	gsl_rng_set (r, 1);
	
    result = polyfit_solution_init (options);
	polyfit (result, data, nobs, knots, 0, options);
    chi2 = result->chi2;
	
	if (!options->ann_compat)
		printf ("# Original chi2: %lf\n", chi2);

	test = malloc (options->knots * sizeof (*test));

	for (iter = 0; iter < options->iters; iter++) {
		for (i = 0; i < options->knots; i++) {
			u = gsl_rng_uniform (r);
			test[i] = knots[i] + options->step_size * 2 * u - options->step_size;
			if (test[i] < -0.5) test[i] += 1.0;
			if (test[i] >  0.5) test[i] -= 1.0;
		}

		polyfit (result, data, nobs, test, 0, options);
        
		if (result->chi2 < chi2) {
			chi2 = result->chi2;
			for (i = 0; i < options->knots; i++)
				knots[i] = test[i];
		}
	}

	if (!options->ann_compat)
		printf ("# Final chi2:    %lf\n# \n", chi2);
	
	polyfit (result, data, nobs, knots, 0, options);

    polyfit_print (result, options, 1, 1);
    
    gsl_rng_free (r);
	free (data);
	free (test);
	free (knots);
	
	polyfit_options_free (options);

	return 0;
}

float altmain (int argc, char **argv)
{
	int i, nobs, iter, status;
	polyfit_triplet *data;
	FILE *in;
	double col1, col2, col3, chi2, chi2test, u;
	char line[255];

	double *knots = NULL;
	double *test;

	polyfit_options *options;
    polyfit_solution *result;
    
    
	gsl_rng *r;

	if (argc < 2) {
		printf ("Usage: ./polyfit [options] lc.dat\n\n");
		printf ("File lc.dat can have 1 column (equidistant fluxes), 2 columns (phase and flux),\n");
		printf ("or 3 columns (phase, flux, and standard deviation)\n\n");
		printf ("Options:\n\n");
		printf ("  -o order          ..  fitting polynomial order (default: 2)\n");
		printf ("  -i iters          ..  number of iterations (default: 10000)\n");
		printf ("  -s step           ..  step for random knot displacement (default: 0.01)\n");
		printf ("  -k k1 k2 ... kN   ..  explicit list of knots\n");
		printf ("  --find-knots      ..  attempt to find knots automatically\n");
		printf ("  --find-step       ..  attempt to find step automatically\n");
		printf ("  --chain-length    ..  minimum chain length for automatic knot search\n");
		printf ("  --ann-compatible  ..  make output ANN-compatible\n\n");
		exit (0);
	}

	options = polyfit_options_default ();
    options->find_knots = FALSE;
    
	for (i = 1; i < argc; i++) {
		if (strcmp (argv[i], "-o") == 0)
			options->polyorder = atoi (argv[++i]);
		if (strcmp (argv[i], "-i") == 0)
			options->iters = atoi (argv[++i]);
		if (strcmp (argv[i], "-s") == 0)
			options->step_size = atof (argv[++i]);
		if (strcmp (argv[i], "-k") == 0) {
			double knot;
			i++;
			options->knots = 0;
			while (sscanf (argv[i], "%lf", &knot) == 1) {
				options->knots++;
				knots = realloc (knots, options->knots * sizeof (*knots));
				knots[options->knots-1] = knot;
				i++;
			}
			i--;
		}
		if (strcmp (argv[i], "--find-knots") == 0)
			options->find_knots = TRUE;
		if (strcmp (argv[i], "--find-step") == 0)
			options->find_step = 1;
		if (strcmp (argv[i], "--chain-length") == 0)
			options->chain_length = atoi (argv[++i]);
		if (strcmp (argv[i], "--ann-compatible") == 0)
			options->ann_compat = 1;
	}

	in = fopen (argv[argc-1], "r");
	if (!in) {
		printf ("file %s not found, aborting.\n", argv[argc-1]);
		exit (0);
	}

	/* Read the input data: */

	data = malloc (NMAX * sizeof (*data));
	i = 0;
	while (!feof (in)) {
		if (!fgets (line, 255, in)) break;
		if (feof (in)) break;
		if (line[0] == '\n') break;
		if (1 <= (status = sscanf (line, "%lf\t%lf\t%lf\n", &col1, &col2, &col3))) {
			switch (status) {
				case 1:
					data[i].x = -0.5 + (double) i / (double) LCPOINTS;
					data[i].y = col1;
					data[i].z = 1.0;
				break;
				case 2:
					data[i].x = col1;
					data[i].y = col2;
					data[i].z = 1.0;
				break;
				case 3:
					data[i].x = col1;
					data[i].y = col2;
					data[i].z = 1e-3/col3/col3;
				break;
				default:

					/* can't ever get here */

				break;
			}
			i++;
		}
	}
	fclose (in);
	nobs = i;

	if (!options->ann_compat)
		printf ("# %d data points read in from %s.\n# \n", nobs, argv[argc-1]);

	/* Sort the data by phase: */

	qsort (data, nobs, sizeof (*data), polyfit_sort_by_phase);

	if (options->find_knots) {
		status = polyfit_find_knots (data, nobs, &knots, options);
		if (!options->ann_compat) {
			if (status != 0)
				printf ("# * automatic search for knots failed, reverting to defaults.\n");
			else
				printf ("# * automatic search for knots successful.\n");
			printf ("# \n");
		}
	}

	/* The initial phase intervals for knots: */

	if (!knots) {
		knots = malloc (options->knots * sizeof (*knots));
        knots[0] = -0.4; knots[1] = -0.1; knots[2] = 0.2; knots[3] = 0.4; 
        /* knots[4] = 0.45; 
        knots[5] = 0.48; */
	}

	/* Sort the knots in ascending order: */
	qsort (knots, options->knots, sizeof (*knots), polyfit_sort_by_value);

	if (options->find_step) {
		double diff;
		/* Step size would be the minimum width between two knots / 5: */
		diff = fabs (knots[1]-knots[0]);
		for (i = 1; i < options->knots-1; i++)
			if (fabs (knots[i+1]-knots[i]) < diff)
				diff = fabs (knots[i+1]-knots[i]);
		if (fabs (knots[i+1]-knots[0]) < diff)
			diff = fabs (knots[i+1]-knots[0]);

		options->step_size = diff / 5.0;
	}

	if (!options->ann_compat) {
		printf ("# Fitting polynomial order: %d\n", options->polyorder);
		printf ("# Initial set of knots: {");
		for (i = 0; i < options->knots-1; i++)
			printf ("%lf, ", knots[i]);
		printf ("%lf}\n", knots[i]);
		printf ("# Number of iterations for knot search: %d\n", options->iters);
		printf ("# Step size for knot search: %lf\n# \n", options->step_size);
	}
	
	r = gsl_rng_alloc (gsl_rng_mt19937);
	gsl_rng_set (r, 1);
	
    result = polyfit_solution_init (options);
	polyfit (result, data, nobs, knots, 0, options);
    chi2 = result->chi2;
	
	if (!options->ann_compat)
		printf ("# Original chi2: %lf\n", chi2);

	test = malloc (options->knots * sizeof (*test));

	for (iter = 0; iter < options->iters; iter++) {
		for (i = 0; i < options->knots; i++) {
			u = gsl_rng_uniform (r);
			test[i] = knots[i] + options->step_size * 2 * u - options->step_size;
			if (test[i] < -0.5) test[i] += 1.0;
			if (test[i] >  0.5) test[i] -= 1.0;
		}

		polyfit (result, data, nobs, test, 0, options);
        
		if (result->chi2 < chi2) {
			chi2 = result->chi2;
			for (i = 0; i < options->knots; i++)
				knots[i] = test[i];
		}
	}

	if (!options->ann_compat)
		printf ("# Final chi2:    %lf\n# \n", chi2);
	
	polyfit (result, data, nobs, knots, 0, options);

    polyfit_print (result, options, 1, 1);
    
    gsl_rng_free (r);
	free (data);
	free (test);
	free (knots);
	
	polyfit_options_free (options);

	return (float) chi2;
}

