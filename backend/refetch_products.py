#!/usr/bin/env python3
"""Re-pull JM product catalog from base.welast.vn. Overwrites raw/products.json."""
import subprocess, welast, json, sys, os

def refetch():
    print("Fetching product catalog from WeLast API...", file=sys.stderr)
    tok = welast.get_token()
    page = 1
    page_size = 200
    all_products = []
    
    while True:
        url = f"/market/products/store/20?page={page}&pageSize={page_size}&sortField=shopifyPublishedAt&sortOrder=descend"
        try:
            d = welast.get(url, tok)
        except Exception as e:
            tok = welast.get_token()
            d = welast.get(url, tok)
            
        prods = d.get("products", []) if isinstance(d, dict) else []
        if not prods:
            break
            
        all_products.extend(prods)
        tot = int(d.get("total") or 0) if isinstance(d, dict) else len(all_products)
        print(f"  Page {page}: +{len(prods)} products (total: {len(all_products)} / {tot})", file=sys.stderr)
        
        if page * page_size >= tot:
            break
        page += 1

    raw_dir = os.path.join(os.path.dirname(__file__), "raw")
    os.makedirs(raw_dir, exist_ok=True)
    out_path = os.path.join(raw_dir, "products.json")
    with open(out_path, "w") as fp:
        json.dump(all_products, fp, indent=2)
    print(f"DONE: Saved {len(all_products)} products to {out_path}", file=sys.stderr)

if __name__ == "__main__":
    refetch()
