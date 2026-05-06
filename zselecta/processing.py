"""Low-level image processing: binarisation and region analysis.

Mirrors the MATLAB pipeline of rescale -> binarise -> regionprops,
using scikit-image equivalents.
"""

import math

import numpy as np
from numpy.typing import NDArray
from skimage.exposure import rescale_intensity
from skimage.measure import label, regionprops

MIN_AREA = 90_000
MAX_AREA = 400_000
MIN_CIRCULARITY = 0.4


def _circularity(area: float, perimeter: float) -> float:
    """4 * pi * area / perimeter^2, clamped to [0, 1]."""
    if perimeter == 0:
        return 0.0
    return min(4.0 * math.pi * area / (perimeter * perimeter), 1.0)


def binarise(image: NDArray, threshold: float = 0.5) -> NDArray[np.bool_]:
    """Rescale *image* to [0, 1], threshold, then invert (complement).

    Equivalent to MATLAB's ``imcomplement(imbinarize(rescale(image), t))``.
    """
    normalised = rescale_intensity(image.astype(np.float64), out_range=(0.0, 1.0))
    return normalised < threshold  # invert + threshold in one step


def largest_qualifying_area(binary: NDArray[np.bool_]) -> float:
    """Return the area of the largest region passing size and shape filters.

    Regions must satisfy:
        - ``MIN_AREA < area < MAX_AREA``
        - ``circularity >= MIN_CIRCULARITY``

    If no region qualifies, falls back to the single largest region
    regardless of shape.

    Returns:
        Area of the selected region, or 0.0 for an empty image.
    """
    labelled = label(binary)
    regions = regionprops(labelled)

    if not regions:
        return 0.0

    qualifying = [
        r
        for r in regions
        if MIN_AREA < r.area < MAX_AREA
        and _circularity(r.area, r.perimeter) >= MIN_CIRCULARITY
    ]

    if qualifying:
        return max(r.area for r in qualifying)

    return max(r.area for r in regions)
