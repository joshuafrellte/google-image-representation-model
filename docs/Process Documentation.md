# GIRD process notes

This note follows the study from raw data to deployment. Substeps, problems, solutions, and remarks are recorded only for work completed so far. Later phases are named so the path stays visible.

## 1. Business understanding

Determine whether Google Image Search's representation of a country diverges from that country's actual urbanization, and whether the divergence is related to income classification. The operational task is to classify income from image-content features, then compare those results with World Bank urbanization. The intended outputs are the measured relationship, a ranked list of mismatched countries, and a lookup prototype.

## 2. Data understanding

Describe the 196-country image set, its attributes, and the quality of the country ground truth before modeling.

### Completed this session

**Substeps.** `CLASS_2026_07_15.csv` supplies the income group, region, and ISO code. `API_SP.URB.TOTL.IN.ZS_DS2_en_excel_v2_2441.csv` supplies urban population as a percent of total population. The country table uses the 2025 value. `main.ipynb` summarizes class counts and draws the income bar chart, the income box plot, and the region box plot.

**Problem.** The income file is not valid UTF-8, so a plain read fails on accented names. Taiwan is one of the 196 countries and has no row in the urbanization file.

**Solution.** The income file is read as Windows-1252. The urbanization file is read as UTF-8. Taiwan stays in the country table with a blank percent and is left out of the urbanization charts.

**Remarks.** A four-country image pilot now exists. The image-content part of the planned EDA has not been run on the full country set. After the 196-country filter, the income counts are 25 low, 47 lower-middle, 59 upper-middle, and 65 high. The 2025 median urban shares are 34.5, 50.9, 65.4, and 80.0 percent. The ranges overlap: Liechtenstein, a high-income country, is 14.6 percent urban.

## 3. Data preparation

Build the country table the image rows will join to, then collect and clean the search images.

### Country universe

**Substeps.** Blank rows and aggregate groups, such as World and regional totals, were dropped. The kept set is the 193 UN member states plus Kosovo, Taiwan, and Palestine. `income_status_binary` collapses Low income with Lower middle income, and Upper middle income with High income. The result is `data/processed/countries.csv`.

**Problem.** The World Bank classification file is wider than the study. Besides the 196 participants it contains aggregate groups and 22 territories, dependencies, and constituent economies, including Bermuda, the Cayman Islands, Hong Kong SAR, and Macao SAR. Vatican City was already absent.

**Solution.** Those aggregate rows and the 22 territories were removed by ISO code before the urbanization join. The notebook checks that the dropped codes are exactly those 22 and that 196 countries remain.

**Remarks.** All 22 removed rows were high income. Removing them changed the high-income urbanization median from 81.3 percent, on the unfiltered World Bank list, to 80.0 percent.

### Short-form country names

**Substeps.** `IndependentStates_Dependencies_INRGGI_08102026.csv`, the U.S. Department of State list verified 10 August 2026, was read as Windows-1252 so accented letters survived. Rows with status Independent were kept, plus Taiwan. The file was joined to the country table on the three-letter code. The short-form name was written to `country_name`, which is the Google Images query. The World Bank label was kept in `world_bank_name`.

The rule and the list are public:

- https://fam.state.gov/FAM/05FAH01/05FAH011020.html
- https://www.state.gov/independent-states-in-the-world

**Problem.** A direct join does not cover every study country, and some published short forms would search badly. Kosovo is `XKS` in the State Department file and `XKX` in the World Bank file. Palestine is not on the independent-states list. "Korea, South", "Korea, North", "Gambia, The", "Bahamas, The", and "Micronesia, Federated States of" are written backwards for a search box. The short form "Congo" is defined as the Republic of the Congo only, but a bare Congo query mostly returns the Democratic Republic. The 10 August 2026 short form for NRU is Naoero, the Nauruan name, which is also the spelling in the World Bank file.

**Solution.** Kosovo's code is matched to `XKX`. Palestine's query is Palestine. The five inverted short forms are reordered to South Korea, North Korea, The Gambia, The Bahamas, and Federated States of Micronesia. The Republic of the Congo is queried as "Republic of the Congo". Naoero is kept as the query, because that is the cited short form. `world_bank_name` for that row is stored as Nauru.

### Project layout

**Substeps.** Downloaded sources were moved to `data/raw`: the World Bank income file, the urbanization file, and `IndependentStates_Dependencies_INRGGI_08102026.csv`. Derived tables go in `data/processed`. The research note and this note are in `docs`. `main.ipynb` and `collect.py` stay in the project root. Both scripts were pointed at the new folders, and the notebook was run again. It still writes 196 rows to `data/processed/countries.csv`.

### Image collection

**Substeps.** `collect.py` searches Malawi, Kenya, Brazil, and Japan through SerpApi, one country from each income group. It drops a result when the title, source, or URL matches flag, coat of arms, emblem, map, locator, encyclopedia, or `.svg`, keeps 10 photos, and sends those photos to Cloud Vision label detection for three labels. The kept rows are `data/processed/images_pilot.csv`. The dropped rows are `data/processed/excluded_pilot.csv`. `.gitignore` excludes `.env`.

The pilot run kept 10 photos for each country. It excluded 5 Malawi results, 3 Kenya results, 4 Brazil results, and 0 Japan results: 40 kept rows and 12 excluded rows.

**Problem.** Google blocked creation of a service-account key, so there is no JSON credential file. The first API key reached Cloud Vision, and Vision then refused the call because billing account `01383E-E18BE8-6ECF90` was closed and not in good standing. Reopen stayed disabled until a one-time payment of US$30 was credited. A new billing account was created during setup. The account already there was equally new, so the extra account did not change the payment requirement, and it was not used. The health-check list on the billing account was budget alerts, extra viewers, extra administrators, and an unlinked project. Those notices were not the payment. The original project, number `1065567207889`, had Cloud Vision enabled and no linked billing account.

**Solution.** The US$30 payment was made on 23 October 2026 and appears as a credit on **My GIRD Vision Billing Account**. After that account showed Open, a new Cloud project was created for GIRD, number `759289031035`, and linked to it. Cloud Vision was enabled there, and a new API key restricted to Cloud Vision replaced `GOOGLE_API_KEY` in `.env`. The key is not printed. `python collect.py` then completed the four-country pilot.

**Remarks.** The keyword filter runs before Cloud Vision. The three labels describe what is visible in the photo. They are stored as `dominant_label_1`, `dominant_label_2`, and `dominant_label_3`, and they are not used to decide whether the photo shows that country. A kept row means Google ranked it for the country name and the title or URL passed the keyword filter. The same filter can drop a photograph when the page title contains "Map" or "Flag". A links-only reading of `images_pilot.csv` also glues the following columns onto the URL, so the pilot photos were checked from local copies instead.

### Pilot review sheet

**Substeps.** `review.py` reads `data/processed/images_pilot.csv` and makes no SerpApi or Cloud Vision calls. It saves each photo under `data/processed/review/images` and writes `data/processed/review/index.html`. Each card shows the local photo, the country, the search rank, the labels, and a link that contains only the image URL. All 40 photos were saved. Empty labels are left blank.

**Remarks.** All 40 local photos were reviewed by hand and accepted.

## 4. Modeling

Not started. The planned comparison is Decision Tree, Random Forest, and multinomial Logistic Regression, for the four-tier income target and the binary target, with the preprocessing grid and a country-level 80/20 split.

## 5. Evaluation

Not started. The planned measures are macro-averaged precision, recall, and F1, plus a confusion matrix for the best model in each target, and a country ranking by representational mismatch.

## 6. Deployment

Not started. The planned prototype is a country lookup showing urbanization, income group, scene mix, and mismatch score, alongside the ranked mismatch list and the most predictive image features.
