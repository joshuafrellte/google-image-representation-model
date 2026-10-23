# **Dataset and Research Objectives Proposal** 

_Country Visual Representation vs. Reality: A 2026 Study of Urbanization-Representation Mismatch in Google Image Search_ 

## **Introduction** 

Google Image Search functions as a primary, often unquestioned, visual reference for how people around the world picture countries they have never visited. A casual search for a wealthy nation such as Germany or Japan typically returns images dominated by skylines, modern infrastructure, and urban landmarks. A search for a lower-income nation, by contrast, frequently surfaces imagery centered on nature, rural life, cultural artifacts, or a single iconic landmark, regardless of that country's actual level of urban development. This pattern raises a question with real social consequences: does the visual representation of a country in search results reflect its actual characteristics, or does it reflect a systematic pattern that diverges from reality? 

This distinction matters because search-engine imagery is not a neutral mirror of the world. It is the product of what content exists online, what gets indexed, and how ranking systems surface that content. If wealthier nations are consistently shown through their cities while poorer nations are consistently reduced to nature or heritage imagery, independent of their true urbanization levels, then search results may be reinforcing outdated or inaccurate stereotypes about entire regions of the world, shaping perception at a scale few other media formats can match. 

**Research Problem.** The naive framing of this issue, that richer countries are shown as more urban because they are more urbanized, is not by itself a meaningful research question: it may simply restate a real, unremarkable economic fact rather than reveal anything about search-engine behavior. A more precise problem, and the one this study addresses, is whether a country's actual urbanization level (independent of its income classification) is faithfully reflected in its image search representation, or whether representation systematically diverges from that reality in ways correlated with income. 

**Research Gap.** Prior work has documented related forms of wealth-correlated visual bias in adjacent domains; for example, Huang et al. (2025, EMNLP) introduced the FairLocator benchmark and found that AI vision models perform substantially worse at geolocating images from less economically developed and less densely populated regions. That work, however, evaluates a model's ability to identify where a photo was taken, not what a search engine chooses to display when a country is queried by name. To date, no study has directly examined whether Google Image Search's representation of a country aligns with that country's actual urbanization data at scale, across a large, systematically sampled set of nations. This study addresses that gap. 

#### **Research Objectives.** 

_General Objective:_ To determine whether a country's image representation in Google Image Search results (urban/city vs. nature/cultural/landmark imagery) diverges from its actual level of urbanization, and whether this divergence is systematically related to the country's income classification, using classification techniques on image-derived content features. 

#### _Specific Objectives:_ 

1. To conduct exploratory data analysis on the dataset, summarizing feature distributions, relationships, and data-quality issues. 

2. To evaluate the effects of different missing-value treatment techniques on model performance. 

3. To evaluate the effects of different feature encoding and scaling techniques on model performance. 

4. To determine the best-performing combination of preprocessing technique and classification algorithm. 

5. To compare model performance when predicting a four-tier income classification versus a binary-collapsed target. 

6. To identify which image content types are most predictive of income classification. 

7. To identify specific countries whose image representation most diverges from their actual urbanization level. 

This study does not claim to establish that any single mechanism, such as Google's ranking algorithm, causes any disparity found. It aims instead to measure, characterize, and document the disparity itself, providing an evidentiary basis for further investigation into its causes. 

## **Methodology** 

This study follows the CRISP-DM (Cross-Industry Standard Process for Data Mining) methodology, organized into six phases. 

### **1. Business Understanding** 

The business problem, reframed for a research context, is to determine whether Google Image Search's representation of countries introduces a measurable representational disparity relative to those countries' actual urbanization levels, and whether that disparity correlates with income classification. The data mining goal that operationalizes this problem is a classification task: predicting a country's income tier from features derived from the content of its search-result images, then comparing those predictions and the underlying image content against independently sourced, ground-truth urbanization data. Success is defined not by achieving high predictive accuracy for its own sake, but by using the trained model's behavior, specifically, which features it relies on and where its implied expectations diverge from reality, as an instrument for identifying and characterizing representational disparity. The study's intended output is threefold: (1) a quantified relationship between image content and income classification, (2) a set of specific countries flagged for high representational mismatch, and (3) a simple prototype through which these findings can be explored. 

### **2. Data Understanding** 

**Dataset.** The Global Image Representation Dataset (GIRD) consists of one record per image, collected for 196 countries (193 UN member states plus Kosovo, Taiwan, and Palestine; Vatican City is excluded due to insufficient World Bank data coverage). The World Bank classification list also includes territories, dependencies, and constituent economies, such as Bermuda, the Cayman Islands, and Hong Kong SAR; those records are filtered out and are not counted among the 196. Ten images are retained per country after filtering, yielding approximately 1,960 image records, well above the 500-record minimum. 

**Attributes.** Each record includes: country_name (the State Department short-form name used as the Google Images query), world_bank_name (the retained World Bank label), iso_code, region, image_url, search_rank, raw_search_rank, development_status (four-tier World Bank income group), income_status_binary (Low income and Lower middle income collapsed together, versus Upper middle income and High income), actual_urban_population_pct (ground-truth urbanization level), dominant_label_1/2/3 (raw Vision API content labels), scene_category (derived: City, Nature, Landmark, Culture/People, Other), has_urban_elements, has_natural_landmark, and representation_mismatch (a derived flag comparing observed representation against expected representation given actual urbanization). 

**Data Sources.** Images and associated metadata are retrieved via SerpApi's Google Images API. Image content labels are generated via the Google Cloud Vision API. Income classification is sourced from the World Bank's Country and Lending Groups dataset. Actual urbanization level is sourced from the World Bank's Urban Population (% of total population) indicator. 

**Initial Exploratory Data Analysis.** Prior to modeling, the dataset will be examined through: (1) descriptive statistics summarizing the distribution of scene_category across regions, income tiers, and urbanization levels; (2) visualizations (bar charts, box plots, and scatter plots) examining the relationship between actual_urban_population_pct and observed scene content; and (3) an audit for missing values, ambiguous or multi-label images, and countries that yielded fewer than the 

target number of usable images after filtering, which may indicate collection or filtering issues requiring attention before modeling proceeds. 

### **3. Data Preparation** 

**Data Cleaning.** One filter decides whether a search result is kept, and every excluded result is logged. Before Cloud Vision, the title, source, and image address drop flags, coats of arms, emblems, maps, locators, encyclopedia thumbnails, and SVG files. An image address is a map when it contains the word map, including when an underscore or hyphen is glued to it, or when it contains `bbcmp_`, `country_profile`, or `harita`, even if Vision later describes the picture as scenery. After labeling, a photo is dropped when any label is Map, Atlas, Advertising, Graphic design, Hoodie, Film, Fictional character, Fungus, Macro photography, or Guinea pig, when every label is a flag word or those words plus Wind, or when the URL is on the reviewed collision list. A flag stays when another label describes a person, crowd, protest, or place. Photographs of places, people, wildlife, and landscape stay. A second crop of the same National Geographic file is dropped. Blank-label rows are listed for review rather than dropped. Countries left under 10 are filled from the next unused results with that same filter. `images.csv` has 1,960 photos, 10 per country. A browser failure to display the remote URL does not drop a row that Vision has already labeled.

**Country universe.** Blank rows and aggregate groups in the World Bank files, such as World and regional totals, are dropped before the territory filter. Urbanization is the 2025 value of indicator SP.URB.TOTL.IN.ZS. Taiwan remains among the 196 and has no urbanization value in the World Bank file.

**Search names.** Each Google Images query uses the U.S. Department of State short-form country name. The department reserves the short form for ordinary reference and the long form for formal diplomatic use (5 FAH-1 H-1021, https://fam.state.gov/FAM/05FAH01/05FAH011020.html). The names are taken from the Independent States in the World list (https://www.state.gov/independent-states-in-the-world), using the local file IndependentStates_Dependencies_INRGGI_08102026.csv verified 10 August 2026. World Bank labels such as "Korea, Rep." and "Venezuela, RB" are administrative abbreviations, so they are retained as `world_bank_name` and are not sent to the search. Kosovo is matched from the State Department code XKS to the World Bank code XKX. Palestine is not on the independent-states list, so its query is Palestine. The short forms "Korea, South", "Korea, North", "Gambia, The", "Bahamas, The", and "Micronesia, Federated States of" are reordered into ordinary word order. The Republic of the Congo is queried as "Republic of the Congo" rather than "Congo", because the source note limits that short form to this country and an unqualified Congo query mostly returns the Democratic Republic. The 10 August 2026 short form for NRU is Naoero, so the query is Naoero. The World Bank file used that same spelling; `world_bank_name` for that row is stored as Nauru. The Turkey query is Türkiye, and `country_name` is stored as Türkiye, because the short form Turkey returns the bird. The Jordan query is "Jordan country", because the short form returns the shoe; the displayed name stays Jordan. 

**Missing-Value Treatment.** Three techniques will be compared: listwise deletion, mode imputation (for categorical features), and a dedicated "no-label" placeholder category, evaluated for their effect on downstream model performance rather than applied by default. 

**Outlier Handling.** Because the dataset's primary numeric feature, actual_urban_population_pct, is a bounded percentage, conventional statistical outlier removal is not expected to be necessary; instead, unusual cases (e.g., very small, highly urbanized city-states) will be examined during EDA and explicitly retained if they reflect genuine, informative data points rather than data-quality errors, consistent with the study's mismatch-detection goal. 

**Encoding.** Categorical features (dominant_label_1/2/3, scene_category, region) will be encoded via one-hot encoding and, for comparison, label encoding, with their effects on model performance evaluated directly rather than assumed. 

**Normalization/Standardization.** The effects of no scaling, normalization, and standardization on actual_urban_population_pct and any other numeric features will be compared across algorithms, since tree-based methods (Decision Tree, Random Forest) are scale-invariant while Logistic Regression is not. 

**Feature Selection.** All engineered features (has_urban_elements, has_natural_landmark, representation_mismatch) are retained for initial modeling; feature importance analysis (Evaluation phase) will subsequently be used to assess which features contribute meaningfully to classification performance. 

### **4. Modeling** 

**Algorithms.** Three classification algorithms are used: Decision Tree, Random Forest, and Logistic Regression (multinomial, for the four-tier target). 

**Target Variables.** Two target framings are modeled and compared: the primary four-tier development_status classification, and the alternative binary-collapsed income_status_binary target. 

**Data Partitioning.** The dataset will be split 80% training / 20% testing, stratified by income tier to preserve class proportions in both sets. Because records are grouped by country (10 images per country), the split will be performed at the country level, not the image level, so that images from the same country never appear in both the training and test sets; this prevents the model 

from learning country-specific artifacts rather than genuine content patterns. Within the training set, 5-fold cross-validation will be used for hyperparameter selection and to obtain a more stable estimate of model performance before final evaluation on the held-out test set. 

**Experimental Procedure.** For each combination of preprocessing choice (missing-value treatment × encoding × scaling) and algorithm, a model is trained and validated via cross-validation. The best-performing preprocessing/algorithm combination for each target framing (four-tier and binary) is then evaluated once on the held-out test set to avoid overfitting to validation performance. 

### **5. Evaluation** 

**Performance Metrics.** Accuracy, Precision (macro-averaged across income tiers), Recall (macro-averaged), and F1-score (macro-averaged) are used to evaluate classification performance across both target framings. 

**Evaluation Procedure.** Models are compared primarily by macro-averaged F1-score, since this metric penalizes poor performance on any single class rather than allowing strong performance on majority classes to mask weak performance on minority classes, which is important given the dataset's income tiers are unlikely to be perfectly balanced. A confusion matrix is produced for the best-performing model in each target framing to examine whether misclassifications cluster near adjacent income-tier boundaries (e.g., Upper-middle vs. Lower-middle), which would suggest the model is capturing a genuine graded signal rather than noise. 

**Mismatch Evaluation.** Beyond standard classification metrics, the study separately evaluates representational mismatch: for each country, the model's predicted income tier and the observed scene_category distribution are compared against actual_urban_population_pct. Countries where observed representation diverges substantially from what actual urbanization would predict are flagged and ranked, forming the basis for the study's qualitative findings on representational disparity. This evaluation is interpretive rather than purely statistical, and findings are reported as evidence of disparity, not proof of a specific causal mechanism. 

### **6. Deployment** 

The study's outputs will be presented through a simple interactive prototype, a lightweight dashboard or lookup tool that allows a user to select or search for a country and view: its actual urbanization percentage, its World Bank income classification, its observed scene_category breakdown from collected images, and a computed representational mismatch score. This prototype serves primarily as a demonstration and communication tool for the study's findings rather than a production system, allowing reviewers to explore specific country-level results (e.g., the cases identified in Objective 7) interactively rather than only through static tables in the report. Alongside the prototype, the study's core deliverables include: a ranked list of the most representationally mismatched countries, a summary of which image content features were most predictive of income classification, and a discussion of the study's limitations regarding causal claims, intended to inform further research into the underlying mechanisms of representational disparity in search-engine imagery. 

