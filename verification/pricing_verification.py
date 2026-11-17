"""Independent check of the Gold PPN pricing workbook.
Run from this folder:  python3 pricing_verification.py
Reads ../data/GVZCLS.csv for the volatility check."""
import csv, os
from datetime import date
from math import log, sqrt, exp
from statistics import NormalDist
N = NormalDist().cdf
S0 = K = 4650.0; r = 0.0434; sigma = 0.1784; T = 10.0; fee = 3.0

def call(K_, s=sigma):
    d1 = (log(S0 / K_) + (r + 0.5 * s * s) * T) / (s * sqrt(T))
    return S0 * N(d1) - K_ * exp(-r * T) * N(d1 - s * sqrt(T))

def fair_cap(budget):
    """Cap c such that (ATM call - call struck at S0*(1+c)) per $100 note = budget."""
    lo, hi = 0.01, 20.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if (call(S0) - call(S0 * (1 + mid))) / S0 * 100 > budget: hi = mid
        else: lo = mid
    return mid

d1 = (r + 0.5 * sigma**2) * T / (sigma * sqrt(T)); d2 = d1 - sigma * sqrt(T)
full = call(S0) / S0 * 100
print("1. Black-Scholes ATM call")
print(f"   d1 {d1:.4f}  d2 {d2:.4f}  N(d1) {N(d1):.4f}  N(d2) {N(d2):.4f}")
print(f"   call per oz ${call(S0):,.2f}   cost of 100% participation per $100 note ${full:.2f}")
print("\n2. Participation rate and fair cap, by compounding convention")
for name, zcb in [("continuous (workbook, report)", 100 * exp(-r * T)), ("annual (other LLM)", 100 / (1 + r) ** T)]:
    b = 100 - zcb - fee
    print(f"   {name:30s} ZCB ${zcb:.2f}  budget ${b:.2f}  participation {b / full:.2%}  fair cap +{fair_cap(b):.1%}")
print("\n3. Volatility sensitivity (continuous compounding, budget fixed)")
b = 100 - 100 * exp(-r * T) - fee
for s in [0.15, 0.1784, 0.20, 0.25, 0.30, 0.35, 0.3704]:
    c = call(S0, s) / S0 * 100
    print(f"   sigma {s:7.2%}  call cost ${c:6.2f}  participation {b / c:.2%}")
print("\n4. GVZ volatility inputs")
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "GVZCLS.csv")
rows = []
for d, v in list(csv.reader(open(path)))[1:]:
    try: rows.append((date.fromisoformat(d), float(v)))
    except ValueError: pass
vals = [v for _, v in rows]
print(f"   {len(rows)} observations, {rows[0][0]} to {rows[-1][0]}, mean {sum(vals) / len(vals):.2f}")
upto = [v for d, v in rows if d <= date(2026, 4, 6)]
print(f"   mean using only data up to 2026-04-06: {sum(upto) / len(upto):.2f} ({len(upto)} observations)")
print(f"   reading on 2026-04-06: {dict(rows)[date(2026, 4, 6)]}")
