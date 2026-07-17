"""Cell segmentation IoU as a downstream performance metric.

We use scikit-image's thresholding combined with morphological cleanup
to produce a binary mask from the filtered image, then compare against
the ground-truth mask.  IoU = |P intersect G| / |P union G|.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from skimage import filters, morphology
from skimage.morphology import remove_small_objects, opening, disk


def segment_otsu(image: NDArray[np.floating]) -> NDArray[np.bool_]:
    """Simple Otsu-thresholded segmentation with morphological cleanup."""
    thresh = filters.threshold_otsu(image.astype(np.float64))
    binary = image.astype(np.float64) > thresh
    binary = opening(binary, disk(2))
    binary = remove_small_objects(binary, min_size=64)
    return binary


def iou(predicted: NDArray[np.bool_], ground_truth: NDArray[np.bool_]) -> float:
    """Intersection over Union for two binary masks."""
    inter = np.logical_and(predicted, ground_truth).sum()
    union = np.logical_or(predicted, ground_truth).sum()
    if union == 0:
        return 0.0
    return float(inter) / float(union)


def segmentation_iou(image: NDArray[np.floating],
                     ground_truth: NDArray[np.bool_]) -> float:
    """Run Otsu segmentation on `image` and compute IoU vs `ground_truth`."""
    pred = segment_otsu(image)
    return iou(pred, ground_truth.astype(bool))