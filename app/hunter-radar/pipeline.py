"""Hunter radar pipeline helpers (stdlib only). No network writes, no message sending."""
import csv, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TOOLS = os.path.join(ROOT, 'tools')
FA = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
EXC = re.compile(r"هایپر|سوپرمارکت|سوپر مارکت|فروشگاه|بقالی|خواربار|hypermarket|supermarket|grocery", re.I)
BBOX = dict(lat_min=36.5, lat_max=38.5, lon_min=48.5, lon_max=50.6)  # same as merge.py
RASHT = (37.2808, 49.5832)

SOURCES = [
    dict(id='gmaps', label='گوگل مپس', color='#34A853'),
    dict(id='balad', label='بلد', color='#004991'),
    dict(id='neshan', label='نشان', color='#910D6A'),
    dict(id='snappfood', label='اسنپ‌فود', color='#FF5A1F'),
    dict(id='divar', label='دیوار', color='#FCBF00'),
]


def source_command(sid, out, env=None):
    """Return (argv, skip_reason). skip_reason is a Persian string when the source can't run."""
    env = os.environ if env is None else env
    py = sys.executable
    if sid == 'gmaps':
        binp = os.path.join(TOOLS, 'google-maps-scraper', 'gmaps')
        if not os.path.exists(binp):
            return None, 'باینری gmaps موجود نیست (tools/google-maps-scraper/README.md)'
        q = out + '.queries.txt'
        with open(q, 'w', encoding='utf-8') as f:
            f.write('کافه رشت\nرستوران رشت\n')
        return [binp, '-input', q, '-results', out, '-exit-monitor', '3m', '-lang', 'fa', '-depth', '5'], None
    if sid == 'balad':
        return [py, os.path.join(TOOLS, 'balad-scraper', 'balad_scraper.py'), '--out', out], None
    if sid == 'neshan':
        if not env.get('NESHAN_API_KEY'):
            return None, 'متغیر NESHAN_API_KEY تنظیم نشده'
        return [py, os.path.join(TOOLS, 'neshan-scraper', 'neshan_scraper.py'), '--term', 'کافه', '--out', out], None
    if sid == 'snappfood':
        return [py, os.path.join(TOOLS, 'snappfood-scraper', 'snappfood_scraper.py'), '--query', 'کافه', '--out', out], None
    if sid == 'divar':
        return [py, os.path.join(TOOLS, 'divar-scraper', 'divar_scraper.py'),
                '--queries', 'استخدام کافه,استخدام رستوران,واگذاری کافه', '--out', out], None
    raise ValueError(sid)


def norm_phone(p):
    p = re.sub(r"\D", "", str(p or "").translate(FA))
    if p.startswith("0098"): p = p[4:]
    elif p.startswith("98"): p = p[2:]
    return ("0" + p.lstrip("0")) if p.strip("0") else ""


def norm_name(n):
    n = str(n or "").lower().replace("ي", "ی").replace("ك", "ک").replace("\u200c", "").translate(FA)
    n = re.sub(r"کافه|رستوران|café|cafe|restaurant", "", n)
    return re.sub(r"[\W_]+", "", n)


def is_mobile(p):
    return bool(re.fullmatch(r"09\d{9}", norm_phone(p)))


def mask_phone(p):
    d = norm_phone(p)
    if not d: return ''
    return d[:2] + '•' * max(len(d) - 4, 0) + d[-2:] if len(d) > 4 else '•' * len(d)


def in_gilan(lat, lon):
    try:
        la, lo = float(lat), float(lon)
    except (TypeError, ValueError):
        return True  # unknown location: keep, as merge.py does
    return BBOX['lat_min'] <= la <= BBOX['lat_max'] and BBOX['lon_min'] <= lo <= BBOX['lon_max']


def is_excluded(name, category):
    return bool(EXC.search(f"{name or ''} {category or ''}"))


def read_csv(path):
    if not path or not os.path.exists(path): return []
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def load_joolio(path):
    """READ-ONLY: a local Joolio contacts export CSV. Returns (phones, names)."""
    phones, names = set(), set()
    for r in read_csv(path):
        for k, v in r.items():
            if k and re.search(r'phone|mobile|tel|موبایل|تلفن', k, re.I) and norm_phone(v): phones.add(norm_phone(v))
            if k and re.search(r'name|نام', k, re.I) and norm_name(v): names.add(norm_name(v))
    return phones, names


BALE_TEMPLATE = ('سلام وقت بخیر، {name} عزیز 🌿\n'
                 'از تیم آرومین هستم؛ نرم‌افزار صندوق و منوی QR برای کافه و رستوران.\n'
                 'اگر مایل باشید یک دمو کوتاه رایگان هماهنگ کنیم.')


def run_pipeline(raw_rows, merged_rows, joolio_path=None):
    """Compute the 4 pipeline steps from real rows. Never sends anything."""
    s1 = [r for r in merged_rows if norm_phone(r.get('phone'))]
    s2 = [r for r in merged_rows if in_gilan(r.get('lat'), r.get('lon')) and not is_excluded(r.get('name'), r.get('category'))]
    jp = joolio_path if joolio_path is not None else os.environ.get('JOOLIO_EXPORT_CSV')
    joolio_ok = bool(jp and os.path.exists(jp))
    jphones, jnames = load_joolio(jp) if joolio_ok else (set(), set())
    s3 = [r for r in s2 if norm_phone(r.get('phone')) not in jphones and norm_name(r.get('name')) not in jnames] if joolio_ok else []
    queue = [dict(id=r.get('id') or '', name=r.get('name') or '', phone_masked=mask_phone(r.get('phone')),
                  text=BALE_TEMPLATE.format(name=r.get('name') or ''), status='preview')
             for r in s3 if is_mobile(r.get('phone'))]
    return dict(steps=[
        dict(id='phones', label='استخراج شماره', count=len(s1), total=len(merged_rows),
             note=f"{sum(1 for r in s1 if is_mobile(r.get('phone')))} موبایل"),
        dict(id='gilan', label='فیلتر گیلان + حذف هایپر', count=len(s2), total=len(raw_rows) or len(merged_rows), note=''),
        dict(id='joolio', label='حذف تکراری با Joolio (فقط خواندنی)', count=len(s3) if joolio_ok else None,
             total=len(s2), note='' if joolio_ok else 'خروجی Joolio تنظیم نشده (JOOLIO_EXPORT_CSV)'),
        dict(id='bale', label='صف پیام بله (فقط پیش‌نمایش)', count=len(queue), total=None, note='ارسال خودکار غیرفعال است'),
    ], queue=queue, joolio_configured=joolio_ok)


def project(lat, lon, w=1000, h=700, bbox=(37.13, 37.43, 49.36, 49.81)):
    """Equirectangular projection of lat/lon into SVG viewBox coordinates."""
    la0, la1, lo0, lo1 = bbox
    return round((float(lon) - lo0) / (lo1 - lo0) * w, 1), round((la1 - float(lat)) / (la1 - la0) * h, 1)


def public_row(r, idx):
    srcs = [s for s in (r.get('source') or '').split(';') if s]
    return dict(key=str(idx), name=r.get('name') or '', category=r.get('category') or '', sources=srcs,
                phone_masked=mask_phone(r.get('phone')), has_phone=bool(norm_phone(r.get('phone'))),
                lat=r.get('lat') or None, lon=r.get('lon') or None, link=r.get('link') or '')
