import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from recommender import ProductRecommender


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once when the server starts: load the dataset and fit the model."""
    app.state.recommender = ProductRecommender()
    yield


app = FastAPI(
    title="Smart Agriculture Product Recommendation API",
    description="Recommends agricultural products based on crop, growth stage and problem.",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the React dev server (Vite runs on port 5173) to call this API.
# Allowed frontend addresses. Set ALLOWED_ORIGINS on the server (comma-separated).
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------- Pydantic models -----------------------------

class RecommendRequest(BaseModel):
    crop: str = Field(..., description="Crop name, e.g. Wheat")
    stage: str = Field(..., description="Crop growth stage, e.g. Vegetative")
    problem: str = Field(..., description="Agricultural problem, e.g. Low Nitrogen")

    @field_validator("crop", "stage", "problem")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty.")
        return value

    model_config = {
        "json_schema_extra": {
            "example": {"crop": "Wheat", "stage": "Vegetative", "problem": "Low Nitrogen"}
        }
    }


class OptionsResponse(BaseModel):
    crops: List[str]
    stages: List[str]
    problems: List[str]


class Recommendation(BaseModel):
    product_id: str
    product_name: str
    category: str
    description: str
    relevance_score: float = Field(..., description="Similarity percentage (0 to 100)")
    reason: str


class RecommendResponse(BaseModel):
    crop: str
    stage: str
    problem: str
    count: int
    message: str
    recommendations: List[Recommendation]


class ProductDetail(BaseModel):
    product_id: str
    product_name: str
    category: str
    suitable_crops: List[str]
    suitable_stages: List[str]
    target_problems: List[str]
    description: str
    manufacturer: str
    source: str


# ------------------------------- Endpoints --------------------------------

def get_recommender(request: Request) -> ProductRecommender:
    return request.app.state.recommender


@app.get("/")
def health_check():
    """Simple health check to confirm the server is running."""
    return {"status": "ok", "message": "Smart Agriculture API is running"}


@app.get("/api/options", response_model=OptionsResponse)
def get_options(request: Request):
    """Crops, growth stages and problems used to fill the dropdowns."""
    return get_recommender(request).get_options()


@app.post("/api/recommend", response_model=RecommendResponse)
def recommend(payload: RecommendRequest, request: Request):
    """Return the top 3 products for the selected crop, stage and problem."""
    try:
        result = get_recommender(request).recommend(
            payload.crop, payload.stage, payload.problem
        )
    except ValueError as error:
        # Unknown crop, stage or problem.
        raise HTTPException(status_code=422, detail=str(error))

    return {
        "crop": payload.crop,
        "stage": payload.stage,
        "problem": payload.problem,
        "count": len(result["recommendations"]),
        "message": result["message"],
        "recommendations": result["recommendations"],
    }


@app.get("/api/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: str, request: Request):
    """Full details for one product."""
    product = get_recommender(request).get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found.")
    return product