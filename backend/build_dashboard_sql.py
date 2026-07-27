import json
import sqlite3
import os
from datetime import date, timedelta
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DB_PATH = os.path.join(ROOT, "jm_explorer.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def canon_product(p):
    if not p: return 'Other'
    p=str(p).lower()
    if 'mug' in p: return 'Mug'
    if 'tumbler' in p: return 'Tumbler'
    if 'canvas' in p: return 'Canvas/Poster'
    if 'poster' in p: return 'Canvas/Poster'
    if 'ornament' in p: return 'Ornament'
    if 'shirt' in p or 'apparel' in p or 'hoodie' in p: return 'Apparel'
    if 'blanket' in p: return 'Blanket'
    if 'pillow' in p: return 'Pillow'
    if 'acrylic' in p: return 'Acrylic Plaque'
    if 'wood' in p: return 'Wooden Sign'
    if 'metal' in p: return 'Metal Sign'
    if 'glass' in p: return 'Glassware'
    if 'mat' in p: return 'Doormat'
    if 'tote' in p: return 'Tote Bag'
    return (str(p or 'Other').strip() or 'Other')[:20]

def build_dashboard():
    conn = get_db()
    c = conn.cursor()
    
    # 1. Overview KPIs
    c.execute('SELECT COUNT(*) as n, SUM(spend) as sp, SUM(rev) as rv FROM designs WHERE spend > 0')
    row = c.fetchone()
    tot_spend = row['sp'] or 0
    tot_rev = row['rv'] or 0
    tot_profit = (0.70 * tot_rev) - tot_spend
    roas = round(tot_rev / tot_spend, 2) if tot_spend else 0
    c.execute('SELECT COUNT(*) as n FROM designs')
    tot_designs = c.fetchone()['n']
    
    # Evergreen KPIs
    c.execute("SELECT SUM(spend) as sp, SUM(rev) as rv FROM designs WHERE occasion='Evergreen' OR occasion IS NULL")
    ev_row = c.fetchone()
    ever_sp = ev_row['sp'] or 0
    ever_rv = ev_row['rv'] or 0
    ever_profit = (0.70 * ever_rv) - ever_sp
    
    # Load original data.json summary to merge
    with open(os.path.join(ROOT, "data.json")) as f:
        data = json.load(f)
    
    # Occasions stats
    c.execute('''
        SELECT occasion, SUM(spend) as spend, SUM(rev) as rev, COUNT(*) as cnt 
        FROM designs WHERE occasion IS NOT NULL 
        GROUP BY occasion ORDER BY spend DESC
    ''')
    raw_occs = c.fetchall()
    
    tot_loss = -sum(min(0, 0.70*(r['rev'] or 0) - (r['spend'] or 0)) for r in raw_occs) or 1
    
    occasions = []
    for r in raw_occs:
        sp = r['spend'] or 0
        rv = r['rev'] or 0
        pr = 0.70 * rv - sp
        occ_name = r['occasion']
        
        occasions.append({
            "name": occ_name,
            "evergreen": occ_name == "Evergreen",
            "spend": round(sp),
            "rev": round(rv),
            "profit": round(pr),
            "roas": round(rv / sp, 2) if sp else 0,
            "n": r['cnt'],
            "pct_spend": round(sp / tot_spend * 100, 1) if tot_spend else 0,
            "pct_loss": round(-pr / tot_loss * 100, 1) if pr < 0 else 0
        })
        
    overview = {
        "kpi": {
            "profit": round(tot_profit), "spend": round(tot_spend), "rev": round(tot_rev),
            "roas": roas, "breakeven": 1.43, "advertised": row['n'], "designs": tot_designs
        },
        "occasions": occasions,
        "funnel": data["summary"]["funnel"],
        "p0": data["summary"]["p0"],
        "evergreen": {
            "spend": round(ever_sp), "profit": round(ever_profit),
            "roas": round(ever_rv / ever_sp, 2) if ever_sp else 0,
            "seasonal_spend": round(tot_spend - ever_sp),
            "seasonal_profit": round(tot_profit - ever_profit)
        }
    }
    
    # 2. Plan Hierarchy
    hier = []
    OCC_ORDER = ["Valentine", "Easter", "Mother's Day", "Graduation", "Father's Day", "4th/Patriotic", "Back to School", "World Cup", "Christmas", "Evergreen"]
    
    c.execute("SELECT * FROM occasions")
    occ_map = {r['name']: r for r in c.fetchall()}
    
    tot_served = 0
    tot_act = 0
    
    for occ in OCC_ORDER:
        jm_plan = []
        occ_meta = occ_map.get(occ)
        if not occ_meta: continue
        
        dated = not occ_meta['evergreen']
        occ_date = date.fromisoformat(occ_meta['occ_date']) if dated and occ_meta['occ_date'] else None
        
        # Get plan rows for this occasion
        if dated:
            w1 = occ_date - timedelta(days=56)
            w2 = occ_date
            c.execute('''
                SELECT p.*, w.start_date, w.end_date 
                FROM plan_rows p 
                JOIN week_meta w ON p.week = w.week
                WHERE w.start_date <= ? AND w.end_date >= ?
            ''', (w2.isoformat(), w1.isoformat()))
        else:
            c.execute('''
                SELECT p.*, w.start_date, w.end_date 
                FROM plan_rows p 
                JOIN week_meta w ON p.week = w.week
                WHERE LOWER(w.theme) LIKE '%evergreen%'
            ''')
            
        plan_rows = c.fetchall()
        for pr in plan_rows:
            cp = canon_product(pr['product'])
            
            # Match ideas based on T+3 weeks rule
            week = pr['week']
            # parse month from week (e.g. 12W1 -> 12)
            import re
            m = re.match(r'(\d+)W', week)
            p_mo = int(m.group(1)) if m else None
            p_yr = (2025 if p_mo >= 8 else 2026) if p_mo else None
            p_T = date(p_yr, p_mo, 1) if p_mo else None
            p_Tend = p_T + timedelta(days=21) if p_T else None
            
            matched = []
            if p_T:
                c.execute('''
                    SELECT * FROM designs 
                    WHERE d_live >= ? AND d_live <= ? AND spend > 0
                ''', (p_T.isoformat(), p_Tend.isoformat()))
                for d in c.fetchall():
                    if cp != 'Other' and canon_product(d['product']) != cp: continue
                    matched.append(d)
                    
            matched_formatted = []
            for d in sorted(matched, key=lambda x: -(x['spend'] or 0)):
                served = (d['days_before_occ'] is not None and d['days_before_occ'] >= 14) if dated else None
                matched_formatted.append({
                    "full": d['full_code'] or d['code'],
                    "idea": (d['niche'] or '')[:26],
                    "link": d['link'] or '',
                    "roas": d['roas'],
                    "spend": round(d['spend']),
                    "served": served
                })
                
            m_spend = sum(d['spend'] or 0 for d in matched)
            m_rev = sum(d['rev'] or 0 for d in matched)
            m_profit = sum(d['profit'] or 0 for d in matched)
            m_roas = round(m_rev / m_spend, 2) if m_spend else 0

            jm_plan.append({
                "week": week,
                "section": pr['section'],
                "product_type": pr['product_type'],
                "product": pr['product'],
                "niche": pr['niche'],
                "planned": pr['planned'],
                "pic": pr['pic'],
                "created": pr['created'],
                "pending": pr['pending'],
                "m_spend": round(m_spend),
                "m_rev": round(m_rev),
                "m_profit": round(m_profit),
                "m_roas": m_roas,
                "matched": matched_formatted
            })
            
        # Acts (matched designs overall for occasion)
        c.execute('SELECT * FROM designs WHERE occasion = ? AND spend > 0 ORDER BY spend DESC', (occ,))
        acts = c.fetchall()
        rows = []
        for d in acts:
            served = (d['days_before_occ'] is not None and d['days_before_occ'] >= 14)
            if served: tot_served += 1
            tot_act += 1
            rows.append({
                "full": d['full_code'] or d['code'],
                "idea": (d['niche'] or '')[:32],
                "product": canon_product(d['product']),
                "recipient": (d['recipient'] or '')[:18],
                "d_ads": d['d_ads'],
                "d_live": d['d_live'],
                "days_before": d['days_before_occ'],
                "served": served,
                "link": d['link'] or '',
                "spend": round(d['spend']),
                "profit": round(d['profit']),
                "roas": d['roas']
            })
            
        quarter = f"Q{(occ_date.month-1)//3 + 1} {occ_date.year}" if dated else "Ongoing"
        month = occ_date.strftime("%B") if dated else "All Year"
        
        hier.append({
            "occasion": occ,
            "occ_date": occ_meta['occ_date'],
            "quarter": quarter,
            "month": month,
            "window": [w1.isoformat(), w2.isoformat()] if dated else None,
            "jm_plan": jm_plan,
            "acts": rows
        })
        
    # Master & Timeline
    master = defaultdict(list)
    c.execute('SELECT * FROM masterplan_idea')
    for r in c.fetchall():
        master[r['occasion']].append({
            "dir": r['dir'], "pct": r['pct'], "searchvol": r['searchvol'], "rank": r['rank']
        })
        
    timeline = defaultdict(list)
    c.execute('SELECT * FROM jm_timeline')
    for r in c.fetchall():
        timeline[r['occasion']].append({
            "week": r['week'], "text": r['text']
        })
        
    c.execute('SELECT * FROM week_meta')
    weeks = {r['week']: dict(r) for r in c.fetchall()}
    weeks_sorted = sorted([k for k,v in weeks.items() if v['start_date']], key=lambda k: weeks[k]['start_date'])
    
    dash = {
        "overview": overview,
        "plan": {
            "hierarchy": hier,
            "master": master,
            "timeline": timeline,
            "served": {
                "rate": round(tot_served / tot_act * 100) if tot_act else 0,
                "served": tot_served,
                "actual": tot_act
            },
            "weeks": weeks_sorted,
            "week_meta": weeks
        }
    }
    
    with open(os.path.join(ROOT, "dash.json"), "w") as f:
        json.dump(dash, f)
        
    with open(os.path.join(ROOT, "dash.js"), "w") as f:
        f.write("const DASH = " + json.dumps(dash) + ";")
        
    print("Dashboard JSON generated successfully.")

if __name__ == '__main__':
    build_dashboard()
