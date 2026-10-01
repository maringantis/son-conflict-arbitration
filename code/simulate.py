"""
Multi-Agent SON Conflict Arbitration: Calibrated Monte Carlo Simulation
(NextGCom 2026 SUBMISSION VERSION, Aug 2026)

NOTE: This is the original submission-version simulation (3,600 trials,
seed 42, single coverage floor of 0.95). It does NOT reproduce the
camera-ready numbers shown in the presentation deck (5 seeds, 18,000 test
trials, calibration/test split, best-fixed-rule baseline, compromise
revalidation, abstention, floors of 0.55 / 0.90).

Illustrative (non-production, non-proprietary) simulation for
constraint-based arbitration between independently acting SON agents
(MLB, MRO, CCO, ESM) in AI-RAN deployments.

Citation anchors for parameter calibration:
  [C1] 3GPP TS 28.313: Mobility Robustness Optimization (MRO).
  [C2] 3GPP TS 28.628: SON Policy NRM.
  [C3] Handover Margin (HOM) recommended band 2-4 dB, deployable 0-10 dB.
  [C4] 3GPP Time-to-Trigger (TTT) enumerated set; recommended 256-640 ms.
  [C5] MDPI Applied Sciences 13(5):3367 (2023), handover management survey
       documenting the MRO / load-balancing conflict on HOM and TTT.
  [C6] US Patent 10,531,429 B2: CCO / ESM coordination conflict.
  [C7] Klessig et al. (TU Dresden) and related ESM studies: roughly 30-35%
       energy saving per sleeping cell.
  [C8] 3GPP TS 32.551: Energy Saving Management concepts and requirements.
  [C9] Emergency-call coverage continuity used only as the CONCEPT of a
       non-negotiable floor. The numeric floor here is illustrative.

No production, carrier-specific, or proprietary data is used.
"""

import os
import numpy as np
import pandas as pd

RNG_SEED = 42
rng = np.random.default_rng(RNG_SEED)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DATA = os.path.join(ROOT, "data")
OUT_TABLES = os.path.join(ROOT, "tables")
os.makedirs(OUT_DATA, exist_ok=True)
os.makedirs(OUT_TABLES, exist_ok=True)

# 1. Calibrated parameter space
HOM_RANGE_DB = (0.0, 10.0)
HOM_RECOMMENDED_DB = (2.0, 4.0)
TTT_ENUM_MS = np.array(
    [0, 40, 64, 80, 100, 128, 160, 256, 320, 480, 512, 640, 1024, 1280, 2560, 5120]
)
TTT_RECOMMENDED_MS = (256, 640)
E911_COVERAGE_FLOOR = 0.95          # illustrative floor
ESM_ENERGY_SAVINGS_MEAN = 0.325
ESM_ENERGY_SAVINGS_STD = 0.03


# 2. Scenario generators
def generate_mlb_mro_scenario(disagreement_intensity):
    """MLB pushes HOM/TTT down (shed load); MRO pushes them up (robustness)."""
    base_hom = rng.uniform(*HOM_RECOMMENDED_DB)
    band = TTT_ENUM_MS[(TTT_ENUM_MS >= TTT_RECOMMENDED_MS[0]) &
                       (TTT_ENUM_MS <= TTT_RECOMMENDED_MS[1])]
    base_ttt = rng.choice(band)

    spread_hom = disagreement_intensity * rng.uniform(2.0, 6.0)
    spread_ttt_idx = int(disagreement_intensity * rng.integers(2, 6))

    mlb_hom = float(np.clip(base_hom - spread_hom / 2, *HOM_RANGE_DB))
    mro_hom = float(np.clip(base_hom + spread_hom / 2, *HOM_RANGE_DB))

    ttt_idx = int(np.where(TTT_ENUM_MS == base_ttt)[0][0])
    mlb_ttt = int(TTT_ENUM_MS[max(0, ttt_idx - spread_ttt_idx)])
    mro_ttt = int(TTT_ENUM_MS[min(len(TTT_ENUM_MS) - 1, ttt_idx + spread_ttt_idx)])

    cell_load = rng.uniform(0.2, 0.95)
    ue_velocity_kmh = rng.uniform(3, 120)

    def predicted_coverage(hom, ttt):
        rlf_risk = np.clip((10 - hom) / 10, 0, 1) * np.clip((5120 - ttt) / 5120, 0, 1)
        mobility_factor = np.clip(ue_velocity_kmh / 120, 0, 1)
        penalty = 0.12 * rlf_risk * mobility_factor
        return float(np.clip(1.0 - penalty, 0, 1))

    return {
        "pair": "MLB_MRO",
        "disagreement_intensity": disagreement_intensity,
        "cell_load": cell_load,
        "ue_velocity_kmh": ue_velocity_kmh,
        "agentA": "MLB", "agentA_hom_db": mlb_hom, "agentA_ttt_ms": mlb_ttt,
        "agentB": "MRO", "agentB_hom_db": mro_hom, "agentB_ttt_ms": mro_ttt,
        "agentA_pred_coverage": predicted_coverage(mlb_hom, mlb_ttt),
        "agentB_pred_coverage": predicted_coverage(mro_hom, mro_ttt),
    }


def generate_cco_esm_scenario(disagreement_intensity):
    """ESM wants a low-load cell asleep; CCO needs it active for coverage."""
    candidate_load = rng.uniform(0.02, 0.35)
    neighbor_overlap = rng.uniform(0.3, 0.95)
    esm_energy_saving = float(np.clip(
        rng.normal(ESM_ENERGY_SAVINGS_MEAN, ESM_ENERGY_SAVINGS_STD), 0.1, 0.5))
    coverage_if_slept = float(np.clip(
        1.0 - neighbor_overlap * (0.5 + 0.5 * disagreement_intensity), 0, 1))
    coverage_if_active = float(np.clip(0.97 + rng.normal(0, 0.01), 0, 1))

    return {
        "pair": "CCO_ESM",
        "disagreement_intensity": disagreement_intensity,
        "candidate_cell_load": candidate_load,
        "neighbor_overlap": neighbor_overlap,
        "agentA": "CCO", "agentA_action": "keep_active",
        "agentA_pred_coverage": coverage_if_active,
        "agentB": "ESM", "agentB_action": "sleep",
        "agentB_pred_coverage": coverage_if_slept,
        "esm_energy_saving": esm_energy_saving,
    }


# 3. Arbitration mechanisms
def arbitrate_constraint_based(s, coverage_floor=E911_COVERAGE_FLOOR):
    """Stage 1: drop candidates below the floor. Stage 2: compromise or select."""
    a_ok = s["agentA_pred_coverage"] >= coverage_floor
    b_ok = s["agentB_pred_coverage"] >= coverage_floor

    if not a_ok and not b_ok:
        return {"outcome": "no_valid_action", "constraint_violated": True,
                "resolved": False, "chosen": None}
    if a_ok and not b_ok:
        return {"outcome": f"select_{s['agentA']}", "constraint_violated": False,
                "resolved": True, "chosen": s["agentA"]}
    if b_ok and not a_ok:
        return {"outcome": f"select_{s['agentB']}", "constraint_violated": False,
                "resolved": True, "chosen": s["agentB"]}

    if s["pair"] == "MLB_MRO":
        wA, wB = s["agentA_pred_coverage"], s["agentB_pred_coverage"]
        total = wA + wB
        hom = (s["agentA_hom_db"] * wA + s["agentB_hom_db"] * wB) / total
        iA = int(np.where(TTT_ENUM_MS == s["agentA_ttt_ms"])[0][0])
        iB = int(np.where(TTT_ENUM_MS == s["agentB_ttt_ms"])[0][0])
        ttt = int(TTT_ENUM_MS[int(round((iA * wA + iB * wB) / total))])
        return {"outcome": "compromise", "constraint_violated": False, "resolved": True,
                "chosen": "compromise", "compromise_hom_db": hom, "compromise_ttt_ms": ttt}

    chosen = s["agentA"] if s["agentA_pred_coverage"] >= s["agentB_pred_coverage"] else s["agentB"]
    return {"outcome": f"compromise_select_{chosen}", "constraint_violated": False,
            "resolved": True, "chosen": chosen}


def arbitrate_static_precedence(s):
    """Baseline: MRO always wins MLB/MRO; ESM always wins CCO/ESM."""
    chosen = "MRO" if s["pair"] == "MLB_MRO" else "ESM"
    cov = s["agentB_pred_coverage"]
    return {"outcome": f"precedence_{chosen}", "constraint_violated": cov < E911_COVERAGE_FLOOR,
            "resolved": True, "chosen": chosen}


def arbitrate_no_coordination(s):
    """Baseline: both actions applied; violation if either breaches the floor."""
    violated = (s["agentA_pred_coverage"] < E911_COVERAGE_FLOOR) or \
               (s["agentB_pred_coverage"] < E911_COVERAGE_FLOOR)
    return {"outcome": "both_applied_uncoordinated", "constraint_violated": violated,
            "resolved": True, "chosen": "both"}


# 4. Monte Carlo experiment
def run_monte_carlo(n_per_intensity=300, intensities=None):
    if intensities is None:
        intensities = np.round(np.linspace(0.0, 1.0, 6), 2)
    rows = []
    for gen, name in [(generate_mlb_mro_scenario, "MLB_MRO"),
                      (generate_cco_esm_scenario, "CCO_ESM")]:
        for intensity in intensities:
            for trial in range(n_per_intensity):
                s = gen(intensity)
                p = arbitrate_constraint_based(s)
                st = arbitrate_static_precedence(s)
                nc = arbitrate_no_coordination(s)
                rows.append({
                    "pair": name, "disagreement_intensity": intensity, "trial": trial,
                    "proposed_resolved": p["resolved"],
                    "proposed_constraint_violated": p["constraint_violated"],
                    "static_constraint_violated": st["constraint_violated"],
                    "none_constraint_violated": nc["constraint_violated"],
                    "proposed_outcome": p["outcome"],
                    "compromise_hom_db": p.get("compromise_hom_db", np.nan),
                    "compromise_ttt_ms": p.get("compromise_ttt_ms", np.nan),
                })
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT_DATA, "raw_trials.csv"), index=False)
    return df


def summarize(df):
    t1 = pd.DataFrame([{
        "Conflict Pair": pair.replace("_", "<->"),
        "Proposed: Resolution Rate": sub["proposed_resolved"].mean(),
        "Proposed: Constraint-Violation Rate": sub["proposed_constraint_violated"].mean(),
        "Static Precedence: Constraint-Violation Rate": sub["static_constraint_violated"].mean(),
        "No Coordination: Constraint-Violation Rate": sub["none_constraint_violated"].mean(),
    } for pair, sub in df.groupby("pair", sort=False)])
    t1.to_csv(os.path.join(OUT_TABLES, "table1_resolution_summary.csv"), index=False)

    t2 = (df.groupby(["pair", "disagreement_intensity"])
            .agg(proposed_resolved_rate=("proposed_resolved", "mean"),
                 proposed_violation_rate=("proposed_constraint_violated", "mean"),
                 static_violation_rate=("static_constraint_violated", "mean"),
                 none_violation_rate=("none_constraint_violated", "mean"))
            .reset_index())
    t2.to_csv(os.path.join(OUT_TABLES, "table2_by_intensity.csv"), index=False)

    m = df[(df["pair"] == "MLB_MRO") & (df["proposed_outcome"] == "compromise")]
    t3 = (m.groupby("disagreement_intensity")
           .agg(n_compromise_events=("compromise_hom_db", "size"),
                compromise_hom_mean_db=("compromise_hom_db", "mean"),
                compromise_hom_std_db=("compromise_hom_db", "std"),
                compromise_ttt_mean_ms=("compromise_ttt_ms", "mean"),
                compromise_ttt_std_ms=("compromise_ttt_ms", "std"))
           .reset_index())
    t3.to_csv(os.path.join(OUT_TABLES, "table3_compromise_stability.csv"), index=False)
    return t1, t2, t3


if __name__ == "__main__":
    df = run_monte_carlo(300)
    t1, t2, t3 = summarize(df)
    print(t1.to_string(index=False))
    print(f"\nTotal trials: {len(df)}")
