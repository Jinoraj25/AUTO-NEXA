# AUTO NEXA Enterprise — Automotive Catalog & Supply Chain Intelligence Engine

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render%20Cloud-22c55e?style=for-the-badge&logo=render&logoColor=white)](https://auto-nexa.onrender.com)
[![Python](https://img.shields.io/badge/Backend-Python%20%7C%20Flask-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![JavaScript](https://img.shields.io/badge/Frontend-ES6%2B%20%7C%20Vanilla%20Architecture-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![License](https://img.shields.io/badge/Architecture-High%20Performance%20In--Memory%20Streams-7c3aed?style=for-the-badge)](https://github.com/Jinoraj25/AUTO-NEXA)

> **Enterprise-grade automotive aftermarket catalog management, OEM-to-OES cross-referencing, multi-channel sales analytics (Counter / Retail), and inventory intelligence platform.**  
> Built and architected by **Jino George** *(Catalog Analyst & Data Engineer)*.

---

## 🚀 Live Demo & Recruiter Access

- **Live Production URL:** [https://auto-nexa.onrender.com](https://auto-nexa.onrender.com) *(or your deployed Render service URL)*
- **Recruiter Demo Access:**
  - Click the **"🚀 1-Click Live Demo (Recruiter & Guest Access)"** button on the login screen for instant authorization.
  - Or sign in using demo enterprise credentials:
    - **User ID / Employee Code:** `SM0237`
    - **Password:** `Catalog@2026`

---

## 💼 Executive Project Overview & Business Impact

In multi-brand automotive supply chains, catalog fragmentation, cross-referencing inconsistencies, and delayed inventory visibility cause millions in lost revenue and margin erosion. **AUTO NEXA** solves these challenges by combining:

1. **Deterministic OEM-to-OES Cross-Referencing:** Instant interchange between Original Equipment Manufacturer (OEM) part numbers and verified Tier-1 OES manufacturers (Bosch, Valeo, TVS Apache, Uno Minda, Lumax, Gabriel, Denso, Mahle, Brembo, etc.) with automated cost savings and margin realization metrics.
2. **5-Level Vehicle Taxonomy Explorer:** Granular drill-down across Make &rarr; Model &rarr; Generation &rarr; Aggregate &rarr; Sub-Aggregate with multi-select filtering and zero-latency in-browser indexing.
3. **Multi-Channel Sales Intelligence (CF vs. RF Analytics):**
   - **CF (Counter Forward / Wholesale):** Commercial fleet and high-volume distributor order tracking with bulk margin analysis.
   - **RF (Retail Franchise / Outlets):** Fast-moving consumer retail demand analytics with counter-velocity metrics.
   - **Consolidated Executive View:** Real-time revenue, gross margin, and volume contribution across all product lines.
4. **Real-time Inventory Valuation & Velocity:** Active stock monitoring, inventory aging brackets, unit valuation calculations, and automated Excel export.
5. **Catalog AI Assistant:** Context-aware technical assistant capable of identifying part compatibility, cross-checking SKU specifications, and parsing customer inquiry scripts.

---

## 📊 High-Performance Data Architecture

One of the key engineering achievements of AUTO NEXA is its ability to handle **massive multi-gigabyte catalog datasets** on lightweight, cost-effective cloud deployments without latency degradation or memory crashes.

```
                    ┌──────────────────────────────────────────────┐
                    │ Raw Master Datasets (>10 GB Raw Data)        │
                    │ • 300,000+ Mapped OEM & OES SKUs             │
                    │ • 169 Global & Domestic Automotive Brands    │
                    │ • Multi-Warehouse Daily Stock & Sales Logs   │
                    └──────────────────────┬───────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │ ETL & Stream Compression Pipeline (Python)   │
                    │ • Casing & Nomenclature Normalization        │
                    │ • Gzip-Compressed In-Memory Binary Streams   │
                    │ • 98.2% Storage Reduction (~15 MB Deploy)    │
                    └──────────────────────┬───────────────────────┘
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼                                     ▼
         ┌───────────────────────────────┐     ┌───────────────────────────────┐
         │ Flask Backend Daemon          │     │ Client-Side Web Worker Engine │
         │ • Fast Index-Lookup REST API  │     │ • Zero-Latency Search & Filter│
         │ • Sub-50ms Response Times     │     │ • Chart.js & SheetJS Export   │
         └───────────────────────────────┘     └───────────────────────────────┘
```

- **Compression & Memory Efficiency:** Master catalog and sales tables are compiled into pre-indexed, compressed gzip data streams (`.json.gz`). This reduces memory consumption by over **98%**, allowing the entire platform to operate within a standard 512 MB RAM container on Render with sub-50ms query response times.
- **Offline & Low-Bandwidth Resilience:** Frontend utilizes intelligent in-memory indexing, enabling vehicle taxonomy searches and SKU queries to execute instantaneously without repeated round-trips to the server.

---

## 🛠️ Core Functional Modules

### 1. OEM to OES Interchange Engine (`tab-oem-oes`)
- Direct cross-referencing from OEM part numbers (Maruti, Tata, Hyundai, Toyota, Mahindra, VW/Skoda) to Tier-1 OES brands (Bosch, Valeo, TVS, Denso, Lumax, etc.).
- Displays real-time Unit Cost difference, Customer Savings (₹ / %), and Margin Gain calculation per unit.
- Priority brand recommendations based on catalog supply availability and fulfillment efficiency.

### 2. Vehicle Taxonomy Explorer (`tab-overall-catalogue`)
- Intuitive 4-step drill-down:
  1. **Make Selection:** 14+ major domestic and international manufacturers with verified OEM brand logos.
  2. **Model & Generation:** Detailed vehicle variants with official manufacturing year ranges.
  3. **Vehicle Hierarchy Inspection:** Interactive wireframe alignment showing component location.
  4. **Dual Aggregate & Sub-Aggregate Split:** Independent dual-box taxonomy with multi-select support for simultaneous subsystem evaluation (e.g., Brake System + Clutch & Transmission).

### 3. Sales Analytics Dashboard (`tab-sales-analytics`)
- **CF Sales View:** Dedicated counter-order tracking, B2B order velocity, and distributor volume trends.
- **RF Sales View:** Retail outlet replenishment velocity, workshop demand patterns, and consumer SKU popularity.
- **Executive Overview:** Unified trend lines, brand market-share donuts, and daily/monthly run-rate tracking.

### 4. Inventory Valuation & Stock Engine (`tab-inventory`)
- Unified stock visibility across all operational warehouses.
- Automated valuation calculation: Total Stock Value = Available Quantity &times; Weighted Unit Cost / MRP.
- Client-side Excel export powered by SheetJS (`.xlsx`) with custom filtering by Make, Category, or Stock Status.

### 5. Catalog AI Copilot (`tab-catalog-ai`)
- Natural language query parser for catalog assistants and sales personnel.
- Pre-loaded inquiry scripts and part number troubleshooting queries.

---

## 💻 Tech Stack & Dependencies

- **Backend:** Python 3.10+, Flask, Gunicorn, Gzip Stream Engine
- **Frontend:** Modern Semantic HTML5, Vanilla JavaScript (ES6+ modular portal architecture), CSS3 Custom Variables & Glassmorphism UI
- **Visualizations:** Chart.js (v4.4.1)
- **Data Export & Processing:** SheetJS (xlsx.full.min.js)
- **Deployment Platform:** Render Cloud (`render.yaml` configuration with zero downtime deploys)

---

## ⚙️ Local Development Setup

To run AUTO NEXA on your local development machine:

```bash
# 1. Clone the repository
git clone https://github.com/Jinoraj25/AUTO-NEXA.git
cd AUTO-NEXA

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Start the local server
python server.py

# 4. Open in your web browser
# Navigate to http://localhost:8000
```

---

## 👤 Candidate Profile & Contact

**Jino George**  
*Catalog Analyst & Automotive Data Solutions Engineer*  
- **Specialization:** Automotive Aftermarket Taxonomy, Master Data Management (MDM), OEM/OES Cross-Referencing, Supply Chain & Inventory Optimization.
- **GitHub:** [@Jinoraj25](https://github.com/Jinoraj25)
- **Project Repository:** [https://github.com/Jinoraj25/AUTO-NEXA](https://github.com/Jinoraj25/AUTO-NEXA)

---
*AUTO NEXA is an enterprise catalog intelligence project showcasing advanced automotive data engineering, taxonomy standardization, and full-stack performance optimization.*
