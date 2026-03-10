# NYC Subway Delay Analytics Dashboard — CLAUDE.md

## Project Overview
A multi-page Streamlit dashboard for analyzing NYC MTA subway delay data.
Built **without pandas** — uses a fully custom CSV parser and DataFrame class.

## Architecture

### Files
- `src/app.py` — Streamlit UI with 8 pages
- `src/core_data.py` — all data engine logic (CSVParser, DataFrame, helpers)
- `data/subway_delays.csv` — primary dataset
- `data/subway_stations_for_join.csv` — lookup table for join demo
- `requirements.txt` — Python dependencies
- `.gitignore`

### core_data.py — Key Classes
- `CSVParser` — custom CSV reader, handles quoted fields with embedded commas
- `DataFrame` — custom columnar store (dict of lists), implements:
  - `select()` — projection (SQL SELECT)
  - `filter_data()` — row filtering (SQL WHERE), accepts a callable condition
  - `group_by()` — aggregation: sum, count, max, min, avg (SQL GROUP BY)
  - `join()` — INNER and LEFT joins with hash-index optimization
  - `to_rows()`, `head()` — utility methods
- `load_mta_data(path)` — convenience loader
- `print_table()` — debug console printer

### app.py — Dashboard Pages
1. **Home** — dataset overview, sample rows, column selector
2. **Data Loading & Parsing** — upload any CSV, parse with custom engine
3. **Projection** — column selector using `DataFrame.select()`
4. **Filter Data** — IN/NOT IN, BETWEEN (numeric range), LIKE-style text search, AND/OR logic
5. **Group By & Aggregation** — multi-column group by with all 5 agg functions
6. **Join Operations** — self join or lookup join (INNER/LEFT), column picker for output
7. **Charts & Insights** — Plotly visualizations: delays by line, monthly trends, top categories, key insights
8. **SQL Query Explorer** — write and run real SQL queries against an in-memory SQLite DB

## Dependencies
- `streamlit` — dashboard UI framework
- `plotly` — charts and visualizations (via `plotly.express`)
- `sqlite3` — in-app SQL query engine (Python stdlib, no install needed)

## Data Notes
- `delays` column auto-converted to int (or None)
- `day_type` normalized: 1/"1" → "Weekday", 2/"2" → "Weekend"
- Headers lowercased on load

## Run Instructions
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run src/app.py
```

## Known Limitations
- Self join on a large dataset can be slow (O(n²) worst case, but hash index mitigates it)
- No actual external SQL database — SQL-equivalent logic is in Python; the SQL Query page uses an in-memory SQLite DB
