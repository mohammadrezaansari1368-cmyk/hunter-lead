---
name: divar-gilan-leads
description: Use when ARASH needs Rasht/Gilan cafe/restaurant signals from Divar (hiring ads, business sale/rent, cafe equipment ads) as leads, before creating any lead in Joolio.
---
# Divar leads for Gilan/Rasht (ARASH)

This skill is only the scraping recipe. The teammate agent **Divar** owns Divar work beyond this.

## Tool
`/workspace/tools/divar-scraper/divar_scraper.py` (Python stdlib). It calls the public `api.divar.ir/v8/postlist/w/search` post list that divar.ir web uses. No login. 3 s delay per query.

## Run
```
python3 divar_scraper.py --city-id 12 --out divar_<date>.csv --queries \
 "استخدام کافه,استخدام رستوران,استخدام باریستا,استخدام فست فود,واگذاری کافه,واگذاری رستوران,اجاره رستوران,تجهیزات کافه,تجهیزات رستوران,دستگاه اسپرسو"
```
City id 12 is Rasht. Add `--category shop-restaurant` to keep only restaurant/shop jobs. The first page is about 20–25 posts per query.
- Hiring ads mean a new or growing cafe. Sale/rent ads mean a new owner is coming. Equipment buyers or sellers mean a café opening or upgrading.

## CSV columns
`name (ad title), category (the query), phone (always blank), address (city), detail (price/district/time), link, id (post token), source`.

## Filter (keep these rows only)
- **Gilan only:** address contains گیلان/رشت/another Gilan city, or lat/lon inside 36.5–38.5 N, 48.5–50.6 E.
- **Cafes and restaurants only:** cafe, coffee shop, restaurant, fast food, bakery-cafe and similar.
- **Drop** hypermarkets, supermarkets, grocery and chain stores (هایپر, سوپرمارکت, فروشگاه, بقالی, hypermarket, supermarket, grocery) and closed places.
Ad titles aren't business names. Open the ad to read the café's name or district, then match that against Joolio.

## Dedupe against Joolio before creating a lead
1. Normalize the phone: Persian/Arabic digits to Latin, strip spaces/dashes, map `+98`/`0098` to `0`.
2. Normalize the name: lowercase, remove کافه/رستوران/cafe/café/restaurant, unify ی/ي and ک/ك, remove ZWNJ and punctuation, trim.
3. Search Joolio by normalized phone first, then by name in the same city. Any match → **skip** (no new lead, no overwrite; a note on the existing lead is fine). Also drop names that are *similar* to an existing Joolio contact.
4. Create a lead only with no phone and no name match. Include source + `link`, category, address, rating.
5. Rows with no phone go to manual review; never create leads from them.

## Phone (manual)
Divar shows phones only after login. Don't log in to scrape and don't bypass it. Mark the phone as manual. Either contact through Divar chat (the Divar agent or a human does this) or find the business mobile via Instagram/Google Maps. Then drop names similar to Joolio contacts and send one Bale message.

## Notes
- Smoke test (2026-10-28): `استخدام کافه,واگذاری کافه`, Rasht → 40 posts, 0 phones, about 7 s.
