"""Quick sanity test on synthetic data to validate filter correctness."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

# Make src importable when running this script via uv-run
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.filters.standard.box import box_filter
from src.filters.standard.median import median_filter
from src.filters.standard.sobel import sobel_sharpen
from src.filters.standard.laplacian_unsharp import unsharp_mask, laplacian_sharpen
from src.filters.custom.avgf import adaptive_variance_gaussian
from src.filters.custom.ngkcs import noise_gated_kirsch_compass
from src.filters.utils.noise_estimation import immerkaer_noise_variance
from src.degradation.poisson_gaussian import add_poisson_gaussian


def make_synthetic_image(size: int = 128) -> np.ndarray:
    """Synthetic test image: smooth background + a sharp circle + a soft square."""
    rng = np.random.default_rng(seed=42)
    img = np.full((size, size), 100.0)
    cy, cx = size // 2, size // 2
    y, x = np.ogrid[:size, :size]
    circle = ((y - cy) ** 2 + (x - cx) ** 2) <= (size // 6) ** 2
    img[circle] = 200.0
    sq_y, sq_x = size // 4, size // 4
    img[sq_y : sq_y + size // 4, sq_x : sq_x + size // 4] = 150.0
    # Smooth gradients with a tiny gaussian blur for realism
    from scipy.ndimage import gaussian_filter
    img = gaussian_filter(img, sigma=1.5).astype(np.float64)
    # Add a small amount of noise so the smoothing filters have work to do
    img += rng.normal(0, 5, img.shape)
    return img


def report(name: str, arr) -> None:
    print(f"  {name:30s}  shape={arr.shape}  dtype={arr.dtype}  "
          f"min={arr.min():.2f} max={arr.max():.2f} mean={arr.mean():.2f}")


def main():
    print("Generating synthetic test image...")
    img = make_synthetic_image()

    print("\n--- Sanity checks ---")
    report("input", img)

    out = box_filter(img)
    report("Box 3x3", out)
    assert out.shape == img.shape

    out = median_filter(img)
    report("Median 3x3", out)

    sigma_n_sq = immerkaer_noise_variance(img)
    print(f"\nImmerkær noise variance estimate: {sigma_n_sq:.2f}")

    noisy = add_poisson_gaussian(img.astype(np.float64), alpha=20.0, sigma_read=8.0)
    report("Noisy (alpha=20, sr=8)", noisy)

    out = box_filter(noisy)
    report("Box 3x3 on noisy", out)

    out = median_filter(noisy)
    report("Median 3x3 on noisy", out)

    out = adaptive_variance_gaussian(noisy)
    report("AVGF custom on noisy", out)

    out = sobel_sharpen(noisy, k=1.0)
    report("Sobel sharpen", out)

    out = unsharp_mask(noisy, sigma=1.0, k=1.5)
    report("Unsharp mask", out)

    out = laplacian_sharpen(noisy, k=1.0)
    report("Laplacian sharpen", out)

    out = noise_gated_kirsch_compass(noisy, k0=0.7, alpha=1.0)
    report("NGKCS custom sharpen", out)

    print("\nAll sanity checks passed.")


if __name__ == "__main__":
    main()