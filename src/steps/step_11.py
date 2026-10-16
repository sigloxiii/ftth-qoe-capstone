# step_11.py
# Objective: Test whether the latency flags of the base case come from a chronic problem or from
#            isolated events, and whether the event of unit 4190285 is specific to the unit or
#            shared by its test server (step_10.py: 6 of its 66 peak records > 30 ms, all on
#            2022-10-23).
#            A) For each unit flagged by latency in step_9.py: concentration of the records above
#               the base threshold by day, and the P95 after removing its worst day.
#            B) Unit 4190285, day 2022-10-23: median RTT of the OTHER units that use the same
#               server, by hour, against the same hours on the other days. If the other units also
#               rise, the event is on the server or the route, not on the unit's line.
#            Diagnostics only: the base case and the thresholds do not change (D4).
# Inputs:    data/interim/udplatency_ftth.csv (created by step_1.py)
# Outputs:   Console only (paste the result in the OUTPUT docstring at the end of this file)

import pandas as pd

BASE = r"D:\Capstone FTTH"
INTERIM = BASE + r"\data\interim"
PEAK_START, PEAK_END = 19, 23           # local hour, [19, 23)
T_LAT = 20                              # base latency threshold
KEY = ["unit_id", "dtime", "target"]
FLAGGED = [943226, 4190285, 24733221, 24840041, 25314177]   # at risk in step_9.py (base case)
UNIT, DAY = 4190285, "2022-10-23"

lat = pd.read_csv(INTERIM + r"\udplatency_ftth.csv", parse_dates=["dtime"])
lat = lat.drop_duplicates()                              # D-05: exact copies keep one
lat = lat[~lat.duplicated(KEY, keep=False)].copy()       # D-05: conflicting copies are dropped
lat["rtt_ms"] = lat["rtt_avg"] / 1000
lat["day"] = lat["dtime"].dt.date

h = lat["dtime"].dt.hour                                 # D-03: dtime is local time
lp = lat[(h >= PEAK_START) & (h < PEAK_END)]

# D-04 / D1: primary server = target with most peak records (ties alphabetical)
cnt = lp.groupby(["unit_id", "target"]).size().reset_index(name="n")
main = cnt.sort_values(["unit_id", "n", "target"], ascending=[True, False, True]).drop_duplicates("unit_id")
lp = lp.merge(main[["unit_id", "target"]], on=["unit_id", "target"])

# ---------------------------------------------------------------- A) Chronic vs isolated
print("=== A) Records above %d ms in the peak window (primary server) ===" % T_LAT)
rows = []
for u in FLAGGED:
    r = lp[lp["unit_id"] == u]
    exc = r[r["rtt_ms"] > T_LAT]
    by_day = exc["day"].value_counts()
    worst = by_day.index[0] if len(by_day) else None
    rest = r[r["day"] != worst]                          # same unit without its worst day
    rows.append({
        "unit_id": u, "n_peak": len(r), "p95_ms": round(r["rtt_ms"].quantile(0.95), 2),
        "n_above": len(exc), "days_above": by_day.size,
        "worst_day": str(worst), "share_worst_day": round(by_day.iloc[0] / len(exc), 2) if len(exc) else None,
        "n_without_worst": len(rest), "p95_without_worst": round(rest["rtt_ms"].quantile(0.95), 2),
    })
print(pd.DataFrame(rows).set_index("unit_id").to_string())

# ---------------------------------------------------------------- B) Server-wide event?
target = main.loc[main["unit_id"] == UNIT, "target"].iloc[0]
print(f"\n=== B) Unit {UNIT}, server {target}, day {DAY}: other units on the same server ===")
srv = lat[(lat["target"] == target) & (lat["unit_id"] != UNIT)].copy()
srv["hour"] = srv["dtime"].dt.hour
srv["is_day"] = srv["day"].astype(str) == DAY
print("Other units using this server:", srv["unit_id"].nunique())
tab = srv.groupby(["hour", "is_day"])["rtt_ms"].median().unstack("is_day").round(1)
tab.columns = ["other_days_median_ms", "event_day_median_ms"]
tab["n_event_day_records"] = srv[srv["is_day"]].groupby("hour").size()
own = lat[(lat["unit_id"] == UNIT) & (lat["target"] == target)].copy()
own["hour"] = own["dtime"].dt.hour
tab["own_event_day_median_ms"] = own[own["day"].astype(str) == DAY].groupby("hour")["rtt_ms"].median().round(1)
print(tab.loc[16:23].to_string())



'''
=== A) Records above 20 ms in the peak window (primary server) ===
          n_peak  p95_ms  n_above  days_above   worst_day  share_worst_day  n_without_worst  p95_without_worst
unit_id                                                                                                       
943226        53   23.13       11           9  2022-10-16             0.27               48              22.86
4190285       66   50.00        6           1  2022-10-23             1.00               60              14.77
24733221      59   23.96       10           7  2022-09-20             0.20               55              23.98
24840041     131   35.80       44          16  2022-10-11             0.09              127              35.81
25314177      62   30.48       28           9  2022-10-11             0.18               57              23.09

=== B) Unit 4190285, server sp1-vm-ashburn-us.samknows.com, day 2022-10-23: other units on the same server ===
Other units using this server: 69
      other_days_median_ms  event_day_median_ms  n_event_day_records  own_event_day_median_ms
hour                                                                                         
16                    10.1                  9.4                   35                     32.1
17                    10.1                  9.4                   35                     30.0
18                    10.0                  8.4                   34                     53.6
19                    10.1                  8.8                   36                     53.6
20                    10.2                  8.5                   38                     54.8
21                    10.7                  8.7                   44                     57.3
22                    10.6                  9.7                   38                     36.8
23                    10.1                  8.6                   34                     12.5
'''