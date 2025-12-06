from __future__ import annotations

from datetime import datetime
from typing import Dict, List
from uuid import uuid4

from .schemas import Campaign, CampaignCreate, CampaignStatus, Contribution, ContributionCreate


class InMemoryStore:
    """Simple in-memory storage for campaigns and contributions."""

    def __init__(self) -> None:
        self._campaigns: Dict[str, Campaign] = {}

    def create_campaign(self, payload: CampaignCreate) -> Campaign:
        campaign_id = str(uuid4())
        now = datetime.utcnow()
        campaign = Campaign(
            id=campaign_id,
            created_at=now,
            total_raised=0.0,
            status=CampaignStatus.active,
            progress=0.0,
            contributions=[],
            **payload.model_dump(),
        )
        self._campaigns[campaign_id] = campaign
        return campaign

    def list_campaigns(self) -> List[Campaign]:
        return list(self._campaigns.values())

    def get_campaign(self, campaign_id: str) -> Campaign:
        if campaign_id not in self._campaigns:
            raise KeyError(campaign_id)
        return self._campaigns[campaign_id]

    def add_contribution(
        self, campaign_id: str, contribution: ContributionCreate
    ) -> Campaign:
        campaign = self.get_campaign(campaign_id)
        new_contribution = Contribution(
            id=str(uuid4()),
            created_at=datetime.utcnow(),
            **contribution.model_dump(),
        )
        campaign.contributions.append(new_contribution)
        campaign.total_raised = round(
            sum(item.amount for item in campaign.contributions), 2
        )
        campaign.progress = min(campaign.total_raised / campaign.goal_amount, 1.0)
        campaign.status = self._compute_status(campaign)
        return campaign

    @staticmethod
    def _compute_status(campaign: Campaign) -> CampaignStatus:
        if campaign.total_raised == 0:
            return CampaignStatus.active
        if campaign.total_raised < campaign.goal_amount:
            return CampaignStatus.active
        if campaign.total_raised == campaign.goal_amount:
            return CampaignStatus.fulfilled
        return CampaignStatus.overfunded
