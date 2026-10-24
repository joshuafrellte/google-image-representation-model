"""Assign a scene to each kept photo from its Cloud Vision labels. No API calls."""

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
IMAGES_PATH = ROOT / "data" / "processed" / "images.csv"
LABEL_COLUMNS = ("dominant_label_1", "dominant_label_2", "dominant_label_3")
SCENE_COLUMNS = ("scene_category", "has_urban_elements", "has_natural_landmark")

# Words that name a built settlement or its streets. A person or a mountain does not.
CITY = {
    "Alley",
    "Arcade",
    "Bank",
    "Bazaar",
    "Bridge",
    "Building",
    "Building material",
    "City",
    "Cityscape",
    "Cobblestone",
    "Commercial building",
    "Condominium",
    "Cottage",
    "Demolition",
    "Dirt road",
    "Earthquake",
    "Eco hotel",
    "Estate",
    "Facade",
    "Fountain",
    "Headquarters",
    "High-rise building",
    "Highway",
    "Hill station",
    "Home",
    "Hotel",
    "House",
    "Hut",
    "Human settlement",
    "Intersection",
    "Lighthouse",
    "Marina",
    "Market",
    "Metropolis",
    "Metropolitan area",
    "Mill",
    "Mixed-use",
    "Mode of transport",
    "Neighbourhood",
    "Pedestrian",
    "Pier",
    "Pollution",
    "Port",
    "Public space",
    "Pueblo",
    "Residential area",
    "Resort",
    "Resort town",
    "Retail",
    "Road",
    "Road surface",
    "Roof",
    "Rubble",
    "Siding",
    "Skyscraper",
    "Sports venue",
    "Stadium",
    "Stairs",
    "Street",
    "Street light",
    "Suburb",
    "Swimming pool",
    "Thatching",
    "Town",
    "Town square",
    "Traffic",
    "Traffic congestion",
    "Urban area",
    "Urban design",
    "Village",
    "Wall",
    "Wind farm",
    "Windmill",
    "Window",
}

# Water, land, plants, and animals. A temple or a crowd is not on this list.
NATURE = {
    "Aeolian landform",
    "African elephant",
    "Agriculture",
    "Alpaca",
    "Archipelago",
    "Aurora",
    "Badlands",
    "Baobab",
    "Beach",
    "Bedrock",
    "Black rhinoceros",
    "Blossom",
    "Boat",
    "Body of water",
    "Botanical garden",
    "Branch",
    "Butte",
    "Camel",
    "Camelids",
    "Canal",
    "Carnivores",
    "Cave",
    "Channel",
    "Cheetah",
    "Cliff",
    "Coast",
    "Coastal and oceanic landforms",
    "Coral",
    "Cumulus",
    "Deer",
    "Desert",
    "Dune",
    "Ecoregion",
    "Elephant",
    "Erg",
    "Extinct volcano",
    "Felidae",
    "Fell",
    "Field",
    "Flower",
    "Flowering plant",
    "Forest",
    "Garden",
    "Landscaping",
    "Geological formation",
    "Geology",
    "Giraffe",
    "Giraffids",
    "Glacial landform",
    "Glacier",
    "Grass",
    "Grassland",
    "Groundcover",
    "Herd",
    "Highland",
    "Hill",
    "Horse",
    "Ice",
    "Impact crater",
    "Indian elephant",
    "Island",
    "Islet",
    "Jungle",
    "Kayak",
    "Lake",
    "Landscape",
    "Larch",
    "Leaf",
    "Lemurs",
    "Lion",
    "Llama",
    "Meadow",
    "Meteorological phenomenon",
    "Mountain",
    "Mountain range",
    "Mountainous landforms",
    "Natural environment",
    "Natural landscape",
    "Natural material",
    "Nature",
    "Ocean",
    "Oasis",
    "Outcrop",
    "Palm trees",
    "Petal",
    "Plant community",
    "Plantation",
    "Plants",
    "Plateau",
    "Primate",
    "Rainbow",
    "Reservoir",
    "Rhinoceros",
    "Rock",
    "Rural area",
    "Safari",
    "Sand",
    "Savanna",
    "Sea",
    "Shore",
    "Shrubland",
    "Snow",
    "Soil",
    "Spruce-fir forests",
    "Steppe",
    "Stream",
    "Tarn",
    "Terrain",
    "Terrestrial animal",
    "Tree",
    "Tropics",
    "Trunk",
    "Underground lake",
    "Underwater",
    "Valley",
    "Vegetation",
    "Vertebrate",
    "Volcanic landform",
    "Wadi",
    "Water",
    "Water resources",
    "Watercourse",
    "Watercraft",
    "Waterfall",
    "Waterway",
    "Wetland",
    "Wilderness",
    "Wildlife",
    "Woody plant",
    "Working animal",
    "Zebra",
    "atmospheric phenomenon",
    "geological phenomenon",
}

# A built place kept for worship, memory, or ruin, rather than as a settlement.
LANDMARK = {
    "Arch",
    "Archaeological site",
    "Architecture",
    "Caravanserai",
    "Castle",
    "Chinese architecture",
    "Church",
    "Classical architecture",
    "Clock tower",
    "Column",
    "Convent",
    "Dome",
    "Finial",
    "Fortification",
    "Hindu Temple",
    "Historic site",
    "Holy places",
    "Japanese architecture",
    "Landmark",
    "Medieval architecture",
    "Megalith",
    "Memorial",
    "Monastery",
    "Monument",
    "Mosque",
    "Pagoda",
    "Palace",
    "Place of worship",
    "Pyramid",
    "Religious Item",
    "Ruins",
    "Sculpture",
    "Spire",
    "Statue",
    "Steeple",
    "Stupa",
    "Temple",
    "Tower",
    "Triumphal arch",
    "Turret",
    "Wonders of the World",
    "World Heritage Site",
    "Château",
}

# A person, a crowd, dress, food, or a ceremony.
CULTURE = {
    "Army",
    "Art",
    "Audience",
    "Backpack",
    "Bag",
    "Barechestedness",
    "Beard",
    "Blazer",
    "Cap",
    "Child",
    "Clothing",
    "Collar",
    "Costume",
    "Crowd",
    "Customer",
    "Dress",
    "Dress shirt",
    "Drum",
    "Entertainment",
    "Event",
    "Eye",
    "Face",
    "Facial expression",
    "Finger",
    "Facial hair",
    "Fashion",
    "Flag",
    "Flag of the United States",
    "Food",
    "Footwear",
    "Forehead",
    "Formal wear",
    "Fur clothing",
    "Glasses",
    "Hat",
    "Head",
    "Headgear",
    "Human body",
    "Ingredient",
    "Jeans",
    "Jersey",
    "Jewellery",
    "Leg",
    "Luggage & bags",
    "Military",
    "Military Person",
    "Military camouflage",
    "Military organization",
    "Military uniform",
    "Marines",
    "Moustache",
    "Muscle",
    "Musical instrument",
    "Natural foods",
    "Neck",
    "Necklace",
    "Necktie",
    "Nose",
    "Official",
    "Outerwear",
    "People",
    "People in nature",
    "Performing Arts",
    "Player",
    "Pottery",
    "Produce",
    "Protest",
    "Public event",
    "Scarf",
    "Shirt",
    "Smile",
    "Soldier",
    "Speech",
    "Spokesperson",
    "Standing",
    "Suit",
    "Sun hat",
    "Swimsuit",
    "T-shirt",
    "Team",
    "Textile",
    "Tradition",
    "Tribe",
    "Trousers",
    "Undergarment",
    "Uniform",
    "Walking",
    "White-collar worker",
    "Woolen",
    "Workwear",
    "Youth",
}

SCENE_OF = {}
for scene, words in (
    ("City", CITY),
    ("Nature", NATURE),
    ("Landmark", LANDMARK),
    ("Culture/People", CULTURE),
):
    overlap = set(SCENE_OF).intersection(words)
    if overlap:
        raise RuntimeError(f"{scene} repeats {sorted(overlap)}")
    for word in words:
        SCENE_OF[word] = scene

NATURAL_OR_LANDMARK = NATURE | LANDMARK


def present_labels(row):
    labels = []
    for column in LABEL_COLUMNS:
        value = row[column]
        if pd.isna(value):
            continue
        text = str(value).strip()
        if text:
            labels.append(text)
    return labels


def scene_category(labels):
    if not labels:
        return ""
    for label in labels:
        scene = SCENE_OF.get(label)
        if scene:
            return scene
    return "Other"


def flag(labels, matches):
    if not labels:
        return ""
    return "True" if matches else "False"


def assign(images):
    frame = images.copy()
    labels = frame.apply(present_labels, axis=1)
    frame["scene_category"] = labels.map(scene_category)
    frame["has_urban_elements"] = [
        flag(words, any(word in CITY for word in words)) for words in labels
    ]
    frame["has_natural_landmark"] = [
        flag(words, any(word in NATURAL_OR_LANDMARK for word in words)) for words in labels
    ]
    return frame


def other_labels(images):
    counts = {}
    for _, row in images.iterrows():
        words = present_labels(row)
        if scene_category(words) != "Other":
            continue
        for word in words:
            if word not in SCENE_OF:
                counts[word] = counts.get(word, 0) + 1
    return counts


def main():
    parser = argparse.ArgumentParser(description="Derive scene fields from Vision labels.")
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print scene counts and labels that fell through to Other. Do not write.",
    )
    args = parser.parse_args()
    images = pd.read_csv(IMAGES_PATH)
    assigned = assign(images)
    counts = assigned["scene_category"].replace("", "(blank)").value_counts()
    print(counts.to_string())
    missed = other_labels(images)
    if missed:
        print("Labels on Other photos that are not on a scene list:")
        for word, count in sorted(missed.items(), key=lambda item: (-item[1], item[0])):
            print(f"  {count}\t{word}")
    else:
        print("No unlisted label remains on an Other photo.")
    if args.report:
        return
    assigned.to_csv(IMAGES_PATH, index=False, encoding="utf-8")
    print(f"Wrote scene fields for {len(assigned)} photos to {IMAGES_PATH}")


if __name__ == "__main__":
    main()
