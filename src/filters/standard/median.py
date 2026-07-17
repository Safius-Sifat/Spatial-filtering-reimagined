"""Standard non-linear smoother: median filter."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def median_filter(image: NDArray[np.floating], kernel_size: int = 3) -> NDArray[np.floating]:
    """Apply a kxk median filter using sliding-window extraction via stride tricks.

    For each pixel, take the median of the kxk neighborhood.

    Parameters
    ----------
    image : 2D array.
    kernel_size : odd integer >= 3.
    """
    if kernel_size % 2 == 0:
        raise ValueError("kernel_size must be odd")
    img = image.astype(np.float64)
    H, W = img.shape
    radius = kernel_size // 2
    padded = np.pad(img, radius, mode="reflect")
    s_y, s_x = padded.strides
    windows = np.lib.stride_tricks.as_strided(
        padded,
        shape=(H, W, kernel_size, kernel_size),
        strides=(s_y, s_x, s_y, s_x),
        writeable=False,
    )
    # Flatten the kxk neighborhood for each pixel and take the median.
    flat = windows.reshape(H, W, -1)
    return np.median(flat, axis=-1)