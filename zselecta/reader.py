"""Image reading for microscopy formats via Bio-Formats.

Uses JPype to call the Bio-Formats Java library directly from a bundled
JAR, avoiding fragile Maven dependency resolution at runtime.

Requires a Java 11+ runtime. The module searches for one in this order:
    1. JAVA_HOME environment variable
    2. cjdk cache (populated by bioio-bioformats / bffile on first install)
    3. System PATH
"""

import os
import sys
from functools import cache
from pathlib import Path

import jpype
import jpype.imports
import numpy as np
from numpy.typing import NDArray

_JAR_PATH = Path(__file__).parent / "jars" / "bioformats_package.jar"

_CJDK_CACHE = Path.home() / "AppData" / "Local" / "cjdk" / "cache" / "v0" / "jdks"
if sys.platform != "win32":
    _CJDK_CACHE = Path.home() / ".cache" / "cjdk" / "v0" / "jdks"


def _find_java_home() -> str | None:
    """Locate a Java 11+ installation, preferring cjdk cache if available."""
    if java_home := os.environ.get("JAVA_HOME"):
        return java_home

    if _CJDK_CACHE.exists():
        for vendor_dir in _CJDK_CACHE.iterdir():
            for jdk_dir in vendor_dir.iterdir():
                if (jdk_dir / "bin" / "java.exe").exists() or (
                    jdk_dir / "bin" / "java"
                ).exists():
                    return str(jdk_dir)

    return None


@cache
def _start_jvm() -> None:
    """Start the JVM with the Bio-Formats JAR on the classpath."""
    if jpype.isJVMStarted():
        return

    java_home = _find_java_home()
    if java_home:
        os.environ["JAVA_HOME"] = java_home

    jvm_path = jpype.getDefaultJVMPath()
    jpype.startJVM(
        jvm_path,
        "-Dlogback.configurationFile=off",
        "-Dorg.slf4j.simpleLogger.defaultLogLevel=off",
        classpath=[str(_JAR_PATH)],
    )

    # Silence Bio-Formats' verbose Java logging.
    from ch.qos.logback.classic import Level  # type: ignore[import]
    from org.slf4j import LoggerFactory  # type: ignore[import]

    LoggerFactory.getLogger("ROOT").setLevel(Level.WARN)


def _create_reader(path: Path):
    """Create and initialise a Bio-Formats ImageReader for *path*."""
    _start_jvm()
    from loci.formats import ImageReader  # type: ignore[import]

    reader = ImageReader()
    reader.setId(str(path.resolve()))
    reader.setSeries(0)
    return reader


def get_num_slices(path: Path) -> int:
    """Return the number of z-slices in the first series of *path*."""
    reader = _create_reader(path)
    try:
        return reader.getSizeZ()
    finally:
        reader.close()


def load_slice(path: Path, z_index: int) -> NDArray[np.uint16]:
    """Load a single z-slice (2-D array) from *path*.

    Args:
        path: Path to the microscopy image file.
        z_index: Zero-based z-slice index.

    Returns:
        2-D numpy array (Y, X) of pixel intensities.
    """
    reader = _create_reader(path)
    try:
        width = reader.getSizeX()
        height = reader.getSizeY()
        plane_index = reader.getIndex(z_index, 0, 0)

        raw_bytes = reader.openBytes(plane_index)
        pixel_type = reader.getPixelType()

        from loci.formats import FormatTools  # type: ignore[import]

        is_little_endian = reader.isLittleEndian()
        bpp = FormatTools.getBytesPerPixel(pixel_type)
        is_float = FormatTools.isFloatingPoint(pixel_type)
        is_signed = FormatTools.isSigned(pixel_type)

        dtype = _pixel_type_to_dtype(bpp, is_float, is_signed, is_little_endian)
        flat = np.frombuffer(bytes(raw_bytes), dtype=dtype)
        return flat.reshape((height, width))
    finally:
        reader.close()


def load_flat(path: Path) -> NDArray[np.uint16]:
    """Load a single-plane image (no z-stack) as a 2-D array."""
    return load_slice(path, z_index=0)


def _pixel_type_to_dtype(
    bpp: int, is_float: bool, is_signed: bool, little_endian: bool
) -> np.dtype:
    """Map Bio-Formats pixel metadata to a numpy dtype."""
    endian = "<" if little_endian else ">"
    if is_float:
        return np.dtype(f"{endian}f{bpp}")
    prefix = "i" if is_signed else "u"
    return np.dtype(f"{endian}{prefix}{bpp}")
