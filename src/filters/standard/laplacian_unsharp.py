"""Standard 2nd-order sharpening: Laplacian + Unsharp Masking."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from src.filters.utils.convolution import (
    convolve2d_separable,
    convolve2d_zero,
    gaussian_kernel_1d,
)


# 4-neighbor Laplacian
LAPLACIAN_4NB = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], dtype=np.float64)


def laplacian_response(image: NDArray[np.floating]) -> NDArray[np.floating]:
    """Return the 4-neighbor Laplacian response."""
    img = image.astype(np.float64)
    return convolve2d_zero(img, LAPLACIAN_4NB)


def unsharp_mask(image: NDArray[np.floating],
                 sigma: float = 1.0,
                 k: float = 1.5) -> NDArray[np.floating]:
    """Standard unsharp-mask sharpening.

    sharpened = f + k * (f - f_blur)

    where f_blur is a Gaussian-blurred version of f (separable convolution
    implemented with two 1D passes for efficiency).
    """
    img = image.astype(np.float64)
    k1d = gaussian_kernel_1d(sigma)
    blurred = convolve2d_separable(img, k1d, k1d)
    mask = img - blurred
    out = img + k * mask
    if img.max() > 1.5:
        return np.clip(out, 0.0, 255.0)
    return np.clip(out, 0.0, 1.0)


def laplacian_sharpen(image: NDArray[np.floating], k: float = 1.0) -> NDArray[np.floating]:
    """Laplacian-based sharpening: f + k * Laplacian(f)."""
    img = image.astype(np.float64)
    lap = laplacian_response(img)
    out = img + k * lap
    if img.max() > 1.5:
        return np.clip(out, 0.0, 255.0)
    return np.clip(out, 0.0, 1.0)