#!/usr/bin/env python

import numpy
from numpy import zeros, dot
import scipy.linalg as linalg

Ab = numpy.zeros( (2,4) )
Ab[0,:] = 1.
Ab[1,:] = 4.

Ab2 = numpy.zeros( (3,4) )
Ab2[0,:] = 1.
Ab2[1,:] = 4.
Ab2[2,:] = 1.

# a nice positive definite matrix
A = numpy.array((
	(4, 1, 0, 0),
	(1, 4, 1, 0),
	(0, 1, 4, 1),
	(0, 0, 1, 4),
), float )

# a random set of right-hand sides
B = numpy.array((
	(1,  2, 3, 4),
	(5,  6, 7, 8),
	(9, 10, 1, 2),
	(3,  4, 5, 6)
), float )

b12 = B[:,0:2]
b1  = B[:,0]
b1v = b1.reshape( (4,1) )  # make into a column vector

print '----- test data'
print 'A=    # 4x4 dense matrix\n', A, '\n'
print 'Ab=   # upper triangular banded matrix\n', Ab, '\n'
print 'Ab2=  # general banded matrix\n', Ab2, '\n'
print 'B=    # 4x4 matrix\n', B, '\n'
print 'b12=  # 4x2 matrix\n', b12, '\n'
print 'b1=   # 4   vector\n', b1, '\n'
print 'b1v=  # 4x1 column vector\n', b1v, '\n'

print '----- test a dense solve -- works'
x = linalg.solve( A, B )
print 'x = solve( A, B )\n', x, '\n'
print 'Ax=\n', dot( A, x ), '\n'
print 'B=\n', B, '\n'

print '----- test a general banded solve, with n rhs -- works'
x = linalg.solve_banded( (1,1), Ab2, B )
print 'x = solve_banded( (1,1), Ab2, B )\n', x, '\n'
print 'Ax=\n', dot( A, x ), '\n'
print 'B=\n', B, '\n'

print '----- test a general banded solve, with 2 rhs -- works'
x = linalg.solve_banded( (1,1), Ab2, b12 )
print 'x = solve_banded( (1,1), Ab2, b12 )\n', x, '\n'
print 'Ax=\n', dot( A, x ), '\n'
print 'b12=\n', b12, '\n'

print '----- test a general banded solve, with 1 rhs (4 vector) -- works'
x = linalg.solve_banded( (1,1), Ab2, b1 )
print 'x = solve_banded( (1,1), Ab2, b1 )\n', x, '\n'
print 'Ax=\n', dot( A, x ), '\n'
print 'b1=\n', b1, '\n'

print '----- test a general banded solve, with 1 rhs (4x1 column vector) -- works'
x = linalg.solve_banded( (1,1), Ab2, b1v )
print 'x = solve_banded( (1,1), Ab2, b1v )\n', x, '\n'
print 'Ax=\n', dot( A, x ), '\n'
print 'b1v=\n', b1v, '\n'

print '----- test a banded cholesky solve, with n rhs -- works'
(cho,x) = linalg.solveh_banded( Ab, B, overwrite_b=1 )
print '(cho,x) = solveh_banded( Ab, B, overwrite_b=1 )\n', x, '\n'
print 'Ax=\n', dot( A, x ), '\n'
print 'B=\n', B, '\n'
print 'Ab=\n', Ab, '\n'

print '----- test a general banded solve, with 1 rhs but transposed -- THIS SEG FAULTS'
print 'this should NOT run since b1.T is shaped wrong.'
print 'presumably it should raise an error though, not seg fault.'
print 'x = solve_banded( (1,1), Ab2, b1v.T )'
#x = linalg.solve_banded( (1,1), Ab2, b1v.T )
#print x, '\n'
#print 'Ax=\n', dot( A, x ), '\n'
#print 'b1v=\n', b1v, '\n'
print

print '----- test a banded cholesky solve, with 1 rhs but transposed -- SHOULD NOT WORK'
print 'this runs, but shouldn\'t since b1.T is shaped wrong.'
print 'The answer is correct, though shaped wrong.'
(cho,x) = linalg.solveh_banded( Ab, b1v.T )
print '(cho,x) = solveh_banded( Ab, b1v.T )\n', x, '\n'
x.shape = (4,1)
print 'x = x.reshape( (4,1) )'
print 'x=\n', x, '\n'
print dot( A, x ), '\n'

print '----- test a banded cholesky solve, with 2 rhs but transposed -- SHOULD NOT WORK'
print 'this runs, but shouldn\'t since b12.T is shaped wrong.'
print 'it does NOT solve Ab x = b12.'
(cho,x) = linalg.solveh_banded( Ab, b12.T )
print '(cho,x) = solveh_banded( Ab, b12.T )\n', x, '\n'

print 'if we reshape it, taking data column-wise, we see it solved the system below'
x = x.T.reshape( (2,4) ).T  # reshape it, taking data column wise!
print 'x = x.T.reshape( (2,4) ).T'
print 'x=\n', x, '\n'
print 'Ax=\n', dot( A, x ), '\n'

print '----- it solved this system:'
print 'reshape the 1st two columns of B, pretending the data was column wise:'
print 'Bhat = B[:,0:2].reshape( (2,4) ).T'
Bhat = B[:,0:2].reshape( (2,4) ).T

x = linalg.solve( A, Bhat )
print 'x = solve(A,Bhat)\n', x, '\n'
print 'Ax=\n', dot( A, x ), '\n'
print 'Bhat=\n', Bhat, '\n'
print 'original B[:,0:2]=\n', B[:,0:2], '\n'

print '----- test banded cholesky solve, with 2 rhs -- THIS CRASHES'
print '(cho,x) = linalg.solveh_banded( Ab, b12 )'
#(cho,x) = linalg.solveh_banded( Ab, b12 )
#print x, '\n'
#print dot( A, x ), '\n'
print

print '----- test banded cholesky solve, with 1 rhs (4 vector) -- THIS CRASHES'
print '(cho,x) = linalg.solveh_banded( Ab, b1 )'
#(cho,x) = linalg.solveh_banded( Ab, b1 )
#print x, '\n'
#print dot( A, x ), '\n'
print

print '----- test banded cholesky solve, with 1 rhs (4x1 column vector) -- THIS CRASHES'
print '(cho,x) = linalg.solveh_banded( Ab, b1v )'
#(cho,x) = linalg.solveh_banded( Ab, b1v )
#print x, '\n'
#print dot( A, x ), '\n'
print
