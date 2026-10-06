import numpy as np, pandas as pd
import sys
sys.path.insert(0, "src")
from iplranking.data import build_systems, load_matches
from iplranking import models, diagnostics as dg

s = build_systems()
A, b = s.A, s.b
fit = models.massey(A, b)
x = fit.x
pred = A @ x
m = A.shape[0]
print("mean(b)          =", repr(float(b.mean())))
print("mean(A x_hat)    =", repr(float(pred.mean())))
print("std(b)           =", repr(float(b.std())), " (ddof=0)")
print("std(b, ddof=1)   =", repr(float(b.std(ddof=1))))
print("std(x)           =", repr(float(x.std())))
print("resid spread ||r||/sqrt(m) =", repr(float(np.linalg.norm(fit.resid)/np.sqrt(m))))
print("fitted spread std(A x_hat)=", repr(float(pred.std())))
print("ratio                      =", repr(float((np.linalg.norm(fit.resid)/np.sqrt(m))/pred.std())))
print("||r||/||Ax|| =", repr(float(np.linalg.norm(fit.resid)/np.linalg.norm(pred))))

# intercept model
A1 = np.hstack([A, np.ones((m,1))])
sol, *_ = np.linalg.lstsq(A1, b, rcond=None)
intercept = float(sol[-1]); xa = sol[:-1]
fitted1 = A1 @ sol
ss_res1 = float(np.sum((b-fitted1)**2))
r2c1 = dg.r_squared(b, fitted1, centred=True)
r2u1 = dg.r_squared(b, fitted1, centred=False)
print()
print("intercept      =", repr(intercept))
print("x_intercept spread:", repr(float(xa.std())))
print("ss_res_int     =", repr(ss_res1))
print("r2 centred int =", repr(r2c1))
print("r2 uncentred int =", repr(r2u1))
print("mean(b)-mean(Ax) =", repr(float(b.mean()-pred.mean())))
print("sum(x_int) =", repr(float(xa.sum())))
print("max|x_int - x_ols - c| ... ")
d = xa - (x - x.mean())
print("  max abs diff after gauge:", repr(float(np.abs(d).max())))
