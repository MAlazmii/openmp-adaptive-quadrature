"""Render the archived timing series and the local OpenMP measurements."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter, ScalarFormatter


ROOT = Path(__file__).resolve().parents[1]
THREADS = (1, 2, 4, 6, 8, 12, 16, 24, 32)
VARIANTS = ("solver1", "solver2")
COMPILERS = ("gnu", "intel")
TEAL = "#4de2c4"
AMBER = "#ffb877"
BLUE = "#a4bcfc"
TEXT = "#edf3fa"
MUTED = "#b3c4d6"
GRID = "#2d4560"
PANEL = "#132237"
BACKGROUND = "#0c1727"


def read_records():
    with (ROOT / "data/cirrus-timings.csv").open(newline="") as source:
        archived = {}
        for row in csv.DictReader(source):
            key = (row["variant"], row["compiler"], int(row["requested_threads"]))
            seconds = float(row["seconds"])
            if key in archived or not math.isfinite(seconds) or seconds <= 0:
                raise ValueError("Invalid historical timing series")
            archived[key] = seconds
    expected = {(v, c, t) for v in VARIANTS for c in COMPILERS for t in THREADS}
    if archived.keys() != expected:
        raise ValueError("Historical series must contain every documented configuration")

    local = json.loads((ROOT / "data/local-comparison.json").read_text())
    record = local["recursive_solver"]
    samples = {}
    for count in (1, 4):
        runs = record["samples_by_requested_threads"][str(count)]
        values = [float(run["seconds_as_printed"]) for run in runs]
        if len(values) != 3 or any(not math.isfinite(s) or s <= 0 for s in values):
            raise ValueError("Expected three positive local timings per thread count")
        if statistics.median(values) != record["median_seconds_by_requested_threads"][str(count)]:
            raise ValueError("Local median does not match the raw samples")
        if any(run["result_as_printed"] != record["common_result_as_printed"] for run in runs):
            raise ValueError("Printed result differs across local samples")
        samples[count] = values
    return archived, samples


def style_axis(axis, title, subtitle):
    axis.set_facecolor(PANEL)
    axis.text(0, 1.15, title, transform=axis.transAxes, color=TEXT,
              fontsize=16, fontweight="bold")
    axis.text(0, 1.064, subtitle, transform=axis.transAxes, color=MUTED, fontsize=10)
    axis.grid(axis="y", color=GRID, linewidth=0.9)
    axis.set_axisbelow(True)
    axis.spines[["right", "top"]].set_visible(False)
    for side in ("left", "bottom"):
        axis.spines[side].set_color(GRID)
    axis.tick_params(colors=MUTED, labelsize=10, length=0, pad=7)
    axis.set_xlabel("Requested threads", labelpad=10, color=MUTED)
    axis.set_ylabel("Elapsed time (s)", labelpad=10, color=MUTED)


def plot(output):
    archived, samples = read_records()
    fig, axes = plt.subplots(1, 3, figsize=(14.3, 6.1), facecolor=BACKGROUND,
                             gridspec_kw={"width_ratios": [1.1, 1.1, 0.88]})
    fig.subplots_adjust(left=0.076, right=0.974, bottom=0.242, top=0.647, wspace=0.36)
    fig.text(0.076, 0.927, "OPENMP ADAPTIVE QUADRATURE", color=TEAL,
             fontsize=12, fontweight="bold")
    fig.text(0.076, 0.85, "How runtime changed with thread count", color=TEXT,
             fontsize=26, fontweight="bold")
    fig.text(0.076, 0.796, "Coursework timing series alongside a fresh rebuild of the recursive solver.",
             color=MUTED, fontsize=12)

    for axis, variant, title, subtitle in zip(
        axes, VARIANTS, ("Recursive tasks", "Reported shared queue"),
        ("Archived coursework timings", "Archived timings · source unresolved")
    ):
        style_axis(axis, title, subtitle)
        axis.set_xscale("log", base=2)
        axis.set_yscale("log")
        axis.set_xticks([1, 2, 4, 8, 16, 32])
        axis.xaxis.set_major_formatter(ScalarFormatter())
        axis.xaxis.set_minor_formatter(NullFormatter())
        axis.set_yticks([1, 2, 4, 8, 16, 32])
        axis.yaxis.set_major_formatter(ScalarFormatter())
        axis.yaxis.set_minor_formatter(NullFormatter())
        axis.set_xlim(0.85, 37)
        axis.set_ylim(0.92, 46)
        for compiler, color, marker, linestyle in (
            ("gnu", TEAL, "o", "-"), ("intel", AMBER, "s", "--")
        ):
            axis.plot(THREADS, [archived[variant, compiler, t] for t in THREADS],
                      color=color, marker=marker, linestyle=linestyle,
                      linewidth=1.8, markersize=4.6, label=compiler.upper() if compiler == "gnu" else "Intel")
        axis.legend(loc="lower left", facecolor=PANEL, edgecolor=GRID,
                    labelcolor=TEXT, fontsize=9, framealpha=1)

    axis = axes[2]
    style_axis(axis, "Fresh recursive run", "Apple M1 · x86-64 Rosetta")
    for index, count in enumerate((1, 4)):
        series = samples[count]
        median = statistics.median(series)
        axis.scatter([index - 0.08, index, index + 0.08], series,
                     s=34, color=BLUE, zorder=3)
        axis.hlines(median, index - 0.25, index + 0.25, linewidth=2.0, color=TEXT)
        axis.annotate(f"{median:.2f} s", (index, max(series)), xytext=(0, 8),
                      textcoords="offset points", ha="center", color=TEXT, fontsize=10)
    axis.set_xticks([0, 1], ["1", "4"])
    axis.set_xlim(-0.55, 1.55)
    axis.set_ylim(0, max(samples[1] + samples[4]) * 1.18)

    fig.text(0.076, 0.095,
             "Historical plots use log scales. Each point is a single timing from the submitted report.",
             color=MUTED, fontsize=10)
    fig.text(0.076, 0.052,
             "Fresh measurements use separate processes. Dots show every sample and bars mark medians.",
             color=MUTED, fontsize=10)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=175, facecolor=BACKGROUND,
                metadata={"Software": "OpenMP Adaptive Quadrature"})
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "figures/thread-scaling.png")
    plot(parser.parse_args().output)
