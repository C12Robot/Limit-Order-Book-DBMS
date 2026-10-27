import os
import re
import warnings

import mysql.connector
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")

st.set_page_config(page_title="Limit Order Book", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    :root { --acc:#ff5a1f; --acc2:#ff8a3d; --line:rgba(255,255,255,0.12); }
    .stApp {
        background:
          radial-gradient(900px 500px at 12% -5%, rgba(255,90,31,.22), transparent 60%),
          radial-gradient(800px 600px at 95% 40%, rgba(255,138,61,.12), transparent 60%),
          radial-gradient(700px 500px at 30% 105%, rgba(255,90,31,.10), transparent 60%),
          #0a0a0c;
    }
    .block-container { padding: 2.4rem 3.2rem 3rem; max-width: 1750px; }
    .hdr h1 { font-size: 2rem; margin: 0; letter-spacing: -0.02em; color: #fff !important; }
    .hdr h1 [data-heading-text] { color: #fff !important; }
    .hdr h1 [data-heading-text] span { color: var(--acc) !important; }
    .hdr p { margin: 0.2rem 0 1.6rem; opacity: 0.6; }
    [data-testid="stDecoration"], [data-testid="stAppDeployButton"], [data-testid="stMainMenu"],
    [data-testid="stToolbarActions"], .stDeployButton { display: none !important; }
    [data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"] {
        display: flex !important; visibility: visible !important; opacity: 1 !important; z-index: 999;
    }
    [data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"] button {
        background: linear-gradient(135deg, #ff5a1f, #c2410c) !important; color: #fff !important;
        border-radius: 12px !important; box-shadow: 0 6px 16px rgba(255,90,31,.4);
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stHorizontalBlock"] { gap: 1.1rem; }

    /* glass surfaces */
    [data-testid="stMetric"], [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stExpander"], [data-testid="stForm"] {
        background: linear-gradient(145deg, rgba(255,255,255,0.09), rgba(255,255,255,0.03)) !important;
        backdrop-filter: blur(16px) saturate(140%); -webkit-backdrop-filter: blur(16px) saturate(140%);
        border: 1px solid var(--line) !important; border-radius: 18px;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.14), 0 8px 24px rgba(0,0,0,0.35);
        transition: transform .25s cubic-bezier(.2,.8,.2,1), box-shadow .25s, border-color .25s, background .25s;
    }
    [data-testid="stMetric"] { padding: 18px 22px; }
    /* hover: whatever card you are on turns orange and lifts */
    [data-testid="stMetric"]:hover {
        background: linear-gradient(135deg, #ff5a1f, #c2410c) !important;
        transform: translateY(-6px) scale(1.03); border-color: transparent !important;
        box-shadow: 0 16px 34px rgba(255,90,31,.35);
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover, [data-testid="stExpander"]:hover {
        transform: translateY(-3px); border-color: rgba(255,90,31,.7) !important;
        box-shadow: 0 14px 30px rgba(0,0,0,.5), 0 0 0 1px rgba(255,90,31,.35);
    }
    [data-testid="stMetricLabel"] p { font-size:.74rem; opacity:.8; text-transform:uppercase; letter-spacing:.08em; }
    [data-testid="stMetricValue"] { font-weight: 700; }
    [data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; border: 1px solid var(--line); }
    .stButton > button, [data-testid="stFormSubmitButton"] button { border-radius: 10px; transition: transform .15s, box-shadow .15s; }
    .stButton > button:hover, [data-testid="stFormSubmitButton"] button:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(255,90,31,.4); }
    h2, h3 { letter-spacing: -0.01em; }

    /* sidebar menu */
    [data-testid="stSidebar"] {
        background: rgba(12,12,15,0.72); backdrop-filter: blur(18px);
        border-right: 1px solid var(--line);
    }
    .brand { font-size: 1.9rem; font-weight: 800; line-height: 1.15; letter-spacing: -0.02em; margin: .6rem 0 1.6rem; }
    .brand span { color: var(--acc); }
    [data-testid="stSidebar"] [role="radiogroup"] { gap: 6px; }
    [data-testid="stSidebar"] [role="radiogroup"] label {
        padding: 10px 14px; border-radius: 12px; border: 1px solid transparent;
        transition: all .2s; width: 100%;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none; }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: rgba(255,90,31,.18); border-color: rgba(255,90,31,.5); transform: translateX(4px);
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(135deg, #ff5a1f, #c2410c); border-color: transparent;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p { color: #fff; font-weight: 600; }

    /* hoverable order-book ladders */
    .lrow { display: grid; grid-template-columns: 90px 60px 1fr 64px; gap: 12px; align-items: center;
        padding: 8px 12px; border-radius: 10px; font-variant-numeric: tabular-nums;
        transition: transform .15s, background .15s, box-shadow .15s; }
    .lrow.lhead { opacity: .55; font-size: .78rem; text-transform: uppercase; letter-spacing: .06em; }
    .lrow:not(.lhead):hover {
        background: linear-gradient(90deg, rgba(255,90,31,.55), rgba(255,90,31,.10));
        transform: translateX(6px) scale(1.015); box-shadow: 0 6px 16px rgba(255,90,31,.25);
    }
    .lrow .lp { font-weight: 700; }
    .lrow.bid .lp { color: #3fcf9f; } .lrow.ask .lp { color: #ff7d6c; }
    .lrow .ls { text-align: right; }
    .lbar { height: 8px; border-radius: 4px; background: rgba(255,255,255,.07); overflow: hidden; }
    .lbar i { display: block; height: 100%; border-radius: 4px; }
    .lrow.bid .lbar i { background: #3fcf9f; } .lrow.ask .lbar i { background: #ff7d6c; }
    </style>
    """,
    unsafe_allow_html=True,
)

STATUS_ORDER = ["NEW", "PARTIAL", "FILLED", "CANCELLED"]
COLORS = {
    "FILLED": "#3fcf9f", "PARTIAL": "#f0b84a", "NEW": "#ff8a3d", "CANCELLED": "#ff7d6c",
    "BUY": "#3fcf9f", "SELL": "#ff7d6c", "FIRED": "#3fcf9f", "DORMANT": "#f0b84a",
}


# ---------------- database helpers ----------------
def get_conn():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


def query(sql, params=None):
    conn = get_conn()
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()


def run(sql, params=None, proc=False):
    """Run a write. Returns (ok, message). Commits on success, rolls back on error."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        if proc:
            cur.callproc(sql, params or ())
        else:
            cur.execute(sql, params or ())
        conn.commit()
        return True, ""
    except mysql.connector.Error as e:
        conn.rollback()
        return False, getattr(e, "msg", str(e))
    finally:
        conn.close()


QUERIES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sql", "queries.sql")


def load_report_queries():
    """Parse sql/queries.sql into [(title, sql)]. One source of truth for the report."""
    with open(QUERIES_PATH, encoding="utf-8") as fh:
        text = fh.read()
    out = []
    for block in re.split(r"(?m)^-- (?=Q\d)", text)[1:]:
        lines = block.split("\n")
        title = lines[0].strip()
        body = "\n".join(ln for ln in lines[1:] if not ln.lstrip().startswith("--")).strip()
        out.append((title, body.rstrip(";")))
    return out



QEXPL = {
    "Q1": ("Volume-weighted average price per instrument.",
           "VWAP = SUM(price x qty) / SUM(qty). fills has no instrument column, so it joins fills to orders (via incoming_order_id) to instrument. tick_size converts ticks to a real price.",
           "Multi-table INNER JOIN, aggregation, GROUP BY (every non-aggregated column must be listed)."),
    "Q2": ("What share of each trader's orders were cancelled.",
           "SUM(status = 'CANCELLED') counts the matches, because a comparison is 1 or 0 in MySQL. Divided by COUNT(*) per trader.",
           "Conditional aggregation with GROUP BY. INNER JOIN drops traders with no orders."),
    "Q3": ("Price levels that traded at least 100 units.",
           "Groups fills by price, sums quantity, keeps only groups at or above 100, and shows the top 10.",
           "HAVING filters groups after aggregation; WHERE filters rows before it. idx_fills_price helps the grouping."),
    "Q4": ("Every stop order and the order it created, if any.",
           "LEFT JOIN keeps dormant stops, whose triggered_order_id is NULL, with NULLs on the order side. CASE labels DORMANT or FIRED.",
           "LEFT JOIN vs INNER JOIN, NULL handling, CASE expression, a nullable foreign key."),
    "Q5": ("Traders who placed more orders than the average trader.",
           "A subquery computes average orders per trader (COUNT(*) / COUNT(DISTINCT trader_id)) once, and HAVING compares each trader against it.",
           "Uncorrelated scalar subquery inside HAVING."),
    "Q6": ("Cumulative traded volume over time.",
           "SUM(quantity) OVER (ORDER BY ts, fill_id) adds a running total to every row. fill_id breaks ties so equal timestamps do not share a total.",
           "Window function: unlike GROUP BY it keeps every row. Needs MySQL 8.0+."),
    "Q7": ("Traders ranked by the volume they traded.",
           "The inner query sums each trader's filled quantity (as resting or incoming side). The outer query ranks the totals.",
           "Derived table in FROM, RANK() OVER. RANK gives ties the same rank and skips the next; DENSE_RANK does not skip."),
    "Q8": ("Orders that never traded, by side, type and status.",
           "For each order, NOT EXISTS checks whether any fill references it; only orders with no match remain, then they are counted.",
           "Anti-join with a correlated subquery. NOT EXISTS is safer than NOT IN, which returns nothing if the list contains NULL."),
}

TABLE_INFO = {
    "trader": "Who places orders. One row per market participant.",
    "instrument": "Tradable securities. tick_size converts integer ticks to a price; tick_value is the money value of one tick.",
    "orders": "Every order placed: side, type (LIMIT/MARKET), price in ticks (NULL for market), quantity, status and logical timestamp ts.",
    "fills": "One row per match. resting_order_id was already on the book, incoming_order_id is the aggressor. Both are foreign keys to orders.",
    "order_events": "Append-only audit log of status changes, written by triggers, never by the app.",
    "stop_orders": "Dormant orders waiting for a trigger price. They become real rows in orders only when they fire.",
}

# ---------------- display helpers ----------------
def num(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def colored(df, cols):
    """Colour status/side/state text. Works across pandas versions."""
    cols = [c for c in cols if c in df.columns]
    if not cols:
        return df

    def paint(v):
        c = COLORS.get(v)
        return f"color: {c}; font-weight: 600" if c else ""

    sty = df.style
    return (sty.map if hasattr(sty, "map") else sty.applymap)(paint, subset=cols)


def show(df, **kw):
    """st.dataframe at full width on both old and new Streamlit versions."""
    try:
        st.dataframe(df, width="stretch", hide_index=True, **kw)
    except Exception:
        st.dataframe(df, use_container_width=True, hide_index=True, **kw)


def bars(df, colors=None):
    if colors:
        try:
            st.bar_chart(df, color=colors)
            return
        except Exception:
            pass
    st.bar_chart(df, color="#ff5a1f")


def flash_and_rerun(message):
    st.session_state["flash"] = message
    st.rerun()


# ---------------- header ----------------
st.markdown(
    '<div class="hdr"><h1>Limit <span>Order</span> Book</h1>'
    "<p>MySQL data layer for the C++ matching engine. Price-time priority, prices in ticks.</p></div>",
    unsafe_allow_html=True,
)

try:
    get_conn().close()
except Exception as e:
    st.error(
        f"Cannot connect to MySQL: {getattr(e, 'msg', str(e))}. "
        "Check that the MySQL80 service is running and that .env is correct."
    )
    st.stop()

if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

# ---------------- KPI row ----------------
k_orders = num(query(
    "SELECT COUNT(*) AS total, "
    "SUM(status IN ('NEW','PARTIAL')) AS open_orders, "
    "SUM(status = 'CANCELLED') AS cancelled FROM orders"
), ["total", "open_orders", "cancelled"]).iloc[0]
k_fills = num(query(
    "SELECT COUNT(*) AS n, COALESCE(SUM(quantity), 0) AS vol, "
    "ROUND(SUM(price_ticks * quantity) / NULLIF(SUM(quantity), 0), 1) AS vwap FROM fills"
), ["n", "vol", "vwap"]).iloc[0]

total = int(k_orders["total"] or 0)
cancelled = int(k_orders["cancelled"] or 0)
m = st.columns(6)
m[0].metric("Orders", f"{total:,}")
m[1].metric("Open orders", f"{int(k_orders['open_orders'] or 0):,}")
m[2].metric("Fills", f"{int(k_fills['n']):,}")
m[3].metric("Volume traded", f"{int(k_fills['vol']):,}")
m[4].metric("VWAP (ticks)", "n/a" if pd.isna(k_fills["vwap"]) else f"{float(k_fills['vwap']):,.1f}")
m[5].metric("Cancel rate", f"{(100 * cancelled / total) if total else 0:.1f}%")

PAGES = ["Order Book", "Orders", "Fills", "Analytics", "Reports", "Schema", "Manage"]
with st.sidebar:
    st.markdown('<div class="brand">Limit <span>Order</span> Book</div>', unsafe_allow_html=True)
    page = st.radio("Navigate", PAGES, label_visibility="collapsed")
    st.caption("MySQL lob_db")

# ---------------- Order Book ----------------
if page == "Order Book":
    syms = query("SELECT symbol FROM instrument ORDER BY instrument_id")["symbol"].tolist()
    sym = st.selectbox("Instrument", syms, key="book_sym")

    open_o = num(query(
        "SELECT o.order_id, o.side, o.price_ticks AS price, o.quantity AS qty "
        "FROM orders o JOIN instrument i ON i.instrument_id = o.instrument_id "
        "WHERE i.symbol = %s AND o.status IN ('NEW', 'PARTIAL') AND o.order_type = 'LIMIT'",
        params=(sym,),
    ), ["price", "qty"])
    fl = num(query(
        "SELECT resting_order_id AS r, incoming_order_id AS i, quantity AS q FROM fills"
    ), ["q"])
    filled = pd.concat([fl.groupby("r")["q"].sum(), fl.groupby("i")["q"].sum()]).groupby(level=0).sum()
    open_o["size"] = (open_o["qty"] - open_o["order_id"].map(filled).fillna(0)).clip(lower=0)
    open_o = open_o[open_o["size"] > 0]

    def ladder(side, ascending):
        d = open_o[open_o["side"] == side].groupby("price").agg(
            orders=("order_id", "count"), size=("size", "sum")).reset_index()
        return d.sort_values("price", ascending=ascending)

    bids, asks = ladder("BUY", False), ladder("SELL", True)
    best_bid = bids["price"].max() if len(bids) else None
    best_ask = asks["price"].min() if len(asks) else None

    t = st.columns(6)
    t[0].metric("Best bid", "n/a" if best_bid is None else f"{int(best_bid):,}")
    t[1].metric("Best ask", "n/a" if best_ask is None else f"{int(best_ask):,}")
    if best_bid is not None and best_ask is not None:
        t[2].metric("Spread (ticks)", f"{int(best_ask - best_bid):,}")
        t[3].metric("Mid price", f"{(best_bid + best_ask) / 2:,.1f}")
    else:
        t[2].metric("Spread (ticks)", "n/a")
        t[3].metric("Mid price", "n/a")
    t[4].metric("Bid depth", f"{int(bids['size'].sum()):,}")
    t[5].metric("Ask depth", f"{int(asks['size'].sum()):,}")

    def ladder_html(df, cls):
        mx = max([1] + df["size"].tolist())
        rows = "".join(
            f'<div class="lrow {cls}"><span class="lp">{int(r.price)}</span><span>{int(r.orders)}</span>'
            f'<span class="lbar"><i style="width:{100 * r.size / mx:.0f}%"></i></span>'
            f'<span class="ls">{int(r.size)}</span></div>' for r in df.itertuples())
        head = '<div class="lrow lhead"><span>Price</span><span>Orders</span><span></span><span>Size</span></div>'
        return f'<div>{head}{rows}</div>'

    top = max([1] + bids["size"].head(15).tolist() + asks["size"].head(15).tolist())
    size_cfg = st.column_config.ProgressColumn("Size", format="%d", min_value=0, max_value=int(top))
    price_cfg = st.column_config.NumberColumn("Price", format="%d")

    b1, b2, b3 = st.columns(3)
    with b1.container(border=True):
        st.subheader("Bids")
        st.markdown(ladder_html(bids.head(14), "bid"), unsafe_allow_html=True)
    with b2.container(border=True):
        st.subheader("Asks")
        st.markdown(ladder_html(asks.head(14), "ask"), unsafe_allow_html=True)
    with b3.container(border=True):
        st.subheader("Recent trades")
        tape = num(query(
            "SELECT f.fill_id, f.price_ticks AS price, f.quantity AS qty, o.side AS aggressor, f.ts "
            "FROM fills f JOIN orders o ON o.order_id = f.incoming_order_id "
            "JOIN instrument i ON i.instrument_id = o.instrument_id "
            "WHERE i.symbol = %s ORDER BY f.fill_id DESC LIMIT 15",
            params=(sym,),
        ), ["price", "qty", "ts"])
        show(colored(tape, ["aggressor"]), height=420)

    with st.container(border=True):
        st.subheader("Market depth")
        st.caption("Cumulative resting size at or better than each price.")
        bd = bids.sort_values("price", ascending=False).assign(cum=lambda d: d["size"].cumsum())
        ad = asks.sort_values("price", ascending=True).assign(cum=lambda d: d["size"].cumsum())
        depth = pd.concat([
            bd.set_index("price")[["cum"]].rename(columns={"cum": "Bids"}),
            ad.set_index("price")[["cum"]].rename(columns={"cum": "Asks"}),
        ]).sort_index()
        if len(depth):
            st.area_chart(depth, color=["#3fcf9f", "#ff7d6c"])
        else:
            st.info("No open limit orders for this instrument.")

# ---------------- Orders ----------------
if page == "Orders":
    orders = num(query(
        "SELECT o.order_id, t.name AS trader, i.symbol, o.side, o.order_type AS type, "
        "o.price_ticks AS price, o.quantity AS qty, o.status, o.ts "
        "FROM orders o JOIN trader t ON t.trader_id = o.trader_id "
        "JOIN instrument i ON i.instrument_id = o.instrument_id "
        "ORDER BY o.ts DESC, o.order_id DESC"
    ), ["price", "qty", "ts"])

    f1, f2, f3, f4 = st.columns([2, 2, 2, 2])
    status_sel = f1.multiselect("Status", STATUS_ORDER)
    side_sel = f2.multiselect("Side", ["BUY", "SELL"])
    trader_sel = f3.multiselect("Trader", sorted(orders["trader"].unique()))
    id_text = f4.text_input("Order ID", placeholder="e.g. 4663")

    view = orders
    if status_sel:
        view = view[view["status"].isin(status_sel)]
    if side_sel:
        view = view[view["side"].isin(side_sel)]
    if trader_sel:
        view = view[view["trader"].isin(trader_sel)]
    if id_text.strip().isdigit():
        view = view[view["order_id"] == int(id_text.strip())]

    st.caption(f"Showing {len(view):,} of {len(orders):,} orders, newest first")
    show(
        colored(view, ["status", "side"]), height=440,
        column_config={
            "order_id": st.column_config.NumberColumn("Order", format="%d"),
            "price": st.column_config.NumberColumn("Price (ticks)", format="%d"),
            "qty": st.column_config.NumberColumn("Qty", format="%d"),
            "ts": st.column_config.NumberColumn("ts", format="%d"),
        },
    )

# ---------------- Fills ----------------
if page == "Fills":
    fills = num(query(
        "SELECT fill_id, resting_order_id AS resting, incoming_order_id AS incoming, "
        "price_ticks AS price, quantity AS qty, ts FROM fills ORDER BY fill_id DESC"
    ), ["price", "qty", "ts"])

    p1, p2 = st.columns([1, 3])
    price_filter = p1.number_input("Price filter (ticks, 0 = all)", min_value=0, value=0, step=1)
    fview = fills[fills["price"] == price_filter] if price_filter else fills
    p2.caption("")
    st.caption(f"Showing {len(fview):,} of {len(fills):,} fills. Price is the resting order's price.")
    show(
        fview, height=380,
        column_config={
            "fill_id": st.column_config.NumberColumn("Fill", format="%d"),
            "price": st.column_config.NumberColumn("Price (ticks)", format="%d"),
            "qty": st.column_config.NumberColumn("Qty", format="%d"),
            "ts": st.column_config.NumberColumn("ts", format="%d"),
        },
    )

    with st.expander("Index demo: idx_fills_price"):
        st.caption("The same lookup, planned with the index and with the index ignored.")
        px = int(st.number_input("Price (ticks)", min_value=1, value=58005, step=1, key="idx_px"))
        base = f"SELECT SUM(quantity) FROM fills{{hint}} WHERE price_ticks = {px}"
        ca, cb = st.columns(2)
        for col, label, hint in (
            (ca, "With index", ""),
            (cb, "Index ignored (full scan)", " IGNORE INDEX (idx_fills_price)"),
        ):
            with col:
                st.markdown(f"**{label}**")
                sql_text = base.format(hint=hint)
                st.code("EXPLAIN " + sql_text + ";", language="sql")
                try:
                    plan = query("EXPLAIN " + sql_text)
                    keep = [c for c in ("type", "key", "rows", "filtered") if c in plan.columns]
                    show(plan[keep] if keep else plan)
                except Exception as e:
                    st.error(str(e))

# ---------------- Analytics ----------------
if page == "Analytics":
    a1, a2 = st.columns(2)
    with a1.container(border=True):
        st.subheader("Orders by status")
        by_status = num(query("SELECT status, COUNT(*) AS n FROM orders GROUP BY status"), ["n"])
        by_status = by_status.set_index("status").reindex(STATUS_ORDER).fillna(0)
        bars(by_status)
    with a2.container(border=True):
        st.subheader("Fill volume per price")
        by_price = num(query(
            "SELECT price_ticks, SUM(quantity) AS volume FROM fills "
            "GROUP BY price_ticks ORDER BY price_ticks"
        ), ["volume"])
        bars(by_price.set_index("price_ticks"))

    a3, a4 = st.columns(2)
    with a3.container(border=True):
        st.subheader("Orders per trader, by status")
        per_trader = num(query(
            "SELECT t.name AS trader, o.status, COUNT(*) AS n "
            "FROM orders o JOIN trader t ON t.trader_id = o.trader_id "
            "GROUP BY t.name, o.status"
        ), ["n"])
        pivot = per_trader.pivot_table(index="trader", columns="status", values="n", fill_value=0)
        pivot = pivot[[c for c in STATUS_ORDER if c in pivot.columns]]
        bars(pivot, colors=[COLORS[c] for c in pivot.columns])
    with a4.container(border=True):
        st.subheader("Cumulative volume over time")
        cum = num(query("SELECT ts, SUM(quantity) AS vol FROM fills GROUP BY ts ORDER BY ts"), ["ts", "vol"])
        cum["cumulative volume"] = cum["vol"].cumsum()
        st.line_chart(cum.set_index("ts")[["cumulative volume"]], color="#ff5a1f")

# ---------------- Reports ----------------
if page == "Reports":
    r1, r2 = st.columns([3, 1])
    r1.caption("Each panel runs a query from sql/queries.sql, shown above its result.")
    expand_all = r2.toggle("Expand all", value=False)
    for title, body in load_report_queries():
        with st.expander(title, expanded=expand_all):
            ex = QEXPL.get(title.split(".")[0].strip())
            if ex:
                st.markdown(f"**What it answers:** {ex[0]}  \n**How it works:** {ex[1]}  \n**DBMS concept:** {ex[2]}")
            st.code(body + ";", language="sql")
            try:
                result = query(body)
                st.caption(f"{len(result)} row(s)")
                show(result)
            except Exception as e:
                st.error(str(e))

# ---------------- Manage ----------------
if page == "Manage":
    traders = query("SELECT trader_id, name FROM trader ORDER BY trader_id")
    trader_names = dict(zip(traders["trader_id"].astype(int), traders["name"]))
    instruments = query("SELECT instrument_id, symbol FROM instrument ORDER BY instrument_id")
    instrument_names = dict(zip(instruments["instrument_id"].astype(int), instruments["symbol"]))

    next_id = int(query(
        "SELECT COALESCE(MAX(order_id), 0) + 1 AS n FROM orders WHERE order_id < 900000"
    )["n"].iloc[0])
    next_ts = int(query(
        "SELECT COALESCE(MAX(ts), 0) + 1 AS n FROM orders WHERE order_id < 900000"
    )["n"].iloc[0])

    left, right = st.columns([3, 2])

    with left:
        st.subheader("Place order")
        with st.form("place_order"):
            c1, c2, c3 = st.columns(3)
            order_id = c1.number_input("Order ID", min_value=1, value=next_id, step=1)
            trader_id = c2.selectbox("Trader", list(trader_names), format_func=lambda i: trader_names[i])
            instrument_id = c3.selectbox("Instrument", list(instrument_names), format_func=lambda i: instrument_names[i])
            c4, c5, c6, c7 = st.columns(4)
            side = c4.selectbox("Side", ["BUY", "SELL"])
            order_type = c5.selectbox("Type", ["LIMIT", "MARKET"])
            price = c6.number_input("Price (ticks)", min_value=0, value=58000, step=1)
            qty = c7.number_input("Quantity", min_value=1, value=1, step=1)
            submitted = st.form_submit_button("Place order", type="primary")
        st.caption("Price is ignored for MARKET orders. Inserting an order makes the trigger write a NEW event.")

        if submitted:
            price_val = None if order_type == "MARKET" else int(price)
            ok, msg = run(
                "INSERT INTO orders (order_id, trader_id, instrument_id, side, order_type, "
                "price_ticks, quantity, ts) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (int(order_id), int(trader_id), int(instrument_id), side,
                 order_type, price_val, int(qty), next_ts),
            )
            if ok:
                flash_and_rerun(f"Order {int(order_id)} placed")
            else:
                st.error(msg)

        st.subheader("Cancel order")
        with st.form("cancel_order"):
            cancel_id = st.number_input("Order ID to cancel", min_value=1, value=1, step=1)
            cancel_clicked = st.form_submit_button("Cancel order")
        st.caption("Calls the stored procedure cancel_order(). Filled or already cancelled orders are refused.")

        if cancel_clicked:
            ok, msg = run("cancel_order", (int(cancel_id),), proc=True)
            if ok:
                flash_and_rerun(f"Order {int(cancel_id)} cancelled")
            else:
                st.error(msg)

    with right:
        st.subheader("Latest order events")
        st.caption("Written by triggers, never by the app.")
        events = query(
            "SELECT event_id, order_id, event_type AS event, event_time AS time "
            "FROM order_events ORDER BY event_id DESC LIMIT 12"
        )
        show(colored(events.rename(columns={"event": "status"}), ["status"]), height=440)

    st.divider()
    st.subheader("Stop orders")
    stops = query(
        "SELECT s.stop_id, t.name AS trader, s.side, s.trigger_price_ticks AS trigger_ticks, "
        "s.limit_price_ticks AS limit_ticks, s.quantity AS qty, "
        "s.triggered_order_id AS fired_as, s.fired "
        "FROM stop_orders_status s JOIN trader t ON t.trader_id = s.trader_id "
        "ORDER BY s.stop_id DESC"
    )
    stops["state"] = stops["fired"].map(lambda v: "FIRED" if int(v) else "DORMANT")
    stops = stops.drop(columns=["fired"])
    st.caption("Read from the stop_orders_status view. A stop becomes a real order only when it fires.")
    show(colored(stops, ["side", "state"]))

    next_stop = int(query(
        "SELECT COALESCE(MAX(stop_id), 899999) + 1 AS n FROM stop_orders"
    )["n"].iloc[0])

    with st.form("add_stop"):
        s1, s2, s3 = st.columns(3)
        stop_id = s1.number_input("Stop ID", min_value=900000, value=next_stop, step=1)
        stop_trader = s2.selectbox("Trader", list(trader_names), format_func=lambda i: trader_names[i], key="st_tr")
        stop_instr = s3.selectbox("Instrument", list(instrument_names), format_func=lambda i: instrument_names[i], key="st_in")
        s4, s5, s6, s7 = st.columns(4)
        stop_side = s4.selectbox("Side", ["BUY", "SELL"], key="st_side")
        trigger = s5.number_input("Trigger (ticks)", min_value=1, value=58020, step=1)
        limit_p = s6.number_input("Limit (ticks)", min_value=1, value=58030, step=1)
        stop_qty = s7.number_input("Quantity", min_value=1, value=1, step=1, key="st_q")
        add_stop = st.form_submit_button("Add stop order", type="primary")

    if add_stop:
        ok, msg = run(
            "INSERT INTO stop_orders (stop_id, trader_id, instrument_id, side, "
            "limit_price_ticks, trigger_price_ticks, quantity) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (int(stop_id), int(stop_trader), int(stop_instr), stop_side,
             int(limit_p), int(trigger), int(stop_qty)),
        )
        if ok:
            flash_and_rerun(f"Stop order {int(stop_id)} added (dormant)")
        else:
            st.error(msg)


# ---------------- Schema ----------------
if page == "Schema":
    st.caption("Read live from information_schema, so this always matches the real database.")
    try:
        cols = query(
            "SELECT c.TABLE_NAME AS tbl, c.COLUMN_NAME AS col, c.COLUMN_TYPE AS type, "
            "c.IS_NULLABLE AS nullable, c.COLUMN_KEY AS keytype, "
            "k.REFERENCED_TABLE_NAME AS ref_table, k.REFERENCED_COLUMN_NAME AS ref_col "
            "FROM information_schema.COLUMNS c "
            "LEFT JOIN information_schema.KEY_COLUMN_USAGE k ON k.TABLE_SCHEMA = c.TABLE_SCHEMA "
            "AND k.TABLE_NAME = c.TABLE_NAME AND k.COLUMN_NAME = c.COLUMN_NAME "
            "AND k.REFERENCED_TABLE_NAME IS NOT NULL "
            "WHERE c.TABLE_SCHEMA = DATABASE() AND c.TABLE_NAME IN "
            "(SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE') "
            "ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION"
        )
        def role(r):
            parts = []
            if r["keytype"] == "PRI":
                parts.append("PRIMARY KEY")
            if r["ref_table"]:
                parts.append(f"FOREIGN KEY -> {r['ref_table']}.{r['ref_col']}")
            return ", ".join(parts)
        cols["key"] = cols.apply(role, axis=1)
        cols["nullable"] = cols["nullable"].map({"YES": "NULL allowed", "NO": "NOT NULL"})
        names = list(dict.fromkeys(cols["tbl"]))
        for i in range(0, len(names), 2):
            row = st.columns(2)
            for col_box, name in zip(row, names[i:i + 2]):
                with col_box.container(border=True):
                    st.subheader(name)
                    st.caption(TABLE_INFO.get(name, ""))
                    show(cols[cols["tbl"] == name][["col", "type", "nullable", "key"]].rename(columns={"col": "column"}))
    except Exception as e:
        st.error(str(e))

    st.divider()
    o1, o2 = st.columns(2)
    with o1.container(border=True):
        st.subheader("Triggers")
        st.caption("Run automatically on INSERT/UPDATE, so the audit trail cannot be bypassed.")
        try:
            show(query("SELECT TRIGGER_NAME AS trigger_name, ACTION_TIMING AS timing, EVENT_MANIPULATION AS event, "
                       "EVENT_OBJECT_TABLE AS on_table FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA = DATABASE()"))
        except Exception as e:
            st.error(str(e))
    with o2.container(border=True):
        st.subheader("Procedures, views and indexes")
        try:
            show(query("SELECT ROUTINE_NAME AS name, ROUTINE_TYPE AS kind FROM information_schema.ROUTINES "
                       "WHERE ROUTINE_SCHEMA = DATABASE()"))
            show(query("SELECT TABLE_NAME AS view_name FROM information_schema.VIEWS WHERE TABLE_SCHEMA = DATABASE()"))
            show(query("SELECT TABLE_NAME AS on_table, INDEX_NAME AS index_name, "
                       "GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS columns_indexed, "
                       "IF(MIN(NON_UNIQUE) = 0, 'UNIQUE', 'non-unique') AS uniqueness "
                       "FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = DATABASE() "
                       "GROUP BY TABLE_NAME, INDEX_NAME ORDER BY TABLE_NAME, INDEX_NAME"))
        except Exception as e:
            st.error(str(e))
