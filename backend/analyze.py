#!/usr/bin/env python3
"""Analyze enriched data.json: real profit by occasion/product + demographic mismatch vs profit."""
import json, os
from collections import defaultdict
d = json.load(open(os.path.join(os.path.dirname(__file__), "..", "data.json")))
des = d["designs"]
adv = [x for x in des if (x.get("spend") or 0) > 0]
AGES = ["18-24","25-34","35-44","45-54","55-64","65+"]

def tbl(keyfn, rows, top=10):
    g = defaultdict(lambda: defaultdict(float)); w = defaultdict(int)
    for x in rows:
        k = keyfn(x); a = g[k]
        a["sp"] += x["spend"]; a["rv"] += x["rev"]; a["rc"] += x.get("real_cogs",0); a["rp"] += x.get("real_profit",0); a["px"] += x.get("profit",0)
        if x.get("real_profit",0) > 0: w[k] += 1
        a["n"] += 1
    out = []
    for k, a in g.items():
        be = 1/(0.96 - a["rc"]/a["rv"]) if a["rv"] else 0
        out.append((a["sp"], k, a, w[k], be))
    return sorted(out, key=lambda t:-t[0])[:top]

print("=== REAL PROFIT BY OCCASION (advertised) ===")
print(f"{'occasion':<16}{'des':>5}{'win':>5}{'spend':>11}{'proxyP':>11}{'realP':>11}{'margin%':>8}{'beROAS':>7}")
for sp,k,a,win,be in tbl(lambda x:x.get("occasion") or "?", adv, 12):
    mg = 100*(a["rv"]-a["rc"])/a["rv"] if a["rv"] else 0
    print(f"{k[:15]:<16}{int(a['n']):>5}{win:>5}{a['sp']:>11,.0f}{a['px']:>11,.0f}{a['rp']:>11,.0f}{mg:>7.1f}%{be:>7.2f}")

print("\n=== REAL BREAKEVEN BY PRODUCT (top by spend) ===")
print(f"{'product':<34}{'spend':>11}{'realP':>11}{'margin%':>8}{'beROAS':>7}")
for sp,k,a,win,be in tbl(lambda x:x.get("product") or "?", adv, 12):
    mg = 100*(a["rv"]-a["rc"])/a["rv"] if a["rv"] else 0
    print(f"{k[:33]:<34}{a['sp']:>11,.0f}{a['rp']:>11,.0f}{mg:>7.1f}%{be:>7.2f}")

# demographic mismatch vs profit (demo-covered advertised designs)
dc = [x for x in adv if x.get("demo_cov")]
def shares(x, kr, kc):
    R, C = x.get(kr,{}), x.get(kc,{})
    ti, tp = sum(R.values()) or 1, sum(C.values()) or 1
    return {a: (R.get(a,0)/ti, C.get(a,0)/tp) for a in set(list(R)+list(C))}
# young-reach-skew = reach share under-45 minus convert share under-45
def young_over(x):
    s = shares(x,"age_reach","age_conv"); U=["18-24","25-34","35-44"]
    return 100*(sum(s.get(a,(0,0))[0] for a in U) - sum(s.get(a,(0,0))[1] for a in U))
buckets = {"high mismatch (>15pt young-over)":[], "mid (5-15)":[], "aligned (<5)":[]}
for x in dc:
    yo = young_over(x)
    b = "high mismatch (>15pt young-over)" if yo>15 else ("mid (5-15)" if yo>5 else "aligned (<5)")
    buckets[b].append(x)
print(f"\n=== DEMOGRAPHIC MISMATCH vs REAL PROFIT ({len(dc)} demo-covered advertised designs) ===")
print(f"{'bucket':<34}{'des':>5}{'spend':>11}{'realP':>11}{'ROAS':>7}{'profit/$spend':>13}")
for b, xs in buckets.items():
    sp=sum(x['spend'] for x in xs); rp=sum(x.get('real_profit',0) for x in xs); rv=sum(x['rev'] for x in xs)
    print(f"{b:<34}{len(xs):>5}{sp:>11,.0f}{rp:>11,.0f}{(rv/sp if sp else 0):>7.2f}{(rp/sp if sp else 0):>13.3f}")

# portfolio demographic reach vs convert (spend-weighted over demo-covered)
aR=defaultdict(float); aC=defaultdict(float)
for x in dc:
    for a,v in x.get("age_reach",{}).items(): aR[a]+=v
    for a,v in x.get("age_conv",{}).items(): aC[a]+=v
ti=sum(aR.values()) or 1; tp=sum(aC.values()) or 1
print("\n=== PORTFOLIO AGE reach% vs convert% (demo-covered) ===")
for a in AGES:
    print(f"  {a:>6}: reach {100*aR[a]/ti:5.1f}%  convert {100*aC[a]/tp:5.1f}%  gap {100*aC[a]/tp-100*aR[a]/ti:+5.1f}")
