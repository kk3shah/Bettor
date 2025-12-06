from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class CampaignStatus(str, Enum):
    active = "active"
    fulfilled = "fulfilled"
    overfunded = "overfunded"


class ContributionCreate(BaseModel):
    donor: str = Field(..., min_length=1, description="Name of the donor")
    amount: float = Field(..., gt=0, description="Contribution amount in dollars")
    note: Optional[str] = Field(
        None, description="Optional note or visibility message from the donor"
    )


class Contribution(ContributionCreate):
    id: str
    created_at: datetime


class CampaignCreate(BaseModel):
    title: str = Field(..., min_length=3, description="Campaign title")
    description: str = Field(..., min_length=1, description="Why this campaign matters")
    goal_amount: float = Field(..., gt=0, description="Target fundraising goal")
    owner: str = Field(..., min_length=2, description="Campaign owner or organization")

    @field_validator("title", "description", "owner")
    @classmethod
    def strip_strings(cls, value: str) -> str:  # noqa: D417
        return value.strip()


class Campaign(BaseModel):
    id: str
    title: str
    description: str
    goal_amount: float
    owner: str
    created_at: datetime
    total_raised: float
    status: CampaignStatus
    progress: float = Field(..., description="0-1 scale for percent funded")
    contributions: List[Contribution]


class CampaignSummary(BaseModel):
    id: str
    title: str
    owner: str
    goal_amount: float
    total_raised: float
    status: CampaignStatus
    progress: float
    latest_contribution: Optional[Contribution]
