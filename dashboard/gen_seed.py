import os, random
import mysql.connector
from dotenv import load_dotenv

load_dotenv()
random.seed(42)
conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"), user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"), database=os.getenv("DB_NAME"))
cur = conn.cursor()

bids, asks = [], []          # resting orders: [price, ts, order_id, remaining]
mid, ts = 58000, 1000

for oid in range(1000, 4000):          # IDs 1000-3999, clear of your hand-made rows
    ts += 1
    mid += random.choice([-1, 0, 1])
    side = random.choice(["BUY", "SELL"])
    otype = "MARKET" if random.random() < 0.2 else "LIMIT"
    qty = random.randint(1, 10)
    if side == "BUY":
        price = mid + random.randint(-8, 3)
    else:
        price = mid + random.randint(-3, 8)

    cur.execute("INSERT INTO orders VALUES (%s,%s,1,%s,%s,%s,%s,'NEW',%s)",
                (oid, random.randint(1, 5), side, otype,
                 price if otype == "LIMIT" else None, qty, ts))

    book = asks if side == "BUY" else bids
    book.sort(key=lambda r: (r[0], r[1]) if side == "BUY" else (-r[0], r[1]))
    rem = qty
    while rem > 0 and book:
        best = book[0]
        crossed = (price >= best[0]) if side == "BUY" else (price <= best[0])
        if otype == "LIMIT" and not crossed:
            break
        traded = min(rem, best[3])
        cur.execute("INSERT INTO fills (resting_order_id, incoming_order_id, "
                    "price_ticks, quantity, ts) VALUES (%s,%s,%s,%s,%s)",
                    (best[2], oid, best[0], traded, ts))
        rem -= traded
        best[3] -= traded
        if best[3] == 0:
            book.pop(0)
    if rem > 0 and otype == "LIMIT":
        (bids if side == "BUY" else asks).append([price, ts, oid, rem])

    if oid % 500 == 0:
        conn.commit()
        print("loaded up to", oid)

conn.commit()
conn.close()
print("done")