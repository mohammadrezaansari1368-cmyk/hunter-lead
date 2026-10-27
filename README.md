# Hunter Lead

## فارسی
**Hunter lead** جعبه‌ابزار پیدا کردن لید کافه و رستوران در رشت/گیلان برای AROMIN است. داده از ۵ منبع جمع می‌شود و در یک فایل یکتا ادغام می‌شود.

### منابع
| منبع | ابزار | وضعیت |
|---|---|---|
| Google Maps | `tools/google-maps-scraper` (باینری gosom) | فعال |
| بلد | `tools/balad-scraper/balad_scraper.py` | فعال |
| نشان | `tools/neshan-scraper/neshan_scraper.py` | نیاز به کلید API رایگان در `NESHAN_API_KEY` |
| اسنپ‌فود | `tools/snappfood-scraper/snappfood_scraper.py` | نیاز به IP ایران |
| دیوار | `tools/divar-scraper/divar_scraper.py` | فقط سیگنال؛ شماره تلفن ندارد |

### اجرا
```bash
python3 tools/balad-scraper/balad_scraper.py
export NESHAN_API_KEY=service.xxx && python3 tools/neshan-scraper/neshan_scraper.py
python3 tools/snappfood-scraper/snappfood_scraper.py   # با IP ایران
python3 tools/divar-scraper/divar_scraper.py
python3 tools/hunter-lead/merge.py
```
جزئیات هر منبع در `skills/<name>/SKILL.md`.

### ادغام و حذف تکراری
`merge.py` شماره‌ها را نرمال می‌کند (ارقام فارسی→لاتین، `+98`/`0098`→`0`)، بر اساس تلفن و سپس نام نرمال‌شده تکراری‌ها را حذف می‌کند، هایپر/سوپرمارکت و نقاط خارج گیلان را فیلتر می‌کند. سپس خروجی با لیدهای موجود در Joolio مقایسه می‌شود (طبق skills/hunter-lead).

### قوانین
- فقط گیلان/رشت
- فقط کافه و رستوران؛ بدون هایپرمارکت/سوپرمارکت
- حذف تکراری‌ها نسبت به Joolio
- هیچ CSV، کوکی، توکن یا کلید API کامیت نشود

## English
**Hunter lead** is AROMIN's lead-generation toolkit for cafes and restaurants in Rasht/Gilan. It collects from 5 sources and merges them into one deduplicated list.

Sources: Google Maps (gosom binary, see `tools/google-maps-scraper/README.md`), Balad, Neshan (needs a free API key in the `NESHAN_API_KEY` env var), SnappFood (needs an Iranian IP), Divar (signals only, no phone numbers). The run commands are above, and each source has its own playbook in `skills/`.

**Merge/dedupe:** `tools/hunter-lead/merge.py` normalizes phones (Persian→Latin digits, `+98`/`0098`→`0`), dedupes by phone then normalized name, drops hypermarkets/supermarkets and points outside Gilan; the output is then checked against Joolio (see `skills/hunter-lead`).

**Rules:** Gilan/Rasht only; cafes/restaurants only; no hypermarkets/supermarkets; dedupe vs Joolio; never commit CSVs, cookies, tokens, `.u100`/`.p100`, or API keys.
