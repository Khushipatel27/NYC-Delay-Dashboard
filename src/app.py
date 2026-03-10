import streamlit as st
import tempfile
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from core_data import DataFrame, CSVParser, load_mta_data

CSV_PATH = "data/subway_delays.csv"

# Global CSS 

def inject_css():
    st.markdown("""
    <style>
    /* Sidebar gradient */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #060b18 0%, #0a1628 60%, #0d1f3c 100%);
        border-right: 1px solid #1e2d4a;
    }

    /* Hero banner */
    .hero {
        background: linear-gradient(135deg, #0039A6 0%, #0052cc 45%, #003580 100%);
        border-radius: 14px;
        padding: 2.8rem 2.4rem 2.2rem;
        text-align: center;
        box-shadow: 0 6px 30px rgba(0,57,166,0.45);
        margin-bottom: 2rem;
    }
    .hero-title {
        color: #ffffff;
        font-size: 2.3rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0 0 0.5rem;
    }
    .hero-sub {
        color: #a8c8ff;
        font-size: 1.05rem;
        margin: 0;
        font-weight: 400;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(255,255,255,0.15);
        color: #d0e8ff;
        border-radius: 20px;
        padding: 0.25rem 0.8rem;
        font-size: 0.78rem;
        margin-top: 1rem;
        letter-spacing: 0.04em;
    }

    /* KPI cards */
    .kpi-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
    .kpi-card {
        flex: 1;
        background: #141828;
        border: 1px solid #1e2d4a;
        border-top: 3px solid #0052cc;
        border-radius: 10px;
        padding: 1.1rem 1rem 0.9rem;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.35);
        transition: transform 0.15s;
    }
    .kpi-card:hover { transform: translateY(-2px); }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #4d9fff;
        line-height: 1.1;
    }
    .kpi-label {
        font-size: 0.75rem;
        color: #6b7a99;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-top: 0.35rem;
    }

    /* Section divider */
    .divider { border: none; border-top: 1px solid #1e2d4a; margin: 1.8rem 0; }

    /* Insight box */
    .insight {
        background: #111827;
        border-left: 4px solid #4d9fff;
        border-radius: 0 8px 8px 0;
        padding: 0.85rem 1.2rem;
        margin: 0.55rem 0;
        color: #c0d0ea;
        font-size: 0.93rem;
        line-height: 1.5;
    }
    .insight strong { color: #7ab8ff; }

    /* Page header underline */
    .page-header {
        font-size: 1.9rem;
        font-weight: 700;
        color: #e8eaf0;
        border-bottom: 2px solid #0052cc;
        padding-bottom: 0.4rem;
        margin-bottom: 1.2rem;
    }

    /* Sidebar brand */
    .sidebar-brand {
        text-align: center;
        padding: 1.2rem 0.5rem 1rem;
        border-bottom: 1px solid #1e2d4a;
        margin-bottom: 0.8rem;
    }
    .sidebar-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #7ab8ff;
        letter-spacing: 0.02em;
    }
    .sidebar-sub {
        font-size: 0.72rem;
        color: #4a5a7a;
        margin-top: 0.2rem;
    }
    </style>
    """, unsafe_allow_html=True)


def kpi_card(label: str, value: str) -> str:
    return f"""
    <div class="kpi-card">
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>"""


def insight_box(text: str) -> None:
    st.markdown(f'<div class="insight">{text}</div>', unsafe_allow_html=True)


def page_header(title: str) -> None:
    st.markdown(f'<div class="page-header">{title}</div>', unsafe_allow_html=True)


PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="sans-serif", color="#c8d8f0"),
    margin=dict(t=50, b=40, l=40, r=20),
)

# Data loading 

@st.cache_data
def load_all_data():
    return load_mta_data(CSV_PATH)


try:
    mta = load_all_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()


@st.cache_resource
def get_sqlite_connection():
    parser = CSVParser(CSV_PATH)
    parser.read_csv()
    headers = parser.columns
    data_rows = parser.data

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE subway_delays (
            month TEXT, division TEXT, line TEXT, day_type TEXT,
            reporting_category TEXT, subcategory TEXT, delays INTEGER
        )
    """)

    col_index = {h: i for i, h in enumerate(headers)}
    rows_to_insert = []
    for row in data_rows:
        raw_day = row[col_index.get("day_type", -1)] if "day_type" in col_index else None
        if raw_day is not None:
            s = str(raw_day).strip()
            day_type = {"1": "Weekday", "2": "Weekend", "weekday": "Weekday", "weekend": "Weekend"}.get(s.lower(), raw_day)
        else:
            day_type = None

        raw_delays = row[col_index["delays"]] if "delays" in col_index else None
        try:
            delays = int(raw_delays)
        except (TypeError, ValueError):
            delays = None

        rows_to_insert.append((
            row[col_index.get("month", 0)] if "month" in col_index else None,
            row[col_index.get("division", 0)] if "division" in col_index else None,
            row[col_index.get("line", 0)] if "line" in col_index else None,
            day_type,
            row[col_index.get("reporting_category", 0)] if "reporting_category" in col_index else None,
            row[col_index.get("subcategory", 0)] if "subcategory" in col_index else None,
            delays,
        ))

    cursor.executemany("INSERT INTO subway_delays VALUES (?,?,?,?,?,?,?)", rows_to_insert)
    conn.commit()
    return conn


def unique_values(df: DataFrame, col: str):
    return sorted(set(df.df_dict[col]))


# Page 1: Home 

def show_home_page(mta: DataFrame):
    inject_css()

    # Hero
    st.markdown("""
    <div class="hero">
        <div class="hero-title">NYC Subway Delay Analytics</div>
        <div class="hero-sub">Exploring MTA delay patterns with a custom-built data engine</div>
        <div class="hero-badge">No pandas &nbsp;·&nbsp; Custom DataFrame &nbsp;·&nbsp; SQLite &nbsp;·&nbsp; Plotly</div>
    </div>
    """, unsafe_allow_html=True)

    # KPI cards
    total_delays = sum(v for v in mta.df_dict["delays"] if v is not None)
    unique_lines  = len(set(mta.df_dict["line"]))
    unique_cats   = len(set(mta.df_dict["reporting_category"]))
    months = sorted(set(m for m in mta.df_dict["month"] if m))
    date_range = f"{months[0][:7]} – {months[-1][:7]}" if len(months) >= 2 else (months[0][:7] if months else "N/A")

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(kpi_card("Total Records",   f"{len(mta):,}"),      unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("Total Delays",    f"{total_delays:,}"),  unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("Subway Lines",    str(unique_lines)),    unsafe_allow_html=True)
    with c4: st.markdown(kpi_card("Date Range",      date_range),           unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # Dataset preview
    page_header("Dataset Preview")
    st.caption(f"Source: `{CSV_PATH}`  ·  {len(mta.columns)} columns")

    selected_cols = st.multiselect(
        "Columns to display:",
        options=mta.columns,
        default=mta.columns,
        key="home_cols",
    )

    rows = [{c: row[c] for c in selected_cols} for row in mta.to_rows(15)]
    st.dataframe(rows, use_container_width=True)


# Page 2: Data Loading & Parsing 

def show_loading_page():
    inject_css()
    page_header("Data Loading & Parsing")

    st.markdown("""
    Upload any CSV file. It will be parsed using the **custom `CSVParser` + `DataFrame`**
    engine from `core_data.py` — no pandas involved.
    """)

    uploaded = st.file_uploader("Upload a CSV file", type=["csv"])

    if uploaded is None:
        st.info("Upload a CSV file above to see the parsing engine in action.")
        return

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded.getvalue())
        tmp_path = tmp.name

    try:
        parsed_df = load_mta_data(tmp_path)
    except Exception as e:
        st.error(f"Error parsing file: {e}")
        return

    c1, c2 = st.columns(2)
    c1.metric("Rows parsed", f"{len(parsed_df):,}")
    c2.metric("Columns detected", len(parsed_df.columns))

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    selected_cols = st.multiselect(
        "Columns to display:",
        options=parsed_df.columns,
        default=parsed_df.columns,
        key="upload_cols",
    )

    st.caption("First 20 rows — after type conversion & normalization")
    rows = [{c: row[c] for c in selected_cols} for row in parsed_df.to_rows(20)]
    st.dataframe(rows, use_container_width=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    page_header("Dataset Profile")

    # Chart 1: Column completeness (% non-null)
    completeness = []
    for col in parsed_df.columns:
        vals = parsed_df.df_dict[col]
        non_null = sum(1 for v in vals if v is not None and str(v).strip() != "")
        completeness.append({"column": col, "pct_filled": round(non_null / len(vals) * 100, 1) if vals else 0})

    fig_complete = px.bar(
        completeness, x="pct_filled", y="column", orientation="h",
        title="Column Completeness (%)",
        labels={"pct_filled": "% Non-Null", "column": "Column"},
        color="pct_filled",
        color_continuous_scale=["#ff4b4b", "#ffa64d", "#4d9fff"],
        range_color=[0, 100],
    )
    fig_complete.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False,
                               yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_complete, use_container_width=True)

    # Chart 2: Delay value distribution (if delays column exists)
    if "delays" in parsed_df.columns:
        delay_vals = [v for v in parsed_df.df_dict["delays"] if v is not None]
        if delay_vals:
            buckets = {}
            bucket_size = max(1, max(delay_vals) // 20) if delay_vals else 1
            for v in delay_vals:
                b = (v // bucket_size) * bucket_size
                buckets[b] = buckets.get(b, 0) + 1
            hist_rows = sorted([{"range": f"{k}–{k+bucket_size-1}", "count": v, "sort_key": k}
                                  for k, v in buckets.items()], key=lambda r: r["sort_key"])
            fig_hist = px.bar(
                hist_rows, x="range", y="count",
                title="Delay Value Distribution",
                labels={"range": "Delay Range", "count": "Frequency"},
                color="count", color_continuous_scale="Blues",
            )
            fig_hist.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False,
                                   xaxis_tickangle=-45)
            st.plotly_chart(fig_hist, use_container_width=True)


# Page 3: Projection 
def show_projection_page(mta: DataFrame):
    inject_css()
    page_header("Projection  (SQL SELECT)")

    st.markdown("Choose which columns to keep. Demonstrates `DataFrame.select()` — the SQL `SELECT` equivalent.")

    selected_cols = st.multiselect(
        "Columns to keep:",
        options=mta.columns,
        default=mta.columns,
        key="projection_cols",
    )

    max_rows = st.number_input(
        "Rows to preview:",
        min_value=1, max_value=len(mta),
        value=min(100, len(mta)), step=10,
        key="projection_max_rows",
    )

    if st.button("Run Projection", type="primary"):
        if not selected_cols:
            st.warning("Select at least one column.")
            return

        projected_df = mta.select(selected_cols)
        st.success(f"Projection complete — {len(projected_df):,} rows × {len(projected_df.columns)} columns.")
        rows = [{c: row[c] for c in projected_df.columns} for row in projected_df.to_rows(int(max_rows))]
        st.dataframe(rows, use_container_width=True)

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        page_header("Projected Column Breakdown")

        cat_cols = [c for c in projected_df.columns if c in ("line","division","day_type","reporting_category","subcategory","month")]
        num_cols = [c for c in projected_df.columns if c == "delays"]

        chart_cols = st.columns(2) if (cat_cols and num_cols) else st.columns(1)
        col_idx = 0

        if cat_cols:
            # Value counts for the first categorical column
            col_to_count = cat_cols[0]
            counts: dict = {}
            for v in projected_df.df_dict[col_to_count]:
                if v is not None:
                    counts[v] = counts.get(v, 0) + 1
            count_rows = sorted([{"value": k, "count": v} for k, v in counts.items()],
                                 key=lambda r: r["count"], reverse=True)
            fig_cat = px.bar(
                count_rows[:25], x="count", y="value", orientation="h",
                title=f"Value Counts — '{col_to_count}'",
                labels={"count": "Count", "value": col_to_count},
                color="count", color_continuous_scale="Blues",
            )
            fig_cat.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False,
                                  yaxis={"categoryorder": "total ascending"})
            with chart_cols[col_idx]:
                st.plotly_chart(fig_cat, use_container_width=True)
            col_idx += 1

        if num_cols:
            delay_vals = [v for v in projected_df.df_dict["delays"] if v is not None]
            if delay_vals:
                bucket_size = max(1, max(delay_vals) // 15) if delay_vals else 1
                buckets: dict = {}
                for v in delay_vals:
                    b = (v // bucket_size) * bucket_size
                    buckets[b] = buckets.get(b, 0) + 1
                hist_rows = sorted([{"range": f"{k}–{k+bucket_size-1}", "count": v, "sk": k}
                                     for k, v in buckets.items()], key=lambda r: r["sk"])
                fig_num = px.bar(
                    hist_rows, x="range", y="count",
                    title="Delays Distribution (projected rows)",
                    labels={"range": "Delay Range", "count": "Frequency"},
                    color="count", color_continuous_scale="Oranges",
                )
                fig_num.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False,
                                      xaxis_tickangle=-45)
                with chart_cols[col_idx]:
                    st.plotly_chart(fig_num, use_container_width=True)


# Page 4: Filter Data 

def show_filter_page(mta: DataFrame):
    inject_css()
    page_header("Filter Data  (SQL WHERE)")

    st.markdown("""
    Apply one or more filters and combine them with **AND** or **OR** logic.
    Supports categorical (IN / NOT IN), numeric range (BETWEEN), and text search (LIKE).
    """)

    filter_logic = st.radio("Combine conditions with:", ["AND", "OR"], horizontal=True, key="filter_logic")

    selected_cols = st.multiselect("Columns to display:", options=mta.columns, default=mta.columns, key="filter_col_select")

    available_filters = ["Line","Division","Day Type","Reporting Category","Subcategory","Month","Min Delays","Max Delays"]
    chosen_filters = st.multiselect("Filter by:", available_filters, key="filter_fields")

    filter_values = {}

    if "Line" in chosen_filters:
        filter_values["line"] = st.multiselect("Line(s):", unique_values(mta, "line"), key="filter_line")
        filter_values["line_not"] = st.checkbox("Exclude (NOT IN)", key="filter_line_not")

    if "Division" in chosen_filters:
        filter_values["division"] = st.multiselect("Division(s):", unique_values(mta, "division"), key="filter_div")
        filter_values["division_not"] = st.checkbox("Exclude (NOT IN)", key="filter_div_not")

    if "Day Type" in chosen_filters:
        filter_values["day_type"] = st.multiselect("Day type(s):", unique_values(mta, "day_type"), key="filter_daytype")
        filter_values["day_type_not"] = st.checkbox("Exclude (NOT IN)", key="filter_daytype_not")

    if "Reporting Category" in chosen_filters:
        filter_values["reporting_category"] = st.multiselect("Category(ies):", unique_values(mta, "reporting_category"), key="filter_rcat")
        filter_values["reporting_category_not"] = st.checkbox("Exclude (NOT IN)", key="filter_rcat_not")

    if "Subcategory" in chosen_filters:
        filter_values["subcategory"] = st.multiselect("Subcategory(ies):", unique_values(mta, "subcategory"), key="filter_subcat")
        filter_values["subcategory_not"] = st.checkbox("Exclude (NOT IN)", key="filter_subcat_not")

    if "Month" in chosen_filters:
        filter_values["month"] = st.multiselect("Month(s):", unique_values(mta, "month"), key="filter_month")
        filter_values["month_not"] = st.checkbox("Exclude (NOT IN)", key="filter_month_not")

    if "Min Delays" in chosen_filters:
        filter_values["min_delays"] = st.number_input("Minimum delays:", min_value=0, value=0, key="filter_min_delay")

    if "Max Delays" in chosen_filters:
        filter_values["max_delays"] = st.number_input("Maximum delays:", min_value=0, value=1000, key="filter_max_delay")

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.subheader("Text Search (LIKE)  — optional")
    use_like = st.checkbox("Enable LIKE-style text search", key="filter_use_like")
    like_col, like_pattern, like_mode = None, "", "contains"

    if use_like:
        text_cols = [c for c in ["line","division","day_type","reporting_category","subcategory","month"] if c in mta.columns]
        like_col = st.selectbox("Column:", text_cols, key="filter_like_col")
        like_pattern = st.text_input("Pattern (e.g. 'crew', 'signal'):", key="filter_like_pattern")
        like_mode = st.selectbox("Match type:", ["contains","starts with","ends with","exact"], key="filter_like_mode")

    if st.button("Apply Filters", type="primary"):
        def condition(i, df):
            conds = []

            for field in ["line","division","day_type","reporting_category","subcategory","month"]:
                if field in filter_values:
                    selected = filter_values[field]
                    use_not  = filter_values.get(f"{field}_not", False)
                    if selected:
                        val = df[field][i]
                        conds.append(val not in selected if use_not else val in selected)

            if "min_delays" in filter_values or "max_delays" in filter_values:
                d = df["delays"][i]
                ok = True
                if "min_delays" in filter_values and (d is None or d < filter_values["min_delays"]): ok = False
                if "max_delays" in filter_values and (d is None or d > filter_values["max_delays"]): ok = False
                conds.append(ok)

            if use_like and like_col and like_pattern.strip():
                val = df[like_col][i]
                if val is None:
                    conds.append(False)
                else:
                    s, p = str(val).lower(), like_pattern.lower()
                    match = (p in s) if like_mode == "contains" else \
                            s.startswith(p) if like_mode == "starts with" else \
                            s.endswith(p) if like_mode == "ends with" else (s == p)
                    conds.append(match)

            if not conds:
                return True
            return all(conds) if filter_logic == "AND" else any(conds)

        filtered_df = mta.filter_data(condition)
        matched   = len(filtered_df)
        total     = len(mta)
        excluded  = total - matched
        pct       = round(matched / total * 100, 1) if total else 0

        st.success(f"Found **{matched:,}** matching rows ({pct}% of dataset).")

        # Filter result charts 
        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        page_header("Filter Results — Visual Breakdown")

        c1, c2 = st.columns(2)

        # Donut: matched vs excluded
        with c1:
            fig_match = go.Figure(go.Pie(
                labels=["Matched", "Excluded"],
                values=[matched, excluded],
                hole=0.58,
                marker=dict(colors=["#4d9fff", "#2a2d3e"],
                            line=dict(color="#0f1117", width=2)),
                textinfo="label+percent",
                textfont=dict(color="#e8eaf0"),
            ))
            fig_match.update_layout(**PLOTLY_LAYOUT, title="Match Rate vs Total Dataset",
                                    showlegend=False)
            st.plotly_chart(fig_match, use_container_width=True)

        # Bar: filtered delays by line or by reporting_category
        with c2:
            bar_col = "line" if "line" in filtered_df.columns else (
                      "reporting_category" if "reporting_category" in filtered_df.columns else None)
            if bar_col and "delays" in filtered_df.columns:
                grp = filtered_df.group_by([bar_col], "delays", "sum", "total_delays")
                grp_rows = sorted(grp.to_rows(), key=lambda r: r["total_delays"] or 0, reverse=True)[:15]
                fig_bar = px.bar(
                    grp_rows, x="total_delays", y=bar_col, orientation="h",
                    title=f"Filtered Delays by {bar_col.replace('_',' ').title()}",
                    labels={"total_delays": "Total Delays", bar_col: bar_col.title()},
                    color="total_delays", color_continuous_scale="Reds",
                )
                fig_bar.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False,
                                      yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig_bar, use_container_width=True)

        st.caption(f"Showing up to 500 of {matched:,} rows")
        rows = [{c: row[c] for c in selected_cols} for row in filtered_df.to_rows(500)]
        st.dataframe(rows, use_container_width=True)


# Page 5: Group By & Aggregation 

def show_groupby_page(mta: DataFrame):
    inject_css()
    page_header("Group By & Aggregation  (SQL GROUP BY)")

    st.markdown("Group by one or more columns and aggregate the `delays` column.")

    groupable = ["line","division","day_type","reporting_category","subcategory","month"]

    col1, col2 = st.columns(2)
    with col1:
        group_col = st.selectbox("Primary group-by column:", groupable, index=0)
        agg_func   = st.selectbox("Aggregation function:", ["sum","count","max","min","avg"])
    with col2:
        extra_cols = st.multiselect("Additional group-by columns (optional):", [c for c in groupable if c != group_col])

    metric_col = "avg_delays" if agg_func == "avg" else f"{agg_func}_delays"
    all_result_cols = [group_col] + extra_cols + [metric_col]

    selected_display = st.multiselect("Columns to show:", all_result_cols, default=all_result_cols, key="groupby_display_cols")

    if st.button("Run Group By", type="primary"):
        grouped = mta.group_by(
            group_cols=[group_col] + extra_cols,
            agg_col="delays",
            agg_func=agg_func,
            new_col_name=metric_col,
        )
        rows = grouped.to_rows()
        filtered_rows = [{c: row[c] for c in selected_display} for row in rows]
        st.success(f"{agg_func.upper()} of delays grouped by **{', '.join([group_col] + extra_cols)}** — {len(filtered_rows):,} groups.")

        # ── Auto-chart the grouped result ──
        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        page_header("Aggregation Chart")

        chart_rows = sorted(rows, key=lambda r: r.get(metric_col) or 0, reverse=True)

        if not extra_cols:
            # Single group-by: horizontal bar + optional pie
            c1, c2 = st.columns([3, 2])
            with c1:
                color_scale = {"sum": "Blues", "count": "Greens", "avg": "Purples",
                               "max": "Oranges", "min": "Reds"}.get(agg_func, "Blues")
                fig_grp = px.bar(
                    chart_rows[:30], x=metric_col, y=group_col, orientation="h",
                    title=f"{agg_func.upper()} of Delays by {group_col.replace('_',' ').title()}",
                    labels={metric_col: metric_col.replace("_", " ").title(),
                            group_col: group_col.replace("_", " ").title()},
                    color=metric_col, color_continuous_scale=color_scale,
                )
                fig_grp.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False,
                                      yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig_grp, use_container_width=True)

            with c2:
                if len(chart_rows) <= 20:
                    labels = [str(r[group_col]) for r in chart_rows]
                    values = [r.get(metric_col) or 0 for r in chart_rows]
                    fig_pie = go.Figure(go.Pie(
                        labels=labels, values=values, hole=0.45,
                        textinfo="label+percent",
                        textfont=dict(color="#e8eaf0"),
                        marker=dict(line=dict(color="#0f1117", width=1)),
                    ))
                    fig_pie.update_layout(**PLOTLY_LAYOUT,
                                         title=f"Share by {group_col.replace('_',' ').title()}",
                                         showlegend=False)
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("Pie chart available when there are ≤ 20 groups.")
        else:
            # Multi group-by: grouped bar (primary group on x, secondary as color)
            fig_multi = px.bar(
                chart_rows[:100],
                x=group_col, y=metric_col,
                color=extra_cols[0] if extra_cols else None,
                barmode="group",
                title=f"{agg_func.upper()} of Delays — {group_col} × {extra_cols[0] if extra_cols else ''}",
                labels={metric_col: metric_col.replace("_"," ").title()},
            )
            fig_multi.update_layout(**PLOTLY_LAYOUT, xaxis_tickangle=-40)
            st.plotly_chart(fig_multi, use_container_width=True)

        st.dataframe(filtered_rows[:500], use_container_width=True)


# Page 6: Join Operations 

def show_join_page(mta: DataFrame):
    inject_css()
    page_header("Join Operations  (SQL JOIN)")

    st.markdown("""
    Demonstrates `DataFrame.join()` — **INNER** and **LEFT** joins using a hash index for efficiency.
    Choose between a self join or a lookup join against the station info table.
    """)

    col1, col2 = st.columns([1, 2])
    with col1:
        join_type = st.radio("Join type:", ["INNER", "LEFT"], horizontal=True, key="join_type")
        preview_limit = st.slider("Max rows to preview:", 50, 500, 200, 50, key="join_preview_limit")

    lookup_df = None
    try:
        lookup_df = load_mta_data("data/subway_stations_for_join.csv")
    except Exception as e:
        st.warning(f"Could not load station lookup table: {e}")

    join_mode = st.radio(
        "Join mode:",
        ["Self Join (delays ⋈ delays)", "Lookup Join (delays ⋈ station info)"],
        key="join_mode",
    )

    joined_df = None
    selected_cols_final = []

    if join_mode.startswith("Self Join"):
        st.subheader("Self Join")
        default_idx = mta.columns.index("line") if "line" in mta.columns else 0
        join_col = st.selectbox("Join column:", mta.columns, index=default_idx, key="self_join_col")
        left_keep  = st.multiselect("Columns from LEFT:",  mta.columns, default=mta.columns, key="self_left_keep")
        right_keep = st.multiselect("Columns from RIGHT:", mta.columns, default=[], key="self_right_keep")

        if st.button("Run Self Join", key="btn_self_join", type="primary"):
            try:
                with st.spinner("Running self join..."):
                    result = mta.join(other=mta, left_on=join_col, right_on=join_col, how=join_type.lower())
                joined_df = result
                selected_cols_final = [f"left_{c}" for c in left_keep] + [f"right_{c}" for c in right_keep]
                st.success(f"Self join complete — {len(joined_df):,} rows × {len(joined_df.columns)} columns.")
            except Exception as e:
                st.error(f"Join error: {e}")
                return
    else:
        st.subheader("Lookup Join  (delays ⋈ station info)")
        if lookup_df is None:
            st.info("Station lookup table unavailable.")
        else:
            default_left  = mta.columns.index("line")       if "line" in mta.columns       else 0
            default_right = lookup_df.columns.index("line") if "line" in lookup_df.columns else 0
            left_col  = st.selectbox("Join column (delays):",         mta.columns,       index=default_left,  key="lookup_left_col")
            right_col = st.selectbox("Join column (station info):",   lookup_df.columns, index=default_right, key="lookup_right_col")
            left_keep  = st.multiselect("Columns from LEFT:",  mta.columns,       default=mta.columns, key="lookup_left_keep")
            right_keep = st.multiselect("Columns from RIGHT:", lookup_df.columns,
                                        default=["station_name","borough"] if "station_name" in lookup_df.columns else [],
                                        key="lookup_right_keep")

            if st.button("Run Lookup Join", key="btn_lookup_join", type="primary"):
                try:
                    with st.spinner("Running lookup join..."):
                        result = mta.join(other=lookup_df, left_on=left_col, right_on=right_col, how=join_type.lower())
                    joined_df = result
                    selected_cols_final = [f"left_{c}" for c in left_keep] + [f"right_{c}" for c in right_keep]
                    st.success(f"Lookup join complete — {len(joined_df):,} rows × {len(joined_df.columns)} columns.")
                except Exception as e:
                    st.error(f"Join error: {e}")
                    return

    if joined_df is not None:
        if not selected_cols_final:
            selected_cols_final = joined_df.columns

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        page_header("Join Result — Visual Summary")

        c1, c2 = st.columns(2)

        # Donut: matched vs unmatched (nulls on right side = LEFT join misses)
        with c1:
            right_cols = [c for c in joined_df.columns if c.startswith("right_")]
            if right_cols:
                check_col = right_cols[0]
                matched_count  = sum(1 for v in joined_df.df_dict[check_col] if v is not None)
                unmatched_count = len(joined_df) - matched_count
                fig_join = go.Figure(go.Pie(
                    labels=["Matched", "Unmatched (NULL)"],
                    values=[matched_count, unmatched_count],
                    hole=0.55,
                    marker=dict(colors=["#4d9fff", "#ff6b6b"],
                                line=dict(color="#0f1117", width=2)),
                    textinfo="label+percent",
                    textfont=dict(color="#e8eaf0"),
                ))
                fig_join.update_layout(**PLOTLY_LAYOUT, title="Row Match Rate",
                                       showlegend=False)
                st.plotly_chart(fig_join, use_container_width=True)

        # Bar: delays by line from joined result (if left_line and left_delays exist)
        with c2:
            line_col   = "left_line"   if "left_line"   in joined_df.columns else None
            delays_col = "left_delays" if "left_delays" in joined_df.columns else None
            if line_col and delays_col:
                grp: dict = {}
                for i in range(len(joined_df)):
                    line_val   = joined_df.df_dict[line_col][i]
                    delays_val = joined_df.df_dict[delays_col][i]
                    if line_val and delays_val is not None:
                        grp[line_val] = grp.get(line_val, 0) + delays_val
                grp_rows = sorted([{"line": k, "total_delays": v} for k, v in grp.items()],
                                   key=lambda r: r["total_delays"], reverse=True)[:20]
                fig_jbar = px.bar(
                    grp_rows, x="total_delays", y="line", orientation="h",
                    title="Delays by Line (joined result)",
                    labels={"total_delays": "Total Delays", "line": "Line"},
                    color="total_delays", color_continuous_scale="Blues",
                )
                fig_jbar.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False,
                                       yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig_jbar, use_container_width=True)

        rows = [{c: row.get(c) for c in selected_cols_final if c in row} for row in joined_df.to_rows(preview_limit)]
        st.caption(f"Showing {min(preview_limit, len(joined_df)):,} of {len(joined_df):,} rows")
        st.dataframe(rows, use_container_width=True)


# Page 7: Charts & Insights 

def show_charts_page(mta: DataFrame):
    inject_css()
    page_header("Charts & Insights")

    st.markdown("Interactive visualizations built from the full dataset using the custom DataFrame engine + Plotly.")

    # Pre-compute all grouped data 
    line_rows = sorted(
        mta.group_by(["line"], "delays", "sum", "total_delays").to_rows(),
        key=lambda r: r["total_delays"] or 0, reverse=True
    )
    month_rows = sorted(
        mta.group_by(["month"], "delays", "sum", "total_delays").to_rows(),
        key=lambda r: r["month"] or ""
    )
    cat_rows = sorted(
        mta.group_by(["reporting_category"], "delays", "sum", "total_delays").to_rows(),
        key=lambda r: r["total_delays"] or 0, reverse=True
    )
    daytype_rows = mta.group_by(["day_type"], "delays", "sum", "total_delays").to_rows()

    # Row 1: Delays by Line + Weekday vs Weekend 
    col1, col2 = st.columns([3, 2])

    with col1:
        fig1 = px.bar(
            line_rows, x="total_delays", y="line", orientation="h",
            color="total_delays", color_continuous_scale="Blues",
            title="Total Delays by Line",
            labels={"total_delays": "Total Delays", "line": "Line"},
        )
        fig1.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False,
                           yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        labels = [r["day_type"] for r in daytype_rows]
        values = [r["total_delays"] or 0 for r in daytype_rows]
        fig2 = go.Figure(go.Pie(
            labels=labels, values=values, hole=0.55,
            marker=dict(colors=["#4d9fff", "#ff6b6b"],
                        line=dict(color="#0f1117", width=2)),
            textinfo="label+percent",
            textfont=dict(color="#e8eaf0"),
        ))
        fig2.update_layout(**PLOTLY_LAYOUT, title="Weekday vs Weekend",
                           showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Row 2: Monthly trend ──
    fig3 = px.area(
        month_rows, x="month", y="total_delays", markers=True,
        title="Monthly Delay Trend",
        labels={"total_delays": "Total Delays", "month": "Month"},
        color_discrete_sequence=["#4d9fff"],
    )
    fig3.update_traces(fill="tozeroy", fillcolor="rgba(77,159,255,0.12)", line=dict(width=2.5))
    fig3.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig3, use_container_width=True)

    # Row 3: Category breakdown + Top 5 subcategories
    col3, col4 = st.columns(2)

    with col3:
        fig4 = px.bar(
            cat_rows, x="total_delays", y="reporting_category", orientation="h",
            color="total_delays", color_continuous_scale="Oranges",
            title="Delays by Reporting Category",
            labels={"total_delays": "Total Delays", "reporting_category": "Category"},
        )
        fig4.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False,
                           yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig4, use_container_width=True)

    with col4:
        subcat_rows = sorted(
            mta.group_by(["subcategory"], "delays", "sum", "total_delays").to_rows(),
            key=lambda r: r["total_delays"] or 0, reverse=True
        )[:10]
        fig5 = px.bar(
            subcat_rows, x="total_delays", y="subcategory", orientation="h",
            color="total_delays", color_continuous_scale="Purples",
            title="Top 10 Delay Subcategories",
            labels={"total_delays": "Total Delays", "subcategory": "Subcategory"},
        )
        fig5.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False,
                           yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig5, use_container_width=True)

    # Key Insights
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    page_header("Key Insights")

    if line_rows:
        top = line_rows[0]
        insight_box(f"<strong>Highest-delay line:</strong> Line {top['line']} with <strong>{top['total_delays']:,}</strong> total delays.")

    if cat_rows:
        top_c = cat_rows[0]
        insight_box(f"<strong>Leading delay cause:</strong> {top_c['reporting_category']} — <strong>{top_c['total_delays']:,}</strong> delays.")

    if len(daytype_rows) == 2:
        d = {r["day_type"]: r["total_delays"] or 0 for r in daytype_rows}
        wkd = d.get("Weekday", 0)
        wke = d.get("Weekend", 0)
        ratio = round(wkd / wke, 1) if wke else "N/A"
        insight_box(f"<strong>Weekday vs Weekend:</strong> Weekday delays are <strong>{ratio}×</strong> higher ({wkd:,} vs {wke:,}).")

    if month_rows:
        peak = max(month_rows, key=lambda r: r["total_delays"] or 0)
        insight_box(f"<strong>Peak month:</strong> {peak['month'][:7]} with <strong>{peak['total_delays']:,}</strong> delays.")


# Page 8: SQL Query Explorer 

def show_sql_page():
    inject_css()
    page_header("SQL Query Explorer")

    st.markdown("""
    Write and execute real SQL queries against the delay dataset.
    Powered by an **in-memory SQLite database** — no external database required.
    """)

    col1, col2 = st.columns([3, 2])

    with col1:
        default_query = (
            "SELECT line, SUM(delays) AS total_delays\n"
            "FROM subway_delays\n"
            "GROUP BY line\n"
            "ORDER BY total_delays DESC\n"
            "LIMIT 10;"
        )
        query = st.text_area("SQL Query:", value=default_query, height=180)

        if st.button("Run Query", type="primary"):
            conn = get_sqlite_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(query)
                cols    = [d[0] for d in cursor.description]
                results = cursor.fetchall()
                rows    = [dict(zip(cols, r)) for r in results]
                st.success(f"{len(rows):,} row(s) returned.")
                st.dataframe(rows, use_container_width=True)
            except Exception as e:
                st.error(f"SQL error: {e}")

    with col2:
        st.markdown("**Available table**")
        st.code("""subway_delays
─────────────────────────────
month              TEXT
division           TEXT
line               TEXT
day_type           TEXT   -- Weekday / Weekend
reporting_category TEXT
subcategory        TEXT
delays             INTEGER""", language="sql")

        with st.expander("Example queries"):
            st.code("""-- Monthly trend
SELECT month, SUM(delays) AS total
FROM subway_delays
GROUP BY month ORDER BY month;

-- Weekday vs Weekend
SELECT day_type, SUM(delays) AS total
FROM subway_delays GROUP BY day_type;

-- Top subcategories
SELECT subcategory, SUM(delays) AS total
FROM subway_delays
GROUP BY subcategory
ORDER BY total DESC LIMIT 10;

-- Division breakdown
SELECT division, COUNT(*) AS records,
       SUM(delays) AS total_delays
FROM subway_delays
GROUP BY division;""", language="sql")


# Main 

def main():
    st.set_page_config(
        page_title="NYC Subway Delay Analytics",
        page_icon="🚇",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Sidebar branding
    st.sidebar.markdown("""
    <div class="sidebar-brand">
        <div style="font-size:2rem">🚇</div>
        <div class="sidebar-title">NYC Subway Analytics</div>
        <div class="sidebar-sub">MTA Delay Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.sidebar.radio(
        "Navigate",
        [
            "Home",
            "Data Loading & Parsing",
            "Projection",
            "Filter Data",
            "Group By & Aggregation",
            "Join Operations",
            "Charts & Insights",
            "SQL Query",
        ],
        label_visibility="collapsed",
    )

    st.sidebar.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.sidebar.caption(f"Dataset: `{CSV_PATH}`\n\n{len(mta):,} records loaded")

    if   page == "Home":                  show_home_page(mta)
    elif page == "Data Loading & Parsing": show_loading_page()
    elif page == "Projection":            show_projection_page(mta)
    elif page == "Filter Data":           show_filter_page(mta)
    elif page == "Group By & Aggregation": show_groupby_page(mta)
    elif page == "Join Operations":       show_join_page(mta)
    elif page == "Charts & Insights":     show_charts_page(mta)
    elif page == "SQL Query":             show_sql_page()


if __name__ == "__main__":
    main()
