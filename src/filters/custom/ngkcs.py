"""Custom Sharpening Filter 2: Noise-Gated Kirsch Compass Sharpening (NGKCS).

This filter combines the 8-directional Kirsch compass with an SNR-aware
adaptive gain to enhance cell-membrane edges at any orientation while
suppressing noise amplification.

References
----------
Kirsch, R. (1971). "Computer Determination of the Constituent Structure
of Biological Images." Computers and Biomedical Research, 4(3), 248-256.
Immerkær, J. (1996). "Fast Noise Variance Estimation." CVGIP, 58(3), 300-302.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from src.filters.utils.convolution import convolve2d_zero
from src.filters.utils.kirsch_kernels import KIRSCH_KERNELS
from src.filters.utils.noise_estimation import immerkaer_noise_variance, local_variance


def noise_gated_kirsch_compass(image: NDArray[np.floating],
                               k0: float = 0.7,
                               alpha: float = 1.0,
                               window_size: int = 5) -> NDArray[np.floating]:
    """Apply the Noise-Gated Kirsch Compass Sharpening filter.

    Parameters
    ----------
    image : 2D float array.
    k0 : base gain for sharp regions (0..2 sensible).
    alpha : tuning constant for the SNR gate; higher = more aggressive
        down-weighting of noisy pixels.
    window_size : odd integer used to compute the local-variance SNR mask.

    Returns
    -------
    sharpened : 2D array, same shape and approximate dtype range as input.
    """
    img = image.astype(np.float64)

    # 1. Robust noise variance estimate (Immerkær)
    sigma_n_sq = immerkaer_noise_variance(img)
    sigma_n_sq = max(sigma_n_sq, 1e-8)

    # 2. Confidence mask rho in [0, 1]
    var_L = local_variance(img, window_size=window_size)
    rho = 1.0 / (1.0 + alpha * var_L / sigma_n_sq)

    # 3. Apply all 8 Kirsch kernels and take absolute responses
    G = np.zeros((8, img.shape[0], img.shape[1]), dtype=np.float64)
    for i, kernel in enumerate(KIRSCH_KERNELS):
        G[i] = np.abs(convolve2d_zero(img, kernel))

    G_max = G.max(axis=0)
    G_mean = G.mean(axis=0)

    # 4. Adaptive fusion: high-confidence -> max, low-confidence -> mean
    rho_3d = rho[None, :, :]
    G_fused = rho_3d * G_max + (1.0 - rho_3d) * G_mean

    # 5. Adaptive gain applied to the fused response, then add back
    gain_map = k0 * rho
    out = img + gain_map * G_fused[0] if G_fused.shape[0] == 1 else img + gain_map * G_fused

    if image.max() > 1.5:
        return np.clip(out, 0.0, 255.0)
    return np.clip(out, 0.0, 1.0)
