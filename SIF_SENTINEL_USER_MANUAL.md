# SIF Sentinel — Comprehensive Application Documentation

## 1. Executive Summary & Core Mission

### Challenge Context: Smart India Hackathon (SIH 2026) — Problem SIH26165
**SIF Sentinel** is an AI-powered **Precursor & Exposure Intelligence Engine** engineered for **Oil India Limited (OIL)**.

In hazardous energy industries (upstream exploration, drilling, gathering stations, and pipeline terminals), traditional safety reporting suffers from two systemic flaws:
1. **Outcome Bias ("The Luck Bias"):** Incidents where someone suffered a scrape are classified as "Minor First Aid", even if the worker stood inches from an unisolated 415V breaker or a suspended drilling elevator. The near-miss was identical to a fatality, separated only by luck.
2. **Superficial Classification & Information Gaps:** Incident forms reduce rich narratives to shallow checkboxes. Crucial safety control verifications (e.g., *"Was a test-for-dead performed before touching the panel?"*, *"Was the exclusion zone set before or after the crane lifted?"*) are omitted or left ambiguous.

### SIF Sentinel's Solution
SIF Sentinel extracts structured safety facts directly from unstructured incident narratives and evaluates:
* **High-Energy Hazard** presence (Electrical, Pressure, Suspended Load, Toxic Gas, Heavy Vehicle, Fall from Height).
* **Worker Exposure** (Direct line of fire, intervening in energized zone).
* **Control State & Verification Timing** (Was the control verified effective prior to exposure?).
* **Precursor Identification (P-01 through P-12)**: Aggregating recurring organizational blind spots regardless of whether an injury actually occurred.

---

## 2. Navigation Architecture & Global Elements

Every page in SIF Sentinel shares a unified navigation and design system:
* **Floating Glass Dock (Left Edge):**
  * **Map Icon (index.html)**: Spatial Command Centre — geographical exposure distribution across Oil India assets.
  * **Analytics Icon (insights.html)**: Pattern Observatory — deep-dive precursor trends, gaps, and triage.
  * **Evidence Graph (evidence.html)**: Causal DAG — interactive graph showing how narrative words map to hazards, controls, and final SIF classification.
  * **Upload Icon (import.html)**: Data Pipeline & Ingestion Wizard.
  * **Science Flask (lab.html)**: Luck Lab — Side-by-side outcome-bias sandbox.
* **Top Header:** Displays active dataset version (OIL India · v2026.03), system status, and filter breadcrumbs.

---

## 3. Detailed Breakdown by Page

### Page 1: Spatial Command Centre (index.html)

The entry point of SIF Sentinel. It displays an interactive geographic projection of India highlighting Oil India installations and real-time precursor signals.

#### Key Features & Visual Elements:
1. **Interactive D3 India Choropleth / Basemap:**
   * High-definition vector boundaries with smooth pan and zoom.
   * Pinpoints core Oil India operating sectors:
     * **Assam Basin**: Naharkatiya Block (AST-01), Moran Gathering Station (AST-02), Rig OIL-D-12 (AST-03), Kumchai Field (AST-04), Jorhat Compressor Station (AST-05).
     * **Krishna Godavari (KG) Offshore**: Block SY-03 (AST-06).
     * **Rajasthan Onshore**: Jaisalmer Exploration Prospect (AST-07).
2. **Asset Glyphs & Indicators:**
   * Each asset marker indicates asset type:
     * ◇ Onshore Field
     * ◈ Gathering / Compressor Station
     * ⌬ Drilling Rig
     * ⬡ Offshore Platform
     * △ Exploration
   * Marker size scales proportionally with the number of flagged reports or active information gaps.
3. **Analytical Lenses (Top Pill Bar):**
   * **Review Attention Lens:** Highlights sites where human safety review is overdue, stale (>90 days), or unassigned.
   * **Information Gaps Lens:** Isolates sites where crucial safety controls were mentioned in narratives without verification proof (e.g. missing isolation certificate, unverified depressurisation, absent gas detector reading).
   * **All Assets Lens:** Displays total cumulative report density.
4. **Site Inspector Card (Right Pane):**
   * Clicking any asset opens a slide-over panel displaying:
     * Asset metadata (Region, Asset ID, Coordinate confidence).
     * Breakdown of reports by status (*Serious-risk candidate*, *Needs information*, *Low potential*, *Reviewed*).
     * **Feed of Individual Incident Reports**: Showing excerpt, exposure type, control failure, and exact information gap.
     * **Evidence Graph Shortcut (↗)**: Direct deep-link to inspect that exact incident's causal breakdown in evidence.html.
5. **Unmapped Queue Indicator:**
   * Bottom banner detailing reports from locations pending coordinate resolution (e.g. Dibrugarh Terminal, Barmer Gathering Line).

---

### Page 2: Pattern Observatory (insights.html)

The strategic intelligence layer. It aggregates individual incident reports into **12 Canonical Organizational Precursors (P-01 to P-12)**.

#### The 12 Canonical Precursor Patterns:
* **P-01**: *Electrical Energy · Isolation · Effectiveness not established*
* **P-02**: *Electrical Energy · Isolation · Effectiveness reported*
* **P-03**: *Suspended Load · Exclusion Zone · Reported after event*
* **P-04**: *Heavy Vehicle · Spotter · Control absent*
* **P-05**: *Toxic/Flammable Gas · Atmosphere Testing · Gap in verification*
* **P-06**: *Drillstring / Stored Tension · Latch Verification · Incomplete evidence*
* **P-07**: *Line of Fire · Mechanical Equipment · Zone compromised*
* **P-08**: *Confined Space · Entry Permit / Ventilation · Unverified atmosphere*
* **P-09**: *High Pressure Release · Depressurisation · Statements conflict*
* **P-10**: *Fall from Height · Fall Arrest / Anchor · Timing unknown*
* **P-11**: *Excavation / Trenching · Underground Utility Scan · Record absent*
* **P-12**: *Hot Work · Spark Containment / Standby · Control compromised*

#### Key Features:
1. **Macro KPI Header:**
   * **Eligible Reports**: Total corpus ingested.
   * **Classified**: Reports with complete hazard-exposure-control tuples.
   * **Unresolved**: Reports stuck in ambiguity requiring field clarification.
   * **Human Reviewed**: Reports audited and signed off by safety officers.
2. **Stream Density Bars:**
   * Dynamic visual progress bars showing the volume of incidents belonging to each pattern family, normalized against peak activity.
3. **Pattern Inspector Modal:**
   * Clicking on any pattern reveals:
     * **Activity, Hazard, Exposure, Control, and State**.
     * **Why this is a gap**: Human-readable explanation of why this pattern is dangerous.
     * **Full Report Table**: All underlying reports with site names, narrative excerpts, and one-click access to their causal evidence graph.

---

### Page 3: Evidence Graph (evidence.html)

The forensic explainability layer. SIF Sentinel never acts as a black box; every prediction produces a verifiable **Causal Directed Acyclic Graph (DAG)**.

#### How It Works:
1. **Interactive Node-Link Canvas (Cytoscape / Vector Engine):**
   * **Source Node**: Raw narrative excerpt extracted from the field incident.
   * **Hazard Node**: The high-energy source detected (e.g., *Kinetic / Suspended Load 12T*).
   * **Exposure Node**: Worker position (e.g., *Worker standing within swing radius*).
   * **Control Node**: The defense barrier (e.g., *Red tape / Physical exclusion barrier*).
   * **State / Timing Node**: Temporal relationship (*Was control present before hazard release?*).
   * **SIF Classification Node**: Final assessment (*SIF Precursor Qualified vs Low Potential*).
2. **Confidence & Evidence Highlighting:**
   * Clicking any node in the graph highlights the exact phrase in the source narrative text from which the AI extracted that fact.
3. **Interactive Timeline / Scrubber:**
   * Bottom slider allowing safety auditors to step through the chronological sequence of events (T0 = Preparation, T1 = Intervention, T2 = Barrier Breakdown, T3 = Energy Release).

---

### Page 4: Ingestion Pipeline (import.html)

The data intake portal:
* Allows safety managers to drag-and-drop raw CSV, Excel, or text dumps of daily safety logs.
* Maps custom column headers (e.g. *Incident Description*, *Location*, *Date*, *Severity Checkbox*) to SIF Sentinel's schema.
* Pre-validates formatting before queuing narratives for asynchronous background classification.

---

### Page 5: The "Luck Lab" (lab.html)

The core demonstration of **Outcome Bias Resistance**.

#### How to Use It:
1. **Side-by-Side Narrative Comparison**:
   * **Scenario A (Catastrophe)**: A heavy drill casing slips from a crane hoist and crushes equipment because the hoist latch pin was omitted. (Traditional classification: *Level 5 Critical Incident*).
   * **Scenario B (Near Miss / Luck)**: A heavy drill casing slips from a crane hoist and lands in the mud 2 feet away because the hoist latch pin was omitted; nobody is hurt. (Traditional classification: *Level 1 Minor Near Miss*).
2. **Run Comparison**:
   * SIF Sentinel classifies **both** scenarios into the exact same category: **SIF Precursor (High SIF Potential)** with an identical **Evidence Graph**.
   * Demonstrates to auditors that safety interventions must focus on **energy and barriers**, not whether someone got lucky.

---

## 4. User Personas & Workflows

### Persona 1: Field Safety Auditor / Rig Safety Officer
* **Primary Page:** index.html (Spatial Command Centre)
* **Workflow:**
  1. Open the Map and switch to the **Information Gaps** lens.
  2. Select their asset (e.g. *Rig OIL-D-12*).
  3. Review reports flagged as *Needs Information*.
  4. Notice that an electrical isolation report lacks a verification test log.
  5. Click **Evidence Graph** to verify the missing link, then request clarification from the shift supervisor.

### Persona 2: Corporate HSE Director (Oil India HQ)
* **Primary Page:** insights.html (Pattern Observatory)
* **Workflow:**
  1. Open Insights to view the global precursor health of all operating basins.
  2. Identify that **P-01 (Energy Isolation)** and **P-03 (Suspended Load)** constitute 45% of all precursor signals across Assam.
  3. Export pattern analytics to issue a targeted corporate safety stand-down focusing on hoist latching protocols before an actual fatality occurs.

---

## 5. Technology Stack Summary

* **Frontend:** Vanilla HTML5, CSS3 Custom Properties, Modern ES6 JavaScript, D3.js (Geographic vector projection), IBM Plex Mono + Space Grotesk typography. Zero external framework dependencies for ultra-fast CDN loading.
* **Backend:** FastAPI (Python 3.11), SQLAlchemy 2.0 (Async), Pydantic v2 schemas.
* **Database:** PostgreSQL with relational integrity for datasets, assets, narratives, and extracted causal nodes.
* **Extraction Engine:** LLM Adapter Pipeline with fallback deterministic heuristics, strict JSON schema extraction prompts, and evidence ground-truth alignment.
