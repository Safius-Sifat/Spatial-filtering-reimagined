"""Manual 2D convolution utilities.

We implement convolution explicitly with NumPy. NO use of cv2.filter2D or
scipy.signal.convolve2d in the filter pipelines themselves (they are allowed
only as cross-validation references in tests). This is a deliberate design
choice to prove mathematical understanding per the project's PO5 criterion.

Conventions
-----------
- Zero-padding at image borders (standard image-processing convention).
- Output has the same spatial dimensions as the input.
- Kernel is provided in "image-order" orientation: K[0,0] is the top-left
  weight.  During convolution we flip the kernel to perform true
  mathematical convolution (not cross-correlation).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def convolve2d_zero(image: NDArray[np.floating], kernel: NDArray[np.floating]) -> NDArray[np.floating]:
    """2D convolution with zero-padding border handling.

    Parameters
    ----------
    image : 2D array of shape (H, W).
    kernel : 2D array of odd shape (kH, kW).  kH, kW >= 1.

    Returns
    -------
    output : 2D array of shape (H, W).
    """
    if image.ndim != 2:
        raise ValueError(f"expected 2D image, got shape {image.shape}")
    if kernel.ndim != 2 or kernel.shape[0] % 2 == 0 or kernel.shape[1] % 2 == 0:
        raise ValueError(f"kernel must be 2D with odd dims, got {kernel.shape}")

    # Flip the kernel for true convolution (vs. cross-correlation)
    k_flipped = kernel[::-1, ::-1]

    H, W = image.shape
    kH, kW = k_flipped.shape
    pad_y = kH // 2
    pad_x = kW // 2

    # Zero-pad the image
    padded = np.zeros((H + 2 * pad_y, W + 2 * pad_x), dtype=np.float64)
    padded[pad_y : pad_y + H, pad_x : pad_x + W] = image.astype(np.float64)

    output = np.zeros_like(image, dtype=np.float64)

    # Vectorized sliding-window multiplication using stride tricks
    # (avoids explicit Python loops over output pixels)
    s_y, s_x = padded.strides
    shape = (H, W, kH, kW)
    strides = (s_y, s_x, s_y, s_x)
    windows = np.lib.stride_tricks.as_strided(padded, shape=shape, strides=strides, writeable=False)

    # windows has shape (H, W, kH, kW); contract with k_flipped
    output = np.einsum("ijkl,kl->ij", windows, k_flipped)
    return output


def convolve2d_separable(image: NDArray[np.floating],
                         k1d_row: NDArray[np.floating],
                         k1d_col: NDArray[np.floating]) -> NDArray[np.floating]:
    """Apply a separable 2D filter as two 1D convolutions.

    Used for performance when the kernel is rank-1 (e.g. Gaussian).
    """
    if image.ndim != 2:
        raise ValueError(f"expected 2D image, got {image.shape}")
    k1d_row = np.asarray(k1d_row, dtype=np.float64).ravel()
    k1d_col = np.asarray(k1d_col, dtype=np.float64).ravel()
    if k1d_row.size % 2 == 0 or k1d_col.size % 2 == 0:
        raise ValueError("separable kernels must have odd length")

    # Convolve rows then columns.
    # For 1D convolution with zero-padding we can use np.convolve per row,
    # but that is slow in a Python loop; vectorize via padding.
    H, W = image.shape
    n_row = k1d_row.size
    n_col = k1d_col.size
    pad_x = n_row // 2
    pad_y = n_col // 2

    # Row-wise pass
    padded = np.zeros((H, W + 2 * pad_x), dtype=np.float64)
    padded[:, pad_x : pad_x + W] = image.astype(np.float64)
    out_rows = np.zeros((H, W), dtype=np.float64)
    for i in range(n_row):
        out_rows += k1d_row[i] * padded[:, i : i + W]

    # Column-wise pass
    padded2 = np.zeros((H + 2 * pad_y, W), dtype=np.float64)
    padded2[pad_y : pad_y + H, :] = out_rows
    out = np.zeros((H, W), dtype=np.float64)
    for i in range(n_col):
        out += k1d_col[i] * padded2[i : i + H, :]
    return out


def gaussian_kernel_1d(sigma: float, radius: int | None = None) -> NDArray[np.floating]:
    """Generate a 1D Gaussian kernel.

    Uses ceil(3*sigma) as the default radius.
    """
    if radius is None:
        radius = int(np.ceil(3.0 * sigma))
    x = np.arange(-radius, radius + 1, dtype=np.float64)
    k = np.exp(-(x * x) / (2.0 * sigma * sigma))
    k /= k.sum()
    return k


def gaussian_kernel_2d(sigma: float, radius: int | None = None) -> NDArray[np.floating]:
    """Generate a 2D Gaussian kernel (rank-1 product of two 1D Gaussians)."""
    k1d = gaussian_kernel_1d(sigma, radius)
    return np.outer(k1d, k1d)


def pad_to_shape(image: NDArray, target_h: int, target_w: int, mode: str = "reflect") -> NDArray:
    """Pad an image to a target size (used to avoid losing border cells)."""
    H, W = image.shape[:2]
    pad_bottom = max(0, target_h - H)
    pad_right = max(0, target_w - W)
    if pad_bottom == 0 and pad_right == 0:
        return image
    if image.ndim == 2:
        pad_widths = ((0, pad_bottom), (0, pad_right))
    else:
        pad_widths = ((0, pad_bottom), (0, pad_right), (0, 0))
    if mode == "zero":
        constant = 0.0
    else:
        constant = None
    return np.pad(image, pad_widths, mode=mode, constant_values=constant)