"""DCF Valuation service - calculates fair value using free cash flow."""

from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass
class DCFResult:
    """DCF valuation result."""

    ticker: str
    current_price: float | None
    fair_value: float | None
    upside_percent: float | None
    fcf_current: float | None
    growth_rate: float
    discount_rate: float
    terminal_growth: float
    shares_outstanding: float | None
    summary: str


class DCFValuationService:
    """Calculate intrinsic value using Discounted Cash Flow model.
    
    Uses free cash flow from Yahoo Finance (no paid API needed).
    """

    DEFAULT_DISCOUNT_RATE = 0.10  # 10% WACC
    DEFAULT_TERMINAL_GROWTH = 0.025  # 2.5% perpetual growth
    PROJECTION_YEARS = 5

    def __init__(self) -> None:
        """Initialize DCF service."""
        self._yf_tool = None

    def _get_yf(self):
        """Lazy load yfinance."""
        if self._yf_tool is None:
            from src.tools.yfinance_tool import YFinanceTool
            self._yf_tool = YFinanceTool()
        return self._yf_tool

    def calculate_dcf(
        self,
        ticker: str,
        growth_rate: float | None = None,
        discount_rate: float | None = None,
        terminal_growth: float | None = None,
    ) -> DCFResult:
        """Calculate DCF fair value for a stock.
        
        Args:
            ticker: Stock ticker symbol.
            growth_rate: Annual FCF growth rate (auto-estimated if None).
            discount_rate: WACC/discount rate (default 10%).
            terminal_growth: Terminal growth rate (default 2.5%).
            
        Returns:
            DCFResult with fair value and analysis.
        """
        import yfinance as yf
        
        ticker = ticker.upper()
        discount_rate = discount_rate or self.DEFAULT_DISCOUNT_RATE
        terminal_growth = terminal_growth or self.DEFAULT_TERMINAL_GROWTH
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            cashflow = stock.cashflow
            
            # Get current price
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            shares = info.get("sharesOutstanding")
            
            if not shares:
                return self._error_result(ticker, "Could not get shares outstanding")
            
            # Get Free Cash Flow
            fcf = None
            if cashflow is not None and not cashflow.empty:
                # Try different FCF labels
                fcf_labels = ["Free Cash Flow", "FreeCashFlow", "Operating Cash Flow"]
                for label in fcf_labels:
                    if label in cashflow.index:
                        fcf = cashflow.loc[label].iloc[0]  # Most recent year
                        break
            
            if fcf is None or fcf <= 0:
                # Fallback: estimate from operating cash flow - capex
                if "Operating Cash Flow" in cashflow.index and "Capital Expenditure" in cashflow.index:
                    ocf = cashflow.loc["Operating Cash Flow"].iloc[0]
                    capex = abs(cashflow.loc["Capital Expenditure"].iloc[0])
                    fcf = ocf - capex
            
            if fcf is None or fcf <= 0:
                return self._error_result(ticker, "Could not determine positive free cash flow")
            
            # Estimate growth rate if not provided
            if growth_rate is None:
                growth_rate = self._estimate_growth_rate(info, cashflow)
            
            # Project future cash flows
            projected_fcf = []
            current_fcf = fcf
            
            for year in range(1, self.PROJECTION_YEARS + 1):
                projected_fcf.append(current_fcf * (1 + growth_rate) ** year)
            
            # Calculate present value of projected FCF
            pv_fcf = sum(
                cf / (1 + discount_rate) ** (i + 1)
                for i, cf in enumerate(projected_fcf)
            )
            
            # Terminal value (Gordon Growth Model)
            terminal_fcf = projected_fcf[-1] * (1 + terminal_growth)
            terminal_value = terminal_fcf / (discount_rate - terminal_growth)
            pv_terminal = terminal_value / (1 + discount_rate) ** self.PROJECTION_YEARS
            
            # Total enterprise value
            enterprise_value = pv_fcf + pv_terminal
            
            # Adjust for cash and debt
            cash = info.get("totalCash", 0) or 0
            debt = info.get("totalDebt", 0) or 0
            equity_value = enterprise_value + cash - debt
            
            # Fair value per share
            fair_value = equity_value / shares
            
            # Upside/downside
            upside = None
            if current_price and fair_value:
                upside = ((fair_value - current_price) / current_price) * 100
            
            summary = self._generate_summary(
                ticker, current_price, fair_value, upside, fcf,
                growth_rate, discount_rate, terminal_growth
            )
            
            return DCFResult(
                ticker=ticker,
                current_price=current_price,
                fair_value=round(fair_value, 2) if fair_value else None,
                upside_percent=round(upside, 1) if upside else None,
                fcf_current=fcf,
                growth_rate=growth_rate,
                discount_rate=discount_rate,
                terminal_growth=terminal_growth,
                shares_outstanding=shares,
                summary=summary,
            )
            
        except Exception as e:
            logger.error("dcf_calculation_failed", ticker=ticker, error=str(e))
            return self._error_result(ticker, str(e))

    def _estimate_growth_rate(self, info: dict, cashflow) -> float:
        """Estimate growth rate from historical data."""
        # Try revenue growth
        revenue_growth = info.get("revenueGrowth")
        if revenue_growth and 0 < revenue_growth < 0.5:
            return min(revenue_growth, 0.25)  # Cap at 25%
        
        # Try earnings growth
        earnings_growth = info.get("earningsGrowth")
        if earnings_growth and 0 < earnings_growth < 0.5:
            return min(earnings_growth, 0.25)
        
        # Default conservative estimate
        return 0.08  # 8% default

    def _generate_summary(
        self,
        ticker: str,
        current_price: float | None,
        fair_value: float | None,
        upside: float | None,
        fcf: float,
        growth_rate: float,
        discount_rate: float,
        terminal_growth: float,
    ) -> str:
        """Generate DCF summary."""
        lines = [f"## DCF Valuation: {ticker}"]
        
        if current_price:
            lines.append(f"**Current Price**: ${current_price:.2f}")
        if fair_value:
            lines.append(f"**Fair Value**: ${fair_value:.2f}")
        
        if upside is not None:
            if upside > 15:
                verdict = "UNDERVALUED"
                emoji = "🟢"
            elif upside < -15:
                verdict = "OVERVALUED"
                emoji = "🔴"
            else:
                verdict = "FAIRLY VALUED"
                emoji = "🟡"
            lines.append(f"**Upside**: {upside:+.1f}% {emoji} {verdict}")
        
        lines.append("")
        lines.append("### Assumptions")
        lines.append(f"- FCF (TTM): ${fcf/1e9:.2f}B")
        lines.append(f"- Growth Rate: {growth_rate:.1%}")
        lines.append(f"- Discount Rate: {discount_rate:.1%}")
        lines.append(f"- Terminal Growth: {terminal_growth:.1%}")
        lines.append(f"- Projection: {self.PROJECTION_YEARS} years")
        
        lines.append("")
        lines.append("*Note: DCF is sensitive to assumptions. Use as one input among many.*")
        
        return "\n".join(lines)

    def _error_result(self, ticker: str, error: str) -> DCFResult:
        """Return error result."""
        return DCFResult(
            ticker=ticker,
            current_price=None,
            fair_value=None,
            upside_percent=None,
            fcf_current=None,
            growth_rate=0,
            discount_rate=self.DEFAULT_DISCOUNT_RATE,
            terminal_growth=self.DEFAULT_TERMINAL_GROWTH,
            shares_outstanding=None,
            summary=f"Could not calculate DCF for {ticker}: {error}",
        )
