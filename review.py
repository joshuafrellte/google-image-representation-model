"""Build a local contact sheet for the image pilot. No API calls."""

import html
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
PILOT_PATH = ROOT / "data" / "processed" / "pilot" / "images_pilot.csv"
REVIEW_DIR = ROOT / "data" / "processed" / "review"
IMAGE_DIR = REVIEW_DIR / "images"
SHEET_PATH = REVIEW_DIR / "index.html"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def image_extension(content, content_type):
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if content.startswith(b"GIF87a") or content.startswith(b"GIF89a"):
        return ".gif"
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return ".webp"
    kind = (content_type or "").split(";")[0].strip().lower()
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }.get(kind)


def download_image(url):
    response = requests.get(url, timeout=25, headers=HEADERS)
    if not response.ok or not response.content:
        return None
    extension = image_extension(response.content, response.headers.get("Content-Type"))
    if extension is None:
        return None
    return response.content, extension


def label_text(row):
    labels = []
    for column in ("dominant_label_1", "dominant_label_2", "dominant_label_3"):
        value = row[column]
        if pd.isna(value):
            continue
        text = str(value).strip()
        if text:
            labels.append(text)
    return ", ".join(labels)


def card_html(row, local_name):
    labels = label_text(row)
    url = html.escape(str(row["image_url"]), quote=True)
    if local_name:
        picture = f'<img src="images/{html.escape(local_name, quote=True)}" alt="">'
    else:
        picture = '<p class="missing">Local copy failed. Open the original link.</p>'
    return f"""
    <article>
      {picture}
      <h2>{html.escape(str(row["country_name"]))} <span>rank {int(row["search_rank"])}</span></h2>
      <p>{html.escape(labels)}</p>
      <p><a href="{url}">Original image</a></p>
    </article>
    """


def main():
    pilot = pd.read_csv(PILOT_PATH)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    cards = []
    saved = 0
    for row in pilot.to_dict("records"):
        stem = f"{row['iso_code']}_{int(row['search_rank']):02d}"
        existing = sorted(IMAGE_DIR.glob(stem + ".*"))
        local_name = None
        if existing:
            local_name = existing[0].name
            saved += 1
        else:
            try:
                downloaded = download_image(row["image_url"])
            except requests.RequestException:
                downloaded = None
            if downloaded:
                content, extension = downloaded
                local_name = stem + extension
                (IMAGE_DIR / local_name).write_bytes(content)
                saved += 1
                print(f"Saved {local_name}")
            else:
                print(f"Failed {stem}")
        cards.append(card_html(row, local_name))

    document = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>GIRD image pilot</title>
  <style>
    body {{ font-family: sans-serif; margin: 24px; background: #f6f6f6; }}
    h1 {{ font-size: 1.4rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }}
    article {{ background: white; padding: 12px; }}
    img {{ width: 100%; height: 200px; object-fit: cover; background: #ddd; }}
    h2 {{ font-size: 1rem; margin: 10px 0 4px; }}
    h2 span, p {{ color: #444; font-weight: normal; }}
    .missing {{ height: 200px; display: grid; place-items: center; background: #eee; text-align: center; }}
    a {{ color: #163; }}
  </style>
</head>
<body>
  <h1>Image pilot, {len(pilot)} photos</h1>
  <div class="grid">
    {"".join(cards)}
  </div>
</body>
</html>
"""
    SHEET_PATH.write_text(document, encoding="utf-8")
    print(f"Wrote {saved} images and {SHEET_PATH}")


if __name__ == "__main__":
    main()
