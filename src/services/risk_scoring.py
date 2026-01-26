"""Risk scoring service based on 10-K analysis and market data."""

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
        "market volatility",
        "economic downturn",
        "recession",
        "inflation",
        "interest rate",
        "currency fluctuation",
        "demand decline",
        "cyclical",
        "commodity price",
        "supply chain disruption",
    ],
    RiskCategory.OPERATIONAL: [
        "supply chain",
        "manufacturing",
        "production capacity",
        "labor shortage",
        "key personnel",
        "single source",
        "concentration",
        "disruption",
        "natural disaster",
        "cybersecurity",
        "data breach",
        "system failure",
    ],
    RiskCategory.FINANCIAL: [
        "debt",
        "leverage",
        "liquidity",
        "credit",
        "cash flow",
        "capital",
        "covenant",
        "refinancing",
        "impairment",
        "goodwill",
        "restructuring",
        "bankruptcy",
        "insolvency",
        "default",
    ],
    RiskCategory.REGULATORY: [
        "regulation",
        "compliance",
        "litigation",
        "lawsuit",
        "investigation",
        "antitrust",
        "patent",
        "intellectual property",
        "license",
        "permit",
        "environmental",
        "government",
        "policy change",
        "tariff",
        "sanction",
    ],
    RiskCategory.GEOPOLITICAL: [
        "china",
        "russia",
        "taiwan",
        "geopolitical",
        "trade war",
        "export control",
        "foreign government",
        "political instability",
        "war",
        "conflict",
        "international operations",
        "emerging market",
    ],
    RiskCategory.COMPETITIVE: [
        "competition",
        "competitor",
        "market share",
        "pricing pressure",
        "new entrant",
        "disruption",
        "obsolescence",
        "commoditization",
        "customer concentration",
        "losing customer",
    ],
    RiskCategory.TECHNOLOGICAL: [
        "technology change",
        "obsolete",
        "innovation",
        "r&d",
        "patent expiration",
        "cybersecurity",
        "data privacy",
        "artificial intelligence",
        "disruption",
    ],
}

# High-severity keywords (increase severity by 1)
HIGH_SEVERITY_KEYWORDS = [
    "material adverse",
    "significant risk",
    "substantial risk",
    "could materially",
    "may materially",
    "adversely affect",
    "critical",
    "severe",
    "major risk",
    "significant uncertainty",
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
        category_scores = dict.fromkeys(RiskCategory, 0)

        # Analyze each category
        for category, keywords in RISK_KEYWORDS.items():
            found_keywords = []

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

        weighted_sum = sum(category_scores[cat] * weights[cat] for cat in RiskCategory)
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

    async def quick_risk_assessment(self, ticker: str) -> RiskScore:
        """Quick risk assessment using LLM analysis of company data.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            RiskScore with LLM-generated analysis.
        """
        from langchain_groq import ChatGroq

        from src.config.settings import get_settings
        from src.tools.yfinance_tool import YFinanceTool

        settings = get_settings()
        ticker = ticker.upper()

        # Get basic company info for context
        try:
            yf_tool = YFinanceTool()
            quote = yf_tool.get_quote(ticker)
            _ = yf_tool.get_financials(ticker)  # noqa: F841
            company_name = quote.name if quote else ticker
            # sector info would come from yfinance  # Default, would get from yfinance
        except Exception:
            company_name = ticker
            pass  # Company name fallback

        # Check for any LLM provider
        has_llm = settings.groq_api_key or settings.use_azure_openai
        if not has_llm:
            return RiskScore(
                ticker=ticker,
                overall_score=5,
                risk_factors=[],
                market_risk=5,
                operational_risk=5,
                financial_risk=5,
                summary=f"Risk assessment unavailable for {ticker} (no LLM configured)",
                recommendations=["Configure Groq or Azure OpenAI API key for risk analysis"],
            )

        # Use LLM for quick risk assessment
        if settings.groq_api_key:
            llm = ChatGroq(
                api_key=settings.groq_api_key,
                model="llama-3.1-8b-instant",
                temperature=0.3,
                max_tokens=500,
            )
        else:
            from langchain_openai import AzureChatOpenAI
            llm = AzureChatOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key.get_secret_value(),
                api_version=settings.azure_openai_api_version,
                azure_deployment=settings.azure_openai_deployment,
                temperature=0.3,
                max_tokens=500,
            )

        prompt = f"""Analyze the investment risks for {company_name} ({ticker}).

Based on your knowledge of this company, provide a brief risk assessment:

1. Overall risk score (1-10, where 10 is highest risk)
2. Market risk score (1-10)
3. Operational risk score (1-10)
4. Financial risk score (1-10)
5. Top 3 specific risks for this company
6. One-paragraph summary

Format your response EXACTLY as:
OVERALL: [number]
MARKET: [number]
OPERATIONAL: [number]
FINANCIAL: [number]
RISKS:
- [risk 1]
- [risk 2]
- [risk 3]
SUMMARY: [your summary]"""

        try:
            response = await llm.ainvoke([{"role": "user", "content": prompt}])
            text = response.content

            # Parse response
            overall = self._extract_score(text, "OVERALL")
            market = self._extract_score(text, "MARKET")
            operational = self._extract_score(text, "OPERATIONAL")
            financial = self._extract_score(text, "FINANCIAL")
            risks = self._extract_risks(text)
            summary = self._extract_summary(text)

            risk_factors = [
                RiskFactor(
                    category=RiskCategory.MARKET,
                    description=risk,
                    severity=3,
                    keywords_found=[],
                )
                for risk in risks
            ]

            return RiskScore(
                ticker=ticker,
                overall_score=overall,
                risk_factors=risk_factors,
                market_risk=market,
                operational_risk=operational,
                financial_risk=financial,
                summary=summary or f"Risk assessment for {ticker}",
                recommendations=self._generate_recommendations(overall, risk_factors),
            )

        except Exception as e:
            logger.error("llm_risk_assessment_failed", ticker=ticker, error=str(e))
            return RiskScore(
                ticker=ticker,
                overall_score=5,
                risk_factors=[],
                market_risk=5,
                operational_risk=5,
                financial_risk=5,
                summary=f"Could not complete risk assessment for {ticker}",
                recommendations=["Try again later"],
            )

    def _extract_score(self, text: str, label: str) -> int:
        """Extract a score from LLM response."""
        import re

        pattern = rf"{label}:\s*(\d+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            score = int(match.group(1))
            return min(max(score, 1), 10)
        return 5

    def _extract_risks(self, text: str) -> list[str]:
        """Extract risk list from LLM response."""

        risks = []
        in_risks = False
        for line in text.split("\n"):
            if "RISKS:" in line.upper():
                in_risks = True
                continue
            if in_risks:
                if line.strip().startswith("-"):
                    risk = line.strip().lstrip("-").strip()
                    if risk:
                        risks.append(risk)
                elif "SUMMARY:" in line.upper():
                    break
        return risks[:5]

    def _extract_summary(self, text: str) -> str:
        """Extract summary from LLM response."""
        import re

        match = re.search(r"SUMMARY:\s*(.+)", text, re.IGNORECASE | re.DOTALL)
        if match:
            summary = match.group(1).strip()
            # Take first paragraph only
            summary = summary.split("\n\n")[0].strip()
            return summary[:500]
        return ""

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
