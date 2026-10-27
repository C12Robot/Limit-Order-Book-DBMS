# Design Decisions Log

Format: **Decision** — what was chosen. **Why** — the reasoning. **Rejected** — the alternative and why it lost.

---

### Price-level container: `std::map<int64_t, PriceLevel>`

**Why:** Need sorted-by-price iteration for best-bid/best-ask lookup (`begin()`/`rbegin()`), and O(log n) insert/erase for adding/removing price levels. `lower_bound()`/`upper_bound()` give direct access to book edges without linear scan. **Rejected:** Sorted `std::vector<PriceLevel>` — better cache locality for iteration, but O(n) insert to maintain sort order on every new price level. `std::map` chosen as the safer default until profiling says otherwise.

### Price representation: `int64_t` ticks, not `double`

**Why:** Floating-point price keys risk equality/comparison bugs when matching or indexing price levels (rounding errors on values that should be identical). Integer tick counts are exact. **Rejected:** `double` price — simpler to read, but unsafe as a map key or for equality checks in a matching engine.

### Order fields: matching-engine data only — no TP/SL, no PnL

**Why:** `Order` should hold only what the matching engine needs to do its one job: match resting orders against incoming ones at the best price. TP/SL is strategy/order-management logic (a layer above the book); PnL is portfolio/backtest accounting (a layer above that). Coupling them into `Order` would force every layer to depend on every other layer's concerns. **Rejected:** A fatter `Order` carrying TP/SL and end-price/PnL fields — flagged as scope creep that would need undoing once a second instrument, bracket style, or backtest-without-brackets scenario showed up.

### PriceLevel's order container: `std::deque<Order>`, not `std::vector<Order>`

**Why:** Price-time priority means oldest order at a level fills first — removal happens constantly at the front. `deque` does front removal/insertion in O(1); `vector` requires O(n) shifting of every remaining element on a front-erase. Cancels can also happen mid-level, which both containers handle similarly (O(n) either way for a middle erase), so the front-removal case is what decides it. **Rejected:** `std::vector<Order>` — better cache locality for straight iteration, but the O(n) front-removal cost is a real bottleneck for this specific access pattern, unlike the general vector-preferred guidance for most other containers in this project.

### PriceLevel does NOT store price or timestamp

**Why:** Price is already the key in the enclosing `std::map<int64_t, PriceLevel>` — storing it again on the struct duplicates data the container already tracks. Timestamp is an `Order`-level concept (each order has its own arrival time for price-time priority) — a price level holds many orders, not one timestamp. **Rejected:** Storing both directly on `PriceLevel` — redundant with the map key (price) and conceptually wrong scope (timestamp).

---

### Fill History Container:

`std::vector<Fill>`, not `std::deque<Order>`.** Reasoning: `fills` is an append-only log — every match pushes a new entry to the back, and it's never removed from or inserted into the front, unlike `PriceLevel::orders` where price-time priority requires O(1) front-removal. Since the access pattern here is pure back-append plus (eventually) full-history iteration, `vector`'s contiguous memory and better cache locality win outright — there's no front-removal cost to avoid, so `deque`'s only advantage over `vector` doesn't apply. Rejected: `std::deque<Fill>` — would work correctness-wise, but offers no benefit here and gives up `vector`'s cache-friendly iteration for nothing in return.

----

### Fill construction: 

local `Fill fill;` declared inside each of the four match branches, not one shared instance at function scope.** Reasoning: a single shared `Fill` reused across all match spots risks a field from a previous match silently surviving into the next one if any branch forgets to overwrite every field before `push_back` — the bug would compile cleanly and produce plausible-looking but wrong trade history, hard to catch by inspection. Scoping `Fill fill;` locally to each branch guarantees every field is freshly set for every recorded trade, at negligible extra typing cost. Rejected: one `Fill fill;` at the top of `Add`, reused across branches — marginally less code, but trades a real correctness guarantee for it.

---

### Order lookup index container: 

`std::unordered_map<uint64_t, OrderIndex>`, not `std::map`.** Reasoning: `orderIndex` exists solely to answer "given this order ID, where does it live in the book?" — a pure point-lookup by ID, with no need for sorted iteration or range queries over IDs. `std::unordered_map`'s O(1) average-case hash lookup directly serves the original goal (avoid an O(n) full-book scan on every `Cancel`); `std::map`'s O(log n) tree lookup would still work correctly but pays traversal cost for an ordering guarantee this structure never uses. Rejected: `std::map<uint64_t, OrderIndex>` — functionally fine, but strictly worse for this access pattern with no compensating benefit.

---

### Stop/trailing-stop orders live in a separate layer above `OrderBook`, not inside it.

Why: `OrderBook::Add` should only ever handle orders that are immediately live and matchable — mixing in dormant, price-triggered orders would mean checking every incoming trade against a watch-list inside the matching engine's core loop, coupling two genuinely separate concerns (matching vs. conditional order triggering). A separate watcher class checking trigger conditions against fills/prices and calling `Add()` only once triggered keeps `OrderBook` narrowly scoped and matches how this is typically done in practice.

---
### Type consistency across `priceTicks` fields.** 

Every field named `priceTicks` — on `Order`, on `OrderIndex`, and as the key type in the `bids`/`asks` maps — must be declared as the exact same type (`uint64_t`), not merely "an integer type." A mismatch here doesn't fail to compile in most cases; it silently produces wrong comparisons (e.g., assigning `uint64_t::max()` into a variable actually typed `int64_t` wraps around to `-1`), which broke market-order price overrides without any compiler error pointing at the real cause. This surfaced twice in this project (`Order` vs. `OrderIndex` mismatch, twice) — worth treating "check every type in the chain" as a standing habit whenever one struct's field feeds into another's, not just when the compiler flags it.

---

### Stop-order watcher's fill-detection mechanism:

size-checkpoint on `GetFills()`, not `orderIndex`.** `orderIndex` was considered and rejected — it only tracks currently-resting orders and has entries erased the moment an order matches or cancels, so it can't represent "a trade happened at price X," which is the actual signal a stop trigger needs. The watcher instead keeps its own `size_t lastCheckedFillCount` state; after each `OrderBook::Add()` call, it compares `book.GetFills().size()` against that stored count, iterates only the new entries beyond it, checks each `.price` against pending stop triggers, and updates the stored count. This needs zero changes to `OrderBook` itself — the entire mechanism lives on the watcher side, reusing the existing fill log as source of truth.

---

