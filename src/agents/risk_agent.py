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
            result = await self._service.score_risk(ticker)
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

        summary = self._generate_summary(ticker, result)

        return RiskAssessment(
            ticker=ticker,
            overall_score=result.overall_score,
            risk_breakdown=result.category_scores,
            top_risks=result.top_risks,
            risk_factors_count=result.total_risk_factors,
            regulatory_risks=result.risks_by_category.get("regulatory", []),
            operational_risks=result.risks_by_category.get("operational", []),
            financial_risks=result.risks_by_category.get("financial", []),
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
        lines.append(f"**Risk Factors Found**: {result.total_risk_factors}")
        lines.append("")
        
        # Risk breakdown by category
        lines.append("### Risk Breakdown")
        lines.append("| Category | Score |")
        lines.append("|----------|-------|")
        
        for category, score in result.category_scores.items():
            cat_emoji = self._get_risk_emoji(score)
            lines.append(f"| {category.capitalize()} | {score}/10 {cat_emoji} |")
        
        lines.append("")
        
        # Top risks
        if result.top_risks:
            lines.append("### Top Risk Factors")
            for risk in result.top_risks[:5]:
                lines.append(f"- **{risk['category'].capitalize()}**: {risk['description'][:100]}...")
        
        lines.append("")
        
        # Risk interpretation
        lines.append("### Interpretation")
        if result.overall_score <= 3:
            lines.append("Low risk profile. The company has relatively few and manageable risk factors.")
        elif result.overall_score <= 6:
            lines.append("Moderate risk profile. Standard business risks present, monitor key areas.")
        else:
            lines.append("High risk profile. Significant risk factors identified that require attention.")
        
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
        all_results.append({
            "ticker": result.ticker,
            "overall_score": result.overall_score,
            "risk_breakdown": result.risk_breakdown,
            "top_risks": result.top_risks,
            "risk_factors_count": result.risk_factors_count,
            "regulatory_risks": result.regulatory_risks[:3],
            "operational_risks": result.operational_risks[:3],
            "financial_risks": result.financial_risks[:3],
            "summary": result.summary,
        })
        all_errors.extend(result.errors)

    return {
        "risk_assessment": all_results,
        "errors": state.get("errors", []) + all_errors,
    }
