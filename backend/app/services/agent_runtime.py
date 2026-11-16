"""LangChain Agent Execution Runtime (Document §5 & §2 Step 5).

Provides autonomous agent decision-making and cross-company partnership evaluation.
Target agents receive matched post event notifications, evaluate synergies with their
interest manifesto, and decide whether to autonomously formulate and publish a comment proposal.
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def evaluate_and_respond(
    agent_id: UUID,
    agent_company: str,
    agent_manifesto: str,
    post_id: UUID,
    post_title: str,
    post_content: str,
    author_company: str,
) -> Optional[str]:
    """
    Evaluate incoming post payload and generate an autonomous partnership response.

    Uses LangChain with OpenAI if configured; otherwise provides intelligent
    context-aware partnership proposition generation based on business domain synergies.
    """
    if settings.OPENAI_API_KEY:
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=settings.OPENAI_API_KEY,
                temperature=0.7,
                max_tokens=200,
            )

            messages = [
                SystemMessage(
                    content=(
                        f"You are the autonomous AI business development agent representing {agent_company}. "
                        f"Your core business interests: {agent_manifesto}. "
                        "When you receive a relevant post from a partner company, write a concise, specific "
                        "and mutually beneficial partnership proposal (1 to 2 sentences) in response. "
                        "Do not include boilerplate greetings. Directly state the concrete value proposition."
                    )
                ),
                HumanMessage(
                    content=(
                        f"Partner Company: {author_company}\n"
                        f"Post Title: {post_title}\n"
                        f"Post Content: {post_content}\n\n"
                        f"Formulate your autonomous partnership response on behalf of {agent_company}:"
                    )
                ),
            ]

            response = await llm.ainvoke(messages)
            proposal = response.content.strip()
            logger.info("LangChain agent response generated for %s: %s", agent_company, proposal[:60])
            return proposal

        except Exception as e:
            logger.warning("LangChain LLM call failed (%s). Using template synergy engine.", e)

    # Intelligent domain synergy fallback generator
    manifesto_lower = agent_manifesto.lower()
    post_lower = (post_title + " " + post_content).lower()

    if "phonepe" in agent_company.lower() or "payment" in manifesto_lower or "fintech" in manifesto_lower:
        return (
            f"{agent_company} will provide exclusive ₹50 cashback for users transacting via {agent_company} "
            f"UPI on {author_company}'s promotional orders."
        )
    elif "hdfc" in agent_company.lower() or "bank" in manifesto_lower:
        return (
            f"{agent_company} offers an instant 10% discount on credit card transactions plus 3-month "
            f"no-cost EMI for {author_company} customers."
        )
    elif "paytm" in agent_company.lower():
        return (
            f"{agent_company} can co-promote this initiative on our homepage and integrate seamless "
            f"wallet cashback for {author_company} transactions."
        )
    elif "flipkart" in agent_company.lower():
        return (
            f"{agent_company} can cross-promote this offer within our SuperCoins rewards ecosystem "
            f"to drive mutual festive engagement."
        )
    elif "swiggy" in agent_company.lower() or "zomato" in manifesto_lower:
        return (
            f"{agent_company} can bundle a complementary dining coupon for orders placed during "
            f"this campaign period."
        )
    else:
        return (
            f"{agent_company} proposes a strategic co-marketing partnership to amplify {author_company}'s "
            "campaign across our active user base."
        )
