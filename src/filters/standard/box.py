"""Standard linear smoother: 3x3 Box (uniform) filter."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from src.filters.utils.convolution import convolve2d_zero


def box_filter(image: NDArray[np.floating], kernel_size: int = 3) -> NDArray[np.floating]:
    """Apply a 3x3 (or kxk) uniform-mean box filter via manual convolution.

    Parameters
    ----------
    image : 2D array.
    kernel_size : odd integer >= 3.

    Returns
    -------
    filtered : same shape as input.
    """
    if kernel_size % 2 == 0:
        raise ValueError("kernel_size must be odd")
    k = np.ones((kernel_size, kernel_size), dtype=np.float64) / (kernel_size * kernel_size)
    return convolve2d_zero(image.astype(np.float64), k)