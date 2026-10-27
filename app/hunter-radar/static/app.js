'use strict';
const $ = s => document.querySelector(s), NS = 'http://www.w3.org/2000/svg';
// Rasht-area bbox; keep in sync with pipeline.project
const BBOX = [37.13, 37.43, 49.36, 49.81], W = 1000, H = 700, RASHT = [37.2808, 49.5832];
const proj = (lat, lon) => [(lon - BBOX[2]) / (BBOX[3] - BBOX[2]) * W, (BBOX[1] - lat) / (BBOX[1] - BBOX[0]) * H];
const el = (t, a = {}, p) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); p && p.appendChild(e); return e; };
const h = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let SRC = [], COLORS = {}, sel = null;

// Schematic offline SVG map (no tiles, works when OSM is blocked). Coarse outline; not survey-accurate.
function drawGeo() {
  const g = $('#geo');
  el('rect', {x: 0, y: 0, width: W, height: H, class: 'sea'}, g);
  // No guessed coastline: grid + compass only. Caspian lies to the north of Rasht.
  for (let i = 1; i < 10; i++) { el('line', {x1: i * 100, y1: 0, x2: i * 100, y2: H, class: 'ring'}, g); if (i < 7) el('line', {x1: 0, y1: i * 100, x2: W, y2: i * 100, class: 'ring'}, g); }
  const n = el('text', {class: 'lbl', x: W / 2, y: 24, 'text-anchor': 'middle'}, g); n.textContent = '▲ شمال (دریای خزر)';
  const sc = el('text', {class: 'lbl', x: 20, y: H - 14}, g); sc.textContent = 'هر خانه ≈ ۴ کیلومتر · نقشه شماتیک آفلاین';
  const [cx, cy] = proj(...RASHT);
  el('circle', {cx, cy, r: 5, class: 'city'}, g);
  const r = el('text', {class: 'lbl', x: cx + 8, y: cy - 8}, g); r.textContent = 'رشت';
  el('circle', {cx, cy, r: 340, fill: 'url(#glow)'}, $('#rings'));
  for (const rr of [80, 160, 240, 320]) el('circle', {cx, cy, r: rr, class: 'ring'}, $('#rings'));
  $('#beamPath').setAttribute('d', `M${cx},${cy} L${cx + 420},${cy} A420,420 0 0,0 ${cx + 420 * Math.cos(-0.6)},${cy + 420 * Math.sin(-0.6)} Z`);
  const sw = $('#sweep'); sw.style.setProperty('--cx', cx + 'px'); sw.style.setProperty('--cy', cy + 'px');
}

async function status() {
  const s = await (await fetch('/api/status')).json();
  SRC = s.sources; SRC.forEach(x => COLORS[x.id] = x.color);
  $('#legend').innerHTML = SRC.map(x => `<li><span class="sw" style="background:${x.color}"></span>${h(x.label)}</li>`).join('');
  $('#status').innerHTML = [
    [s.neshan_key, s.neshan_key ? 'کلید نشان: تنظیم شده' : 'کلید نشان: تنظیم نشده'],
    [s.snappfood.ok, 'اسنپ‌فود: ' + s.snappfood.msg],
    [s.joolio, s.joolio ? 'Joolio: خروجی فقط‌خواندنی' : 'Joolio: تنظیم نشده'],
  ].map(([ok, t]) => `<span class="pill ${ok ? 'ok' : 'bad'}">${h(t)}</span>`).join('');
}

const STL = {idle: 'آماده', queued: 'در صف', running: 'در حال اجرا…', done: 'تمام', failed: 'خطا', skipped: 'رد شد'};
async function progress() {
  const p = await (await fetch('/api/progress')).json();
  $('#progress').innerHTML = SRC.map(x => { const s = p.sources[x.id];
    return `<li title="${h(s.msg)}"><span class="sw" style="background:${x.color}"></span>${h(x.label)}<span class="st ${s.state}">${STL[s.state]}${s.rows != null ? ' · ' + s.rows : ''}</span></li>`; }).join('')
    + (p.merge ? `<li class="muted">ادغام: ${h(p.merge)}</li>` : '');
  $('#scan').disabled = p.running;
  return p.running;
}

async function leads() {
  const d = await (await fetch('/api/leads')).json();
  const dots = $('#dots'); dots.innerHTML = '';
  $('#empty').hidden = d.leads.length > 0;
  $('#count').textContent = d.leads.length ? `(${d.leads.length})` : '';
  for (const r of d.leads) if (r.x != null) {
    const c = el('circle', {cx: r.x, cy: r.y, r: 6, class: 'dot', fill: COLORS[r.sources[0]] || '#fff'}, dots);
    c.dataset.key = r.key; c.onclick = () => select(r.key);
    el('title', {}, c).textContent = r.name;
  }
  $('#list').innerHTML = d.leads.length ? d.leads.map(r => `<div class="card" id="c${r.key}">
    <div class="n">${h(r.name)}</div><div class="m">${h(r.category) || '—'}</div>
    <div>${r.sources.map(s => `<span class="tag" style="background:${COLORS[s] || '#555'}">${h((SRC.find(x => x.id == s) || {label: s}).label)}</span>`).join('')}</div>
    <div>📞 ${r.has_phone ? `<span class="ph" id="p${r.key}">${h(r.phone_masked)}</span> <button class="rv" data-k="${r.key}">نمایش</button>` : '<span class="muted">بدون شماره</span>'}</div>
  </div>`).join('') : '<p class="muted">داده‌ای وجود ندارد.</p>';
  document.querySelectorAll('.rv').forEach(b => b.onclick = async () => {
    const j = await (await fetch('/api/reveal/' + b.dataset.k)).json(); $('#p' + b.dataset.k).textContent = j.phone; b.remove(); });
  $('#stepper').innerHTML = d.pipeline.steps.map((s, i) => `<li>${i + 1}. ${h(s.label)} — <b>${s.count ?? '—'}</b>${s.total != null ? ' از ' + s.total : ''}${s.note ? `<small>${h(s.note)}</small>` : ''}</li>`).join('');
  $('#queue').innerHTML = d.pipeline.queue.length ? d.pipeline.queue.map(q => `<div class="card msg"><b>${h(q.name)}</b> <span class="ph">${h(q.phone_masked)}</span>\n${h(q.text)}</div>`).join('')
    : '<p class="muted">صف خالی است.</p>';
}

function select(k) {
  document.querySelectorAll('.card.sel').forEach(c => c.classList.remove('sel'));
  const c = $('#c' + k); if (c) { c.classList.add('sel'); c.scrollIntoView({block: 'nearest', behavior: 'smooth'}); }
}

$('#scan').onclick = async () => {
  await fetch('/api/scan', {method: 'POST'});
  const tick = async () => { if (await progress()) setTimeout(tick, 1500); else leads(); };
  tick();
};

(async () => { drawGeo(); await status(); await progress(); await leads(); })();
