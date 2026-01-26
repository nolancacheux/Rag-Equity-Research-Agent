"""Risk Scoring Agent for 10-K risk analysis."""

from dataclasses import dataclass
from typing import Any

import structlog

from src.services.risk_scoring import RiskScoringService

logger = structlog.get_logger()


@dataclass
class RiskAssessment:
    """Result from risk scoring analysis."""

    ticker: str
    overall_score: int  # 1-10 (10 = highest risk)
    risk_breakdown: dict[str, int]  # category -> score
    top_risks: list[dict]  # {category, description, score}
    risk_factors_count: int
    regulatory_risks: list[str]
    operational_risks: list[str]
    financial_risks: list[str]
    summary: str
    errors: list[str]


class RiskScoringAgent:
    """Agent for scoring risk from 10-K filings.

    Responsibilities:
    - Analyze 10-K Risk Factors section
    - Score risks by category (regulatory, operational, financial)
    - Provide overall risk score (1-10)
    """

    def __init__(self) -> None:
        """Initialize risk scoring agent."""
        self._service = RiskScoringService()

    async def assess_risk(self, ticker: str) -> RiskAssessment:
        """Assess risk for a ticker based on 10-K.

        Args:
            ticker: Stock ticker symbol

        Returns:
            RiskAssessment with risk scores
        """
        ticker = ticker.upper()
        errors = []

        try:
            # Use quick assessment (without full 10-K parsing)
            result = await self._service.quick_risk_assessment(ticker)
        except Exception as e:
            logger.error("risk_scoring_failed", ticker=ticker, error=str(e))
            return RiskAssessment(
                ticker=ticker,
                overall_score=5,
                risk_breakdown={},
                top_risks=[],
                risk_factors_count=0,
                regulatory_risks=[],
                operational_risks=[],
                financial_risks=[],
                summary=f"Could not assess risk for {ticker}: {e}",
                errors=[str(e)],
            )

        if not result:
            return RiskAssessment(
                ticker=ticker,
                overall_score=5,
                risk_breakdown={},
                top_risks=[],
                risk_factors_count=0,
                regulatory_risks=[],
                operational_risks=[],
                financial_risks=[],
                summary=f"No 10-K data found for risk assessment of {ticker}",
                errors=["No 10-K data found"],
            )

        # Build risk breakdown from individual category scores
        risk_breakdown = {
            "market": result.market_risk,
            "operational": result.operational_risk,
            "financial": result.financial_risk,
        }

        # Build top risks from risk factors
        top_risks = (
            [
                {
                    "category": rf.category.value
                    if hasattr(rf.category, "value")
                    else str(rf.category),
                    "description": rf.description,
                    "score": rf.severity,
                }
                for rf in result.risk_factors[:5]
            ]
            if result.risk_factors
            else []
        )

        # Group risks by category
        risks_by_category: dict[str, list[str]] = {
            "regulatory": [],
            "operational": [],
            "financial": [],
        }
        for rf in result.risk_factors:
            cat = rf.category.value if hasattr(rf.category, "value") else str(rf.category)
            if cat in risks_by_category:
                risks_by_category[cat].append(rf.description)

        summary = result.summary if result.summary else self._generate_summary(ticker, result)

        return RiskAssessment(
            ticker=ticker,
            overall_score=result.overall_score,
            risk_breakdown=risk_breakdown,
            top_risks=top_risks,
            risk_factors_count=len(result.risk_factors),
            regulatory_risks=risks_by_category.get("regulatory", []),
            operational_risks=risks_by_category.get("operational", []),
            financial_risks=risks_by_category.get("financial", []),
            summary=summary,
            errors=errors,
        )

    def _get_risk_emoji(self, score: int) -> str:
        """Get emoji for risk score."""
        if score <= 3:
            return "🟢"  # Low risk
        elif score <= 6:
            return "🟡"  # Medium risk
        else:
            return "🔴"  # High risk

    def _generate_summary(self, ticker: str, result: Any) -> str:
        """Generate risk assessment summary."""
        emoji = self._get_risk_emoji(result.overall_score)

        lines = [f"## Risk Assessment: {ticker} {emoji}"]
        lines.append(f"**Overall Risk Score**: {result.overall_score}/10")
        lines.append(
            f"**Risk Factors Found**: {len(result.risk_factors) if result.risk_factors else 0}"
        )
        lines.append("")

        # Risk breakdown by category
        lines.append("### Risk Breakdown")
        lines.append("| Category | Score |")
        lines.append("|----------|-------|")

        categories = {
            "Market": result.market_risk,
            "Operational": result.operational_risk,
            "Financial": result.financial_risk,
        }

        for category, score in categories.items():
            if score > 0:
                cat_emoji = self._get_risk_emoji(score)
                lines.append(f"| {category} | {score}/5 {cat_emoji} |")

        lines.append("")

        # Top risks
        if result.risk_factors:
            lines.append("### Top Risk Factors")
            for rf in result.risk_factors[:5]:
                cat = rf.category.value if hasattr(rf.category, "value") else str(rf.category)
                lines.append(f"- **{cat.capitalize()}**: {rf.description}")

        lines.append("")

        # Risk interpretation
        lines.append("### Interpretation")
        if result.overall_score <= 3:
            lines.append(
                "Low risk profile. The company has relatively few and manageable risk factors."
            )
        elif result.overall_score <= 6:
            lines.append(
                "Moderate risk profile. Standard business risks present, monitor key areas."
            )
        else:
            lines.append(
                "High risk profile. Significant risk factors identified that require attention."
            )

        # Add recommendations if available
        if result.recommendations:
            lines.append("")
            lines.append("### Recommendations")
            for rec in result.recommendations[:3]:
                lines.append(f"- {rec}")

        return "\n".join(lines)


async def run_risk_agent_node(state: dict) -> dict:
    """LangGraph node function for risk scoring agent.

    Args:
        state: Current graph state

    Returns:
        Updated state with risk assessment
    """
    tickers = state.get("tickers", [])

    if not tickers:
        return {
            "risk_assessment": None,
            "errors": state.get("errors", []) + ["No tickers provided for risk assessment"],
        }

    agent = RiskScoringAgent()
    all_results = []
    all_errors = []

    for ticker in tickers:
        result = await agent.assess_risk(ticker)
        all_results.append(
            {
                "ticker": result.ticker,
                "overall_score": result.overall_score,
                "risk_breakdown": result.risk_breakdown,
                "top_risks": result.top_risks,
                "risk_factors_count": result.risk_factors_count,
                "regulatory_risks": result.regulatory_risks[:3],
                "operational_risks": result.operational_risks[:3],
                "financial_risks": result.financial_risks[:3],
                "summary": result.summary,
            }
        )
        all_errors.extend(result.errors)

    return {
        "risk_assessment": all_results,
        "errors": state.get("errors", []) + all_errors,
    }
