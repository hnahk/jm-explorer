import sys, json
sys.path.append("./backend")
from welast import get_token, get

token = get_token()
print("Token:", len(token))

# 1. Test Orders
try:
    print("\n--- Orders API ---")
    orders = get("/orders?page=1&pageSize=5&storeCode=all&startDate=2026-07-20&endDate=2026-07-23&platform=Shopify&fulfillType=All", token)
    print("Keys in response:", orders.keys())
    if "data" in orders and orders["data"]:
        print("Keys in first order:", orders["data"][0].keys())
        first = orders["data"][0]
        # Look for UTMs
        for k, v in first.items():
            if isinstance(v, (dict, list)): continue
            if "utm" in str(v).lower() or "facebook" in str(v).lower():
                print(f"UTM found in {k}: {v}")
        if "landingSite" in first: print("landingSite:", first["landingSite"])
        if "tags" in first: print("tags:", first["tags"])
        if "noteAttributes" in first: print("noteAttributes:", first["noteAttributes"])
except Exception as e:
    print("Orders error:", e)

# 2. Test Demographics guessing
try:
    print("\n--- Demographics API Guess 1 ---")
    res = get("/report/breakdown/campaigns?breakdown=country&startDate=2026-07-20&endDate=2026-07-23", token)
    print("Result 1:", list(res.keys()) if isinstance(res, dict) else type(res))
except Exception as e:
    print("Guess 1 error:", e)

try:
    print("\n--- Demographics API Guess 2 ---")
    res = get("/report/demographics/campaigns?startDate=2026-07-20&endDate=2026-07-23", token)
    print("Result 2:", list(res.keys()) if isinstance(res, dict) else type(res))
except Exception as e:
    print("Guess 2 error:", e)
