# FTTH QoE Risk Optimization - Executive Project Brief
### Capstone: Google Data Analytics + FCC MBA Data | Sept 2022

>Quick technical cheat-sheet and Business context for non-technical readers.

---

### 1. What is this project about? (For everyone)

Imagine you are a fiber ISP (FTTH). You have thousands of homes with a small white box (Whitebox) measuring internet quality every hour.

The problem: At night, 19:00-23:00, when everyone streams, games, and video-calls, some homes experience lag. If you don't detect them, they churn to a competitor.

**This project answers:** Which of my fiber homes are at risk of poor experience and how much money do I lose if I don't act?

**Key Result:** Out of 257 valid fiber homes, **17 are at risk (6.61%)**. Proactive fix saves ~$690/month in churn.

### 2. What does each register measure? (No jargon)

Each row in the raw data is NOT a customer, it's a **test packet**.

*   **Born at home:** Whitebox generates a small UDP packet (like a ping).
*   **Travels:** Whitebox -> Home Router -> ONT (fiber box) -> light over fiber -> Splitter -> OLT at central office -> ISP Core -> Internet Backbone -> MBA Test Server.
*   **Returns:** Server replies, Whitebox measures how long it took (latency), how much it varied (jitter), and if it was lost (loss).

**Under normal circumstances (healthy fiber):**
Latency < 15ms, Jitter < 3ms, Loss 0%. Everything smooth.

**When we mark `risk_flag = 1`:**
Not because of one bad packet. It's because during the WHOLE month, at peak time, 95% of its packets are slow. The 95th percentile (p95) > 20ms. That means that home, every night, sees frozen videos.

### 3. Datasets Used (Technical Cheat-Sheet)

| File | Role | 1 row = | Key Columns |
| :--- | :--- | :--- | :--- |
| `unit-profile-sept2022.csv` | DIM - Who | 1 Whitebox / home | `unit_id, Technology, Model, provisioned_down/up, timezone_offset` |
| `curr_udplatency.csv` | FACT - Latency | 1 UDP probe | `unit_id, timestamp_utc, rtt_avg (us), success/failures` |
| `curr_udpjitter.csv` | FACT - Jitter | 1 UDP burst | `unit_id, timestamp_utc, jitter_up/down` |
| `curr_udploss.csv` | FACT - Loss | 1 loss test | `unit_id, timestamp_utc, packets_sent/lost` |
| `fiber_units.csv` | Clean DIM (258) | 1 valid home | Filter: `Model IN (skwb8 227, ac1750v2 28, skwb8p 3)` |
| `ftth_final_258_v2_1.csv` | Aggregated FACT (257) | 1 home summarized at peak | `unit_id, p95_latency_ms, p95_jitter_ms, avg_loss_pct, risk_flag` |

**Golden Rule:** `raw microseconds / 1000 = ms`. `p95` must be calculated with `PERCENTILE.INC` in both Python and PowerBI, NOT with `AVERAGE`.

### 4. Full Process (6 Steps for Quick Review)

**Step 1 - Instrument Bias Fix (Your v2.1.3 differentiator):**
v1 showed 21% risk because it included legacy hardware: `wnr3500l-high (480MHz CPU caps at <95Mbps)` and `wdr3600 (no HW NAT)` creating false latency.
Fix: `INCLUDE Model IN (skwb8, skwb8p, ac1750v2) AND capacity >= provisioned*1.1`. Leaves 258.

**Step 2 - Time Normalization:**
`local_time = timestamp_utc + timezone_offset`. Filter `local_hour BETWEEN 19 AND 22`. This is prime time.

**Step 3 - Aggregation:**
Per `unit_id` at peak: `p95_latency = P95(rtt_avg/1000)`, `p95_jitter = P95(avg(up/down)/1000)`, `avg_loss = MEAN(loss)`.

**Step 4 - Risk Flag:**
`risk_flag = IF(p95_latency_ms > 20, 1, 0)`. Result: 17/257 = 6.61%.
Why 257 not 258? 1 unit had no tests during peak, so it drops. Expected.

**Step 5 - PowerBI :**
Import 2 tables. DO NOT filter hour again (already filtered). Relationship `fiber_units[Unit ID] -> ftth_final[unit_id]` One-to-Many Single. DAX Measures: `PERCENTILEX.INC`, `COUNTROWS=257`, `SUM(risk_flag)=17`.

**Step 6 - Act:**
Executive Dashboard: % Risk + $ ROI. NOC Dashboard: table by `unit_id` with 19-23h timeline for triage.

### 5. Quick Glossary (For non-technical stakeholder)
 (FULL Glossay in /docs)
*   **FTTH:** Fiber To The Home.
*   **Whitebox:** FCC measurement router, not the customer router.
*   **p95:** 95% of the time it's better than this value. If p95 is high, it's almost always bad at peak.
*   **Bufferbloat:** Packet queue in home router when upload saturates.
*   **OLT/ONT:** OLT is at ISP central, ONT is box at home. Light travels between them.
*   **Churn:** Customer leaving. Each retained customer worth ~$135.

### 6. Stakeholders & Business Questions

**Stakeholders:** NOC Manager (wants actionable list), CXO (wants $).

**3 Business Questions Answered:**
1. What % of our fiber base has poor QoE at peak?
2. Which are the specific units to intervene?
3. What is the financial impact of proactive intervention?

**3 Recommendations:**
1. Auto-alert if p95>20ms for 3 consecutive days.
2. Remote triage: check OLT and bufferbloat before dispatching tech.
3. Proactive SMS: "We detected nighttime slowness, want us to check?" Reduces churn by 30%.

