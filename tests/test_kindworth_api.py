from kindworth.app.main import (
    add_contribution,
    create_campaign,
    get_campaign,
    list_campaigns,
    store,
)
from kindworth.app.schemas import CampaignCreate, CampaignStatus, ContributionCreate


def _reset_store():
    store._campaigns.clear()


def test_create_and_fetch_campaign():
    _reset_store()
    payload = CampaignCreate(
        title="Clean Water Wells",
        description="Fund wells for rural villages",
        goal_amount=5000,
        owner="Kindworth Org",
    )
    created = create_campaign(payload)
    assert created.title == payload.title
    assert created.goal_amount == payload.goal_amount

    fetched = get_campaign(created.id)
    assert fetched.id == created.id


def test_add_contribution_and_progress_status():
    _reset_store()
    campaign = create_campaign(
        CampaignCreate(
            title="Solar Schools",
            description="Panels for classrooms",
            goal_amount=200,
            owner="Kindworth Labs",
        )
    )

    updated = add_contribution(
        campaign.id,
        ContributionCreate(donor="Alex", amount=150, note="Excited to help"),
    )
    assert updated.total_raised == 150
    assert updated.status == CampaignStatus.active

    final = add_contribution(
        campaign.id, ContributionCreate(donor="Sam", amount=50)
    )
    assert final.status == CampaignStatus.fulfilled
    assert final.progress == 1


def test_list_campaigns_shows_latest_contribution():
    _reset_store()
    campaign = create_campaign(
        CampaignCreate(
            title="Mentorship Fund",
            description="Support for after-school program",
            goal_amount=100,
            owner="Kindworth",
        )
    )

    add_contribution(
        campaign.id, ContributionCreate(donor="Taylor", amount=30)
    )
    add_contribution(
        campaign.id, ContributionCreate(donor="Jordan", amount=40)
    )

    listing = list_campaigns()
    assert len(listing) == 1
    summary = listing[0]
    assert summary.latest_contribution and summary.latest_contribution.donor == "Jordan"
    assert summary.total_raised == 70
