# AgriSmart: AI-Powered Smart Agriculture Product Recommendation System

A beginner-friendly full-stack project built for an AI/ML + UI/UX Intern machine test. A farmer selects a **crop**, a **growth stage** and an **agricultural problem**. The system recommends the **top 3 matching products** and explains why each one matches.

> **Important:** The product data is a small **illustrative sample** made of generic product types. It is not a verified product catalog, and the recommendations are not agronomic advice. The system never gives dosages, application rates or chemical treatment instructions. Always follow product labels and local agricultural officer advice.

---

## Features

- Home page with a hero section, a "Get Recommendations" button and a "How it works" section
- Farmer input form with three dropdowns and form validation
- Top 3 product cards showing name, category, relevance score, description and recommendation reason
- Product details page with crops, growth stages, target problems, manufacturer and source
- Loading, empty and error states on every screen that uses the API
- Content-based ML recommender (TF-IDF + cosine similarity) with basic filtering
- FastAPI backend with input validation, error handling, CORS and Swagger docs
- Responsive, accessible interface in plain CSS (forest green, light green, cream, white)
- Automated backend tests (pytest)

## Architecture

```
┌──────────────────┐   HTTP / JSON   ┌───────────────────────────┐
│  React (Vite)    │ ──────────────▶ │  FastAPI (main.py)        │
│  localhost:5173  │ ◀────────────── │  localhost:8001           │
└──────────────────┘                 │                           │
                                     │  ProductRecommender       │
                                     │  (recommender.py)         │
                                     │   - Pandas  (load CSV)    │
                                     │   - TF-IDF  (vectors)     │
                                     │   - Cosine  (ranking)     │
                                     │                           │
                                     │  dataset/products.csv     │
                                     └───────────────────────────┘
```

1. When the server starts, the CSV is loaded and the TF-IDF model is fitted **once**.
2. React asks `/api/options` to fill the dropdowns.
3. The farmer submits the form, and React sends `POST /api/recommend`.
4. The recommender filters, scores and ranks the products, and returns the top 3 with reasons.
5. Clicking "View details" calls `GET /api/products/{product_id}`.

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, React Router, HTML, CSS, JavaScript |
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| ML | Pandas, Scikit-learn (`TfidfVectorizer`, `cosine_similarity`) |
| Data | Local CSV file |
| Testing | Pytest, FastAPI TestClient |

No database, authentication, external APIs, Docker or paid services are used.

## Folder Structure

```
smart-agri-recommender/
├── backend/
│   ├── dataset/
│   │   └── products.csv        # 26 illustrative sample products
│   ├── main.py                 # FastAPI app and endpoints
│   ├── recommender.py          # ML recommendation engine
│   ├── test_api.py             # Automated tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/         # ProductCard, SelectField, StatusMessage
│   │   ├── pages/              # Home, Recommend, ProductDetail
│   │   ├── api.js              # All calls to the backend
│   │   ├── App.jsx             # Layout and routes
│   │   ├── main.jsx            # React entry point
│   │   └── index.css           # All styling
│   ├── .env                    # VITE_API_URL
│   └── package.json
├── .gitignore
└── README.md
```

## Installation

**Requirements:** Python 3.10 or newer, Node.js 18 or newer.

### Backend

```bash
cd backend
python -m venv venv

# Activate the virtual environment
# Windows (PowerShell):  venv\Scripts\Activate.ps1
# macOS / Linux:         source venv/bin/activate

pip install -r requirements.txt
```

If a pinned version fails to install on your Python version, install without pins:

```bash
pip install fastapi "uvicorn[standard]" pandas scikit-learn pydantic
```

### Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env` with the backend address:

```
VITE_API_URL=http://127.0.0.1:8001
```

## Running the Project

Use two terminals.

**Terminal 1: backend**

```bash
cd backend
# activate the virtual environment first
uvicorn main:app --reload --port 8001
```

- API: http://127.0.0.1:8001
- Swagger docs: http://127.0.0.1:8001/docs

**Terminal 2: frontend**

```bash
cd frontend
npm run dev
```

- App: http://localhost:5173

If you change the backend port, update `VITE_API_URL` in `frontend/.env` and restart `npm run dev`.

### Run the tests

```bash
cd backend
# activate the virtual environment first
pip install pytest httpx
pytest -v -s
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/api/options` | Crops, growth stages and problems for the dropdowns |
| POST | `/api/recommend` | Top 3 recommended products for a crop, stage and problem |
| GET | `/api/products/{product_id}` | Full details of one product |

**Status codes:** `200` success (including "no matching products"), `404` product not found, `422` invalid input (blank, missing or unknown values).

## ML Methodology

The engine is a **content-based recommender**. It compares what the farmer selected with the text describing each product.

1. **Build text features.** For each product, its crops, growth stages, target problems and description are combined into one text. Multi-word values such as `Low Nitrogen` become single tokens (`low_nitrogen`), so TF-IDF does not split them into separate words.
2. **TF-IDF.** `TfidfVectorizer` turns every product text into a numeric vector. Rare, distinctive terms get higher weights than common ones. The model is fitted once at startup.
3. **Build the query.** The farmer's crop, stage and problem are converted into a vector with the same vectorizer.
4. **Filter.** Only products that match both the selected **crop** and the selected **problem** are kept, so irrelevant products are never recommended.
5. **Cosine similarity.** The query vector is compared with each remaining product vector. A score of 0 means nothing in common and 1 means identical. It is shown as a percentage.
6. **Rank and explain.** Products are sorted by score (ties are broken by product ID, so results are deterministic) and the top 3 are returned. Each recommendation includes a reason built from the actual matches. If the product is not listed for the chosen growth stage, the reason says so.

**Edge cases:** if fewer than 3 products match, only those are returned with an explanatory message. If none match, an empty list and a message are returned. Unknown crops, stages and problems are rejected.

**Why no supervised model or saved model file?** There is no labeled training data (such as farmer purchases), and fitting TF-IDF on 26 products takes milliseconds, so the model is built at startup. This keeps it in sync with the CSV and avoids pickle version issues.

## Dataset

File: `backend/dataset/products.csv`, with 26 products and these fields:

`product_id`, `product_name`, `category`, `suitable_crops`, `suitable_stages`, `target_problems`, `description`, `manufacturer`, `source`

- **Categories:** Fertilizer, Micronutrient, Biofertilizer, Plant Protection (Biological, Physical and Chemical)
- **Coverage:** 10 crops, 6 growth stages, 21 problems
- Multi-value fields use the `|` separator, for example `Wheat|Rice|Maize`.
- Every row is labeled **"Illustrative sample entry ... Not a verified product listing"** in the `source` column. Entries are generic product types, so `manufacturer` is `Generic (no specific brand)`.
- Descriptions contain no dosages, application rates or guaranteed results. Chemical plant protection entries only say to follow the label and local agricultural officer advice.

To make the data real, replace rows with products from official sources (for example fertilizer control order listings, registered pesticide lists, or ICAR and state agriculture department guides) and put the real link in `source`.

## Sample Input and Output

**Request:** `POST /api/recommend`

```json
{
  "crop": "Wheat",
  "stage": "Vegetative",
  "problem": "Low Nitrogen"
}
```

**Response:**

```json
{
  "crop": "Wheat",
  "stage": "Vegetative",
  "problem": "Low Nitrogen",
  "count": 3,
  "message": "Showing the top 3 matching products.",
  "recommendations": [
    {
      "product_id": "P001",
      "product_name": "Urea (Nitrogen Fertilizer)",
      "category": "Fertilizer",
      "description": "Widely used nitrogen fertilizer that supplies nitrogen for leafy green growth in cereal and cash crops.",
      "relevance_score": 30.5,
      "reason": "Suitable for Wheat and listed for the problem 'Low Nitrogen'. It fits the Vegetative stage."
    },
    {
      "product_id": "P014",
      "product_name": "Azospirillum Culture",
      "category": "Biofertilizer",
      "description": "Root-associated bacteria that help cereal and cane crops use nitrogen and grow stronger roots.",
      "relevance_score": 25.2,
      "reason": "Suitable for Wheat and listed for the problem 'Low Nitrogen'. It fits the Vegetative stage."
    },
    {
      "product_id": "P004",
      "product_name": "NPK Complex Water Soluble Fertilizer",
      "category": "Fertilizer",
      "description": "Balanced mix of nitrogen phosphorus and potassium used when a crop needs general nutrition support.",
      "relevance_score": 23.7,
      "reason": "Suitable for Wheat and listed for the problem 'Low Nitrogen'. It fits the Vegetative stage."
    }
  ]
}
```

**No-match example:** `{"crop": "Wheat", "stage": "Flowering", "problem": "Blight"}` returns `count: 0`, an empty `recommendations` list and the message "No products in the sample dataset match Wheat with the problem 'Blight'. Try a different problem or crop."

**Invalid input example:** `{"crop": "Banana", "stage": "Sowing", "problem": "Blight"}` returns status `422` with a message listing the valid crops.

## Limitations

- The dataset is a small, illustrative sample of generic product types. It is not verified, and it contains no real brands or prices.
- Relevance scores are text-similarity percentages. They do not measure how well a product will work on a real farm.
- The crop and problem filter does most of the relevance work. TF-IDF mainly orders products that already match.
- Many crop and problem pairs have no matching product, which is expected with only 26 products.
- There is no soil, weather, region or farm-size information, and no user feedback or learning over time.
- The app gives no dosage, application rate or treatment instructions. Users must follow product labels and local agricultural officer advice.

## Possible Future Improvements

- Replace the sample rows with verified products from official sources
- Add more crops, regions and languages
- Collect farmer feedback and train a learning-to-rank model
- Add soil and weather inputs