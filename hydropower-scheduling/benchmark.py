"""Out-of-sample decision-regret benchmark. Synthetic reservoir LPs only."""
import csv
from pathlib import Path
import numpy as np
from scipy.optimize import linprog

CAPACITY, RELEASE_LIMIT, TERMINAL = 100., 28., 30.
HORIZON = 7
SCENARIO_FACTORS = np.array([.55,1.,1.55])
PROBABILITIES = np.array([.25,.5,.25])

def optimize(prices, inflows, initial, day1=None):
    prices,inflows=np.asarray(prices,float),np.asarray(inflows,float)
    T=len(prices)
    c=np.r_[-prices,np.zeros(T),np.r_[np.zeros(T-1),-TERMINAL]]
    A=np.zeros((T,3*T));b=inflows.copy();b[0]+=initial
    for t in range(T):
        A[t,t]=A[t,T+t]=A[t,2*T+t]=1.
        if t:A[t,2*T+t-1]=-1.
    bounds=[(0,RELEASE_LIMIT)]*T+[(0,None)]*T+[(0,CAPACITY)]*T
    if day1 is not None:
        bounds[0]=(day1[0],day1[0]);bounds[T]=(day1[1],day1[1])
    r=linprog(c,A_eq=A,b_eq=b,bounds=bounds,method="highs")
    if not r.success:raise RuntimeError(r.message)
    assert np.max(np.abs(A@r.x-b))<1e-6
    return {"value":float(-r.fun),"release":r.x[:T],"spill":r.x[T:2*T],"storage":r.x[2*T:]}

def stochastic(prices,mean_inflows,initial,risk_weight=0.,alpha=.8):
    prices=np.asarray(prices,float);mean_inflows=np.asarray(mean_inflows,float)
    T=len(prices);K=len(SCENARIO_FACTORS);n=3*T*K+1+K;eta=3*T*K
    c=np.zeros(n);c[eta]=risk_weight
    eq=[];rhs=[];ub_rows=[];ub_vals=[];bounds=[]
    for k,(factor,prob) in enumerate(zip(SCENARIO_FACTORS,PROBABILITIES)):
        o=3*T*k;c[o:o+T]=-prob*prices;c[o+3*T-1]=-prob*TERMINAL
        c[eta+1+k]=risk_weight*prob/(1-alpha)
        bounds.extend([(0,RELEASE_LIMIT)]*T+[(0,None)]*T+[(0,CAPACITY)]*T)
        inflows=mean_inflows.copy();inflows[1:]*=factor
        for t in range(T):
            row=np.zeros(n);row[o+t]=row[o+T+t]=row[o+2*T+t]=1.
            if t:row[o+2*T+t-1]=-1.
            eq.append(row);rhs.append(inflows[t]+(initial if t==0 else 0))
        row=np.zeros(n);row[o:o+T]=-prices;row[o+3*T-1]=-TERMINAL
        row[eta]=-1.;row[eta+1+k]=-1.
        ub_rows.append(row);ub_vals.append(0.)
    for k in range(1,K):
        for j in (0,T,2*T):
            row=np.zeros(n);row[j]=1.;row[3*T*k+j]=-1.
            eq.append(row);rhs.append(0.)
    bounds.extend([(None,None)]+[(0,None)]*K)
    r=linprog(c,A_eq=eq,b_eq=rhs,A_ub=ub_rows,b_ub=ub_vals,bounds=bounds,method="highs")
    if not r.success:raise RuntimeError(r.message)
    assert np.max(np.abs(np.asarray(eq)@r.x-np.asarray(rhs)))<1e-6
    return (float(r.x[0]),float(r.x[T]))

def experiment(seed=20261017,contexts=35,outcomes_per_context=5):
    rng=np.random.default_rng(seed);rows=[]
    for context in range(contexts):
        prices=np.clip(rng.normal(62,19,HORIZON),15,140)
        expected=np.clip(rng.normal(13,4,HORIZON),3,25)
        initial=float(rng.uniform(28,92))
        baseline=optimize(prices,expected,initial)
        actions={
            "expected_inflow":(float(baseline["release"][0]),float(baseline["spill"][0])),
            "scenario_lp":stochastic(prices,expected,initial,0.),
            "cvar_lp":stochastic(prices,expected,initial,.6)}
        for outcome in range(outcomes_per_context):
            factor=float(rng.choice([.45,.7,1.,1.3,1.75],p=[.12,.23,.3,.23,.12]))
            actual=expected.copy();actual[1:]*=factor
            oracle=optimize(prices,actual,initial)["value"]
            for policy,day1 in actions.items():
                value=optimize(prices,actual,initial,day1)["value"]
                assert value<=oracle+1e-5
                rows.append({"context":context,"outcome":outcome,"policy":policy,
                    "oracle":oracle,"realized_value":value,"regret":max(0.,oracle-value),
                    "first_release":day1[0],"first_spill":day1[1]})
    return rows

def summarize(rows):
    summary={}
    for name in ("expected_inflow","scenario_lp","cvar_lp"):
        vals=np.array([r["regret"] for r in rows if r["policy"]==name])
        summary[name]={"n":len(vals),"mean_regret":round(float(vals.mean()),3),
            "p90_regret":round(float(np.quantile(vals,.9)),3),
            "max_regret":round(float(vals.max()),3),
            "zero_regret_pct":round(float(np.mean(vals<1e-6)*100),1)}
    return summary

if __name__=="__main__":
    rows=experiment()
    output=Path(__file__).resolve().parent/"benchmark_results.csv"
    with output.open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    for name,statistics in summarize(rows).items():print(name,statistics)
    print("Saved",output)
