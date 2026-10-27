#!/usr/bin/env python3
"""Merge source CSVs, filter Gilan cafes/restaurants, cross-source dedupe by phone then name.
Usage: merge.py --out merged.csv gmaps.csv balad.csv neshan.csv snappfood.csv divar.csv  (gmaps cols title/latitude/longitude mapped)"""
import argparse,csv,re
FA=str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩","01234567890123456789")
EXC=re.compile(r"هایپر|سوپرمارکت|سوپر مارکت|فروشگاه|بقالی|خواربار|hypermarket|supermarket|grocery",re.I)
def ph(p):
    p=re.sub(r"\D","",str(p or "").translate(FA))
    if p.startswith("0098"):p=p[4:]
    elif p.startswith("98"):p=p[2:]
    return ("0"+p.lstrip("0")) if p else ""
def nm(n):
    n=str(n or "").lower().replace("ي","ی").replace("ك","ک").replace("\u200c","").translate(FA)
    n=re.sub(r"کافه|رستوران|café|cafe|restaurant","",n);return re.sub(r"[\W_]+","",n)
ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('files',nargs='+');a=ap.parse_args()
out={};F=['name','category','phone','address','lat','lon','rating','link','id','source','phone_norm','name_norm']
for f in a.files:
    for r in csv.DictReader(open(f,encoding='utf-8-sig')):
        r={'name':r.get('name') or r.get('title'),'category':r.get('category'),'phone':r.get('phone'),'address':r.get('address') or r.get('complete_address'),
           'lat':r.get('lat') or r.get('latitude'),'lon':r.get('lon') or r.get('longitude'),'rating':r.get('rating') or r.get('review_rating'),
           'link':r.get('link'),'id':r.get('id') or r.get('place_id'),'source':r.get('source') or 'gmaps'}
        if EXC.search(f"{r['name']} {r['category']}"):continue
        try:
            if r['lat'] and not(36.5<=float(r['lat'])<=38.5 and 48.5<=float(r['lon'])<=50.6):continue
        except ValueError:pass
        r['phone_norm'],r['name_norm']=ph(r['phone']),nm(r['name'])
        k=next((k for k,v in out.items() if (r['phone_norm'] and v['phone_norm']==r['phone_norm']) or (r['name_norm'] and v['name_norm']==r['name_norm'])),None)
        if k:
            v=out[k];v['source']=';'.join(sorted(set(v['source'].split(';'))|{r['source']}))
            for c in F:
                if not v.get(c) and r.get(c):v[c]=r[c]
        else: out[len(out)]=r
w=csv.DictWriter(open(a.out,'w',newline='',encoding='utf-8-sig'),fieldnames=F);w.writeheader();w.writerows(out.values())
print(len(out),'merged,',sum(1 for v in out.values() if v['phone_norm']),'with phone ->',a.out)
