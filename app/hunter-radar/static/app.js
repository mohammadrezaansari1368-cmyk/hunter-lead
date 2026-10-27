'use strict';
const $ = s => document.querySelector(s);
const h = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const J = async (u, o) => (await fetch(u, o)).json();
const post = (u, b) => J(u, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(b || {})});
const BLUE = '#7ff3ff', PURPLE = '#910D6A';
let SRC = [], MAP = null, LEADS = [], sel = null, angle = 0;
const cv = $('#radar'), ctx = cv.getContext('2d');
let view = null, roadLayer = null;

// ---- projection (Web-Mercator-ish local equirectangular with cos(lat) correction) ----
function fit() {
  const r = cv.getBoundingClientRect(), dpr = devicePixelRatio || 1;
  cv.width = r.width * dpr; cv.height = r.height * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  if (!MAP) return (view = null);
  const [s, w, n, e] = MAP.bbox, k = Math.cos((s + n) / 2 * Math.PI / 180);
  const sc = Math.min(r.width / ((e - w) * k), r.height / (n - s)) * 0.95;
  view = {w: r.width, h: r.height, sc, k, cx: (w + e) / 2, cy: (s + n) / 2};
  roadLayer = null;
}
const P = (lat, lon) => [view.w / 2 + (lon - view.cx) * view.k * view.sc, view.h / 2 - (lat - view.cy) * view.sc];

const W = {motorway: 2.4, trunk: 2.2, primary: 2, secondary: 1.6, tertiary: 1.2};
function drawRoads() {
  const off = document.createElement('canvas'); off.width = cv.width; off.height = cv.height;
  const c = off.getContext('2d'); c.setTransform(cv.width / view.w, 0, 0, cv.height / view.h, 0, 0);
  c.lineCap = 'round';
  for (const pass of [0, 1]) for (const way of MAP.ways) {
    const wd = W[way.k.replace('_link', '')] || 0.6;
    if (pass === 0 && wd < 1.2) continue;
    c.strokeStyle = pass ? `rgba(30,120,200,${wd > 1 ? .75 : .32})` : 'rgba(30,120,200,.15)';
    c.lineWidth = pass ? wd : wd * 4;
    c.beginPath(); way.c.forEach(([la, lo], i) => { const [x, y] = P(la, lo); i ? c.lineTo(x, y) : c.moveTo(x, y); }); c.stroke();
  }
  roadLayer = off;
}

function frame() {
  const r = cv.getBoundingClientRect();
  ctx.clearRect(0, 0, r.width, r.height);
  if (view) {
    if (!roadLayer) drawRoads();
    ctx.drawImage(roadLayer, 0, 0, r.width, r.height);
    const [cx, cy] = P(...MAP.center), R = Math.hypot(r.width, r.height) / 2;
    ctx.strokeStyle = 'rgba(42,212,255,.25)'; ctx.lineWidth = 1;
    for (let i = 1; i <= 4; i++) { ctx.beginPath(); ctx.arc(cx, cy, R * i / 4.5, 0, 7); ctx.stroke(); }
    ctx.beginPath(); ctx.moveTo(cx - R, cy); ctx.lineTo(cx + R, cy); ctx.moveTo(cx, cy - R); ctx.lineTo(cx, cy + R); ctx.stroke();
    // sweep
    const g = ctx.createConicGradient ? ctx.createConicGradient(angle - 0.9, cx, cy) : null;
    if (g) { g.addColorStop(0, 'rgba(42,212,255,0)'); g.addColorStop(0.14, 'rgba(42,212,255,.38)'); g.addColorStop(0.1401, 'rgba(42,212,255,0)'); g.addColorStop(1, 'rgba(42,212,255,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(cx, cy, R, 0, 7); ctx.fill(); }
    ctx.strokeStyle = '#bff4ff'; ctx.lineWidth = 2; ctx.shadowColor = BLUE; ctx.shadowBlur = 12;
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(angle) * R, cy + Math.sin(angle) * R); ctx.stroke(); ctx.shadowBlur = 0;
    // dots
    for (const d of LEADS) if (d.lat && d.lon) {
      const [x, y] = P(+d.lat, +d.lon); d._x = x; d._y = y;
      let a = Math.atan2(y - cy, x - cx) - angle; a = ((a % 6.283) + 6.283) % 6.283;
      const glow = 1 - Math.min(a, 6.283 - a) / 1.2, col = d.qualified ? PURPLE : BLUE;
      ctx.fillStyle = col; ctx.shadowColor = d.qualified ? '#ff4fd0' : BLUE; ctx.shadowBlur = 8 + Math.max(glow, 0) * 18;
      ctx.beginPath(); ctx.arc(x, y, d.key === sel ? 8 : 5.5, 0, 7); ctx.fill(); ctx.shadowBlur = 0; ctx.strokeStyle = '#fff'; ctx.lineWidth = 1; ctx.stroke();
      if (d.key === sel) { ctx.strokeStyle = '#FCBF00'; ctx.lineWidth = 2; ctx.stroke(); }
    }
    ctx.shadowBlur = 0;
    angle = (angle + 0.012) % 6.283;
  }
  requestAnimationFrame(frame);
}

cv.addEventListener('click', ev => {
  const r = cv.getBoundingClientRect(), x = ev.clientX - r.left, y = ev.clientY - r.top;
  let best = null, bd = 12;
  for (const d of LEADS) if (d._x != null) { const dd = Math.hypot(d._x - x, d._y - y); if (dd < bd) { bd = dd; best = d; } }
  if (best) select(best.key);
});

async function loadMap(city) {
  $('#cityName').textContent = city; $('#mapInfo').textContent = 'در حال دریافت نقشه از OSM…';
  const m = await J('/api/map?city=' + encodeURIComponent(city));
  if (m.error) { $('#mapInfo').textContent = 'خطای نقشه: ' + m.error; return; }
  MAP = m; $('#cityName').textContent = m.name;
  $('#mapInfo').textContent = `${m.ways.length.toLocaleString('fa')} مسیر · ${m.center.map(v => v.toFixed(3)).join(', ')}`;
  $('#mapsrc').textContent = 'نقشه: ' + m.source; fit();
}

async function status() {
  const s = await J('/api/status'); SRC = s.sources;
  $('#status').innerHTML = [[s.neshan_key, 'نشان: ' + (s.neshan_key ? 'کلید دارد' : 'بدون کلید')],
    [s.snappfood.ok, 'اسنپ‌فود: ' + s.snappfood.msg], [s.joolio, 'Joolio: ' + (s.joolio ? 'فقط‌خواندنی' : 'تنظیم نشده')]]
    .map(([ok, t]) => `<span class="pill ${ok ? 'ok' : ''}">${h(t)}</span>`).join('');
}

const STL = {idle: 'آماده', queued: 'در صف', running: 'در حال اجرا…', done: 'تمام', failed: 'خطا', skipped: 'رد شد'};
const PCT = {idle: 0, queued: 5, running: 50, done: 100, failed: 100, skipped: 100};
async function progress() {
  const p = await J('/api/progress');
  $('#progress').innerHTML = SRC.map(x => { const s = p.sources[x.id];
    return `<li title="${h(s.msg)}" style="display:block"><div style="display:flex;gap:8px;align-items:center"><span class="sw" style="background:${x.color};color:${x.color}"></span>${h(x.label)}<span class="st ${s.state}">${STL[s.state]}${s.rows != null ? ' · ' + s.rows : ''}</span></div><div class="bar"><i style="width:${PCT[s.state]}%"></i></div></li>`; }).join('');
  $('#merge').textContent = p.merge ? 'ادغام: ' + p.merge : '';
  $('#scan').disabled = p.running; return p.running;
}

async function leads() {
  const d = await J('/api/leads'); LEADS = d.leads;
  $('#empty').hidden = LEADS.length > 0;
  $('#count').textContent = LEADS.length ? `(${LEADS.length} · ${LEADS.filter(x => x.qualified).length} واجد شرایط)` : '';
  $('#list').innerHTML = LEADS.length ? LEADS.map(r => `<div class="card ${r.qualified ? 'q' : ''}" id="c${r.key}" data-k="${r.key}">
    <div class="n">${h(r.name)}</div><div class="m">${h(r.category) || '—'} · ${r.sources.map(s => h((SRC.find(x => x.id == s) || {label: s}).label)).join('، ')}</div>
    <div>📞 ${r.has_phone ? `<span class="ph" id="p${r.key}">${h(r.phone_masked)}</span> <button class="rv" data-k="${r.key}">نمایش</button>` : '<span class="muted">بدون شماره</span>'}</div></div>`).join('')
    : '<p class="muted">داده‌ای وجود ندارد.</p>';
  document.querySelectorAll('.card').forEach(c => c.onclick = () => select(c.dataset.k));
  document.querySelectorAll('.rv').forEach(b => b.onclick = async e => { e.stopPropagation();
    $('#p' + b.dataset.k).textContent = (await J('/api/reveal/' + b.dataset.k)).phone; b.remove(); });
  $('#stepper').innerHTML = d.pipeline.steps.map((s, i) => `<li>${i + 1}. ${h(s.label)} — <b>${s.count ?? '—'}</b>${s.total != null ? ' از ' + s.total : ''}${s.note ? `<small>${h(s.note)}</small>` : ''}</li>`).join('');
}

function select(k) {
  sel = k; document.querySelectorAll('.card.sel').forEach(c => c.classList.remove('sel'));
  const c = $('#c' + k); if (c) { c.classList.add('sel'); c.scrollIntoView({block: 'nearest', behavior: 'smooth'}); }
}

const BST = {draft: 'پیش‌نویس', skip_blacklist: 'لیست سیاه', skip_already_contacted: 'قبلاً پیام گرفته', skip_duplicate: 'تکراری', skip_daily_cap: 'سقف روزانه', skip_no_phone: 'بدون شماره'};
function renderBale(b, extra) {
  $('#baleOn').checked = b.enabled; $('#baleOn').disabled = b.stopped; $('#baleLive').checked = false;
  $('#dry').disabled = !b.enabled || b.stopped;
  const cur = b.channels.find(c => c.id === b.channel);
  $('#channels').innerHTML = b.channels.map(c => `<button class="chip ${c.id === b.channel ? 'on' : ''}" data-c="${c.id}" title="${h(c.requirements)}">${h(c.label)}</button>`).join('');
  document.querySelectorAll('.chip').forEach(x => x.onclick = async () => renderBale(await post('/api/bale/channel', {id: x.dataset.c})));
  $('#baleInfo').innerHTML = `کانال: <b>${h(cur.label)}</b> · حالت: <b>${b.mode}</b> · اتصال: هیچ · سقف روزانه ${b.daily_cap} · فاصله تصادفی ${b.delay[0]}–${b.delay[1]} ثانیه`
    + `<br><span title="${h(cur.requirements)}">پیش‌نیاز (مستند): ${h(cur.requirements)}</span>` + (b.stopped ? '<br><b style="color:#f88">توقف اضطراری فعال است</b>' : '') + (extra ? '<br>' + h(extra) : '');
  $('#queue').innerHTML = b.plan.length ? b.plan.map(p => `<div class="card msg"><b>${h(p.name)}</b> <span class="ph">${h(p.phone)}</span> · ${BST[p.status] || p.status}${p.delay_s ? ` · ⏱${p.delay_s}s` : ''}\n${p.status === 'draft' ? h(p.text) : ''}</div>`).join('')
    : '<p class="muted">صف خالی است (فقط سرنخ‌های بنفش با موبایل؛ هر نفر فقط یک بار در کل کانال‌ها).</p>';
}
const bale = async () => renderBale(await J('/api/bale'));
$('#baleOn').onchange = async e => { const r = await post('/api/bale/enable', {on: e.target.checked}); r.error ? (alert(r.error), bale()) : renderBale(r); };
$('#baleLive').onchange = async e => { const r = await post('/api/bale/live', {on: e.target.checked}); e.target.checked = false; renderBale(r.plan ? r : await J('/api/bale'), r.error); };
$('#dry').onclick = async () => { const r = await post('/api/bale/dryrun'); renderBale(await J('/api/bale'), `اجرای آزمایشی: ${r.drafted} پیش‌نویس — چیزی ارسال نشد`); };
$('#stop').onclick = async () => renderBale(await post('/api/bale/stop'), 'توقف اضطراری اعمال شد');

$('#scan').onclick = async () => { await post('/api/scan');
  const tick = async () => { if (await progress()) setTimeout(tick, 1500); else { leads(); bale(); } }; tick(); };
$('#cityForm').onsubmit = e => { e.preventDefault(); loadMap($('#city').value.trim() || 'Rasht'); };
addEventListener('resize', fit);
setInterval(() => { const d = new Date(); $('#time').textContent = d.toLocaleTimeString('fa-IR'); $('#date').textContent = d.toLocaleDateString('fa-IR', {weekday: 'long', day: 'numeric', month: 'long'}); }, 1000);

(async () => { requestAnimationFrame(frame); fit(); await status(); await progress(); await leads(); bale(); loadMap($('#city').value); })();
