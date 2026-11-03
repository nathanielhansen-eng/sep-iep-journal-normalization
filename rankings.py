"""Combine citation counts (data/citations.tsv) with paper counts (output/classified.json)
into output/normalized_rankings_1990-2026.csv: SEP+IEP citations per 100 papers.

Three journals need a denominator Crossref can't supply in full:
  Philosophers' Imprint  Crossref has DOIs only from 2021, so the count is taken by hand (below).
  Phil. & Public Affairs Crossref is missing 1990-93; extrapolated at the 1994-2026 rate.
  American Phil. Quarterly  Crossref starts 2017; estimated at the 2017-25 rate back to 1990 (+/-15%).
Science is excluded (a general-science weekly, ~150k Crossref items in the window).
"""
import argparse, csv, json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('--classified', default=os.path.join(ROOT, 'output', 'classified.json'))
ap.add_argument('--out', default=os.path.join(ROOT, 'output', 'normalized_rankings_1990-2026.csv'))
args = ap.parse_args()

# Philosophers' Imprint, counted 2026-11-02.
# Vols 1-21 (2001-21): Michigan quod.lib archive, which numbers articles per volume with no gaps.
# Vols 22-26 (2022-26): the publisher's issue pages.
IMPRINT_BY_VOLUME = [4, 5, 4, 3, 7, 4, 9, 12, 12, 12, 18, 19, 24, 35, 35, 19, 25, 25, 54, 34, 36,
                     24, 29, 23, 52, 28]

cl = {r['journal']: r for r in json.load(open(args.classified))['journals']}
cites = [(r['journal'], int(r['sep_iep_citations_1990_2026']))
         for r in csv.DictReader(open(os.path.join(ROOT, 'data', 'citations.tsv')), delimiter='\t')]
raw_rank = {j: i for i, (j, _) in enumerate(cites, 1)}


def years(r, a, b):
    return sum(v for k, v in r['by_year'].items() if a <= int(k) <= b)


rows = []
for j, c in cites:
    if j == 'Science':
        continue
    rng, note = '', ''
    if j == "Philosophers' Imprint":
        n = sum(IMPRINT_BY_VOLUME)
        note = 'counted by hand from the journal archive (Crossref DOIs start 2021); all articles regardless of length'
    elif j == 'American Philosophical Quarterly':
        rate = years(cl[j], 2017, 2025) / 9
        n = round(rate * 37)
        rng = f'{100 * c / (n * 1.15):.0f}-{100 * c / (n * 0.85):.0f}'
        note = f'Crossref starts 2017; estimated at the 2017-25 rate ({rate:.0f}/yr) back to 1990, +/-15%'
    elif j == 'Philosophy and Public Affairs':
        n = round(cl[j]['kept'] * 37 / 33)
        note = '1990-93 missing from Crossref; extrapolated at the 1994-2026 rate'
    else:
        n = cl[j]['kept']
    if j == 'Analysis':
        note = 'lower page minimum (short-paper journal)'
    rows.append([j, c, n, 100 * c / n, rng, note])
rows.sort(key=lambda r: -r[3])

os.makedirs(os.path.dirname(args.out), exist_ok=True)
with open(args.out, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['norm_rank', 'raw_rank', 'journal', 'sep_iep_citations', 'papers_1990_2026',
                'citations_per_100_papers', 'range_if_estimated', 'note'])
    for i, (j, c, n, v, rng, note) in enumerate(rows, 1):
        w.writerow([i, raw_rank[j], j, c, n, f'{v:.1f}', rng, note])
    w.writerow(['', raw_rank['Science'], 'Science', dict(cites)['Science'], '', '', '',
                'excluded: general-science weekly'])
for i, (j, c, n, v, *_) in enumerate(rows, 1):
    print(f'{i:2d}  {j:46s} {c:5d} / {n:5d}  = {v:6.1f}')
