---
name: Iran maps lead sourcing (Balad, Neshan, Google Maps)
description: Use when sourcing local cafe/restaurant/shop leads for AROMIN in Rasht/Gilan from map apps (Balad, Neshan, Google Maps) as a third source after Instagram and job channels, including spotting newly opened places, filtering, dedup and CSV output.
---
# سورس لید از نقشه‌ها (بلد، نشان، گوگل مپ) برای آرومین

نقشه‌ها **منبع سوم** هستند (اول اینستاگرام، دوم کانال‌های آگهی استخدام). خروجی نقشه فقط «کاندید» است؛ طبق مهارت `aromin-qualified-lead-criteria` لیست خام نقشه لید نیست تا نیاز واقعی و جواب‌دادن شماره تأیید نشود.
وضعیت تست‌ها: ۲۸ مهر ۱۴۰۵ (2026-10-19)، از باکس لینوکسی با curl و پایتون، بدون کلید و بدون لاگین.

| منبع | وضعیت | نیازمندی |
|---|---|---|
| بلد | ✅ تست شد و کار کرد (۲۰ کافه + ۲۰ فست‌فود رشت، هر کدام ۱ صفحه) | هیچ (بدون کلید/لاگین) |
| نشان API | ❌ بدون کلید خطای 480 می‌دهد | Api-Key از پنل توسعه‌دهندگان نشان (ثبت‌نام رایگان)؛ v1 هم با تیکت فعال می‌شود |
| گوگل مپ | ⚠️ تست نشد (پولی است) | اکتور Apify (هزینه به ازای هر مکان) یا مرورگر |

## ۱. بلد (balad.ir): منبع اصلی نقشه، تست‌شده ✅
### الف) API لیست دسته (JSON، بدون کلید)
```
GET https://search.raah.ir/v4/placeslist/cat/?region=city-rasht&name=coffee-shop&page=1
Headers: accept: application/json, platform: web, referer: https://balad.ir/, User-Agent مرورگر
```
- خروجی: `items` = لیست توکن (۲۰ تا در هر صفحه) + `page_count` (کافه‌های رشت: ۳۶ صفحه ≈ ۷۰۰ مکان؛ فست‌فود: ۲۳ صفحه).
- جزئیات ۲۰ توکن در یک درخواست:
```
GET https://poi.raah.ir/web/v4/preview-bulk/<token1>,<token2>,...
```
  فیلدها: `token, name, category, address, telephone, website, geometry.coordinates [lng,lat], rating.score, rating.count, images, badges, url_title`.
### ب) صفحه وب دسته (SSR، جایگزین)
`https://balad.ir/city-rasht/cat-<slug>`: داخل `<script id="__NEXT_DATA__">` در مسیر `props.pageProps.data.items` همان فیلدها هست، به‌اضافه `pageCount` و `adItems` (آگهی‌ها).
### ج) صفحه هر مکان (برای سیگنال تازه‌تأسیس)
`https://balad.ir/p/<token>` (ریدایرکت به اسلاگ). در `__NEXT_DATA__` → `props.pageProps.data.poi`: ساعت کاری، تلفن، `id` عددی، امتیازها، و `comments[].createdAt` به‌صورت نسبی (مثلاً «۴ سال پیش»، «۲ هفته پیش»). بخش «من صاحب این کسب‌وکار هستم» (claim) هم آنجاست.
### اسلاگ‌های مفید (از balad.ir/bundles)
`coffee-shop` (کافه)، `coffee-house` (قهوه‌خانه/چایخانه)، `restaurant`، `fast-food-restaurant`، `catering`، `confectionery` (شیرینی‌فروشی)، `ice-cream-and-juice-shop`، `clothing-store`، `bag-and-shoes-shop`، `cosmetics-store`، `cell-phone-store`، `nuts-store`، `meat-and-protein-shop`. **`supermarket` را نگیر.** شهرها: `city-rasht`، `city-lahijan`، `city-bandar-anzali` (اسلاگ‌های غیر رشت تست نشده‌اند).
فیلترهای صفحه: فقط تلفن‌دار (61)، فقط باز (21)، فقط عکس‌دار (41)، مرتب‌سازی امتیاز (13) / پربازدید (14). پارامتر URL این فیلترها تست نشده؛ مرتب‌سازی «جدیدترین» وجود ندارد.
### اسکریپت آماده
```
python3 /home/box/agent-data/workflows/iran-maps-lead-sourcing/balad_fetch.py --city rasht --cat coffee-shop --pages 2 --out /workspace/balad_cafe.csv [--contacts existing_contacts.csv]
```
بین درخواست‌ها ۲ تا ۶ ثانیه تأخیر تصادفی می‌گذارد، سوپرمارکت/هایپر را حذف می‌کند، با فایل مخاطبین بر اساس تلفن و نام dedup می‌کند و CSV با ستون‌های استاندارد پایین می‌سازد.
نتیجه تست: کافه رشت صفحه ۱ → ۲۰ مکان، ۱۶ تلفن‌دار، ۱۸ با ۰ تا ۵ نظر. فست‌فود صفحه ۱ → ۲۰ مکان، ۱۷ تلفن‌دار.
**قواعد ادب:** هر بار حداکثر چند صفحه، تأخیر ۳ ثانیه یا بیشتر، بدون موازی‌سازی و بدون چرخش IP یا دورزدن محدودیت. اگر 429/403 آمد، متوقف شو.

## ۲. نشان (neshan.org): نیازمند کلید ❌
- v1 (قدیمی، حداکثر ۳۰ نتیجه، مرتب بر اساس فاصله):
```
curl 'https://api.neshan.org/v1/search?term=کافه&lat=37.2808&lng=49.5832' -H 'Api-Key: <KEY>'
```
- v3 (جدید): `GET https://api.neshan.org/v3/search?q=<URL-encoded {"term":"کافه","center":{"latitude":37.2808,"longitude":49.5832}}>` با همان هدر.
- فیلدهای خروجی: `title, address, neighbourhood, region, type, category (place/municipal/region), location.x/y`. **تلفن، امتیاز و تعداد نظر ندارد**، پس فقط برای کشف نام و آدرس به کار می‌آید و باید با بلد یا اینستاگرام تکمیل شود.
- تست ۱۴۰۵/۰۷/۲۸ بدون کلید: `480 KeyNotFound`. کلید با ثبت‌نام رایگان در پنل توسعه‌دهندگان نشان (platform.neshan.org) گرفته می‌شود؛ طبق مستندات v1 باید با تیکت فعال شود. ثبت‌نام **انجام نشده** و تصمیمش با کاربر است. خطاها: 481 سقف مصرف، 482 سقف نرخ.
- مرکز رشت: lat=37.2808, lng=49.5832. برای پوشش بیشتر چند مرکز بگذار (گلسار، منظریه، حافظ، بلوار معلم و غیره).

## ۳. گوگل مپ: از طریق Apify، تست نشده ⚠️
- فچ مستقیم `google.com/maps/search/...` فقط یک پوسته JS برمی‌گرداند و داده ندارد، پس بدون مرورگر یا Apify قابل استفاده نیست.
- اکتور: `compass/crawler-google-places` از کانکتور `user-Apify` (ابزار `call-actor`). **پولی است** (پرداخت به ازای رویداد؛ پلن FREE حدود $0.004 برای هر مکان، هر نظر $0.0005، هر عکس $0.0005، هر فیلتر $0.001). اجرا فقط با تأیید کاربر و همیشه با `callOptions.maxTotalChargeUsd` (مثلاً 0.1).
- ورودی پیشنهادی (تست نشده؛ قبل از اجرا با `fetch-actor-details` اسکیمای ورودی را چک کن):
```json
{"searchStringsArray":["کافه","coffee shop"],"locationQuery":"Rasht, Iran","maxCrawledPlacesPerSearch":10,"language":"fa","maxReviews":3,"reviewsSort":"oldest","maxImages":0}
```
- فیلدهای مهم: `title, categoryName, address, phone, totalScore, reviewsCount, url, placeId, website, openingHours, reviews[].publishedAtDate, imagesCount`. نظرهایی که با `reviewsSort: oldest` می‌آیند تاریخ اولین نظر را می‌دهند، که بهترین سیگنال تازه‌تأسیس است.
- مهارت `google-maps-lead-generation` (شخص ثالث، ویرایش نکن) با ScrapeGraphAI و Playwright و کلید LLM کار می‌کند. پیش‌نیازهای سنگینی دارد، تست نشده و فقط جایگزین است.

## ۴. تشخیص کسب‌وکار تازه‌تأسیس
سیگنال‌ها (هر کدام را در ستون `signals` بنویس):
- `few_reviews`: بین ۱ تا ۵ نظر؛ `no_reviews`: صفر نظر. **به‌تنهایی کافی نیست.** در تست، کافه‌ای با ۲ نظر داشتیم که اولین نظرش «۴ سال پیش» بود.
- `recent_first_review`: قدیمی‌ترین نظر در بلد (`comments[].createdAt`) یا گوگل (`publishedAtDate`) کمتر از ۶ ماه پیش باشد. **قوی‌ترین سیگنال.**
- `recent_photos`: اولین عکس‌ها جدیدند (فقط در گوگل از طریق Apify).
- `new_label`: برچسب «جدید» یا «New» در گوگل مپ یا `badges` بلد (در بلد دیده نشده و تست نشده).
- `unclaimed`: صاحب کسب‌وکار هنوز مکان را claim نکرده (گزینه «من صاحب این کسب‌وکار هستم» فعال است). سیگنال ضعیف.
- `high_poi_id`: `id` عددی بلد بالاتر از بیشتر مکان‌های همان دسته باشد، که احتمالاً یعنی اخیراً اضافه شده (فرضیه، تست نشده).
- `mobile`: شماره موبایل ۰۹ معمولاً مال صاحب کسب‌وکار است و احتمال جواب‌دادنش بیشتر است.
- `insta_new`: پیج اینستاگرامی با پست‌های اول «افتتاحیه» یا «به‌زودی» در چند ماه اخیر.

## ۵. فیلترها
- حذف کامل: سوپرمارکت، هایپرمارکت، فروشگاه زنجیره‌ای (افق کوروش، شهروند، رفاه، اتکا، هایپراستار، جانبو و مشابه).
- حذف یا پایین‌آوردن امتیاز: زنجیره‌ها و شعب برندهای سراسری که نرم‌افزار متمرکز دارند؛ مکان‌های بدون تلفن؛ شماره ناقص (کمتر از ۱۱ رقم، مثل `0133617` که در تست دیدیم)؛ آگهی‌های `adItems` فقط اگر مرتبط باشند.
- خارج از بازار: هر چیزی جز رستوران، کافه، فست‌فود، قنادی و مغازه خرده‌فروشی.
- نیاز واقعی و جواب‌دادن شماره را قبل از تحویل به فروش چک کن.

## ۶. حذف تکراری‌ها (dedup) با مخاطبین موجود
- تلفن: ارقام فارسی و عربی را به لاتین تبدیل کن، فقط رقم‌ها را نگه دار، پیشوند `98` را به `0` تبدیل کن و ۱۰ رقم آخر را مقایسه کن.
- نام: «ي/ك» عربی را به «ی/ک» تبدیل کن، نیم‌فاصله و کلمات عمومی (کافه، رستوران، فست‌فود، رشت) را حذف کن و نام نرمال‌شده را مقایسه کن. برای نام‌های نزدیک به هم، نام + محله را دستی چک کن.
- بین منابع: یک کسب‌وکار ممکن است در بلد، گوگل و اینستاگرام باشد. با تلفن یکی کن و منابع را در ستون `source` با `;` کنار هم بنویس.
- فهرست مخاطبین موجود (CRM جولیو یا خروجی CSV) را با `--contacts` به اسکریپت بده.

## ۷. ستون‌های CSV خروجی (UTF-8 با BOM)
`name, category, phone, address, city, source, map_url, review_count, signals, score`
- `source`: balad / neshan / gmaps (چندتایی با `;`).
- `map_url`: `https://balad.ir/p/<token>` یا URL گوگل مپ.
- `score` پیشنهادی: تلفن معتبر +۲ (بدون تلفن -۵)؛ `recent_first_review` +۳؛ `few_reviews` +۲؛ `no_reviews` +۱؛ `mobile` +۱؛ `insta_new` +۳؛ زنجیره‌ای -۳؛ سوپر/هایپر = حذف. امتیاز نهایی را با محورهای مهارت معیار لید ترکیب کن.

## ۸. تطبیق با اینستاگرام
برای هر کاندید با امتیاز بالا: «نام + رشت» را در اینستاگرام یا وب جستجو کن (مثلاً `site:instagram.com "نام کافه" رشت`). تاریخ اولین پست، پست افتتاحیه، آگهی استخدام، تعداد فالوور و شماره در بیو را چک کن. اگر شماره بیو با شماره نقشه فرق داشت، هر دو را بنویس. پیج تازه با فالوور کم و پست‌های افتتاحیه، `insta_new` می‌گیرد.

## ۹. روال پیشنهادی
1. بلد: `coffee-shop`، `restaurant` و `fast-food-restaurant` رشت را ۲ تا ۳ صفحه بگیر (اسکریپت).
2. برای ۲۰ تا ۳۰ مکان با کمترین تعداد نظر، صفحه `balad.ir/p/<token>` را با تأخیر بگیر و تاریخ اولین نظر را دربیاور (تابع این مرحله هنوز در اسکریپت نیست).
3. اگر کاربر اجازه داد: Apify گوگل مپ با سقف هزینه برای همان دسته‌ها.
4. dedup، فیلتر، امتیازدهی، تطبیق با اینستاگرام و تأیید شماره، سپس تحویل لیدهای کلاس B و بالاتر.
