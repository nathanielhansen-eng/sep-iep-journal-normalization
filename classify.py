"""Count research papers per journal, 1990-2026, from the Crossref downloads in data/crossref/.

Writes output/classified.json: per journal, papers kept, how many items each rule dropped,
and papers kept per year.

Rules, applied in this order (each item is dropped by the first rule it fails):
  no_author    no author listed (front matter, notices)
  junk         title matches JUNK (front/back matter, indexes, errata, books received, ...)
  review       title matches REVIEW (book-review patterns; see the regex)
  short        fewer than --min-pages pages (default 10; --analysis-min-pages for Analysis, default 2)
  unknown_len  only a start page is recorded and the item is last in its issue, so its length
               can't be inferred. Only applied when the page minimum is 10 or more: in the
               review-heavy print journals these are almost all book reviews.
  duplicate    same volume + issue + start page as an item already kept (the same paper
               registered under two DOIs). Falls back to title + year when no page is recorded.

Length: from "start-end" page ranges; when only a start page is given, from the next item's
start page in the same issue.

Try other choices, e.g.  python classify.py --min-pages 5
"""
import argparse, collections, gzip, json, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('--min-pages', type=int, default=10)
ap.add_argument('--analysis-min-pages', type=int, default=2)
ap.add_argument('--out', default=os.path.join(ROOT, 'output', 'classified.json'))
args = ap.parse_args()


def plen(p):
    if not p:
        return None
    m = re.match(r'^[A-Za-z]*(\d+)\s*[-–]\s*[A-Za-z]*(\d+)$', p.strip())
    if not m:
        return None
    a, b = int(m[1]), int(m[2])
    return b - a + 1 if b >= a else None


def norm(t):
    return re.sub(r'[^a-z0-9]', '', t.lower())


JUNK = re.compile(r"issue information|front matter|back matter|cover and|^index|author index|index to volume|index:|books? received|journals received|notes on (the )?contributors|editorial board|erratum|errata|correction|corrigend|retraction|announcement|call for|new books|recent publications|^abstracts|^contents|table of contents|solicitation|forthcoming issues|teaching (&|&amp;|and) learning guide|in memoriam|memorium|obituar|^preface|^foreword|editor.?s? foreword|message from|referees|acknowledg|volume information|^editorial|prize|^notes and news|^news", re.I)
REVIEW = re.compile(r"book ?reviews?|^review[:. ]|review of |critical notice|^reviews\b|university press|\bpress[,.;:)]|\bpp\.|\bisbn|\$\s?\d|£\s?\d|\bpaper(back)?\b.*\d|\bcloth\b|\(eds?\.\)|\beds?\.,|, by [A-Z]|\bby [A-Z][a-z]+,? [A-Z]|\bedited by\b|\. by [A-Z]|^<i>|</i>\s*by\b|</i>\.?\s*[A-Z][a-z]+ [A-Z]|^\s*:", re.I)

rows = []
for line in open(os.path.join(ROOT, 'data', 'issn.tsv')):
    name, issn = line.rstrip('\n').split('\t')
    if name == 'Science':
        continue
    with gzip.open(os.path.join(ROOT, 'data', 'crossref', f'{issn}.json.gz'), 'rt') as f:
        items = json.load(f)
    starts = collections.defaultdict(list)
    for x in items:
        m = re.match(r'^(\d+)', (x.get('page') or '').strip())
        if m:
            starts[(x.get('volume'), x.get('issue'))].append(int(m[1]))
    for k in starts:
        starts[k] = sorted(set(starts[k]))
    minp = args.analysis_min_pages if name == 'Analysis' else args.min_pages
    seen, keys = set(), set()
    c, byyear = collections.Counter(), collections.Counter()
    for x in items:
        doi = x['DOI'].lower()
        if doi in seen:
            continue
        seen.add(doi)
        t = (x.get('title') or [''])[0]
        y = (x.get('published') or {}).get('date-parts', [[None]])[0][0]
        pg = (x.get('page') or '').strip()
        L, startonly = plen(pg), False
        if L is None:
            m = re.match(r'^(\d+)$', pg)
            if m:
                p = int(m[1])
                nxt = [q for q in starts[(x.get('volume'), x.get('issue'))] if q > p]
                if nxt:
                    L = nxt[0] - p
                else:
                    startonly = True
        if not x.get('author'):
            c['no_author'] += 1; continue
        if JUNK.search(t):
            c['junk'] += 1; continue
        if REVIEW.search(t):
            c['review'] += 1; continue
        if L is not None and L < minp:
            c['short'] += 1; continue
        if startonly and minp >= 10:
            c['unknown_len'] += 1; continue
        if re.match(r'^(introduction|symposium)\b', t, re.I) and (L or 99) < 8:
            c['junk'] += 1; continue
        sm = re.match(r'^[A-Za-z]*(\d+)', pg)
        key = (x.get('volume'), x.get('issue'), sm[1]) if sm and x.get('volume') else (norm(t), y)
        if key in keys:
            c['duplicate'] += 1; continue
        keys.add(key)
        c['kept'] += 1
        byyear[y] += 1
    rows.append(dict(
        journal=name, issn=issn, crossref_items=len(seen), kept=c['kept'],
        dropped_no_author=c['no_author'], dropped_junk=c['junk'], dropped_review=c['review'],
        dropped_short=c['short'], dropped_unknown_len=c['unknown_len'], dropped_duplicate=c['duplicate'],
        first_year=min(k for k in byyear if k),
        by_year={k: byyear[k] for k in sorted(k for k in byyear if k)}))
    print(f"{name:45s} items={len(seen):5d} kept={c['kept']:5d}  review={c['review']:4d} short={c['short']:4d} "
          f"junk={c['junk']:4d} no_author={c['no_author']:4d} unknown_len={c['unknown_len']:3d} dup={c['duplicate']:4d}")

os.makedirs(os.path.dirname(args.out), exist_ok=True)
json.dump(dict(settings=vars(args) | {'out': None}, journals=rows), open(args.out, 'w'), indent=1)
