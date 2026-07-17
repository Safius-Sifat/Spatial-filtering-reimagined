"""Realistic Poisson-Gaussian noise degradation for fluorescence microscopy.

The model follows Lebrun & Morel (2015): the clean image is first corrupted
by Poisson (photon-shot) noise whose mean scales with the local intensity,
then Gaussian (read) noise is added.

Reference
---------
Lebrun, M. & Morel, J.-M. (2015). "A Poisson-Gaussian Noise Model for Image
Denoising." J. Math. Imaging Vis., 53(3), 263-283.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def add_poisson_gaussian(image: NDArray[np.floating],
                         alpha: float = 50.0,
                         sigma_read: float = 5.0,
                         rng: np.random.Generator | None = None) -> NDArray[np.floating]:
    """Add Poisson-Gaussian noise to a (float) image.

    Parameters
    ----------
    image : 2D float array with values in [0, 255] (8-bit dynamic range).
    alpha : Poisson scaling factor.  Larger alpha = less Poisson noise.
    sigma_read : Standard deviation of additive Gaussian read noise.

    Returns
    -------
    noisy : float array with same dtype as input.
    """
    if rng is None:
        rng = np.random.default_rng(seed=0)

    img = image.astype(np.float64)
    img = np.clip(img, 0.0, 255.0)

    # Poisson noise: lambda = img / alpha, then rescale back.
    # For very low alpha the Poisson mean is tiny and rounding dominates.
    lam = img / alpha
    noisy_poisson = rng.poisson(lam).astype(np.float64) * alpha
    noisy = noisy_poisson + rng.normal(0.0, sigma_read, size=img.shape)
    noisy = np.clip(noisy, 0.0, 255.0)
    return noisy.astype(image.dtype)


NOISE_REGIMES = {
    "mild":      {"alpha": 50.0, "sigma_read": 5.0},
    "heavy":     {"alpha": 10.0, "sigma_read": 15.0},
    "realistic": {"alpha": 20.0, "sigma_read": 8.0},
}


def degrade_regime(image: NDArray[np.floating],
                   regime: str,
                   rng: np.random.Generator | None = None) -> NDArray[np.floating]:
    """Apply one of the three predefined noise regimes."""
    if regime not in NOISE_REGIMES:
        raise ValueError(f"unknown regime '{regime}'. Choose from {list(NOISE_REGIMES)}")
    params = NOISE_REGIMES[regime]
    return add_poisson_gaussian(image, alpha=params["alpha"], sigma_read=params["sigma_read"], rng=rng)