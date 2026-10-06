# Handoff — F1 IPL power ranking

- **Slug:** 2026-10-02-ipl-power-ranking-f1
- **Stage reached:** 3 PLAN. Nothing implemented. No code written.
- **Why this file exists:** the next session should not have to re-fetch the dataset, re-discover the two errors in the inherited shortlist, or re-derive the run-margin problem.

## 1. What was actually verified, and by whom

One read-only gather node, 2026-10-02, against `https://cricsheet.org/downloads/ipl_json.zip` (5,180,977 bytes). Extracted to OS temp only; nothing was written into this repo. Numbers below are **measured**, not recalled.

| Fact | Value | Status |
|---|---|---|
| Total matches | 1,243 | Confirmed — the prior run was right about this |
| Distinct team-name strings | 19 | New — prior run said "10 unknowns" |
| Canonical franchises | 15 (14 merging Deccan→SRH) | New |
| Winner present | 1,218 | New |
| Tied, no `winner` field | 16 (all Super Over via `outcome.eliminator`) | New |
| `"no result"` | 9 | New |
| **Run margin available** | **558** | New — the central constraint |
| Wicket margin only | 660 | New |
| Margin sign | **unsigned** | New |
| `info.outcome.method == "D/L"` | 23 | New — field is at `info.outcome.method`, not `info.method` (never present) |
| Win/loss graph components | **1**, for the full graph and every **modelling** subset | **CORRECTED.** The gather node first reported "in every subset", which is false: a random 30-match subset disconnects in 18 of 200 trials, and the first 5 matches give 3 components. Connectivity 1 holds for all-winner, run-margin, wicket-only and per-season subsets, which is all that the rank argument needs. |
| Seasons present | 19, from 2007/08 to 2026 | New — but `info["season"]` is int or str, so a naive `len(set(...))` returns **24**. Normalise before counting. |
| Match-data licence on cricsheet.org | **NOT FOUND** | Weakens the prior run's "ODC-BY" |

### Per-season squad size — where "10 unknowns" came from

2007/08 through 2021 mostly field **8** teams. 2022 onward field **10**. The shortlist's "10 unknowns" is one recent season's squad size mistaken for the franchise count. The pipeline has **15** unknowns.

### The trap in the raw names

`Rising Pune Supergiants` (2016) and `Rising Pune Supergiant` (2017) are **two distinct strings for one franchise** — it dropped the "s" mid-run. Left unmerged, this silently invents a 16th unknown with almost no data.

Also present and not in most people's list: `Gujarat Lions` (2016–2017, pre-Titans).

### A false assumption that is easy to carry in

"Deccan Chargers / Rajasthan Royals became Mumbai Indians in 2011" is **false**. Mumbai Indians appears in all 19 seasons. Deccan ends 2012, Sunrisers begins 2013. Do not write this into the canonicalisation map.

## 2. The two corrections to the inherited shortlist

Recorded because the INDEX lesson is *verify the replacement, not just the original*, and both of these would have been caught by an examiner.

1. **"10 unknowns" is wrong.** It is 15. The shortlist's own demo script — "1,243 matches, 10 unknowns" — would have been corrected mid-sentence.
2. **"QR of A gives an orthonormal basis of the row space" is wrong.** With `A` at `558 × 15`, thin QR yields `Q` of shape `m × n`, but `rank(A) = 14`, so `Col(Q)` is 15-dimensional while `Col(A)` is 14-dimensional — `Q`'s columns span a space *containing* `Col(A)`, and are certainly not a basis of `Row(A) ⊆ R¹⁵`. Two different spaces; two orthogonalizations.

The shortlist also said the eigen route should **reproduce** the least-squares fit. It will not: `AᵀA x = Aᵀb` has a right-hand side, the eigenvector problem does not, and they run on different datasets. The shortlist is withdrawn on that point too.

## 3. Still unverified — carry these forward

- **The blocker.** Whether dataset substitution is permitted. Open through two prior runs and this one. Spec §0. Nothing gets built until it is answered.
- **`numpy.linalg.qr` behaviour on this rank-deficient `A`.** Whether it produces rank-revealing `Q`, and which leading columns span `Col(A)`. Deferred to code in plan step 8, not asserted here.
- **Match-data licence.** No statement found anywhere on cricsheet.org; no `/licence/` page. Four third-party sites assert ODC-BY 1.0. Corroboration, not proof. Attribute precisely; do not assert the licence term.
- **`"no result"` vs `"abandoned"`.** The schema has no `abandoned` value. Cannot separate them.
- **Deccan→Sunrisers merge.** Defensible (2013 franchise sale) but a judgement call. Flagged for a sensitivity check, not silently applied.
- **Stage 7 not green from the prior run.** Two reviews on the PESU shortlist returned `blocked`; the fixes were never re-reviewed. That was about a different candidate, but it is the reason this plan front-loads tests and the margin decision instead of trusting prose.

## 4. Repo state — a trap for the next session

**CORRECTED 2026-10-02 later the same day.** The first version of this section was wrong. Stage 0 concluded "tree is `docs/` plus four PDFs, no `.git`" from a single glob. An implementer re-measured and found otherwise. Verified:

- **`AGENTS.md` and `CLAUDE.md` described PESDac** (Astro 6, React 19, Meta Astryx, FastAPI, Neon, BetterAuth). None of it existed. **Both were rewritten this run** — `AGENTS.md` now holds binding facts and prohibitions, `CLAUDE.md` the process and gates. Do not reintroduce web-stack content.
- **`ipl_json/` already exists** — 1,243 extracted Cricsheet JSON files plus the archive's `README.txt`, which independently states "This archive contains 1243 Indian Premier League matches." The raw snapshot needs no downloading. Only its **provenance record** is missing.
- **`.git` exists** on branch `main` with **zero commits**, ~1,258 entries staged, and **no `.gitignore`**. The whole project is uncommitted and unrecoverable until a baseline commit is made.

Why this matters: three documents written earlier in this run (the spec, the plan, and this handoff) carried the wrong inventory, and one of them — the plan — instructed a `git init && git add -A`, which against this tree would have staged 1,244 data files and any virtualenv. All are corrected now.

**Lesson recorded in `INDEX.md`:** a search tool returning implausibly little is a finding, not a clean bill of health. Corroborate an inventory claim with a second mechanism before writing it into a binding rules file.

Also: with no test runner in the tree, stage 5 VERIFY is genuinely not applicable on documentation-only work. Do not record a pass. `pytest` arrives in plan step 2, and the gate becomes real at that point.

## 5. Where to pick up

Read in this order:

1. This file
2. **`reports/2026-10-02-ipl-power-ranking-f1-build-audit.md`** — the end-to-end runbook, with manual-vs-AI designation per step, and the feasibility-probe numbers that changed the design
3. `specs/2026-10-02-ipl-power-ranking-f1.md` — especially §0 (blocker), §3 (the two corrections), §4 (modelling decisions, incl. D1 as revised by the probe)
4. `plans/2026-10-02-ipl-power-ranking-f1.md` — start at step 1

**Step 1 is a question to the instructor, not a command.** Nothing else starts until it is answered.

## 6. The probe result you must not skip

A feasibility probe run on 2026-10-02 measured the actual pipeline before any code was written. It inverted the project's framing:

```text
Massey least squares (558 × 15):  R² = 0.0214,  winner accuracy 55.0%
Colley eigenvector  (1218 × 15):  Perron-Frobenius positivity confirmed
Spearman(Massey, Colley) = 0.000
```

The margin model is topped by Kochi Tuskers Kerala, a franchise that existed for **one season**, and bottomed by Gujarat Lions, which existed for two. **The obvious approach does not work, and that is the project's actual finding.** Read build-audit Part 1 before writing any code.
