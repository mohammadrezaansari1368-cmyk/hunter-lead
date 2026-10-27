"""Multi-channel outreach — DRAFT / DRY-RUN ONLY. No account connections, no integrations, no network.

Channels: Bale, Rubika, Eitaa, Telegram, WhatsApp. Each has an adapter STUB whose send() always refuses.
Shared rules across ALL channels:
- shared blacklist: outreach_blacklist.txt (+ legacy bale_blacklist.txt)
- ONE shared contacts log: outreach_contacts_log.csv (+ legacy bale_contacts_log.csv), columns phone,channel,sent_at.
  A phone in it is never planned again on any channel (one message per person, ever). This app only READS it.
- per-channel daily cap, random delay per message, global emergency stop.
- module disabled by default; live send can't be enabled.
"""
import csv, os, random, re, time
from datetime import date

FA = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def norm(p):
    p = re.sub(r"\D", "", str(p or "").translate(FA))
    if p.startswith("0098"): p = p[4:]
    elif p.startswith("98"): p = p[2:]
    return ("0" + p.lstrip("0")) if p.strip("0") else ""


class Adapter:
    id = label = ''
    requirements = ''

    def send(self, phone, text):
        raise PermissionError(f'{self.label}: not integrated — draft/dry-run only.')


class Bale(Adapter):
    id, label = 'bale', 'بله'
    requirements = ('Official Bale Bot API (tapi.bale.ai) with a bot token from @botfather. Bots can only message users '
                    'who started the bot first; cold messaging a phone number is not possible via the bot API.')


class Rubika(Adapter):
    id, label = 'rubika', 'روبیکا'
    requirements = ('Rubika Bot API (botapi.rubika.ir) with a bot token; same limit — only users who started the bot. '
                    'Personal-account automation is unofficial and risks a ban.')


class Eitaa(Adapter):
    id, label = 'eitaa', 'ایتا'
    requirements = ('Eitaayar API (eitaayar.ir) token can post to the owner\'s channels/groups only; no official API to '
                    'message arbitrary users.')


class Telegram(Adapter):
    id, label = 'telegram', 'تلگرام'
    requirements = ('Telegram Bot API token (@BotFather): only users who started the bot. Messaging by phone needs a user '
                    'account via MTProto (api_id/api_hash) — against ToS for cold outreach, high ban risk. Filtered in Iran.')


class WhatsApp(Adapter):
    id, label = 'whatsapp', 'واتساپ'
    requirements = ('No official API for personal accounts. WhatsApp Business Platform (Cloud API) needs a Meta business '
                    'account, verified number and pre-approved templates, and opt-in. Unofficial libraries = ban risk. '
                    'Filtered in Iran.')


CHANNELS = {c.id: c() for c in (Bale, Rubika, Eitaa, Telegram, WhatsApp)}


class Outbox:
    def __init__(self, data_dir, daily_cap=20, delay=(45, 180), seed=None, caps=None):
        self.dir = data_dir
        self.enabled = False
        self.live = False
        self.stopped = False
        self.caps = {c: (caps or {}).get(c, daily_cap) for c in CHANNELS}
        self.delay = delay
        self.rng = random.Random(seed)

    def _files(self, *names):
        return [os.path.join(self.dir, n) for n in names if os.path.exists(os.path.join(self.dir, n))]

    def blacklist(self):
        out = set()
        for p in self._files('outreach_blacklist.txt', 'bale_blacklist.txt'):
            out |= {norm(l) for l in open(p, encoding='utf-8') if l.strip() and not l.lstrip().startswith('#')}
        return out - {''}

    def contacted(self):
        """(phones ever contacted on any channel, {channel: sent today})."""
        phones, today, t = set(), {c: 0 for c in CHANNELS}, date.today().isoformat()
        for p in self._files('outreach_contacts_log.csv', 'bale_contacts_log.csv'):
            legacy = p.endswith('bale_contacts_log.csv')
            for r in csv.DictReader(open(p, encoding='utf-8-sig')):
                phones.add(norm(r.get('phone')))
                ch = r.get('channel') or ('bale' if legacy else '')
                if ch in today and (r.get('sent_at') or '').startswith(t): today[ch] += 1
        return phones - {''}, today

    def set_live(self, on):
        if on: raise PermissionError('Live send is disabled: no messaging integration exists in this app.')

    def send_one(self, channel, item):
        return CHANNELS[channel].send(item.get('phone'), item.get('text'))

    def emergency_stop(self):
        self.stopped = True; self.enabled = False

    def plan(self, queue, channel='bale'):
        if channel not in CHANNELS: raise ValueError(channel)
        black = self.blacklist(); done, today = self.contacted()
        seen, out, left = set(), [], max(self.caps[channel] - today[channel], 0)
        for q in queue:
            ph = norm(q.get('phone'))
            item = dict(name=q.get('name', ''), phone=ph, text=q.get('text', ''), channel=channel, delay_s=None)
            if not ph: st = 'skip_no_phone'
            elif ph in black: st = 'skip_blacklist'
            elif ph in done: st = 'skip_already_contacted'
            elif ph in seen: st = 'skip_duplicate'
            elif left <= 0: st = 'skip_daily_cap'
            else: st = 'draft'; left -= 1; item['delay_s'] = self.rng.randint(*self.delay)
            if ph: seen.add(ph)
            item['status'] = st; out.append(item)
        return out

    def dry_run(self, queue, channel='bale', sleep=time.sleep):
        """Simulate only. Appends to outreach_dryrun_log.csv; never touches the contacts log; never sends."""
        if not self.enabled or self.stopped:
            return dict(drafted=0, reason='stopped' if self.stopped else 'module disabled', plan=[])
        plan = self.plan(queue, channel); n = 0
        with open(os.path.join(self.dir, 'outreach_dryrun_log.csv'), 'a', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            for p in plan:
                if self.stopped: break
                if p['status'] != 'draft': continue
                w.writerow([time.strftime('%Y-%m-%dT%H:%M:%S'), channel, p['phone'][-2:], p['delay_s'], 'DRY_RUN']); n += 1
                sleep(0)  # the real delay (p['delay_s']) is only shown, never waited, nothing is sent
        return dict(drafted=n, reason='dry-run', plan=plan)
