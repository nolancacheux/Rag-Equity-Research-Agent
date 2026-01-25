"""SEC EDGAR tool for downloading and parsing 10-K annual reports."""

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import get_settings
from src.utils.rate_limiter import sec_limiter

logger = structlog.get_logger()

# SEC EDGAR API base URL
SEC_BASE_URL = "https://data.sec.gov"
SEC_FILINGS_URL = f"{SEC_BASE_URL}/submissions"


@dataclass
class SECFiling:
    """SEC filing metadata."""

    company_name: str
    cik: str
    ticker: str | None
    form_type: str
    filing_date: str
    accession_number: str
    primary_document: str
    file_url: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "company_name": self.company_name,
            "cik": self.cik,
            "ticker": self.ticker,
            "form_type": self.form_type,
            "filing_date": self.filing_date,
            "accession_number": self.accession_number,
            "primary_document": self.primary_document,
            "file_url": self.file_url,
        }


class SECEdgarTool:
    """Tool for fetching SEC EDGAR filings (10-K, 10-Q, etc.).

    Downloads real annual reports from the SEC database.
    Handles rate limiting and error recovery.
    """

    # Common company CIKs (for quick lookup)
    KNOWN_CIKS = {
        "AAPL": "0000320193",
        "MSFT": "0000789019",
        "GOOGL": "0001652044",
        "AMZN": "0001018724",
        "NVDA": "0001045810",
        "META": "0001326801",
        "TSLA": "0001318605",
        "AMD": "0000002488",
        "INTC": "0000050863",
        "NFLX": "0001065280",
    }

    def __init__(self) -> None:
        """Initialize SEC EDGAR tool."""
        self._settings = get_settings()
        self._client = httpx.Client(
            headers={
                "User-Agent": self._settings.sec_user_agent,
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    def _get_cik(self, ticker: str) -> str | None:
        """Get CIK number for a ticker symbol.

        Args:
            ticker: Stock ticker symbol

        Returns:
            CIK number (padded to 10 digits) or None
        """
        ticker = ticker.upper()

        # Check known CIKs first
        if ticker in self.KNOWN_CIKS:
            return self.KNOWN_CIKS[ticker]

        # Search SEC for CIK
        try:
            sec_limiter.acquire_sync("cik_lookup")

            response = self._client.get(
                f"{SEC_BASE_URL}/cgi-bin/browse-edgar",
                params={
                    "action": "getcompany",
                    "CIK": ticker,
                    "type": "10-K",
                    "dateb": "",
                    "owner": "include",
                    "count": "1",
                    "output": "atom",
                },
            )

            if response.status_code == 200:
                # Parse CIK from response (simplified - would need proper XML parsing)
                text = response.text
                if "CIK=" in text:
                    start = text.find("CIK=") + 4
                    end = text.find("&", start)
                    if end == -1:
                        end = text.find('"', start)
                    cik = text[start:end].zfill(10)
                    logger.info("sec_cik_found", ticker=ticker, cik=cik)
                    return cik

            logger.warning("sec_cik_not_found", ticker=ticker)
            return None

        except Exception as e:
            logger.error("sec_cik_lookup_error", ticker=ticker, error=str(e))
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def get_company_filings(self, ticker: str) -> dict[str, Any] | None:
        """Get all filings for a company.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Company filings data or None
        """
        cik = self._get_cik(ticker)
        if not cik:
            return None

        sec_limiter.acquire_sync("filings")

        try:
            response = self._client.get(f"{SEC_FILINGS_URL}/CIK{cik}.json")

            if response.status_code != 200:
                logger.warning("sec_filings_not_found", ticker=ticker, cik=cik)
                return None

            data = response.json()
            logger.info("sec_filings_fetched", ticker=ticker, cik=cik)
            return data

        except Exception as e:
            logger.error("sec_filings_error", ticker=ticker, error=str(e))
            raise

    def get_latest_10k(self, ticker: str) -> SECFiling | None:
        """Get the latest 10-K filing for a company.

        Args:
            ticker: Stock ticker symbol

        Returns:
            SECFiling object or None
        """
        filings_data = self.get_company_filings(ticker)
        if not filings_data:
            return None

        recent_filings = filings_data.get("filings", {}).get("recent", {})
        forms = recent_filings.get("form", [])
        filing_dates = recent_filings.get("filingDate", [])
        accession_numbers = recent_filings.get("accessionNumber", [])
        primary_docs = recent_filings.get("primaryDocument", [])

        # Find latest 10-K
        for i, form in enumerate(forms):
            if form == "10-K":
                cik = self._get_cik(ticker)
                accession = accession_numbers[i].replace("-", "")

                filing = SECFiling(
                    company_name=filings_data.get("name", ticker),
                    cik=cik or "",
                    ticker=ticker.upper(),
                    form_type="10-K",
                    filing_date=filing_dates[i],
                    accession_number=accession_numbers[i],
                    primary_document=primary_docs[i],
                    file_url=f"{SEC_BASE_URL}/Archives/edgar/data/{cik}/{accession}/{primary_docs[i]}",
                )

                logger.info(
                    "sec_10k_found",
                    ticker=ticker,
                    filing_date=filing.filing_date,
                    url=filing.file_url,
                )
                return filing

        logger.warning("sec_10k_not_found", ticker=ticker)
        return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def download_filing(self, filing: SECFiling, output_dir: str | None = None) -> Path | None:
        """Download a filing document.

        Args:
            filing: SECFiling object
            output_dir: Directory to save the file (uses temp dir if not specified)

        Returns:
            Path to downloaded file or None
        """
        sec_limiter.acquire_sync("download")

        try:
            response = self._client.get(filing.file_url)

            if response.status_code != 200:
                logger.warning("sec_download_failed", url=filing.file_url)
                return None

            # Determine output path
            if output_dir:
                out_path = Path(output_dir)
            else:
                out_path = Path(tempfile.gettempdir()) / "sec_filings"

            out_path.mkdir(parents=True, exist_ok=True)

            filename = f"{filing.ticker}_{filing.form_type}_{filing.filing_date}{Path(filing.primary_document).suffix}"
            file_path = out_path / filename

            file_path.write_bytes(response.content)
            logger.info("sec_filing_downloaded", path=str(file_path), size=len(response.content))

            return file_path

        except Exception as e:
            logger.error("sec_download_error", url=filing.file_url, error=str(e))
            raise

    def download_latest_10k(self, ticker: str, output_dir: str | None = None) -> Path | None:
        """Convenience method to download the latest 10-K.

        Args:
            ticker: Stock ticker symbol
            output_dir: Directory to save the file

        Returns:
            Path to downloaded file or None
        """
        filing = self.get_latest_10k(ticker)
        if not filing:
            return None

        return self.download_filing(filing, output_dir)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
