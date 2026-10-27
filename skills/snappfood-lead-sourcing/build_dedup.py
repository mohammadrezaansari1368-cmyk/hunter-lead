import json,re,csv,pandas as pd
from rapidfuzz import fuzz, process
FA=str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩","01234567890123456789")
STRIP=r"(?<!\S)(کافه|کافی ?شاپ|رستوران|فست ?فود|فستفود|فست|فود|رشت|گیلان|شعبه|cafe|coffee|restaurant)(?!\S)"
def norm(n):
    n=str(n or "").lower().replace("ي","ی").replace("ى","ی").replace("ك","ک").replace("ة","ه").replace("أ","ا").replace("إ","ا").translate(FA)
    n=n.replace("\u200c"," ").replace("\u200f","")
    n=re.sub(r"\(.*?\)","",n) if re.sub(r"\(.*?\)","",n).strip() else n
    n=re.sub(STRIP,"",n)
    return re.sub(r"[\s\-_.،,:|/]+","",n)
def nphone(p):
    p=re.sub(r"\D","",str(p or "").translate(FA).replace(".0",""))
    if p.startswith("98"):p=p[2:]
    return p.lstrip("0")[-10:] if p else ""
raw=json.load(open('raw/balad_raw.json'))
EXC=re.compile(r"هایپر|سوپرمارکت|سوپر مارکت|فروشگاه|بقالی|خواربار|میوه")
rows=[]
for t,it in raw.items():
    name=it.get('name') or ''; cat=it.get('category') or ''
    if EXC.search(name+' '+cat): continue
    r=it.get('rating') or {}; rc=r.get('count') or 0
    ph=re.sub(r"\D","",(it.get('telephone') or '').translate(FA))
    if ph.startswith('98'): ph='0'+ph[2:]
    sig=[]
    if rc==0: sig.append('no_reviews')
    elif rc<=5: sig.append('few_reviews')
    if not it.get('images') and not it.get('image'): sig.append('no_photos')
    if any(b.get('label')=='new' for b in it.get('badges') or []): sig.append('new_badge')
    if any(b.get('label')=='verification' for b in it.get('badges') or []): sig.append('owner_verified')
    web=it.get('website') or ''
    insta=web if 'instagram' in web else ''
    addr=it.get('address') or ''
    area=addr.split('،')[1] if addr.count('،')>=1 else addr
    lon,lat=(it.get('geometry') or {}).get('coordinates',[None,None])
    rows.append(dict(name=name,category=cat,area=area,address=addr,rating=r.get('score'),review_count=rc,new_signal=';'.join(sig),
        snappfood_url='',balad_url=f"https://balad.ir/p/{t}",website=web,instagram=insta,phone=ph,lat=lat,lng=lon,source='balad'))
allv=pd.DataFrame(rows)
allv['_n']=allv.name.map(norm)
allv=allv.sort_values(['review_count']).drop_duplicates(subset=['_n','phone'])
# CRM
names=[];phones={}
for f in ['/workspace/arash/invite/contacts.xlsx','/workspace/shared/joolio_contacts_all.xlsx']:
    x=pd.read_excel(f,dtype=str)
    for _,r in x.iterrows():
        label=' / '.join(str(r[c]) for c in ['نام شرکت','نام‌خانوادگی'] if pd.notna(r.get(c)))
        for c in ['نام شرکت','نام‌خانوادگی']:
            if pd.notna(r.get(c)): names.append((norm(r[c]),r[c],f.split('/')[-1]))
        for c in ['شماره \u200cتماس اصلی','شماره موبایل اصلی','شماره موبایل دوم','شماره‌تماس شرکت','شماره‌تماس منزل']:
            if c in x.columns and pd.notna(r.get(c)):
                p=nphone(r[c]); 
                if len(p)>=8: phones[p]=(label,f.split('/')[-1])
q=pd.read_csv('/workspace/arash/invite/queue.csv',dtype=str)
for _,r in q.iterrows():
    if pd.notna(r.company): names.append((norm(r.company),r.company,'queue.csv'))
    p=nphone(r.phone)
    if len(p)>=8: phones.setdefault(p,(r.company,'queue.csv'))
names=[n for n in {(a,b,c) for a,b,c in names} if len(n[0])>=2]
choices=[n[0] for n in names]
match=[]
for i,r in allv.iterrows():
    why=None
    if 'مادام' in r['name'] and 'موسیو' in r['name']: why=('blacklist','مادام موسیو','blacklist',100)
    p=nphone(r.phone)
    if not why and p in phones: why=('phone',)+phones[p]+(100,)
    if not why and len(r._n)>=2:
        b=process.extractOne(r._n,choices,scorer=fuzz.ratio)
        if b and (b[1]==100 or (b[1]>=85 and min(len(r._n),len(b[0]))>=5)): why=('name',names[b[2]][1],names[b[2]][2],round(b[1]))
    match.append(why)
allv['match']=match
cols=['name','category','area','address','rating','review_count','new_signal','snappfood_url','balad_url','website','instagram','phone','lat','lng','source']
allv[cols].to_csv('rasht_vendors_all.csv',index=False,encoding='utf-8-sig')
m=allv[allv.match.notna()].copy()
m['match_type']=m.match.map(lambda w:w[0]);m['matched_to']=m.match.map(lambda w:w[1]);m['matched_file']=m.match.map(lambda w:w[2]);m['score']=m.match.map(lambda w:w[3])
m[cols+['match_type','matched_to','matched_file','score']].to_csv('rasht_matched_joolio.csv',index=False,encoding='utf-8-sig')
n=allv[allv.match.isna()].copy()
n['mobile']=n.phone.where(n.phone.str.match(r'^09\d{9}$'),'')
n['phone_source']=n.mobile.map(lambda v:'balad' if v else '')
n=n.sort_values(['review_count','rating'],na_position='first')
n[cols+['mobile','phone_source']].to_csv('rasht_new_not_in_joolio.csv',index=False,encoding='utf-8-sig')
print(len(allv),len(m),m.match_type.value_counts().to_dict(),len(n),(n.mobile!='').sum(), (n.phone!='').sum())
print(m[m.match_type=='name'][['name','matched_to','score']].head(40).to_string())
