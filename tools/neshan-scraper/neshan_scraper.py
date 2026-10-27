#!/usr/bin/env python3
"""Neshan official Search API (free key from https://platform.neshan.org, service key with Search enabled). export NESHAN_API_KEY=service.xxx
Usage: neshan_scraper.py --term کافه --lat 37.2808 --lon 49.5832 --out out.csv  (max ~30 results/term; no phones)"""
import argparse,csv,hashlib,json,os,urllib.parse,urllib.request
ap=argparse.ArgumentParser();ap.add_argument('--term',required=True);ap.add_argument('--lat',type=float,default=37.2808);ap.add_argument('--lon',type=float,default=49.5832);ap.add_argument('--out',required=True);a=ap.parse_args()
k=os.environ.get('NESHAN_API_KEY') or exit('set NESHAN_API_KEY (free at platform.neshan.org)')
url='https://api.neshan.org/v1/search?'+urllib.parse.urlencode(dict(term=a.term,lat=a.lat,lng=a.lon))
d=json.loads(urllib.request.urlopen(urllib.request.Request(url,headers={'Api-Key':k}),timeout=30).read())
rows=[]
for x in d.get('items') or []:
    loc=x.get('location') or {};lat,lon=loc.get('y'),loc.get('x')
    rows.append(dict(name=x.get('title'),category=x.get('category'),type=x.get('type'),phone='',address=x.get('address') or x.get('region'),lat=lat,lon=lon,rating='',
      link=f'https://neshan.org/maps/@{lat},{lon},18z',id=hashlib.md5(f"{x.get('title')}{lat}{lon}".encode()).hexdigest()[:12],source='neshan'))
f=['name','category','type','phone','address','lat','lon','rating','link','id','source']
w=csv.DictWriter(open(a.out,'w',newline='',encoding='utf-8-sig'),fieldnames=f);w.writeheader();w.writerows(rows);print(len(rows),'rows ->',a.out)
