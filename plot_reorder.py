#!/usr/bin/env python3
"""
plot_drop_bars.py
─────────────────
Generate TWO separate grouped-bar charts (DT/ABM/OBM/LQD) for x = 0.3, 0.6, 0.9:
  1) Thousands of Packets Reordered  -> reordered_thousands.png
  2) Thousands of Packets Dropped    -> dropped_thousands.png
"""

import os
import re
import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FuncFormatter

# ── Display mapping (identical colors & order) ────────────────────
ALGO_META = {
    "dt":  ("DT",  "#00FFFF"),
    "abm": ("ABM", "#FFD700"),
    "obm": ("OBM", "#FF0000"),
    "lqd": ("LQD", "#32CD32"),
}
ORDERED_LABELS = ["DT", "ABM", "OBM", "LQD"]

# ——— Same font/tick styling as your FCT code ———
YLABEL_FONTSIZE = 44
XLABEL_FONTSIZE = 42
YTICK_FONTSIZE  = 40
XTICK_FONTSIZE  = 38
LEGEND_FONTSIZE = 40
TICK_LENGTH     = 12
TICK_WIDTH      = 2.4

# Target number of visible y-ticks (after hiding the very top one)
MAX_YTICKS = 9

# Fixed X values (order must match file line order)
X_TICKS = [0.3, 0.6, 0.9]

RE_DROP    = re.compile(r"drop\s+count\s*=\s*([0-9]+)", re.I)
RE_REORDER = re.compile(r"reorder(?:ing)?\s+count\s*=\s*([0-9]+)", re.I)

# ── Helpers ───────────────────────────────────────────────────────
def compact_even_ticks(ax, max_ticks: int, bottom: float = 0.0):
    ax.set_ylim(bottom=bottom)
    locator = MaxNLocator(nbins=max_ticks, steps=[1, 2, 2.5, 5, 10])
    ax.yaxis.set_major_locator(locator)
    ticks = [t for t in ax.get_yticks() if t >= bottom]
    if len(ticks) < 2:
        return
    delta = ticks[1] - ticks[0]
    ax.set_ylim(top=ticks[-1] + delta, bottom=bottom)
    ax.yaxis.set_major_locator(locator)
    ticks2 = [t for t in ax.get_yticks() if t >= bottom]
    if len(ticks2) >= 2:
        ax.set_yticks(ticks2[:-1])
    ax.tick_params(axis="y", labelsize=YTICK_FONTSIZE, length=TICK_LENGTH, width=TICK_WIDTH)

def grouped_bars(ax, x_ticks, data_by_label, colors, ylabel):
    n = len(ORDERED_LABELS)
    group_gap   = 0.10
    group_width = 1.0 - group_gap

    shrink = 0.90
    bar_w  = (group_width / n) * shrink
    block_w = n * bar_w

    x_centers  = np.arange(len(x_ticks), dtype=float)
    group_left = x_centers - group_width / 2.0
    block_left = group_left + (group_width - block_w) / 2.0

    for j, lbl in enumerate(ORDERED_LABELS):
        y = np.array(data_by_label.get(lbl, []), dtype=float)
        lefts = block_left + j * bar_w
        ax.bar(lefts, y, align="edge", width=bar_w, label=lbl,
               color=colors[lbl], edgecolor="black", linewidth=1.8)

    ax.set_ylabel(ylabel, fontsize=YLABEL_FONTSIZE, labelpad=16)
    ax.set_xlabel("Load", fontsize=XLABEL_FONTSIZE, labelpad=10)
    ax.set_xticks(x_centers)
    ax.set_xticklabels([str(t) for t in x_ticks], fontsize=XTICK_FONTSIZE)
    ax.tick_params(axis="x", labelsize=XTICK_FONTSIZE, length=TICK_LENGTH, width=TICK_WIDTH)
    ax.yaxis.grid(True, linestyle=":", color="#999999", linewidth=1.2)
    ax.set_axisbelow(True)

def add_legend(ax):
    import numpy as np
    n = len(ORDERED_LABELS)
    ncol = int(np.ceil(np.sqrt(n)))
    lgd = ax.legend(loc="upper left", frameon=True, fontsize=LEGEND_FONTSIZE,
                    ncol=ncol, columnspacing=1.2, handlelength=1.8,
                    borderpad=0.7, labelspacing=0.7)
    lgd.get_frame().set_edgecolor("black")
    lgd.get_frame().set_linewidth(1.4)

# ── Parsing ───────────────────────────────────────────────────────
def parse_counts(path, regex):
    vals = []
    with open(path, "r", errors="ignore") as fh:
        for ln in fh:
            m = regex.search(ln)
            if m:
                vals.append(int(m.group(1)))
    if len(vals) != 3:
        raise ValueError(f"{path}: expected 3 '{regex.pattern}' lines, found {len(vals)}")
    return vals

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dt",  default="/home/dan/LQD/obm-sim/obm-sim/net-sim-dt/reordering_dt.txt")
    ap.add_argument("--abm", default="/home/dan/LQD/obm-sim/obm-sim/net-sim-abm/reordering_abm.txt")
    ap.add_argument("--obm", default="/home/dan/LQD/obm-sim/obm-sim/net-sim-obm/reordering_obm.txt")
    ap.add_argument("--lqd", default="/home/dan/LQD/obm-sim/obm-sim/net-sim-obm/reordering_lqd.txt")
    ap.add_argument("--out-reordered", default="reordered_thousands.png")
    ap.add_argument("--out-dropped",   default="dropped_thousands.png")
    args = ap.parse_args()

    # Colors by label
    colors = {ALGO_META[k][0]: ALGO_META[k][1] for k in ALGO_META}

    # Build series
    series_reord = {
        "DT":  parse_counts(args.dt,  RE_REORDER),
        "ABM": parse_counts(args.abm, RE_REORDER),
        "OBM": parse_counts(args.obm, RE_REORDER),
        "LQD": parse_counts(args.lqd, RE_REORDER),
    }
    series_drop = {
        "DT":  parse_counts(args.dt,  RE_DROP),
        "ABM": parse_counts(args.abm, RE_DROP),
        "OBM": parse_counts(args.obm, RE_DROP),
        "LQD": parse_counts(args.lqd, RE_DROP),
    }

    kfmt_int = FuncFormatter(lambda x, _: f"{x/1000:.0f}")  # integers in thousands

    # --- Figure 1: Reordered ---
    fig1, ax1 = plt.subplots(figsize=(14.5, 12.5))
    grouped_bars(ax1, X_TICKS, series_reord, colors,
                 ylabel="Thousands of Packets Reordered")
    compact_even_ticks(ax1, MAX_YTICKS, bottom=0)
    ax1.yaxis.set_major_formatter(kfmt_int)
    add_legend(ax1)
    fig1.tight_layout()
    fig1.savefig(args.out_reordered, dpi=400, bbox_inches="tight")

    # --- Figure 2: Dropped ---
    fig2, ax2 = plt.subplots(figsize=(14.5, 12.5))
    grouped_bars(ax2, X_TICKS, series_drop, colors,
                 ylabel="Thousands of Packets Dropped")
    compact_even_ticks(ax2, MAX_YTICKS, bottom=0)
    ax2.yaxis.set_major_formatter(kfmt_int)
    add_legend(ax2)
    fig2.tight_layout()
    fig2.savefig(args.out_dropped, dpi=400, bbox_inches="tight")

    print("Wrote:",
          os.path.abspath(args.out_reordered),
          "and",
          os.path.abspath(args.out_dropped))

if __name__ == "__main__":
    main()
