from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw

from image_to_ascii_workbench.cli import main


def test_cli_smoke():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        image_path = root / "input.png"
        txt_path = root / "out.txt"
        png_path = root / "out.png"
        image = Image.new("RGB", (64, 64), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((8, 8, 56, 56), outline="black", width=4)
        draw.line((8, 56, 56, 8), fill="black", width=3)
        image.save(image_path)
        assert main(
            [
                str(image_path),
                "--width",
                "48",
                "--sampling",
                "super2x",
                "--palette",
                "classic",
                "--dither",
                "atkinson",
                "--edge-mode",
                "sobel-hybrid",
                "--save-txt",
                str(txt_path),
                "--save-png",
                str(png_path),
            ]
        ) == 0
        assert txt_path.read_text(encoding="utf-8").strip()
        assert png_path.exists()
