---
name: balad-gilan-leads
description: Use when ARASH needs fresh cafe/restaurant leads in Rasht/Gilan from Balad (balad.ir) city/category pages, before creating any lead in Joolio.
---
# Balad leads for Gilan/Rasht (ARASH)

## Tool
`/workspace/tools/balad-scraper/balad_scraper.py` (Python stdlib). It reads the public `balad.ir/city-<city>/cat-<cat>` pages (the `__NEXT_DATA__` JSON the site renders). Free, no login. Default delay 2 s per page.

## Run
```
python3 /workspace/tools/balad-scraper/balad_scraper.py --city rasht \
  --cats coffee-shop,restaurant,fast-food-restaurant --max-pages 5 --out /workspace/arash/balad_<date>.csv
```
About 20 places per page. Other Gilan city slugs: bandar-anzali, lahijan, langarud, astara, talesh, fuman, rudsar (check the slug on balad.ir if a page comes back empty).

## CSV columns
`name, category, phone, address, lat, lon, rating, review_count, website, link, id, source`. Phones are usually present (`telephone` field).

## Filter (keep these rows only)
- **Gilan only:** address contains گیلان/رشت/another Gilan city, or lat/lon inside 36.5–38.5 N, 48.5–50.6 E.
- **Cafes and restaurants only:** cafe, coffee shop, restaurant, fast food, bakery-cafe and similar.
- **Drop** hypermarkets, supermarkets, grocery and chain stores (هایپر, سوپرمارکت, فروشگاه, بقالی, hypermarket, supermarket, grocery) and closed places.
Balad category pages also list supermarkets, so always apply the drop list.

## Dedupe against Joolio before creating a lead
1. Normalize the phone: Persian/Arabic digits to Latin, strip spaces/dashes, map `+98`/`0098` to `0`.
2. Normalize the name: lowercase, remove کافه/رستوران/cafe/café/restaurant, unify ی/ي and ک/ك, remove ZWNJ and punctuation, trim.
3. Search Joolio by normalized phone first, then by name in the same city. Any match → **skip** (no new lead, no overwrite; a note on the existing lead is fine). Also drop names that are *similar* to an existing Joolio contact.
4. Create a lead only with no phone and no name match. Include source + `link`, category, address, rating.
5. Rows with no phone go to manual review; never create leads from them.

## Notes
- Keep `--delay` ≥ 2 and don't hammer pages. If a page returns no `__NEXT_DATA__`, back off.
- Earlier work: `/workspace/arash/snappfood/build.py` (Balad + Joolio fuzzy match), `/workspace/arash/pass*/balad.py`.
- Smoke test (2026-10-28): rasht / coffee-shop, 1 page → 20 rows, 16 with phones, about 5 s.
