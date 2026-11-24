"""
Recommendation engine for the Smart Agriculture Product Recommendation System.

Approach (content-based filtering):
1. Each product is turned into one text made of its crops, stages, problems
   and description.
2. TF-IDF converts these texts into numeric vectors.
3. The farmer's selection (crop, stage, problem) is converted into a vector too.
4. Cosine similarity ranks products against the farmer's selection.
5. A basic filter keeps only products that match BOTH the crop and the problem.
"""

from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATASET_PATH = Path(__file__).parent / "dataset" / "products.csv"
TOP_N = 3

# Used only to show growth stages in a natural order in the dropdown.
STAGE_ORDER = [
    "Land Preparation",
    "Sowing",
    "Seedling",
    "Vegetative",
    "Flowering",
    "Fruit or Grain Development",
]

REQUIRED_COLUMNS = {
    "product_id", "product_name", "category", "suitable_crops",
    "suitable_stages", "target_problems", "description", "manufacturer", "source",
}
LIST_COLUMNS = ["suitable_crops", "suitable_stages", "target_problems"]


def _split_values(value):
    """Turn 'Wheat|Rice|Maize' into ['Wheat', 'Rice', 'Maize']."""
    return [item.strip() for item in str(value).split("|") if item.strip()]


def _token(text):
    """Turn 'Low Nitrogen' into 'low_nitrogen' so TF-IDF treats it as one word."""
    return text.strip().lower().replace(" ", "_")


def _tokens(items):
    return " ".join(_token(item) for item in items)


class ProductRecommender:
    """Loads the dataset once, trains TF-IDF once, then answers many requests."""

    def __init__(self, csv_path=DATASET_PATH):
        df = pd.read_csv(csv_path, dtype=str).fillna("")

        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Dataset is missing columns: {sorted(missing)}")
        if df.empty:
            raise ValueError("Dataset is empty.")

        # Split the pipe-separated fields into Python lists.
        for column in LIST_COLUMNS:
            df[column + "_list"] = df[column].apply(_split_values)

        # One text per product: crops + stages + problems + description.
        df["features"] = [self._product_text(row) for _, row in df.iterrows()]
        self.df = df

        # Train TF-IDF once. The matrix has one row per product.
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(self.df["features"])

        # Values used for dropdowns and input validation.
        self.crops = self._unique_values("suitable_crops_list")
        self.problems = self._unique_values("target_problems_list")
        stages = set(self._unique_values("suitable_stages_list"))
        self.stages = [s for s in STAGE_ORDER if s in stages] + sorted(stages - set(STAGE_ORDER))

    # ----------------------------- helpers -----------------------------

    @staticmethod
    def _product_text(row):
        return " ".join([
            _tokens(row["suitable_crops_list"]),
            _tokens(row["suitable_stages_list"]),
            _tokens(row["target_problems_list"]),
            row["description"],
        ])

    def _unique_values(self, column):
        return sorted({value for items in self.df[column] for value in items})

    @staticmethod
    def _resolve(value, options, label):
        """Match user input to a known option (ignores case and extra spaces)."""
        lookup = {option.lower(): option for option in options}
        key = str(value).strip().lower()
        if key not in lookup:
            raise ValueError(f"Unknown {label}: '{value}'. Choose one of: {', '.join(options)}")
        return lookup[key]

    @staticmethod
    def _build_reason(row, crop, stage, problem):
        """Plain-language explanation built from the actual matches."""
        reason = f"Suitable for {crop} and listed for the problem '{problem}'."
        if stage in row["suitable_stages_list"]:
            reason += f" It fits the {stage} stage."
        else:
            listed = ", ".join(row["suitable_stages_list"])
            reason += f" Note: it is mainly listed for other stages ({listed}), not {stage}."
        return reason

    # ----------------------------- public API -----------------------------

    def get_options(self):
        """Values for the three dropdowns."""
        return {"crops": self.crops, "stages": self.stages, "problems": self.problems}

    def get_product(self, product_id):
        """Full details of one product, or None if the ID does not exist."""
        match = self.df[self.df["product_id"].str.upper() == str(product_id).strip().upper()]
        if match.empty:
            return None
        row = match.iloc[0]
        return {
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            "category": row["category"],
            "suitable_crops": row["suitable_crops_list"],
            "suitable_stages": row["suitable_stages_list"],
            "target_problems": row["target_problems_list"],
            "description": row["description"],
            "manufacturer": row["manufacturer"],
            "source": row["source"],
        }

    def recommend(self, crop, stage, problem):
        """Return up to 3 products ranked by similarity, with reasons."""
        crop = self._resolve(crop, self.crops, "crop")
        stage = self._resolve(stage, self.stages, "growth stage")
        problem = self._resolve(problem, self.problems, "problem")

        # Step 1 - basic filter: product must match the crop AND the problem.
        candidates = [
            i for i, (crops, problems) in enumerate(
                zip(self.df["suitable_crops_list"], self.df["target_problems_list"])
            )
            if crop in crops and problem in problems
        ]
        if not candidates:
            return {
                "recommendations": [],
                "message": (
                    f"No products in the sample dataset match {crop} with the problem "
                    f"'{problem}'. Try a different problem or crop."
                ),
            }

        # Step 2 - turn the farmer's selection into a TF-IDF vector.
        query = f"{_token(crop)} {_token(stage)} {_token(problem)} {problem.lower()}"
        query_vector = self.vectorizer.transform([query])

        # Step 3 - cosine similarity against the filtered products only.
        scores = cosine_similarity(query_vector, self.matrix[candidates]).ravel()

        # Step 4 - rank (highest score first, product_id breaks ties) and keep top 3.
        ranked = sorted(
            zip(candidates, scores),
            key=lambda pair: (-pair[1], self.df.at[pair[0], "product_id"]),
        )[:TOP_N]

        recommendations = []
        for index, score in ranked:
            row = self.df.iloc[index]
            recommendations.append({
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "category": row["category"],
                "description": row["description"],
                "relevance_score": round(float(score) * 100, 1),
                "reason": self._build_reason(row, crop, stage, problem),
            })

        count = len(recommendations)
        if count < TOP_N:
            message = (
                f"Only {count} suitable product{'s' if count != 1 else ''} found "
                "for this combination in the sample dataset."
            )
        else:
            message = f"Showing the top {TOP_N} matching products."
        return {"recommendations": recommendations, "message": message}


if __name__ == "__main__":
    # Quick manual test: python recommender.py
    recommender = ProductRecommender()
    test_cases = [
        ("Wheat", "Vegetative", "Low Nitrogen"),                # several matches
        ("Tomato", "Flowering", "Aphid and Sucking Pests"),     # exactly 3 matches
        ("Rice", "Seedling", "Potassium Deficiency"),           # 1 match, stage mismatch
        ("Wheat", "Flowering", "Blight"),                       # no match
        ("Banana", "Sowing", "Blight"),                         # invalid crop
    ]
    for crop, stage, problem in test_cases:
        print(f"\n=== {crop} | {stage} | {problem} ===")
        try:
            result = recommender.recommend(crop, stage, problem)
        except ValueError as error:
            print("Error:", error)
            continue
        print(result["message"])
        for rank, item in enumerate(result["recommendations"], start=1):
            print(f"  {rank}. {item['product_name']} ({item['relevance_score']}%)")
            print(f"     {item['reason']}")