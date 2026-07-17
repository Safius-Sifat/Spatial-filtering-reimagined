"""Custom Smoothing Filter 1: Adaptive Variance-Gaussian Filter (AVGF).

This filter adaptively chooses the Gaussian sigma for each pixel based on
the local image variance, so that flat cytoplasm regions receive strong
smoothing while cell-membrane pixels (high local variance) are preserved.

Theoretical basis
-----------------
Direct extension of Lee (1980) reformulated as a kernel-width adaptation
rather than a per-neighbor pixel weight.  See the project plan for the
novelty claim vs. Tomasi-Manduchi (1998) bilateral filter.

References
----------
Lee, J.-S. (1980). "Digital Image Enhancement and Noise Filtering by Use
of Local Statistics." IEEE TPAMI, PAMI-2(2), 165-168.
Tomasi, C. & Manduchi, R. (1998). "Bilateral Filtering for Gray and Color
Images." ICCV, 839-846.
Immerkær, J. (1996). "Fast Noise Variance Estimation." CVGIP, 58(3), 300-302.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from src.filters.utils.convolution import gaussian_kernel_1d
from src.filters.utils.noise_estimation import immerkaer_noise_variance


def _gaussian_2d(sigma: float) -> NDArray[np.floating]:
    k1d = gaussian_kernel_1d(sigma)
    return np.outer(k1d, k1d)


def _convolve_separable(image: NDArray[np.floating], sigma: float) -> NDArray[np.floating]:
    """Apply a Gaussian convolution via two 1D passes (manual)."""
    k1d = gaussian_kernel_1d(sigma)
    H, W = image.shape
    n = k1d.size
    pad = n // 2
    # Row-wise pass
    padded = np.zeros((H, W + 2 * pad), dtype=np.float64)
    padded[:, pad : pad + W] = image
    out = np.zeros_like(image)
    for i in range(n):
        out += k1d[i] * padded[:, i : i + W]
    # Column-wise pass
    padded2 = np.zeros((H + 2 * pad, W), dtype=np.float64)
    padded2[pad : pad + H, :] = out
    out2 = np.zeros_like(image)
    for i in range(n):
        out2 += k1d[i] * padded2[i : i + H, :]
    return out2


def _local_variance(image: NDArray[np.floating], window: int) -> NDArray[np.floating]:
    """Sliding-window local variance (uniform window)."""
    if window % 2 == 0:
        raise ValueError("window must be odd")
    radius = window // 2
    padded = np.pad(image, radius, mode="reflect")
    s_y, s_x = padded.strides
    windows = np.lib.stride_tricks.as_strided(
        padded,
        shape=(image.shape[0], image.shape[1], window, window),
        strides=(s_y, s_x, s_y, s_x),
        writeable=False,
    )
    mu = windows.mean(axis=(2, 3))
    mu2 = (windows ** 2).mean(axis=(2, 3))
    return mu2 - mu ** 2


def adaptive_variance_gaussian(image: NDArray[np.floating],
                                sigma_min: float = 0.5,
                                sigma_max: float = 2.0,
                                T_low_mult: float = 1.0,
                                T_high_mult: float = 4.0,
                                window_size: int = 5,
                                num_levels: int = 8) -> NDArray[np.floating]:
    """Apply the Adaptive Variance-Gaussian Filter.

    Parameters
    ----------
    image : 2D array, dtype float.
    sigma_min, sigma_max : bounds for the adaptive kernel std.
    T_low_mult, T_high_mult : thresholds expressed as multiples of the
        Immerkær noise variance estimate.
    window_size : odd integer for the local-statistics window.
    num_levels : number of discrete sigma levels to pre-compute kernels for.
        Each output pixel uses the kernel whose sigma corresponds to its
        local variance.

    Returns
    -------
    filtered : 2D array, same shape and approximate dtype range as input.
    """
    img = image.astype(np.float64)
    H, W = img.shape

    # 1. Estimate the global noise variance (Immerkær)
    sigma_n_sq = immerkaer_noise_variance(img)
    T_low = T_low_mult * sigma_n_sq
    T_high = T_high_mult * sigma_n_sq

    # 2. Compute per-pixel local variance
    var_L = _local_variance(img, window_size)

    # 3. Quantise sigma to `num_levels` discrete levels between min and max
    sigma_levels = np.linspace(sigma_min, sigma_max, num_levels)

    # Map each pixel's variance to an integer sigma index 0..(num_levels-1)
    # If var_L < T_low -> sigma_max (index num_levels-1, strongest smoothing)
    # If var_L > T_high -> sigma_min (index 0, minimal smoothing)
    interp = (T_high - var_L) / max(T_high - T_low, 1e-12)  # in [0, 1] roughly
    interp = np.clip(interp, 0.0, 1.0)
    sigma_idx = (interp * (num_levels - 1) + 0.5).astype(np.int64)
    sigma_idx = np.clip(sigma_idx, 0, num_levels - 1)

    # 4. For each sigma level, smooth the pixels that map to it
    #    Approximation: smooth the whole image N times with each sigma and
    #    blend the results using a per-pixel weight (one-hot mask per level).
    #    More efficient: precompute N smoothings and assemble via np.stack.
    smoothed_stack = np.zeros((num_levels, H, W), dtype=np.float64)
    for i, sigma in enumerate(sigma_levels):
        smoothed_stack[i] = _convolve_separable(img, float(sigma))

    # 5. Build per-pixel selection: scatter index into a 3D mask
    #    Build the mask flattened as (num_levels, H*W), then reshape.
    flat_mask = np.zeros((num_levels, H * W), dtype=np.float64)
    flat_idx = sigma_idx.ravel()
    pixel_pos = np.arange(H * W)
    flat_mask[flat_idx, pixel_pos] = 1.0
    mask = flat_mask.reshape(num_levels, H, W)

    output = (mask * smoothed_stack).sum(axis=0)

    # Clip to original dynamic range
    if image.max() > 1.5:
        return np.clip(output, 0.0, 255.0)
    return np.clip(output, 0.0, 1.0)