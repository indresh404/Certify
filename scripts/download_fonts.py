import urllib.request
from pathlib import Path


def download_fonts():
    fonts_dir = Path("assets/fonts")
    fonts_dir.mkdir(parents=True, exist_ok=True)

    base_url = "https://raw.githubusercontent.com/googlefonts/opensans/main/fonts/ttf/"
    fonts = [
        "OpenSans-Regular.ttf",
        "OpenSans-Bold.ttf",
        "OpenSans-Italic.ttf",
        "OpenSans-BoldItalic.ttf",
    ]

    for font in fonts:
        print(f"Downloading {font}...")
        try:
            urllib.request.urlretrieve(base_url + font, fonts_dir / font)
            print("Success")
        except Exception as e:  # noqa: BLE001
            print(f"Failed to download {font}: {e}")


if __name__ == "__main__":
    download_fonts()
