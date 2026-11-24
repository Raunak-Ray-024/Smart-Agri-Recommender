import re

import pytest
from fastapi.testclient import TestClient

from main import app
from recommender import STAGE_ORDER, ProductRecommender

HEADER = (
    "product_id,product_name,category,suitable_crops,suitable_stages,"
    "target_problems,description,manufacturer,source\n"
)


@pytest.fixture(scope="module")
def client():
    # "with" runs the startup code, so the model is loaded.
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def recommender():
    return ProductRecommender()


# --------------------------- Basic endpoints ---------------------------

def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_options(client):
    data = client.get("/api/options").json()
    assert len(data["crops"]) == 10
    assert data["stages"] == STAGE_ORDER
    assert len(data["problems"]) >= 20


def test_cors_allows_react_origin(client):
    headers = {"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"}
    response = client.options("/api/recommend", headers=headers)
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_blocks_other_origin(client):
    headers = {"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"}
    response = client.options("/api/recommend", headers=headers)
    assert "access-control-allow-origin" not in response.headers


# --------------------------- Recommendations ---------------------------

def recommend(client, crop, stage, problem):
    return client.post("/api/recommend", json={"crop": crop, "stage": stage, "problem": problem})


def test_three_results(client):
    data = recommend(client, "Wheat", "Vegetative", "Low Nitrogen").json()
    assert data["count"] == 3
    assert "Urea" in data["recommendations"][0]["product_name"]


def test_exactly_three_matches(client):
    data = recommend(client, "Tomato", "Flowering", "Aphid and Sucking Pests").json()
    names = {item["product_name"] for item in data["recommendations"]}
    assert data["count"] == 3
    assert any("Neem" in name for name in names)
    assert any("Beauveria" in name for name in names)
    assert any("Sticky" in name for name in names)


def test_fewer_than_three_results(client):
    data = recommend(client, "Rice", "Seedling", "Potassium Deficiency").json()
    assert data["count"] == 1
    assert "MOP" in data["recommendations"][0]["product_name"]
    assert "other stages" in data["recommendations"][0]["reason"]


def test_no_match_is_not_an_error(client):
    response = recommend(client, "Wheat", "Flowering", "Blight")
    data = response.json()
    assert response.status_code == 200
    assert data["count"] == 0
    assert data["recommendations"] == []
    assert "No products" in data["message"]


def test_input_is_case_insensitive(client):
    response = recommend(client, "wheat", "vegetative", "low nitrogen")
    assert response.status_code == 200
    assert response.json()["count"] == 3


# --------------------------- Invalid input ---------------------------

@pytest.mark.parametrize("payload", [
    {"crop": "Banana", "stage": "Sowing", "problem": "Blight"},
    {"crop": "Wheat", "stage": "Harvest", "problem": "Blight"},
    {"crop": "Wheat", "stage": "Sowing", "problem": "Alien Attack"},
    {"crop": "   ", "stage": "Sowing", "problem": "Blight"},
    {"crop": "", "stage": "", "problem": ""},
    {"crop": "Wheat", "stage": "Sowing"},
    {"crop": 123, "stage": "Sowing", "problem": "Blight"},
    {"crop": "<script>alert(1)</script>", "stage": "Sowing", "problem": "Blight"},
    {},
])
def test_invalid_payloads_return_422(client, payload):
    assert client.post("/api/recommend", json=payload).status_code == 422


def test_non_json_body_returns_422(client):
    response = client.post(
        "/api/recommend", content="not json", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422


# --------------------------- Product details ---------------------------

def test_product_found(client):
    response = client.get("/api/products/P001")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data["suitable_crops"], list)
    assert data["source"]


def test_product_id_is_case_insensitive(client):
    assert client.get("/api/products/p001").status_code == 200


def test_product_not_found(client):
    response = client.get("/api/products/P999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


# --------------------------- Whole-model checks ---------------------------

def test_all_combinations_are_valid(recommender):
    options = recommender.get_options()
    matched = 0
    for crop in options["crops"]:
        for stage in options["stages"]:
            for problem in options["problems"]:
                result = recommender.recommend(crop, stage, problem)
                items = result["recommendations"]
                assert len(items) <= 3
                scores = [item["relevance_score"] for item in items]
                assert scores == sorted(scores, reverse=True)
                for item in items:
                    product = recommender.get_product(item["product_id"])
                    assert crop in product["suitable_crops"]
                    assert problem in product["target_problems"]
                    assert 0 <= item["relevance_score"] <= 100
                    assert item["reason"]
                matched += bool(items)
    print(f"\nCombinations with at least one product: {matched} of 1260")


def test_results_are_deterministic(recommender):
    first = recommender.recommend("Cotton", "Vegetative", "Caterpillar Pests")
    second = recommender.recommend("Cotton", "Vegetative", "Caterpillar Pests")
    assert first == second


# --------------------------- Dataset safety rules ---------------------------

def test_dataset_rules(recommender):
    df = recommender.df
    assert len(df) >= 20
    assert df["product_id"].is_unique
    forbidden = ["dosage", "dose", "per acre", "per hectare", "kg", "litre", "guaranteed", "100%"]
    for _, row in df.iterrows():
        text = row["description"].lower()
        assert not re.search(r"\d", text), f"{row['product_id']} has numbers in its description"
        assert not any(word in text for word in forbidden), row["product_id"]
        assert "Illustrative sample entry" in row["source"]
        assert "Not a verified product listing" in row["source"]


# --------------------------- Missing data ---------------------------

def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        ProductRecommender(tmp_path / "missing.csv")


def test_missing_columns(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("product_id,product_name\nP1,Test\n")
    with pytest.raises(ValueError, match="missing columns"):
        ProductRecommender(path)


def test_empty_dataset(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text(HEADER)
    with pytest.raises(ValueError, match="empty"):
        ProductRecommender(path)


def test_row_with_blank_fields_does_not_crash(tmp_path):
    path = tmp_path / "blank.csv"
    path.write_text(HEADER + "P1,Test Product,Fertilizer,,,,Plain test description,Generic,Illustrative sample entry\n")
    model = ProductRecommender(path)
    assert model.get_options()["crops"] == []
    with pytest.raises(ValueError):
        model.recommend("Wheat", "Sowing", "Blight")