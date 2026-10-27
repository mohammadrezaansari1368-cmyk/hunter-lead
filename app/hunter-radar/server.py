#!/usr/bin/env python3
"""رادار Hunter lead — local web server (stdlib only). Usage: python3 server.py [--port 8765]
Runs tools/ scrapers + merge.py on demand. Never sends Bale messages, never writes to Joolio."""
import argparse, glob, json, os, subprocess, sys, threading, time, urllib.request
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import pipeline as P, outreach as B, osmmap as M

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get('HUNTER_RADAR_DATA', os.path.join(HERE, 'data'))  # gitignored
STATE = dict(running=False, run=None, sources={s['id']: dict(state='idle', msg='', rows=None) for s in P.SOURCES}, merge=None)
LOCK = threading.Lock()
os.makedirs(DATA, exist_ok=True)
OUTBOX = B.Outbox(DATA, daily_cap=int(os.environ.get('OUTREACH_DAILY_CAP', '20')))
CHANNEL = dict(id='bale')


def joolio():
    jp = os.environ.get('JOOLIO_EXPORT_CSV'); ok = bool(jp and os.path.exists(jp))
    return (P.load_joolio(jp) if ok else (set(), set())), ok


def bale_queue(merged):
    j, ok = joolio()
    return [dict(name=r.get('name') or '', phone=r.get('phone'), text=P.BALE_TEMPLATE.format(name=r.get('name') or ''))
            for r in merged if P.qualifies(r, j, ok) and P.is_mobile(r.get('phone'))]


def bale_public(plan):
    return [dict(p, phone=P.mask_phone(p['phone'])) for p in plan]


def bale_state():
    ch = CHANNEL['id']
    return dict(enabled=OUTBOX.enabled, live=False, stopped=OUTBOX.stopped, channel=ch, daily_cap=OUTBOX.caps[ch], delay=OUTBOX.delay,
                channels=[dict(id=c.id, label=c.label, requirements=c.requirements, cap=OUTBOX.caps[c.id]) for c in B.CHANNELS.values()],
                mode='DRY-RUN', integration='none', plan=bale_public(OUTBOX.plan(bale_queue(load_latest()[1]), ch)))


def redact(s):
    k = os.environ.get('NESHAN_API_KEY')
    s = str(s)
    return s.replace(k, '***') if k else s


def snappfood_status(timeout=8):
    url = 'https://snappfood.ir/mobile/v3/restaurant/vendors-list?lat=37.2808&long=49.5832&page=0&page_size=1&client=WEBSITE&deviceType=WEBSITE&appVersion=8.1.1'
    try:
        urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=timeout)
        return dict(ok=True, msg='در دسترس (IP ایران)')
    except urllib.error.HTTPError as e:
        return dict(ok=False, msg=f'مسدود ({e.code}) — فقط با IP ایران کار می‌کند')
    except Exception as e:
        return dict(ok=False, msg='در دسترس نیست — فقط با IP ایران کار می‌کند')


def load_latest(data_dir=DATA):
    runs = sorted(glob.glob(os.path.join(data_dir, 'runs', '*', 'merged.csv')))
    if not runs: return [], [], None
    m = runs[-1]; d = os.path.dirname(m)
    raw = [r for f in glob.glob(os.path.join(d, '*.csv')) if not f.endswith('merged.csv') for r in P.read_csv(f)]
    return raw, P.read_csv(m), os.path.basename(d)


def scan():
    run = time.strftime('%Y%m%d-%H%M%S'); d = os.path.join(DATA, 'runs', run); os.makedirs(d, exist_ok=True)
    with LOCK:
        STATE.update(running=True, run=run, merge=None)
        for s in STATE['sources'].values(): s.update(state='queued', msg='', rows=None)
    outs = []
    for s in P.SOURCES:
        sid = s['id']; out = os.path.join(d, f'{sid}.csv'); st = STATE['sources'][sid]
        argv, why = P.source_command(sid, out)
        if why: st.update(state='skipped', msg=why); continue
        st.update(state='running')
        try:
            p = subprocess.run(argv, capture_output=True, text=True, timeout=600, cwd=d)
            if p.returncode == 0 and os.path.exists(out):
                st.update(state='done', rows=len(P.read_csv(out)), msg=redact(p.stdout.strip()[-200:]).replace(d + os.sep, '')); outs.append(out)
            else:
                st.update(state='failed', msg=redact((p.stderr or p.stdout).strip()[-300:]))
        except Exception as e:
            st.update(state='failed', msg=redact(e))
    if outs:
        p = subprocess.run([sys.executable, os.path.join(P.TOOLS, 'hunter-lead', 'merge.py'), '--out', os.path.join(d, 'merged.csv')] + outs,
                           capture_output=True, text=True)
        STATE['merge'] = redact((p.stdout or p.stderr).strip()).replace(d + os.sep, '')
    else:
        STATE['merge'] = 'هیچ منبعی داده برنگرداند'
    STATE['running'] = False


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=os.path.join(HERE, 'static'), **k)

    def log_message(self, *a): pass

    def js(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store'); self.send_header('Content-Length', len(b)); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/api/status':
            return self.js(dict(sources=P.SOURCES, neshan_key=bool(os.environ.get('NESHAN_API_KEY')),
                                snappfood=snappfood_status(), joolio=bool(os.environ.get('JOOLIO_EXPORT_CSV'))))
        if path == '/api/progress':
            return self.js(STATE)
        if path == '/api/leads':
            raw, merged, run = load_latest()
            j, ok = joolio()
            rows = [dict(P.public_row(r, i), qualified=P.qualifies(r, j, ok)) for i, r in enumerate(merged)]
            return self.js(dict(run=run, leads=rows, pipeline=P.run_pipeline(raw, merged)))
        if path == '/api/map':
            from urllib.parse import parse_qs, urlparse
            city = (parse_qs(urlparse(self.path).query).get('city') or ['Rasht'])[0][:60]
            try: return self.js(M.city_map(city, os.path.join(DATA, 'maps')))
            except Exception as e: return self.js(dict(error=redact(e)), 502)
        if path == '/api/bale':
            return self.js(bale_state())
        if path.startswith('/api/reveal/'):
            _, merged, _ = load_latest(); i = path.rsplit('/', 1)[1]
            if i.isdigit() and int(i) < len(merged): return self.js(dict(phone=P.norm_phone(merged[int(i)].get('phone'))))
            return self.js(dict(error='not found'), 404)
        return super().do_GET()

    def do_POST(self):
        if self.path == '/api/scan':
            if STATE['running']: return self.js(dict(error='در حال اسکن'), 409)
            threading.Thread(target=scan, daemon=True).start(); return self.js(dict(ok=True))
        n = int(self.headers.get('Content-Length') or 0); body = json.loads(self.rfile.read(n) or b'{}') if n else {}
        if self.path == '/api/bale/enable':
            if OUTBOX.stopped and body.get('on'): return self.js(dict(error='توقف اضطراری فعال است؛ سرور را ری‌استارت کنید'), 409)
            OUTBOX.enabled = bool(body.get('on')); return self.js(bale_state())
        if self.path == '/api/bale/live':
            if body.get('on'): return self.js(dict(error='ارسال واقعی غیرفعال است؛ هیچ اتصال پیام‌رسانی وجود ندارد', **bale_state()), 403)
            return self.js(bale_state())
        if self.path == '/api/bale/channel':
            if body.get('id') in B.CHANNELS: CHANNEL['id'] = body['id']
            return self.js(bale_state())
        if self.path == '/api/bale/dryrun':
            r = OUTBOX.dry_run(bale_queue(load_latest()[1]), CHANNEL['id']); r['plan'] = bale_public(r['plan']); return self.js(r)
        if self.path == '/api/bale/stop':
            OUTBOX.emergency_stop(); return self.js(bale_state())
        if self.path.startswith('/api/bale'):
            return self.js(dict(error='ارسال پیام بله غیرفعال است'), 403)
        self.js(dict(error='not found'), 404)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--port', type=int, default=8765); ap.add_argument('--host', default='127.0.0.1'); a = ap.parse_args()
    print(f'رادار Hunter lead → http://{a.host}:{a.port}')
    ThreadingHTTPServer((a.host, a.port), H).serve_forever()
