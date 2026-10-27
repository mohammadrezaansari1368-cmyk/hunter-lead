#!/usr/bin/env python3
"""SnappFood public vendors-list endpoint used by snappfood.ir web. GEO-BLOCKED outside Iran (403) -> run from an Iranian IP.
Usage: snappfood_scraper.py --lat 37.2808 --lon 49.5832 --query کافه --pages 2 --out out.csv  (no phones exposed)"""
import argparse,csv,json,time,urllib.parse,urllib.request
ap=argparse.ArgumentParser();ap.add_argument('--lat',type=float,default=37.2808);ap.add_argument('--lon',type=float,default=49.5832)
ap.add_argument('--query',default='');ap.add_argument('--pages',type=int,default=1);ap.add_argument('--delay',type=float,default=2);ap.add_argument('--out',required=True);a=ap.parse_args()
rows={}
for p in range(a.pages):
    q=dict(lat=a.lat,long=a.lon,page=p,page_size=20,superType='[1]',optionalClient='WEBSITE',client='WEBSITE',deviceType='WEBSITE',appVersion='8.1.1',locale='fa',
           filters='{"filters":null,"sortings":null}',query=a.query)
    url='https://snappfood.ir/mobile/v3/restaurant/vendors-list?'+urllib.parse.urlencode(q)
    try: d=json.loads(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read())
    except Exception as e: raise SystemExit(f'blocked/failed: {e} (snappfood geo-blocks non-Iran IPs)')
    fl=(d.get('data') or {}).get('finalResult') or []
    for x in fl:
        v=x.get('data') or {}
        if not v.get('code'):continue
        rows[v['code']]=dict(name=v.get('title'),category=v.get('description') or v.get('vendorTypeTitle'),phone='',address=v.get('address'),
          lat=v.get('lat'),lon=v.get('lon'),rating=v.get('rating'),review_count=v.get('commentCount'),link=f"https://snappfood.ir/restaurant/menu/{v['code']}",id=v['code'],source='snappfood')
    if not fl:break
    time.sleep(a.delay)
f=['name','category','phone','address','lat','lon','rating','review_count','link','id','source']
w=csv.DictWriter(open(a.out,'w',newline='',encoding='utf-8-sig'),fieldnames=f);w.writeheader();w.writerows(rows.values());print(len(rows),'rows ->',a.out)
