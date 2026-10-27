---
name: gmaps-gilan-leads
description: Use when ARASH needs fresh cafe/restaurant leads in Rasht/Gilan from Google Maps (gosom/google-maps-scraper), before creating any lead in Joolio.
---
# Google Maps leads for Gilan/Rasht (ARASH)

## Tool
Binary: `/workspace/tools/google-maps-scraper/gmaps` (official release v1.18.1 linux-amd64; it downloads its own Playwright/Chromium the first time it runs). It costs nothing. Don't use the paid LeadsDB/AWS flags.

## Run
1. Put one query per line in a file, e.g. `/workspace/arash/queries.txt`:
   - Persian: `کافه رشت`, `رستوران رشت`, `کافه رستوران رشت`, `فست فود رشت`, `کافه انزلی`, `رستوران لاهیجان`, `کافه لنگرود`, `رستوران آستارا`, `کافه تالش`, `رستوران فومن`, `کافه رودسر`
   - English: `cafe Rasht`, `restaurant Rasht`, `coffee shop Rasht Gilan`, `restaurant Bandar Anzali`, `cafe Lahijan`
2. Run:
   ```
   cd /workspace/tools/google-maps-scraper
   ./gmaps -input /workspace/arash/queries.txt -results /workspace/arash/gmaps_<date>.csv \
     -depth 1 -c 2 -exit-on-inactivity 2m
   ```
   `-depth 1` returns about 15 places per query. Use `-depth 3` to `-depth 5` for more. Keep `-c` low so Google doesn't throttle the scrape. Add `-email` only if you need emails, because it visits each website and runs slower.

## CSV columns to use
`title`, `category`, `phone`, `address`, `complete_address`, `website`, `review_count`, `review_rating`, `latitude`, `longitude`, `link`, `place_id`, `status`, `emails`.

## Filter (keep these rows only)
- **Gilan only:** `address`/`complete_address` contains Gilan / گیلان / Rasht / رشت (or another Gilan city), or the lat/lon falls roughly inside 36.5–38.5 N, 48.5–50.6 E.
- **Cafes and restaurants only:** the category must be a cafe, coffee shop, restaurant, fast food, bakery-cafe, or similar.
- **Drop** hypermarkets, supermarkets, grocery stores, chain stores (هایپر, سوپرمارکت, فروشگاه, hypermarket, supermarket, grocery), and anything with `status` = permanently closed.

## Dedupe against Joolio before creating a lead
1. Normalize the phone: convert Persian/Arabic digits to Latin, strip spaces and dashes, and map `+98`/`0098` to `0` (for example `09xxxxxxxxx` or `013xxxxxxxx`).
2. Normalize the name: lowercase it, remove the words کافه/رستوران/cafe/café/restaurant, map ی/ي and ک/ك to one form, remove ZWNJ (zero-width non-joiner) characters and punctuation, and trim.
3. Search Joolio for the normalized phone first, then for the name in the same city. If either one matches, **skip the row**. Don't create a lead and don't overwrite the existing one. You may add a note on the existing lead.
4. Create a lead only when there is no match on either phone or name. Include the source (`Google Maps` + `link`), category, address, rating and review count.
5. Rows with no phone go to manual review; don't create leads from them.

## Notes
- Google can rate-limit large runs. If you see empty results or many failed jobs, lower `-c`, add a pause between batches, or use `-proxies`.
- Smoke test (2026-10-28): `کافه رشت`, depth 1 → 16 rows, 13 with phones, in about 20 s.
