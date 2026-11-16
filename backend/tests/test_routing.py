"""Comprehensive integration tests for 3-Stage Routing and Closed-Loop Feedback."""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from app.database import AsyncSessionLocal
from app.main import app
from app.models.agent import Agent
from app.models.post import Post
from app.models.routing_log import RoutingLog
from app.services.feedback import compute_engagement_rate, update_agent_profile_vector
from app.services.routing_engine import route_post


@pytest.mark.asyncio
async def test_agent_registration_and_list():
    """Verify agent registration endpoint creates agent and auto-indexes embeddings."""
    unique_company = f"TestCorp Fintech {uuid.uuid4().hex[:6]}"
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        payload = {
            "company_name": unique_company,
            "industry_category": "Payments & Fintech",
            "webhook_url": "https://testcorp.example.com/events",
            "interest_manifesto": "Looking for digital banking, micro-loans, and festive UPI payment promotions.",
        }
        res = await ac.post("/api/v1/agents/register", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["company_name"] == unique_company
        assert "id" in data
        assert data["trust_score"] == 1.0

        # List agents
        list_res = await ac.get("/api/v1/agents")
        assert list_res.status_code == 200
        agents = list_res.json()
        assert any(a["company_name"] == unique_company for a in agents)


@pytest.mark.asyncio
async def test_post_creation_and_routing_pipeline():
    """Verify publishing a post triggers the multi-stage relevance routing pipeline."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Get an existing author agent
        agents_res = await ac.get("/api/v1/agents")
        agents = agents_res.json()
        assert len(agents) >= 2
        author = agents[0]

        post_payload = {
            "author_agent_id": author["id"],
            "title": "Exclusive Festive Dining & Food Cashback Offers",
            "content": "Offering 20% discount on festive dinner combos and looking for payment partner cashback integration.",
        }
        res = await ac.post("/api/v1/posts?trigger_autonomous_response=true", json=post_payload)
        assert res.status_code == 201
        data = res.json()

        assert "post" in data
        assert "routing" in data
        assert data["routing"]["stage1_eligible_count"] >= 1
        assert "dispatched_webhooks" in data

        # Check post detail
        post_id = data["post"]["id"]
        detail_res = await ac.get(f"/api/v1/posts/{post_id}")
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert "routing_logs" in detail
        assert "comments" in detail


@pytest.mark.asyncio
async def test_dashboard_stats_and_network_graph():
    """Verify dashboard KPI statistics and force-graph network payload."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        stats_res = await ac.get("/api/v1/dashboard/stats")
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert stats["total_agents"] >= 1
        assert stats["total_posts"] >= 1
        assert "engagement_rate" in stats

        net_res = await ac.get("/api/v1/dashboard/network")
        assert net_res.status_code == 200
        network = net_res.json()
        assert "nodes" in network
        assert "links" in network
        assert len(network["nodes"]) >= 1


@pytest.mark.asyncio
async def test_dynamic_profile_learning():
    """Verify closed-loop feedback and negative gradient shift calculation."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        agent = (await session.execute(select(Agent))).scalars().first()
        assert agent is not None

        # Compute engagement rate
        rate_info = await compute_engagement_rate(agent.id, session)
        assert "engagement_rate" in rate_info

        # Run profile optimization (ignore threshold 1 so it triggers if any unengaged logs exist)
        shift = await update_agent_profile_vector(
            agent_id=agent.id,
            db=session,
            learning_rate=0.05,
            ignore_threshold=1,
        )
        # Result is either None (if no unengaged samples) or a dict with shift magnitude
        if shift:
            assert "shift_magnitude" in shift
            assert shift["shift_magnitude"] >= 0
