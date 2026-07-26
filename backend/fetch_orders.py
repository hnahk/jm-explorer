#!/usr/bin/env python3
"""
Pull Shopify orders from WeLast, filtering for Facebook Paid Traffic.
Extracts true Net Revenue, designCodes, and items to raw/orders.json.
"""
import subprocess, welast, json, sys, os
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor

def get_detail(token, oid):
    try:
        out = subprocess.check_output(["curl", "-s", "--max-time", "30",
            f"https://base.welast.vn/orders/{oid}",
            "-H", "accept: application/json", "-H", "origin: https://data.welast.vn",
            "-H", f"authorization: Bearer {token}"])
        return json.loads(out)
    except Exception as e:
        return None

def main():
    END = date.today()
    out = {}
    raw_dir = os.path.join(os.path.dirname(__file__), "raw")
    orders_file = os.path.join(raw_dir, "orders.json")
    if os.path.exists(orders_file):
        try:
            out = json.load(open(orders_file))
        except:
            pass
            
    tok = welast.get_token()
    
    start_m = 1
    if not os.environ.get("FULL_SYNC"):
        start_m = max(1, END.month - 1)
        
    for m in range(start_m, END.month + 1):
        s = date(2026, m, 1)
        nm = date(2026, m, 1) + timedelta(days=32)
        e = min(date(nm.year, nm.month, 1) - timedelta(days=1), END)
        key = f"2026-{m:02d}"
        
        if os.environ.get("TEST_QUICK"):
            s = date(2026, 7, 20)
            e = date(2026, 7, 21)
            
        print(f"Fetching {s} to {e}...", file=sys.stderr)
        rows = []
        page = 1
        
        while True:
            url = f"/orders?page={page}&pageSize=100&storeCode=all&startDate={s}&endDate={e}&platform=Shopify&fulfillType=All"
            try:
                d = json.loads(subprocess.check_output(["curl","-s","--max-time","60",
                    "https://base.welast.vn"+url,
                    "-H","accept: application/json","-H","origin: https://data.welast.vn",
                    "-H",f"authorization: Bearer {tok}"]))
            except:
                break
            
            orders = d.get("data", [])
            tot = int(d.get("total") or 0)
            print(f"  {key} p{page}: list +{len(orders)} (tot~{tot})", file=sys.stderr)
            
            with ThreadPoolExecutor(max_workers=10) as exe:
                details = list(exe.map(lambda o: get_detail(tok, o["id"]), orders))
            
            fb_orders = []
            for base, det in zip(orders, details):
                if not det: continue
                fv = det.get("firstVisit") or {}
                source = (fv.get("source") or "").lower()
                med = (fv.get("medium") or "").lower()
                if "facebook" in source or "paid" in med:
                    fb_orders.append({
                        "id": base["id"],
                        "name": base.get("orderName"),
                        "createdAt": base.get("createdAt"),
                        "totalPrice": float(base.get("totalPrice") or 0),
                        "cogs": float(base.get("cogs") or 0),
                        "designCodes": base.get("designCodes", []),
                        "campaign": fv.get("campaign"),
                        "items": [it.get("name") for it in det.get("orderItems", [])]
                    })
            
            rows.extend(fb_orders)
            print(f"    -> {len(fb_orders)} were FB Paid.", file=sys.stderr)
            
            if page * 100 >= tot or not orders: break
            page += 1
            if os.environ.get("TEST_QUICK"): break
            
        out[key] = rows
        if os.environ.get("TEST_QUICK"): break

    raw_dir = os.path.join(os.path.dirname(__file__), "raw")
    os.makedirs(raw_dir, exist_ok=True)
    json.dump(out, open(os.path.join(raw_dir, "orders.json"), "w"))
    print("DONE", sum(len(v) for v in out.values()), "FB orders")

if __name__ == "__main__":
    main()
