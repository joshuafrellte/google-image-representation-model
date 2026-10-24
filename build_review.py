"""Rebuild the full-run review sheet from images.csv and excluded.csv. No API calls."""

import html
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
IMAGES_PATH = ROOT / "data" / "processed" / "images.csv"
EXCLUDED_PATH = ROOT / "data" / "processed" / "review" / "excluded.csv"
COUNTRIES_PATH = ROOT / "data" / "processed" / "countries.csv"
SHEET_PATH = ROOT / "data" / "processed" / "review" / "index.html"
LABEL_COLUMNS = ("dominant_label_1", "dominant_label_2", "dominant_label_3")


def text(value):
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def labels_for(row):
    labels = []
    for column in LABEL_COLUMNS:
        value = row[column]
        if pd.isna(value):
            continue
        cleaned = str(value).strip()
        if cleaned:
            labels.append(cleaned)
    return labels


def urban_percent(value):
    if value is None or pd.isna(value) or str(value).strip() == "":
        return None
    return float(value)


def reason_descriptors(reason):
    cleaned = text(reason)
    if not cleaned:
        return []
    descriptors = [cleaned]
    if ":" in cleaned:
        tail = cleaned.split(":", 1)[1].strip()
        if tail and tail.lower() not in {item.lower() for item in descriptors}:
            descriptors.append(tail)
    return descriptors


def with_source(descriptors, source):
    cleaned = text(source)
    if cleaned and cleaned.lower() not in {item.lower() for item in descriptors}:
        return [*descriptors, cleaned]
    return list(descriptors)


def card(country, rank, region, status, urban, descriptors, url, labels, photo_set, source):
    urban_attr = "" if urban is None else str(urban)
    lines = []
    place = " · ".join(part for part in (region, status) if part)
    if place:
        lines.append(html.escape(place))
    if urban is not None:
        lines.append(f"{urban:.1f}% urban")
    if text(source):
        lines.append(html.escape(text(source)))
    rank_attr = "" if rank is None else str(rank)
    rank_html = "" if rank is None else f" <span>rank {rank}</span>"
    hidden = " hidden" if photo_set == "excluded" else ""
    escaped_url = html.escape(url, quote=True)
    return f"""
    <article{hidden} data-set="{photo_set}" data-country="{html.escape(country, quote=True)}" data-rank="{rank_attr}" data-region="{html.escape(region, quote=True)}" data-development="{html.escape(status, quote=True)}" data-urban="{urban_attr}" data-descriptors="{html.escape(json.dumps(descriptors), quote=True)}">
      <img src="{escaped_url}" alt="" loading="lazy">
      <h2>{html.escape(country)}{rank_html}</h2>
      <p class="meta">{"<br>".join(lines)}</p>
      <p class="labels">{html.escape(labels)}</p>
      <p><a href="{escaped_url}">Original image</a></p>
    </article>"""


def kept_card(row):
    labels = labels_for(row)
    rank = text(row["search_rank"])
    return card(
        country=text(row["country_name"]),
        rank=int(float(rank)) if rank else None,
        region=text(row["region"]),
        status=text(row["development_status"]),
        urban=urban_percent(row["actual_urban_population_pct"]),
        descriptors=labels,
        url=text(row["image_url"]),
        labels=", ".join(labels),
        photo_set="kept",
        source="",
    )


def excluded_card(row, country_row):
    reason = text(row["reason"])
    source = text(row["source"])
    rank = text(row["raw_search_rank"])
    meta = country_row or {}
    return card(
        country=text(row["country_name"]),
        rank=int(float(rank)) if rank else None,
        region=text(meta.get("region")),
        status=text(meta.get("development_status")),
        urban=urban_percent(meta.get("actual_urban_population_pct")),
        descriptors=with_source(reason_descriptors(reason), source),
        url=text(row["image_url"]),
        labels=reason,
        photo_set="excluded",
        source=source,
    )


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>GIRD images</title>
  <style>
    body { font-family: sans-serif; margin: 24px; background: #f6f6f6; color: #1a1a1a; }
    h1 { font-size: 1.4rem; margin-bottom: 8px; }
    .toolbar {
      position: sticky;
      top: 0;
      z-index: 2;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px 16px;
      align-items: end;
      margin: 0 -24px;
      padding: 12px 24px 14px;
      background: #f6f6f6;
      border-bottom: 1px solid #e4e4e4;
    }
    .field { display: flex; flex-direction: column; gap: 4px; font-size: 0.75rem; color: #333; }
    .field input, .field select, .field button {
      font: inherit;
      font-size: 0.95rem;
      color: #1a1a1a;
      width: 100%;
      padding: 8px 10px;
      border: 1px solid #ccc;
      border-radius: 4px;
      background: #fff;
    }
    .field button { cursor: pointer; text-align: left; }
    .field button[aria-pressed="true"] {
      background: #1a1a1a;
      color: #fff;
      border-color: #1a1a1a;
    }
    .hint, #count { color: #444; }
    .hint { margin: 10px 0 0; font-size: 0.9rem; }
    #count { margin: 8px 0 16px; }
    #empty { margin: 0 0 16px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
    article { background: white; padding: 12px; }
    img { width: 100%; height: 200px; object-fit: cover; background: #ddd; }
    h2 { font-size: 1rem; margin: 10px 0 4px; }
    h2 span, p { color: #444; font-weight: normal; }
    .meta { font-size: 0.85rem; margin: 0 0 4px; }
    .missing { height: 200px; display: grid; place-items: center; background: #eee; text-align: center; padding: 12px; }
    a { color: #163; }
  </style>
</head>
<body>
  <h1>GIRD images</h1>
  <div class="toolbar">
    <div class="field">
      <span id="set-label">Showing final cut</span>
      <button id="set-toggle" type="button" aria-pressed="false">Show excluded</button>
    </div>
    <label class="field search">
      Search
      <input id="search" type="search" placeholder="ja, city, water" autocomplete="off">
    </label>
    <label class="field">
      Region
      <select id="region">
        <option value="">All regions</option>
      </select>
    </label>
    <label class="field">
      Development status
      <select id="development">
        <option value="">All statuses</option>
      </select>
    </label>
    <label class="field">
      Sort
      <select id="sort">
        <option value="original">Original order</option>
        <option value="alpha-asc">Alphabetical, A to Z</option>
        <option value="alpha-desc">Alphabetical, Z to A</option>
        <option value="urban-desc">Urban population, high to low</option>
        <option value="urban-asc">Urban population, low to high</option>
      </select>
    </label>
  </div>
  <p class="hint">Shows a country when its name starts with the text, and any photo whose label, exclusion reason, or source starts with the text.</p>
  <p id="count"></p>
  <p id="empty" hidden>No photos match this search and these filters.</p>
  <div class="grid" id="grid">
__CARDS__
  </div>
  <script>
    const DEVELOPMENT_ORDER = ["Low income", "Lower middle income", "Upper middle income", "High income"];

    const grid = document.querySelector("#grid");
    const searchInput = document.querySelector("#search");
    const regionSelect = document.querySelector("#region");
    const developmentSelect = document.querySelector("#development");
    const sortSelect = document.querySelector("#sort");
    const count = document.querySelector("#count");
    const empty = document.querySelector("#empty");
    const setLabel = document.querySelector("#set-label");
    const setToggle = document.querySelector("#set-toggle");

    let currentSet = "kept";
    let articles = [];
    let items = new Map();

    grid.addEventListener("error", (event) => {
      if (event.target.tagName !== "IMG") return;
      const missing = document.createElement("p");
      missing.className = "missing";
      missing.textContent = "Image failed to load.";
      event.target.replaceWith(missing);
    }, true);

    function addOptions(select, values) {
      values.forEach((value) => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        select.append(option);
      });
    }

    function describeSet() {
      const showingExcluded = currentSet === "excluded";
      setLabel.textContent = showingExcluded ? "Showing excluded" : "Showing final cut";
      setToggle.textContent = showingExcluded ? "Show final cut" : "Show excluded";
      setToggle.setAttribute("aria-pressed", showingExcluded ? "true" : "false");
    }

    function fillFilters() {
      [regionSelect, developmentSelect].forEach((select) => {
        [...select.options].slice(1).forEach((option) => option.remove());
      });
      const regions = [...new Set(articles.map((article) => items.get(article).region))]
        .filter(Boolean)
        .sort((a, b) => a.localeCompare(b));
      const developments = DEVELOPMENT_ORDER.filter((status) =>
        articles.some((article) => items.get(article).development === status)
      );
      addOptions(regionSelect, regions);
      addOptions(developmentSelect, developments);
    }

    function matchesSearch(item, query) {
      if (!query) return true;
      const q = query.toLowerCase();
      if (item.country.toLowerCase().startsWith(q)) return true;
      return item.descriptors.some((descriptor) => descriptor.toLowerCase().startsWith(q));
    }

    function urbanValue(item, mode) {
      if (Number.isFinite(item.urban)) return item.urban;
      return mode === "urban-asc" ? Infinity : -Infinity;
    }

    function compare(a, b, mode) {
      const left = items.get(a);
      const right = items.get(b);
      if (mode === "alpha-asc" || mode === "alpha-desc") {
        const byName = left.country.localeCompare(right.country);
        const directed = mode === "alpha-asc" ? byName : -byName;
        if (directed) return directed;
      } else if (mode === "urban-asc" || mode === "urban-desc") {
        const byUrban = urbanValue(left, mode) - urbanValue(right, mode);
        const directed = mode === "urban-asc" ? byUrban : -byUrban;
        if (directed) return directed;
        const byName = left.country.localeCompare(right.country);
        if (byName) return byName;
      } else if (left.index !== right.index) {
        return left.index - right.index;
      }
      const leftRank = Number.isFinite(left.rank) ? left.rank : Infinity;
      const rightRank = Number.isFinite(right.rank) ? right.rank : Infinity;
      if (leftRank !== rightRank) return leftRank - rightRank;
      return left.index - right.index;
    }

    function apply() {
      const query = searchInput.value.trim();
      const region = regionSelect.value;
      const development = developmentSelect.value;
      const mode = sortSelect.value;
      const ordered = articles.slice().sort((a, b) => compare(a, b, mode));
      let shown = 0;
      ordered.forEach((article) => {
        const item = items.get(article);
        const match = matchesSearch(item, query)
          && (!region || item.region === region)
          && (!development || item.development === development);
        article.hidden = !match;
        if (match) shown += 1;
        grid.append(article);
      });
      const setName = currentSet === "kept" ? "final-cut" : "excluded";
      count.textContent = shown + " of " + articles.length + " " + setName + " photos";
      empty.hidden = shown !== 0;
    }

    function restoreSelect(select, value) {
      const exists = [...select.options].some((option) => option.value === value);
      select.value = exists ? value : "";
    }

    function indexArticles() {
      const previousRegion = regionSelect.value;
      const previousDevelopment = developmentSelect.value;
      const all = [...grid.querySelectorAll("article")];
      all.forEach((article) => {
        if (article.dataset.set !== currentSet) article.hidden = true;
      });
      articles = all.filter((article) => article.dataset.set === currentSet);
      items = new Map();
      articles.forEach((article, index) => {
        const urban = article.dataset.urban === "" ? NaN : Number(article.dataset.urban);
        const rank = article.dataset.rank === "" ? NaN : Number(article.dataset.rank);
        items.set(article, {
          index,
          country: article.dataset.country,
          rank,
          descriptors: JSON.parse(article.dataset.descriptors || "[]"),
          region: article.dataset.region,
          development: article.dataset.development,
          urban
        });
      });
      fillFilters();
      restoreSelect(regionSelect, previousRegion);
      restoreSelect(developmentSelect, previousDevelopment);
      apply();
    }

    function parseCsv(text) {
      const rows = [];
      let row = [];
      let field = "";
      let quoted = false;
      for (let i = 0; i < text.length; i += 1) {
        const char = text[i];
        if (quoted) {
          if (char === '"') {
            if (text[i + 1] === '"') {
              field += '"';
              i += 1;
            } else {
              quoted = false;
            }
          } else {
            field += char;
          }
        } else if (char === '"') {
          quoted = true;
        } else if (char === ",") {
          row.push(field);
          field = "";
        } else if (char === "\n") {
          row.push(field);
          rows.push(row);
          row = [];
          field = "";
        } else if (char !== "\r") {
          field += char;
        }
      }
      if (field || row.length) {
        row.push(field);
        rows.push(row);
      }
      const header = rows.shift() || [];
      return rows
        .filter((cells) => cells.length === header.length && cells.some((cell) => cell !== ""))
        .map((cells) => {
          const record = {};
          header.forEach((name, index) => {
            record[name] = cells[index];
          });
          return record;
        });
    }

    function reasonDescriptors(reason) {
      const cleaned = (reason || "").trim();
      if (!cleaned) return [];
      const descriptors = [cleaned];
      const splitAt = cleaned.indexOf(":");
      if (splitAt !== -1) {
        const tail = cleaned.slice(splitAt + 1).trim();
        if (tail && !descriptors.some((item) => item.toLowerCase() === tail.toLowerCase())) {
          descriptors.push(tail);
        }
      }
      return descriptors;
    }

    function articleFrom(record, photoSet, countries) {
      const excluded = photoSet === "excluded";
      const country = excluded ? (countries.get(record.iso_code) || {}) : record;
      const labels = excluded
        ? reasonDescriptors(record.reason)
        : ["dominant_label_1", "dominant_label_2", "dominant_label_3"]
          .map((key) => (record[key] || "").trim())
          .filter(Boolean);
      const source = excluded ? (record.source || "").trim() : "";
      const descriptors = labels.slice();
      if (source && !descriptors.some((item) => item.toLowerCase() === source.toLowerCase())) {
        descriptors.push(source);
      }
      const urbanRaw = country.actual_urban_population_pct;
      const urban = urbanRaw === undefined || urbanRaw === "" ? NaN : Number(urbanRaw);
      const rankRaw = excluded ? record.raw_search_rank : record.search_rank;
      const rank = rankRaw === undefined || rankRaw === "" ? NaN : Number(rankRaw);
      const region = country.region || "";
      const development = country.development_status || "";
      const countryName = record.country_name || "";
      const article = document.createElement("article");
      article.dataset.set = photoSet;
      article.hidden = photoSet !== currentSet;
      article.dataset.country = countryName;
      article.dataset.rank = Number.isFinite(rank) ? String(rank) : "";
      article.dataset.region = region;
      article.dataset.development = development;
      article.dataset.urban = Number.isFinite(urban) ? String(urban) : "";
      article.dataset.descriptors = JSON.stringify(descriptors);
      const image = document.createElement("img");
      image.src = record.image_url;
      image.alt = "";
      image.loading = "lazy";
      const heading = document.createElement("h2");
      heading.append(countryName + (Number.isFinite(rank) ? " " : ""));
      if (Number.isFinite(rank)) {
        const rankNode = document.createElement("span");
        rankNode.textContent = "rank " + rank;
        heading.append(rankNode);
      }
      const meta = document.createElement("p");
      meta.className = "meta";
      const place = [region, development].filter(Boolean).join(" · ");
      if (place) meta.append(place);
      if (Number.isFinite(urban)) {
        if (meta.childNodes.length) meta.append(document.createElement("br"));
        meta.append(urban.toFixed(1) + "% urban");
      }
      if (source) {
        if (meta.childNodes.length) meta.append(document.createElement("br"));
        meta.append(source);
      }
      const labelLine = document.createElement("p");
      labelLine.className = "labels";
      labelLine.textContent = excluded ? (record.reason || "").trim() : labels.join(", ");
      const linkLine = document.createElement("p");
      const link = document.createElement("a");
      link.href = record.image_url;
      link.textContent = "Original image";
      linkLine.append(link);
      article.append(image, heading, meta, labelLine, linkLine);
      return article;
    }

    searchInput.addEventListener("input", apply);
    regionSelect.addEventListener("change", apply);
    developmentSelect.addEventListener("change", apply);
    sortSelect.addEventListener("change", apply);
    setToggle.addEventListener("click", () => {
      currentSet = currentSet === "kept" ? "excluded" : "kept";
      describeSet();
      indexArticles();
    });
    describeSet();
    indexArticles();

    Promise.all([
      fetch(new URL("../images.csv", document.baseURI)),
      fetch(new URL("excluded.csv", document.baseURI)),
      fetch(new URL("../countries.csv", document.baseURI))
    ]).then(async (responses) => {
      if (responses.some((response) => !response.ok)) {
        throw new Error("Could not read the review tables");
      }
      const [imagesText, excludedText, countriesText] = await Promise.all(
        responses.map((response) => response.text())
      );
      const countries = new Map(parseCsv(countriesText).map((row) => [row.iso_code, row]));
      const kept = parseCsv(imagesText).map((record) => articleFrom(record, "kept", countries));
      const excludedRows = parseCsv(excludedText).map((record) => articleFrom(record, "excluded", countries));
      if (!kept.length && !excludedRows.length) return;
      grid.replaceChildren(...kept, ...excludedRows);
      indexArticles();
    }).catch(() => {});
  </script>
</body>
</html>
"""


def main():
    images = pd.read_csv(IMAGES_PATH)
    excluded = pd.read_csv(EXCLUDED_PATH)
    countries = pd.read_csv(COUNTRIES_PATH)
    country_by_iso = {row["iso_code"]: row for row in countries.to_dict("records")}
    cards = "\n".join(
        [kept_card(row) for row in images.to_dict("records")]
        + [
            excluded_card(row, country_by_iso.get(row["iso_code"]))
            for row in excluded.to_dict("records")
        ]
    )
    SHEET_PATH.write_text(TEMPLATE.replace("__CARDS__", cards), encoding="utf-8")
    print(f"Wrote {len(images)} final-cut cards and {len(excluded)} excluded cards to {SHEET_PATH}")


if __name__ == "__main__":
    main()
