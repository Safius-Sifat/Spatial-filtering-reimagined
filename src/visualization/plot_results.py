"""Visualisation utilities for producing report-ready figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import numpy as np


def plot_filter_comparison(image_paths: dict[str, Path],
                           titles: dict[str, str],
                           output_path: Path,
                           cmap: str = "gray") -> None:
    """Plot a 1-row montage of all filtered images for visual inspection."""
    n = len(image_paths)
    fig, axes = plt.subplots(1, n, figsize=(3 * n, 3.5))
    if n == 1:
        axes = [axes]
    for ax, (label, p) in zip(axes, image_paths.items()):
        if p is not None and Path(p).exists():
            img = plt.imread(p) if str(p).endswith(".png") else _imread(p)
            ax.imshow(img, cmap=cmap, vmin=0, vmax=1)
        ax.set_title(titles.get(label, label), fontsize=10)
        ax.axis("off")
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close()


def _imread(path):
    from PIL import Image
    return np.asarray(Image.open(path).convert("L")) / 255.0


def plot_metric_bar_table(csv_path: Path, output_path: Path,
                          group_col: str = "regime",
                          metric_col: str = "psnr",
                          filter_col: str = "filter") -> None:
    """Plot a grouped bar chart from the metrics CSV."""
    import pandas as pd
    df = pd.read_csv(csv_path)
    pivot = df.pivot_table(index=group_col, columns=filter_col,
                           values=metric_col, aggfunc="mean")
    pivot.plot.bar(figsize=(10, 5))
    plt.ylabel(metric_col.upper())
    plt.title(f"{metric_col.upper()} by {group_col} and filter")
    plt.xticks(rotation=0)
    plt.legend(loc="upper right", fontsize=8)
    plt.tight_layout()
    plt.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"  saved {output_path}")


# Report-ready bar charts: one per metric, averaged over all (image, regime)
_REPORT_FILTER_ORDER = [
    "Noisy_Baseline", "Box_3x3", "Median_3x3", "AVGF_Custom",
    "Sobel_Sharpen", "Unsharp_Mask", "NGKCS_Custom",
]
_REPORT_LABELS = {
    "Noisy_Baseline": "Noisy\n(baseline)",
    "Box_3x3": "Box\n3x3",
    "Median_3x3": "Median\n3x3",
    "AVGF_Custom": "AVGF\n(custom)",
    "Sobel_Sharpen": "Sobel\nsharpen",
    "Unsharp_Mask": "Unsharp\nmask",
    "NGKCS_Custom": "NGKCS\n(custom)",
}
_REPORT_COLORS = {
    "Noisy_Baseline": "#888888",
    "Box_3x3": "#4c72b0",
    "Median_3x3": "#dd8452",
    "AVGF_Custom": "#55a868",
    "Sobel_Sharpen": "#c44e52",
    "Unsharp_Mask": "#8172b3",
    "NGKCS_Custom": "#937860",
}


def plot_report_bars(csv_path: Path, output_dir: Path,
                     metrics=("psnr", "ssim", "fom")) -> None:
    """Produce per-metric bar charts averaged over all images and regimes."""
    import pandas as pd
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(csv_path)

    for metric in metrics:
        means = (df.groupby("filter")[metric]
                   .mean()
                   .reindex(_REPORT_FILTER_ORDER))
        fig, ax = plt.subplots(figsize=(7, 4.2))
        colors = [_REPORT_COLORS[f] for f in _REPORT_FILTER_ORDER]
        bars = ax.bar(_REPORT_FILTER_ORDER, means.values, color=colors,
                      edgecolor="black", linewidth=0.6)
        for b, v in zip(bars, means.values):
            ax.text(b.get_x() + b.get_width() / 2, v,
                     f"{v:.3f}" if metric != "psnr" else f"{v:.2f}",
                     ha="center", va="bottom", fontsize=9)
        ax.set_xticks(range(len(_REPORT_FILTER_ORDER)))
        ax.set_xticklabels([_REPORT_LABELS[f] for f in _REPORT_FILTER_ORDER],
                           fontsize=9)
        title_metric = {"psnr": "PSNR (dB)", "ssim": "SSIM", "fom": "Pratt FOM"}[metric]
        ax.set_ylabel(f"Mean {title_metric}")
        ax.set_title(f"Mean {title_metric} per filter (all images and noise regimes)")
        ax.set_ylim(0, max(means.values) * 1.15)
        ax.grid(axis="y", linestyle=":", alpha=0.5)
        plt.tight_layout()
        out = output_dir / f"fig_bar_{metric}.png"
        plt.savefig(out, dpi=120, bbox_inches="tight")
        plt.close()
        print(f"  saved {out}")


# ---------------------------------------------------------------------------
# Canny-edge overlay figure (one panel per filter, edges drawn in red)
# ---------------------------------------------------------------------------
from skimage import feature  # noqa: E402  -- local import keeps module-light


_CANNY_CASES = [
    # (image_key, regime, selected sample filename)
    ("bbbc005",    "heavy",     "bbbc005_sample_256.png"),
    ("fluo_gowt1", "realistic", "fluo_gowt1_sample_256.png"),
    ("bbbc034",    "realistic", "bbbc034_sample_256.png"),
]

# (label shown on the panel, key used in the PNG filename, descriptive colour)
_CANNY_PANELS = [
    ("Original",     None,    "#222222"),
    ("Noisy",        None,    "#444444"),
    ("Box 3x3",      "Box_3x3",        "#4c72b0"),
    ("Median 3x3",   "Median_3x3",     "#dd8452"),
    ("AVGF (custom)", "AVGF_Custom",   "#55a868"),
    ("Sobel sharpen", "Sobel_Sharpen", "#c44e52"),
    ("Unsharp mask",  "Unsharp_Mask",  "#8172b3"),
    ("NGKCS (custom)","NGKCS_Custom",  "#937860"),
]


def _read_gray(path: Path) -> np.ndarray:
    from PIL import Image
    return np.asarray(Image.open(path).convert("L"))


def plot_canny_overlays(project_root: Path | None = None,
                        figure_dir: Path | None = None) -> list[Path]:
    """For each representative (image, regime), draw a 1x8 grid with the Canny
    edge map of every filter output overlaid in red on the grayscale image.

    Produces:
        results/figures/canny_<image>_<regime>.png

    Returns the list of written paths.
    """
    import pandas as pd  # only needed to derive paths

    project_root = project_root or Path(__file__).resolve().parents[2]
    figure_dir   = figure_dir   or project_root / "results" / "figures"
    selected_dir = project_root / "data" / "selected"
    figure_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for image_key, regime, sample_name in _CANNY_CASES:
        sample_path = selected_dir / sample_name
        if not sample_path.exists():
            print(f"  [skip] missing sample: {sample_path}")
            continue

        fig, axes = plt.subplots(1, len(_CANNY_PANELS),
                                 figsize=(2.4 * len(_CANNY_PANELS), 2.8))
        for ax, (title, filter_key, _color) in zip(axes, _CANNY_PANELS):
            if filter_key is None and title == "Original":
                img = _read_gray(sample_path)
            elif filter_key is None and title == "Noisy":
                img = _read_gray(figure_dir / f"{image_key}_{regime}_noisy.png")
            else:
                img = _read_gray(figure_dir / f"{image_key}_{regime}_{filter_key}.png")

            ax.imshow(img, cmap="gray", vmin=0, vmax=255)
            # Canny edges on the same image (same call as src/metrics/epi_fom.py)
            edges = feature.canny(img.astype(np.float64), sigma=1.5)
            # Overlay edges in red, transparent so the image stays visible
            overlay = np.zeros((*img.shape, 4), dtype=np.float64)
            overlay[edges] = [1.0, 0.1, 0.1, 0.95]
            ax.imshow(overlay)
            ax.set_title(title, fontsize=10)
            ax.set_xticks([])
            ax.set_yticks([])

        fig.suptitle(
            f"Canny edges overlaid on every filter output ({image_key}, "
            f"{regime} noise regime)",
            fontsize=11,
        )
        plt.tight_layout(rect=(0, 0, 1, 0.95))
        out_path = figure_dir / f"canny_{image_key}_{regime}.png"
        plt.savefig(out_path, dpi=120, bbox_inches="tight")
        plt.close()
        written.append(out_path)
        print(f"  saved {out_path}")
    return written


if __name__ == "__main__":
    plot_canny_overlays()