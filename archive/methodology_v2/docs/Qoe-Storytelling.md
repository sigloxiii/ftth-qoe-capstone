# QoE Risk Analysis - ISP Benchmarking (258 Units)

## Finding
The gap in `% At Risk` between ISPs is explained by packet loss, not latency or jitter.

- **Latency:** Homogeneous 5-22ms p95 across all ISPs. Not a differentiator.
- **Jitter:** Max 3.1ms observed. No unit exceeds 5ms threshold. 0% of risk is from jitter.
- **Packet Loss:** 100% of risk is driven by `avg_loss_pct >1%`.

**ISP with highest risk is Frontier with 77.42% At Risk (48 of 62 units), average loss 7.18%.**
Second is Verizon with 36.84% At Risk (28 of 76 units), average loss 6.21%.
Healthiest is Cincinnati Bell with 10.83% At Risk (13 of 120 units), average loss 1.19%.

Overall: Total Units 258 | At Risk 34.50% (89 units) | Severe 10.08% | OPEX Saved $6,660.

---

## Visuals

### Executive Page
- **Map `Avg Loss % per State`:** Texas and Southeast show highest concentration of loss.
- **Bar `At Risk % by ISP`:** Frontier 77.42% (red), Verizon 36.84% (yellow), Cincinnati Bell 10.83% (blue). Directly matches average loss ranking.

### QoE Risk - Linear vs Logarithmic

**Setup:**
- X: `p95_latency_ms` (Don't summarize)
- Y: `avg_loss_pct_for_log` (Don't summarize)
- Legend: `risk_flag`
- DAX: `avg_loss_pct_for_log = IF([avg_loss_pct]<=0, 0.01, [avg_loss_pct])`

**Linear Scale (Impact View):**
Shows business impact. Frontier contributes the long tail up to 80% loss. 4 units >60% loss are Frontier/Verizon. The 2%-40% cluster (~89 units) is what inflates Frontier to 77% At Risk.

**Logarithmic Scale (Diagnostic View):**
With `Y-Axis > Logarithmic scale = On`, distribution below 1% is visible:
- Healthy: 0.2% - 0.9% loss (mostly Cincinnati Bell)
- At Risk: 1.2% - 80% loss (mostly Frontier)

Threshold `loss >1%` in `risk_flag` is the natural breakpoint. Best-performing ISP keeps fleet below 1%.

**Technical Note - 0.01 cluster:**
Dense line at Y=0.01 is units with 0% loss mapped to 0.01 to enable `log(0)`. Retained to preserve Total Units = 258. 

### JITTER vs LOSS Page

**Setup:** X `p95_jitter_ms`, Y `avg_loss_pct_for_log` (Log On), Legend `risk_flag`

**Result:** Max jitter 3.1ms. No unit exceeds `jitter >5ms`. Therefore jitter does not contribute to current risk. All yellow points (risk_flag=1) in low loss area are not from jitter, they are from loss >1% but close to threshold. This validates risk is loss-driven, not voice/video instability.

---

## Root Cause by ISP (Data-Backed)

From `ftth_final_258_v2_1.csv`:

| ISP | Total Units | At Risk % | Avg Loss % | Avg Latency p95 | Avg Jitter p95 |
| --- | --- | --- | --- | --- | --- |
| Frontier | 62 | 77.42% | 7.18% | 8.31 ms | 0.96 ms |
| Verizon | 76 | 36.84% | 6.21% | 12.08 ms | 1.78 ms |
| Cincinnati Bell | 120 | 10.83% | 1.19% | 14.80 ms | 0.71 ms |

- **Frontier:** Critical. 48 at-risk units. Highest average loss. Main driver of OPEX and % Severe.
- **Verizon:** Degraded. High average loss but lower at-risk rate due to spread (many zeros + many highs).
- **Cincinnati Bell:** Healthy reference. Lowest average loss despite slightly higher latency.

---

## Action

1.  **P0 - Critical (>40% loss):** Immediate dispatch for Frontier/Verizon top 4 units. Outside plant / optical power check. Prevents churn.
2.  **P1 - Degraded (2%-40% loss):** Remote check before truck roll for Frontier (48 units) and Verizon (28 units). This action drives the $6,660 OPEX Saved shown in Executive.
3.  **P2 - Flag Tuning:** Current jitter threshold 5ms never triggers. Lower to 2.5ms for early voice/video warning, or keep as severe-only detector.

**Conclusion:** Executive identifies Frontier as highest risk at 77.42%. QoE Risk proves why: 7.18% average packet loss. JITTER vs LOSS proves what is not the cause: jitter is stable under 3.1ms.

---
*File: powerbianalysis.pbix | Data: ftth_final_258_v2_1.csv | Total Units: 258*
