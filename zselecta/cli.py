"""CLI entry point for ZSelecta.

Usage::

    zselecta ./experiment --output ./pngs
    zselecta ./experiment --output ./pngs --recursive
"""

from pathlib import Path
from typing import Annotated

import typer
from PIL import Image

from zselecta.focus import select_focused_image

app = typer.Typer(help="Convert .vsi microscopy images to in-focus PNGs.")

VSI_GLOB = "*.vsi"


def _discover_vsi(input_dir: Path, recursive: bool) -> list[Path]:
    """Return all .vsi files under *input_dir*."""
    pattern = f"**/{VSI_GLOB}" if recursive else VSI_GLOB
    return sorted(input_dir.glob(pattern))


def _output_path_for(vsi_path: Path, input_dir: Path, output_dir: Path) -> Path:
    """Mirror *vsi_path*'s relative location under *output_dir* as a .png."""
    relative = vsi_path.relative_to(input_dir).with_suffix(".png")
    return output_dir / relative


def _process_file(vsi_path: Path, png_path: Path) -> None:
    """Select the best-focus plane and save as PNG."""
    image_data = select_focused_image(vsi_path)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(image_data).save(png_path)


@app.command()
def convert(
    input_dir: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            help="Directory containing .vsi files.",
        ),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output directory for PNGs."),
    ] = Path("output"),
    recursive: Annotated[
        bool,
        typer.Option("--recursive", "-r", help="Search subdirectories for .vsi files."),
    ] = False,
) -> None:
    """Convert .vsi microscopy images to in-focus PNGs.

    Scans INPUT_DIR for .vsi files, selects the sharpest z-slice from
    each, and writes the result as a PNG. The input folder structure is
    mirrored in the output directory.
    """
    vsi_files = _discover_vsi(input_dir, recursive)

    if not vsi_files:
        typer.echo(f"No .vsi files found in {input_dir}")
        raise typer.Exit(code=1)

    typer.echo(f"Found {len(vsi_files)} .vsi file(s)")

    for i, vsi_path in enumerate(vsi_files, start=1):
        png_path = _output_path_for(vsi_path, input_dir, output)
        typer.echo(f"[{i}/{len(vsi_files)}] {vsi_path.name} -> {png_path}")

        try:
            _process_file(vsi_path, png_path)
        except Exception as exc:
            typer.echo(f"  ERROR: {exc}", err=True)

    typer.echo("Done.")
