#!/usr/bin/env python3
"""Polite Balad category fetcher (no key/login). Tested 2026-10-19.
Usage: python3 balad_fetch.py --city rasht --cat coffee-shop --pages 2 --out out.csv [--contacts contacts.csv]
"""
import argparse, csv, json, random, re, sys, time, urllib.parse, urllib.request
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
HDR = {"User-Agent": UA, "accept": "application/json, text/plain, */*", "platform": "web", "referer": "https://balad.ir/"}
EXCLUDE = re.compile(r"هایپر|سوپرمارکت|سوپر مارکت|فروشگاه زنجیره|افق کوروش|شهروند|رفاه|اتکا|هایپراستار|جانبو|کوروش")
FA = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

def get(url):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def norm_phone(p):
    p = re.sub(r"\D", "", (p or "").translate(FA))
    if p.startswith("98"): p = "0" + p[2:]
    return p

def norm_name(n):
    n = (n or "").replace("ي", "ی").replace("ك", "ک").replace("\u200c", " ")
    return re.sub(r"\s+", " ", re.sub(r"(کافه|رستوران|فست ?فود|رشت)", "", n)).strip()

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--city", default="rasht"); a.add_argument("--cat", default="coffee-shop")
    a.add_argument("--pages", type=int, default=1); a.add_argument("--out", default="balad_leads.csv")
    a.add_argument("--contacts", help="CSV with phone/name columns to dedup against")
    o = a.parse_args()
    seen_p, seen_n = set(), set()
    if o.contacts:
        for row in csv.DictReader(open(o.contacts, encoding="utf-8-sig")):
            for k, v in row.items():
                if k and re.search(r"phone|tel|mobile|شماره|تلفن", k, re.I) and v: seen_p.add(norm_phone(v)[-10:])
                if k and re.search(r"name|نام", k, re.I) and v: seen_n.add(norm_name(v))
    rows = []
    for page in range(1, o.pages + 1):
        q = urllib.parse.urlencode({"region": f"city-{o.city}", "name": o.cat, "page": page})
        lst = get(f"https://search.raah.ir/v4/placeslist/cat/?{q}")
        toks = lst.get("items", [])
        if not toks: break
        time.sleep(random.uniform(2, 4))
        det = get("https://poi.raah.ir/web/v4/preview-bulk/" + ",".join(toks)).get("items", [])
        for it in det:
            name = it.get("name") or ""; cat = it.get("category") or ""
            if EXCLUDE.search(name + " " + cat): continue
            ph = norm_phone(it.get("telephone"))
            if ph and ph[-10:] in seen_p: continue
            if norm_name(name) in seen_n: continue
            rc = (it.get("rating") or {}).get("count") or 0
            sig = []
            if rc == 0: sig.append("no_reviews")
            elif rc <= 5: sig.append("few_reviews")
            if not it.get("images") and not it.get("image"): sig.append("no_photos")
            if ph.startswith("09"): sig.append("mobile")
            score = (2 if ph else -5) + (2 if 0 < rc <= 5 else 1 if rc == 0 else 0)
            rows.append({"name": name, "category": cat, "phone": ph, "address": it.get("address") or "",
                         "city": o.city, "source": "balad", "map_url": f"https://balad.ir/p/{it.get('token')}",
                         "review_count": rc, "signals": ";".join(sig), "score": score})
        print(f"page {page}: {len(det)} places, total kept {len(rows)} (pageCount={lst.get('page_count') or lst.get('pageCount')})", file=sys.stderr)
        time.sleep(random.uniform(3, 6))
    with open(o.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["name","category","phone","address","city","source","map_url","review_count","signals","score"])
        w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} rows -> {o.out}", file=sys.stderr)

if __name__ == "__main__":
    main()
