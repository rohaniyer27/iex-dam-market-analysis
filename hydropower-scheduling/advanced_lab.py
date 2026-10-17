"""Synthetic HydroOpt extensions; not production hydropower modelling."""
import numpy as np
from scipy.optimize import linprog, minimize
from stochastic_reservoir import solve_stochastic, PRICES, INFLOW, INITIAL, CAPACITY, MAX_RELEASE, TERMINAL_VALUE
from reservoir_lab import solve

def rolling(horizon=3, forecast_bias=0.30):
    """Implement each first-day LP decision using actual inflows."""
    initial=INITIAL; q=[]; s=[]
    for t in range(len(PRICES)):
        end=min(len(PRICES),t+horizon)
        f=INFLOW[t:end].copy()
        f[1:]*=1+forecast_bias
        # Adapt existing single-reservoir LP to changing initial storage.
        p=PRICES[t:end]; T=len(p)
        c=np.r_[-p,np.zeros(T),np.r_[np.zeros(T-1),-TERMINAL_VALUE]]
        A=np.zeros((T,3*T)); b=f.copy();b[0]+=initial
        for j in range(T):
            A[j,j]=A[j,T+j]=A[j,2*T+j]=1
            if j:A[j,2*T+j-1]=-1
        sol=linprog(c,A_eq=A,b_eq=b,bounds=[(0,MAX_RELEASE)]*T+[(0,None)]*T+[(0,CAPACITY)]*T,method="highs")
        if not sol.success:raise RuntimeError(sol.message)
        discharge,spill=sol.x[0],sol.x[T]
        initial+=INFLOW[t]-discharge-spill
        assert -1e-6<=initial<=CAPACITY+1e-6
        q.append(discharge);s.append(initial)
    return {"release":np.array(q),"storage":np.array(s),
            "value":float(PRICES@q+TERMINAL_VALUE*initial)}

def head_dependent():
    """Synthetic nonlinear head effect; SLSQP LOCAL optimum only."""
    T=len(PRICES)
    def states(x):return INITIAL+np.cumsum(INFLOW-x[:T]-x[T:])
    def objective(x):
        st=states(x);begin=np.r_[INITIAL,st[:-1]]
        return -float(PRICES@(x[:T]*(0.65+0.0035*begin))+TERMINAL_VALUE*st[-1])
    x0=np.r_[np.minimum(INFLOW,MAX_RELEASE),np.zeros(T)]
    result=minimize(objective,x0,method="SLSQP",
      bounds=[(0,MAX_RELEASE)]*T+[(0,None)]*T,
      constraints=[{"type":"ineq","fun":states},{"type":"ineq","fun":lambda x:CAPACITY-states(x)}],
      options={"maxiter":2000,"ftol":1e-9})
    if not result.success:raise RuntimeError(result.message)
    assert min(states(result.x))>=-1e-5 and max(states(result.x))<=CAPACITY+1e-5
    return {"value":-result.fun,"storage":states(result.x),"release":result.x[:T]}

def learned_terminal_value():
    """Concavity projection on context-averaged LP value samples; no certified SDDP cuts."""
    grid=np.arange(0,101,10,dtype=float)
    contexts=[(PRICES[3:6],INFLOW[3:6]),(PRICES[1:4],INFLOW[1:4]),(PRICES[4:7],INFLOW[4:7])]
    curves=[]
    for p,f in contexts:
        # Translate varying initial storage through each LP equality RHS.
        vals=[]
        for initial in grid:
            T=len(p); c=np.r_[-p,np.zeros(T),np.r_[np.zeros(T-1),-TERMINAL_VALUE]]
            A=np.zeros((T,3*T));b=f.copy();b[0]+=initial
            for j in range(T):
                A[j,j]=A[j,T+j]=A[j,2*T+j]=1
                if j:A[j,2*T+j-1]=-1
            r=linprog(c,A_eq=A,b_eq=b,bounds=[(0,MAX_RELEASE)]*T+[(0,None)]*T+[(0,CAPACITY)]*T,method="highs")
            if not r.success:raise RuntimeError(r.message)
            vals.append(-r.fun)
        curves.append(np.array(vals))
    train=(curves[0]+curves[1])/2
    blocks=[]
    for v in np.diff(train)/10:
        blocks.append([float(v),1])
        while len(blocks)>1 and blocks[-2][0]<blocks[-1][0]-1e-10:
            a,n=blocks.pop();b,m=blocks.pop();blocks.append([(a*n+b*m)/(n+m),n+m])
    slope=np.concatenate([np.repeat(v,n) for v,n in blocks])
    fit=np.r_[train[0],train[0]+np.cumsum(10*slope)]
    assert np.all(np.diff(slope)<=1e-8)
    return {"storage":grid,"value":fit,"held_out_mae":float(np.mean(abs(fit-curves[2])))}

if __name__=="__main__":
    a=rolling();b=head_dependent();c=learned_terminal_value()
    print("Rolling objective:",round(a["value"],2))
    print("Head-dependent local objective:",round(b["value"],2))
    print("Concave learned-value held-out context MAE:",round(c["held_out_mae"],2))
    print("Two-stage expected objective:",round(solve_stochastic()["expected_objective"],2))
    print("Feasibility and concavity checks passed")
