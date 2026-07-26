import sys, json
sys.path.append("./backend")
from welast import get_token, get

token = get_token()

# Let's try getting a specific order or searching
res = get("/orders?page=1&pageSize=2&search=facebook", token)
if "data" in res and res["data"]:
    print("Search 'facebook' returned data!")
    
# Let's see if there is an export endpoint or order detail
try:
    order_id = res["data"][0]["id"]
    detail = get(f"/orders/{order_id}", token)
    print("Detail keys:", detail.keys())
    print("Detail dump:", json.dumps(detail, indent=2)[:500])
except Exception as e:
    print("Detail error:", e)

