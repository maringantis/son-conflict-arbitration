"""Generate figures from simulation outputs (submission version)."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES = os.path.join(ROOT, "tables")
FIGS = os.path.join(ROOT, "figures")
os.makedirs(FIGS, exist_ok=True)
plt.rcParams.update({"font.size": 10, "font.family": "serif",
                     "axes.grid": True, "grid.alpha": 0.3, "figure.dpi": 200})

t1 = pd.read_csv(os.path.join(TABLES, "table1_resolution_summary.csv"))
t2 = pd.read_csv(os.path.join(TABLES, "table2_by_intensity.csv"))
t3 = pd.read_csv(os.path.join(TABLES, "table3_compromise_stability.csv"))

# Fig 1: violation rate vs intensity
fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
for ax, pair, title in zip(axes, ["MLB_MRO", "CCO_ESM"], ["MLB vs MRO", "CCO vs ESM"]):
    sub = t2[t2["pair"] == pair].sort_values("disagreement_intensity")
    x = sub["disagreement_intensity"]
    ax.plot(x, sub["proposed_violation_rate"] * 100, marker="o", lw=2, label="Proposed")
    ax.plot(x, sub["static_violation_rate"] * 100, marker="s", lw=2, ls="--", label="Static precedence")
    ax.plot(x, sub["none_violation_rate"] * 100, marker="^", lw=2, ls=":", label="No coordination")
    ax.set_title(title)
    ax.set_xlabel("Agent disagreement intensity")
    ax.set_ylim(-5, 105)
axes[0].set_ylabel("Constraint-violation rate (%)")
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.10), frameon=False)
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "fig1_violation_rate_vs_intensity.png"), bbox_inches="tight")
plt.close()

# Fig 2: resolution rate
fig, ax = plt.subplots(figsize=(5.2, 3.6))
for pair, mk, lab in [("MLB_MRO", "o", "MLB vs MRO"), ("CCO_ESM", "s", "CCO vs ESM")]:
    sub = t2[t2["pair"] == pair].sort_values("disagreement_intensity")
    ax.plot(sub["disagreement_intensity"], sub["proposed_resolved_rate"] * 100, marker=mk, lw=2, label=lab)
ax.set_xlabel("Agent disagreement intensity")
ax.set_ylabel("Conflict resolution rate (%)")
ax.set_ylim(0, 105)
ax.legend(frameon=False)
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "fig2_resolution_rate.png"), bbox_inches="tight")
plt.close()

# Fig 3: aggregate bars
fig, ax = plt.subplots(figsize=(6.2, 3.8))
x, w = np.arange(len(t1)), 0.25
cols = [("Proposed: Constraint-Violation Rate", "Proposed"),
        ("Static Precedence: Constraint-Violation Rate", "Static precedence"),
        ("No Coordination: Constraint-Violation Rate", "No coordination")]
for k, (c, lab) in enumerate(cols):
    v = t1[c] * 100
    ax.bar(x + (k - 1) * w, v, w, label=lab)
    for i, val in enumerate(v):
        ax.text(x[i] + (k - 1) * w, val + 2, f"{val:.1f}", ha="center", fontsize=8)
ax.set_xticks(x)
ax.set_xticklabels(t1["Conflict Pair"])
ax.set_ylabel("Constraint-violation rate (%)")
ax.legend(frameon=False)
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "fig3_aggregate_comparison.png"), bbox_inches="tight")
plt.close()

# Fig 4: compromise stability
fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
axes[0].errorbar(t3["disagreement_intensity"], t3["compromise_hom_mean_db"],
                 yerr=t3["compromise_hom_std_db"], marker="o", capsize=4, lw=2)
axes[0].axhspan(2, 4, alpha=0.15, color="green", label="Recommended band (2 to 4 dB)")
axes[0].set_xlabel("Agent disagreement intensity")
axes[0].set_ylabel("Compromise HOM (dB)")
axes[0].legend(frameon=False, fontsize=8)
axes[1].errorbar(t3["disagreement_intensity"], t3["compromise_ttt_mean_ms"],
                 yerr=t3["compromise_ttt_std_ms"], marker="s", capsize=4, lw=2, color="tab:orange")
axes[1].axhspan(256, 640, alpha=0.15, color="green", label="Recommended band (256 to 640 ms)")
axes[1].set_xlabel("Agent disagreement intensity")
axes[1].set_ylabel("Compromise TTT (ms)")
axes[1].legend(frameon=False, fontsize=8)
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "fig4_compromise_stability.png"), bbox_inches="tight")
plt.close()
print("Figures written to", FIGS)
