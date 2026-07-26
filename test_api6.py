import sys, json
sys.path.append("./backend")
from welast import get_token, get

token = get_token()

res = get("/orders?page=1&pageSize=2&storeCode=all&startDate=2026-07-20&endDate=2026-07-23&platform=Shopify&fulfillType=All", token)
if "data" in res and res["data"]:
    order_id = res["data"][0]["id"]
    try:
        detail = get(f"/orders/{order_id}", token)
        print("landingSite:", detail.get("landingSite"))
        print("firstVisit:", detail.get("firstVisit"))
        print("lastVisit:", detail.get("lastVisit"))
        print("noteAttributes:", detail.get("noteAttributes"))
    except Exception as e:
        pass
