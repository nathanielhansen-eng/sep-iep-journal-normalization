import csv,os
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
"""Bar chart of output/normalized_rankings_1990-2026.csv -> output/normalized_rankings_1990-2026.png (needs matplotlib)."""
D=os.path.join(os.path.dirname(os.path.abspath(__file__)),'output')
rows=[r for r in csv.reader(open(f'{D}/normalized_rankings_1990-2026.csv'))][1:]
rows=[r for r in rows if r[0]]
SURF,INK,INK2,BLUE='#fcfcfb','#0b0b0b','#52514e','#2a78d6'
plt.rcParams['font.family']=['Helvetica Neue','Helvetica','Arial','DejaVu Sans']
fig=plt.figure(figsize=(10.8,13.5),dpi=100,facecolor=SURF)
ax=fig.add_axes([0.40,0.115,0.53,0.77],facecolor=SURF)
n=len(rows); vmax=max(float(r[5]) for r in rows)
for i,r in enumerate(rows):
    y=n-1-i; v=float(r[5]); est=bool(r[6])
    ax.add_patch(FancyBboxPatch((0,y-0.32),v,0.64,boxstyle="round,pad=0,rounding_size=0.25",fc=BLUE,ec='none',mutation_aspect=0.6))
    ax.text(v+1.2,y,f"{v:.0f}{'*' if est else ''}",va='center',ha='left',fontsize=12.5,color=INK)
    name=r[2].replace('Philosophy and Phenomenological Research','Phil. & Phenomenological Research').replace('British Journal for the Philosophy of Science','British J. for the Philosophy of Science').replace('Journal of Aesthetics and Art Criticism','J. of Aesthetics & Art Criticism').replace('Philosophy and Public Affairs','Philosophy & Public Affairs').replace('Nous','Noûs')
    ax.text(-2,y,f"{int(r[0]):>2}.  {name}",va='center',ha='right',fontsize=12.5,color=INK)
    delta=int(r[1])-int(r[0])
    tag=f"▲{delta}" if delta>0 else (f"▼{-delta}" if delta<0 else "–")
    ax.text(vmax*1.13+8,y,f"{r[1]}",va='center',ha='center',fontsize=11.5,color=INK2)
    ax.text(vmax*1.13+17,y,tag,va='center',ha='center',fontsize=11,color=INK2)
ax.text(vmax*1.13+12.5,n-0.1,"raw rank",ha='center',va='bottom',fontsize=10.5,color=INK2)
ax.set_xlim(0,vmax*1.13+21); ax.set_ylim(-0.7,n-0.3)
for s in ax.spines.values(): s.set_visible(False)
ax.set_xticks([]); ax.set_yticks([])
fig.text(0.04,0.955,"Which philosophy journals' papers get cited most in the SEP and IEP?",fontsize=19,weight='bold',color=INK)
fig.text(0.04,0.928,"Citations per 100 research papers published, 1990–2026  ·  top 29 journals by raw citation count",fontsize=13.5,color=INK2)
fig.text(0.04,0.03,"Citations: SEP + IEP references to papers from 1990–2026, from “Journal Citation Rankings in Philosophy” (Oct 2026).\n"
         "Papers: Crossref journal articles 1990–2026, excluding book reviews, front matter, errata, duplicate DOIs and items under 10 pages (2 for Analysis). Science excluded.\n"
         "* APQ paper count estimated (Crossref starts 2017), ±15%. Older papers have had longer to be cited.",
         fontsize=9.5,color=INK2,va='bottom',linespacing=1.5)
fig.savefig(f'{D}/normalized_rankings_1990-2026.png',facecolor=SURF)
