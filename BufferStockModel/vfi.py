import numpy as np
from numba import njit, prange

 # consav
from consav import linear_interp # for linear interpolation
from consav import golden_section_search # for optimization in 1D

import utility

# a. define objective function
@njit
def obj_bellman(c,p,m,v_plus,par):
    """ evaluate bellman equation """

    # a. end-of-period assets
    a = m-c
    
    # b. continuation value
    w = 0
    for ishock in range(par.Nshocks):
            
        # i. shocks
        psi = par.psi[ishock]
        psi_w = par.psi_w[ishock]
        xi = par.xi[ishock]
        xi_w = par.xi_w[ishock]

        # ii. next-period states
        p_plus = p*psi
        y_plus = p_plus*xi
        m_plus = par.R*a + y_plus
        
        # iii. weight
        weight = psi_w*xi_w
        
        # iv. interpolate
        w += weight*par.beta*linear_interp.interp_2d(par.grid_p,par.grid_m,v_plus,p_plus,m_plus)
    
    # c. total value
    value_of_choice = utility.func(c,par) + w

    return -value_of_choice # we are minimizing

# b. create optimizer
opt_bellman = golden_section_search.create_optimizer(obj_bellman)

# c. solve bellman equation        
@njit(parallel=True)
def solve_bellman(t,sol,par):
    """solve bellman equation using vfi"""

    # unpack
    c = sol.c[t]
    v = sol.v[t]

    # loop over outer states
    for ip in prange(par.Np):

        # a. permanent income
        p = par.grid_p[ip]

        # d. loop over cash-on-hand
        for im in range(par.Nm):
            
            # a. cash-on-hand
            m = par.grid_m[im]

            # b. optimal choice
            c_low = np.fmin(m/2,1e-8)
            c_high = m
            c[ip,im] = opt_bellman(c_low,c_high,par.tol,p,m,sol.v[t+1],par)

            # c. optimal value
            v[ip,im] = -obj_bellman(c[ip,im],p,m,sol.v[t+1],par)

