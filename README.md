# SON Conflict Arbitration: Simulation Code

Companion code for the NextGCom 2026 paper **"Multi-Agent Conflict
Arbitration for Autonomous SON Functions in AI-RAN."**

## Version notice (please read)

This repository contains the **submission-version** simulation
(August 2026): 3,600 trials, fixed seed 42, and a single illustrative
coverage floor of 0.95.

The camera-ready paper uses a revised evaluation (5 seeds, 18,000 test
trials, calibration/test split, best-fixed-rule baseline, compromise
revalidation, abstention, and floors of 0.55 and 0.90). **This code does
not reproduce the camera-ready numbers.** The revised simulation will be
added to this repository as a tagged release.

## What it does

A calibrated Monte Carlo study of conflicts between independently acting
Self-Organizing Network (SON) functions:

- **MLB vs MRO**: Mobility Load Balancing and Mobility Robustness
  Optimization both adjust Handover Margin (HOM) and Time To Trigger (TTT).
- **CCO vs ESM**: Coverage and Capacity Optimization wants a cell kept on;
  Energy Saving Management wants it asleep.

Three strategies are compared: the proposed two-stage constraint-based
arbiter, static precedence, and no coordination.

All data is synthetic. Parameter ranges are calibrated to public sources
(3GPP TS 28.313, TS 28.628, TS 32.551, a 2023 MDPI handover survey,
US Patent 10,531,429, and published Energy Saving Management studies).
No production, carrier, or proprietary data is used.

## Repository layout

    code/simulate.py        Monte Carlo engine (writes data/ and tables/)
    code/make_figures.py    Figure generation (writes figures/)
    data/raw_trials.csv     Trial-level output (3,600 rows)
    tables/                 Summary tables
    figures/                Four figures

## Reproduce

    pip install -r requirements.txt
    python3 code/simulate.py
    python3 code/make_figures.py

Expected summary (seed 42):

| Pair      | Proposed resolved | Proposed violation | Static precedence violation | No coordination violation |
|-----------|-------------------|--------------------|-----------------------------|---------------------------|
| MLB vs MRO | 80.3%            | 19.7%              | 19.7%                       | 44.7%                     |
| CCO vs ESM | 97.7%            | 2.3%               | 100.0%                      | 100.0%                    |

## Citation

See `CITATION.cff`, or cite the NextGCom 2026 paper.

## License

MIT. See `LICENSE`.
