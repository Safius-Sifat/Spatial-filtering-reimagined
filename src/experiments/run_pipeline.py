"""Main experiment pipeline.

Runs every filter on every (image, noise-regime) combination and emits:
  * PNG files under results/figures/ for visual inspection
  * CSV files under results/tables/ for downstream pandas analysis
  * Console output of summary statistics

This is the single entry point that produces all report-ready results.
"""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

import numpy as np
from PIL import Image
import tifffile

from src.degradation.poisson_gaussian import NOISE_REGIMES, degrade_regime
from src.filters.standard.box import box_filter
from src.filters.standard.median import median_filter
from src.filters.standard.sobel import sobel_sharpen
from src.filters.standard.laplacian_unsharp import unsharp_mask, laplacian_sharpen
from src.filters.custom.avgf import adaptive_variance_gaussian
from src.filters.custom.ngkcs import noise_gated_kirsch_compass
from src.metrics.psnr_ssim import mse, psnr, ssim
from src.metrics.epi_fom import edge_preservation_index, pratt_fom
from src.metrics.segmentation_iou import segmentation_iou


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SELECTED_DIR = PROJECT_ROOT / "data" / "selected"
FIG_DIR = PROJECT_ROOT / "results" / "figures"
TABLE_DIR = PROJECT_ROOT / "results" / "tables"
LOG_DIR = PROJECT_ROOT / "results" / "logs"
for d in (FIG_DIR, TABLE_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)


# Filter registry: name -> (callable, kwargs)
SMOOTHING_FILTERS = {
    "Box_3x3":        (box_filter,               {"kernel_size": 3}),
    "Median_3x3":     (median_filter,            {"kernel_size": 3}),
    "AVGF_Custom":    (adaptive_variance_gaussian, {"sigma_min": 0.5, "sigma_max": 2.0,
                                                    "T_low_mult": 1.0, "T_high_mult": 4.0,
                                                    "window_size": 5, "num_levels": 4}),
}

SHARPENING_FILTERS = {
    "Sobel_Sharpen":  (sobel_sharpen,            {"k": 0.3}),
    "Unsharp_Mask":   (unsharp_mask,             {"sigma": 1.0, "k": 1.5}),
    "NGKCS_Custom":   (noise_gated_kirsch_compass, {"k0": 0.7, "alpha": 1.0, "window_size": 5}),
}

ALL_FILTERS = {**SMOOTHING_FILTERS, **SHARPENING_FILTERS}


def load_image(path: Path) -> np.ndarray:
    """Load a grayscale image as float64 in [0, 255]."""
    if path.suffix.lower() in (".tif", ".tiff"):
        img = tifffile.imread(path)
    else:
        img = np.asarray(Image.open(path).convert("L"))
    return img.astype(np.float64)


def load_mask(path: Path | None) -> np.ndarray | None:
    if path is None or not path.exists():
        return None
    return (np.asarray(Image.open(path).convert("L")) > 127).astype(bool)


def evaluate(clean: np.ndarray, processed: np.ndarray, mask: np.ndarray | None) -> dict:
    out = {
        "mse": mse(clean, processed),
        "psnr": psnr(clean, processed),
        "ssim": ssim(clean, processed),
        "epi": edge_preservation_index(clean, processed),
        "fom": pratt_fom(clean, processed),
    }
    if mask is not None:
        out["iou"] = segmentation_iou(processed, mask)
    return out


def run(image_paths: dict[str, Path], mask_paths: dict[str, Path] | None = None,
        output_csv: Path | None = None,
        seed: int = 0) -> list[dict]:
    """Run all filters on all images at all noise regimes."""
    rng = np.random.default_rng(seed)
    rows = []

    for image_name, image_path in image_paths.items():
        if image_path is None or not image_path.exists():
            print(f"[skip] missing image: {image_name}")
            continue
        print(f"\n=== {image_name} ===")
        clean = load_image(image_path)
        mask = load_mask(mask_paths.get(image_name)) if mask_paths else None

        for regime_name in NOISE_REGIMES:
            print(f"  Regime: {regime_name}")
            noisy = degrade_regime(clean, regime=regime_name, rng=rng)

            # Persist the noisy image
            fig_path = FIG_DIR / f"{image_name}_{regime_name}_noisy.png"
            Image.fromarray(noisy.astype(np.uint8)).save(fig_path)

            # Evaluate on noisy (baseline)
            metrics_noisy = evaluate(clean, noisy, mask)
            row = {
                "image": image_name,
                "regime": regime_name,
                "filter": "Noisy_Baseline",
                **metrics_noisy,
                "time_s": 0.0,
            }
            rows.append(row)

            for filter_name, (fn, kwargs) in ALL_FILTERS.items():
                t0 = time.perf_counter()
                processed = fn(noisy, **kwargs)
                elapsed = time.perf_counter() - t0
                metrics = evaluate(clean, processed, mask)
                row = {
                    "image": image_name,
                    "regime": regime_name,
                    "filter": filter_name,
                    **metrics,
                    "time_s": elapsed,
                }
                rows.append(row)
                out_fig = FIG_DIR / f"{image_name}_{regime_name}_{filter_name}.png"
                Image.fromarray(np.clip(processed, 0, 255).astype(np.uint8)).save(out_fig)
                print(f"    {filter_name:20s} PSNR={metrics['psnr']:6.2f} SSIM={metrics['ssim']:.4f} "
                      f"EPI={metrics['epi']:.4f} FOM={metrics['fom']:.4f} "
                      f"time={elapsed*1000:.1f}ms")

    # Persist CSV
    if output_csv is None:
        output_csv = TABLE_DIR / "all_results.csv"
    fieldnames = ["image", "regime", "filter", "mse", "psnr", "ssim", "epi", "fom", "iou", "time_s"]
    with output_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f"\nResults written to {output_csv}")
    return rows


def main():
    parser = argparse.ArgumentParser(description="Run filter comparison experiments")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--csv", type=Path, default=TABLE_DIR / "all_results.csv")
    args = parser.parse_args()

    image_paths = {
        "bbbc005":     SELECTED_DIR / "bbbc005_sample_256.png",
        "fluo_gowt1":  SELECTED_DIR / "fluo_gowt1_sample_256.png",
        "bbbc034":     SELECTED_DIR / "bbbc034_sample_256.png",
    }
    mask_paths = {
        "bbbc005":     SELECTED_DIR / "bbbc005_mask_256.png",
        "fluo_gowt1":  None,
        "bbbc034":     None,
    }
    run(image_paths, mask_paths, output_csv=args.csv, seed=args.seed)


if __name__ == "__main__":
    main()