# ZSelecta

ZSelecta converts `.vsi` microscopy images to in-focus `.png` files. For z-stack images it automatically selects the sharpest slice; single-plane images are exported directly.

Currently supports Olympus cellSens `.vsi` files. Other formats readable by [Bio-Formats](https://www.openmicroscopy.org/bio-formats/) may work but have not been tested.

## Installation

### 1. Prerequisites

- **Python 3.10+**
- **Java 11+** runtime (JRE is sufficient). If you don't have one installed, [Adoptium Temurin](https://adoptium.net/) is a free, open-source option available for all platforms.

### 2. Download Bio-Formats JAR

ZSelecta requires the Bio-Formats all-in-one JAR (~51 MB). Download `bioformats_package.jar` from the [Bio-Formats downloads page](https://www.openmicroscopy.org/bio-formats/downloads/) and place it in `zselecta/jars/`:

```
zselecta/
  jars/
    bioformats_package.jar
```

> **Note:** Bio-Formats is licensed separately under [GPL v2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html) by the Open Microscopy Environment. It is not distributed with ZSelecta.

### 3. Install

```bash
pip install .
```

## Usage

Point ZSelecta at a directory containing `.vsi` files:

```bash
zselecta ./experiment --output ./pngs
```

To search subdirectories recursively:

```bash
zselecta ./experiment --output ./pngs --recursive
```

The output folder mirrors the input directory structure -- each `.vsi` file produces a `.png` with the same relative path.

## How It Works

1. Discovers `.vsi` files in the input directory.
2. For each file, queries the number of z-slices via Bio-Formats.
3. If multiple slices exist, selects the most in-focus plane:
   - Each slice is rescaled to [0, 1], binarised at a threshold of 0.5, and inverted.
   - Connected regions are extracted using `regionprops`.
   - Candidate regions are filtered by area (90,000--400,000 pixels) and circularity (>= 0.4).
   - The slice containing the largest qualifying region is chosen. If no region passes filtering, the slice with the overall largest region is used as a fallback.
4. Saves the selected plane as a 16-bit greyscale PNG at native resolution.

## Dependencies

- **Java 11+** runtime -- required by Bio-Formats
- [Bio-Formats](https://www.openmicroscopy.org/bio-formats/) (downloaded separately) -- reads `.vsi` and 150+ microscopy formats
- [JPype1](https://jpype.readthedocs.io/) -- Python-to-Java bridge
- [scikit-image](https://scikit-image.org/) -- region analysis and thresholding
- [Pillow](https://pillow.readthedocs.io/) -- PNG export
- [Typer](https://typer.tiangolo.com/) -- CLI framework

## Citation

If you use ZSelecta in your research, please cite:

```bibtex
@software{ZSelecta2026,
  title   = {ZSelecta},
  author  = {Sammy Shorthouse and Aya Elghajiji and Qiang Liu and James Armstrong},
  year    = {2026},
  url     = {https://github.com/SammySho/ZSelecta}
}
```

## License

ZSelecta is released under the MIT License. See [LICENSE](LICENSE) for details.

Bio-Formats is licensed separately under GPL v2 by the [Open Microscopy Environment](https://www.openmicroscopy.org/).
