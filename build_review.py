"""Rebuild the full-run review sheet from images.csv. No API calls."""

import html
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
IMAGES_PATH = ROOT / "data" / "processed" / "images.csv"
SHEET_PATH = ROOT / "data" / "processed" / "review" / "index.html"
LABEL_COLUMNS = ("dominant_label_1", "dominant_label_2", "dominant_label_3")


def labels_for(row):
    labels = []
    for column in LABEL_COLUMNS:
        value = row[column]
        if pd.isna(value):
            continue
        text = str(value).strip()
        if text:
            labels.append(text)
    return labels


def urban_percent(value):
    if pd.isna(value) or str(value).strip() == "":
        return None
    return float(value)


def card(row):
    labels = labels_for(row)
    urban = urban_percent(row["actual_urban_population_pct"])
    urban_attr = "" if urban is None else str(urban)
    urban_line = "" if urban is None else f"<br>{urban:.1f}% urban"
    descriptors = html.escape(json.dumps(labels), quote=True)
    url = html.escape(str(row["image_url"]), quote=True)
    country = html.escape(str(row["country_name"]))
    region = html.escape(str(row["region"]))
    status = html.escape(str(row["development_status"]))
    rank = int(row["search_rank"])
    return f"""
    <article data-country="{html.escape(str(row["country_name"]), quote=True)}" data-rank="{rank}" data-region="{html.escape(str(row["region"]), quote=True)}" data-development="{html.escape(str(row["development_status"]), quote=True)}" data-urban="{urban_attr}" data-descriptors="{descriptors}">
      <img src="{url}" alt="" loading="lazy">
      <h2>{country} <span>rank {rank}</span></h2>
      <p class="meta">{region} · {status}{urban_line}</p>
      <p class="labels">{html.escape(", ".join(labels))}</p>
      <p><a href="{url}">Original image</a></p>
    </article>"""


def main():
    images = pd.read_csv(IMAGES_PATH)
    cards = "\n".join(card(row) for row in images.to_dict("records"))
    document = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>GIRD images</title>
  <style>
    body {{ font-family: sans-serif; margin: 24px; background: #f6f6f6; color: #1a1a1a; }}
    h1 {{ font-size: 1.4rem; margin-bottom: 8px; }}
    .toolbar {{
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
    }}
    .field {{ display: flex; flex-direction: column; gap: 4px; font-size: 0.75rem; color: #333; }}
    .field input, .field select {{
      font: inherit;
      font-size: 0.95rem;
      color: #1a1a1a;
      width: 100%;
      padding: 8px 10px;
      border: 1px solid #ccc;
      border-radius: 4px;
      background: #fff;
    }}
    .hint, #count {{ color: #444; }}
    .hint {{ margin: 10px 0 0; font-size: 0.9rem; }}
    #count {{ margin: 8px 0 16px; }}
    #empty {{ margin: 0 0 16px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }}
    article {{ background: white; padding: 12px; }}
    img {{ width: 100%; height: 200px; object-fit: cover; background: #ddd; }}
    h2 {{ font-size: 1rem; margin: 10px 0 4px; }}
    h2 span, p {{ color: #444; font-weight: normal; }}
    .meta {{ font-size: 0.85rem; margin: 0 0 4px; }}
    .missing {{ height: 200px; display: grid; place-items: center; background: #eee; text-align: center; padding: 12px; }}
    a {{ color: #163; }}
  </style>
</head>
<body>
  <h1>GIRD images</h1>
  <div class="toolbar">
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
  <p class="hint">Shows a country when its name starts with the text, and any photo whose descriptor starts with the text.</p>
  <p id="count"></p>
  <p id="empty" hidden>No photos match this search and these filters.</p>
  <div class="grid">
{cards}
  </div>
  <script>
    const DEVELOPMENT_ORDER = ["Low income", "Lower middle income", "Upper middle income", "High income"];

    const grid = document.querySelector(".grid");
    let articles = [...grid.querySelectorAll("article")];
    let items = new Map();

    grid.addEventListener("error", (event) => {{
      if (event.target.tagName !== "IMG") return;
      const missing = document.createElement("p");
      missing.className = "missing";
      missing.textContent = "Image failed to load.";
      event.target.replaceWith(missing);
    }}, true);

    function addOptions(select, values) {{
      values.forEach((value) => {{
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        select.append(option);
      }});
    }}

    const searchInput = document.querySelector("#search");
    const regionSelect = document.querySelector("#region");
    const developmentSelect = document.querySelector("#development");
    const sortSelect = document.querySelector("#sort");
    const count = document.querySelector("#count");
    const empty = document.querySelector("#empty");

    function fillFilters() {{
      [regionSelect, developmentSelect].forEach((select) => {{
        [...select.options].slice(1).forEach((option) => option.remove());
      }});
      const regions = [...new Set(articles.map((article) => items.get(article).region))]
        .sort((a, b) => a.localeCompare(b));
      const developments = DEVELOPMENT_ORDER.filter((status) =>
        articles.some((article) => items.get(article).development === status)
      );
      addOptions(regionSelect, regions);
      addOptions(developmentSelect, developments);
    }}

    function matchesSearch(item, query) {{
      if (!query) return true;
      const q = query.toLowerCase();
      if (item.country.toLowerCase().startsWith(q)) return true;
      return item.descriptors.some((descriptor) => descriptor.toLowerCase().startsWith(q));
    }}

    function urbanValue(item, mode) {{
      if (Number.isFinite(item.urban)) return item.urban;
      return mode === "urban-asc" ? Infinity : -Infinity;
    }}

    function compare(a, b, mode) {{
      const left = items.get(a);
      const right = items.get(b);
      if (mode === "alpha-asc" || mode === "alpha-desc") {{
        const byName = left.country.localeCompare(right.country);
        const directed = mode === "alpha-asc" ? byName : -byName;
        if (directed) return directed;
      }} else if (mode === "urban-asc" || mode === "urban-desc") {{
        const byUrban = urbanValue(left, mode) - urbanValue(right, mode);
        const directed = mode === "urban-asc" ? byUrban : -byUrban;
        if (directed) return directed;
        const byName = left.country.localeCompare(right.country);
        if (byName) return byName;
      }} else if (left.index !== right.index) {{
        return left.index - right.index;
      }}
      if (left.rank !== right.rank) return left.rank - right.rank;
      return left.index - right.index;
    }}

    function apply() {{
      const query = searchInput.value.trim();
      const region = regionSelect.value;
      const development = developmentSelect.value;
      const mode = sortSelect.value;
      const ordered = articles.slice().sort((a, b) => compare(a, b, mode));
      let shown = 0;
      ordered.forEach((article) => {{
        const item = items.get(article);
        const match = matchesSearch(item, query)
          && (!region || item.region === region)
          && (!development || item.development === development);
        article.hidden = !match;
        if (match) shown += 1;
        grid.append(article);
      }});
      count.textContent = shown + " of " + articles.length + " photos";
      empty.hidden = shown !== 0;
    }}

    function indexArticles(nextArticles) {{
      articles = nextArticles;
      items = new Map();
      articles.forEach((article, index) => {{
        const urban = article.dataset.urban === "" ? NaN : Number(article.dataset.urban);
        items.set(article, {{
          index,
          country: article.dataset.country,
          rank: Number(article.dataset.rank),
          descriptors: JSON.parse(article.dataset.descriptors),
          region: article.dataset.region,
          development: article.dataset.development,
          urban
        }});
      }});
      fillFilters();
      apply();
    }}

    function parseCsv(text) {{
      const rows = [];
      let row = [];
      let field = "";
      let quoted = false;
      for (let i = 0; i < text.length; i += 1) {{
        const char = text[i];
        if (quoted) {{
          if (char === '"') {{
            if (text[i + 1] === '"') {{
              field += '"';
              i += 1;
            }} else {{
              quoted = false;
            }}
          }} else {{
            field += char;
          }}
        }} else if (char === '"') {{
          quoted = true;
        }} else if (char === ",") {{
          row.push(field);
          field = "";
        }} else if (char === "\\n") {{
          row.push(field);
          rows.push(row);
          row = [];
          field = "";
        }} else if (char !== "\\r") {{
          field += char;
        }}
      }}
      if (field || row.length) {{
        row.push(field);
        rows.push(row);
      }}
      const header = rows.shift() || [];
      return rows
        .filter((cells) => cells.length === header.length && cells.some((cell) => cell !== ""))
        .map((cells) => {{
          const record = {{}};
          header.forEach((name, index) => {{
            record[name] = cells[index];
          }});
          return record;
        }});
    }}

    function articleFrom(record) {{
      const labels = ["dominant_label_1", "dominant_label_2", "dominant_label_3"]
        .map((key) => (record[key] || "").trim())
        .filter(Boolean);
      const urban = record.actual_urban_population_pct === "" ? NaN : Number(record.actual_urban_population_pct);
      const article = document.createElement("article");
      article.dataset.country = record.country_name;
      article.dataset.rank = String(Number(record.search_rank));
      article.dataset.region = record.region;
      article.dataset.development = record.development_status;
      article.dataset.urban = Number.isFinite(urban) ? String(urban) : "";
      article.dataset.descriptors = JSON.stringify(labels);
      const image = document.createElement("img");
      image.src = record.image_url;
      image.alt = "";
      image.loading = "lazy";
      const heading = document.createElement("h2");
      heading.append(record.country_name + " ");
      const rank = document.createElement("span");
      rank.textContent = "rank " + Number(record.search_rank);
      heading.append(rank);
      const meta = document.createElement("p");
      meta.className = "meta";
      meta.append(record.region + " · " + record.development_status);
      if (Number.isFinite(urban)) {{
        meta.append(document.createElement("br"), urban.toFixed(1) + "% urban");
      }}
      const labelLine = document.createElement("p");
      labelLine.className = "labels";
      labelLine.textContent = labels.join(", ");
      const linkLine = document.createElement("p");
      const link = document.createElement("a");
      link.href = record.image_url;
      link.textContent = "Original image";
      linkLine.append(link);
      article.append(image, heading, meta, labelLine, linkLine);
      return article;
    }}

    searchInput.addEventListener("input", apply);
    regionSelect.addEventListener("change", apply);
    developmentSelect.addEventListener("change", apply);
    sortSelect.addEventListener("change", apply);
    indexArticles(articles);

    fetch(new URL("../images.csv", document.baseURI))
      .then((response) => {{
        if (!response.ok) throw new Error("Could not read images.csv");
        return response.text();
      }})
      .then((text) => {{
        const records = parseCsv(text);
        if (!records.length) return;
        const next = records.map(articleFrom);
        grid.replaceChildren(...next);
        indexArticles(next);
      }})
      .catch(() => {{}});
  </script>
</body>
</html>
"""
    SHEET_PATH.write_text(document, encoding="utf-8")
    print(f"Wrote {len(images)} cards to {SHEET_PATH}")


if __name__ == "__main__":
    main()
