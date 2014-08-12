#include <phoebe/phoebe.h>

typedef struct polyfit_options {
	int    polyorder;
	int    iters;
	double step_size;
	int    knots;
	bool   find_knots;
	bool   find_step;
	int    chain_length;
	bool   ann_compat;
} polyfit_options;

typedef struct polyfit_triplet {
	double x;
	double y;
	double z;
} polyfit_triplet;

typedef struct polyfit_solution {
	double chi2;
	int    *npts;   /* Number of data points on each interval */
	double *knots;  /* Array of knots */
	double **ck;	/* Polynomial coefficients */
} polyfit_solution;

polyfit_options  *polyfit_options_default ();
int               polyfit_options_free    (polyfit_options *options);
polyfit_solution *polyfit_solution_init   (polyfit_options *options);
int               polyfit_solution_free   (polyfit_solution *solution, polyfit_options *options);
int               polyfit_sort_by_phase   (const void *a, const void *b);
int               polyfit_sort_by_value   (const void *a, const void *b);
int               polyfit_find_knots      (polyfit_triplet *data, int nobs, double **knots, polyfit_options *options);
double            polyfit_compute         (polyfit_solution *result, polyfit_options *options, double phase);
int               polyfit_print           (polyfit_solution *result, polyfit_options *options, int VERBOSE, int PRINT_SOLUTION);
int               polyfit                 (polyfit_solution *result, polyfit_triplet *data, int nobs, double *knots, int PRINT, polyfit_options *options);
