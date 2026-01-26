"""Synthesizer Agent for compiling final research reports."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import get_settings

logger = structlog.get_logger()


SYNTHESIS_SYSTEM_PROMPT = """You are a professional equity research analyst.
Your task is to synthesize market data, SEC filings analysis, and news into a cohesive research report.

Guidelines:
- Be factual and cite specific numbers from the data provided
- Highlight key risks and opportunities
- Compare metrics between companies when multiple tickers are analyzed
- Reference specific passages from SEC filings when relevant
- Note any data limitations or errors encountered
- Use professional financial terminology
- Structure the report clearly with sections

Output a well-structured markdown report."""


@dataclass
class ResearchReport:
    """Final research report."""

    title: str
    tickers: list[str]
    generated_at: str
    executive_summary: str
    full_report: str
    data_sources: list[str]
    errors: list[str]


class SynthesizerAgent:
    """Agent for synthesizing research reports using LLM.

    Responsibilities:
    - Compile all gathered data into coherent report
    - Generate executive summary
    - Highlight key insights and risks
    - Format professional research output
    """

    def __init__(self) -> None:
        """Initialize synthesizer agent."""
        self._settings = get_settings()
        self._llm = self._create_llm()

    def _create_llm(self) -> BaseChatModel:
        """Create LLM instance.

        Priority: Groq (free) > Azure OpenAI > OpenAI
        """
        # Groq - Free tier (recommended for zero-cost deployment)
        if self._settings.use_groq:
            from langchain_groq import ChatGroq

            return ChatGroq(
                api_key=self._settings.groq_api_key.get_secret_value(),
                model="llama-3.3-70b-versatile",  # Free, fast, capable
                temperature=0.3,
            )
        # Azure OpenAI
        elif self._settings.use_azure_openai:
            from langchain_openai import AzureChatOpenAI

            return AzureChatOpenAI(
                azure_endpoint=self._settings.azure_openai_endpoint,
                api_key=self._settings.azure_openai_api_key.get_secret_value(),
                deployment_name=self._settings.azure_openai_deployment,
                api_version=self._settings.azure_openai_api_version,
                temperature=0.3,
            )
        # OpenAI direct
        elif self._settings.openai_api_key:
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                api_key=self._settings.openai_api_key.get_secret_value(),
                model="gpt-4o-mini",
                temperature=0.3,
            )
        else:
            raise RuntimeError("No LLM provider configured")

    def _format_context(
        self,
        query: str,
        market_data: dict[str, Any] | None,
        document_analysis: list[dict[str, Any]] | None,
        news_analysis: list[dict[str, Any]] | None,
        earnings_analysis: list[dict[str, Any]] | None = None,
        reddit_sentiment: list[dict[str, Any]] | None = None,
        peer_analysis: list[dict[str, Any]] | None = None,
        risk_assessment: list[dict[str, Any]] | None = None,
    ) -> str:
        """Format all data into context for LLM."""
        sections = [f"# Research Query\n{query}\n"]

        # Market Data Section
        if market_data:
            sections.append("# Market Data")
            if "summary" in market_data:
                sections.append(market_data["summary"])
            else:
                sections.append("```json")
                import json

                sections.append(json.dumps(market_data, indent=2, default=str))
                sections.append("```")

        # SEC Filing Analysis Section
        if document_analysis:
            sections.append("\n# SEC Filing Analysis")
            for doc in document_analysis:
                sections.append(
                    f"\n## {doc.get('ticker', 'Unknown')} - Query: {doc.get('query', '')}"
                )
                if doc.get("filing_date"):
                    sections.append(f"**Filing Date**: {doc['filing_date']}")
                if doc.get("summary"):
                    sections.append(doc["summary"])
                elif doc.get("passages"):
                    for i, passage in enumerate(doc["passages"][:3], 1):
                        content = passage.get("content", "")[:800]
                        sections.append(f"\n**Passage {i}** (Score: {passage.get('score', 0):.2f})")
                        sections.append(f"```\n{content}\n```")

        # Earnings Call Section (NEW)
        if earnings_analysis:
            sections.append("\n# Earnings Call Analysis")
            for earnings in earnings_analysis:
                if earnings.get("summary"):
                    sections.append(earnings["summary"])
                else:
                    sections.append(
                        f"## {earnings.get('ticker', 'Unknown')} - {earnings.get('quarter', '')} {earnings.get('year', '')}"
                    )
                    sections.append(f"**Sentiment**: {earnings.get('sentiment', 'N/A')}")
                    if earnings.get("key_points"):
                        sections.append("**Key Points**:")
                        for point in earnings["key_points"][:5]:
                            sections.append(f"- {point}")
                    if earnings.get("guidance"):
                        sections.append(f"**Guidance**: {earnings['guidance']}")

        # Reddit Sentiment Section (NEW)
        if reddit_sentiment:
            sections.append("\n# Social Sentiment (Reddit)")
            for reddit in reddit_sentiment:
                if reddit.get("summary"):
                    sections.append(reddit["summary"])
                else:
                    sections.append(f"## {reddit.get('ticker', 'Unknown')}")
                    sections.append(
                        f"**Sentiment**: {reddit.get('sentiment_label', 'N/A')} ({reddit.get('sentiment_score', 0):+.2f})"
                    )
                    sections.append(f"**Mentions**: {reddit.get('total_mentions', 0)}")
                    if reddit.get("trending_topics"):
                        sections.append(f"**Trending**: {', '.join(reddit['trending_topics'][:5])}")

        # Peer Comparison Section (NEW)
        if peer_analysis:
            sections.append("\n# Peer Comparison")
            for peer in peer_analysis:
                if peer.get("summary"):
                    sections.append(peer["summary"])
                else:
                    sections.append(f"## {peer.get('ticker', 'Unknown')}")
                    sections.append(f"**Sector**: {peer.get('sector', 'N/A')}")
                    sections.append(f"**Peers**: {', '.join(peer.get('peers', []))}")
                    if peer.get("strengths"):
                        sections.append("**Strengths**: " + "; ".join(peer["strengths"][:3]))
                    if peer.get("weaknesses"):
                        sections.append("**Weaknesses**: " + "; ".join(peer["weaknesses"][:3]))

        # Risk Assessment Section (NEW)
        if risk_assessment:
            sections.append("\n# Risk Assessment (10-K)")
            for risk in risk_assessment:
                if risk.get("summary"):
                    sections.append(risk["summary"])
                else:
                    sections.append(f"## {risk.get('ticker', 'Unknown')}")
                    sections.append(
                        f"**Overall Risk Score**: {risk.get('overall_score', 'N/A')}/10"
                    )
                    sections.append(f"**Risk Factors**: {risk.get('risk_factors_count', 0)}")
                    if risk.get("top_risks"):
                        sections.append("**Top Risks**:")
                        for r in risk["top_risks"][:3]:
                            sections.append(
                                f"- [{r.get('category', 'N/A')}] {r.get('description', '')[:100]}..."
                            )

        # News Section
        if news_analysis:
            sections.append("\n# Recent News")
            for news in news_analysis:
                if news.get("summary"):
                    sections.append(news["summary"])

        return "\n".join(sections)

    def synthesize(
        self,
        query: str,
        tickers: list[str],
        market_data: dict[str, Any] | None = None,
        document_analysis: list[dict[str, Any]] | None = None,
        news_analysis: list[dict[str, Any]] | None = None,
        earnings_analysis: list[dict[str, Any]] | None = None,
        reddit_sentiment: list[dict[str, Any]] | None = None,
        peer_analysis: list[dict[str, Any]] | None = None,
        risk_assessment: list[dict[str, Any]] | None = None,
        errors: list[str] | None = None,
    ) -> ResearchReport:
        """Synthesize all data into a research report.

        Args:
            query: Original research query
            tickers: List of analyzed tickers
            market_data: Market data from MarketDataAgent
            document_analysis: SEC filing analysis from DocumentReaderAgent
            news_analysis: News from NewsSentimentAgent
            earnings_analysis: Earnings call analysis from EarningsAgent
            reddit_sentiment: Reddit sentiment from RedditSentimentAgent
            peer_analysis: Peer comparison from PeerComparisonAgent
            risk_assessment: Risk scoring from RiskScoringAgent
            errors: Any errors encountered

        Returns:
            ResearchReport with full analysis
        """
        errors = errors or []

        # Format context
        context = self._format_context(
            query,
            market_data,
            document_analysis,
            news_analysis,
            earnings_analysis,
            reddit_sentiment,
            peer_analysis,
            risk_assessment,
        )

        # Build prompt
        user_prompt = f"""Based on the following research data, create a comprehensive equity research report.

{context}

{"## Errors/Limitations" if errors else ""}
{chr(10).join(f"- {e}" for e in errors) if errors else ""}

Please generate:
1. An executive summary (2-3 paragraphs)
2. A detailed analysis covering:
   - Current market position and valuation
   - Key findings from SEC filings (if available)
   - Earnings call highlights (if available)
   - Social sentiment from Reddit (if available)
   - Peer comparison insights (if available)
   - Risk assessment from 10-K (if available)
   - Recent news and sentiment
   - Investment considerations

Format as a professional markdown report."""

        try:
            # Call LLM
            logger.info("synthesis_starting", context_length=len(context))
            messages = [
                SystemMessage(content=SYNTHESIS_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ]

            logger.info("synthesis_calling_llm")
            response = self._llm.invoke(messages)
            logger.info("synthesis_llm_responded")
            full_report = response.content

            # Extract executive summary (first section after title)
            exec_summary = self._extract_executive_summary(full_report)

            logger.info("report_synthesized", tickers=tickers, length=len(full_report))

        except Exception as e:
            logger.error("synthesis_failed", error=str(e))
            errors.append(f"LLM synthesis failed: {str(e)}")
            full_report = self._generate_fallback_report(
                query, tickers, market_data, document_analysis, news_analysis
            )
            exec_summary = "Report generation encountered errors. See detailed analysis below."

        # Determine data sources used
        data_sources = []
        if market_data:
            data_sources.append("Yahoo Finance (real-time)")
        if document_analysis:
            data_sources.append("SEC EDGAR (10-K filings)")
        if earnings_analysis:
            data_sources.append("Earnings Call Transcripts")
        if reddit_sentiment:
            data_sources.append("Reddit (WSB, stocks, investing)")
        if peer_analysis:
            data_sources.append("Peer Comparison Analysis")
        if risk_assessment:
            data_sources.append("10-K Risk Factor Analysis")
        if news_analysis:
            data_sources.append("DuckDuckGo News")

        return ResearchReport(
            title=f"Equity Research: {', '.join(tickers)}",
            tickers=tickers,
            generated_at=datetime.now().isoformat(),
            executive_summary=exec_summary,
            full_report=full_report,
            data_sources=data_sources,
            errors=errors,
        )

    def _extract_executive_summary(self, report: str) -> str:
        """Extract executive summary from report."""
        # Look for executive summary section
        lower = report.lower()

        markers = ["executive summary", "summary", "overview"]
        for marker in markers:
            if marker in lower:
                start = lower.find(marker)
                # Find the next section header
                next_section = report.find("\n##", start + len(marker))
                if next_section == -1:
                    next_section = report.find("\n#", start + len(marker))

                if next_section != -1:
                    summary = report[start:next_section].strip()
                    # Remove the header
                    lines = summary.split("\n")
                    return "\n".join(lines[1:]).strip()

        # Fallback: first 500 chars
        return report[:500] + "..."

    def _generate_fallback_report(
        self,
        query: str,
        tickers: list[str],
        market_data: dict[str, Any] | None,
        document_analysis: list[dict[str, Any]] | None,
        news_analysis: list[dict[str, Any]] | None,
    ) -> str:
        """Generate fallback report without LLM."""
        lines = [f"# Equity Research Report: {', '.join(tickers)}\n"]
        lines.append(f"**Query**: {query}")
        lines.append(f"**Generated**: {datetime.now().isoformat()}\n")
        lines.append("---\n")

        if market_data and "summary" in market_data:
            lines.append(market_data["summary"])
            lines.append("\n---\n")

        if document_analysis:
            for doc in document_analysis:
                if doc.get("summary"):
                    lines.append(doc["summary"])
            lines.append("\n---\n")

        if news_analysis:
            for news in news_analysis:
                if news.get("summary"):
                    lines.append(news["summary"])

        return "\n".join(lines)


def run_synthesizer_node(state: dict) -> dict:
    """LangGraph node function for synthesizer agent.

    Args:
        state: Current graph state

    Returns:
        Updated state with final report
    """
    query = state.get("query", "")
    tickers = state.get("tickers", [])
    market_data = state.get("market_data")
    document_analysis = state.get("document_analysis")
    news_analysis = state.get("news_analysis")
    earnings_analysis = state.get("earnings_analysis")
    reddit_sentiment = state.get("reddit_sentiment")
    peer_analysis = state.get("peer_analysis")
    risk_assessment = state.get("risk_assessment")
    errors = state.get("errors", [])

    agent = SynthesizerAgent()
    report = agent.synthesize(
        query=query,
        tickers=tickers,
        market_data=market_data,
        document_analysis=document_analysis,
        news_analysis=news_analysis,
        earnings_analysis=earnings_analysis,
        reddit_sentiment=reddit_sentiment,
        peer_analysis=peer_analysis,
        risk_assessment=risk_assessment,
        errors=errors,
    )

    return {
        "report": {
            "title": report.title,
            "tickers": report.tickers,
            "generated_at": report.generated_at,
            "executive_summary": report.executive_summary,
            "full_report": report.full_report,
            "data_sources": report.data_sources,
        },
        "errors": report.errors,
    }
