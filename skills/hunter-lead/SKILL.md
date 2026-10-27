---
name: hunter-lead
description: Use when ARASH wants one combined, deduped list of Rasht/Gilan cafe/restaurant leads from all sources (Google Maps, Balad, Neshan, SnappFood, Divar), before creating any lead in Joolio.
---
# Hunter lead

## Steps
1. Run each source skill and save the CSVs to `/workspace/arash/hunt_<date>/`:
   - `gmaps-gilan-leads` → gmaps.csv (has phones)
   - `balad-gilan-leads` → balad.csv (has phones)
   - `neshan-gilan-leads` → neshan.csv (needs NESHAN_API_KEY, no phones)
   - `snappfood-gilan-leads` → snappfood.csv (needs an Iranian IP, no phones)
   - `divar-gilan-leads` → divar.csv (no phones, signals only)
   If a source is blocked, skip it and say so in the report.
2. Merge, filter and cross-source dedupe:
   ```
   python3 /workspace/tools/hunter-lead/merge.py --out /workspace/arash/hunt_<date>/merged.csv /workspace/arash/hunt_<date>/*.csv
   ```
   This maps Google Maps columns (title, latitude…), keeps rows inside the Gilan bbox, drops hyper/supermarkets, and merges rows by normalized phone and then by normalized name. The `source` column lists every source that matched, e.g. `balad;gmaps`. Empty fields get filled from the duplicate rows.
3. Do **one** Joolio dedupe on merged.csv: phone first, then name in the same city. Also drop names similar to existing contacts. Use the same rules as in the source skills.
4. Final list: `final.csv` (rows with a phone and no Joolio match) for lead creation, and `manual_review.csv` (no phone) for the Instagram/Google Maps mobile lookup, then one Bale message.

## Notes
- Smoke test (2026-10-28): gmaps_test + Balad + Divar → 72 merged rows, 27 with phones.
