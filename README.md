# JoyMade Trace Explorer — H1 2026 (Facebook)

An interactive tool to **trace one thread across all five systems** and back:

```
FINANCIAL ─(occasion / evergreen)─ PLAN
PLAN ─(occasion · niche · recipient · persona ; unique = IDEA CODE)─ IDEA
IDEA ─(product live link)─ DESIGN & LISTING
IDEA ─(idea code + product link, 1 → many)─ MEDIA (videos, each with a TB##### id)
MEDIA ─(TB##### in campaign name)─ ADS ─(rev · profit · roas · cpa · cpm · [cpc])─ FINANCIAL
```

The universal hard join key across every code system is the **design number `C####/B####`**.

## Open it
Double-click **`explorer.html`** (no server needed — it loads `data.js` locally, stays fully private on your machine).

- **Designs** tab — one row per idea code. Filter by occasion / bucket / creator / product; sort any column; search code or idea.
- **Campaigns** tab — every campaign (reverse trace); each links back to its design + media (TB).
- **Click any row** → the drawer shows the whole 6-stage chain (Plan → Idea → Design/Listing → Media → Ads → Financial) with the join key on each stage.
- **P0 chips** (Winners / Losers / Untestable) are click-to-filter.

## The numbers (reconcile to the store P&L)
- Net FB profit **−$385,897** · spend $2.53M · rev $3.06M · breakeven **ROAS 1.43**.
- Funnel: **5,770 created → 5,516 live → 3,234 advertised → 34 profitable**.
- P0: winners +$126K (34) · conclusive losers −$112K (223) · **untestable −$399K (2,977)** ← the loss.

## The backend (`backend/`)
- **`welast.py`** — API client. `get_token()` refreshes the short-lived JWT from the 7-day refresh token; `get(path, token)` hits base.welast.vn.
- **`build.py`** — the pipeline. Loads the raw API pulls + the three Feishu exports, joins them on the design code, computes buckets/funnel/P0, and writes `../data.js` + `../data.json`. Fully commented; read it to see exactly how each number is produced.
- **`raw/`** — cached API pulls (`products.json` = catalog, `campaigns.json` = per-campaign spend/rev/orders/impressions) so the build is offline & deterministic.

### Inputs (from ~/Downloads)
- `WorkFlows 2026 1.0_💡 Product Table_khanh.xlsx` — ideas: idea code, creator, occasion, niche, recipient, persona, Created Date, Design Done Date.
- `WorkFlows 2026 1.0_Media Table 1.0_khanh.xlsx` — videos: idea code, Numbering ID (TB), Product Link, done date.
- `JM Idea's Plan .xlsx` — weekly planned vs created idea quantities.

### Regenerate
```bash
cd backend && python3 build.py       # rebuilds data.js from raw/ + the xlsx inputs
```
To pull fresh API data, use `welast.py` to refetch the catalog and campaigns into `raw/` first
(ask the user for a current refresh token — it is a secret and is not stored here).

## What each design row shows
Full **idea code** (e.g. `JMAPPBH2PT2B6971`; the short `C####/B####` is the internal join key, on hover).
Drawer stages carry the live links: ③ **product live link**, ④ **finished-video links** (▶ Google Drive,
per video), ⑤ **ad-creative** (🖼️ thumbnail) + Facebook campaign id per campaign, and CPA/CPM/CPC.

## Sharing (private link for your boss)
`share.html` is a self-contained copy for publishing as a **private** Claude artifact (artifacts can't
load an external `data.js`, so data is inlined). It includes **all advertised designs** (never-advertised
catalog designs omitted); ad-creative thumbnails are kept for winners+losers only to control size (the
local `explorer.html` has thumbnails for everything). Rebuild with `python3 backend/build_share.py`, then
re-publish `share.html`. Link: `https://claude.ai/code/artifact/234c4933-baf1-42e9-856a-1b17b34d3067`
(private until you share it from the artifact's share menu).

## Known limitations
- **Facebook channel only** (Axon/Google excluded, per scope).
- **CPC / CPM / CPA** all computed (from clicks / impressions / orders) — per campaign and per design.
- **Plan↔recipient crosswalk** — the plan's granular niches are mapped to the **Recipient** field
  (`Niche` collapses ~71% to "Family"). Shown in the drawer's ① Plan stage. Caveat: "Memorial" and
  "Reaction/Scale" are theme/strategy labels, not person-recipients, so they show planned-but-0-created.
- **Media coverage** — full-history Media export: 2,500 idea codes have videos (74% of advertised). The
  media↔ads `TB` link resolves for 91% of campaigns that carry a TB id; ~50% of campaigns have no TB
  token in their name (older naming). `build.py` auto-picks the newest `Media Table 1.0*.xlsx` in ~/Downloads.