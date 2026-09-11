# SIF Sentinel — Session Handoff

**Date:** 2026-09-11
**Project:** SIF Sentinel (SIH 2026, challenge SIH26165 — Oil India SIF Precursor Engine)
**Repo root on user's machine:** `C:\Users\paras\Documents\sih\sif-sentinel\`
**Attached Claude project:** `sih` (docs: `claude/FRONTEND_V2_PLAN.md`, `claude/BUILD_STATUS.md`, `claude/CODEBASE_BUNDLE.md`)

---

## TL;DR for the next AI

The app **now runs** locally via `docker compose up` (from `infra/`) and serves at
**http://localhost:8000**. The frontend loads, the India basemap renders, the API +
Postgres + worker are all healthy, and the worker classifies the 10 seeded demo
reports successfully.

**The remaining problem is DATA SHAPE / AGGREGATION, not infrastructure.** The pages
are wired to the live backend, but the backend's insights + spatial layers don't
match what the classifier actually writes, so the UI shows placeholder/garbage values
instead of the rich data the mockups had. Three concrete bugs, all diagnosed below.

**Do NOT** re-investigate docker, the static-file mount, api.js, or CORS — those are
fixed and verified. Go straight to the three data bugs.

---

## Environment constraints (important)

- **The user is on Windows.** A Windows update (~Sept 8) broke the Cowork workspace's
  ability to *mount* the user's folder, so `device_bash` (a shell on the user's
  machine) **fails** with "no Plan9 drive shares mounted". You CANNOT run commands on
  the user's machine. You CAN still read/write their files via
  `device_list_dir` / `device_stage_files` / `device_commit_files`. Plan around this:
  edit files in the cloud, commit them back, and have the *user* run `docker compose`.
- The **cloud sandbox has no Docker daemon** (client only) — you can't `docker compose
  up` in the cloud. But it DOES have Python 3.11, Postgres 16 binaries, and all
  backend deps, so you can reproduce the backend end-to-end in the cloud by running
  `uvicorn` + a local Postgres cluster (that's how the bugs below were confirmed). See
  "How to reproduce locally in the cloud" at the bottom.
- Cloud egress blocks `unpkg.com` (D3/topojson) and Google Fonts — so cloud
  screenshots show fallback fonts and no basemap. On the user's real machine these
  CDNs load fine (their latest screenshots prove the basemap renders).

---

## Architecture (as-built)

Static multi-page frontend (vanilla HTML/CSS/JS — NOT Next.js), served **by the
FastAPI backend itself** from the same origin.

```
services/backend/    FastAPI + async SQLAlchemy + Postgres 16 + polling worker
  app/main.py        mounts /api/v1 AND StaticFiles at "/" (frontend)
  app/api/v1/        health, datasets, reports, imports, insights, lab
  app/analysis/      adapter → pipeline → policy (the Luck Test engine)
  app/services/      report_service, insights_service, import_service
  app/worker/        polling worker that runs analysis jobs
  app/cli/seed.py    10 demo Oil India reports
  migrations/        alembic (001_initial_schema — 14 tables)
services/frontend/   index.html (Spatial), insights.html, evidence.html,
                     import.html, lab.html + css/sentinel.css + js/{api,insights,spatial}.js
infra/docker-compose.yml   postgres + api + worker
safety/site_coordinates.yaml   7 sites w/ lon/lat for the map
```

Design system (the user built this, DO NOT redesign): glassmorphic "Pattern
Observatory" — paper `#f2f0ec`, violet `#5b3df5`, Space Grotesk + IBM Plex Mono,
gradient blobs + grain.

`MODEL_PROVIDER=fixture` in the demo → the **FixtureAdapter** classifies via keyword
regex (deterministic, no LLM). This is intentional for the demo. It works: it extracts
hazards (gravity/pressure/mechanical/electrical/fire_explosion/toxic_asphyxiation/
vehicle), exposure, and control-failure/success signals.

---

## What was fixed THIS session (verified working — don't redo)

1. **`services/frontend/js/api.js`** — was corrupted (template literals stripped, invalid
   JS). Rewrote it correctly. Also fixed `getSpatialOverview()` to call
   `/insights/spatial` (was calling a non-existent top-level `/spatial`). ✅ committed.

2. **`infra/docker-compose.yml`** — added a mount so the API can serve the static
   frontend. `app/main.py` resolves the frontend dir as `<app/app>/../../frontend`
   which is **`/frontend`** inside the container (only `backend` is mounted at `/app`).
   The mount is now `../services/frontend:/frontend`. ✅ committed & verified — the app
   boots clean now. (Earlier I wrongly used `/app/frontend` and the API crashed with
   `RuntimeError: Directory '/app/app/../../frontend' does not exist` — that's fixed.)

3. Cross-page nav hrefs and the new **evidence.html** (Evidence Graph page) were
   integrated in a prior session; those are fine.

---

## THE CURRENT PROBLEM — three data bugs

The user's latest screenshots (Spatial + Insights running on live Docker) show:
- Spatial: **"0 assets · 0 reports"**, "Unmapped assets 2", "Unassigned reports 1",
  empty map with "NO MATCHING REPORTS".
- Insights: every row's activity/exposure/control literally reads **"Activity /
  Exposure / Control"** (placeholders), hazards show as raw enum keys (`pressure`,
  `gravity`, `fire_explosion`, `toxic_asphyxiat…`), and the footer shows broken math:
  **"HUMAN-REVIEW COVERAGE 61 of 10 · 610%"**, **"UNRESOLVED 44"** — against only 10 reports.

### Bug 1 — Spatial: site names don't match, and compute_spatial is a stub

`app/services/insights_service.py::compute_spatial()` (lines ~221-255):
- It builds `assets` ONLY from `safety/site_coordinates.yaml` and **hardcodes
  `review/gaps/total = 0`** for every asset. It never queries reports or joins them to
  sites. Comment even says "This is a mock implementation for the demo."
- Worse, the YAML site `short` values (`Naharkatiya`, `Moran`, `OIL-D-12`, `Kumchai`,
  `Jorhat`, `SY-03`, `Jaisalmer`) **do not match** the seed's `supplied_site` values
  (`Naharkatiya Drilling Site`, `Moran Processing Plant`, `Duliajan Field`,
  `Digboi Refinery`, `Jorhat Pipeline Corridor`, `Geleki Gas Collection Station`,
  `Rupsi Helibase`, `Jaisalmer` not present at all). So even a proper join would map
  almost nothing.
- Also: the map shows "0 ASSETS" even though the YAML has 7 sites — check whether the
  YAML path resolves inside the container. `compute_spatial` opens
  `os.path.dirname(__file__)/../../../safety/site_coordinates.yaml`. From
  `/app/app/services/` that's `/app/safety/...`, but `safety/` is NOT mounted into the
  container (only `services/backend` → `/app` and `services/frontend` → `/frontend`).
  **So the YAML almost certainly isn't found → `except:` swallows it → 0 assets.**
  This is the same class of path/mount bug as the frontend one.

**Fix direction:**
  (a) Mount `safety/` into the container (e.g. `../safety:/app/safety` in the api
      service) OR bake it into the image, so the YAML is found.
  (b) Rewrite `compute_spatial` to actually query reports grouped by site, join to
      coordinates, and populate `review/gaps/total`. Reports that match a coordinate →
      `assets`; reports whose site has no coordinate → `unmapped`.
  (c) Reconcile site names: either update `site_coordinates.yaml` `short`/`name` to the
      8 real seed sites (Duliajan Field, Moran Processing Plant, Naharkatiya Drilling
      Site, Digboi Refinery, Jorhat Pipeline Corridor, Geleki Gas Collection Station,
      Rupsi Helibase, + a matcher), or add a site→coord alias map. Get lon/lat for the
      real Assam/Upper-Assam sites (Duliajan ~27.37/95.32, Digboi ~27.39/95.62,
      Geleki ~26.9/94.6, Rupsi ~26.14/89.9, etc. — verify before shipping).

Confirmed `GET /api/v1/insights/spatial` returns `{"assets":[],"unmapped":[]}` in the
cloud repro — consistent with the YAML not being found.

### Bug 2 — Insights: "Activity / Exposure / Control" placeholders + coverage math

Two sub-problems:

**(2a) The fixture adapter never produces activity / exposure-object / control-concept
strings.** The frontend's pattern rows expect ACTIVITY / HAZARD / EXPOSURE / CONTROL
CONCEPT / REPORTED STATE. The pipeline builds `facts` (HazardFinding) with
`hazard_kind` and `controls[].state`, but there is **no "activity", no "exposure area",
no "control concept"** field — so the frontend falls back to the literal words
"Activity"/"Exposure"/"Control". The mockup's rich labels ("Maintenance / Electrical
energy / Worker performing intervention / Isolation / Effectiveness not established")
were **demo constants baked into the mockup**, never produced by this backend.

  → Decide: either (i) extend the fixture adapter + pipeline + schema to extract/emit
    `activity`, `exposure_area`, `control_concept`, `reported_state` per fact, and have
    `compute_patterns` group on those; or (ii) accept the coarser real labels (hazard +
    control_state) and update the frontend copy so it stops showing placeholder words.
    Option (i) matches the mockup; more work. Check `app/schemas/analysis.py`
    (HazardFinding) and `compute_patterns` in insights_service.py.

**(2b) `compute_patterns` reads keys that may not survive JSON serialization.**
`insights_service.compute_patterns` (and `compute_overview`) read
`payload.get("facts", [])`, then `fact.get("hazard_kind")` and
`fact.get("controls", [{}])[0].get("state")`. The pipeline's `AnalysisResult.facts` are
Pydantic `HazardFinding` objects. **Verify how the worker serializes `payload_json`** —
if it uses `.model_dump()` the keys are snake_case (`hazard_kind`, `controls`, `state`)
and match; if it uses `.model_dump(by_alias=True)` or the enum values serialize as
objects, the reads silently return defaults → this is why patterns show `hazard` +
`failed` but nothing richer. **Read `app/worker/processor.py` and
`app/services/report_service.py` to see exactly what dict gets stored in
`Analysis.payload_json`.** (Wasn't fully traced this session — START HERE for Bug 2.)

**(2c) Footer "61 of 10 · 610%" and "UNRESOLVED 44".** The backend `compute_overview`
returns clean values (`classification_coverage` = 100.0, `unresolved` = total-analyzed).
Confirmed via cloud repro: overview returned
`total_eligible:10, positive:9, negative:1, unresolved:0, coverage:100.0`. So **the
"61", "44", "610%" are hardcoded demo constants still living in
`services/frontend/js/insights.js`** that aren't being overwritten by the live payload
(the live render path isn't replacing the demo footer numbers). Grep insights.js for
`44`, `61`, `610`, `HUMAN-REVIEW`, `UNRESOLVED` and wire those to the API response
fields. Same likely applies to the "low support" / "of 10" denominators — verify each
footer/stat is bound to live data, not a constant.

### Bug 3 — (minor) "Unassigned reports 1" / "Unmapped assets 2"

Falls out of Bug 1 — once sites join to coordinates correctly, recount. The Rupsi
Helibase / Jaisalmer / Digboi type sites with no coordinate become "unmapped"; make
sure that's intentional and the counts are real, not demo constants.

---

## Suggested order of work for next session

1. **Confirm the stored payload shape** — read `app/worker/processor.py` +
   `report_service.py`, dump one `Analysis.payload_json` from the DB, and see whether
   `facts[].hazard_kind` / `facts[].controls[].state` are actually present. This
   unblocks Bug 2b and tells you if `compute_overview`/`compute_patterns` even see data.
2. **Fix spatial** (Bug 1): mount/bundle `safety/`, reconcile site names + coords,
   rewrite `compute_spatial` to join reports→sites with real counts.
3. **Fix insights footer/labels** (Bug 2a/2c): bind insights.js footer + row labels to
   the live API response; remove leftover demo constants (44/61/610).
4. Decide on activity/exposure/control-concept richness (Bug 2a option i vs ii) with
   the user — it's a product call, not just a bug.
5. Re-run `docker compose up`, screenshot all pages, confirm against the mockups.

## Files most relevant to the current problem

- `services/backend/app/services/insights_service.py` — compute_overview,
  compute_patterns, **compute_spatial (stub)**, get_pattern_reports (returns []).
- `services/backend/app/analysis/fixture_adapter.py` — keyword classifier (works).
- `services/backend/app/analysis/pipeline.py` — builds `facts`/`lsr_findings`.
- `services/backend/app/worker/processor.py` — **serializes payload_json (TRACE THIS)**.
- `services/backend/app/services/report_service.py` — persists analysis.
- `services/backend/app/schemas/api.py` — InsightsOverviewResponse / PatternGroup /
  SpatialOverviewResponse shapes (frontend contract).
- `services/frontend/js/insights.js` — **has leftover demo constants (44/61/610)**.
- `services/frontend/js/spatial.js` — calls `API.getSpatialOverview()`, falls back to
  hardcoded demo data on failure (line ~641), so map never crashes but shows nothing.
- `safety/site_coordinates.yaml` — **site names DON'T match seed sites; not mounted**.
- `services/backend/app/cli/seed.py` — the 10 demo reports (rich narratives, correct).

## How to reproduce the backend locally in the cloud (for the next AI)

Docker isn't available in the cloud, but you can run the real stack directly:

```bash
# 1. Stage the backend + frontend + safety from the user's machine into the cloud
#    (device_stage_files), assembling under a work dir with backend & frontend siblings.
# 2. Boot a local Postgres as an unprivileged user (root can't run initdb):
useradd -m pg 2>/dev/null; mkdir -p /home/claude/pgdata /home/claude/pgsock
chown -R pg:pg /home/claude/pgdata /home/claude/pgsock
su pg -c "/usr/lib/postgresql/16/bin/initdb -U postgres -D /home/claude/pgdata -A trust"
su pg -c "/usr/lib/postgresql/16/bin/pg_ctl -D /home/claude/pgdata -l /tmp/pg.log \
  -o '-p 5432 -k /home/claude/pgsock' start"
su pg -c "/usr/lib/postgresql/16/bin/psql -h 127.0.0.1 -p 5432 -U postgres \
  -c \"CREATE USER sif_user WITH PASSWORD 'sif_pass' SUPERUSER;\""
su pg -c "/usr/lib/postgresql/16/bin/psql -h 127.0.0.1 -p 5432 -U postgres \
  -c \"CREATE DATABASE sif_sentinel OWNER sif_user;\""
# 3. From services/backend/, with PYTHONPATH set and DATABASE_URL[_SYNC] pointing at
#    127.0.0.1:5432, MODEL_PROVIDER=fixture DEMO_MODE=true:
alembic upgrade head
python -m app.cli.seed_if_empty
WORKER_ENABLED=true python -m app.worker.main &   # classifies the 10 reports
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
# 4. curl to inspect: /api/v1/health, /api/v1/insights/overview,
#    /api/v1/insights/patterns, /api/v1/insights/spatial, /api/v1/reports?limit=3
#    (main.py resolves frontend at ../../frontend — keep backend & frontend as siblings)
```
All backend runtime deps are already importable in the cloud (fastapi, sqlalchemy,
asyncpg, psycopg2, alembic, uvicorn, pydantic_settings, yaml). Note: pyproject requires
py3.12 but the code imports fine on the cloud's 3.11; the Docker image is 3.12 so it's a
non-issue for the user.

## How the user runs it (Windows, their machine)

```powershell
cd C:\Users\paras\Documents\sih\sif-sentinel\infra
docker compose up            # Docker Desktop must be running
# open http://localhost:8000
```
Pages: `/` (Spatial), `/insights.html`, `/evidence.html?report=RPT-2214`,
`/import.html`, `/lab.html`. Stop with Ctrl+C; `docker compose down -v` wipes the DB.

## Watch-outs

- Editing files: edit in the cloud, then `device_commit_files` back to the exact
  Windows path. You can't run anything on the user's machine.
- Don't "fix" api.js's spatial path or the compose mount again — done & verified.
- The FixtureAdapter is deliberate (demo mode); don't replace it with an LLM call.
- Preserve the user's design system exactly.
- The Evidence Graph page (`evidence.html`) runs on 4 self-contained demo cases and has
  NO backend endpoint yet (`/reports/{id}/evidence-graph` is a 404 stub in api.js).
  Building that endpoint is an open, previously-offered task — not part of these 3 bugs.

---

## Evidence Graph page (`services/frontend/evidence.html`) — how it's built

The Evidence Graph is a **new page** added this project. It is a single, fully
self-contained HTML file (~1,498 lines, ~94 KB): inline `<style>` + inline `<script>`,
no build step, no framework, and — importantly — **no backend calls at all**. It runs
entirely on hardcoded demo cases. Only external dependency is Google Fonts. It was
ported from a mockup the user made (`Sentinel_Evidence_Graph.html`), then wired into
the app's nav and given a `?report=` entry point.

### What it shows (the concept)

A **bow-tie causal graph** per report: hazards (left) → preventive barriers → the
central **event / loss of control** → recovery barriers → consequences → **receptor**
(who was exposed), with context nodes (asset, location, activity, life-saving rules,
reported outcome) floating around the spine. It's the visual expression of the Luck
Test: the graph is read by **barrier state over time**, not by the reported outcome.
The "no injury reported" outcome sits off to the side as context — the path to harm is
judged by whether the barriers were actually closed.

### Data model (all inline in the file)

- **`PHASES`** (line ~290): the timeline scrubber steps —
  `["prep","work start","exposure","event","after"]`.
- **`NODES`** (per case): each node is
  `{id, type, col, row, label, sub, support, ctx?, states?, gap?, detail}`.
  - `type` ∈ `asset | location | activity | rule | hazard | barrier | event |
    consequence | receptor | outcome`.
  - `col`/`row` are graph coordinates (fractional rows allowed for the context ring).
  - `support` (1–3) drives stroke weight/opacity — how well the source evidences it
    (a `support:1` node like "Pyrophoric scale" or "Vessel overpressure" is drawn thin
    = policy-inferred / credible-but-unreported).
  - `ctx:true` = context node (no causal flow).
  - **`states`** (barriers only): a per-phase map, e.g.
    `{prep:"intact","work start":"failed",exposure:"failed",event:"failed",after:"failed"}`.
    **Barrier-state vocabulary (6):** `intact | failed | unknown | late | bypassed |
    absent`. Semantics matter and are deliberate:
    - `unknown` = named in source but no reading/time/instrument → drawn as a **hole**,
      explicitly NOT "absent" and NOT "failed" (this is the information-gap concept).
    - `absent` = barrier genuinely not present.
    - `late` = only exists after the event (e.g. an alarm that fired post-flash) →
      drawn *behind* the event.
  - **`gap`** (optional on barriers): `{q, why}` — the open question a reviewer must
    answer to resolve an `unknown` barrier. Counts into "N unresolved barriers".
- **`EDGES`** (per case): `{from, to, via?, kind, support, live?, label?}`.
  - `kind` ∈ `causal | inferred | context`. `via` routes a causal edge *through* a
    barrier node. `live:true` edges carry the animated "flow" during replay.
    `kind:"inferred"` edges (e.g. policy inference) are drawn distinctly from reported
    `causal` ones.
- **`EVIDENCE`** (per case, line ~381): the source narrative as an array of
  `{t, m}` fragments — `t` is a text run, `m` is a marker id (e.g. `"E-GAS"`,
  `"E-EVENT"`, `"E-RECEPTOR"`) linking that sentence to a node/finding. This is what
  lets the graph highlight the exact words behind a node.
- **`DISAGREE`** (per case, line ~391): the **model-vs-reviewer** overlay, e.g.
  `{"B-GAS":{model:"absent", reviewer:"unknown", reason:"narrative does not establish
  absence"}}`. When compare mode is on, nodes in this map are badged with both readings.
- **`RING`** (per case, line ~421): the context ring config (asset/activity/rule
  ghost-node expansion behavior).

### The 4 demo cases

`CASES` (line ~432) keyed by report id, and `CASE_LIST` (line ~624) is the switcher
menu. All four are hand-authored:
- **RPT-2214** — Rig A · Hot work · ignition in vessel · *2 unresolved barriers*
  (the default/richest case; gas test unknown + inerting unknown).
- **RPT-2140** — Moran · Vehicle movement · crew in swept path · 1 unresolved.
- **RPT-2189** — Naharkatiya · Maintenance · isolation not verified · 1 unresolved.
- **RPT-2104** — Block SY-03 · Personnel transfer · wind limit passed · 1 unresolved.

Note these ids are **demo-only** and do NOT correspond to the seeded DB reports
(OIL-2025-xxxx). The insights/spatial pages gate the "Evidence graph ↗" link behind a
`GRAPHED = new Set(["RPT-2214","RPT-2140","RPT-2189","RPT-2104"])` allow-list in
`insights.js` / `spatial.js`; other reports show a disabled "Evidence graph —" chip.

### Entry point / routing

- Reads `?report=` from the URL (line ~1489):
  `new URLSearchParams(location.search).get("report")`. If it matches a key in `CASES`,
  that case loads; otherwise it defaults to **RPT-2214**.
- So `evidence.html?report=RPT-2140` deep-links to a specific case. The in-page
  "Switch report" control (`CASE_LIST`) does the same client-side via `loadCase(id)`.

### Rendering & interaction (key functions, all inline)

- **`build()`** (~773) — the main render: lays out nodes by `col`/`row`, draws edges as
  SVG paths, applies per-phase barrier states, applies the compare overlay.
- **`fit(animate)`** (~1269) / **`remeasure()`** (~1453) — compute the SVG viewBox and
  scale to fit the container; there's a boot loop that retries measurement up to ~50×
  before first fit (handles the container not being sized yet on load).
- **`renderScrub()`** (~1157) / **`setPhase(i)`** (~1175) — the phase scrubber UI; moving
  it re-colors every barrier to its state at that phase and updates the reading caption.
- **`replayFlow()`** (~1181) — animates the "live" flow along `live:true` edges once,
  ~420ms after fit (the "graph at rest · flow runs once" behavior).
- **compare mode** — `#compareBtn` toggles `S.compare` (~1402); when on, `build()` badges
  every node in `DISAGREE` with model vs reviewer readings and a reason.
- **`renderLegend()`** (~1350), **`autoCollapse()`** (~1476) — legend + responsive panel
  collapse. State lives in a single `S` object (~652):
  `{caseId, scale, phase, focus, expanded:Set, compare, ...}`.
- **`setFocus(id)`** — clicking a node focuses it and dims the rest; the inspector panel
  shows that node's `detail`, evidence, and (for a gap barrier) the open question.

### How it was integrated this project

1. Ported the mockup into `services/frontend/evidence.html` (self-contained, inline).
2. Fixed the dock nav hrefs to the real app filenames (`index.html`, `insights.html`,
   `import.html`, `lab.html`) so the page sits inside the multi-page app. **These are
   real links in the device copy** — only the published-Artifact demo copy neutralized
   them with `onclick="return false"` because a single hosted page has no siblings.
3. Added the `Evidence graph` nav item to the docks on `index.html` + `insights.html`.
4. Added the `GRAPHED` allow-list + `graphLink()` helper to `insights.js` and
   `spatial.js` so report threads link into the graph only for the 4 built cases.
5. Added a stub `getEvidenceGraph(reportId)` to `api.js` → `GET
   /reports/{id}/evidence-graph` — **this endpoint does not exist on the backend yet
   (404)**. It's the seam for making the graph data-driven later.

### If you make the Evidence Graph live (open task, not one of the 3 bugs)

The graph's `{NODES, EDGES, EVIDENCE, states, gap, DISAGREE}` model is richer than what
the FixtureAdapter currently extracts. To drive it from real analyses you'd:
- Build `GET /api/v1/reports/{id}/evidence-graph` in `app/api/v1/reports.py` that
  transforms an `Analysis.payload_json` (`facts`/`hazards`, `lsr_findings`, control
  states, evidence spans) into the node/edge/phase shape above.
- The hardest gaps: per-phase barrier `states` (the fixture gives one control state, not
  a timeline), the `EVIDENCE` sentence↔node markers (evidence spans exist in the
  payload — see `pipeline.py` EvidenceSpan with `start_utf16/end_utf16`), and
  `DISAGREE` (needs a stored reviewer decision from the Review table).
- Keep the 4 hardcoded cases as a fallback for reports with no built graph.
