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

**Remarks.** The image table has 10 photos for each of the 196 countries. The four-country pilot file is unchanged. The image-content part of the planned EDA has not been run. After the 196-country filter, the income counts are 25 low, 47 lower-middle, 59 upper-middle, and 65 high. The 2025 median urban shares are 34.5, 50.9, 65.4, and 80.0 percent. The ranges overlap: Liechtenstein, a high-income country, is 14.6 percent urban.

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

**Remarks.** The keyword filter runs before Cloud Vision. The three labels describe what is visible in the photo. They are stored as `dominant_label_1`, `dominant_label_2`, and `dominant_label_3`. On the first pass they are not used to accept or reject a row. A kept row means Google ranked it for the country name and the title or URL passed the keyword filter. The same filter can drop a photograph when the page title contains "Map" or "Flag". An underscore hides the word, so a URL such as `country_profile_map` still gets through. A links-only reading of `images_pilot.csv` also glues the following columns onto the URL, so the pilot photos were checked from local copies instead.

### Pilot review sheet

**Substeps.** `review.py` reads `data/processed/images_pilot.csv` and makes no SerpApi or Cloud Vision calls. It saves each photo under `data/processed/review/images` and writes `data/processed/review/index.html`. Each card shows the local photo, the country, the search rank, the labels, and a link that contains only the image URL. All 40 photos were saved. Empty labels are left blank.

**Remarks.** All 40 local photos were reviewed by hand and accepted.

### Full image collection

**Substeps.** `collect_all.py` reads `data/processed/countries.csv` and searches all 196 countries with the same SerpApi query, keyword filter, and Cloud Vision labeling as `collect.py`. It keeps 10 photos per country. Kept rows are appended to `data/processed/images.csv`. Dropped rows are appended to `data/processed/excluded.csv`. `data/processed/collection_progress.csv` records a country only after that country's search finishes. The columns in `images.csv` match the pilot file. The pilot files are not read or written.

`python collect_all.py` prints how many countries remain and makes no API calls. `python collect_all.py --run` collects the countries that are not yet in the progress file. `python collect_all.py --run --refresh` deletes the three full-run files and collects all 196 countries again.

The run on 23 October 2026 kept 10 photos for every country: 1,960 image rows and 929 excluded rows. The exclusions were 331 encyclopedia, 262 map, 248 flag, 87 vision failed, and 1 coat of arms. The wall-clock time was 5:17 PM to 6:52 PM, about 1 hour 35 minutes.

**Problem.** `collect.py` cannot do this run. It searches only Malawi, Kenya, Brazil, and Japan, and it stops when `images_pilot.csv` already exists. The first full attempt ran for 9 minutes and stopped with a connection error while collecting Somalia, after 18 countries had been saved. Somalia was not written to the progress file. A network failure also spends that country's SerpApi and Cloud Vision calls again when the country is collected later. Separately, 31 kept photos have all three labels blank, and 140 have fewer than three. An empty label list is stored as blank fields and the photo is still kept, because the label request itself did not fail. The 87 vision-failed rows are the ones excluded.

**Solution.** The full run writes `images.csv`, `excluded.csv`, and `collection_progress.csv`, so the pilot rows stay intact. After the connection error, `collect_all.py` retries a network failure three times, waiting 5, then 10, then 15 seconds. The resumed command was `python -u collect_all.py --run`. It skipped the 18 finished countries, retried Somalia once, and finished the rest in about 1 hour 26 minutes. A later `--run` skips every country already listed in the progress file.

**Remarks.** Each finished country is appended before the next search starts. `--refresh` spends the SerpApi and Cloud Vision calls a second time. `scene_category`, `has_urban_elements`, `has_natural_landmark`, and `representation_mismatch` are not in `images.csv`.

### Second-pass exclusions

**Substeps.** `second_pass.py --run` reads `images.csv`. Photographs of places, people, wildlife, and landscape stay. A row is dropped when any Cloud Vision label is Map, Atlas, Advertising, Graphic design, Hoodie, Film, Fictional character, Fungus, Macro photography, or Guinea pig. The drop is logged in `excluded.csv` with reason `vision label:` plus that label. `search_rank` is reassigned among the photos that remain. Countries left under 10 are filled from later Google Image results, skipping URLs already kept or excluded, and the same label rule applies to the replacements. Flag rows are listed in `data/processed/flag_review.csv` and are not dropped.

The run dropped 132 photos. That left 73 countries short. Every one of those countries was filled back to 10. `images.csv` again has 1,960 photos, 10 per country, and none of the documented labels remain. The exclusion log contains 160 `vision label` rows, including replacements that were themselves maps or name collisions. Thirty Flag rows remain for a hand check.

**Problem.** The title filter missed maps whose page title never says "map," including Global R2P graphics and BBC country-profile files. An underscore hides the word in addresses such as `country_profile_map`. The same sheet also contained hoodies, posters, a movie poster for Togo, petri dishes for Niger, and a guinea pig for Guinea. A gray "Image failed to load" card is a browser block on the remote URL. Cloud Vision has already labeled that row.

**Solution.** Wildlife, landscape, and city photographs were kept. The documented labels were excluded and the short countries were filled with `python second_pass.py --run`. Flag was not blanket-dropped. A failed browser load was not used as a drop rule.

**Remarks.** Removing the animals and deserts would leave only the pictures that already look urban. Scene categories still wait. The 30 Flag rows in `flag_review.csv` have not been reviewed.

### Third-pass exclusions

**Substeps.** `third_pass.py` reads `images.csv`. A row is dropped when its address contains `bbcmp_`, `country_profile_map`, or the word map even if an underscore or hyphen is glued to it. A row is also dropped when every Cloud Vision label is a flag word (`Flag`, `Flags`, `Flag Day`, or a label beginning `Flag of`) or the only other label is Wind. Identified collisions are dropped by URL: the Niger mold diagrams and river graphic, the guinea-fowl and Papua New Guinea photos filed under Guinea, the film stills from *A United Kingdom*, the Brunei YouTube composite, and the Uganda flag drawing. A Republic of the Congo row is dropped when that same URL is already kept for the Democratic Republic of the Congo. `search_rank` is reassigned. Rows with no labels, and the BBC country-profile files that already have a scene label, are written to `data/processed/blank_label_review.csv` and are not dropped. `flag_review.csv` is rewritten to the flag rows that remain. `python third_pass.py --run` searches only the countries left under 10, and a replacement is rejected by the same address rule and flag-subject rule.

The drop on 23 October 2026 removed 51 photos: 25 map addresses, 8 film stills, 6 Niger collisions, 4 Guinea collisions, 4 flag-subject rows, 2 Republic of the Congo duplicates, 1 YouTube composite, and 1 clip-art flag. Finland and Tonga matched a BBC country-profile address and were kept, because Vision had already labeled them Snow, and Ocean. The refill then added 29 photos and brought 17 countries back to 10. It also returned two more guinea-fowl photos and two more Democratic Republic of the Congo images under the Republic of the Congo. Those four were dropped. `images.csv` now has 1,934 photos. 182 countries have 10.

**Problem.** SerpApi returned HTTP 429, "Your account has run out of searches," while filling Indonesia. Twelve countries had not been refilled, and the four later collision drops left two more countries short. Fourteen countries were still under 10: United Kingdom 2, Sweden 7, Guinea 8, Republic of the Congo 8, United States 8, and Brunei, Bulgaria, Guyana, Hungary, Indonesia, Iran, Libya, the Philippines, and Serbia at 9. The title filter still misses a map whose address never says map, so Ukraine's `ukraine.png`, the United States `untitled-design` map, and Belarus's `belarus-1.png` are in the blank-label list rather than dropped.

**Solution.** The drop and the partial refill were kept. `blank_label_review.csv` has 14 rows: 12 with no labels, plus Finland and Tonga. `flag_review.csv` has 27 rows. A later `python third_pass.py --run` skips every country that already has 10 photos. Wildlife, landscape, people, and a flag that shares the top labels with a person, crowd, protest, or place stay.

**Remarks.** Scene categories still wait. `--run` spends SerpApi and Cloud Vision calls for the short countries only.

### Same-rule cleanup

**Substeps.** The map test now lives in `collect.py`: the word map counts even when an underscore or hyphen is glued to it, and an image address containing `bbcmp_` or `country_profile` is a map. A scene label no longer keeps that address. The Turkey query is Türkiye. The Jordan query is "Jordan country", while the displayed country name stays Jordan. `third_pass.py` applies those rules to `images.csv`, plus the reviewed rows a rule cannot see: the Togo film dog, the Iraq collage, the Saudi Arabia illustration, and the locator maps whose addresses do not say map. The Iran news photograph stays.

The cleanup dropped 39 photos: 20 Turkey and Jordan query collisions, 11 reviewed maps, 5 map addresses, 2 edited graphics, and 1 film still. That left 1,895 photos and 33 countries short, including Türkiye and Jordan at zero.

**Problem.** The first SerpApi account had no searches left, so that short list could not be filled. A second account then filled all 33 countries back to 10. Two of the new Türkiye results were maps whose filenames use the Turkish word harita, and Guinea came back with more guinea-fowl photos plus one rodent photo. A follow-up drop briefly removed every new Türkiye and Jordan photo, because the filter treated those two country codes as collisions. That check was removed. The bird and shoe URLs stay excluded. Eight of the good Türkiye photos were put back, and the ten with the best search ranks were kept.

**Solution.** `harita` is now a map address in `collect.py`. The extra guinea-fowl and rodent URLs are named drops. `python third_pass.py --run` filled only Guinea after those drops. `images.csv` again has 1,960 photos, 10 for each of the 196 countries. `blank_label_review.csv` has 2 rows: a Palestine New Yorker photo and a South Sudan State Department photo. Vision returns no labels for the Palestine file, so that photo stays unlabeled. `flag_review.csv` has 33 rows. The Iran news photograph stays, and so do leader portraits. A later look removed the Republic of the Congo card whose labels were only Blue and Symbol, the unlabeled Guinea reddit map, the Niger ancient-sites map, and the edited United States graphics. The Statue of Liberty photograph and a Capitol crowd photograph stay. A second crop of the same National Geographic file is dropped, which removed the square Zion Canyon photo and a second Tripoli photo under Libya.

**Remarks.** Scene categories still wait. The first good Jordan set remains in `excluded.csv` because the second search already supplied 10 photos.

### One filter

**Substeps.** The Vision label list, the flag-subject rule, the reviewed URL list, the Guinea and Congo address tests, and the duplicate-crop test now live in `collect.py`. `collect_country` applies them during a search. `python collect_all.py --refill` reads `images.csv` and drops any row that filter would reject. `python collect_all.py --run --refill` searches only countries still under 10. It does not delete the sheet. `second_pass.py` and `third_pass.py` are gone.

**Problem.** A new search used to keep a photo first and only then discover that a later pass would reject it.

**Solution.** Collection and the refill use the same decision. Checked against the current sheet, the filter drops nothing: 1,960 photos, 10 per country, remain.

**Remarks.** `--run --refresh` still deletes the full-run files and spends the searches again. That is not the refill.

## 4. Modeling

Not started. The planned comparison is Decision Tree, Random Forest, and multinomial Logistic Regression, for the four-tier income target and the binary target, with the preprocessing grid and a country-level 80/20 split.

## 5. Evaluation

Not started. The planned measures are macro-averaged precision, recall, and F1, plus a confusion matrix for the best model in each target, and a country ranking by representational mismatch.

## 6. Deployment

Not started. The planned prototype is a country lookup showing urbanization, income group, scene mix, and mismatch score, alongside the ranked mismatch list and the most predictive image features.
