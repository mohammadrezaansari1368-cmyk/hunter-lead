import csv, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pipeline as P, outreach as B, osmmap as M


class Qualify(unittest.TestCase):
    J = (set(['09120000000']), set(['zzz']))

    def test_purple_only_when_all_pass(self):
        ok = dict(name='A', phone='09121234567', lat='37.27', lon='49.58')
        self.assertTrue(P.qualifies(ok, self.J, True))
        self.assertFalse(P.qualifies(dict(ok, phone=''), self.J, True))
        self.assertFalse(P.qualifies(dict(ok, lat='35.7', lon='51.4'), self.J, True))
        self.assertFalse(P.qualifies(dict(ok, name='سوپرمارکت A'), self.J, True))
        self.assertFalse(P.qualifies(dict(ok, phone='09120000000'), self.J, True))
        self.assertFalse(P.qualifies(ok, (set(), set()), False), 'no Joolio check -> not qualified')


class Bale(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        open(os.path.join(self.d, 'bale_blacklist.txt'), 'w').write('09121111111\n# comment\n')
        with open(os.path.join(self.d, 'bale_contacts_log.csv'), 'w', newline='') as f:
            csv.writer(f).writerows([['phone', 'sent_at'], ['09122222222', '2026-10-01']])
        self.o = B.Outbox(self.d, daily_cap=2, delay=(30, 90), seed=1)
        self.q = [dict(phone=p, name=n, text='t') for p, n in
                  [('09121111111', 'black'), ('09122222222', 'logged'), ('09123333333', 'a'), ('09123333333', 'dup'),
                   ('09124444444', 'b'), ('09125555555', 'c')]]

    def test_defaults_disabled_dry_run(self):
        self.assertFalse(self.o.enabled); self.assertFalse(self.o.live)

    def test_plan_rules(self):
        plan = self.o.plan(self.q)
        st = {(p['name'], p['status']) for p in plan}
        self.assertIn(('black', 'skip_blacklist'), st)
        self.assertIn(('logged', 'skip_already_contacted'), st)
        self.assertIn(('dup', 'skip_duplicate'), st)
        drafts = [p for p in plan if p['status'] == 'draft']
        self.assertEqual(len(drafts), 2)
        self.assertIn(('c', 'skip_daily_cap'), st)
        self.assertTrue(all(30 <= p['delay_s'] <= 90 for p in drafts))

    def test_live_cannot_be_enabled_and_send_refuses(self):
        with self.assertRaises(PermissionError): self.o.set_live(True)
        with self.assertRaises(PermissionError): self.o.send_one('bale', self.q[2])

    def test_dry_run_never_writes_contacts_log_and_stop_works(self):
        log = os.path.join(self.d, 'bale_contacts_log.csv'); before = open(log).read()
        self.o.enabled = True
        r = self.o.dry_run(self.q, sleep=lambda s: None)
        self.assertEqual(r['drafted'], 2); self.assertEqual(open(log).read(), before)
        self.o.emergency_stop()
        self.assertEqual(self.o.dry_run(self.q, sleep=lambda s: None)['drafted'], 0)

    def test_shared_log_across_channels_and_per_channel_cap(self):
        with open(os.path.join(self.d, 'outreach_contacts_log.csv'), 'w', newline='') as f:
            csv.writer(f).writerows([['phone', 'channel', 'sent_at'], ['09123333333', 'whatsapp', '2026-01-01']])
        for ch in B.CHANNELS:
            st = {p['name']: p['status'] for p in self.o.plan(self.q, ch)}
            self.assertEqual(st['a'], 'skip_already_contacted', ch)
            self.assertEqual(st['logged'], 'skip_already_contacted', ch)
        o = B.Outbox(self.d, daily_cap=5, caps={'eitaa': 1})
        self.assertEqual(sum(p['status'] == 'draft' for p in o.plan(self.q, 'eitaa')), 1)
        self.assertEqual(sum(p['status'] == 'draft' for p in o.plan(self.q, 'telegram')), 2)

    def test_all_adapters_refuse_and_document(self):
        self.assertEqual(set(B.CHANNELS), {'bale', 'rubika', 'eitaa', 'telegram', 'whatsapp'})
        for ch, a in B.CHANNELS.items():
            self.assertTrue(a.requirements)
            with self.assertRaises(PermissionError): self.o.send_one(ch, self.q[2])
        self.assertIn('No official API', B.CHANNELS['whatsapp'].requirements)

    def test_dry_run_requires_module_enabled(self):
        self.assertEqual(self.o.dry_run(self.q, sleep=lambda s: None)['drafted'], 0)


class Map(unittest.TestCase):
    def test_parse_overpass(self):
        js = {'elements': [{'type': 'way', 'tags': {'highway': 'primary'}, 'geometry': [{'lat': 37.2, 'lon': 49.5}, {'lat': 37.3, 'lon': 49.6}]},
                           {'type': 'way', 'tags': {'highway': 'residential'}, 'geometry': [{'lat': 37.2, 'lon': 49.5}]}]}
        ways = M.parse_ways(js)
        self.assertEqual(len(ways), 1); self.assertEqual(ways[0]['k'], 'primary')

    def test_query_bbox(self):
        q = M.overpass_query((37.2, 49.5, 37.3, 49.6))
        self.assertIn('(37.2,49.5,37.3,49.6)', q); self.assertIn('highway', q)


if __name__ == '__main__':
    unittest.main()
