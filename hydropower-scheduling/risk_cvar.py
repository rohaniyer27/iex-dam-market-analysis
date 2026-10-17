"""Risk-aware two-stage stochastic reservoir LP using CVaR of negative total value.
All scenarios synthetic. CVaR penalty can be zero or positive; no performance guarantees.
"""
import numpy as np
from scipy.optimize import linprog
from stochastic_reservoir import PRICES, INFLOW, INITIAL, CAPACITY, MAX_RELEASE, TERMINAL_VALUE

def solve(risk_weight=0.35, alpha=.9):
    assert 0<=risk_weight<=1 and 0<alpha<1
    factors=[.65,1,1.4]; probs=[.25,.5,.25]; T=len(PRICES)
    n=9*T+4; eta=9*T; c=np.zeros(n); c[eta]=risk_weight
    eq=[];rhs=[];ineq=[];ub=[]
    bounds=[]
    for k,(factor,p) in enumerate(zip(factors,probs)):
        o=k*3*T;c[o:o+T]=-p*PRICES;c[o+3*T-1]=-p*TERMINAL_VALUE
        c[eta+1+k]=risk_weight*p/(1-alpha)
        bounds += [(0,MAX_RELEASE)]*T+[(0,None)]*T+[(0,CAPACITY)]*T
        for t in range(T):
            r=np.zeros(n);r[o+t]=r[o+T+t]=r[o+2*T+t]=1.
            if t:r[o+2*T+t-1]=-1.
            eq.append(r);rhs.append(INFLOW[t]*(1 if t==0 else factor)+(INITIAL if t==0 else 0))
        r=np.zeros(n);r[o:o+T]=-PRICES;r[o+3*T-1]=-TERMINAL_VALUE
        r[eta]=-1.;r[eta+1+k]=-1.
        ineq.append(r);ub.append(0.)
    for k in [1,2]:
        for j in [0,T,2*T]:
            r=np.zeros(n);r[j]=1.;r[k*3*T+j]=-1.;eq.append(r);rhs.append(0.)
    bounds += [(None,None)]+[(0,None)]*3
    res=linprog(c,A_eq=eq,b_eq=rhs,A_ub=ineq,b_ub=ub,bounds=bounds,method="highs")
    if not res.success:raise RuntimeError(res.message)
    assert np.allclose(np.asarray(eq)@res.x,np.asarray(rhs),atol=1e-7)
    vals=[]
    for k in range(3):
        o=k*3*T
        vals.append(float(PRICES@res.x[o:o+T]+TERMINAL_VALUE*res.x[o+3*T-1]))
    return {"expected_value":float(np.dot(probs,vals)),"risk_adjusted_objective":-float(res.fun),
            "scenario_values":vals,"day_one_release":float(res.x[0])}

if __name__=="__main__":
    for weight in (0.,.35):
        print("CVaR weight",weight,solve(weight))
