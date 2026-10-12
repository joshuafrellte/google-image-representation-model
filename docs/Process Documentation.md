# GIRD process notes

This note follows the study from raw data to deployment. Substeps, problems, solutions, and remarks are recorded only for work completed in this session. Later phases are named so the path stays visible.

## 1. Business understanding

Determine whether Google Image Search's representation of a country diverges from that country's actual urbanization, and whether the divergence is related to income classification. The operational task is to classify income from image-content features, then compare those results with World Bank urbanization. The intended outputs are the measured relationship, a ranked list of mismatched countries, and a lookup prototype.

## 2. Data understanding

Describe the 196-country image set, its attributes, and the quality of the country ground truth before modeling.

### Completed this session

**Substeps.** `CLASS_2026_07_15.csv` supplies the income group, region, and ISO code. `API_SP.URB.TOTL.IN.ZS_DS2_en_excel_v2_2441.csv` supplies urban population as a percent of total population. The country table uses the 2025 value. `main.ipynb` summarizes class counts and draws the income bar chart, the income box plot, and the region box plot.

**Problem.** The income file is not valid UTF-8, so a plain read fails on accented names. Taiwan is one of the 196 countries and has no row in the urbanization file.

**Solution.** The income file is read as Windows-1252. The urbanization file is read as UTF-8. Taiwan stays in the country table with a blank percent and is left out of the urbanization charts.

**Remarks.** The image-content part of the planned EDA has not been run, because no image file has been collected. After the 196-country filter, the income counts are 25 low, 47 lower-middle, 59 upper-middle, and 65 high. The 2025 median urban shares are 34.5, 50.9, 65.4, and 80.0 percent. The ranges overlap: Liechtenstein, a high-income country, is 14.6 percent urban.

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

### Image collection

**Substeps.** `collect.py` is written to search Malawi, Kenya, Brazil, and Japan through SerpApi, drop flags, maps, coats of arms, and encyclopedia results, keep 10 photos, and send those photos to Cloud Vision for three labels. `.gitignore` excludes `.env`.

**Problem.** Google blocked creation of a service-account key on this account, so there is no JSON credential file. The API key that replaced it reached Cloud Vision, and Vision then refused the call: the billing account is closed and is not in good standing until a one-time payment of at least US$30 is credited. The pilot did not produce `data/processed/images_pilot.csv`.

**Solution.** Vision is called with `GOOGLE_API_KEY` from `.env`. The key is not printed. The billing block is not solved. The account has to show an active status, project `1065567207889` has to be linked to it, and `python collect.py` has to be run again. SerpApi did accept the Malawi search, so that half of the pilot does not need to be rebuilt. The photo filter and the label step have not been checked on real results.

## 4. Modeling

Not started. The planned comparison is Decision Tree, Random Forest, and multinomial Logistic Regression, for the four-tier income target and the binary target, with the preprocessing grid and a country-level 80/20 split.

## 5. Evaluation

Not started. The planned measures are macro-averaged precision, recall, and F1, plus a confusion matrix for the best model in each target, and a country ranking by representational mismatch.

## 6. Deployment

Not started. The planned prototype is a country lookup showing urbanization, income group, scene mix, and mismatch score, alongside the ranked mismatch list and the most predictive image features.
