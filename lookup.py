"""Write the country lookup page from the ranking, the photos, and the importance rows.

The page embeds its data. Opening the file does not fetch a CSV and does not
call SerpApi or Cloud Vision. The predicted income tier is left out.
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
RANKING_PATH = ROOT / "data" / "processed" / "modeling" / "mismatch_ranking.csv"
IMAGES_PATH = ROOT / "data" / "processed" / "images.csv"
RESULTS_PATH = ROOT / "data" / "processed" / "modeling" / "model_results.csv"
PAGE_PATH = ROOT / "data" / "processed" / "lookup" / "index.html"
SCENE_ORDER = ("City", "Nature", "Landmark", "Culture/People", "Other", "blank")
TARGET_LABELS = {
    "development_status": "Four-tier decision tree",
    "income_status_binary": "Binary logistic regression",
}


def scene_name(value):
    if value is None or pd.isna(value):
        return "blank"
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return "blank"
    return text


def scene_counts(images):
    counts = {}
    for iso_code, group in images.groupby("iso_code", sort=False):
        seen = {}
        for name in group["scene_category"].map(scene_name):
            seen[name] = seen.get(name, 0) + 1
        ordered = []
        for name in SCENE_ORDER:
            if name in seen:
                ordered.append({"scene": name, "count": seen.pop(name)})
        for name in sorted(seen):
            ordered.append({"scene": name, "count": seen[name]})
        counts[iso_code] = ordered
    return counts


def number(value):
    return float(value)


def countries(ranking, images):
    counts = scene_counts(images)
    rows = []
    for record in ranking.to_dict("records"):
        iso_code = str(record["iso_code"])
        rows.append(
            {
                "country_name": str(record["country_name"]),
                "iso_code": iso_code,
                "development_status": str(record["development_status"]),
                "actual_urban_population_pct": number(record["actual_urban_population_pct"]),
                "city_share": number(record["city_share"]),
                "predicted_city_share": number(record["predicted_city_share"]),
                "signed_residual": number(record["signed_residual"]),
                "absolute_residual": number(record["absolute_residual"]),
                "rank": int(record["rank"]),
                "representation_mismatch": bool(record["representation_mismatch"]),
                "scenes": counts.get(iso_code, []),
            }
        )
    return rows


def importance_rows(results):
    importance = results.loc[results["row_type"] == "importance"]
    groups = []
    for target, rows in importance.groupby("target", sort=False):
        groups.append(
            {
                "target": str(target),
                "label": TARGET_LABELS.get(str(target), str(target)),
                "features": [
                    {"feature": str(row.feature), "drop": number(row.importance)}
                    for row in rows.itertuples(index=False)
                ],
            }
        )
    return groups


def payload(ranking, images, results):
    rows = countries(ranking, images)
    flagged = [row for row in rows if row["representation_mismatch"]]
    return {
        "countries": rows,
        "importance": importance_rows(results),
        "summary": {
            "countries": len(rows),
            "flagged": len(flagged),
            "above": sum(row["signed_residual"] > 0 for row in flagged),
            "below": sum(row["signed_residual"] < 0 for row in flagged),
        },
    }


def embed(data):
    return json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GIRD country lookup</title>
  <style>
    body { font-family: sans-serif; margin: 24px; background: #f6f6f6; color: #1a1a1a; }
    h1 { font-size: 1.4rem; margin: 0 0 8px; }
    h2 { font-size: 1.05rem; margin: 0 0 8px; }
    p { margin: 0 0 8px; }
    .summary, .note { color: #444; font-size: 0.95rem; }
    .layout { display: grid; grid-template-columns: minmax(240px, 320px) 1fr; gap: 16px; align-items: start; margin-top: 16px; }
    .panel { background: #fff; padding: 12px; }
    label { display: block; font-size: 0.75rem; color: #333; margin-bottom: 8px; }
    input { font: inherit; font-size: 0.95rem; width: 100%; box-sizing: border-box; padding: 8px 10px; border: 1px solid #ccc; border-radius: 4px; }
    #ranking { list-style: none; margin: 0; padding: 0; max-height: 70vh; overflow: auto; }
    #ranking button { font: inherit; text-align: left; width: 100%; padding: 8px; border: 0; border-bottom: 1px solid #eee; background: #fff; cursor: pointer; }
    #ranking button[aria-current="true"] { background: #1a1a1a; color: #fff; }
    #ranking .flag { color: #163; }
    #ranking button[aria-current="true"] .flag { color: #d8efe4; }
    #empty { color: #444; }
    dl { display: grid; grid-template-columns: 11rem 1fr; gap: 6px 12px; margin: 0; }
    dt { color: #444; }
    dd { margin: 0; }
    .scenes { list-style: none; margin: 0; padding: 0; }
    .scenes li { display: grid; grid-template-columns: 8.5rem 1.5rem minmax(4rem, 1fr); gap: 8px; align-items: center; margin-bottom: 4px; }
    .track { display: block; height: 8px; background: #e4e4e4; }
    .bar { display: block; height: 8px; background: #1a1a1a; }
    .importance { margin-top: 16px; }
    .models { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; padding: 4px 8px 4px 0; border-bottom: 1px solid #eee; }
    td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
    @media (max-width: 720px) {
      body { margin: 16px; }
      .layout { grid-template-columns: 1fr; }
      #ranking { max-height: 40vh; }
    }
  </style>
</head>
<body>
  <h1>GIRD country lookup</h1>
  <p class="summary" id="summary"></p>
  <div class="layout">
    <section class="panel">
      <label>
        Country
        <input id="search" type="search" placeholder="Cameroon" autocomplete="off">
      </label>
      <p id="empty" hidden>No country matches.</p>
      <ul id="ranking"></ul>
    </section>
    <section class="panel" id="detail" aria-live="polite"></section>
  </div>
  <section class="panel importance">
    <h2>Permutation importance</h2>
    <p class="note">These drops are from training photos and are not the mismatch score.</p>
    <div class="models" id="importance"></div>
  </section>
  <script>
    const payload = __PAYLOAD__;

    const search = document.querySelector("#search");
    const ranking = document.querySelector("#ranking");
    const empty = document.querySelector("#empty");
    const detail = document.querySelector("#detail");
    const summary = payload.summary;
    let selected = payload.countries[0].iso_code;

    document.querySelector("#summary").textContent =
      summary.flagged + " countries are flagged, " +
      summary.above + " above the line and " +
      summary.below + " below. The score is the signed residual.";

    function signed(value) {
      const text = value.toFixed(3);
      return value > 0 ? "+" + text : text;
    }

    function scenes(country) {
      const items = country.scenes.map((scene) => {
        const label = scene.scene === "blank" ? "Blank" : scene.scene;
        const width = scene.count * 10;
        return "<li><span>" + label + "</span><span>" + scene.count +
          "</span><span class=\\"track\\"><span class=\\"bar\\" style=\\"width:" + width + "%\\"></span></span></li>";
      }).join("");
      return "<ul class=\\"scenes\\">" + items + "</ul>";
    }

    function renderDetail() {
      const country = payload.countries.find((row) => row.iso_code === selected);
      const flag = country.representation_mismatch
        ? "Flagged. The absolute residual is at least 0.20."
        : "Not flagged. The absolute residual is under 0.20.";
      detail.innerHTML =
        "<h2>" + country.country_name + "</h2>" +
        "<dl>" +
        "<dt>Urban percent</dt><dd>" + country.actual_urban_population_pct.toFixed(1) + "%</dd>" +
        "<dt>Income group</dt><dd>" + country.development_status + "</dd>" +
        "<dt>Scene counts</dt><dd>" + scenes(country) + "</dd>" +
        "<dt>City share</dt><dd>" + country.city_share.toFixed(1) + "</dd>" +
        "<dt>Predicted City share</dt><dd>" + country.predicted_city_share.toFixed(3) + "</dd>" +
        "<dt>Signed residual</dt><dd>" + signed(country.signed_residual) + "</dd>" +
        "<dt>Mismatch</dt><dd>" + flag + "</dd>" +
        "</dl>";
    }

    function renderList() {
      const query = search.value.trim().toLowerCase();
      const shown = payload.countries.filter((country) =>
        country.country_name.toLowerCase().includes(query)
      );
      empty.hidden = shown.length > 0;
      ranking.replaceChildren(...shown.map((country) => {
        const item = document.createElement("li");
        const button = document.createElement("button");
        button.type = "button";
        if (country.iso_code === selected) button.setAttribute("aria-current", "true");
        button.addEventListener("click", () => {
          selected = country.iso_code;
          render();
        });
        const mark = country.representation_mismatch ? " <span class=\\"flag\\">flagged</span>" : "";
        button.innerHTML = country.rank + " " + country.country_name + " " + signed(country.signed_residual) + mark;
        item.append(button);
        return item;
      }));
    }

    function renderImportance() {
      const root = document.querySelector("#importance");
      root.replaceChildren(...payload.importance.map((group) => {
        const section = document.createElement("section");
        const heading = document.createElement("h2");
        heading.textContent = group.label;
        const table = document.createElement("table");
        const body = document.createElement("tbody");
        group.features.forEach((feature) => {
          const row = document.createElement("tr");
          const name = document.createElement("td");
          name.textContent = feature.feature;
          const drop = document.createElement("td");
          drop.className = "num";
          drop.textContent = signed(feature.drop);
          row.append(name, drop);
          body.append(row);
        });
        table.append(body);
        section.append(heading, table);
        return section;
      }));
    }

    function render() {
      renderList();
      renderDetail();
    }

    search.addEventListener("input", renderList);
    render();
    renderImportance();
  </script>
</body>
</html>
"""


def main():
    ranking = pd.read_csv(RANKING_PATH)
    images = pd.read_csv(IMAGES_PATH)
    results = pd.read_csv(RESULTS_PATH)
    data = payload(ranking, images, results)
    PAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PAGE_PATH.write_text(TEMPLATE.replace("__PAYLOAD__", embed(data)), encoding="utf-8")
    print(f"Wrote {data['summary']['countries']} countries to {PAGE_PATH}")


if __name__ == "__main__":
    main()
