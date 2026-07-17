"""Parameter sweep for AVGF and NGKCS custom filters.

This is a sensitivity analysis script: vary one parameter at a time and
record SSIM (for AVGF) and EPI (for NGKCS) on a representative noisy
image.  Output a CSV and a line plot for the report.
"""

from __future__ import annotations

import csv
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.degradation.poisson_gaussian import degrade_regime
from src.filters.custom.avgf import adaptive_variance_gaussian
from src.filters.custom.ngkcs import noise_gated_kirsch_compass
from src.filters.standard.median import median_filter
from src.filters.standard.sobel import sobel_sharpen
from src.filters.standard.laplacian_unsharp import unsharp_mask
from src.metrics.psnr_ssim import ssim
from src.metrics.epi_fom import edge_preservation_index


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = PROJECT_ROOT / "results" / "tables"
FIG_DIR = PROJECT_ROOT / "results" / "figures"
LOG_DIR = PROJECT_ROOT / "results" / "logs"
for d in (TABLE_DIR, FIG_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)


def load_first_selected():
    from PIL import Image
    for name in ("bbbc005_sample.png", "fluo_gowt1_sample.png", "bbbc034_sample.png"):
        p = PROJECT_ROOT / "data" / "selected" / name
        if p.exists():
            return np.asarray(Image.open(p).convert("L")).astype(np.float64)
    raise FileNotFoundError("No selected images found. Run select_samples.py first.")


def sweep_avgf(clean):
    """Sweep AVGF parameters on the realistic noise regime."""
    noisy = degrade_regime(clean, regime="realistic")
    rows = []
    sigma_mins = [0.3, 0.5, 0.8, 1.0]
    sigma_maxs = [1.5, 2.0, 2.5, 3.0]
    high_mults = [2.0, 4.0, 6.0, 8.0]
    base = {"sigma_min": 0.5, "sigma_max": 2.0, "T_low_mult": 1.0, "T_high_mult": 4.0,
            "window_size": 5, "num_levels": 8}

    # 1. sigma_min sweep
    for v in sigma_mins:
        kw = dict(base); kw["sigma_min"] = v
        out = adaptive_variance_gaussian(noisy, **kw)
        rows.append({"filter": "AVGF", "param": "sigma_min", "value": v,
                     "ssim": ssim(clean, out)})
    # 2. sigma_max sweep
    for v in sigma_maxs:
        kw = dict(base); kw["sigma_max"] = v
        out = adaptive_variance_gaussian(noisy, **kw)
        rows.append({"filter": "AVGF", "param": "sigma_max", "value": v,
                     "ssim": ssim(clean, out)})
    # 3. T_high_mult sweep
    for v in high_mults:
        kw = dict(base); kw["T_high_mult"] = v
        out = adaptive_variance_gaussian(noisy, **kw)
        rows.append({"filter": "AVGF", "param": "T_high_mult", "value": v,
                     "ssim": ssim(clean, out)})
    return rows


def sweep_ngkcs(clean):
    """Sweep NGKCS parameters on the realistic noise regime."""
    noisy = degrade_regime(clean, regime="realistic")
    rows = []
    k0s = [0.3, 0.5, 0.7, 1.0, 1.5]
    alphas = [0.25, 0.5, 1.0, 2.0, 4.0]
    base = {"k0": 0.7, "alpha": 1.0, "window_size": 5}

    for v in k0s:
        kw = dict(base); kw["k0"] = v
        out = noise_gated_kirsch_compass(noisy, **kw)
        rows.append({"filter": "NGKCS", "param": "k0", "value": v,
                     "epi": edge_preservation_index(clean, out)})
    for v in alphas:
        kw = dict(base); kw["alpha"] = v
        out = noise_gated_kirsch_compass(noisy, **kw)
        rows.append({"filter": "NGKCS", "param": "alpha", "value": v,
                     "epi": edge_preservation_index(clean, out)})
    return rows


def write_and_plot(rows, csv_path: Path, fig_path: Path, metric: str):
    if not rows:
        return
    fieldnames = sorted({k for r in rows for k in r.keys()})
    with csv_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # Group by filter and param, plot metric vs value
    by_key = {}
    for r in rows:
        key = (r.get("filter"), r.get("param"))
        by_key.setdefault(key, []).append((r["value"], r[metric]))

    fig, ax = plt.subplots(figsize=(8, 4))
    for (flt, param), pts in by_key.items():
        pts.sort()
        vals, metrics = zip(*pts)
        ax.plot(vals, metrics, marker="o", label=f"{flt}/{param}")
    ax.set_xlabel("parameter value")
    ax.set_ylabel(metric.upper())
    ax.set_title(f"Parameter sensitivity ({metric})")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(fig_path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"  -> {csv_path}\n  -> {fig_path}")


def main():
    print("Loading representative image...")
    clean = load_first_selected()
    print(f"  shape={clean.shape}")

    print("\nAVGF sensitivity sweep...")
    avgf_rows = sweep_avgf(clean)
    write_and_plot(avgf_rows,
                   TABLE_DIR / "sweep_avgf.csv",
                   FIG_DIR / "sweep_avgf.png",
                   metric="ssim")

    print("\nNGKCS sensitivity sweep...")
    ngkcs_rows = sweep_ngkcs(clean)
    write_and_plot(ngkcs_rows,
                   TABLE_DIR / "sweep_ngkcs.csv",
                   FIG_DIR / "sweep_ngkcs.png",
                   metric="epi")


if __name__ == "__main__":
    main()