import numpy as np, csv
from scipy.stats import norm
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

S0=K=4650.0; r=0.0434; sig=0.1784; T=10.0; n=100; N=2520; dt=T/N
fee=0.03; notional=10_000_000
zcb=100*np.exp(-r*T); budget=100*(1-fee)-zcb
def bs(S,tau):
    tau=np.maximum(tau,1e-12)
    d1=(np.log(S/K)+(r+.5*sig**2)*tau)/(sig*np.sqrt(tau))
    return S*norm.cdf(d1)-K*np.exp(-r*tau)*norm.cdf(d1-sig*np.sqrt(tau))
part=budget/(bs(S0,T)/S0*100)

np.random.seed(42)
Z=np.random.standard_normal((n,N))
S=np.hstack([np.full((n,1),S0), S0*np.exp(np.cumsum((r-.5*sig**2)*dt+sig*np.sqrt(dt)*Z,axis=1))])
t=np.linspace(0,T,N+1)
# market value of the embedded option per $100 note along each path
V=part*(100/S0)*bs(S,(T-t)[None,:]); V[:,-1]=part*(100/S0)*np.maximum(S[:,-1]-K,0)
ST=S[:,-1]; itm=ST>K
pay=notional*(1+part*np.maximum(ST/S0-1,0))

print(f"participation {part:.4%}  option value t=0 per $100: {V[0,0]:.2f} (budget {budget:.2f})")
print(f"ITM {itm.sum()}  OTM {(~itm).sum()}")
print(f"S_T mean {ST.mean():,.0f} median {np.median(ST):,.0f} max {ST.max():,.0f} min {ST.min():,.0f}")
print(f"option value at T per $100: mean {V[:,-1].mean():.2f} max {V[:,-1].max():.2f}")
print(f"payout min {pay.min():,.0f} mean {pay.mean():,.0f} median {np.median(pay):,.0f} max {pay.max():,.0f}")
print(f"discounted mean option payoff per $100: {np.exp(-r*T)*V[:,-1].mean():.2f}")

with open("gold_ppn_mc_paths_summary.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["path","S_T_usd_per_oz","gold_return","option_value_at_T_per_100","payout_usd_10M","in_the_money"])
    for i in range(n): w.writerow([i+1,round(ST[i],2),round(ST[i]/S0-1,4),round(V[i,-1],2),round(pay[i],0),bool(itm[i])])
yrs=np.arange(0,N+1,21)
with open("gold_ppn_mc_option_value_paths.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["year"]+[f"path_{i+1}" for i in range(n)])
    for j in yrs: w.writerow([round(t[j],4)]+[round(v,3) for v in V[:,j]])

B,O,INK,MUT="#2a78d6","#eb6834","#1a1a1a","#666666"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False,
  "axes.edgecolor":"#bbbbbb","axes.grid":True,"grid.color":"#e6e6e6","grid.linewidth":0.6,"axes.axisbelow":True,
  "axes.titleweight":"bold","axes.titlesize":11,"axes.titlelocation":"left","xtick.color":MUT,"ytick.color":MUT,"axes.labelcolor":MUT})
fig=plt.figure(figsize=(13,13)); gs=fig.add_gridspec(3,2,height_ratios=[1,1,0.8],hspace=0.38,wspace=0.2)
usd=FuncFormatter(lambda x,_:f"${x:,.0f}")
def paths(ax,Y,title,ylab,fmt,ref,reflab):
    for i in range(n): ax.plot(t[::5],Y[i,::5],color=B if itm[i] else O,lw=0.6,alpha=0.35)
    ax.plot(t[::5],Y.mean(axis=0)[::5],color=INK,lw=2,label="Mean of 100 paths")
    ax.axhline(ref,color=MUT,lw=1,ls=":"); ax.text(10.05,ref,reflab,color=MUT,fontsize=8.5,va="center")
    ax.plot([],[],color=B,lw=2,label=f"Ends above strike (n={itm.sum()})"); ax.plot([],[],color=O,lw=2,label=f"Ends at or below strike (n={(~itm).sum()})")
    ax.set_title(title); ax.set_ylabel(ylab); ax.set_xlabel("Years since issue"); ax.set_xlim(0,10); ax.yaxis.set_major_formatter(fmt)
    ax.legend(frameon=False,loc="upper left",fontsize=9)
paths(fig.add_subplot(gs[0,:]),S,"Simulated gold price, 100 GBM paths","USD per oz",usd,K,"Strike\n$4,650")
paths(fig.add_subplot(gs[1,:]),V,"Market value of the embedded option along each path, per $100 note","USD per $100 note",
      FuncFormatter(lambda x,_:f"${x:,.0f}"),budget,f"Cost at issue\n${budget:.2f}")
ax=fig.add_subplot(gs[2,0]); bins=np.linspace(0,18000,25)
ax.hist([ST[~itm],ST[itm]],bins=bins,stacked=True,color=[O,B],edgecolor="white",linewidth=1,label=["At or below strike","Above strike"])
ax.axvline(ST.mean(),color=INK,lw=1.5,ls="--"); ax.text(ST.mean()+250,ax.get_ylim()[1]*0.93,f"Mean ${ST.mean():,.0f}",color=INK,fontsize=9)
ax.set_title("Gold price at maturity"); ax.set_xticks(range(0,18001,5000)); ax.set_xlabel("USD per oz"); ax.set_ylabel("Paths"); ax.xaxis.set_major_formatter(usd); ax.legend(frameon=False,fontsize=9,loc="upper right",bbox_to_anchor=(1,0.85))
ax=fig.add_subplot(gs[2,1]); pm=pay/1e6; bins=np.linspace(10,32,23)
ax.hist([pm[~itm],pm[itm]],bins=bins,stacked=True,color=[O,B],edgecolor="white",linewidth=1)
ax.axvline(pm.mean(),color=INK,lw=1.5,ls="--"); ax.text(pm.mean()+0.4,ax.get_ylim()[1]*0.93,f"Mean ${pm.mean():.2f}M",color=INK,fontsize=9)
ax.set_title(f"Investor payout at maturity on $10M, {part:.1%} participation"); ax.set_xlabel("USD millions"); ax.set_ylabel("Paths")
ax.xaxis.set_major_formatter(FuncFormatter(lambda x,_:f"${x:.0f}M"))
fig.suptitle("Gold PPN Monte Carlo simulation",x=0.125,y=0.955,ha="left",fontsize=15,fontweight="bold",color=INK)
fig.text(0.125,0.925,f"S0 = K = $4,650, r = 4.34%, sigma = 17.84%, T = 10 years, daily steps (1/252), NumPy seed 42",color=MUT,fontsize=10)
fig.savefig("gold_ppn_monte_carlo.png",dpi=200,bbox_inches="tight",facecolor="white")
