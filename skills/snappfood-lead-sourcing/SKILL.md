---
name: SnappFood lead sourcing
description: Use when building an AROMIN lead list of restaurants/cafes/fast-food in Rasht or other Gilan cities from SnappFood (or Balad as fallback), deduped against the Joolio CRM and enriched with owner mobiles, before the first Bale message.
---
# سورس لید از اسنپ‌فود (و جایگزین بلد) برای آرومین

آخرین اجرا: ۲۸ مهر ۱۴۰۵ (2026-10-19). خروجی‌ها در `/workspace/arash/snappfood/`.

## ۱. اسنپ‌فود: از باکس مسدود است ❌
- هر درخواستی به `snappfood.ir` (چه صفحه، چه API) از IP خارج از ایران **403 با «Server Code: 5700»** (فایروال ArvanCloud، geo-block) می‌گیرد. curl از باکس، WebFetch و `apify/rag-web-browser` هر سه 403 گرفتند. دورزدن (پراکسی/VPN ایرانی) **انجام نده** مگر کاربر صریحاً بگوید.
- اندپوینت‌های شناخته‌شده وب‌اپ (فقط از IP ایران، مثلاً روی دسکتاپ کاربر با machineId، تست نشده):
  - لیست وندور بر اساس مختصات: `GET https://snappfood.ir/mobile/v3/restaurant/vendors-list?lat=<lat>&long=<lng>&page=0&page_size=20&optionalClient=WEBSITE&client=WEBSITE&deviceType=WEBSITE&appVersion=8.1.1&locale=fa` (پارامتر `superType=[1]` برای رستوران؛ کافه و شیرینی superType دیگری دارند).
  - جزئیات وندور: `GET https://snappfood.ir/mobile/v2/restaurant/details/dynamic?lat=..&long=..&vendorCode=<code>&optionalClient=WEBSITE&client=WEBSITE&deviceType=WEBSITE&appVersion=8.1.1`
  - صفحه شهر (SSR): `https://snappfood.ir/service/restaurant/city/rasht/` و `https://snappfood.ir/service/all/city/rasht/`؛ لینک وندور: `https://snappfood.ir/restaurant/menu/<slug>-r-<vendorCode>/`.
  - فیلدهای مفید: `title, vendorCode, rating, commentCount, address/area, vendorType/childType, isNew / badges`.
  - گوگل هم صفحات وندورهای رشت را تقریباً ایندکس نکرده (`site:snappfood.ir/restaurant/menu رشت` نتیجه نداد).
- اگر کاربر دسکتاپش را وصل کرد: `ListMachines` → `Shell` با machineId، curl با User-Agent مرورگر، ۳ تا ۵ ثانیه تأخیر، حداکثر چند صفحه، بدون لاگین.

## ۲. جایگزین کارکرده: بلد ✅
اسکریپت: `/home/box/agent-data/workflows/iran-maps-lead-sourcing/balad_fetch.py` (جزئیات در مهارت `iran-maps-lead-sourcing`).
```
python3 balad_fetch.py --city rasht --cat coffee-shop --pages 8 --out balad_coffee-shop.csv
# بعد: fast-food-restaurant و restaurant
```
- `search.raah.ir/v4/placeslist/cat/?region=city-rasht&name=<slug>&page=N` → توکن‌ها؛ `poi.raah.ir/web/v4/preview-bulk/<t1,t2,...>` → name, category, address, telephone, website, rating{score,count}, badges.
- صفحه هر مکان `balad.ir/p/<token>` → در `__NEXT_DATA__` فیلد `fields` اینستاگرام و همه تلفن‌ها را دارد؛ `id` عددی هم هست (بزرگ‌تر = احتمالاً جدیدتر).
- تعداد صفحه در رشت: کافه ۳۶، فست‌فود ۲۳، رستوران ۸۱ صفحه (هر صفحه ۲۰ مکان). اجرای ۸ صفحه از هر دسته ← ۴۱۸ مکان یکتا.
- شهرهای دیگر گیلان: `city-lahijan`، `city-bandar-anzali`، `city-langarud`، `city-fuman`، `city-astara`، `city-talesh`، `city-sowme-e-sara`، `city-rudsar` (اسلاگ‌ها جز رشت تست نشده‌اند؛ اول یک صفحه تست کن). برای اسنپ‌فود فقط lat/lng مرکز شهر را عوض کن (لاهیجان 37.207,50.003؛ انزلی 37.472,49.462؛ لنگرود 37.197,50.153).

## ۳. فیلتر
- فقط کافه، رستوران، فست‌فود، کبابی، طباخی، کافه‌قنادی. حذف: سوپرمارکت، هایپر، فروشگاه، بقالی، میوه، زنجیره‌ای‌ها.
- بلک‌لیست: «مادام موسیو».
- سالن غذاخوری دانشگاه/اداره را دستی حذف کن.

## ۴. dedup با Joolio (CRM)
اسکریپت آماده: `build_dedup.py` همین پوشه (ورودی `raw/balad_raw.json`).
- منابع: `/workspace/arash/invite/contacts.xlsx` (= `/workspace/shared/joolio_contacts_all.xlsx`)، ستون‌های «نام شرکت» و «نام‌خانوادگی» + همه ستون‌های شماره؛ و `/workspace/arash/invite/queue.csv` (company, phone).
- نرمال‌سازی: ي→ی، ك→ک، ارقام فارسی→لاتین، حذف ZWNJ و فاصله و علائم، حذف کلمات **کامل** کافه/کافی‌شاپ/رستوران/فست‌فود/رشت/گیلان/شعبه. (حذف داخل کلمه خطا می‌دهد: «درشتی» → «دی»).
- تطبیق: شماره (۱۰ رقم آخر) یکسان = تکراری. نام: `rapidfuzz.fuzz.ratio ≥ 85`؛ اما اگر نام نرمال‌شده کمتر از ۵ حرف است فقط تطابق ۱۰۰. ستون `confidence=review` برای ۸۵ تا ۹۴ یعنی دستی چک شود (مثل «آشپزخانه پدر» ↔ «آشپزخانه مدرن»).
- نتیجه اجرای اول: ۴۱۸ کل → ۱۳۱ تکراری (۱۱۱ نام، ۲۰ شماره) → ۲۸۷ جدید.

## ۵. پیدا کردن موبایل
ترتیب پیشنهادی (از ارزان به گران):
1. **تلفن خود بلد**: بیشترین بازده. از ۲۸۷ مکان جدید، ۱۰۹ موبایل ۰۹ و حدود ۸۰ تلفن ثابت داشتند.
2. **صفحه مکان بلد** (`balad.ir/p/<token>`): اینستاگرام و تلفن دوم. با ۳ تا ۵ ثانیه تأخیر.
3. **WebSearch** با `"<نام>" رشت` یا `"<نام>" رشت اینستاگرام`. صفحات `exa.ai/library/place/<id>` داده گوگل‌مپ دارند (Phone، Coordinates)؛ با WebFetch بخوان و **حتماً مختصات را چک کن** (رشت ≈ 37.2,49.6). در تست سه شماره مال قوچان/ساری/اراک بود. behtarino، bertina، bazarol و cafe-gilan.ir هم شماره دارند.
4. **Apify گوگل‌مپ** (`compass/crawler-google-places`): حدود $0.004 برای هر مکان. اعتبار رایگان این ماه فقط $0.34 مانده بود و اجرا رد شد. فقط با تأیید کاربر.
- بازده واقعی برای مکان‌های «۰ نظر» بلد پایین است (۱ موبایل از ۴۰)، چون بیشترشان ثبت‌های قدیمی و راکدند. پس **اولویت را به مکان‌هایی بده که ۱ تا ۵ نظر و id بالا دارند**، نه فقط ۰ نظر.
- همیشه `phone_source` را ثبت کن. شماره ثابت 013 را جدا نگه دار (برای بله کار نمی‌کند).

## ۶. پیام اول در بله
- فقط به موبایل‌های ۰۹ تأییدشده و بعد از dedup. **ارسال فقط با تأیید صریح کاربر.** صف ارسال در `/workspace/arash/invite/queue.csv` با وضعیت `sent` / `not_on_bale`.
- پیام اول کوتاه و شخصی باشد: نام کافه، معرفی آرومین (رشت؛ صندوق فروشگاهی، کاغذ رول، نرم‌افزار سپیدز) و یک سؤال ساده («الان برای صندوق و فاکتور از چی استفاده می‌کنید؟»). بدون لینک و بدون قیمت در پیام اول.
- **هر کسی در بله جواب داد = لید بالقوه.** وضعیت را `replied` بزن و طبق مهارت `aromin-qualified-lead-criteria` نیاز واقعی را بسنج. جواب‌ندادن یا «not_on_bale» = هنوز لید نیست.

## خروجی‌ها
`rasht_vendors_all.csv`، `rasht_matched_joolio.csv` (match_type, matched_to, score, confidence)، `rasht_new_not_in_joolio.csv` (مرتب بر اساس کمترین نظر)، `rasht_with_mobile.csv` (name, category, area, rating, review_count, new_signal, snappfood_url, balad_url, instagram, mobile, phone_source). ستون `snappfood_url` تا وقتی اسنپ‌فود در دسترس نیست خالی می‌ماند.
