#!/usr/bin/env python3
"""
Post-build enrichment: join REAL COGS (wedash estBaseCost) and DEMOGRAPHIC reach/convert
(Meta age+gender breakdowns) onto every design in data.json, then rewrite data.json + data.js.

Inputs (backend/raw/):
  jm_cogs_all.json  - exact per-campaign COGS by fbId (from jm_cogs_all.py, /report/stores/campaigns/5)
  cogs_ratios.json  - per-product COGS ratios + portfolio default (fallback)
  reach_age.json    - top-N campaigns' age breakdown, tagged (from reach_pull.py)
  reach_gender.json - same campaigns' gender breakdown by fbId (from reach_pull_gender.py)

Cost model (locked with owner): contribution = rev - COGS - FEE*rev - ad_spend
  (shipping already inside COGS; payment fee 4%; refunds/discounts excluded for now)
"""
import json, os
HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)
RAW = os.path.join(HERE, "raw")
FEE = 0.04

def load(p, d=None):
    try: return json.load(open(p))
    except Exception: return d

data = json.load(open(os.path.join(ROOT, "data.json")))
designs = data["designs"]; campaigns = data["campaigns"]
cogs = load(os.path.join(RAW, "jm_cogs_all.json"), {}).get("by_fb", {})
ratios = load(os.path.join(RAW, "cogs_ratios.json"), {"ratio": {}, "default": 0.246})
pratio, DEFR = ratios.get("ratio", {}), ratios.get("default", 0.246)
age = load(os.path.join(RAW, "reach_age.json"), {}).get("campaigns", [])
gender = load(os.path.join(RAW, "reach_gender.json"), {}).get("by_fb", {})

# fb -> design code
fb2code = {}
for code, cl in campaigns.items():
    for c in cl:
        if c.get("fb"): fb2code[c["fb"]] = code

# demographics aggregated to design code
demo = {}  # code -> {"aR":{seg:impr},"aC":{seg:pc},"gR":{},"gC":{}}
def bump(d, k, seg, v): d.setdefault(k, {}); d[k][seg] = d[k].get(seg, 0) + v
for rec in age:
    code = fb2code.get(rec["fb"])
    if not code: continue
    e = demo.setdefault(code, {})
    for r in rec.get("age", []):
        bump(e, "aR", r["seg"], r["impr"]); bump(e, "aC", r["seg"], r["pc"])
for fb, rows in gender.items():
    code = fb2code.get(fb)
    if not code: continue
    e = demo.setdefault(code, {})
    for r in rows:
        bump(e, "gR", r["seg"], r["impr"]); bump(e, "gC", r["seg"], r["pc"])

# per-design COGS ratio from exact jm_cogs (sum over the design's campaign fbIds)
def design_cogs_ratio(code, product):
    sc = sr = 0.0
    for c in campaigns.get(code, []):
        m = cogs.get(c.get("fb"))
        if m and m.get("rev", 0) > 0:
            sc += m["cogs"]; sr += m["rev"]
    if sr > 0: return sc / sr, "exact"
    if product in pratio: return pratio[product], "product"
    return DEFR, "default"

n_demo = n_exact = 0
tot = {"spend": 0.0, "rev": 0.0, "real_cogs": 0.0, "real_profit": 0.0, "proxy": 0.0}
for d in designs:
    rv, sp = d.get("rev", 0) or 0, d.get("spend", 0) or 0
    r, src = design_cogs_ratio(d["code"], d.get("product", ""))
    if src == "exact": n_exact += 1
    real_cogs = r * rv
    real_profit = rv - real_cogs - FEE * rv - sp
    d["real_cogs"] = round(real_cogs, 2)
    d["real_profit"] = round(real_profit, 2)
    d["real_margin"] = round((1 - r - FEE) * 100, 1) if rv else 0
    d["cogs_ratio"] = round(r, 4)
    d["cogs_src"] = src
    d["real_be_roas"] = round(1 / (0.96 - r), 2) if r < 0.96 else None
    e = demo.get(d["code"])
    if e:
        d["age_reach"] = {k: round(v) for k, v in e.get("aR", {}).items()}
        d["age_conv"] = {k: round(v, 1) for k, v in e.get("aC", {}).items()}
        d["gender_reach"] = {k: round(v) for k, v in e.get("gR", {}).items()}
        d["gender_conv"] = {k: round(v, 1) for k, v in e.get("gC", {}).items()}
        d["demo_cov"] = True; n_demo += 1
    else:
        d["demo_cov"] = False
    if sp > 0:
        tot["spend"] += sp; tot["rev"] += rv; tot["real_cogs"] += real_cogs
        tot["real_profit"] += real_profit; tot["proxy"] += 0.70 * rv - sp

# summary
be = 1 / (0.96 - tot["real_cogs"] / tot["rev"]) if tot["rev"] else 0
data["summary"]["real"] = {
    "profit": round(tot["real_profit"]), "cogs": round(tot["real_cogs"]),
    "cogs_pct": round(100 * tot["real_cogs"] / tot["rev"], 1) if tot["rev"] else 0,
    "be_roas": round(be, 2), "fee": FEE, "proxy_profit": round(tot["proxy"]),
    "demo_designs": n_demo, "cogs_exact_designs": n_exact,
}
data["note"] = ("FB channel only; PROXY profit=0.70*rev-spend (breakeven 1.43); "
                "REAL profit=rev-COGS-4%fee-spend using wedash estBaseCost (see summary.real); "
                "age_reach/age_conv/gender_* = Meta breakdown impressions/purchases per segment (demo_cov designs only)")

json.dump(data, open(os.path.join(ROOT, "data.json"), "w"), ensure_ascii=False)
with open(os.path.join(ROOT, "data.js"), "w") as fp:
    fp.write("window.JM = "); json.dump(data, fp, ensure_ascii=False); fp.write(";")

print(f"enriched {len(designs)} designs | exact-COGS {n_exact} | demo-covered {n_demo}")
print(f"PROXY profit ${tot['proxy']:,.0f}  ->  REAL profit ${tot['real_profit']:,.0f}  (COGS {data['summary']['real']['cogs_pct']}% of rev, breakeven ROAS {be:.2f})")
