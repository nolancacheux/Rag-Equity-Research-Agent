"""Risk scoring service based on 10-K analysis and market data."""

import re
from dataclasses import dataclass
from enum import Enum

import structlog

logger = structlog.get_logger()


class RiskCategory(str, Enum):
    """Risk categories."""

    MARKET = "market"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    REGULATORY = "regulatory"
    GEOPOLITICAL = "geopolitical"
    COMPETITIVE = "competitive"
    TECHNOLOGICAL = "technological"


@dataclass
class RiskFactor:
    """Individual risk factor."""

    category: RiskCategory
    description: str
    severity: int  # 1-5
    keywords_found: list[str]


@dataclass
class RiskScore:
    """Complete risk assessment."""

    ticker: str
    overall_score: int  # 1-10 (10 = highest risk)
    risk_factors: list[RiskFactor]
    market_risk: int
    operational_risk: int
    financial_risk: int
    summary: str
    recommendations: list[str]


# Risk keywords by category
RISK_KEYWORDS = {
    RiskCategory.MARKET: [
        "market volatility", "economic downturn", "recession", "inflation",
        "interest rate", "currency fluctuation", "demand decline",
        "cyclical", "commodity price", "supply chain disruption",
    ],
    RiskCategory.OPERATIONAL: [
        "supply chain", "manufacturing", "production capacity", "labor shortage",
        "key personnel", "single source", "concentration", "disruption",
        "natural disaster", "cybersecurity", "data breach", "system failure",
    ],
    RiskCategory.FINANCIAL: [
        "debt", "leverage", "liquidity", "credit", "cash flow", "capital",
        "covenant", "refinancing", "impairment", "goodwill", "restructuring",
        "bankruptcy", "insolvency", "default",
    ],
    RiskCategory.REGULATORY: [
        "regulation", "compliance", "litigation", "lawsuit", "investigation",
        "antitrust", "patent", "intellectual property", "license", "permit",
        "environmental", "government", "policy change", "tariff", "sanction",
    ],
    RiskCategory.GEOPOLITICAL: [
        "china", "russia", "taiwan", "geopolitical", "trade war", "export control",
        "foreign government", "political instability", "war", "conflict",
        "international operations", "emerging market",
    ],
    RiskCategory.COMPETITIVE: [
        "competition", "competitor", "market share", "pricing pressure",
        "new entrant", "disruption", "obsolescence", "commoditization",
        "customer concentration", "losing customer",
    ],
    RiskCategory.TECHNOLOGICAL: [
        "technology change", "obsolete", "innovation", "r&d", "patent expiration",
        "cybersecurity", "data privacy", "artificial intelligence", "disruption",
    ],
}

# High-severity keywords (increase severity by 1)
HIGH_SEVERITY_KEYWORDS = [
    "material adverse", "significant risk", "substantial risk",
    "could materially", "may materially", "adversely affect",
    "critical", "severe", "major risk", "significant uncertainty",
]


class RiskScoringService:
    """Service for calculating risk scores from SEC filings."""

    def __init__(self) -> None:
        """Initialize risk scoring service."""
        pass

    def analyze_risk(self, ticker: str, filing_text: str) -> RiskScore:
        """Analyze risk from a 10-K filing text.
        
        Args:
            ticker: Stock ticker symbol.
            filing_text: Full text of the 10-K filing.
            
        Returns:
            RiskScore with detailed analysis.
        """
        ticker = ticker.upper()
        filing_lower = filing_text.lower()
        
        risk_factors = []
        category_scores = {cat: 0 for cat in RiskCategory}
        
        # Analyze each category
        for category, keywords in RISK_KEYWORDS.items():
            found_keywords = []
            base_severity = 2  # Default severity
            
            for keyword in keywords:
                # Count occurrences
                count = filing_lower.count(keyword.lower())
                if count > 0:
                    found_keywords.append(f"{keyword} ({count}x)")
            
            if found_keywords:
                # Calculate severity based on keyword count
                severity = min(2 + len(found_keywords) // 3, 5)
                
                # Check for high-severity indicators
                for high_kw in HIGH_SEVERITY_KEYWORDS:
                    if high_kw.lower() in filing_lower:
                        severity = min(severity + 1, 5)
                        break
                
                # Create risk factor
                risk_factors.append(
                    RiskFactor(
                        category=category,
                        description=f"{category.value.title()} risks identified",
                        severity=severity,
                        keywords_found=found_keywords[:5],  # Top 5
                    )
                )
                
                category_scores[category] = severity

        # Calculate overall score (weighted average)
        weights = {
            RiskCategory.FINANCIAL: 1.5,
            RiskCategory.GEOPOLITICAL: 1.3,
            RiskCategory.REGULATORY: 1.2,
            RiskCategory.OPERATIONAL: 1.1,
            RiskCategory.MARKET: 1.0,
            RiskCategory.COMPETITIVE: 1.0,
            RiskCategory.TECHNOLOGICAL: 0.9,
        }
        
        weighted_sum = sum(
            category_scores[cat] * weights[cat] for cat in RiskCategory
        )
        total_weight = sum(weights.values())
        overall_score = min(int(weighted_sum / total_weight * 2), 10)

        # Generate summary
        summary = self._generate_summary(ticker, overall_score, risk_factors)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(overall_score, risk_factors)

        return RiskScore(
            ticker=ticker,
            overall_score=overall_score,
            risk_factors=sorted(risk_factors, key=lambda x: x.severity, reverse=True),
            market_risk=category_scores[RiskCategory.MARKET],
            operational_risk=category_scores[RiskCategory.OPERATIONAL],
            financial_risk=category_scores[RiskCategory.FINANCIAL],
            summary=summary,
            recommendations=recommendations,
        )

    def quick_risk_assessment(self, ticker: str) -> RiskScore:
        """Quick risk assessment without full 10-K (uses heuristics).
        
        Args:
            ticker: Stock ticker symbol.
            
        Returns:
            RiskScore based on market data heuristics.
        """
        # This is a simplified version using market data
        # Full version would fetch and analyze the 10-K
        
        return RiskScore(
            ticker=ticker.upper(),
            overall_score=5,  # Neutral
            risk_factors=[],
            market_risk=5,
            operational_risk=5,
            financial_risk=5,
            summary=f"Quick assessment for {ticker}. For detailed analysis, use full 10-K scan.",
            recommendations=["Review the latest 10-K for detailed risk factors"],
        )

    def _generate_summary(
        self, ticker: str, overall_score: int, risk_factors: list[RiskFactor]
    ) -> str:
        """Generate human-readable risk summary."""
        if overall_score <= 3:
            level = "LOW"
            description = "relatively few risk factors identified"
        elif overall_score <= 6:
            level = "MODERATE"
            description = "typical risk profile for its sector"
        elif overall_score <= 8:
            level = "HIGH"
            description = "elevated risk factors requiring attention"
        else:
            level = "VERY HIGH"
            description = "significant risk factors across multiple categories"

        top_risks = [f.category.value for f in risk_factors[:3]]
        top_risks_str = ", ".join(top_risks) if top_risks else "none identified"

        return f"{ticker} Risk Level: {level} ({overall_score}/10)\n\n{description.capitalize()}. Top risk categories: {top_risks_str}."

    def _generate_recommendations(
        self, overall_score: int, risk_factors: list[RiskFactor]
    ) -> list[str]:
        """Generate investment recommendations based on risk."""
        recommendations = []

        if overall_score >= 8:
            recommendations.append("Consider position sizing carefully due to elevated risk")
            recommendations.append("Monitor quarterly filings for risk factor changes")
        elif overall_score >= 6:
            recommendations.append("Review risk factors before significant position changes")

        # Category-specific recommendations
        for rf in risk_factors:
            if rf.severity >= 4:
                if rf.category == RiskCategory.GEOPOLITICAL:
                    recommendations.append("Monitor geopolitical developments closely")
                elif rf.category == RiskCategory.FINANCIAL:
                    recommendations.append("Review debt covenants and liquidity position")
                elif rf.category == RiskCategory.REGULATORY:
                    recommendations.append("Track regulatory proceedings and compliance")

        return recommendations[:5]  # Limit to 5


# Singleton instance
_risk_service: RiskScoringService | None = None


def get_risk_service() -> RiskScoringService:
    """Get singleton risk scoring service."""
    global _risk_service
    if _risk_service is None:
        _risk_service = RiskScoringService()
    return _risk_service
