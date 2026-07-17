"""PSNR, MSE, and SSIM metrics."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from skimage.metrics import structural_similarity as _ssim


def mse(reference: NDArray, processed: NDArray) -> float:
    """Mean squared error between reference and processed images."""
    ref = reference.astype(np.float64)
    prc = processed.astype(np.float64)
    return float(np.mean((ref - prc) ** 2))


def psnr(reference: NDArray, processed: NDArray, data_range: float = 255.0) -> float:
    """Peak signal-to-noise ratio in dB."""
    err = mse(reference, processed)
    if err <= 1e-12:
        return float("inf")
    return float(10.0 * np.log10((data_range * data_range) / err))


def ssim(reference: NDArray, processed: NDArray, data_range: float = 255.0) -> float:
    """Structural similarity index (Wang et al. 2004)."""
    ref = reference.astype(np.float64)
    prc = processed.astype(np.float64)
    return float(_ssim(ref, prc, data_range=data_range))