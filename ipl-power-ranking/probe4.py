import numpy as np, pandas as pd, sys
sys.path.insert(0,"src")
from iplranking.data import build_systems
from iplranking.canon import canonical
s = build_systems()
A,b=s.A,s.b
f=s.matches
run = f[f["margin_runs"].notna() & f["winner"].notna()].reset_index(drop=True)
raw = (run["winner"].astype(str)==run["canonical_team1"].astype(str)).to_numpy().astype(int)
can = (run["winner"].astype(str).map(canonical)==run["canonical_team1"].astype(str)).to_numpy().astype(int)
tab=pd.DataFrame({"season":run["season"].astype(str).to_numpy(),"raw":raw,"can":can})
g=tab.groupby("season",sort=True).agg(n=("can","size"),raw=("raw","sum"),can=("can","sum"))
g["raw_share"]=(g["raw"]/g["n"]).round(3); g["can_share"]=(g["can"]/g["n"]).round(3)
print(g.to_string())
print()
print("total raw:",int(raw.sum()),"-> ",repr(raw.sum()/len(raw)), " total can:",int(can.sum()),"-> ",repr(can.sum()/len(can)))
print("sign(b)>0:",int((b>0).sum()),"->",repr(float((b>0).mean())))
print()
print("held-out seasons (canonical):")
sub=run[run["season"].astype(str).isin(["2024","2025","2026"])]
c2=(sub["winner"].astype(str).map(canonical)==sub["canonical_team1"].astype(str))
print("  n=",len(sub)," team1 wins=",int(c2.sum())," share=",repr(float(c2.mean())))
r2=(sub["winner"].astype(str)==sub["canonical_team1"].astype(str))
print("  raw-string count=",int(r2.sum()))
