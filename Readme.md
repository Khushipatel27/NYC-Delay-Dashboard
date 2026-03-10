<div align="center">

# 🚇 NYC Subway Delay Analytics

**An end-to-end data analytics dashboard built from scratch — no pandas, no shortcuts.**

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Plotly](https://img.shields.io/badge/Plotly-Visualizations-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)
[![SQLite](https://img.shields.io/badge/SQLite-In--App_SQL-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![No Pandas](https://img.shields.io/badge/Pandas-NOT_USED-red?style=for-the-badge)](https://github.com)

*Custom CSV parser · Custom DataFrame engine · 8-page interactive dashboard · Live SQL explorer*

---

</div>

## What Is This?

Most data projects import pandas and call it a day.

This one doesn't.

Every piece of data infrastructure here — the CSV parser, the DataFrame class, the filtering engine, the join logic — was built from scratch in Python. Then wrapped in a Streamlit dashboard with Plotly visualizations and a live SQLite query explorer.

The dataset is real NYC MTA subway delay data. The goal: understand **why trains are late, which lines suffer most, and how delays shift across time.**

---

## Dashboard at a Glance

| # | Page | What It Does |
|---|------|-------------|
| 1 | **Home** | Live KPI cards — total records, delays, lines, date range |
| 2 | **Data Loading & Parsing** | Upload any CSV, profile columns, view completeness chart |
| 3 | **Projection** | Pick columns to keep — SQL `SELECT` in action |
| 4 | **Filter Data** | IN/NOT IN, BETWEEN, LIKE with AND/OR logic + match-rate donut |
| 5 | **Group By & Aggregation** | Multi-column GROUP BY with auto bar + pie charts |
| 6 | **Join Operations** | INNER & LEFT join with match-rate visualization |
| 7 | **Charts & Insights** | 5 Plotly charts — trends, categories, weekday vs weekend |
| 8 | **SQL Query Explorer** | Write real SQL against an in-memory SQLite database |

---

## Under the Hood

```
┌─────────────────────────────────────────────────────┐
│                    app.py (UI layer)                 │
│         8 Streamlit pages · Plotly charts            │
└────────────────────┬────────────────────────────────┘
                     │ calls
┌────────────────────▼────────────────────────────────┐
│               core_data.py (engine layer)            │
│                                                      │
│  CSVParser ──► DataFrame                             │
│                  ├── .select()      →  SQL SELECT    │
│                  ├── .filter_data() →  SQL WHERE     │
│                  ├── .group_by()    →  SQL GROUP BY  │
│                  └── .join()        →  SQL JOIN      │
└────────────────────┬────────────────────────────────┘
                     │ loaded into
┌────────────────────▼────────────────────────────────┐
│            SQLite (in-memory, page 8 only)           │
│         Accepts raw SQL · no external DB needed      │
└─────────────────────────────────────────────────────┘
```

---

## Project Structure

```
nyc-delay-dashboard/
├── src/
│   ├── app.py                    # Streamlit dashboard (8 pages)
│   └── core_data.py              # Custom CSV parser & DataFrame engine
├── data/
│   ├── subway_delays.csv         # Primary MTA delay dataset
│   └── subway_stations_for_join.csv  # Station lookup table
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/nyc-delay-dashboard.git
cd nyc-delay-dashboard

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac / Linux

# Install dependencies
pip install -r requirements.txt

# Launch the dashboard
streamlit run src/app.py
```

Open **http://localhost:8501** in your browser.

---

## Key Findings

> Analysis of NYC MTA subway delay records reveals consistent, data-backed patterns:

**Infrastructure dominates.**
Door failures, braking issues, and signal problems under *Infrastructure & Equipment* account for the single largest share of delays — a systemic problem tied to aging rolling stock.

**Staffing is the hidden pressure.**
*Crew Availability* is the #2 delay cause system-wide, reflecting ongoing workforce challenges that technology alone can't fix.

**Weekdays are exponentially worse.**
Weekday delays significantly outpace weekends — not just because there are more trains, but because higher frequency means disruptions cascade across the entire schedule.

**Older lines, more problems.**
Numbered lines (1–6) accumulate more infrastructure-related delays than lettered lines, consistent with their older physical infrastructure and rolling stock.

**Winter spikes are real.**
Monthly trends show delay volume rising in winter months — weather impacts track equipment, signals, and external factors simultaneously.

**External factors are unpredictable.**
Debris, utility interference, and third-party agency issues represent a smaller but stubborn share of delays — entirely outside MTA operational control.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Language | Python 3.x | Core engine + UI |
| Dashboard | Streamlit | Rapid interactive UI |
| Charts | Plotly Express + Graph Objects | Publication-quality interactive visuals |
| SQL Engine | SQLite (stdlib) | Zero-dependency in-app SQL |
| Data Engine | Custom (this repo) | No pandas — built from scratch |
| Dataset | MTA Open Data | Real NYC subway delay records |

---

<div align="center">

*Built as a portfolio project demonstrating data engineering fundamentals, SQL fluency, and analytical thinking.*

</div>
