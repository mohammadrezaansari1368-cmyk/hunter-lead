import csv, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pipeline as P
import server as S


class T(unittest.TestCase):
    def test_phone(self):
        self.assertEqual(P.norm_phone('+98 912 ۱۲۳ 4567'), '09121234567')
        self.assertTrue(P.is_mobile('00989121234567'))
        self.assertFalse(P.is_mobile('01333334444'))
        self.assertEqual(P.mask_phone('09121234567'), '09•••••••67')
        self.assertEqual(P.mask_phone(''), '')

    def test_filters(self):
        self.assertTrue(P.is_excluded('هایپر استار', ''))
        self.assertFalse(P.is_excluded('کافه نارنج', 'coffee-shop'))
        self.assertTrue(P.in_gilan(37.28, 49.58))
        self.assertFalse(P.in_gilan(35.7, 51.4))

    def test_pipeline_without_joolio_has_no_queue(self):
        rows = [dict(name='A', phone='09121234567', lat='37.2', lon='49.5', source='balad')]
        out = P.run_pipeline(rows, rows, joolio_path='')
        self.assertFalse(out['joolio_configured'])
        self.assertEqual(out['queue'], [])

    def test_pipeline_with_joolio_dedupes_and_previews_only(self):
        rows = [dict(name='A', phone='09121234567', lat='37.2', lon='49.5', id='1'),
                dict(name='B', phone='09120000000', lat='37.2', lon='49.5', id='2'),
                dict(name='C', phone='01333334444', lat='37.2', lon='49.5', id='3'),
                dict(name='هایپر X', phone='09125555555', lat='37.2', lon='49.5', id='4')]
        with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False, encoding='utf-8') as f:
            csv.writer(f).writerows([['name', 'mobile'], ['zzz', '0912 000 0000']])
        out = P.run_pipeline(rows, rows, joolio_path=f.name)
        self.assertEqual([q['name'] for q in out['queue']], ['A'])
        self.assertTrue(all(q['status'] == 'preview' for q in out['queue']))
        self.assertNotIn('1234567', out['queue'][0]['phone_masked'])

    def test_source_skips(self):
        argv, why = P.source_command('neshan', '/tmp/x.csv', env={})
        self.assertIsNone(argv); self.assertIn('NESHAN_API_KEY', why)
        argv, why = P.source_command('neshan', '/tmp/x.csv', env={'NESHAN_API_KEY': 'secret'})
        self.assertNotIn('secret', ' '.join(argv))

    def test_project(self):
        x, y = P.project(37.2808, 49.5832)
        self.assertTrue(0 < x < 1000 and 0 < y < 700)

    def test_server_redacts_secret(self):
        os.environ['NESHAN_API_KEY'] = 'service.SECRET123'
        self.assertNotIn('SECRET123', S.redact('error key service.SECRET123 bad'))

    def test_empty_state(self):
        d = tempfile.mkdtemp()
        self.assertEqual(S.load_latest(d), ([], [], None))


if __name__ == '__main__':
    unittest.main()
