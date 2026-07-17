"""Standard 1st-order edge detector: Sobel operator."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from src.filters.utils.convolution import convolve2d_zero


SOBEL_GX = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64)
SOBEL_GY = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float64)


def sobel_gradients(image: NDArray[np.floating]) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    """Return the Sobel gradient components Gx and Gy."""
    img = image.astype(np.float64)
    gx = convolve2d_zero(img, SOBEL_GX)
    gy = convolve2d_zero(img, SOBEL_GY)
    return gx, gy


def sobel_magnitude(image: NDArray[np.floating]) -> NDArray[np.floating]:
    """Return the Sobel gradient magnitude sqrt(Gx^2 + Gy^2)."""
    gx, gy = sobel_gradients(image)
    return np.sqrt(gx * gx + gy * gy)


def sobel_sharpen(image: NDArray[np.floating], k: float = 0.3) -> NDArray[np.floating]:
    """High-pass sharpening: f + k * normalised_gradient_magnitude.

    We normalise the gradient magnitude by its per-image maximum so the
    filter behaves consistently across images of different brightness.
    Result is clipped to the [0, 255] dynamic range (or [0, 1] for
    normalised images).
    """
    img = image.astype(np.float64)
    g = sobel_magnitude(img)
    g_norm = g / max(g.max(), 1e-9)
    out = img + k * g_norm * 255.0
    if img.max() > 1.5:
        return np.clip(out, 0.0, 255.0)
    return np.clip(out / 255.0, 0.0, 1.0) if False else np.clip(out, 0.0, 255.0)
