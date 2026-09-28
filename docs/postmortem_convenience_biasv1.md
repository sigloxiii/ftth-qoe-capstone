# Postmortem: Convenience Bias in v1 Sampling - FCC MBA FTTH

**Date:** 2026-09-27  
**Author:** Ing. Rafael Cansigno Peláez  
**Status:** `v1 FAILED` -> `v2 CORRECTED`  
**Severity:** High - Invalidated ROI and risk_flag distribution  
**Related:** `data/methodology_v1_FAILED/` | `python/corrected_ingest.py`

---

## 1. Executive Summary

During peer review of methodology v1, we identified a **convenience sampling bias** introduced by using `df.head(1000)` / `pd.read_csv(..., nrows=1000)` on FCC Measuring Broadband America (MBA) monthly CSVs.

The first 1000 rows are not random. They correspond systematically to the oldest `unit_id` enrolled in the MBA program (2012-2016, SamKnows Whitebox v1). This caused overestimation of `risk_flag` by ~3.2x and invalidated the truck-roll savings model.

**Decision:** Preserve v1 intact as audit evidence in `/data/methodology_v1_FAILED/` and rebuild the project under v2.0 with stratified probabilistic sampling.

This document follows Google Data Analytics Phase 6 (Act) - documenting limitations and corrective actions.

## 2. v1 Methodology (Failed)

### What was done:

```python
# notebooks/01_ingest.ipynb - v1
df = pd.read_csv("2023-08-UDP.csv", nrows=1000)
# or
df = pd.read_csv("2023-08-UDP.csv").head(1000)

ftth_df = df[df['technology'] == 'FIBER'] # Filter AFTER sampling
p95 = ftth_df['rtt'].quantile(0.95)
risk_flag = (p95 > 80) | (loss > 0.015)