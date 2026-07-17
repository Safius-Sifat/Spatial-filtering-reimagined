"""Noise variance estimation utilities.

Implements the Immerkær (1996) single-pass noise variance estimator that
suppresses image signal while preserving noise via a high-pass Laplacian
mask.  The estimator is used both inside AVGF and NGKCS for adaptive
parameter setting and SNR gating.

Reference
---------
Immerkær, J. (1996). "Fast Noise Variance Estimation."
CVGIP: Graphical Models and Image Processing, 58(3), 300-302.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

# High-pass Laplacian mask from Immerkær (1996).
_IMMERKAER_MASK = np.array(
    [[1, -2, 1], [-2, 4, -2], [1, -2, 1]], dtype=np.float64
)


def immerkaer_noise_variance(image: NDArray[np.floating]) -> float:
    """Estimate the noise variance of a (grayscale) image using Immerkær's method.

    The formula is:
        sigma_n^2 = (pi/2)^(1/1.2) * sum(|L*I|)^(1/1.2) /
                    (6 * (W-2) * (H-2))
    where L is the [[1,-2,1],[-2,4,-2],[1,-2,1]] Laplacian mask and the
    sum runs over the interior (W-2) * (H-2) pixels (where the mask
    fully overlaps the image).  Note (pi/2)^(1/1.2) ~ 1.5928; many
    references instead use pi/2 directly which is equivalent up to a
    multiplicative constant; we use the exponentiated form for fidelity
    to the original paper.
    """
    if image.ndim != 2:
        raise ValueError(f"expected 2D image, got {image.shape}")

    # Manual convolution (per project policy: no OpenCV filter2D here)
    kH, kW = _IMMERKAER_MASK.shape
    H, W = image.shape
    pad_y = kH // 2
    pad_x = kW // 2

    padded = np.zeros((H + 2 * pad_y, W + 2 * pad_x), dtype=np.float64)
    padded[pad_y : pad_y + H, pad_x : pad_x + W] = image.astype(np.float64)

    s_y, s_x = padded.strides
    windows = np.lib.stride_tricks.as_strided(
        padded,
        shape=(H - 2 * pad_y, W - 2 * pad_x, kH, kW),
        strides=(s_y, s_x, s_y, s_x),
        writeable=False,
    )
    response = np.einsum("ijkl,kl->ij", windows, _IMMERKAER_MASK)

    power = 1.0 / 1.2
    sigma_n_sq = ((np.pi / 2.0) ** power) * np.sum(np.abs(response) ** power) / (
        6.0 * response.shape[0] * response.shape[1]
    )
    return float(sigma_n_sq)


def local_variance(image: NDArray[np.floating], window_size: int = 5) -> NDArray[np.floating]:
    """Compute per-pixel local variance using a uniform window.

    Returns an array of the same shape as ``image``.  Uses a simple
    moving-average of the squared deviations from the local mean.
    """
    if window_size % 2 == 0:
        raise ValueError("window_size must be odd")
    img = image.astype(np.float64)
    radius = window_size // 2

    # Pad with reflection to avoid border artefacts
    padded = np.pad(img, radius, mode="reflect")
    H, W = img.shape
    s_y, s_x = padded.strides
    windows = np.lib.stride_tricks.as_strided(
        padded,
        shape=(H, W, window_size, window_size),
        strides=(s_y, s_x, s_y, s_x),
        writeable=False,
    )
    local_mean = windows.mean(axis=(2, 3))
    local_sq_mean = (windows ** 2).mean(axis=(2, 3))
    return local_sq_mean - local_mean ** 2