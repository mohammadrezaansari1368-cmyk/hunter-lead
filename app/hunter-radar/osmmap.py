"""City vector map from OpenStreetMap (Nominatim geocode + Overpass roads). Stdlib only, cached on disk."""
import json, os, time, urllib.parse, urllib.request

UA = {'User-Agent': 'hunter-radar/1.0 (local tool)'}
OVERPASS = ['https://overpass-api.de/api/interpreter', 'https://overpass.private.coffee/api/interpreter']
KEEP = ('motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'residential',
        'motorway_link', 'trunk_link', 'primary_link', 'secondary_link', 'tertiary_link', 'living_street')


def overpass_query(bbox):
    s, w, n, e = bbox
    return f'[out:json][timeout:90];way["highway"~"^({"|".join(KEEP)})$"]({s},{w},{n},{e});out geom;'


def parse_ways(js):
    out = []
    for el in js.get('elements', []):
        g = el.get('geometry') or []
        k = (el.get('tags') or {}).get('highway', '')
        if el.get('type') == 'way' and len(g) >= 2 and k in KEEP:
            out.append(dict(k=k, c=[[round(p['lat'], 5), round(p['lon'], 5)] for p in g]))
    return out


def _get(url, data=None, timeout=60):
    req = urllib.request.Request(url, data=data, headers=UA)
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def geocode(city):
    q = urllib.parse.urlencode(dict(q=f'{city}, Iran', format='json', limit=1, featuretype='city'))
    r = _get('https://nominatim.openstreetmap.org/search?' + q, timeout=30)
    if not r: raise LookupError(f'شهر «{city}» پیدا نشد')
    s, n, w, e = map(float, r[0]['boundingbox'])
    return dict(name=r[0].get('name', city), display=r[0].get('display_name', ''), center=[float(r[0]['lat']), float(r[0]['lon'])],
                bbox=[s, w, n, e])


def city_map(city, cache_dir, retries=3):
    os.makedirs(cache_dir, exist_ok=True)
    fn = os.path.join(cache_dir, ''.join(c for c in city.lower() if c.isalnum()) + '.json')
    if os.path.exists(fn): return json.load(open(fn, encoding='utf-8'))
    g = geocode(city)
    data = urllib.parse.urlencode(dict(data=overpass_query(g['bbox']))).encode()
    err = None
    for i in range(retries):
        for url in OVERPASS:
            try:
                g['ways'] = parse_ways(_get(url, data, timeout=120)); g['source'] = 'OpenStreetMap (Overpass) © OSM contributors'
                json.dump(g, open(fn, 'w', encoding='utf-8')); return g
            except Exception as e:
                err = e
        time.sleep(2 ** i * 3)
    raise ConnectionError(f'Overpass در دسترس نیست: {err}')
