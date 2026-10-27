---
name: neshan-gilan-leads
description: Use when ARASH needs cafe/restaurant leads in Rasht/Gilan from Neshan (neshan.org) via the official Neshan Search API, before creating any lead in Joolio.
---
# Neshan leads for Gilan/Rasht (ARASH)

## Tool
`/workspace/tools/neshan-scraper/neshan_scraper.py`. It calls the official `api.neshan.org/v1/search` endpoint and needs a **free** service API key from https://platform.neshan.org (sign up there and create a key with the Search service enabled), then `export NESHAN_API_KEY=service.xxx`. The neshan.org web app's own `pwa-api` returns obfuscated payloads, so don't scrape or decode it.

## Run
```
export NESHAN_API_KEY=service.xxxx
python3 neshan_scraper.py --term "کافه" --lat 37.2808 --lon 49.5832 --out neshan_cafe_<date>.csv
```
You get at most about 30 results per term around the point. Get wider coverage by changing the term (کافه, رستوران, فست فود, کافی شاپ) and moving lat/lon across Rasht and other Gilan towns.

## CSV columns
`name, category, type, phone (blank, the API has no phones), address, lat, lon, rating (blank), link, id, source`.

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
- The free tier has daily quotas, so space calls out by a second or more.
- Smoke test (2026-10-28): no key on the box, so the API returned HTTP 480 (invalid key) and 0 rows. Needs the user's free key.
