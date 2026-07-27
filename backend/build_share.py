#!/usr/bin/env python3
"""
Build ../share.html — a self-contained (body-only) copy of explorer.html for publishing as a private
Claude artifact. Artifacts can't load an external data.js, so the data is inlined. Includes ALL
advertised designs (spend>0); the ~2,500 never-advertised catalog designs are dropped (they carry no
financials). Ad-creative thumbnails are kept only for the decision designs (winners+losers) to control
size; the local explorer.html has thumbnails for everything.
Re-publish by pointing the Artifact tool at ../share.html (keeps the same URL).
"""
import json, re, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
J = json.load(open(os.path.join(ROOT, "data.json")))

def sd(d):
    o = dict(d)   # copy ALL design fields so the share never lags the local build
    o["idea"] = (d.get("idea") or "")[:40]
    o["persona"] = (d.get("persona") or "")[:22]
    o["product"] = (d.get("product") or "")[:24]
    o["videos"] = [{"tb": v.get("tb",""), "date": v.get("date"), "vlink": v.get("vlink","")} for v in (d.get("videos") or [])[:6]]
    return o

adv = [d for d in J["designs"] if d["spend"] > 0]
keepc = set(d["code"] for d in adv)
decisive = set(d["code"] for d in adv if d["bucket"] in ("winner", "loser"))   # keep thumbnails only for these
designs = [sd(d) for d in adv]
def cr(code, r):
    row = {k: r[k] for k in ("date","media_id","spend","rev","orders","impr","clk")}
    row["name"] = (r["name"] or "")[:48]; row["fb"] = r.get("fb", "")
    if code in decisive: row["thumb"] = r.get("thumb", "")     # ad-creative link, decision designs only (size)
    return row
camps = {code: [cr(code, r) for r in rows] for code, rows in J["campaigns"].items() if code in keepc}

datajson = json.dumps(designs, ensure_ascii=False, separators=(",", ":"))
campjson = json.dumps(camps, ensure_ascii=False, separators=(",", ":"))
dashjson = open(os.path.join(ROOT, "dash.json"), encoding="utf-8").read()

banner = '<div style="background:var(--warnbg);color:var(--warn);padding:6px 18px;font-size:12px;border-bottom:1px solid var(--line)">Shared view · all advertised designs · ad-creative thumbnails shown for winners + losers</div>'

# 1. Build execdashboard
os.makedirs(os.path.join(ROOT, "execdashboard"), exist_ok=True)
ed = open(os.path.join(ROOT, "execdashboard.html"), encoding="utf-8").read()
ed = ed.replace('<script src="dash.js"></script>', f'<script>window.DASH={dashjson};</script>')
ed = ed.replace('<script src="data.js"></script>', '')
ed = ed.replace('<body>', '<body>\n' + banner)
open(os.path.join(ROOT, "execdashboard", "index.html"), "w", encoding="utf-8").write(ed)

# 2. Build trace
os.makedirs(os.path.join(ROOT, "trace"), exist_ok=True)
tr = open(os.path.join(ROOT, "trace.html"), encoding="utf-8").read()
tr = tr.replace('<script src="dash.js"></script>', f'<script>window.DASH={dashjson};</script>')
tr = tr.replace('<script src="data.js"></script>', f'<script>window.DATA={datajson}; window.CAMP={campjson};</script>')
tr = tr.replace('<body>', '<body>\n' + banner)
open(os.path.join(ROOT, "trace", "index.html"), "w", encoding="utf-8").write(tr)

# 3. Build root index.html redirect
redirect_html = '<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0; url=execdashboard/"></head><body></body></html>'
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(redirect_html)

print("execdashboard: %.2f MB, trace: %.2f MB (designs %d, campaigns %d)" % (
    os.path.getsize(os.path.join(ROOT, "execdashboard", "index.html"))/1e6,
    os.path.getsize(os.path.join(ROOT, "trace", "index.html"))/1e6,
    len(designs), sum(len(v) for v in camps.values())
))