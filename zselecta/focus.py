"""Z-stack focus selection.

Iterates through z-slices and picks the one whose largest qualifying
region has the greatest area -- a proxy for being most in-focus.
"""

from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from zselecta.processing import binarise, largest_qualifying_area
from zselecta.reader import get_num_slices, load_flat, load_slice


def _sharpness(image: NDArray) -> float:
    """Score a single z-slice by its largest qualifying region area."""
    binary = binarise(image)
    return largest_qualifying_area(binary)


def select_focused_image(path: Path) -> NDArray[np.uint16]:
    """Return the most in-focus 2-D image from *path*.

    If the file contains a single plane, returns it directly.
    For z-stacks, scores every slice and returns the sharpest.
    """
    num_slices = get_num_slices(path)

    if num_slices <= 1:
        return load_flat(path)

    best_index = 0
    best_score = -1.0

    for z in range(num_slices):
        score = _sharpness(load_slice(path, z))
        if score > best_score:
            best_score = score
            best_index = z

    return load_slice(path, best_index)
