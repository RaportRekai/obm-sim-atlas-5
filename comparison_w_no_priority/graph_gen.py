#!/usr/bin/env python3
import re
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# ── INPUT FILES ────────────────────────────────────────────────────────────────
PATH_NO_PRIO = "/home/dan/LQD/obm-sim/obm-sim/comparison_w_no_priority/stats_obm_no_priority.txt"
PATH_W_PRIO  = "/home/dan/LQD/obm-sim/obm-sim/comparison_w_no_priority/stats_obm_w_priority.txt"

# ── OUTPUT DIR ────────────────────────────────────────────────────────────────
# generic (always the same folder as the inputs)
OUT_DIR = Path(PATH_NO_PRIO).parent
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ── PARSER ────────────────────────────────────────────────────────────────────
INC_RE  = re.compile(r"incast-trace-100G-degree-([0-9.]+)\.csv\.processed")
WEB_RE  = re.compile(r"websearch-trace-100G-load-([0-9.]+)\.csv\.processed")

P99S_RE   = re.compile(r"p99 FCT short flows:\s*([0-9.]+)us")
P999S_RE  = re.compile(r"p99\.9 FCT short flows:\s*([0-9.]+)us")
P99L_RE   = re.compile(r"p99 FCT long flows:\s*([0-9.]+)us")
P999L_RE  = re.compile(r"p99\.9 FCT long flows:\s*([0-9.]+)us")

def parse_stats(txt_path):
    """
    Returns nested dict:
    data[workload]['incast'|'websearch'][load_str]['short'|'long']['p99'|'p99.9'] -> float(us)
    """
    txt = Path(txt_path).read_text().splitlines()
    data = {'incast': {}, 'websearch': {}}

    curr_wl = None  # 'incast' | 'websearch'
    curr_load = None

    def ensure(d, k, default):
        if k not in d: d[k] = default
        return d[k]

    for line in txt:
        line = line.strip()
        if not line: 
            continue

        if line.startswith("workloads/"):
            m_in = INC_RE.search(line)
            m_ws = WEB_RE.search(line)
            if m_in:
                curr_wl = 'incast'
                curr_load = m_in.group(1)  # e.g., "0.2"
            elif m_ws:
                curr_wl = 'websearch'
                curr_load = m_ws.group(1)  # e.g., "0.3"
            else:
                curr_wl = None
                curr_load = None
            if curr_wl:
                ensure(data[curr_wl], curr_load, {'short': {}, 'long': {}})
            continue

        if not curr_wl or not curr_load:
            continue

        # Extract metrics
        if P99S_RE.search(line):
            v = float(P99S_RE.search(line).group(1))
            data[curr_wl][curr_load]['short']['p99'] = v
        elif P999S_RE.search(line):
            v = float(P999S_RE.search(line).group(1))
            data[curr_wl][curr_load]['short']['p99.9'] = v
        elif P99L_RE.search(line):
            v = float(P99L_RE.search(line).group(1))
            data[curr_wl][curr_load]['long']['p99'] = v
        elif P999L_RE.search(line):
            v = float(P999L_RE.search(line).group(1))
            data[curr_wl][curr_load]['long']['p99.9'] = v

    return data

no_prio = parse_stats(PATH_NO_PRIO)
w_prio  = parse_stats(PATH_W_PRIO)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def series_for(workload, flow_kind, perc, loads_order):
    """Return two aligned arrays (no_priority, with_priority) for the requested slice."""
    a = []
    b = []
    for ld in loads_order:
        # default to np.nan if missing
        v_a = no_prio[workload].get(ld, {}).get(flow_kind, {}).get(perc, np.nan)
        v_b = w_prio[workload].get(ld, {}).get(flow_kind, {}).get(perc, np.nan)
        a.append(v_a)
        b.append(v_b)
    return np.array(a, dtype=float), np.array(b, dtype=float)

def plot_one(workload, flow_kind, perc, loads_order, xlabel, title_stub):
    y_a, y_b = series_for(workload, flow_kind, perc, loads_order)

    x = np.arange(len(loads_order))
    width = 0.38

    fig, ax = plt.subplots(figsize=(7,4.5), dpi=160)
    ax.bar(x - width/2, y_b, width, label="With Priority",  edgecolor='black')
    ax.bar(x + width/2, y_a, width, label="No Priority",    edgecolor='black')

    ax.set_xticks(x)
    ax.set_xticklabels(loads_order, fontsize=11)
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel("FCT (us)", fontsize=12)
    ax.set_title(f"{title_stub} – {perc}", fontsize=13)

    # Nice headroom
    ymax = np.nanmax([y_a, y_b])
    if np.isfinite(ymax):
        ax.set_ylim(0, ymax * 1.15)

    ax.grid(axis='y', linestyle='--', alpha=0.4)
    ax.legend(frameon=True, fontsize=10)

    fname = f"{workload}_{flow_kind}_{perc.replace('.','')}.png"
    out_path = OUT_DIR / fname
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    print("Saved", out_path)

# ── PLOTS (8 graphs) ──────────────────────────────────────────────────────────
# Incast loads and Websearch loads (x-axis tick order)
incast_loads    = ["0.2", "0.4", "0.6", "0.8"]
websearch_loads = ["0.3", "0.6", "0.9"]

# 1–4: Incast (short/long) × (p99/p99.9)
plot_one("incast", "short", "p99",   incast_loads,    "Load (degree)", "Incast Short FCT")
plot_one("incast", "short", "p99.9", incast_loads,    "Load (degree)", "Incast Short FCT")
plot_one("incast", "long",  "p99",   incast_loads,    "Load (degree)", "Incast Long FCT")
plot_one("incast", "long",  "p99.9", incast_loads,    "Load (degree)", "Incast Long FCT")

# 5–8: Websearch (short/long) × (p99/p99.9)
plot_one("websearch", "short", "p99",   websearch_loads, "Load", "Websearch Short FCT")
plot_one("websearch", "short", "p99.9", websearch_loads, "Load", "Websearch Short FCT")
plot_one("websearch", "long",  "p99",   websearch_loads, "Load", "Websearch Long FCT")
plot_one("websearch", "long",  "p99.9", websearch_loads, "Load", "Websearch Long FCT")
