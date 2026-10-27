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

## v2 — JARVIS HUD, city vector map, multi-channel outreach (dry-run)
- Type a city (e.g. `Rasht`) → geocoded via Nominatim, roads fetched from OSM Overpass (stdlib `urllib`, retries + mirror), cached in `data/maps/` (gitignored), drawn on `<canvas>` with a rotating radar sweep. No new dependencies; no tiles. Neshan has no simple public vector-roads API, so it isn't used for the map.
- Dots: neon blue = found; purple `#910D6A` = phone found AND inside Gilan AND not hyper/supermarket AND not in the Joolio export. Without `JOOLIO_EXPORT_CSV` nothing can be purple (the Joolio check can't be done).
- `outreach.py`: Bale, Rubika, Eitaa, Telegram, WhatsApp adapter **stubs** (every `send` raises). Disabled by default, DRY-RUN only, live-send toggle refused by server (403) for all channels.
  - shared blacklist `data/outreach_blacklist.txt` (+ legacy `bale_blacklist.txt`)
  - ONE shared contacts log `data/outreach_contacts_log.csv` (`phone,channel,sent_at`; + legacy `bale_contacts_log.csv`) — read-only here; a phone in it is never planned again on any channel
  - per-channel daily cap (`OUTREACH_DAILY_CAP`, default 20), random delay 45–180 s per message (shown, never waited), global emergency stop (needs server restart to clear)
  - dry runs append only to `data/outreach_dryrun_log.csv` (last 2 phone digits)
- What a real integration would need (NOT implemented; needs separate approval):
  - **Bale / Rubika**: official bot API + bot token; bots can only message users who started the bot (no cold messaging by phone).
  - **Eitaa**: Eitaayar token posts only to your own channels/groups; no API for messaging arbitrary users.
  - **Telegram**: Bot API has the same limit; messaging by phone needs a MTProto user account → against ToS for cold outreach, high ban risk.
  - **WhatsApp**: no official API for personal accounts; WhatsApp Business Cloud API needs Meta business verification, approved templates, and opt-in. Unofficial libraries risk a ban.
