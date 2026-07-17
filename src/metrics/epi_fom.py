"""Edge Preservation Index (EPI) and Pratt's Figure of Merit (FOM).

EPI definition (Sattar et al. 1997):
    EPI = sum( (1 - |I_proc - I_ref| / 255) * mask_ref ) / sum(mask_ref)
where mask_ref is the binary edge map of the reference image.  EPI is in
[0, 1]; 1.0 means perfect edge preservation.

Pratt's Figure of Merit (Pratt 1978):
    FOM = (1 / max(N_I, N_A)) * sum_i (1 / (1 + alpha * d_i^2))
where N_I and N_A are the number of ideal and actual edge pixels, d_i is
the distance from actual edge pixel i to the nearest ideal edge pixel,
and alpha is a scaling constant (we use alpha = 1.0).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from skimage import feature


def _edge_map(image: NDArray, sigma: float = 1.5) -> NDArray[np.bool_]:
    return feature.canny(image.astype(np.float64), sigma=sigma)


def edge_preservation_index(reference: NDArray,
                            processed: NDArray,
                            data_range: float = 255.0) -> float:
    """EPI per Sattar et al. 1997."""
    ref = reference.astype(np.float64)
    prc = processed.astype(np.float64)
    mask_ref = _edge_map(ref)
    if mask_ref.sum() == 0:
        return 1.0
    diff = np.abs(prc - ref) / data_range
    weight = 1.0 - diff
    weight = np.clip(weight, 0.0, 1.0)
    epi = float((weight * mask_ref).sum() / mask_ref.sum())
    return epi


def pratt_fom(reference: NDArray,
              processed: NDArray,
              alpha: float = 1.0,
              sigma: float = 1.5) -> float:
    """Pratt's Figure of Merit comparing edge maps of two images."""
    ideal = _edge_map(reference, sigma=sigma)
    actual = _edge_map(processed, sigma=sigma)
    n_i = int(ideal.sum())
    n_a = int(actual.sum())
    if n_a == 0 or n_i == 0:
        return 0.0

    # Get coordinates of ideal and actual edge pixels
    iy, ix = np.where(ideal)
    ay, ax = np.where(actual)

    # For each actual pixel, find min Euclidean distance to any ideal pixel
    # (vectorised via broadcasting over a chunked subset to limit memory)
    # We use a simple chunked computation.
    distances = np.empty(n_a, dtype=np.float64)
    chunk = 256
    for start in range(0, n_a, chunk):
        end = min(start + chunk, n_a)
        dyx = ay[start:end][:, None] - iy[None, :]
        dxx = ax[start:end][:, None] - ix[None, :]
        d2 = dyx * dyx + dxx * dxx
        distances[start:end] = d2.min(axis=1)
    distances = np.sqrt(distances)
    score = (1.0 / (1.0 + alpha * distances ** 2)).sum()
    return float(score / max(n_i, n_a))