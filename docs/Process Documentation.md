# GIRD process notes

This note follows the study from raw data to deployment. Substeps, problems, solutions, and remarks are recorded only for work completed so far. Later phases are named so the path stays visible.

## 1. Business understanding

Determine whether Google Image Search's representation of a country diverges from that country's actual urbanization, and whether the divergence is related to income classification. The operational task is to classify income from image-content features, then compare those results with World Bank urbanization. The intended outputs are the measured relationship, a ranked list of mismatched countries, and a lookup prototype.

## 2. Data understanding

Describe the 196-country image set, its attributes, and the quality of the country ground truth before modeling.

### Completed this session

**Substeps.** `CLASS_2026_07_15.csv` supplies the income group, region, and ISO code. `API_SP.URB.TOTL.IN.ZS_DS2_en_excel_v2_2441.csv` supplies urban population as a percent of total population. The country table uses the 2025 value. `main.ipynb` summarizes class counts and draws the income bar chart, the income box plot, and the region box plot.

**Problem.** The income file is not valid UTF-8, so a plain read fails on accented names. Taiwan is one of the 196 countries and has no row in the urbanization file.

**Solution.** The income file is read as Windows-1252. The urbanization file is read as UTF-8. The World Bank extract has no Taiwan value, and the World Bank API returns none for indicator SP.URB.TOTL.IN.ZS. That indicator cites the UN Population Division's World Urbanization Prospects, national definitions. Table A3 of the 2025 edition gives China, Taiwan Province of China a 2025 proportion urban of 78.9 percent. That figure is written to the Taiwan row of `countries.csv` and the 10 Taiwan rows of `images.csv`, with `urban_year` 2025, and the country-building cell applies it after the join so a rerun does not wipe it. The same publication's Degree of Urbanization cities share for Taiwan in 2025 is 78.1 percent, and that series is not used. The filled percent lets Taiwan appear in the urbanization charts and in the later mismatch comparison. It is not a World Bank row. It is not a classifier feature, and it is not being held back for a later modeling stage.

**Remarks.** The image table has 10 photos for each of the 196 countries. The four-country pilot file is unchanged. The image-content part of the planned EDA has been run: the scene-mix section of `main.ipynb` counts scenes by income tier and by region, plots City share against the 2025 urban percent, charts the three incomplete-label groups, and charts the 331 multi-scene photos. After the 196-country filter, the income counts are 25 low, 47 lower-middle, 59 upper-middle, and 65 high. With Taiwan's UN figure included, the 2025 median urban shares are 34.5, 50.9, 65.4, and 79.7 percent. The high-income median on the World Bank rows alone, before that fill, was 80.0 percent. The ranges overlap: Liechtenstein, a high-income country, is 14.6 percent urban.

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

**Remarks.** The keyword filter runs before Cloud Vision. The three labels describe what is visible in the photo. They are stored as `dominant_label_1`, `dominant_label_2`, and `dominant_label_3`. Label detection is requested with `maxResults` 3. Vision returns those labels in descending confidence order. The code stores that order and does not sort it again. `dominant_label_1` is the strongest of the three, and `dominant_label_3` is the weakest of the three. The confidence scores are not saved. A blank later column means Vision returned fewer than three labels. `scene_category` then walks column 1, then 2, then 3, and keeps the first word that sits on a scene list. On the first pass they are not used to accept or reject a row. A kept row means Google ranked it for the country name and the title or URL passed the keyword filter. The same filter can drop a photograph when the page title contains "Map" or "Flag". An underscore hides the word, so a URL such as `country_profile_map` still gets through. A links-only reading of `images_pilot.csv` also glues the following columns onto the URL, so the pilot photos were checked from local copies instead.

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

### Excluded photographs left out

**Substeps.** The full-run review sheet can show the 1,960 kept photos or only the excluded rows. A pass through the excluded sheet found photographs of cities, coasts, animals, and people whose logged reason was encyclopedia, flag, or map. The checked files include the Ouagadougou street, the Central African Republic bongos, the Lake Chad shore, Monrovia, Lake Malawi, a Mali wedding, Maputo, the Pyongyang skyline, the Meroë pyramids, the Banjul port, the Dhaka night view, the Kampala street, an Anjouan coast, and the Cairo aerial. The Benin City aerial is logged under Benin and shows Benin City, Nigeria. On 23 October 2026 three of the addresses were sent to Cloud Vision. Abidjan (`Abidjan-Cote-Ivoire.jpg`) returned Sky, Skyscraper, and Urban area. The Dhaka night view returned City, Urban area, and Building. The Angkor address `https://whc.unesco.org/document/197586/t=xl` failed again: Vision could not fetch the URL, and the download was an HTTP 403 HTML page. The `vision failed` rows were not rerun as a batch. Most are Instagram or Facebook crawler links, or files that already failed both the URL request and the byte upload.

**Problem.** The keyword filter reads the page title, the source, and the image address as one string, and it runs before Cloud Vision. A Britannica title that contains Flag or Map, or a Wikipedia or Britannica source, can drop a photograph the later rules would keep. Several of those files have a better raw search rank than photos that stayed. Reviewing the excluded sheet by hand is slow, and a restore list would keep growing. Three responses were considered. One was to delete the keyword filter and recollect all 196 countries. One was to move each confirmed photograph into `images.csv` and drop that country's current last photo so the country stayed at 10. One was to leave `excluded.csv` unchanged.

**Solution.** `excluded.csv` stays as logged. No excluded photograph was moved into `images.csv`. The keyword filter and the Vision rules define the 1,960-photo analysis set.

**Remarks.** Two human decisions were compared, and they are not the same kind of decision. Removing a map, a flag graphic, a film still, a name collision, or a duplicate says what counts as a photograph of the queried country. That rule was applied to every country, and each open slot was filled by the next Google result that passed the same rule. Restoring a photograph because it looks like a key or high-ranking picture of the country would let the group choose the representation the study is measuring. Wildlife and rural scenes were left in the kept set for that reason: dropping them would leave only pictures that already look urban. Deleting the keyword filter would also change the 10 photos. Vision still misses maps it describes as scenery, and a flag stays when another label describes a person, crowd, protest, or place, so the early ranks would change. A full recollect would spend the SerpApi and Cloud Vision quota again. The limitation is that the keyword rule can drop a high-ranking photograph when the article title contains Flag or Map, or when the source is an encyclopedia. Small file size was not the cause. In the checked set, the Wikipedia thumbnails at 250px and 500px are the only small files.

### Scene categories

**Substeps.** `scenes.py` reads `data/processed/images.csv` and makes no SerpApi or Cloud Vision calls. It walks `dominant_label_1`, then `dominant_label_2`, then `dominant_label_3`. Blue, Sky, Daytime, Cloud, Happiness, and the other words that are not a scene are skipped. The first remaining label on a scene list sets `scene_category`. `has_urban_elements` is true when any label is a built settlement. `has_natural_landmark` is true when any label is nature or a landmark. A person or a crowd does not set that flag. Labels that existed and matched nothing became Other. One pass then added the scene words that had fallen through: Facial expression, Finger, Pottery, and Landscaping. The lists were left fixed after that pass. `main.ipynb` counts scenes by income tier and by region, plots the share of City photos against the 2025 urban percentage, and counts blank-label photos and photos whose labels name more than one scene.

**Problem.** The research note names the five scenes and does not say which label wins when a photo matches more than one. `representation_mismatch` is also named, and the note gives no cutoff for it.

**Solution.** The tie-break is Vision's own order. That order is the confidence rank recorded at collection: `dominant_label_1` is the strongest of the three returned labels, and `dominant_label_3` is the weakest. The scores themselves are not saved. A waterfront whose first real label is Water stays Nature, and `has_urban_elements` still records a later City label. `representation_mismatch` is left unset. The run wrote 1,031 Nature, 473 City, 235 Culture/People, 180 Landmark, 39 Other, and 2 blank. The blank rows are the Palestine and South Sudan photos already listed in `blank_label_review.csv`. The 39 Other photos are labeled only with color, time of day, mood, a vehicle, or a word such as Tourist attraction.

**Remarks.** `excluded.csv` was not read. No model was fit. Twenty-nine photos have an empty label slot and stay in the 1,960-photo sheet. The 2 with no labels remain in `blank_label_review.csv`. The 27 with a later slot empty are in `missing_label_review.csv`. The incomplete-label bar charts only those three groups: 18 missing only label 3, 9 missing labels 2 and 3, and 2 with no labels. The title carries the 1,931 photos that have all three labels. Which missing-value treatment is used is still a modeling comparison, not a drop. Words such as Blue, Sky, Daytime, Cloud, and Happiness are skipped when a scene is chosen. The photo stays. No chart was added for those words. A photo whose labels never name a scene remains Other in the existing scene charts. On the current sheet, 842 photos have at least one skipped word, and 449 of those still get a scene from a later label. The reason each kept word is on its list, and the reason each skipped word is not, is in the next section. The horizontal bar covers the 331 photos whose labels name more than one scene. Label order is ignored in that chart, so Nature then City counts with City then Nature. `scene_category` still uses Vision's own order. The seven bars are Nature and City 159, City and Landmark 48, Culture/People and Landmark 41, Nature and Landmark 34, Culture/People and City 24, three scenes 16, and Culture/People and Nature 9.

Modeling has since finished, and its settings and scores are in the Modeling section below.

### Why each word is kept or skipped

The four lists stay in `scenes.py`. A skipped word is any Vision label on the current sheet that is not in `CITY`, `NATURE`, `LANDMARK`, or `CULTURE`. There is no separate skip file. A skipped word does not remove the photo. Of the 842 photos that carry at least one skipped word, 449 still receive a scene from a later label. The most common skipped words are Blue (222), Tourist attraction (131), Daytime (97), Sky (76), Cloud (54), Green (37), Summer (31), Bird's-eye view (28), Happiness (24), and Horizon (24).

**City.** The word names a built settlement or its streets. A person or a mountain does not.

The settlement itself: `City`, `Cityscape`, `Estate`, `Hill station`, `Human settlement`, `Metropolis`, `Metropolitan area`, `Neighbourhood`, `Pueblo`, `Residential area`, `Resort town`, `Suburb`, `Town`, `Urban area`, `Urban design`, `Village`.

A building, or a part of one: `Bank`, `Building`, `Building material`, `Commercial building`, `Condominium`, `Cottage`, `Eco hotel`, `Facade`, `Headquarters`, `High-rise building`, `Home`, `Hotel`, `House`, `Hut`, `Mill`, `Mixed-use`, `Resort`, `Roof`, `Siding`, `Skyscraper`, `Thatching`, `Wall`, `Window`, `Wind farm`, `Windmill`.

A street, or movement on a street: `Alley`, `Arcade`, `Bridge`, `Cobblestone`, `Dirt road`, `Highway`, `Intersection`, `Mode of transport`, `Pedestrian`, `Road`, `Road surface`, `Stairs`, `Street`, `Street light`, `Town square`, `Traffic`, `Traffic congestion`.

A built place that serves the settlement: `Bazaar`, `Fountain`, `Lighthouse`, `Marina`, `Market`, `Pier`, `Port`, `Public space`, `Retail`, `Sports venue`, `Stadium`, `Swimming pool`.

A settlement Vision describes as damaged, which is still a built place rather than land or a person: `Demolition`, `Earthquake`, `Pollution`, `Rubble`.

**Nature.** The word names water, land, plants, or animals. A temple or a crowd does not.

Water, or a craft on it: `Archipelago`, `Beach`, `Body of water`, `Boat`, `Canal`, `Channel`, `Coast`, `Coastal and oceanic landforms`, `Coral`, `Island`, `Islet`, `Kayak`, `Lake`, `Ocean`, `Oasis`, `Reservoir`, `Sea`, `Shore`, `Stream`, `Tarn`, `Underground lake`, `Underwater`, `Water`, `Water resources`, `Watercourse`, `Watercraft`, `Waterfall`, `Waterway`, `Wetland`.

Land, ice, or a named phenomenon of the land and sky: `Aeolian landform`, `Aurora`, `Badlands`, `Bedrock`, `Butte`, `Cave`, `Cliff`, `Cumulus`, `Desert`, `Dune`, `Erg`, `Extinct volcano`, `Fell`, `Geological formation`, `Geology`, `geological phenomenon`, `Glacial landform`, `Glacier`, `Highland`, `Hill`, `Ice`, `Impact crater`, `Meteorological phenomenon`, `Mountain`, `Mountain range`, `Mountainous landforms`, `Outcrop`, `Plateau`, `Rainbow`, `Rock`, `Sand`, `Snow`, `Soil`, `Terrain`, `Valley`, `Volcanic landform`, `Wadi`, `atmospheric phenomenon`.

Plants, or the ground they cover: `Agriculture`, `Baobab`, `Blossom`, `Botanical garden`, `Branch`, `Ecoregion`, `Field`, `Flower`, `Flowering plant`, `Forest`, `Garden`, `Grass`, `Grassland`, `Groundcover`, `Jungle`, `Landscape`, `Landscaping`, `Larch`, `Leaf`, `Meadow`, `Natural environment`, `Natural landscape`, `Natural material`, `Nature`, `Palm trees`, `Petal`, `Plant community`, `Plantation`, `Plants`, `Rural area`, `Savanna`, `Shrubland`, `Spruce-fir forests`, `Steppe`, `Tree`, `Tropics`, `Trunk`, `Vegetation`, `Wilderness`, `Woody plant`.

Animals: `African elephant`, `Alpaca`, `Black rhinoceros`, `Camel`, `Camelids`, `Carnivores`, `Cheetah`, `Deer`, `Elephant`, `Felidae`, `Giraffe`, `Giraffids`, `Herd`, `Horse`, `Indian elephant`, `Lemurs`, `Lion`, `Llama`, `Primate`, `Rhinoceros`, `Safari`, `Terrestrial animal`, `Vertebrate`, `Wildlife`, `Working animal`, `Zebra`.

**Landmark.** The word names a built place kept for worship, memory, or ruin, rather than as a settlement.

Worship: `Church`, `Convent`, `Hindu Temple`, `Holy places`, `Monastery`, `Mosque`, `Pagoda`, `Place of worship`, `Religious Item`, `Stupa`, `Temple`.

Memory or a monument: `Arch`, `Clock tower`, `Column`, `Landmark`, `Memorial`, `Monument`, `Sculpture`, `Statue`, `Triumphal arch`, `Wonders of the World`, `World Heritage Site`.

A ruin or a historic site: `Archaeological site`, `Caravanserai`, `Historic site`, `Megalith`, `Pyramid`, `Ruins`.

A kept building, rather than a street of houses: `Architecture`, `Castle`, `Chinese architecture`, `Château`, `Classical architecture`, `Dome`, `Finial`, `Fortification`, `Japanese architecture`, `Medieval architecture`, `Palace`, `Spire`, `Steeple`, `Tower`, `Turret`.

**Culture/People.** The word names a person, a crowd, dress, food, or a ceremony.

A person, a body, or a crowd: `Army`, `Audience`, `Barechestedness`, `Beard`, `Child`, `Crowd`, `Customer`, `Eye`, `Face`, `Facial expression`, `Facial hair`, `Finger`, `Forehead`, `Head`, `Human body`, `Leg`, `Marines`, `Military`, `Military Person`, `Military organization`, `Moustache`, `Muscle`, `Neck`, `Nose`, `Official`, `People`, `People in nature`, `Player`, `Smile`, `Soldier`, `Speech`, `Spokesperson`, `Standing`, `Team`, `Walking`, `White-collar worker`, `Youth`.

Dress, or something worn or carried: `Backpack`, `Bag`, `Blazer`, `Cap`, `Clothing`, `Collar`, `Costume`, `Dress`, `Dress shirt`, `Fashion`, `Footwear`, `Formal wear`, `Fur clothing`, `Glasses`, `Hat`, `Headgear`, `Jeans`, `Jersey`, `Jewellery`, `Luggage & bags`, `Military camouflage`, `Military uniform`, `Necklace`, `Necktie`, `Outerwear`, `Scarf`, `Shirt`, `Suit`, `Sun hat`, `Swimsuit`, `T-shirt`, `Textile`, `Trousers`, `Undergarment`, `Uniform`, `Woolen`, `Workwear`.

Food: `Food`, `Ingredient`, `Natural foods`, `Produce`.

A ceremony, or a cultural object: `Art`, `Drum`, `Entertainment`, `Event`, `Flag`, `Flag of the United States`, `Musical instrument`, `Performing Arts`, `Pottery`, `Protest`, `Public event`, `Tradition`, `Tribe`. A flag names the symbol people display. It stays with Culture/People because the cleaning rule already keeps a flag only when another label describes a person, crowd, protest, or place.

**Skipped.** These 135 words are on the current sheet and on none of the four lists. Each fails the four rules for the reason named with its group.

Color, which does not say what the photo is of: `Blue`, `Brown`, `Camouflage`, `Green`, `Orange`, `Paint`, `Purple`, `Red`, `Yellow`.

Time of day: `Afterglow`, `Daylighting`, `Daytime`, `Dusk`, `Evening`, `Morning`, `Night`, `Sun`, `Sunlight`, `Sunrise`, `Sunset`.

Season: `Spring`, `Summer`, `Winter`.

Mood or leisure, which describes the viewer rather than the place or the person: `Adventure`, `Beauty`, `Fun`, `Happiness`, `Holiday`, `Leisure`, `Love`, `Outdoor recreation`, `Recreation`, `Travel`, `Vacation`.

Viewpoint: `Aerial photography`, `Bird's-eye view`.

Sky, light, or a condition that is not water, land, plants, or animals. `Cumulus`, `Aurora`, `Rainbow`, and the named meteorological words stay on the Nature list. These do not: `Cloud`, `Fire`, `Flame`, `Fluid`, `Heat`, `Horizon`, `Reflection`, `Shadow`, `Sky`, `Smoke`, `Wind`.

A general word that does not say whether the photo is a settlement, a landscape, a monument, or a person: `Ancient history`, `Community`, `Government`, `History`, `Organization`, `Photograph`, `Stock photography`, `Symbol`, `Tourist attraction`.

A vehicle or a part of one. A vehicle is not a settlement, a landscape, a monument, or a person: `Automotive Exterior`, `Bicycle`, `Bicycle handlebar`, `Bicycle wheel`, `Bus`, `Cable car`, `Car`, `Classic car`, `Combat vehicle`, `Double-decker bus`, `Family car`, `Full-size car`, `Helicopter`, `Land vehicle`, `Motor vehicle`, `Motorcycle`, `pole`, `Rail transport`, `Rotorcraft`, `Sport utility vehicle`, `Tire`, `Train`, `Transport`, `Truck`, `Van`, `Vehicle`, `Wheel`.

A ship or its cargo. `Boat`, `Kayak`, and `Watercraft` stay on the Nature list because they name the craft on the water. These name equipment or a hull class: `Boats and boating--Equipment and supplies`, `Container ship`, `Panamax`, `Shipping container`.

Tack, rather than the animal. `Horse` stays on the Nature list: `Bridle`, `Horse tack`.

A weapon or protective gear. The person and the uniform are already on the Culture/People list: `Air gun`, `Firearm`, `Gun`, `Helmet`, `Machine gun`, `Missile`, `Personal protective equipment`, `Rocket`, `Shotgun`.

An object that is not dress, food, a person, or a ceremony. `Flower`, `Petal`, and `Blossom` stay on the Nature list. `Fur clothing` stays on Culture/People. `Religious Item` and `Sculpture` stay on Landmark: `Audio equipment`, `Basket`, `Christmas decoration`, `Clock`, `Cob`, `Cone`, `Cross`, `Fan`, `Ferris wheel`, `Floristry`, `Flower bouquet`, `Flowerpot`, `Fur`, `Furniture`, `Horn`, `Lighting`, `List of nonbuilding structure types`, `Microphone`, `Outdoor furniture`, `Podium`, `Sign`, `Table`, `Tableware`, `Tent`, `Triangle`.

An activity or a discipline, rather than a scene: `Aerospace Engineering`, `Camping`, `Engineering`, `Underwater diving`. `Underwater` itself stays on the Nature list.

A compound or a proper name. The lists keep the general word and were not extended to every compound: `Bridge` is kept and these bridge types are not, `Wall` is kept and `Stone wall` is not, `Village` is kept and `Mountain Village` is not, `House` is kept and `Mansion` is not, `Mountain` is kept and `Alps` is not, `Cobblestone` is kept and `Flagstone` is not. The words left off are `Alps`, `Arch bridge`, `Cable-stayed bridge`, `Flagstone`, `Mansion`, `Mountain Village`, `Stone wall`, `Tied-arch bridge`.

### Where the side lists are

The pilot tables are now in `data/processed/pilot/`. The drop log and the hand lists, `excluded.csv`, `flag_review.csv`, `blank_label_review.csv`, and `missing_label_review.csv`, are now in `data/processed/review/` next to the review page. `countries.csv`, `images.csv`, and `collection_progress.csv` stay in `data/processed/`. Model scores are in `data/processed/modeling/model_results.csv`. The collection write-ups above keep the paths they were written with.

## 4. Modeling

**Substeps.** `main.ipynb` predicts income from `dominant_label_1`, `dominant_label_2`, `dominant_label_3`, `scene_category`, `has_urban_elements`, and `has_natural_landmark`. The urban percent, region, and `representation_mismatch` are not features. One 80/20 split of countries, stratified on the four-tier income group with `random_state=42`, is shared by both targets. It holds out 40 countries: 5 low, 10 lower-middle, 12 upper-middle, and 13 high. The other 156 countries, 1,560 photos, are the training set. Inside those countries, 5-fold grouped cross-validation selects the setting. The folds are built on the four-tier label and reused for the binary target.

Stage 1 uses default hyperparameters. It crosses listwise deletion, most-frequent imputation, and a `no-label` placeholder with one-hot or ordinal encoding and with no scaling, min-max, or standardization. Each of those 18 preprocessors is fit for a decision tree, a random forest of 100 trees, and multinomial logistic regression: 54 settings for each target, 108 in all. Stage 2 keeps the winning preprocessor of each algorithm. It tunes tree `max_depth` in {4, 8, unlimited} and `min_samples_leaf` in {1, 5}, forest `max_depth` in {8, unlimited} and `min_samples_leaf` in {1, 5}, and logistic `C` in {0.1, 1, 10}. The best setting for each target is refit on the training countries and scored once on the held-out countries. The country counts at each cut, the five training groups, and the derivation of the 108 and 26 settings are in the Modeling section of the research note. Scores, the chosen settings, and training permutation importance are in `data/processed/modeling/model_results.csv`.

**Problem.** Listwise deletion removes a photo when any of the six predictors is blank. Twenty-nine photos are in that state. The other two treatments keep them: most-frequent imputation fills a blank from the training fold, and the placeholder writes `no-label` in a blank label or scene and 0 in a blank flag. Fifteen logistic fits did not converge within 1,000 iterations. Those fits stayed in the comparison.

**Solution.** The four-tier winner is a decision tree with the `no-label` placeholder, one-hot encoding, and no scaling, at the default depth and leaf size (`max_depth` unlimited, `min_samples_leaf` 1). Its cross-validation macro F1 is 0.336 and its cross-validation accuracy is 0.351. On the 400 held-out photos the macro F1 is 0.341, precision 0.346, recall 0.346, and accuracy is 0.388. The binary winner is logistic regression with most-frequent imputation, one-hot encoding, no scaling, and `C` 1. Its cross-validation macro F1 is 0.630 and its cross-validation accuracy is 0.694. On the same 400 photos the macro F1 is 0.599, precision 0.648, recall 0.603, and accuracy is 0.670. Neither winner uses listwise deletion, so none of the 29 blank-predictor photos are removed from those two scores. On the training photos, permuting a column drops the four-tier macro F1 most for `dominant_label_1` (0.408), then `dominant_label_2` (0.353), `dominant_label_3` (0.257), and `scene_category` (0.186). The two flags move it by about 0.03. For the binary model the three labels move the training macro F1 by 0.110, 0.074, and 0.055, and the scene and the flags move it by about 0.002.

**Remarks.** The confusion matrices are in the modeling section of `main.ipynb`. The first scoring run recorded macro F1, macro precision, and macro recall. Accuracy was already named as a metric in the research note, so the modeling cell was run again and accuracy was added for every setting. The winners stayed the ones chosen by mean macro F1. The mismatch ranking has not been started. The research note was updated in three places. Its exploratory-analysis paragraph now names the charts that were run. Its missing-value paragraph now names the comparison that was run. Its encoding paragraphs now say ordinal encoding.

## 5. Evaluation

The classification scores and the two confusion matrices are recorded in the modeling section. The confusion matrices and the importance chart stay in the notebook until they are exported as image files. Whether the four-tier mistakes fall on neighboring income tiers has not been written, and that reading goes with the mismatch write-up. The country ranking by representational mismatch has not been started. `representation_mismatch` is still unset.

## 6. Deployment

Not started. The planned prototype is a country lookup showing urbanization, income group, scene mix, and mismatch score, alongside the ranked mismatch list and the most predictive image features.
