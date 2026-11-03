"""Download Crossref metadata (type journal-article, 1990-2026) for every journal in data/issn.tsv.

Writes data/crossref/<ISSN>.json.gz. Existing files are skipped, so delete one to refresh it.
The copies in this repo were downloaded on 2026-11-03.
"""
import gzip, json, os, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'data', 'crossref')
os.makedirs(OUT, exist_ok=True)

for line in open(os.path.join(ROOT, 'data', 'issn.tsv')):
    name, issn = line.rstrip('\n').split('\t')
    if name == 'Science':
        continue
    fn = os.path.join(OUT, f'{issn}.json.gz')
    if os.path.exists(fn):
        continue
    cur, out = '*', []
    while True:
        u = (f"https://api.crossref.org/journals/{issn}/works?filter=from-pub-date:1990-01-01,until-pub-date:2026-12-31,type:journal-article"
             f"&select=DOI,title,page,published,author,volume,issue&rows=1000&cursor={urllib.parse.quote(cur)}")
        for attempt in range(4):
            try:
                req = urllib.request.Request(u, headers={'User-Agent': 'sep-iep-journal-normalization/1.0'})
                m = json.load(urllib.request.urlopen(req, timeout=60))['message']
                break
            except Exception as e:
                print('retry', name, e)
                time.sleep(3)
        else:
            raise SystemExit(f'failed: {name}')
        out += m['items']
        if not m['items'] or len(out) >= m['total-results']:
            break
        cur = m['next-cursor']
    with gzip.open(fn, 'wt') as f:
        json.dump(out, f)
    print(name, len(out), flush=True)
