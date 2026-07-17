# Spatial Filters for Fluorescence Microscopy Enhancement

Custom-design spatial filtering pipeline (4 standard + 2 custom filters) for
noise-robust enhancement of fluorescence microscopy images. CSE 4106 project.

## Setup

```fish
# Install uv if you don't have it
brew install uv

# From project root
uv sync   # creates .venv and installs pinned deps
```

## Running

```fish
# 1. Download datasets (one-time)
bash scripts/download_datasets.sh        # all four
# or, if downloads were interrupted:
bash scripts/resume_downloads.sh         # only the large ones

# 2. Select one representative field-of-view per dataset
uv run python -m src.datasets.select_samples

# 3. Run the full pipeline (degrade → filter → metric → figure/table)
uv run python -m src.experiments.run_pipeline

# 4. Parameter sensitivity sweep for the custom filters
uv run python -m src.experiments.parameter_sweep

# 5. Quick sanity test on synthetic data
uv run python tests/test_filters.py
```

## Project Structure

```
src/
├── filters/
│   ├── standard/   # Box, Median, Sobel, Laplacian+Unsharp (4 standard)
│   ├── custom/     # AVGF, NGKCS (2 custom)
│   └── utils/      # Convolution, Immerkær noise estimator, Kirsch kernels
├── datasets/       # BBBC005 / Fluo-N2DH-GOWT1 / BBBC034 loaders
├── degradation/    # Poisson-Gaussian noise model (Lebrun-Morel 2015)
├── metrics/        # PSNR, SSIM, EPI, Pratt FOM, Segmentation IoU
├── experiments/    # run_pipeline, parameter_sweep
└── visualization/  # matplotlib-based plotting
data/               # raw, ground_truth, selected samples
results/            # figures, tables, logs
tests/              # sanity tests on synthetic data
docs/               # report drafts, presentation outline
```

## Filter Catalog

| # | Name | Type | Citation |
|---|---|---|---|
| 1 | Box 3×3 | Linear smoothing | Gonzalez & Woods 2018 |
| 2 | Median 3×3 | Non-linear smoothing | Huang 1979 |
| 3 | Sobel | 1st-order sharpening | Sobel 1970 |
| 4 | Laplacian + Unsharp | 2nd-order sharpening | Gonzalez & Woods 2018 |
| 5 | **AVGF** | **Custom smoothing** | Lee 1980 (adapted), Tomasi-Manduchi 1998 (compared), Immerkær 1996 (noise est.) |
| 6 | **NGKCS** | **Custom sharpening** | Kirsch 1971 (compass), Immerkær 1996 (noise gate) |

## Datasets

- **BBBC005** — Synthetic HCS fluorescent cell populations + ground-truth masks
  https://bbbc.broadinstitute.org/BBBC005
- **Fluo-N2DH-GOWT1** — GFP-GOWT1 mouse stem cells (Cell Tracking Challenge)
  https://celltrackingchallenge.net/2d-datasets/
- **BBBC034** — hiPSC colony volumes
  https://bbbc.broadinstitute.org/BBBC034

All datasets are CC0 / freely downloadable; no login required.

## Outputs

After running, see:
- `results/tables/all_results.csv` — per-image × per-regime × per-filter metrics
- `results/figures/` — visual comparisons of all filter outputs
- `results/tables/sweep_*.csv` — parameter sensitivity tables
- `results/figures/sweep_*.png` — sensitivity plots