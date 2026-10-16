# step_10.py
# Objective: Close the two data checks that step_9.py leaves open (base case: local time,
#            primary server of the latency file, peak window [19, 23)).
#            A) Jitter unit: compare jitter_up / jitter_down with rtt_std per unit. If both are
#               in microseconds, their magnitudes should be of the same order (spec section 5,
#               data_dictionary check 2).
#            B) Unit 4190285: P95 latency = 50.00 ms exactly in step_9.py. Show the values around
#               the P95 position and the days with high latency, to decide whether it is a real
#               degradation, a few outlier days, or a measurement ceiling.
#            Note: the interim latency file from step_1.py keeps only rtt_avg, rtt_min, successes
#            and failures. rtt_std and rtt_max are read once from the raw file (258 units only)
#            and cached, so step_1.py does not have to be changed or rerun.
# Inputs:    data/fiber_units.csv
#            data/interim/udplatency_ftth.csv, udpjitter_ftth.csv (created by step_1.py)
#            data/raw/validated-data-sept2022/curr_udplatency.csv (first run only)
# Outputs:   data/interim/udplatency_extra_ftth.csv (cache, gitignored)
#            Console only (paste the result in the OUTPUT docstring at the end of this file)

import os
import pandas as pd

BASE = r"D:\Capstone FTTH"
RAW = BASE + r"\data\raw\validated-data-sept2022"
INTERIM = BASE + r"\data\interim"
PEAK_START, PEAK_END = 19, 23            # local hour, [19, 23)
KEY = ["unit_id", "dtime", "target"]
UNIT = 4190285

lat = pd.read_csv(INTERIM + r"\udplatency_ftth.csv", parse_dates=["dtime"])
jit = pd.read_csv(INTERIM + r"\udpjitter_ftth.csv", parse_dates=["dtime"])

# D-05: exact duplicates keep one; conflicting duplicates are dropped entirely
lat = lat.drop_duplicates()
jit = jit.drop_duplicates()
lat = lat[~lat.duplicated(KEY, keep=False)].copy()
jit = jit[~jit.duplicated(KEY, keep=False)].copy()

# rtt_std and rtt_max: not in the interim file, read once from the raw file and cached
extra_file = INTERIM + r"\udplatency_extra_ftth.csv"
if not os.path.exists(extra_file):
    ids = set(lat["unit_id"])
    parts = []
    for chunk in pd.read_csv(RAW + r"\curr_udplatency.csv", usecols=KEY + ["rtt_std", "rtt_max"],
                             parse_dates=["dtime"], chunksize=2_000_000):
        parts.append(chunk[chunk["unit_id"].isin(ids)])  # only the FTTH units
    pd.concat(parts).to_csv(extra_file, index=False)
extra = pd.read_csv(extra_file, parse_dates=["dtime"]).drop_duplicates()
extra = extra[~extra.duplicated(KEY, keep=False)]        # same D-05 rule
lat = lat.merge(extra, on=KEY, how="left")
print("Latency rows without rtt_std after merge:", int(lat["rtt_std"].isna().sum()), "of", len(lat))

lat["rtt_ms"] = lat["rtt_avg"] / 1000
jit["jitter_ms"] = (jit["jitter_up"] + jit["jitter_down"]) / 2 / 1000

def peak(df):
    h = df["dtime"].dt.hour  # D-03: dtime is local time
    return df[(h >= PEAK_START) & (h < PEAK_END)]

lp, jp = peak(lat), peak(jit)

# D-04 / D1: primary server = target with most peak latency records (ties alphabetical)
cnt = lp.groupby(["unit_id", "target"]).size().reset_index(name="n")
main = cnt.sort_values(["unit_id", "n", "target"], ascending=[True, False, True]).drop_duplicates("unit_id")
lp = lp.merge(main[["unit_id", "target"]], on=["unit_id", "target"])
jp = jp.merge(main[["unit_id", "target"]], on=["unit_id", "target"])

# ---------------------------------------------------------------- A) Jitter unit
print("=== A) Jitter unit: per-unit medians, peak window, primary server ===")
cmp_ = pd.DataFrame({
    "jitter_ms_if_us": jp.groupby("unit_id")["jitter_ms"].median(),
    "rtt_std_ms_if_us": (lp["rtt_std"] / 1000).groupby(lp["unit_id"]).median(),
}).dropna()
print(cmp_.describe().round(2))
print("Median of (jitter / rtt_std) per unit; near 1 supports microseconds:",
      round((cmp_["jitter_ms_if_us"] / cmp_["rtt_std_ms_if_us"]).median(), 2))
print("Spearman correlation between both:", round(cmp_.corr(method="spearman").iloc[0, 1], 3))
print("Raw max jitter_up / jitter_down:", int(jit["jitter_up"].max()), int(jit["jitter_down"].max()))
print("Raw median jitter_up / jitter_down:", int(jit["jitter_up"].median()), int(jit["jitter_down"].median()))

# ---------------------------------------------------------------- B) Unit 4190285
print(f"\n=== B) Unit {UNIT}: P95 latency at the peak window ===")
print("Rows with rtt_ms == 50.0 exactly (all units, all hours):", int((lat["rtt_ms"] == 50.0).sum()))
print("Max rtt_ms (all units, all hours):", round(lat["rtt_ms"].max(), 2))
u = lp[lp["unit_id"] == UNIT].sort_values("rtt_ms")
n = len(u)
pos = 0.95 * (n - 1)  # linear interpolation position (pandas quantile default)
lo, hi = int(pos), min(int(pos) + 1, n - 1)
print(f"Peak records: {n} | target: {u['target'].iloc[0]} | P95 position {pos:.2f} -> "
      f"between sorted values #{lo + 1} ({u['rtt_ms'].iloc[lo]:.2f} ms) and #{hi + 1} ({u['rtt_ms'].iloc[hi]:.2f} ms)")
print("P95 computed:", round(u["rtt_ms"].quantile(0.95), 2))
print("Quantiles (ms):", u["rtt_ms"].quantile([0.5, 0.75, 0.9, 0.95, 1]).round(2).to_dict())
print("Top 8 records (dtime, rtt_ms, rtt_min ms, rtt_max ms):")
print(u.sort_values("rtt_ms", ascending=False).head(8)
        .assign(rtt_min_ms=lambda d: d["rtt_min"] / 1000, rtt_max_ms=lambda d: d["rtt_max"] / 1000)
        [["dtime", "rtt_ms", "rtt_min_ms", "rtt_max_ms"]]
        .round({"rtt_ms": 2, "rtt_min_ms": 2, "rtt_max_ms": 2}).to_string())
print("Records with rtt_ms > 30 per day:")
print(u.loc[u["rtt_ms"] > 30, "dtime"].dt.date.value_counts().sort_index().to_string())
# All hours of the same unit and server: is the degradation specific to the evening?
ua = lat[(lat["unit_id"] == UNIT) & (lat["target"] == u["target"].iloc[0])]
print("Median rtt_ms by local hour (all hours, same server):")
print(ua.groupby(ua["dtime"].dt.hour)["rtt_ms"].median().round(1).to_string())


'''
Latency rows without rtt_std after merge: 0 of 172791
=== A) Jitter unit: per-unit medians, peak window, primary server ===
       jitter_ms_if_us  rtt_std_ms_if_us
count           258.00            258.00
mean              0.88              1.13
std               0.73              0.87
min               0.08              0.15
25%               0.36              0.53
50%               0.70              0.96
75%               1.03              1.19
max               2.76              3.50
Median of (jitter / rtt_std) per unit; near 1 supports microseconds: 0.83
Spearman correlation between both: 0.816
Raw max jitter_up / jitter_down: 580881 428137
Raw median jitter_up / jitter_down: 1220 86

=== B) Unit 4190285: P95 latency at the peak window ===
Rows with rtt_ms == 50.0 exactly (all units, all hours): 0
Max rtt_ms (all units, all hours): 94.65
Peak records: 66 | target: sp1-vm-ashburn-us.samknows.com | P95 position 61.75 -> between sorted values #62 (39.26 ms) and #63 (53.59 ms)
P95 computed: 50.0
Quantiles (ms): {0.5: 14.08, 0.75: 14.34, 0.9: 15.76, 0.95: 50.0, 1.0: 57.57}
Top 8 records (dtime, rtt_ms, rtt_min ms, rtt_max ms):
                    dtime  rtt_ms  rtt_min_ms  rtt_max_ms
14318 2022-10-23 21:44:55   57.57       45.43       66.36
311   2022-10-23 21:37:54   57.34       40.33       66.74
312   2022-10-23 20:37:54   54.85       36.03       65.80
19431 2022-10-23 19:37:54   53.59       25.72       66.18
18160 2022-10-23 21:46:26   39.26       29.42       47.28
6721  2022-10-23 22:47:56   36.84        7.65       64.95
22027 2022-10-22 22:37:55   16.68        6.68       32.66
13050 2022-10-21 19:37:53   14.86        9.10       21.10
Records with rtt_ms > 30 per day:
dtime
2022-10-23    6
Median rtt_ms by local hour (all hours, same server):
dtime
0     13.8
1     13.7
2     13.8
3     13.9
4     13.9
5     13.9
6     13.9
7     14.0
8     14.0
9     13.8
10    14.0
11    13.9
12    14.0
13    13.9
14    13.9
15    14.0
16    14.0
17    14.0
18    14.0
19    14.1
20    14.1
21    14.2
22    14.0
23    14.0
'''