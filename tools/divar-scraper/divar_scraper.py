#!/usr/bin/env python3
"""Divar public post-list API (same as divar.ir web). Phones need login -> phone always blank (manual).
Usage: divar_scraper.py --city-id 12 --queries "استخدام کافه,استخدام رستوران,تجهیزات کافه,واگذاری کافه,اجاره رستوران" --out out.csv
City ids: 12=Rasht. Category optional (e.g. shop-restaurant = jobs in shop/restaurant)."""
import argparse,csv,json,time,urllib.request
ap=argparse.ArgumentParser();ap.add_argument('--city-id',default='12');ap.add_argument('--queries',required=True);ap.add_argument('--category',default='')
ap.add_argument('--delay',type=float,default=3);ap.add_argument('--out',required=True);a=ap.parse_args()
rows={}
for q in a.queries.split(','):
    sd={'query':q.strip()}
    if a.category: sd['form_data']={'data':{'category':{'str':{'value':a.category}}}}
    req=urllib.request.Request('https://api.divar.ir/v8/postlist/w/search',data=json.dumps({'city_ids':[a.city_id],'search_data':sd}).encode(),
        headers={'User-Agent':'Mozilla/5.0','Content-Type':'application/json'},method='POST')
    d=json.loads(urllib.request.urlopen(req,timeout=30).read())
    for w in d.get('list_widgets',[]):
        x=w.get('data',{})
        if not x.get('@type','').endswith('PostRowData'):continue
        p=x['action']['payload'];t=p['token']
        rows[t]=dict(name=x.get('title'),category=q.strip(),phone='',address=p.get('web_info',{}).get('city_persian',''),lat='',lon='',rating='',
          detail=' | '.join(str(x.get(k,'')) for k in ('top_description_text','middle_description_text','bottom_description_text') if x.get(k)),
          link=f'https://divar.ir/v/{t}',id=t,source='divar')
    time.sleep(a.delay)
f=['name','category','phone','address','lat','lon','rating','detail','link','id','source']
w=csv.DictWriter(open(a.out,'w',newline='',encoding='utf-8-sig'),fieldnames=f);w.writeheader();w.writerows(rows.values());print(len(rows),'rows ->',a.out)
