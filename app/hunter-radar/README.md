# رادار Hunter lead

Local, dependency-free (Python stdlib + vanilla JS/SVG) radar UI over the scripts in `tools/`.

```bash
cd app/hunter-radar
export NESHAN_API_KEY=...            # optional; never printed or returned by the API
export JOOLIO_EXPORT_CSV=/path/joolio_contacts.csv   # optional, READ-ONLY local export
python3 server.py --port 8765        # open http://127.0.0.1:8765
python3 -m unittest discover -s tests
```

- «شروع اسکن» runs each source script (gmaps binary if present, Balad, Neshan, SnappFood, Divar), then `tools/hunter-lead/merge.py`. Output goes to `app/hunter-radar/data/runs/<ts>/` (gitignored).
- Phones are masked; click «نمایش» per row.
- Pipeline: phone extraction → Gilan filter + hypermarket removal → Joolio dedupe (read-only CSV export; nothing is written to Joolio) → Bale queue **preview only**. `/api/bale*` always returns 403.
- SnappFood reachability is probed on load (geo-blocked outside Iran).
- Map is an offline schematic SVG (no tiles, works where OSM is blocked).
