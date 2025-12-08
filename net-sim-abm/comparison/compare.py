#!/usr/bin/env python3
"""
compare_fct_abm_obm_lt.py
─────────────────────────
Compare FCTs per matching flow between ABM and OBM logs,
restricted to flows with flowsize < LT (default: 100).

Outputs:
  - fct_compare_abm_vs_obm_lt{LT}.csv  (full joined table for flowsize<LT)
  - fct_bad_abm_lt{LT}.csv             (ABM worse)
  - fct_bad_obm_lt{LT}.csv             (OBM worse)
"""

import argparse
import csv
import os
import re
import sys
from statistics import median

LINE_RE = re.compile(
    r"""
    (?P<idx>\d+)\s*,\s*
    src:\s*h(?P<src>\d+)\s*,\s*
    dst:\s*h(?P<dst>\d+)\s*,\s*
    sport:\s*(?P<sport>\d+)\s*,\s*
    dport:\s*(?P<dport>\d+)\s*,\s*
    flowsize:\s*(?P<flowsize>\d+)\s*,\s*
    starttime:\s*(?P<start>\d+)\s*,\s*
    finishtime:\s*(?P<finish>\d+)\s*,\s*
    fct:\s*(?P<fct>\d+)
    """,
    re.VERBOSE,
)

FlowKey = tuple  # (src, dst, sport, dport, flowsize, start)

def parse_file(path):
    results = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            m = LINE_RE.search(line)
            if not m:
                continue
            src = int(m.group("src"))
            dst = int(m.group("dst"))
            sport = int(m.group("sport"))
            dport = int(m.group("dport"))
            flowsize = int(m.group("flowsize"))
            start = int(m.group("start"))
            fct = int(m.group("fct"))
            key: FlowKey = (src, dst, sport, dport, flowsize, start)
            if key in results:
                results[key]["fct"] = min(results[key]["fct"], fct)
            else:
                results[key] = {
                    "fct": fct,
                    "flowsize": flowsize,
                    "src": src,
                    "dst": dst,
                    "sport": sport,
                    "dport": dport,
                    "start": start,
                }
    return results

def autodetect_files():
    files = [f for f in os.listdir(".") if os.path.isfile(f)]
    abm = next((f for f in files if "abm" in f.lower()), None)
    obm = next((f for f in files if "obm" in f.lower()), None)
    return abm, obm

def load_inputs(abm_path, obm_path):
    if not abm_path or not obm_path:
        a, o = autodetect_files()
        abm_path = abm_path or a
        obm_path = obm_path or o
    if not abm_path or not os.path.exists(abm_path):
        sys.exit("ERROR: ABM file not found. Pass with --abm or place a file containing 'abm' in its name here.")
    if not obm_path or not os.path.exists(obm_path):
        sys.exit("ERROR: OBM file not found. Pass with --obm or place a file containing 'obm' in its name here.")
    return abm_path, obm_path

def write_csv(rows, out_path):
    cols = [
        "src","dst","sport","dport","flowsize","start",
        "fct_abm","fct_obm","delta_abs","delta_pct","worse_algo"
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return out_path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--abm", help="Path to ABM file")
    ap.add_argument("--obm", help="Path to OBM file")
    ap.add_argument("--top", type=int, default=25, help="How many worst flows to print for each side")
    ap.add_argument("--lt", type=int, default=100, help="Compare flows with flowsize < LT (default: 100)")
    args = ap.parse_args()

    abm_path, obm_path = load_inputs(args.abm, args.obm)
    abm_all = parse_file(abm_path)
    obm_all = parse_file(obm_path)

    # Filter to flowsize < LT
    LT = args.lt
    abm = {k:v for k,v in abm_all.items() if k[4] < LT}
    obm = {k:v for k,v in obm_all.items() if k[4] < LT}

    keys_intersection = set(abm.keys()) & set(obm.keys())
    if not keys_intersection:
        sys.exit(f"No matching flows with flowsize < {LT} found between the two files.")

    rows = []
    for k in keys_intersection:
        a = abm[k]["fct"]
        o = obm[k]["fct"]
        delta_abs = a - o  # >0 => ABM slower
        baseline = min(a, o)
        delta_pct = ((abs(a - o)) / baseline) * 100.0 if baseline > 0 else 0.0
        worse = "ABM" if a > o else ("OBM" if o > a else "tie")
        src, dst, sport, dport, flowsize, start = k
        rows.append({
            "src": src, "dst": dst, "sport": sport, "dport": dport,
            "flowsize": flowsize, "start": start,
            "fct_abm": a, "fct_obm": o,
            "delta_abs": delta_abs,
            "delta_pct": round(delta_pct, 2),
            "worse_algo": worse
        })

    abm_worse = [r for r in rows if r["worse_algo"] == "ABM"]
    obm_worse = [r for r in rows if r["worse_algo"] == "OBM"]
    ties      = [r for r in rows if r["worse_algo"] == "tie"]

    def ratios(lst, num_key, den_key):
        vals = []
        for r in lst:
            num = r[num_key]; den = r[den_key]
            if den > 0:
                vals.append(num/den)
        return vals

    abm_over_obm = ratios(abm_worse, "fct_abm", "fct_obm")
    obm_over_abm = ratios(obm_worse, "fct_obm", "fct_abm")

    suffix = f"lt{LT}"
    write_csv(rows, f"fct_compare_abm_vs_obm_{suffix}.csv")
    write_csv(sorted(abm_worse, key=lambda r: r["delta_pct"], reverse=True), f"fct_bad_abm_{suffix}.csv")
    write_csv(sorted(obm_worse, key=lambda r: r["delta_pct"], reverse=True), f"fct_bad_obm_{suffix}.csv")

    total = len(rows)
    print(f"\n=== FCT Comparison (ABM vs OBM) — flowsize < {LT} ===")
    print(f"Files: ABM='{abm_path}'  OBM='{obm_path}'")
    print(f"Matched flows: {total}")
    print(f"ABM worse: {len(abm_worse)} | OBM worse: {len(obm_worse)} | ties: {len(ties)}")
    if abm_over_obm:
        print(f"ABM/OBM ratio  median={median(abm_over_obm):.3f}  max={max(abm_over_obm):.3f}")
    if obm_over_abm:
        print(f"OBM/ABM ratio  median={median(obm_over_abm):.3f}  max={max(obm_over_abm):.3f}")

    # Top offenders
    top = args.top
    print(f"\n--- Top {top} flows where ABM is worse (largest % over OBM) ---")
    for r in sorted(abm_worse, key=lambda r: r["delta_pct"], reverse=True)[:top]:
        print(f"[ABM>OBM by {r['delta_pct']:.1f}%] h{r['src']}->{r['dst']} ({r['sport']}/{r['dport']}), "
              f"size={r['flowsize']}, start={r['start']}, FCTs: ABM={r['fct_abm']}, OBM={r['fct_obm']}")

    print(f"\n--- Top {top} flows where OBM is worse (largest % over ABM) ---")
    for r in sorted(obm_worse, key=lambda r: r["delta_pct"], reverse=True)[:top]:
        print(f"[OBM>ABM by {r['delta_pct']:.1f}%] h{r['src']}->{r['dst']} ({r['sport']}/{r['dport']}), "
              f"size={r['flowsize']}, start={r['start']}, FCTs: OBM={r['fct_obm']}, ABM={r['fct_abm']}")

    print(f"\nWrote: fct_compare_abm_vs_obm_{suffix}.csv, fct_bad_abm_{suffix}.csv, fct_bad_obm_{suffix}.csv")

if __name__ == "__main__":
    main()
