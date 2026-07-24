#!/usr/bin/env python3
"""Re-pull JM campaigns keeping inlineLinkClicks (for CPC) + impressions (CPM). Overwrites raw/campaigns.json."""
import subprocess, welast, json, urllib.parse, sys, os
from datetime import date, timedelta

KEEP = ('id','name','spend','rev','orderCount','impressions','inlineLinkClicks','status','fbId','adFbId','thumbnail')
af = {'advancedFilter[groups][0][conditions][0][field]':'spend',
      'advancedFilter[groups][0][conditions][0][operator]':'GreaterThan',
      'advancedFilter[groups][0][conditions][0][value]':'0'}
afq = urllib.parse.urlencode(af)
def last_dom(y,m):
    nm=date(y,m,1)+timedelta(days=32); return date(nm.year,nm.month,1)-timedelta(days=1)
END = date.today(); out = {}
for m in range(1, END.month + 1):
    s=date(2026,m,1); e=min(last_dom(2026,m),END); key=f"2026-{m:02d}"; rows=[]; page=1
    while True:
        tok=welast.get_token()
        url=f"/report/stores/campaigns/5?startDate={s}&endDate={e}&page={page}&pageSize=500&{afq}"
        d=json.loads(subprocess.check_output(["curl","-s","--max-time","150","https://base.welast.vn"+url,
            "-H","accept: application/json","-H","origin: https://data.welast.vn",
            "-H",f"authorization: Bearer {tok}"],timeout=160))
        c=[x for x in d.get("campaigns",[]) if float(x.get('spend') or 0)>0]
        rows+=[{k:x.get(k) for k in KEEP} for x in c]
        tot=int(d.get("total") or 0)
        print(f"  {key} p{page}: +{len(c)} (tot~{tot})", file=sys.stderr)
        if page*500>=tot or not d.get("campaigns"): break
        page+=1
    out[key]=rows
raw_dir = os.path.join(os.path.dirname(__file__), "raw")
os.makedirs(raw_dir, exist_ok=True)
json.dump(out, open(os.path.join(raw_dir, "campaigns.json"), "w"))
print("DONE", sum(len(v) for v in out.values()), "rows")