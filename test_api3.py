import sys, json
sys.path.append("./backend")
from welast import get_token, get

token = get_token()

res = get("/report/summary/campaigns?startDate=2026-07-20&endDate=2026-07-23&breakdown=country", token)
print("Keys with breakdown=country:", res.keys())
if "data" in res:
    print("Data sample:", json.dumps(res["data"][:1], indent=2))

res2 = get("/report/summary/campaigns?startDate=2026-07-20&endDate=2026-07-23&breakdowns=country", token)
print("\nKeys with breakdowns=country:", res2.keys())
if "data" in res2:
    print("Data sample:", json.dumps(res2["data"][:1], indent=2))

