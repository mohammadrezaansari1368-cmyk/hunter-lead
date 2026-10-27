# google-maps-scraper (gosom)
Binary not committed. Download from https://github.com/gosom/google-maps-scraper/releases (linux amd64), save as `gmaps`, `chmod +x gmaps`.

```bash
printf 'کافه رشت\nرستوران رشت\n' > q.txt
./gmaps -input q.txt -results gmaps_rasht.csv -exit-monitor 3m -lang fa -depth 5
```
Then merge with `tools/hunter-lead/merge.py`.
