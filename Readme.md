# NYC Subway Delay Analytics Dashboard

A multi-page interactive dashboard for exploring NYC MTA subway delay data — built without pandas, using a fully custom CSV parser, DataFrame engine, and SQL-equivalent operations.

## Features

- Custom CSV parser with quoted-field support
- Custom DataFrame class implementing: SELECT (projection), WHERE (filtering with AND/OR), GROUP BY (sum, count, min, max, avg), INNER/LEFT JOIN with hash indexing
- Interactive Streamlit dashboard with 8 pages
- Plotly visualizations: delay trends, line comparisons, category breakdowns
- Live SQL query explorer powered by SQLite

## Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.x | Core language |
| Streamlit | Dashboard UI |
| Plotly Express | Charts & visualizations |
| SQLite (stdlib) | In-app SQL query engine |
| MTA Open Data | Source dataset |

## Project Structure

```
nyc-delay-dashboard/
├── src/
│   ├── app.py                    # Streamlit dashboard (8 pages)
│   └── core_data.py              # Custom CSV parser & DataFrame engine
├── data/
│   ├── subway_delays.csv         # Primary MTA delay dataset
│   └── subway_stations_for_join.csv  # Station lookup table (for join demo)
├── requirements.txt              # Python dependencies
├── README.md                     # Project documentation
└── .gitignore
```

## Setup & Run

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the dashboard
streamlit run src/app.py
```

Open http://localhost:8501 in your browser.

## Dashboard Pages

| Page | Description |
|---|---|
| Home | Dataset overview, row count, column explorer |
| Data Loading & Parsing | Upload any CSV and parse with custom engine |
| Projection | Column selection demo (SQL SELECT equivalent) |
| Filter Data | IN/NOT IN, BETWEEN, LIKE-style search with AND/OR logic |
| Group By & Aggregation | Multi-column GROUP BY with sum/count/min/max/avg |
| Join Operations | INNER and LEFT join: self join or station lookup join |
| Charts & Insights | Plotly visualizations: delays by line, monthly trends, top categories |
| SQL Query Explorer | Write and execute real SQL queries against the dataset |

## Key Findings

Analysis of NYC MTA subway delay data reveals several patterns:

- **Infrastructure & Equipment** is the leading cause of delays across all lines, accounting for the largest share of total delay incidents — primarily door-related issues, braking failures, and signal problems.
- **Crew Availability** is consistently the second-largest delay category, reflecting ongoing staffing pressures system-wide.
- **Weekday delays significantly outpace weekend delays** in total volume, driven by higher train frequency and passenger load on weekdays.
- **Older numbered lines** (1, 2, 3, 4, 5, 6) tend to accumulate more infrastructure-related delays, consistent with aging rolling stock and station infrastructure.
- **External Factors** (debris, utility interference, external agencies) represent a smaller but non-trivial share of delays — a category that is largely outside MTA operational control.
- Monthly trends show **delay spikes in winter months**, likely correlated with weather-related disruptions to track equipment and signal systems.

## Notes

> **MySQL Workbench row limit:** If you previously tested queries in MySQL Workbench and noticed fewer rows than expected, this is caused by Workbench's default `LIMIT 0, 1000` setting on the Results Grid. Uncheck "Limit Rows" under Edit → Preferences → SQL Editor to see full results.
