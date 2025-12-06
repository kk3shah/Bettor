# Kindworth MVP

A lightweight FastAPI service that models the Kindworth minimum viable product: simple campaign funding for social good with transparent contribution tracking.

## Features
- Create campaigns with goals and key details.
- Record contributions with donor names and optional notes.
- View real-time campaign progress and fulfillment status.
- In-memory storage for easy prototyping.

## Getting Started

### Prerequisites
- Python 3.8+
- `pip install -r requirements.txt`

### Run the API
```bash
uvicorn kindworth.app.main:app --reload --port 9000
```

### API Overview
- `POST /campaigns` — create a campaign (title, description, goal_amount, owner).
- `GET /campaigns` — list campaigns with progress summaries.
- `GET /campaigns/{campaign_id}` — fetch campaign details.
- `POST /campaigns/{campaign_id}/contributions` — add a donor contribution.

### Running Tests
```bash
pytest tests/test_kindworth_api.py
```

## Notes
This MVP uses in-memory storage for clarity; swap `InMemoryStore` with a database-backed implementation when persisting data.
