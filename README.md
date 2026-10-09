<a name="top"></a>

# 🛡️ SIF Sentinel

<p align="center">
  <b>AI-Powered Precursor & Exposure Intelligence Engine for High-Hazard Energy Operations</b><br>
  <i>"No injury is an outcome — not evidence of protection."</i>
</p>

<p align="center">
  <a href="https://github.com/ParasKaushal123/SIF-sentinel/actions"><img src="https://img.shields.io/badge/build-passing-brightgreen?style=flat-square" alt="Build Status"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11%20%7C%203.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL"></a>
  <a href="https://d3js.org/"><img src="https://img.shields.io/badge/D3.js-v7-F9A03C?style=flat-square&logo=d3.js&logoColor=white" alt="D3"></a>
  <a href="https://docker.com"><img src="https://img.shields.io/badge/docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License"></a>
  <a href="#-quickstart"><img src="https://img.shields.io/badge/deployment-docker%20%7C%20vercel-black?style=flat-square" alt="Deploy"></a>
</p>

<p align="center">
  ⭐ <b>Star this repository on GitHub</b> to support open-source industrial safety intelligence!
</p>

---

## 📑 Table of Contents
- [About](#-about)
- [Core Innovation: The Luck Test](#-core-innovation-the-luck-test)
- [Key Features](#-key-features)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Quickstart](#-quickstart)
  - [Option A: One-Command Docker Setup (Recommended)](#option-a-one-command-docker-setup-recommended)
  - [Option B: Local Python Development](#option-b-local-python-development)
  - [Option C: Cloud Deployment (Vercel)](#option-c-cloud-deployment-vercel)
- [Walkthrough of System Modules](#-walkthrough-of-system-modules)
  - [1. Spatial Command Centre](#1-spatial-command-centre)
  - [2. Pattern Observatory](#2-pattern-observatory)
  - [3. Forensic Evidence Graph](#3-forensic-evidence-graph)
  - [4. The Luck Lab](#4-the-luck-lab)
  - [5. Batch Ingestion Pipeline](#5-batch-ingestion-pipeline)
- [API Reference](#-api-reference)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## 🚀 About

**SIF Sentinel** is a precursor intelligence system designed for **Oil India Limited (OIL)** to triage, extract, and classify high-hazard safety narratives (unsafe acts, unsafe conditions, and near-misses).

In upstream exploration, drilling, gas gathering stations, and pipeline networks, conventional HSE reporting is plagued by **outcome bias**:
* If a 12-ton drill pipe swings free of an elevator due to an unlatched pin and crushes equipment, it is logged as a *Tier-1 Critical Incident*.
* If that exact same pipe swings free but lands 2 feet away in the mud and injures nobody, traditional systems file it under *Minor First Aid / Low Near Miss*.

**SIF Sentinel eliminates this outcome bias.** It analyzes the high-energy hazard, worker exposure, and control barrier efficacy, treating the near-miss and the catastrophe with identical preventative urgency.

`
       UNSTRUCTURED NARRATIVE
  "Worker adjusted 415V breaker
   without multimeter test..."
                │
                ▼
      ┌───────────────────┐
      │  SIF SENTINEL AI  │ ──► Extracts: [Hazard: Electrical Energy]
      │  ANALYSIS ENGINE  │ ──► Extracts: [Exposure: Worker Intervening]
      └───────────────────┘ ──► Extracts: [Barrier: Isolation Unverified]
                │
                ▼
   PRECURSOR CLASSIFICATION: P-01
   "Energy Isolation · Effectiveness Not Established"
   (Flagged regardless of zero-injury outcome)
`

---

## 🧠 Core Innovation: The Luck Test

> *"No injury is an outcome — not evidence of protection."*

When a safety report reads "no injury occurred", that fact describes **what happened at the end**, not whether the defense barriers functioned. SIF Sentinel evaluates three deterministic dimensions:

1. **High-Energy Hazard**: Gravitational (suspended load, height), Electrical (energized switchgear), Pressure (hydrocarbon lines), Mechanical (rotating machinery), Toxic Gas ($, methane).
2. **Exposure Mechanism**: Was a worker physically located inside the energy release corridor?
3. **Control Barrier Timing & Efficacy**: Was a certified physical barrier, lockout/tagout, or exclusion zone verified effective *before* the worker intervened?

If high energy was present and control verification is missing, SIF Sentinel classifies the report as a **SIF Precursor**, generating actionable alerts before a fatality occurs.

---

## ✨ Key Features

- **Interactive Spatial Command Centre:** High-performance D3 vector basemap plotting Oil India assets across Assam, Rajasthan, and KG Offshore with real-time operational lenses (*Review Attention*, *Information Gaps*, *Total Density*).
- **Pattern Observatory:** Aggregates messy free-text logs into **12 Canonical Organizational Precursors (P-01 to P-12)** with dynamic stream density bars and human-readable gap explanations.
- **Explainable Evidence Graphs (DAGs):** Generates interactive causal Directed Acyclic Graphs tracing how specific words in the source narrative map to hazards, exposures, barrier failures, and SIF potential.
- **Audit-Ready Explainability:** Clicking any node in the evidence graph highlights the exact phrase in the source narrative, eliminating "black-box" AI guesswork.
- **The Luck Lab:** A side-by-side sandbox comparing two incident narratives (e.g. fatal outcome vs. lucky near-miss) to prove identical precursor classification.
- **Glassmorphic Pattern Observatory UI:** Ergonomic interface built on vanilla ES6, CSS3 custom properties, Space Grotesk, and IBM Plex Mono typography with zero heavy framework overhead.

---

## 🏗️ Architecture & Tech Stack

`
┌────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND OBSERVATORY                          │
│        Vanilla HTML5 · CSS3 Custom Tokens · ES6 Modules · D3.js        │
│                                                                        │
│   ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────┐   │
│   │ Spatial Command  │  │ Pattern Observ.  │  │   Evidence Graph   │   │
│   │  (index.html)    │  │ (insights.html)  │  │  (evidence.html)   │   │
│   └────────┬─────────┘  └────────┬─────────┘  └─────────┬──────────┘   │
└────────────┼─────────────────────┼──────────────────────┼──────────────┘
             │                     │                      │
             ▼ REST /api/v1 (JSON) │                      │
┌──────────────────────────────────┴──────────────────────┴──────────────┐
│                           FASTAPI BACKEND API                          │
│               Python 3.11/3.12 · Pydantic v2 · SQLAlchemy 2            │
│                                                                        │
│   ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────┐   │
│   │ Insights Service │  │  Report Service  │  │   Import Service   │   │
│   └────────┬─────────┘  └────────┬─────────┘  └─────────┬──────────┘   │
│            └─────────────────────┼──────────────────────┘              │
│                                  │                                     │
│                        Extraction & Policy                             │
│                  (Adapter Pattern: Fixture / LLM)                      │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
              ┌────────────────────┴───────────────────┐
              ▼                                        ▼
   ┌─────────────────────┐                  ┌─────────────────────┐
   │    ANALYSIS WORKER  │                  │    POSTGRESQL 16    │
   │   Job Queue Poller  │ ◄──────────────► │  14 Tables + JSONB  │
   │ (SKIP LOCKED Lease) │                  │ Relational Storage  │
   └─────────────────────┘                  └─────────────────────┘
`

| Layer | Technologies | Rationale |
|---|---|---|
| **Frontend** | Vanilla ES6, D3.js (geo), CSS3 | Blazing fast load times (<100ms), zero bundling bloat, full offline fallback capability |
| **Backend API** | FastAPI, Pydantic v2, Python 3.11 | High throughput asynchronous endpoints with strict schema validation |
| **Database** | PostgreSQL 16 + SQLAlchemy 2.0 (asyncpg) | Relational integrity for reports, revisions, and extracted causal nodes |
| **Worker Engine** | Custom Python Async Worker | Distributed transactional job claiming with FOR UPDATE SKIP LOCKED |
| **GIS Mapping** | D3 Geo Mercator + Survey of India GeoJSON | Accurate representation of Indian state boundaries (J&K, Ladakh, Assam) |

---

## ⚡ Quickstart

### Option A: One-Command Docker Setup (Recommended)

Run the entire full-stack application (PostgreSQL + FastAPI + Worker + Frontend):

`ash
# Clone the repository
git clone https://github.com/ParasKaushal123/SIF-sentinel.git
cd SIF-sentinel/infra

# Spin up all containers
docker compose up -d
`

Open your browser:
* 🌐 **Frontend Observatory**: [http://localhost:8000](http://localhost:8000)
* 📖 **Interactive API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* 🔍 **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

### Option B: Local Python Development

#### 1. Backend Setup
`ash
cd services/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations & seed demo dataset
alembic upgrade head
python -m app.cli.seed

# Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
`

#### 2. Start Worker (in a separate terminal)
`ash
cd services/backend
python -m app.worker.main
`

---

### Option C: Cloud Deployment (Vercel)

The frontend is fully decoupled and ready for instant deployment on Vercel:
1. Import ParasKaushal123/SIF-sentinel on **[Vercel](https://vercel.com)**.
2. Set **Root Directory** to services/frontend.
3. Framework Preset: **Other**.
4. Click **Deploy**.

> *Note:* If deployed without an active backend, the frontend automatically falls back to the bundled Oil India benchmark dataset so all visualisations and graphs work smoothly for demonstration.

---

## 🔍 Walkthrough of System Modules

### 1. Spatial Command Centre (index.html)
Visualises regional risk concentrations across Oil India's operational assets:
* **Naharkatiya & Moran**: Primary upstream drilling and gathering installations in Upper Assam.
* **Rig OIL-D-12 & Kumchai**: Heavy onshore drilling rigs and development fields.
* **Block SY-03**: Deepwater offshore exploration in the Krishna Godavari basin.
* **Jaisalmer Prospect**: High-temperature desert drilling operations in Rajasthan.
* **Lenses**: Toggle between **Review Attention** (audit backlogs) and **Information Gaps** (unverified barrier claims).

### 2. Pattern Observatory (insights.html)
Synthesises raw reports into the 12 canonical SIF precursor patterns:
* **P-01 to P-02**: Electrical Isolation (*Unverified vs. Meter-verified*).
* **P-03**: Suspended Loads (*Exclusion zones declared post-lift*).
* **P-04**: Heavy Equipment / Pipeline Transport (*Absence of vehicle spotters*).
* **P-05**: Hydrocarbon Flammable / Toxic Release (*Atmospheric testing gaps*).
* **P-06**: Drilling String Mechanical Tension (*Elevator latch uninspected*).
* **P-07 to P-12**: Line of fire, confined spaces, depressurisation conflicts, height drops, and hot work.

### 3. Forensic Evidence Graph (evidence.html)
Provides full explainability for each classification:
* Renders a Directed Acyclic Graph connecting **Narrative Excerpt ➔ Hazard ➔ Exposure ➔ Barrier State ➔ Precursor Output**.
* Interactive time scrubber allowing investigators to walk through the event from $ (preparation) to $ (energy release).

### 4. The Luck Lab (lab.html)
Outcome-bias demonstration suite:
* Enter two contrasting safety reports side-by-side.
* Witness the classification engine ignore the outcome ("worker escaped unhurt") and focus strictly on the failed barrier, demonstrating true outcome resistance.

### 5. Batch Ingestion Pipeline (import.html)
* Batch CSV and raw incident ingestion wizard with pre-validation and asynchronous queueing for large historical safety archives.

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | /api/v1/health | Returns health status of API, database, and background worker |
| GET | /api/v1/insights/spatial | Returns mapped Oil India assets, coordinates, report counts, and unmapped sites |
| GET | /api/v1/insights/patterns | Returns the 12 canonical precursor groups with member report excerpts and gap analysis |
| GET | /api/v1/reports | Paginated list of ingested incident reports with filters by site, status, and hazard |
| POST | /api/v1/reports | Ingests a new narrative report and enqueues it for SIF analysis |
| POST | /api/v1/lab/compare | Compares two safety narratives side-by-side for outcome-bias resilience testing |

---

## 🤝 Contributing

Contributions and feedback from safety professionals and software engineers are very welcome!

1. Fork the Project (https://github.com/ParasKaushal123/SIF-sentinel/fork)
2. Create your Feature Branch (git checkout -b feature/AmazingFeature)
3. Commit your Changes (git commit -m 'Add some AmazingFeature')
4. Push to the Branch (git push origin feature/AmazingFeature)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📬 Contact & Support

* **Maintainer:** Paras Kaushal
* **GitHub:** [@ParasKaushal123](https://github.com/ParasKaushal123)
* **Project Repository:** [https://github.com/ParasKaushal123/SIF-sentinel](https://github.com/ParasKaushal123/SIF-sentinel)

[Back to top](#top)
