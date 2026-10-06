import numpy as np, pandas as pd, sys
sys.path.insert(0,"src")
from iplranking.data import build_systems
from iplranking.canon import canonical
s = build_systems()
A,b = s.A, s.b
f = s.matches
run = f[f["margin_runs"].notna() & f["winner"].notna()].reset_index(drop=True)
raw_t1 = (run["winner"].astype(str) == run["canonical_team1"].astype(str)).to_numpy()
can_t1 = (run["winner"].astype(str).map(canonical) == run["canonical_team1"].astype(str)).to_numpy()
canon_team1_from_raw = run["team1"].astype(str).map(canonical).to_numpy()
can_t1b = (run["winner"].astype(str).map(canonical) == canon_team1_from_raw).to_numpy()
print("raw winner == canonical_team1 :", int(raw_t1.sum()))
print("canonical(winner)==canonical_team1:", int(can_t1.sum()), int(can_t1b.sum()))
print("sign(b)>0 count:", int((b>0).sum()))
print("agree can_t1 vs sign(b):", bool(np.all(can_t1.astype(int)==(b>0).astype(int))))
print("agree raw_t1 vs sign(b):", bool(np.all(raw_t1.astype(int)==(b>0).astype(int))))
# where do they differ?
diff = np.flatnonzero(raw_t1.astype(int)!=(b>0).astype(int))
print("n diff:", diff.size)
sub = run.iloc[diff]
print(sub[["season","team1","team2","winner","canonical_team1","canonical_team2"]].head(12).to_string())
