"""Search Google Images and keep the photos that pass one filter.

The pilot command searches Malawi, Kenya, Brazil, and Japan. The same
filter is what the full run and the refill use. Photographs of places,
people, wildlife, and landscape stay. A flag stays when another label
describes a person, crowd, protest, or place.
"""

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
IMAGES_PATH = ROOT / "data" / "processed" / "pilot" / "images_pilot.csv"
EXCLUDED_PATH = ROOT / "data" / "processed" / "pilot" / "excluded_pilot.csv"
PILOT_ISO_CODES = ("MWI", "KEN", "BRA", "JPN")
KEEP_PER_COUNTRY = 10
DROP_RULES = (
    (re.compile(r"\bflags?\b", re.I), "flag"),
    (re.compile(r"coat of arms", re.I), "coat of arms"),
    (re.compile(r"\bemblem\b", re.I), "emblem"),
    (re.compile(r"(^|[^A-Za-z0-9])maps?([^A-Za-z0-9]|$)", re.I), "map"),
    (re.compile(r"\blocator\b", re.I), "locator"),
    (re.compile(r"wikipedia|britannica|encyclopedia", re.I), "encyclopedia"),
    (re.compile(r"\.svg\b", re.I), "svg"),
)
URL_MAP = re.compile(r"bbcmp_|country_profile|harita", re.I)
QUERY_OVERRIDES = {
    "JOR": "Jordan country",
    "TUR": "Türkiye",
}
LABEL_COLUMNS = ("dominant_label_1", "dominant_label_2", "dominant_label_3")
DROP_LABELS = {
    "map",
    "atlas",
    "advertising",
    "graphic design",
    "hoodie",
    "film",
    "fictional character",
    "fungus",
    "macro photography",
    "guinea pig",
}
FLAG_EXACT = {"flag", "flags", "flag day"}
MAX_SEARCH_PAGES = 2
GUINEA_BIRD = re.compile(r"guinea[-_ ]?(?:fowl|hens?|chicks?)|bissau", re.I)
WRONG_CONGO = re.compile(r"democratic-republic|(?<![A-Za-z])drc(?![A-Za-z])", re.I)
NATGEO_ID = re.compile(r"natgeofe\.com/k/([0-9a-f-]{36})", re.I)
NAMED_URLS = {
    ("NER", "https://bizimages.withfloats.com/tile/06723fcc0a004870a362c80670a6ebe8.jpg"): "named: niger collision",
    ("NER", "https://static.wixstatic.com/media/b021fd_9a28aa46f0da476a8d72ac6832a14a64~mv2.png/v1/fill/w_568,h_568,al_c,lg_1,q_85,enc_avif,quality_auto/b021fd_9a28aa46f0da476a8d72ac6832a14a64~mv2.png"): "named: niger collision",
    ("NER", "https://i.ytimg.com/vi/bCfO_pbRqzo/maxresdefault.jpg"): "named: niger collision",
    ("NER", "https://www.bustmold.com/wp-content/uploads/2018/02/aspergillus-niger-conidiophore.png"): "named: niger collision",
    ("NER", "https://www.bustmold.com/wp-content/uploads/2019/02/Aspergillus-Niger.jpg"): "named: niger collision",
    ("NER", "https://etamold.com/wp-content/uploads/2025/05/photo_conclusion_AspergillusNiger.webp"): "named: niger collision",
    ("GIN", "https://b2573706.assetcdn.net/2.0/2573706/wp-content/uploads/2023/05/AdobeStock_169414963-1024x807.jpeg?lossy=1&strip=1&webp=1"): "named: guinea collision",
    ("GIN", "https://i0.wp.com/gaildamerow.com/wp-content/uploads/2025/04/Guineas-French01.jpg?resize=508%2C330&ssl=1"): "named: guinea collision",
    ("GIN", "https://media.cntraveler.com/photos/5ad8d432a4034c61525d8a35/16:9/w_4496,h_2529,c_limit/TR050418_Papua10.jpg"): "named: guinea collision",
    ("GIN", "http://media.cntraveler.com/photos/5ad8d432a4034c61525d8a35/master/pass/TR050418_Papua10.jpg"): "named: guinea collision",
    ("GIN", "https://chickenscratchny.com/wp-content/uploads/2022/11/Guinea-Hens-Blog26-scaled.png"): "named: guinea collision",
    ("GIN", "https://b2573706.assetcdn.net/2.0/2573706/wp-content/uploads/2021/11/Guinea-scaled.jpg?lossy=1&strip=1&webp=1"): "named: guinea collision",
    ("GIN", "https://ogden_images.s3.amazonaws.com/www.motherearthnews.com/images/2022/06/07084123/pexels-jennifer-myers-4052987-768x654.jpg"): "named: guinea collision",
    ("GIN", "https://www.dartagnan.com/dw/image/v2/BJQL_PRD/on/demandware.static/-/Sites-dartagnan-Library/default/dw68924066/images/content/what-is-a-guinea-hen.jpg?sw=1200&strip=false"): "named: guinea collision",
    ("GIN", "https://a-z-animals.com/media/Guinea-fowl-5.jpg"): "named: guinea collision",
    ("GIN", "https://nationalzoo.si.edu/sites/default/files/animals/20200114-roshanpatel09.jpg"): "named: guinea collision",
    ("GBR", "https://i.guim.co.uk/img/media/07a5b78ae6d4fb08139f1d960b0ab60b8abfbbfe/61_0_1000_600/master/1000.jpg?width=465&dpr=1&s=none&crop=none"): "named: film still",
    ("GBR", "https://statcdn.fandango.com/MPX/image/NBCU_Fandango/622/643/AUnitedKingdom_Trailer.jpg"): "named: film still",
    ("GBR", "https://m.media-amazon.com/images/M/MV5BMTg5NDAxOTUxNV5BMl5BanBnXkFtZTgwMzUxMDQzMTI@._V1_.jpg"): "named: film still",
    ("GBR", "https://m.media-amazon.com/images/S/pv-target-images/503fb76311e5b6ea7f0197cfe6d337c1e482575b0169d718cc4f56ddc3525ade.jpg"): "named: film still",
    ("GBR", "https://i.guim.co.uk/img/media/31840cc0a6a78a0b4f946080563caf549c47b7aa/0_0_4912_3274/master/4912.jpg?width=700&quality=85&auto=format&fit=max&s=78d2e44ec0e05cc45fafbcf5b7063dee"): "named: film still",
    ("GBR", "https://ichef.bbci.co.uk/images/ic/1920x1080/p087ftdb.jpg"): "named: film still",
    ("GBR", "https://people.com/thmb/S9ZPKb1lyoZ9bSSv7-Y8WUMUPvQ=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc():focal(665x0:667x2)/khama-williams-2000-854f539b7b4d42ac8990f59a90e391b7.jpg"): "named: film still",
    ("GBR", "https://m.media-amazon.com/images/M/MV5BMjI1MTkzNzg0NF5BMl5BanBnXkFtZTgwNTQxNDE0MDI@._V1_.jpg"): "named: film still",
    ("BRN", "https://i.ytimg.com/vi/zl7GpUiAWHI/maxresdefault.jpg"): "named: youtube composite",
    ("UGA", "https://africandefenders.org/wp-content/uploads/2022/04/uganda-1758988_1280.png"): "named: clip art",
    ("COG", "https://www.ambadrcusa.org/wp-content/uploads/2024/01/democratic-republic-of-the-congo.jpg"): "duplicate of Democratic Republic of the Congo",
    ("COG", "https://www.fao.org/media/images/newsroomlibraries/stories-images/drc-feature-1-1.jpg?sfvrsn=e3844369_11"): "duplicate of Democratic Republic of the Congo",
    ("TGO", "https://m.media-amazon.com/images/M/MV5BMGFlMGNhZmItNWI1OC00YjBlLThlZDItMmNhZTEzYjJlYjFhXkEyXkFqcGdeQXRyYW5zY29kZS13b3JrZmxvdw@@._V1_.jpg"): "reviewed: film still",
    ("IRQ", "https://assets.newsweek.com/wp-content/uploads/2025/08/2210818-iraq-war.png"): "reviewed: edited graphic",
    ("SAU", "https://www.economist.com/cdn-cgi/image/width=1424,quality=80,format=auto/content-assets/images/20261024_LDD002.jpg"): "reviewed: edited graphic",
    ("BLR", "https://news.stthomas.edu/wp-content/uploads/2012/04/belarus-1.png"): "reviewed: map",
    ("CMR", "https://images.ctfassets.net/6dczv5fypa6q/1WVT3APNhlj8EKX6YpnPv5/b73569f3cc8aff93f160c43499e53dd0/Cameroon.jpg"): "reviewed: map",
    ("COD", "https://assets.publishing.service.gov.uk/media/6a196a3465bc5f798327f4fe/FCDO_TA_012_-_Democratic_Repbulic_of_the_Congo_Travel_Advice_Ed20_WEB.jpg"): "reviewed: map",
    ("MDA", "https://images.ctfassets.net/6dczv5fypa6q/Mq19mH6f4R82QONDdM08q/c98f5b3c82782886a606c2769f25460b/Moldova.jpg"): "reviewed: map",
    ("SWE", "https://european-union.europa.eu/sites/default/files/styles/oe_theme_medium_no_crop/public/2025-12/Sweden.png?itok=NieB6Zm3"): "reviewed: map",
    ("TWN", "https://ichef.bbci.co.uk/news/480/cpsprodpb/24F6/production/_132226490_china_taiwan_v05_first_island_chain_2x640-nc.png.webp"): "reviewed: map",
    ("UKR", "https://ichef.bbci.co.uk/ace/standard/976/cpsprodpb/1601E/production/_109224109_ukraine.png"): "reviewed: map",
    ("USA", "https://www.worldatlas.com/upload/99/0f/79/217/untitled-design-2019-04-26t144520-641.jpg"): "reviewed: map",
    ("KIR", "https://preview.redd.it/how-is-living-on-kiribati-v0-538r8xtu2fxg1.jpeg?width=1080&crop=smart&auto=webp&s=aac5fe9e12aca0889833e297332ed3881b52c333"): "reviewed: map",
    ("NER", "https://i.redd.it/2x58tb0gwnff1.jpeg"): "reviewed: map",
    ("SDN", "https://countrystudies.us/sudan/geography.gif"): "reviewed: map",
    ("COG", "https://www.cdc.gov/global-health/media/images/DRC01_1.png"): "reviewed: flag graphic",
    ("GIN", "https://i.redd.it/qkt38zom8rhc1.png"): "reviewed: map",
    ("COG", "https://www.measureevaluation.org/countries/democratic-republic-of-congo/carousel/democratic-republic-of-congo/image"): "duplicate of Democratic Republic of the Congo",
    ("COG", "https://www.fauna-flora.org/wp-content/uploads/2017/05/DRC-0001-AGT.jpg"): "duplicate of Democratic Republic of the Congo",
    ("COG", "https://www.aljazeera.com/wp-content/uploads/2012/03/201234161732851734_20.jpeg?resize=1200%2C675"): "reviewed: map",
    ("GIN", "https://townlinehatchery.com/wp-content/uploads/2026/10/Guinea-chick-DP.jpg"): "named: guinea collision",
    ("GIN", "https://images.ctfassets.net/6dczv5fypa6q/1f26ofi312Erb6TVXoFn6K/d84b930b9126689d8746bc2b294ba6a9/Guinea-Bissau.jpg"): "named: guinea collision",
    ("NER", "http://www.taneter.org/niger%20ancient%20sites.png"): "reviewed: map",
    ("USA", "https://www.saadatrent.com/mag/wp-content/uploads/2024/12/US-states-and-cities.webp"): "reviewed: edited graphic",
    ("USA", "https://m.media-amazon.com/images/S/pv-target-images/2ea3b071872abb032afc5327152308cd4989b3291a527215a12672b11598cfb7._SX1080_FMjpg_.jpg"): "reviewed: edited graphic",
    ("USA", "https://m.media-amazon.com/images/M/MV5BY2FmNmNkOGEtZDY4ZC00N2I2LWFhMGQtOWRiMTVlOGY3Mzk2XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"): "named: film still",
    ("USA", "https://miro.medium.com/1*jV34kOOQws-ryLxn9DmBcA.png"): "reviewed: edited graphic",
    ("USA", "http://cdn.statcdn.com/Infographic/images/normal/19038.jpeg"): "reviewed: map",
    ("USA", "https://www.thefactsite.com/wp-content/uploads/2022/06/usa-facts.jpg"): "reviewed: edited graphic",
    ("USA", "https://pi.tedcdn.com/r/talkstar-assets.s3.amazonaws.com/production/playlists/playlist_917/81eda5e5-c366-4c38-9621-167777af7803/happy_birthday_usa-2000x2000_VP.jpeg?u%5Br%5D=2&u%5Bs%5D=0.5&u%5Ba%5D=0.8&u%5Bt%5D=0.03&quality=80&w=3840"): "duplicate photo",
    ("USA", "https://www.battlefields.org/sites/default/files/styles/resource_hero/public/thumbnails/image/Constitution%2520Social%2520Card.jpg.webp?h=268b1787&itok=t_Sj5gTD"): "reviewed: document",
}


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


def map_address(url):
    text = str(url or "")
    return bool(URL_MAP.search(text) or DROP_RULES[3][0].search(text))


def search_query(country):
    return QUERY_OVERRIDES.get(country["iso_code"], country["country_name"])


def rejection_reason(result):
    text = " ".join(
        str(result.get(field) or "") for field in ("title", "source", "link", "original")
    )
    for pattern, reason in DROP_RULES:
        if pattern.search(text):
            return reason
    original = result.get("original") or ""
    if not original:
        return "missing image url"
    if map_address(original):
        return "map"
    return None


def search_images(query, api_key, page=0):
    params = {"engine": "google_images", "q": query, "api_key": api_key, "hl": "en"}
    if page:
        params["ijn"] = page
    response = requests.get(
        "https://serpapi.com/search.json",
        params=params,
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


def present_labels(labels):
    if labels is None:
        return None
    values = []
    for value in labels:
        if value is None or pd.isna(value):
            continue
        text = str(value).strip()
        if text:
            values.append(text)
    return values


def is_flag_word(text):
    folded = str(text).casefold()
    return folded in FLAG_EXACT or folded.startswith("flag of")


def flag_subject(labels):
    if not labels:
        return False
    others = [text for text in labels if not is_flag_word(text)]
    if not others:
        return True
    return all(text.casefold() == "wind" for text in others)


def has_flag_word(labels):
    return any(is_flag_word(text) for text in present_labels(labels) or [])


def vision_label_reason(labels):
    for text in labels:
        if text.casefold() in DROP_LABELS:
            return f"vision label: {text}"
    return ""


def collision(url, labels, iso_code):
    text = str(url or "")
    if iso_code == "COG" and WRONG_CONGO.search(text):
        return "duplicate of Democratic Republic of the Congo"
    if iso_code == "GIN" and GUINEA_BIRD.search(text):
        return "named: guinea collision"
    if labels and iso_code == "GIN" and any(text.casefold() == "phasianidae" for text in labels):
        return "named: guinea collision"
    return ""


def asset_id(url):
    match = NATGEO_ID.search(str(url or ""))
    if not match:
        return ""
    return match.group(1).casefold()


def duplicate_asset(url, kept_urls):
    asset = asset_id(url)
    if not asset:
        return ""
    for other in kept_urls:
        if str(other) == str(url):
            continue
        if asset_id(other) == asset:
            return "duplicate photo"
    return ""


def photo_reason(url, labels, iso_code, kept_urls=(), congo_urls=()):
    url = str(url or "")
    named = NAMED_URLS.get((iso_code, url))
    if named:
        return named
    present = present_labels(labels)
    collided = collision(url, present, iso_code)
    if collided:
        return collided
    if map_address(url):
        return "url: map"
    if iso_code == "COG" and url in set(congo_urls):
        return "duplicate of Democratic Republic of the Congo"
    if duplicate_asset(url, kept_urls):
        return "duplicate photo"
    if present is None:
        return ""
    labeled = vision_label_reason(present)
    if labeled:
        return labeled
    if flag_subject(present):
        return "flag subject"
    return ""


def mark_duplicate_photos(images, reasons):
    reasons = reasons.copy()
    grouped = {}
    for idx, row in images.iterrows():
        if reasons.loc[idx]:
            continue
        asset = asset_id(row["image_url"])
        if not asset:
            continue
        key = (row["iso_code"], asset)
        rank = row["raw_search_rank"]
        if key not in grouped or rank < grouped[key][1]:
            if key in grouped:
                reasons.loc[grouped[key][0]] = "duplicate photo"
            grouped[key] = (idx, rank)
        else:
            reasons.loc[idx] = "duplicate photo"
    return reasons


def assign_ranks(frame):
    if frame.empty:
        return frame
    ordered = frame.sort_values(["iso_code", "raw_search_rank"], kind="mergesort").copy()
    ordered["search_rank"] = ordered.groupby("iso_code").cumcount() + 1
    return ordered


def kept_record(country, url, raw_rank, labels, search_rank):
    return {
        **country,
        "image_url": url,
        "search_rank": search_rank,
        "raw_search_rank": raw_rank,
        "dominant_label_1": labels[0],
        "dominant_label_2": labels[1],
        "dominant_label_3": labels[2],
    }


def excluded_record(country, url, raw_rank, result, reason):
    return {
        "country_name": country["country_name"],
        "iso_code": country["iso_code"],
        "raw_search_rank": raw_rank,
        "image_url": url,
        "title": (result or {}).get("title") or "",
        "source": (result or {}).get("source") or "",
        "reason": reason or "",
    }


def consider_result(country, result, raw_rank, api_keys, kept_urls, congo_urls):
    url = result.get("original") or ""
    reason = rejection_reason(result)
    if not reason and url:
        reason = photo_reason(url, None, country["iso_code"], kept_urls, congo_urls)
    if reason:
        return None, excluded_record(country, url, raw_rank, result, reason)
    labels = vision_labels(url, api_keys["GOOGLE_API_KEY"])
    time.sleep(0.2)
    if labels is None:
        return None, excluded_record(country, url, raw_rank, result, "vision failed")
    reason = photo_reason(url, labels, country["iso_code"], kept_urls, congo_urls)
    if reason:
        return None, excluded_record(country, url, raw_rank, result, reason)
    return labels, None


def collect_country(country, api_keys, congo_urls=()):
    kept = []
    excluded = []
    kept_urls = []
    results = search_images(search_query(country), api_keys["SERPAPI_API_KEY"])
    for index, result in enumerate(results, start=1):
        raw_rank = result.get("position") or index
        labels, rejected = consider_result(
            country, result, raw_rank, api_keys, kept_urls, congo_urls
        )
        if rejected:
            excluded.append(rejected)
            continue
        kept_urls.append(result.get("original") or "")
        kept.append(kept_record(country, kept_urls[-1], raw_rank, labels, len(kept) + 1))
        if len(kept) == KEEP_PER_COUNTRY:
            break
    return kept, excluded


def fill_country(country, images, excluded, api_keys, congo_urls=()):
    iso_code = country["iso_code"]
    have = images.loc[images["iso_code"] == iso_code]
    need = KEEP_PER_COUNTRY - len(have)
    if need <= 0:
        return images, excluded, 0
    seen = set(have["image_url"].astype(str))
    seen.update(excluded.loc[excluded["iso_code"] == iso_code, "image_url"].astype(str))
    kept_urls = list(have["image_url"].astype(str))
    added = []
    new_excluded = []
    for page in range(MAX_SEARCH_PAGES):
        if len(added) >= need:
            break
        results = search_images(search_query(country), api_keys["SERPAPI_API_KEY"], page=page)
        for index, result in enumerate(results, start=1):
            if len(added) >= need:
                break
            url = result.get("original") or ""
            if not url or url in seen:
                continue
            seen.add(url)
            raw_rank = (result.get("position") or index) + page * 100
            labels, rejected = consider_result(
                country, result, raw_rank, api_keys, kept_urls, congo_urls
            )
            if rejected:
                new_excluded.append(rejected)
                continue
            kept_urls.append(url)
            added.append(kept_record(country, url, raw_rank, labels, 0))
    if added:
        images = pd.concat([images, pd.DataFrame(added)], ignore_index=True)
        images = assign_ranks(images)
    if new_excluded:
        excluded = pd.concat([excluded, pd.DataFrame(new_excluded)], ignore_index=True)
    return images, excluded, len(added)


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
