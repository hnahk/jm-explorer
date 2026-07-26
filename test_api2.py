import sys, json
sys.path.append("./backend")
from welast import get_token, get

token = get_token()

# 1. Orders
print("\n--- Orders Data ---")
orders = get("/orders?page=1&pageSize=2&storeCode=all&startDate=2026-07-20&endDate=2026-07-23&platform=Shopify&fulfillType=All", token)
if "data" in orders and orders["data"]:
    print(json.dumps(orders["data"][0], indent=2))

# 2. Demographics Guess Errors
print("\n--- Demographics Error ---")
for path in [
    "/report/breakdown/campaigns", 
    "/report/summary/campaigns?breakdowns=country",
    "/report/summary/campaigns?advancedFilter[groups][0][conditions][0][field]=status&advancedFilter[groups][0][conditions][0][operator]=Equal&advancedFilter[groups][0][conditions][0][value]=ACTIVE&breakdowns=country"
]:
    print(f"\nPath: {path}")
    try:
        res = get(path, token)
        print(json.dumps(res)[:200])
    except Exception as e:
        print("Error:", e)
