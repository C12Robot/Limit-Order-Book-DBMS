-- ============================================================
-- queries.sql : 8 report queries for lob_db
-- Run: USE lob_db;  then execute each query separately.
-- Prices are stored as integer ticks; price = price_ticks * tick_size.
-- ============================================================

-- Q1. VWAP per instrument  [JOIN + aggregate]
-- fills has no instrument_id, so join through the incoming order.
SELECT i.symbol,
       SUM(f.quantity)                                        AS total_qty,
       ROUND(SUM(f.price_ticks * f.quantity) / SUM(f.quantity), 2) AS vwap_ticks,
       ROUND(SUM(f.price_ticks * f.quantity) / SUM(f.quantity) * i.tick_size, 2) AS vwap_price
FROM fills f
JOIN orders o     ON o.order_id = f.incoming_order_id
JOIN instrument i ON i.instrument_id = o.instrument_id
GROUP BY i.instrument_id, i.symbol, i.tick_size;

-- Q2. Cancel ratio per trader  [GROUP BY + conditional aggregate]
SELECT t.name,
       COUNT(o.order_id)                                   AS orders,
       SUM(o.status = 'CANCELLED')                         AS cancelled,
       ROUND(100 * SUM(o.status = 'CANCELLED') / COUNT(o.order_id), 1) AS cancel_pct
FROM trader t
JOIN orders o ON o.trader_id = t.trader_id
GROUP BY t.trader_id, t.name
ORDER BY cancel_pct DESC;

-- Q3. Busy price levels: volume per price  [GROUP BY + HAVING]
SELECT price_ticks,
       COUNT(*)      AS fills,
       SUM(quantity) AS volume
FROM fills
GROUP BY price_ticks
HAVING SUM(quantity) >= 100
ORDER BY volume DESC
LIMIT 10;

-- Q4. Stop-order chain: stop -> triggered order -> trader  [multi-table LEFT JOIN]
-- LEFT JOIN keeps dormant stops (triggered_order_id IS NULL).
SELECT s.stop_id,
       t.name           AS trader,
       s.side,
       s.trigger_price_ticks,
       s.limit_price_ticks,
       o.order_id       AS triggered_order,
       o.status         AS order_status,
       CASE WHEN s.triggered_order_id IS NULL THEN 'DORMANT' ELSE 'FIRED' END AS stop_state
FROM stop_orders s
JOIN trader t       ON t.trader_id = s.trader_id
LEFT JOIN orders o  ON o.order_id = s.triggered_order_id
ORDER BY s.stop_id;

-- Q5. Traders with above-average order count  [subquery in HAVING]
SELECT t.name, COUNT(*) AS orders
FROM trader t
JOIN orders o ON o.trader_id = t.trader_id
GROUP BY t.trader_id, t.name
HAVING COUNT(*) > (SELECT COUNT(*) / COUNT(DISTINCT trader_id) FROM orders)
ORDER BY orders DESC;

-- Q6. Running traded volume over time  [window function: SUM OVER]
SELECT ts, fill_id, price_ticks, quantity,
       SUM(quantity) OVER (ORDER BY ts, fill_id) AS running_volume
FROM fills
ORDER BY ts, fill_id
LIMIT 20;

-- Q7. Trader ranking by filled volume  [window function: RANK OVER]
-- Counts each fill once per side (resting or incoming) for that trader's orders.
SELECT name, filled_qty,
       RANK() OVER (ORDER BY filled_qty DESC) AS volume_rank
FROM (
    SELECT t.name, SUM(f.quantity) AS filled_qty
    FROM trader t
    JOIN orders o ON o.trader_id = t.trader_id
    JOIN fills  f ON f.resting_order_id = o.order_id
                  OR f.incoming_order_id = o.order_id
    GROUP BY t.trader_id, t.name
) x
ORDER BY volume_rank;

-- Q8. Orders that never traded  [anti-join: NOT EXISTS]
SELECT o.side, o.order_type, o.status, COUNT(*) AS orders
FROM orders o
WHERE NOT EXISTS (
    SELECT 1 FROM fills f
    WHERE f.resting_order_id = o.order_id
       OR f.incoming_order_id = o.order_id
)
GROUP BY o.side, o.order_type, o.status
ORDER BY orders DESC;