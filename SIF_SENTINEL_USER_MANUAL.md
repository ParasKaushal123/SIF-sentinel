# SIF Sentinel — Comprehensive Technical & User Documentation

## 1. System Overview & Philosophy

**SIF Sentinel** is an AI-powered safety intelligence engine built for high-hazard industrial environments—specifically upstream oil and gas exploration, drilling, processing plants, and pipeline networks for **Oil India Limited (OIL)**.

### The Problem: Outcome Bias in HSE Reporting
In traditional industrial safety management, incident reporting is systematically distorted by **outcome bias** (the "Luck Bias"):
* When an unlatched 12-ton drill pipe swings free and crushes a compressor skid, it is logged as a *High-Severity / Tier-1 Incident*.
* When the exact same unlatched pipe swings free and drops harmlessly into the mud because a worker happened to step back to tie their boot, the event is logged as *Minor Near-Miss* or *First Aid*.

The barrier failure and the hazard exposure were identical; only luck separated the near-miss from a fatality.

### The SIF Sentinel Solution
SIF Sentinel acts as an automated triage intelligence layer. It reads unstructured, free-text safety narratives (daily logs, observation cards, unsafe act reports) and extracts:
1. **High-Energy Hazard Mechanisms**: Kinetic, gravitational, electrical, pressurized fluid/gas, toxic atmospheres, mechanical rotating parts.
2. **Worker Exposure State**: Physical proximity, line of fire, intervening within an energized perimeter.
3. **Control Barrier Timing & Verification**: Was a recognized barrier (lockout-tagout, pressure release bleed, certified exclusion zone, gas detection) verified effective *prior* to worker exposure?

By cross-referencing these components, SIF Sentinel identifies **Serious Injury or Fatality (SIF) Precursors** across 12 canonical operational patterns, alerting HSE leadership before an incident results in death or disability.

---

## 2. Global Navigation & Architecture

SIF Sentinel uses a responsive, glassmorphic design system ("Pattern Observatory") built with vanilla HTML5, CSS3 Custom Properties, ES6 modules, and D3.js:

* **Floating Dock (Left Screen Edge):**
  * 🗺️ **Command Centre (`index.html`)**: Interactive geographic projection of Oil India installations, asset statuses, and risk lenses.
  * 📊 **Pattern Observatory (`insights.html`)**: Real-time aggregation of safety narratives into 12 precursor stream families.
  * 🕸️ **Evidence Graph (`evidence.html`)**: Causal Directed Acyclic Graph (DAG) illustrating how words in a narrative produce safety classifications.
  * 📤 **Import Wizard (`import.html`)**: Bulk CSV and report file ingestion pipeline.
  * 🧪 **Luck Lab (`lab.html`)**: Side-by-side outcome-bias demonstration sandbox.
* **Header Bar:**
  * Active dataset pill (`OIL India · v2026.03`), search field, and navigation breadcrumbs.

---

## 3. In-Depth Screen Specifications

### 1. Spatial Command Centre (`index.html`)

The operational map provides visibility across Oil India's active geographic basins.

#### Key Components:
1. **Interactive D3 India Basemap:**
   * High-precision vector rendering using bundled official Survey of India boundary data (`data/india.geojson`) ensuring correct regional boundaries (including Jammu & Kashmir, Ladakh, and Assam).
   * Pan, zoom, and parallax controls with smooth transitions.
2. **Asset Markers & Categorization:**
   * Plots major installations:
     * **Assam Basin**: Naharkatiya Block (`AST-01`), Moran Gathering Station (`AST-02`), Rig OIL-D-12 (`AST-03`), Kumchai Field (`AST-04`), Jorhat Compressor (`AST-05`).
     * **KG Offshore**: Block SY-03 (`AST-06`).
     * **Rajasthan**: Jaisalmer Exploration Prospect (`AST-07`).
   * Visual glyphs identify facility types:
     * `◇` Onshore Field
     * `◈` Processing Installation
     * `⌬` Drilling Rig
     * `⬡` Offshore Platform
     * `△` Exploration
3. **Operational Lenses:**
   * **Review Attention**: Highlights sites with overdue human reviews or unverified model classifications.
   * **Information Gaps**: Isolates sites with critical narrative omissions (e.g. isolation claimed without test-for-dead records).
   * **All Assets**: Visualizes gross report density.
4. **Site Inspector Slide-Over:**
   * Selecting any asset opens a detail drawer showing:
     * Total reports, pending reviews, and information gaps.
     * Scrollable feed of individual site reports with narrative excerpts, hazard identification, and direct shortcuts (`↗`) to the interactive evidence graph.

---

### 2. Pattern Observatory (`insights.html`)

The executive intelligence dashboard. It transforms isolated incident logs into organizational trends across 12 canonical SIF precursor patterns.

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

#### Visual Features:
* **Stream Density Bars**: Dynamic proportional bars showing incident distribution normalized against peak volume.
* **KPI Ribbon**: Total eligible reports, complete extractions, unresolved ambiguities, and human audit status.
* **Pattern Inspector**: Detailed modal with underlying causal definitions, explanation of the safety gap, and member report listings.

---

### 3. Forensic Evidence Graph (`evidence.html`)

Provides transparent explainability for AI extractions.

#### Features:
* **Causal Directed Acyclic Graph (DAG):**
  * Maps connections from raw source text to hazard nodes, exposure mechanisms, barrier evaluations, and final SIF potential.
* **Bidirectional Ground-Truth Highlighting:**
  * Clicking any node in the graph instantly highlights the exact supporting sentence in the original narrative text.
* **Temporal Scrubber:**
  * Timeline control allowing safety officers to step chronologically through the event:
    * **T0**: Work Planning & Permit Issuance
    * **T1**: Worker Position & Exposure
    * **T2**: Barrier Compromise / Failure
    * **T3**: Energy Release / Incident Occurrence

---

### 4. The Luck Lab (`lab.html`)

The empirical test chamber demonstrating outcome-bias resistance.

#### Workflow:
1. Input two reports side-by-side:
   * **Report A (Severe Consequence)**: Load drops from crane hoist, destroys equipment.
   * **Report B (No Consequence)**: Same load drops from crane hoist due to the same missing latch pin, but misses everyone.
2. Click **Run Comparison**.
3. The engine produces the exact same classification (**SIF Precursor P-03**) and identical barrier breakdown graphs for both, demonstrating that safety interventions must focus on barrier integrity, not outcome luck.

---

### 5. Ingestion Pipeline (`import.html`)

The enterprise data onboarding module:
* Accepts drag-and-drop CSV or Excel incident exports.
* Pre-validates mandatory narrative fields.
* Enqueues reports for asynchronous background classification.

---

## 4. End-to-End Operational Workflows

### Workflow 1: Rig Safety Officer (Daily Field Triage)
1. Navigate to the **Spatial Command Centre (`index.html`)**.
2. Select the **Information Gaps** lens.
3. Click your assigned installation (e.g., *Rig OIL-D-12*).
4. Review reports flagged as *Needs Information*.
5. Click **Evidence Graph (`↗`)** to inspect why the extraction flagged an ambiguity (e.g. missing elevator latch check record).
6. Request direct field verification from the rig floor before authorizing subsequent operations.

### Workflow 2: Corporate HSE Leadership (Basin-Wide Prevention)
1. Open the **Pattern Observatory (`insights.html`)**.
2. Examine the stream density bars across the 12 precursor families.
3. Identify spikes in specific patterns (e.g., **P-01 Electrical Isolation** or **P-04 Vehicle Spotter Absence**).
4. Export the pattern audit trail to issue targeted corporate safety bulletins before a fatality occurs.
