from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .schemas import (
    Campaign,
    CampaignCreate,
    CampaignSummary,
    ContributionCreate,
)
from .storage import InMemoryStore

app = FastAPI(title="Kindworth MVP", version="0.1.0")
store = InMemoryStore()


@app.post("/campaigns", response_model=Campaign, status_code=201)
def create_campaign(payload: CampaignCreate) -> Campaign:
    """Create a new fundraising campaign."""
    return store.create_campaign(payload)


@app.get("/campaigns", response_model=list[CampaignSummary])
def list_campaigns() -> list[CampaignSummary]:
    """Return all campaigns with a short progress summary."""
    summaries: list[CampaignSummary] = []
    for campaign in store.list_campaigns():
        latest = campaign.contributions[-1] if campaign.contributions else None
        summaries.append(
            CampaignSummary(
                id=campaign.id,
                title=campaign.title,
                owner=campaign.owner,
                goal_amount=campaign.goal_amount,
                total_raised=campaign.total_raised,
                status=campaign.status,
                progress=campaign.progress,
                latest_contribution=latest,
            )
        )
    return summaries


@app.get("/campaigns/{campaign_id}", response_model=Campaign)
def get_campaign(campaign_id: str) -> Campaign:
    """Get campaign details and contributions."""
    try:
        return store.get_campaign(campaign_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Campaign not found")


@app.post(
    "/campaigns/{campaign_id}/contributions",
    response_model=Campaign,
    status_code=201,
)
def add_contribution(campaign_id: str, payload: ContributionCreate) -> Campaign:
    """Add a contribution to a campaign and return the updated campaign."""
    try:
        return store.add_contribution(campaign_id, payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Campaign not found")
