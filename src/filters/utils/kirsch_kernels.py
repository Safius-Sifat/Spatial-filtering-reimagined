"""Kirsch compass kernel construction.

Reference
---------
Kirsch, R. (1971). "Computer Determination of the Constituent Structure
of Biological Images." Computers and Biomedical Research, 4(3), 248-256.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

KIRSCH_KERNELS: list[NDArray[np.floating]] = [
    np.array([[-3, -3, 5], [-3, 0, 5], [-3, -3, 5]], dtype=np.float64),  # 0 deg (E)
    np.array([[-3, 5, 5], [-3, 0, 5], [-3, -3, -3]], dtype=np.float64),  # 45 deg (NE)
    np.array([[5, 5, 5], [-3, 0, -3], [-3, -3, -3]], dtype=np.float64),  # 90 deg (N)
    np.array([[5, 5, -3], [5, 0, -3], [-3, -3, -3]], dtype=np.float64),  # 135 deg (NW)
    np.array([[5, -3, -3], [5, 0, -3], [5, -3, -3]], dtype=np.float64),  # 180 deg (W)
    np.array([[-3, -3, -3], [5, 0, -3], [5, 5, -3]], dtype=np.float64),  # 225 deg (SW)
    np.array([[-3, -3, -3], [-3, 0, -3], [5, 5, 5]], dtype=np.float64),  # 270 deg (S)
    np.array([[-3, -3, -3], [-3, 0, 5], [-3, 5, 5]], dtype=np.float64),  # 315 deg (SE)
]

DIRECTION_ANGLES_DEG: list[int] = [0, 45, 90, 135, 180, 225, 270, 315]