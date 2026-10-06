# Manual checklist — what the code cannot do for you

- **Slug:** `2026-10-04-ipl-power-ranking-visual-build`
- **Generated:** 2026-10-05
- **Same list appears at the end of `report/report.html` and in `README.md`.**

Everything the code can do is done and verified: **235 tests pass**, the demo runs
offline from a clean clone with no install step, and two runs produce byte-identical
figures and page. The six items below are the remainder, and **item 1 gates the rest.**

---

## 1. Ask the instructor the blocker question — GATING

Has never been answered, across four runs. No instructor contact is recorded
anywhere in this repository.

> Strang problem 5 in the projects book is *"Linear equations + college football
> team ranking."* May I keep Strang's mathematics and rank **IPL** teams instead,
> using the mandated 11-stage LA workflow and the 1,243-match Cricsheet dataset?
> Or must I submit the book's task list on college football data?

**If the answer is "the book's task list is mandatory":** the IPL reframe is not
permitted, the dataset advantage that made this problem choice the strongest pick
disappears, and this code should be **discarded, not adapted**. The pick reopens,
and choosing the next candidate is a deliberate decision — do not drift into it.

**Record the answer in `docs/reasonix/` — who gave it, when, in what form.** A
written reply (email or message) is preferred. A verbal answer must be recorded
immediately *and* confirmed in writing before you rely on it. `AGENTS.md` §2: the
gate is the **recording**, not the medium, and an inferred answer does not count.

Why the code exists anyway: the question is a five-minute conversation, and asking
it with a working demo, a measured result and 235 green tests in hand is worth
more than asking it cold.

## 2. State the licence position exactly as read

The demo and the report assert **no licence term**. Cricsheet's primary site
carries no licence statement for the match data and its licence path returns 404;
four third-party sites assert ODC-BY 1.0, which is corroboration, not the primary
source. If asked in the viva, say exactly that — do not upgrade it to "ODC-BY"
for a cleaner answer. The full worded position is in `data/provenance.json` and in
the report's provenance block.

## 3. Rebuild the snapshot once and check the hash

```text
python ipl-power-ranking/scripts/build_snapshot.py
```

Compare the reported manifest hash against `sha256` in `data/provenance.json`.
This proves the hash is reproducible rather than pasted, and it is the same check
the invariant tests make. Note what the hash *covers*: the archive
(`ipl_json.zip`) was not retained on this machine, so the hash is of a
**deterministic manifest of the extracted files**, and `sha256_covers` says so.

## 4. Rehearse these two viva answers

Both are places where the project was wrong before review and is now right. A
sharp examiner will find them, so have them ready.

- *"Your margin model is worse than predicting a constant. Why?"*
  Because `A @ 1 = 0` exactly — the design matrix has no intercept and cannot have
  one, so `A x` has mean zero while the data's mean margin is **+18.04 runs**. The
  fit sits **17.30 runs low on every match** by construction. Add the constant
  column it was never allowed and centred `R²` goes from **−0.2103** to
  **+0.0181** — a real improvement and still no signal. Stage 4's rank deficiency
  and stage 8's negative `R²` are the same fact.
- *"You report 55% winner accuracy. Isn't that better than chance?"*
  Chance is the wrong comparator. The majority-class baseline is **77.96%** — the
  first-listed team won 435 of the 558 run-margin matches — so 55.02% is
  **negative skill**. And the held-out split is degenerate: the first-listed team
  won 100% of run-margin matches in **every** season from 2018 onward, so the
  43.2% held-out figure is not a clean out-of-sample estimate and is reported with
  that caveat attached.

## 5. Decide the official-table basis and say it out loud

The demo compares against the **all-time** table, 2 points per win, across all 19
seasons, tied matches excluded because they have no `winner`. That is a choice,
not the only choice. If the viva expects a specific season, decide before the
demo and state the basis in the first minute rather than being asked.

## 6. Close the loop in the documentation

Record the released answer — or the reopen decision — in `docs/reasonix/`, and add
the run row to `docs/reasonix/INDEX.md`. Do not rewrite history in that table: a
superseded run stays, marked superseded, because the fact that it happened is part
of the record.

---

## Not on this list, deliberately

- **Recency weighting** — a named "what next", not part of this deliverable
  (`AGENTS.md` §10, spec §D4).
- **The residual-SVD stretch variant** — held on purpose (`AGENTS.md` §10).
- **The wicket→run conversion** — refused on integrity grounds. An invented
  runs-per-wicket constant in the middle of a linear-algebra project is a viva
  loss, and two honest models on two datasets beat one dishonest model.
