#!/usr/bin/env python3
"""Balad public city/category pages (Next.js __NEXT_DATA__). Usage:
  balad_scraper.py --city rasht --cats coffee-shop,restaurant,fast-food-restaurant --max-pages 2 --out out.csv"""
import argparse,csv,json,re,time,urllib.request
UA='Mozilla/5.0 (X11; Linux x86_64) Chrome/120'
def page(city,cat,p):
    url=f'https://balad.ir/city-{city}/cat-{cat}'+(f'?page={p}' if p>1 else '')
    h=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA}),timeout=30).read().decode('utf-8','ignore')
    m=re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',h,re.S)
    d=(json.loads(m.group(1))['props']['pageProps'].get('data') or {}) if m else {}
    return d.get('items') or [],d.get('pageCount',0)
ap=argparse.ArgumentParser();ap.add_argument('--city',default='rasht');ap.add_argument('--cats',default='coffee-shop,restaurant,fast-food-restaurant')
ap.add_argument('--max-pages',type=int,default=1);ap.add_argument('--delay',type=float,default=2);ap.add_argument('--out',required=True);a=ap.parse_args()
rows={}
for cat in a.cats.split(','):
    p=1
    while p<=a.max_pages:
        it,pc=page(a.city,cat,p)
        for x in it:
            lon,lat=(x.get('geometry') or {}).get('coordinates',[None,None]);r=x.get('rating') or {}
            rows[x['token']]=dict(name=x.get('name'),category=x.get('category'),phone=x.get('telephone') or '',address=x.get('address'),lat=lat,lon=lon,
              rating=r.get('score'),review_count=r.get('count'),website=x.get('website') or '',link=f"https://balad.ir/p/{x['token']}",id=x['token'],source='balad')
        if p>=pc or not it:break
        p+=1;time.sleep(a.delay)
    time.sleep(a.delay)
f=['name','category','phone','address','lat','lon','rating','review_count','website','link','id','source']
w=csv.DictWriter(open(a.out,'w',newline='',encoding='utf-8-sig'),fieldnames=f);w.writeheader();w.writerows(rows.values())
print(len(rows),'rows,',sum(1 for r in rows.values() if r['phone']),'with phone ->',a.out)
