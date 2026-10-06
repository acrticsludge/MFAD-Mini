# CLAUDE.md

Engineering operating system for this repository. This file defines the default execution pipeline for the agent working here. Skills are the specialist execution layer; this file is the orchestration and quality-gate layer. Do not treat the skill library as a menu of optional advice.

> Turn a request into a verified, honest, reproducible mini-project artefact with the minimum necessary complexity.

Two rules outrank everything else here:

1. **This project is blocked.** The IPL reframe of Strang problem #5 is unapproved. See `AGENTS.md` §2. Never write project code before the instructor's answer is **recorded** — who gave it, when, and in what form — and confirmed in writing. A verbal answer is acceptable only once it is written down and confirmed. An inferred or unrecorded answer does not count.
2. **Numbers are measured, not asserted.** See `AGENTS.md` §4. Every count, rank, nullity and condition number must be computed by a test.

**Status: nothing is implemented.** The tree is `docs/`, three course PDFs, the extracted Cricsheet snapshot at `ipl_json/`, and these two files. No `src/`, no package manifest, no test runner. Stage 4 IMPLEMENT has not started.

---

# 1. Operating Mode

Whenever the user asks to implement, build, modify, fix, refactor, or prepare something, automatically run the appropriate pipeline.

Do NOT wait for the user to explicitly say "use skills", "make a plan", "write tests", "review this", or "check the data". Those are part of the default pipeline.

Do NOT blindly execute every installed skill. Classify the work first, then activate the relevant ones. Mandatory gates always run; specialist skills run when their trigger conditions apply.

The user should be able to say "Build the run-margin design matrix" and the full lifecycle should run without manually chaining skills.

---

# 2. Skill Stack

Only skills that plausibly apply to a Python numerical-analysis coursework project belong here.

**Define:** `using-agent-skills`, `interview-me`, `idea-refine`, `spec-driven-development`
**Plan:** `planning-and-task-breakdown`
**Build:** `context-engineering`, `source-driven-development`, `doubt-driven-development`, `test-driven-development`, `incremental-implementation`
**Verify and debug:** `debugging-and-error-recovery`
**Review:** `code-review-and-quality`, `code-simplification`
**Ship:** `git-workflow-and-versioning`, `documentation-and-adrs`

**Explicitly not used:** web performance, search visibility, marketing funnels, payment flows, authentication, database schemas, deployment targets, infrastructure. There is no product here and no server to harden. If a trigger suggests one, the trigger does not apply.

---

# 3. Systematic Debugging

For failures, bugs, unexpected numbers, broken tests, runtime errors, or regressions: **DO NOT PATCH THE SYMPTOM FIRST.**

```text
Reproduce → Gather evidence → Trace/localize → Form hypotheses
          → Test hypotheses → Identify root cause → Implement fix
          → Add regression protection → Verify
```

If three reasonable fix attempts fail, stop treating the problem as a local bug and reassess the mathematics or the data assumptions.

**The most common root cause in this repository is a wrong premise, not a wrong line of code.** When a number surprises you — a rank, a component count, a dimension mismatch — the first hypothesis to test is that a prior document's figure was wrong. Two such figures were already found the hard way.

---

# 4. MASTER PIPELINE

```text
USER REQUEST
     ↓
0. ORIENT / DISCOVER → 1. DEFINE → 2. ARCHITECT → 3. PLAN
     ↓
4. IMPLEMENT → 5. VERIFY → 6. HARDEN → 7. REVIEW
     ↓
8. PRODUCTIONIZE → 9. SHIP → 10. REPORT
```

A stage may activate multiple specialist skills. A stage may be skipped only when its trigger conditions genuinely do not apply, and the reason must be recorded in the final report.

**Stages 6, 8 and 9 have no deployment meaning in a 10-mark coursework project.** They are re-scoped below to provenance, demo preparation and commit hygiene. Do not inflate them into ceremony, and do not claim infrastructure work that did not happen.

---

# 5. STAGE 0 — ORIENT / DISCOVER

1. Inspect the repository.
2. Read `AGENTS.md` and `docs/reasonix/INDEX.md` — the index carries the open blocker and the lessons that cost real work.
3. Read the relevant spec and plan for this project under `docs/reasonix/`.
4. Inspect the code paths you are about to touch.
5. Classify: greenfield, brownfield, bugfix, or documentation-only.
6. Determine the blast radius and write it down.
7. **Check the blocker.** If the task is project code and the instructor's answer is not yet recorded — who, when, in what form — and confirmed in writing, stop and report the gate.
8. Identify relevant installed skills.

State the current state honestly. Never describe a stage as built when it is planned.

---

# 6. STAGE 1 — DEFINE

- The requirement is explicit, or the ambiguity was resolved by interview.
- Acceptance criteria are testable; non-goals are written down.
- The 11 mandated stages are mapped in the order given by the guidelines. A stage that is genuinely thin is named out loud, not hidden — but no gap is manufactured to appear rigorous, and no stage is padded with fake analysis to fill a slot.
- The design question is not already answered in print. If the authority publishes the coefficients you would recover by least squares, the fit is circular — pick a different question or say so.

---

# 7. STAGE 2 — ARCHITECT

- Choose the smallest structure that supports the 11 stages.
- Two models on two datasets is a legitimate architecture. One model needing an invented constant is not.
- Fix the canonicalisation map before any matrix is built. `n` depends on it.
- Record every decision that could reasonably have gone the other way.
- Verify the mathematics claims in `AGENTS.md` §6 before building on them.

---

# 8. STAGE 3 — PLAN

- Break the work into ordered, verifiable slices. Each slice ends green or is not finished.
- State which slice creates the test harness. Until a `pytest` gate exists, verification stages are not applicable and must not be recorded as passed.
- Write the plan to `docs/reasonix/plans/`.
- Respect `AGENTS.md` §10. Held items stay held.

---

# 9. STAGE 4 — IMPLEMENT

- Write the failing test first, then the fix.
- No code before the blocker is answered.
- Derive every count from the snapshot. Never hard-code one.
- The demo path must read the committed snapshot and never the network.
- Keep the maths visible in code and comments; the examiner reads the machinery, not the algebra.

---

# 10. STAGE 5 — VERIFY

Verification is evidence, not confidence. **In this project, verification means the number was computed, not asserted.**

```text
targeted test → module tests → full pytest suite → invariant tests
             → offline demo run → reproducibility check (run twice, identical)
```

```text
pytest tests/test_data_invariants.py -q
pytest tests/test_canonicalisation.py -q
pytest tests/test_design_matrix.py -q
pytest tests/test_structure.py -q
pytest -q
python -m iplranking.demo --offline
python -m iplranking.demo --offline   # again, compare output
```

The project lives under `ipl-power-ranking/`, with the package importable as `iplranking` and the tests as a sibling package:

```text
ipl-power-ranking/
  pyproject.toml
  src/iplranking/
  tests/test_data_invariants.py
  tests/test_canonicalisation.py
  tests/test_design_matrix.py
  tests/test_structure.py
```

Invariant tests matter most here. They pin the measured facts in `AGENTS.md` §3 against the actual snapshot, so a future agent cannot reintroduce the wrong numbers without a red test:

- match count is 1,243
- `n` is 15 after canonicalisation
- run-margin subset is 558, wicket-only is 660
- the win/loss graph has exactly 1 connected component
- `rank(A) == n - 1` and `nullity(A) == 1`

Do not report a stage as covered until the check that covers it has run.

---

# 11. STAGE 6 — HARDEN

Re-scoped for coursework. Hardening here means the demo cannot embarrass you.

**Offline demo check.** The demo runs with the network off, from a clean clone. No absolute paths, no machine-specific environment variables. Check the environment from a fresh shell, not from your own.

**Data provenance.** Source URL recorded. UTC retrieval date recorded. HTTP status recorded. SHA-256 of the downloaded archive recorded. Row count recorded and matched against the invariant test. The attribution states what was actually read from the primary source — do not assert a licence term that was not read there.

**Personal data.** No player names, email addresses, or personal identifiers in committed artefacts beyond what the public match files already contain. No staff directories, enrolment lists, or anything resembling personal data from an institutional source.

**Reproducibility.** Two clean runs give identical output. No unset random seeds where results depend on them. Fixed ordering everywhere iteration order could change results.

---

# 12. STAGE 7 — REVIEW

Run `code-review-and-quality` and `code-simplification`. For anything that changes a number, a rank, or a claimed result, additionally use `doubt-driven-development`.

Review for: correctness of the linear algebra; honesty of the claims; coverage of the 11 stages without fakery; reproducibility; legibility of the maths for an examiner who is not a specialist. Then simplify.

Treat an adversarial reviewer's findings as evidence, not verdict. One reviewer flagged a figure as fabricated that was merely stale. Do not "clean up" unrelated code or docs.

---

# 13. STAGE 8 — PRODUCTIONIZE

Re-scoped for coursework: this stage produces the artefacts the other five marks are graded on.

- Project report: written, honest, no overclaiming.
- Viva script: prepared, with the numbers that will be asked about — including the ones excluded, and why.
- Demo script: short enough for the time allowed, with a fallback for each step that could fail on stage.
- Figures produced by Matplotlib, saved deterministically.
- All 11 mandated stages are covered; any stage that turned out genuinely thin is named out loud rather than hidden. No gap is manufactured to appear rigorous.
- `documentation-and-adrs` for any decision expensive to revisit.

A demo that depends on the network, on a specific machine, or on a package the examiner does not have is not productionized.

---

# 14. STAGE 9 — SHIP

Use `git-workflow-and-versioning`. "SHIP" means committed and recoverable. There is nothing to deploy.

- Small atomic commits, imperative messages, on a branch — never straight on the default branch.
- Commit after a verified logical slice.
- Never commit secrets, generated figures, or scratch files.

**Commit before demo day, not on it.** A repository with no baseline commit and a thousand files staged but uncommitted is one failed `git status` away from losing the work. Establish the baseline commit early.

---

# 15. COURSEWORK READINESS GATE

A change is NOT "done" merely because it runs locally.

**Requirements** — [ ] blocker answered and recorded per `AGENTS.md` §2, with written confirmation obtained, or no project code written; [ ] acceptance criteria satisfied; non-goals respected; held items still held.

**Mathematics** — [ ] every stated number is computed by a test, not asserted in prose; [ ] `rank`, `nullity` and component counts computed from the snapshot; [ ] Col/Row space claims match `AGENTS.md` §6; [ ] least-squares and eigen routes presented as different models on different datasets, not as one reproducing the other.

**Stages** — [ ] all 11 mandated stages covered in the guidelines' order, and any stage not done honestly named out loud; [ ] no gap manufactured for appearance; [ ] no stage padded with a fake analysis.

**Data** — [ ] provenance complete: URL, UTC date, HTTP status, SHA-256, row count; [ ] licence statement matches what the primary source actually says; [ ] canonicalisation map yields `n = 15`; [ ] demo reads only the committed snapshot.

**Reproducibility** — [ ] full `pytest` suite green; [ ] offline demo run clean; [ ] two runs produce identical output.

**Honest accounting** — [ ] excluded matches counted and stated in the demo, not a footnote; [ ] no claim rests on an unmeasured assumption; [ ] no finding is already published.

**Documentation** — [ ] `docs/reasonix/INDEX.md` has a row for this run; [ ] docs describe the system that exists, not the one that was planned; [ ] `AGENTS.md` and `CLAUDE.md` agree with each other.

If a critical applicable item fails, do not claim ready.

---

# 16. QUALITY GATES ARE LOOPS

`FAIL → Diagnose → Fix → Re-run affected verification → Re-enter gate`

Do not continue past a failed critical gate merely because the remaining pipeline is easier to execute.

**A failed test is evidence. Never make it pass by deleting the assertion, adding a skip, or loosening the tolerance.** That is a hard stop, not a retry strategy — a gate that cannot fail stops being a gate.

---

# 17. RISK-BASED ESCALATION

**Small / low-risk** — fixing a doc line that contradicts `AGENTS.md`, renaming a local variable, adding one invariant test:
`orient → implement → verify → review`

**Medium** — building the run-margin design matrix, adding a canonicalisation test, writing a stage section:
`define → architect → plan → implement → verify → harden → review → ship`

**High-risk** — anything that changes a headline number, rank, or the divergence between the two models; changing the canonicalisation map, which changes `n` and every dimension; choosing which matches enter a design matrix; the held residual-SVD stretch variant or recency weighting, both explicitly out of scope. Additionally activate `doubt-driven-development`, `source-driven-development`, systematic debugging where relevant, and an independent re-measurement of every affected number.

Never trade correctness for speed on high-risk changes. When in doubt, re-measure.

---

# 18. PROJECT STACK

Accurate as of 2026-10-02. Verify against the repository before making technology assumptions.

**Data:** Cricsheet IPL JSON v1.2.0, extracted to `ipl_json/`, 1,243 match files. Provenance not yet recorded in this repository.

**Analysis:** Python 3 with NumPy for the linear algebra; Pandas for tabular joins and match-level filtering; Matplotlib for figures; pytest for the invariant tests that pin every measured number.

**Course documents:** the problem-statements PDF (the 14 problems), the guidelines PDF (the 11 mandated stages), and Strang's projects book, which is also the Python reference style to follow.

**Not present, and not to be introduced:** no web framework, no front end, no notebook server, no database, no deployment target, no CI configuration unless the demo genuinely needs it.

Do not introduce a technology because it is preferred personally. The Strang projects book is plain Python; match it.

---

# 19. CODING STANDARDS

- Python 3, typed where the type is informative.
- NumPy for linear algebra, not hand-rolled loops over matrices.
- Explicit matrix shapes, with a comment naming the shape.
- Keep the maths legible: the examiner reads this code.
- No magic numbers. Every dataset-derived constant is computed and named.
- Validate the shape of every matrix at the boundary where it is built.
- Seed anything stochastic; fix ordering where iteration could change results.
- Focused functions; no abstraction for a single call site.
- Errors must say which invariant failed and with what numbers.

---

# 20. SOURCE-OF-TRUTH RULE

When instructions disagree:

1. Prefer `AGENTS.md` — it holds the binding project facts.
2. Prefer the measured snapshot over any prose figure. If the snapshot contradicts this file or any doc, the snapshot wins and the doc is corrected.
3. Prefer the course PDFs over any inherited planning document.
4. Prefer the most task-specific specialist skill.
5. Prefer verified repository behavior over assumptions.
6. Resolve contradictions explicitly and record the resolution.

Never blindly merge conflicting instructions.

---

# 21. ANTI-RATIONALIZATION RULES

Never use these excuses.

> "I'll add tests later."
No. The invariant tests are the entire point of this project.

> "The rank is obviously n − 1."
Then compute it. Connectivity implies the rank; it does not prove the matrix was built correctly.

> "I'll just state the rank analytically, no need to compute it."
No. That is the exact failure this project has already paid for once. An asserted rank cannot be wrong, which means it cannot be a finding.

> "I'll convert wickets to runs so all 1,243 rows work."
No. That requires an invented constant. Two honest models on two datasets beat one dishonest model. The 558/660 split is the central constraint, not a defect to engineer around.

> "I'll merge Gujarat Lions into Gujarat Titans so the count looks cleaner."
No. That one merge alone takes `n` from 15 to 14 — both extra merges would take it to 13 — so `n` and every dimension change and every already-computed figure is invalidated. The merge set is deliberate and fixed.

> "The answer is published anyway, so the fit is fine."
If it is published, the fit is circular. Say so and pick a different question.

> "I'll add the stage analysis later to fill the gap."
No. There is no gap to fill — all 11 stages are covered. A faked stage is worse than an honest thin one, and manufacturing a gap to appear rigorous is its own dishonesty.

> "The existing doc is messy, so I'll rewrite it."
No. Smallest correct change unless a rewrite is the task.

> "Three fixes didn't work, I'll try another patch."
Stop. The premise is probably wrong. Re-measure.

---

# 22. DOCUMENTATION OUTPUT MAP

The repository has a canonical documentation tree. Treat it as the single home for agent-generated planning and reporting artifacts. Do NOT scatter generated Markdown across the root, random folders, or source directories.

**Canonical locations — these are the only documentation locations that exist:**

```text
docs/
└── reasonix/
    ├── INDEX.md          # run index: every run, the blocker, the lessons
    ├── specs/            # specifications
    ├── plans/            # implementation plans
    └── reports/          # reports and handoffs
```

**Routing:** a specification for work about to start → `specs/`; an ordered implementation plan → `plans/`; a run report or handoff → `reports/`; the run index including the blocker → `INDEX.md`; a measurement correction → the index's lessons list, plus the corrected fact in `AGENTS.md`.

Anything else — architecture overviews, decision records, design documents, audit reports — **may be created only when genuinely needed**, under a clear name, at the point the need arises. Do not pre-create empty directories to imply a documentation practice this repository does not have.

---

# 23. EXECUTION ARTIFACT RETENTION

`docs/reasonix/` is for agent execution artifacts: `specs/` for specifications useful to future agents or humans, `plans/` for the ordered plan a run intends to execute, `reports/` for what actually happened including partial progress, and `INDEX.md` for the one-row-per-run history.

A report states what happened, not what was intended. If a run stopped at a blocked gate, the report says blocked.

---

# 24. DOCUMENT NAMING

Use lowercase kebab-case, descriptive names, dates for historical records matching the existing convention, and zero-padded sequential numbers for anything numbered:

```text
2026-10-02-ipl-power-ranking-f1.md
2026-10-02-ipl-power-ranking-f1-handoff.md
0001-two-dataset-model-choice.md
```

Avoid `final.md`, `new.md`, `notes2.md`, `latest.md`, `stuff.md`, `temp.md`. Never create something like `plan-v2-final.md` without a meaningful reason.

---

# 25. DOCUMENT UPDATE RULES

When an implementation or a measurement invalidates existing documentation: identify the canonical document, update it as part of the same task, search for contradictory stale documentation when the change is mathematical or externally visible, and do not leave two documents describing different realities.

Documentation must describe the system that actually exists. Do not document planned behavior as implemented behavior.

Use explicit status labels: Proposed, In Progress, Implemented, Deprecated, Superseded. A superseded run stays in the index marked superseded — never rewrite history, because the fact that a run happened and was wrong is part of what the next agent needs.

---

# 26. DOCUMENTATION QUALITY GATE

- [ ] The index has a row for this run, with the stage actually reached.
- [ ] Facts measured are labelled as measured, with a date.
- [ ] Facts assumed are labelled as assumed, or eliminated.
- [ ] Blocked is recorded as blocked, not as "pending review".
- [ ] Nothing claims behavior the code does not provide.
- [ ] Every franchise, count and rank matches `AGENTS.md`.
- [ ] No licence claim exceeds what the primary source states.

---

# 27. AI CONFIG SYNCHRONIZATION

This repository intentionally maintains two agent instruction files. Keep them synchronized when changing project-wide rules:

- `AGENTS.md` — binding project facts and prohibitions
- `CLAUDE.md` — process, pipeline and quality gates

They must agree on the stack, the blocker, the honesty rules, the docs locations, and the scope discipline. If they disagree, the disagreement is a bug. Fix it in both files in the same change.

Do not blindly overwrite one to match the other. Each has a distinct role: `AGENTS.md` says what is true and what is forbidden; this file says how work runs. Preserve each structure while keeping the shared facts identical.

---

# 28. FINAL RESPONSE CONTRACT

**Implemented.** What changed, one line per change. Say "nothing implemented, blocked at the gate" when that is the truth.

**Skills activated.** Only the meaningful ones actually used.

**Verification.** Exact checks run and their real results. Never a summary of intent. If a number is quoted, the check that computed it is named.

```text
pytest -q                                    42 passed
python -m iplranking.demo --offline          ok, figures written
rerun of the same command                    identical output
measured: n=15, run-margin rows=558,
          wicket-only rows=660, components=1
```

**Blockers.** Anything unresolved. Include the instructor question if still open.

**Remaining risks.** Anything intentionally not verified, plus known limitations.

**Coursework status.** Use exactly one of:

```text
READY FOR DEMO AND VIVA
```

or

```text
NOT READY — <the failing gate>
```

Never say ready while the blocker is open or a critical applicable gate is unresolved.

---

# 29. THE ONE-LINE RULE

The user should be able to say "Build the run-margin design matrix" and the agent should automatically:

```text
understand → specify → architect → plan → implement
  → test → debug → review → document → commit
```

while activating the installed skills that actually apply to a Python numerical project.

The objective is not maximum process. It is maximum verified, reproducible, honest output with minimum unnecessary work.