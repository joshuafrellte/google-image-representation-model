# GIRD agent notes

Read `docs/Process Documentation.md` for the work log and `docs/Data Mining Research.md` for the study design. When those files disagree with this note, follow this note. Sections of the process log that name `second_pass.py` or `third_pass.py` are history. Those files are gone.

## What this is

GIRD asks whether Google Image Search's picture of a country diverges from that country's World Bank urbanization, and whether that divergence lines up with income. The universe is 193 UN members plus Kosovo (XKX), Taiwan (TWN), and Palestine (PSE). Vatican City is out. Twenty-two territories were removed.

`data/processed/images.csv` has 1,960 photos, 10 for each of 196 countries. `scenes.py` has already set `scene_category`, `has_urban_elements`, and `has_natural_landmark`. `representation_mismatch` is not set. Modeling, evaluation, and deployment have not started.

## Do not

- Run `python collect_all.py --run --refresh`. It deletes `images.csv`, `excluded.csv`, and `collection_progress.csv` and spends the SerpApi and Cloud Vision calls again.
- Run `python collect.py --refresh`, or edit `images_pilot.csv` and `excluded_pilot.csv`. The pilot is closed.
- Run `review.py` on the full sheet. It downloads every photo. Rebuild the review page with `python build_review.py`. Open `data/processed/review/index.html` as a file. It cannot fetch the CSV.
- Print `.env`, quote an API key, or add a service-account JSON. An HTTP 429 from SerpApi means that account has no searches left. Do not print the exception. The message can contain the key.
- Move rows from `excluded.csv` into `images.csv`. That review is closed. The keyword filter can drop a real photo when the page title says flag or map, or when the source is an encyclopedia. Leaving those rows out is the analysis set.
- Drop wildlife, rural scenes, or a straight portrait of a leader. A flag stays when another label describes a person, crowd, protest, or place.
- Use `actual_urban_population_pct` or `representation_mismatch` as a classifier feature. Predictors are image content only. Urbanization is the thing the image mix is compared with. The Feature Selection paragraph in the research note is stale on this point.
- Split images from the same country across train and test. The split is an 80/20 cut of countries, stratified by income tier.

## Commands

`python collect_all.py --refill` applies the filter in `collect.py` and does not search. `python collect_all.py --run --refill` searches only countries that have fewer than 10 photos. `python scenes.py` labels scenes from the three stored Vision labels and does not call an API.

Search names are the State Department short form, with these exceptions: Türkiye (the stored `country_name`; "Turkey" returns the bird), the query "Jordan country" (the sheet still says Jordan), "Republic of the Congo", Naoero, and Palestine.

## Still open

`representation_mismatch` has no cutoff. `flag_review.csv` is still a hand list, not a drop list. The two blank-label photos, Palestine and South Sudan, stay. Scene category counts from the last `scenes.py` run are in the process log.
