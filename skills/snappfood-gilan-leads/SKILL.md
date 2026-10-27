---
name: snappfood-gilan-leads
description: Use when ARASH needs cafe/restaurant leads in Rasht/Gilan from SnappFood vendor listings (no phones), before creating any lead in Joolio.
---
# SnappFood leads for Gilan/Rasht (ARASH)

## Tool
`/workspace/tools/snappfood-scraper/snappfood_scraper.py` (Python stdlib). It calls the public `snappfood.ir/mobile/v3/restaurant/vendors-list` endpoint that the snappfood.ir website uses (by lat/lon, with an optional query). No login. No Apify actor exists for SnappFood.
**Blocker:** SnappFood returns 403 to non-Iranian IPs, including the box. Run it from an Iranian connection (the user's computer), or skip this source. Don't use proxies to get around the block.

## Run
```
python3 snappfood_scraper.py --lat 37.2808 --lon 49.5832 --query کافه --pages 3 --out snappfood_<date>.csv
```
Rasht center is 37.2808, 49.5832. Anzali is 37.4727, 49.4622. Lahijan is 37.2072, 50.0039. Each page has 20 vendors and there's a 2 s delay between pages. Run separate queries for کافه, رستوران and فست فود.

## CSV columns
`name, category, phone (always blank), address, lat, lon, rating, review_count, link, id, source`.

## Filter (keep these rows only)
- **Gilan only:** address contains گیلان/رشت/another Gilan city, or lat/lon inside 36.5–38.5 N, 48.5–50.6 E.
- **Cafes and restaurants only:** cafe, coffee shop, restaurant, fast food, bakery-cafe and similar.
- **Drop** hypermarkets, supermarkets, grocery and chain stores (هایپر, سوپرمارکت, فروشگاه, بقالی, hypermarket, supermarket, grocery) and closed places.

## Dedupe against Joolio before creating a lead
1. Normalize the phone: Persian/Arabic digits to Latin, strip spaces/dashes, map `+98`/`0098` to `0`.
2. Normalize the name: lowercase, remove کافه/رستوران/cafe/café/restaurant, unify ی/ي and ک/ك, remove ZWNJ and punctuation, trim.
3. Search Joolio by normalized phone first, then by name in the same city. Any match → **skip** (no new lead, no overwrite; a note on the existing lead is fine). Also drop names that are *similar* to an existing Joolio contact.
4. Create a lead only with no phone and no name match. Include source + `link`, category, address, rating.
5. Rows with no phone go to manual review; never create leads from them.

## No-phone flow (manual)
Drop names similar to existing Joolio contacts → find the owner mobile via Instagram or Google Maps (gmaps-gilan-leads) → re-run the Joolio phone dedupe → send one Bale message only. Until a mobile is found, the row stays in manual review.

## Notes
- SnappFood never exposes vendor phones, so every row goes through the no-phone flow.
- The field names in the response may change. If you get 0 rows from an Iranian IP, inspect `data.finalResult[].data`.
- Smoke test (2026-10-28) from the box: 403 geo-block, 0 rows. Not yet verified from an Iranian IP.
