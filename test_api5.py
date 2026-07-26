import sys, json
sys.path.append("./backend")
from welast import get_token, get

token = get_token()

res = get("/orders?page=1&pageSize=2&storeCode=all&startDate=2026-07-20&endDate=2026-07-23&platform=Shopify&fulfillType=All", token)
if "data" in res and res["data"]:
    order_id = res["data"][0]["id"]
    try:
        detail = get(f"/orders/{order_id}", token)
        print("Detail keys:", detail.keys())
        print("Detail dump:", json.dumps(detail, indent=2)[:800])
    except Exception as e:
        print("Detail error:", e)
