"""Collect a small Google Images pilot and label the kept photos."""

import argparse
import base64
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
COUNTRIES_PATH = ROOT / "data" / "processed" / "countries.csv"
IMAGES_PATH = ROOT / "data" / "processed" / "images_pilot.csv"
EXCLUDED_PATH = ROOT / "data" / "processed" / "excluded_pilot.csv"
PILOT_ISO_CODES = ("MWI", "KEN", "BRA", "JPN")
KEEP_PER_COUNTRY = 10
DROP_RULES = (
    (re.compile(r"\bflags?\b", re.I), "flag"),
    (re.compile(r"coat of arms", re.I), "coat of arms"),
    (re.compile(r"\bemblem\b", re.I), "emblem"),
    (re.compile(r"\bmaps?\b", re.I), "map"),
    (re.compile(r"\blocator\b", re.I), "locator"),
    (re.compile(r"wikipedia|britannica|encyclopedia", re.I), "encyclopedia"),
    (re.compile(r"\.svg\b", re.I), "svg"),
)


def load_env(path):
    if not path.exists():
        raise SystemExit(f"Missing {path.name}. Add SERPAPI_API_KEY and GOOGLE_API_KEY.")
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    missing = [name for name in ("SERPAPI_API_KEY", "GOOGLE_API_KEY") if not values.get(name)]
    if missing:
        raise SystemExit(f"Missing {', '.join(missing)} in {path.name}.")
    return values


def rejection_reason(result):
    text = " ".join(
        str(result.get(field) or "") for field in ("title", "source", "link", "original")
    )
    for pattern, reason in DROP_RULES:
        if pattern.search(text):
            return reason
    if not result.get("original"):
        return "missing image url"
    return None


def search_images(query, api_key):
    response = requests.get(
        "https://serpapi.com/search.json",
        params={"engine": "google_images", "q": query, "api_key": api_key, "hl": "en"},
        timeout=45,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("error"):
        raise SystemExit(f"SerpApi error for {query}: {payload['error']}")
    return payload.get("images_results") or []


def vision_labels(image_url, api_key):
    labels = request_labels({"source": {"imageUri": image_url}}, api_key)
    if labels is not None:
        return labels
    downloaded = requests.get(
        image_url,
        timeout=25,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    if not downloaded.ok or not downloaded.content:
        return None
    encoded = base64.b64encode(downloaded.content).decode("ascii")
    return request_labels({"content": encoded}, api_key)


def request_labels(image, api_key):
    response = requests.post(
        "https://vision.googleapis.com/v1/images:annotate",
        params={"key": api_key},
        json={
            "requests": [
                {
                    "image": image,
                    "features": [{"type": "LABEL_DETECTION", "maxResults": 3}],
                }
            ]
        },
        timeout=45,
    )
    if not response.ok:
        message = ""
        try:
            message = response.json().get("error", {}).get("message", "")
        except ValueError:
            message = ""
        if response.status_code in (401, 403) or "API key" in message:
            raise SystemExit(f"Vision API rejected the request: {message or response.status_code}")
        return None
    payload = response.json()
    responses = payload.get("responses") or []
    if not responses or responses[0].get("error"):
        return None
    annotations = responses[0].get("labelAnnotations") or []
    names = [item.get("description", "") for item in annotations[:3]]
    return (names + ["", "", ""])[:3]


def collect_country(country, api_keys):
    kept = []
    excluded = []
    results = search_images(country["country_name"], api_keys["SERPAPI_API_KEY"])
    for index, result in enumerate(results, start=1):
        raw_rank = result.get("position") or index
        reason = rejection_reason(result)
        record = {
            "country_name": country["country_name"],
            "iso_code": country["iso_code"],
            "raw_search_rank": raw_rank,
            "image_url": result.get("original") or "",
            "title": result.get("title") or "",
            "source": result.get("source") or "",
            "reason": reason or "",
        }
        if reason:
            excluded.append(record)
            continue
        labels = vision_labels(record["image_url"], api_keys["GOOGLE_API_KEY"])
        time.sleep(0.2)
        if labels is None:
            record["reason"] = "vision failed"
            excluded.append(record)
            continue
        kept.append(
            {
                **country,
                "image_url": record["image_url"],
                "search_rank": len(kept) + 1,
                "raw_search_rank": raw_rank,
                "dominant_label_1": labels[0],
                "dominant_label_2": labels[1],
                "dominant_label_3": labels[2],
            }
        )
        if len(kept) == KEEP_PER_COUNTRY:
            break
    return kept, excluded


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    if IMAGES_PATH.exists() and not args.refresh:
        print(f"{IMAGES_PATH.name} already exists. Pass --refresh to collect again.")
        return

    api_keys = load_env(ENV_PATH)
    countries = pd.read_csv(COUNTRIES_PATH)
    pilot = countries.loc[countries["iso_code"].isin(PILOT_ISO_CODES)].copy()
    missing = set(PILOT_ISO_CODES) - set(pilot["iso_code"])
    if missing:
        raise SystemExit(f"Pilot countries missing from the country table: {sorted(missing)}")
    pilot["pilot_order"] = pilot["iso_code"].map({code: index for index, code in enumerate(PILOT_ISO_CODES)})
    pilot = pilot.sort_values("pilot_order")

    kept_rows = []
    excluded_rows = []
    for country in pilot.drop(columns=["pilot_order"]).to_dict("records"):
        print(f"Collecting {country['country_name']} ({country['iso_code']})")
        kept, excluded = collect_country(country, api_keys)
        print(f"  kept {len(kept)}; excluded {len(excluded)}")
        if len(kept) < KEEP_PER_COUNTRY:
            print("  fewer than 10 photos remained after filtering")
        kept_rows.extend(kept)
        excluded_rows.extend(excluded)

    IMAGES_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(kept_rows).to_csv(IMAGES_PATH, index=False)
    pd.DataFrame(excluded_rows).to_csv(EXCLUDED_PATH, index=False)
    print(f"Wrote {len(kept_rows)} image rows to {IMAGES_PATH}")
    print(f"Wrote {len(excluded_rows)} excluded rows to {EXCLUDED_PATH}")


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as exc:
        print(f"Request failed: {exc.__class__.__name__}", file=sys.stderr)
        raise SystemExit(1) from exc
