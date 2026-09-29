"""
carbon_analysis/plot_graphs.py
Generates all graphs for the report from carbon_results.csv

Run: .venv\Scripts\python.exe -m carbon_analysis.plot_graphs
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

RESULTS_CSV = "carbon_analysis/results/carbon_results.csv"
OUTPUT_DIR  = "carbon_analysis/graphs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Style ─────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family':   'DejaVu Sans',
    'font.size':     11,
    'axes.titlesize': 13,
    'axes.labelsize': 11,
    'axes.grid':     True,
    'grid.alpha':    0.3,
    'figure.dpi':    150,
})

COLORS = {
    'Static':  '#1F3864',   # dark navy
    'Dynamic': '#2E75B6',   # medium blue
    'Pure_ML': '#C00000',   # deep red
}
MARKERS = {'Static': 'o', 'Dynamic': 's', 'Pure_ML': '^'}

def load_data():
    if not os.path.exists(RESULTS_CSV):
        print(f"Results not found at {RESULTS_CSV}")
        print("Run measure_carbon.py first.")
        return None
    return pd.read_csv(RESULTS_CSV)


def plot_execution_time(df):
    """Graph 1: Execution time vs code size for all three modes."""
    fig, ax = plt.subplots(figsize=(8, 5))
    lines_vals = sorted(df['lines'].unique())

    for mode in ['Static', 'Dynamic', 'Pure_ML']:
        subset = df[df['mode'] == mode].sort_values('lines')
        ax.plot(subset['lines'], subset['avg_time_ms'],
                color=COLORS[mode], marker=MARKERS[mode],
                linewidth=2, markersize=8, label=mode)
        ax.fill_between(
            subset['lines'],
            subset['avg_time_ms'] - subset['std_time_ms'],
            subset['avg_time_ms'] + subset['std_time_ms'],
            alpha=0.15, color=COLORS[mode]
        )

    ax.set_xlabel("Source Code Size (lines)")
    ax.set_ylabel("Average Execution Time (ms)")
    ax.set_title("Execution Time vs Code Size\nStatic vs Dynamic vs Pure ML")
    ax.legend(title="Analysis Mode")
    ax.set_xticks(lines_vals)
    plt.tight_layout()
    path = f"{OUTPUT_DIR}/graph1_execution_time.png"
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f"Saved: {path}")


def plot_co2_emissions(df):
    """Graph 2: CO2 emissions vs code size."""
    fig, ax = plt.subplots(figsize=(8, 5))
    lines_vals = sorted(df['lines'].unique())

    for mode in ['Static', 'Dynamic', 'Pure_ML']:
        subset = df[df['mode'] == mode].sort_values('lines')
        ax.plot(subset['lines'], subset['emissions_g_co2'] * 1000,  # convert to mg
                color=COLORS[mode], marker=MARKERS[mode],
                linewidth=2, markersize=8, label=mode)

    ax.set_xlabel("Source Code Size (lines)")
    ax.set_ylabel("CO₂ Emissions (mg CO₂eq)")
    ax.set_title("CO₂ Emissions vs Code Size\nStatic vs Dynamic vs Pure ML")
    ax.legend(title="Analysis Mode")
    ax.set_xticks(lines_vals)
    plt.tight_layout()
    path = f"{OUTPUT_DIR}/graph2_co2_emissions.png"
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f"Saved: {path}")


def plot_grouped_bar_time(df):
    """Graph 3: Grouped bar chart — time per mode per file size."""
    fig, ax = plt.subplots(figsize=(9, 5))
    line_sizes = sorted(df['lines'].unique())
    modes      = ['Static', 'Dynamic', 'Pure_ML']
    x          = np.arange(len(line_sizes))
    width      = 0.25

    for i, mode in enumerate(modes):
        subset = df[df['mode'] == mode].sort_values('lines')
        vals   = subset['avg_time_ms'].values
        errs   = subset['std_time_ms'].values
        bars   = ax.bar(x + i*width, vals, width,
                        label=mode, color=COLORS[mode],
                        yerr=errs, capsize=4, alpha=0.85)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{val:.1f}', ha='center', va='bottom', fontsize=8)

    ax.set_xlabel("Source Code Size (lines)")
    ax.set_ylabel("Execution Time (ms)")
    ax.set_title("Execution Time Comparison by Analysis Mode")
    ax.set_xticks(x + width)
    ax.set_xticklabels([f"{l} lines" for l in line_sizes])
    ax.legend(title="Mode")
    plt.tight_layout()
    path = f"{OUTPUT_DIR}/graph3_grouped_bar_time.png"
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f"Saved: {path}")


def plot_co2_per_token(df):
    """Graph 4: CO2 per token analysed — efficiency metric."""
    fig, ax = plt.subplots(figsize=(8, 5))
    lines_vals = sorted(df['lines'].unique())

    for mode in ['Static', 'Dynamic', 'Pure_ML']:
        subset = df[df['mode'] == mode].sort_values('lines').copy()
        subset['co2_per_token'] = (
            subset['emissions_g_co2'] * 1e6 / subset['tokens'].clip(lower=1)
        )
        ax.plot(subset['lines'], subset['co2_per_token'],
                color=COLORS[mode], marker=MARKERS[mode],
                linewidth=2, markersize=8, label=mode)

    ax.set_xlabel("Source Code Size (lines)")
    ax.set_ylabel("CO₂ per Token (μg CO₂eq)")
    ax.set_title("Carbon Efficiency: CO₂ per Token Analysed")
    ax.legend(title="Analysis Mode")
    ax.set_xticks(lines_vals)
    plt.tight_layout()
    path = f"{OUTPUT_DIR}/graph4_co2_per_token.png"
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f"Saved: {path}")


def plot_scalability(df):
    """Graph 5: Scalability — time per line of code."""
    fig, ax = plt.subplots(figsize=(8, 5))

    for mode in ['Static', 'Dynamic', 'Pure_ML']:
        subset = df[df['mode'] == mode].sort_values('lines').copy()
        subset['ms_per_line'] = subset['avg_time_ms'] / subset['lines']
        ax.plot(subset['lines'], subset['ms_per_line'],
                color=COLORS[mode], marker=MARKERS[mode],
                linewidth=2, markersize=8, label=mode)

    ax.set_xlabel("Source Code Size (lines)")
    ax.set_ylabel("Time per Line (ms/line)")
    ax.set_title("Scalability: Analysis Time per Line of Code")
    ax.legend(title="Analysis Mode")
    plt.tight_layout()
    path = f"{OUTPUT_DIR}/graph5_scalability.png"
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f"Saved: {path}")


def plot_detection_rate(df):
    """Graph 6: Flagged tokens vs code size — detection coverage."""
    fig, ax = plt.subplots(figsize=(8, 5))

    for mode in ['Static', 'Dynamic', 'Pure_ML']:
        subset = df[df['mode'] == mode].sort_values('lines').copy()
        subset['detection_rate'] = subset['flagged'] / subset['tokens'].clip(lower=1) * 100
        ax.plot(subset['lines'], subset['detection_rate'],
                color=COLORS[mode], marker=MARKERS[mode],
                linewidth=2, markersize=8, label=mode)

    ax.set_xlabel("Source Code Size (lines)")
    ax.set_ylabel("Detection Rate (%)")
    ax.set_title("Detection Rate: Flagged Tokens as % of Total Tokens")
    ax.legend(title="Analysis Mode")
    plt.tight_layout()
    path = f"{OUTPUT_DIR}/graph6_detection_rate.png"
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f"Saved: {path}")


def main():
    df = load_data()
    if df is None:
        return

    print(f"Loaded {len(df)} records from {RESULTS_CSV}")
    print(df.to_string(index=False))
    print("\nGenerating graphs...")

    plot_execution_time(df)
    plot_co2_emissions(df)
    plot_grouped_bar_time(df)
    plot_co2_per_token(df)
    plot_scalability(df)
    plot_detection_rate(df)

    print(f"\nAll graphs saved to {OUTPUT_DIR}/")
    print("Add these 6 PNG files to your report.")


if __name__ == "__main__":
    main()