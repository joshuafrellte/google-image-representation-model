"""Collect Google Images for every country in the country table.

Writes data/processed/images.csv and data/processed/review/excluded.csv.
Does not read or write the pilot files. A country is recorded in
data/processed/collection_progress.csv only after its search finishes,
so a later run skips countries that already spent SerpApi and Cloud Vision calls.

No API calls happen unless --run is passed. --refresh deletes the full-run
files and collects all 196 countries again; it still requires --run.
--refill applies the same filter to images.csv and, with --run, searches
only the countries that have fewer than 10 photos. It does not delete the sheet.
"""

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import requests

import collect

ROOT = Path(__file__).resolve().parent
IMAGES_PATH = ROOT / "data" / "processed" / "images.csv"
EXCLUDED_PATH = ROOT / "data" / "processed" / "review" / "excluded.csv"
PROGRESS_PATH = ROOT / "data" / "processed" / "collection_progress.csv"
FLAG_PATH = ROOT / "data" / "processed" / "review" / "flag_review.csv"
BLANK_PATH = ROOT / "data" / "processed" / "review" / "blank_label_review.csv"
EXPECTED_COUNTRIES = 196
IMAGE_COLUMNS = [
    "country_name",
    "world_bank_name",
    "iso_code",
    "region",
    "development_status",
    "income_status_binary",
    "actual_urban_population_pct",
    "urban_year",
    "image_url",
    "search_rank",
    "raw_search_rank",
    "dominant_label_1",
    "dominant_label_2",
    "dominant_label_3",
]
EXCLUDED_COLUMNS = [
    "country_name",
    "iso_code",
    "raw_search_rank",
    "image_url",
    "title",
    "source",
    "reason",
]
PROGRESS_COLUMNS = ["iso_code", "country_name", "kept", "excluded"]


def output_paths():
    paths = (IMAGES_PATH, EXCLUDED_PATH, PROGRESS_PATH)
    pilot = {collect.IMAGES_PATH.resolve(), collect.EXCLUDED_PATH.resolve()}
    for path in paths:
        if path.resolve() in pilot:
            raise SystemExit(f"{path.name} is a pilot file. The full run must use a different name.")
    return paths


def load_countries():
    countries = pd.read_csv(collect.COUNTRIES_PATH)
    count = len(countries)
    unique = countries["iso_code"].nunique(dropna=True)
    if count != EXPECTED_COUNTRIES or unique != EXPECTED_COUNTRIES:
        raise SystemExit(
            f"Expected {EXPECTED_COUNTRIES} unique countries, found {count} rows and {unique} iso codes."
        )
    return countries


def completed_codes():
    if not PROGRESS_PATH.exists():
        if IMAGES_PATH.exists() or EXCLUDED_PATH.exists():
            raise SystemExit(
                "Full-run image files exist without collection_progress.csv. "
                "Pass --run --refresh to start over, which spends the API calls again."
            )
        return set()
    progress = pd.read_csv(PROGRESS_PATH)
    return set(progress["iso_code"].astype(str))


def append_rows(path, rows, columns):
    if not rows:
        return
    frame = pd.DataFrame(rows, columns=columns)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, mode="a", header=not path.exists(), index=False, encoding="utf-8")


def clear_outputs():
    for path in output_paths():
        path.unlink(missing_ok=True)


def row_count(path):
    if not path.exists():
        return 0
    return len(pd.read_csv(path))


def congo_urls(images):
    if images is None or images.empty:
        return set()
    return set(images.loc[images["iso_code"] == "COD", "image_url"].astype(str))


def collect_with_retries(country, api_keys, kept_congo=(), attempts=4):
    for attempt in range(1, attempts + 1):
        try:
            return collect.collect_country(country, api_keys, congo_urls=kept_congo)
        except requests.RequestException as exc:
            if attempt == attempts:
                raise
            wait = 5 * attempt
            print(
                f"  {exc.__class__.__name__}; retry {attempt} of {attempts - 1} in {wait}s",
                flush=True,
            )
            time.sleep(wait)


def sheet_reasons(images):
    reasons = images.apply(
        lambda row: collect.photo_reason(
            row["image_url"],
            [row[column] for column in collect.LABEL_COLUMNS],
            row["iso_code"],
            (),
            congo_urls(images),
        ),
        axis=1,
    )
    return collect.mark_duplicate_photos(images, reasons)


def write_reviews(images):
    flags = images.loc[
        images.apply(
            lambda row: collect.has_flag_word([row[column] for column in collect.LABEL_COLUMNS]),
            axis=1,
        )
    ]
    flags.to_csv(FLAG_PATH, index=False, encoding="utf-8")
    blank = images.loc[
        images.apply(
            lambda row: not collect.present_labels(
                [row[column] for column in collect.LABEL_COLUMNS]
            ),
            axis=1,
        )
    ].copy()
    blank["review_reason"] = "blank labels"
    blank.to_csv(BLANK_PATH, index=False, encoding="utf-8")
    print(f"Listed {len(flags)} flag rows in {FLAG_PATH.name}.")
    print(f"Listed {len(blank)} rows in {BLANK_PATH.name}.")


def update_progress(images, excluded):
    if not PROGRESS_PATH.exists():
        return
    progress = pd.read_csv(PROGRESS_PATH)
    kept_counts = images.groupby("iso_code").size()
    excluded_counts = excluded.groupby("iso_code").size()
    progress["kept"] = progress["iso_code"].map(kept_counts).fillna(0).astype(int)
    progress["excluded"] = progress["iso_code"].map(excluded_counts).fillna(0).astype(int)
    progress.to_csv(PROGRESS_PATH, index=False, encoding="utf-8")


def short_countries(images, countries):
    counts = images.groupby("iso_code").size()
    short = []
    for country in countries.to_dict("records"):
        if int(counts.get(country["iso_code"], 0)) < collect.KEEP_PER_COUNTRY:
            short.append(country)
    return short


def apply_filter(images, excluded):
    images = images.copy()
    images["drop_reason"] = sheet_reasons(images)
    dropped = images.loc[images["drop_reason"] != ""].copy()
    kept = images.loc[images["drop_reason"] == ""].drop(columns=["drop_reason"])
    kept = collect.assign_ranks(kept)
    if dropped.empty:
        print("No photos left to drop.")
        return kept, excluded
    new_rows = pd.DataFrame(
        {
            "country_name": dropped["country_name"],
            "iso_code": dropped["iso_code"],
            "raw_search_rank": dropped["raw_search_rank"],
            "image_url": dropped["image_url"],
            "title": "",
            "source": "",
            "reason": dropped["drop_reason"],
        }
    )
    excluded = pd.concat([excluded, new_rows], ignore_index=True)
    kept.to_csv(IMAGES_PATH, index=False, encoding="utf-8")
    excluded.to_csv(EXCLUDED_PATH, index=False, encoding="utf-8")
    print(f"Dropped {len(dropped)} photos. {len(kept)} remain.")
    print(dropped["drop_reason"].value_counts().to_string())
    return kept, excluded


def fill_with_retries(country, images, excluded, api_keys, attempts=4):
    for attempt in range(1, attempts + 1):
        try:
            return collect.fill_country(
                country, images, excluded, api_keys, congo_urls=congo_urls(images)
            )
        except requests.RequestException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status == 429:
                print(
                    "SerpApi has no searches left. Countries still under 10 were not filled.",
                    flush=True,
                )
                raise SystemExit(1) from exc
            if attempt == attempts:
                raise
            wait = 5 * attempt
            print(
                f"  {exc.__class__.__name__}; retry {attempt} of {attempts - 1} in {wait}s",
                flush=True,
            )
            time.sleep(wait)


def refill(run):
    if not IMAGES_PATH.exists() or not EXCLUDED_PATH.exists():
        raise SystemExit("images.csv and excluded.csv must exist before a refill.")
    images = pd.read_csv(IMAGES_PATH)
    excluded = pd.read_csv(EXCLUDED_PATH)
    images, excluded = apply_filter(images, excluded)
    countries = load_countries()
    pending = short_countries(images, countries)
    print(f"{len(pending)} countries have fewer than 10 photos.")
    update_progress(images, excluded)
    write_reviews(images)
    if not pending:
        print(f"{len(images)} photos remain.")
        return
    if not run:
        print("Pass --run --refill to search again for those countries only.")
        return
    api_keys = collect.load_env(collect.ENV_PATH)
    for number, country in enumerate(pending, start=1):
        before = int((images["iso_code"] == country["iso_code"]).sum())
        print(
            f"Filling {country['country_name']} ({country['iso_code']}) "
            f"[{number}/{len(pending)}] from {before}",
            flush=True,
        )
        images, excluded, added = fill_with_retries(country, images, excluded, api_keys)
        after = int((images["iso_code"] == country["iso_code"]).sum())
        print(f"  added {added}; now {after}", flush=True)
        images.to_csv(IMAGES_PATH, index=False, encoding="utf-8")
        excluded.to_csv(EXCLUDED_PATH, index=False, encoding="utf-8")
        update_progress(images, excluded)
        if after < collect.KEEP_PER_COUNTRY:
            print("  fewer than 10 photos remained after the extra search", flush=True)
    write_reviews(images)
    print(f"Wrote {len(images)} photos to {IMAGES_PATH.name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--refill", action="store_true")
    args = parser.parse_args()
    output_paths()
    if args.refill and args.refresh:
        print("--refill leaves the sheet in place. --refresh would delete it and search again.")
        return
    if args.refill:
        refill(args.run)
        return

    countries = load_countries()
    if args.refresh and not args.run:
        print(
            "--refresh would delete images.csv, excluded.csv, and collection_progress.csv, "
            "then collect all 196 countries again."
        )
        print("Pass --run --refresh to do that. Pilot files are not touched.")
        print("That spends the SerpApi and Cloud Vision calls a second time.")
        return

    if args.refresh:
        clear_outputs()
        print("Cleared the full-run files. Pilot files were left in place.")

    done = completed_codes()
    pending = countries.loc[~countries["iso_code"].astype(str).isin(done)]
    if pending.empty:
        print(f"{IMAGES_PATH.name} already covers all {EXPECTED_COUNTRIES} countries.")
        print("Pass --run --refresh to collect again. That spends the API calls a second time.")
        return

    if not args.run:
        print(
            f"{len(pending)} countries would be collected into {IMAGES_PATH.name}. "
            f"{len(done)} are already recorded in {PROGRESS_PATH.name}."
        )
        print("Each country is one SerpApi search, then one Cloud Vision call per photo that reaches labeling.")
        print("Pass --run to start. A later --run skips countries already in the progress file.")
        return

    api_keys = collect.load_env(collect.ENV_PATH)
    records = countries.to_dict("records")
    for number, country in enumerate(records, start=1):
        iso_code = str(country["iso_code"])
        if iso_code in done:
            continue
        print(
            f"Collecting {country['country_name']} ({iso_code}) [{number}/{EXPECTED_COUNTRIES}]",
            flush=True,
        )
        kept_congo = ()
        if iso_code == "COG" and IMAGES_PATH.exists():
            kept_congo = congo_urls(pd.read_csv(IMAGES_PATH))
        kept, excluded = collect_with_retries(country, api_keys, kept_congo)
        print(f"  kept {len(kept)}; excluded {len(excluded)}", flush=True)
        if len(kept) < collect.KEEP_PER_COUNTRY:
            print("  fewer than 10 photos remained after filtering", flush=True)
        append_rows(IMAGES_PATH, kept, IMAGE_COLUMNS)
        append_rows(EXCLUDED_PATH, excluded, EXCLUDED_COLUMNS)
        append_rows(
            PROGRESS_PATH,
            [
                {
                    "iso_code": iso_code,
                    "country_name": country["country_name"],
                    "kept": len(kept),
                    "excluded": len(excluded),
                }
            ],
            PROGRESS_COLUMNS,
        )
        done.add(iso_code)

    print(f"Wrote {row_count(IMAGES_PATH)} image rows to {IMAGES_PATH}")
    print(f"Wrote {row_count(EXCLUDED_PATH)} excluded rows to {EXCLUDED_PATH}")
    print(f"Completed {len(done)} of {EXPECTED_COUNTRIES} countries")


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as exc:
        print(f"Request failed: {exc.__class__.__name__}", file=sys.stderr)
        raise SystemExit(1) from exc
