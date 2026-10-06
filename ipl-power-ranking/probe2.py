import numpy as np, pandas as pd, sys
sys.path.insert(0,"src")
from iplranking.data import build_systems
from iplranking import models, diagnostics as dg
s = build_systems()
A,b = s.A, s.b
fit = models.massey(A,b); pred = A@fit.x
f = s.matches
run = f[f["margin_runs"].notna() & f["winner"].notna()]
print("run rows:", len(run))
t1won = (run["winner"].astype(str).to_numpy() == run["canonical_team1"].astype(str).to_numpy())
print("team1 wins:", int(t1won.sum()), "share:", repr(float(t1won.mean())))
print("model acc:", repr(dg.winner_accuracy(pred,b)), dg.winner_accuracy(pred,b)==307/558)
# majority_class_accuracy on same convention
same = float(np.mean(np.sign(pred)==np.where(t1won,1.0,-1.0)))
print("majority-class-scored acc:", repr(same))
# per season
tab = pd.DataFrame({"season": run["season"].astype(str).to_numpy(), "t1": t1won})
g = tab.groupby("season", sort=True)["t1"].agg(["sum","count"])
g["share"]=g["sum"]/g["count"]
print(g.to_string())
print()
print("share of labelled b>0 :", repr(float((b>0).mean())))
print("all-decided team1 share:", end=" ")
dec = f[f["winner"].notna()]
t2 = (dec["winner"].astype(str).to_numpy()==dec["canonical_team1"].astype(str).to_numpy())
print(repr(float(t2.mean())), int(t2.sum()), len(dec))
# held-out share
held = models.held_out_fit(s.matches, s.teams, 3)
print("held test acc:", held.accuracy, "rmse", held.rmse, "base", held.baseline_rmse)
# ridge
for lam in (0.0,1.0,10.0,50.0,200.0,1000.0):
    xs = models.ridge(A,b,lam)
    print(f"lam {lam:8g}  R2c={dg.r_squared(b, A@xs, centred=True):.4f}  max|x|={float(np.abs(xs).max()):.2f} ||x||={float(np.linalg.norm(xs)):.2f}")
