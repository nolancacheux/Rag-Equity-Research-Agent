"""Tests for all agent modules."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestMarketDataAgent:
    """Tests for MarketDataAgent."""

    @patch("src.agents.market_data.YFinanceTool")
    def test_analyze_success(self, mock_yfinance_class):
        """Test successful analysis."""
        from src.agents.market_data import MarketDataAgent, MarketDataResult

        # Setup mocks
        mock_tool = MagicMock()
        mock_yfinance_class.return_value = mock_tool

        mock_quote = MagicMock()
        mock_quote.to_dict.return_value = {
            "symbol": "NVDA",
            "name": "NVIDIA Corporation",
            "price": 875.50,
            "change_percent": 1.42,
            "market_cap": 2150000000000,
            "pe_ratio": 65.5,
            "market_state": "REGULAR",
        }
        mock_tool.get_quote.return_value = mock_quote

        mock_financials = MagicMock()
        mock_financials.to_dict.return_value = {
            "revenue": 60000000000,
            "net_income": 20000000000,
            "profit_margin": 0.33,
        }
        mock_tool.get_financials.return_value = mock_financials

        agent = MarketDataAgent()
        result = agent.analyze(["NVDA"])

        assert isinstance(result, MarketDataResult)
        assert "NVDA" in result.quotes
        assert "NVDA" in result.financials
        assert len(result.errors) == 0

    @patch("src.agents.market_data.YFinanceTool")
    def test_analyze_no_quote_data(self, mock_yfinance_class):
        """Test handling of missing quote data."""
        from src.agents.market_data import MarketDataAgent

        mock_tool = MagicMock()
        mock_yfinance_class.return_value = mock_tool
        mock_tool.get_quote.return_value = None
        mock_tool.get_financials.return_value = None

        agent = MarketDataAgent()
        result = agent.analyze(["INVALID"])

        assert "No quote data for INVALID" in result.errors

    @patch("src.agents.market_data.YFinanceTool")
    def test_analyze_quote_exception(self, mock_yfinance_class):
        """Test handling of quote fetch exception."""
        from src.agents.market_data import MarketDataAgent

        mock_tool = MagicMock()
        mock_yfinance_class.return_value = mock_tool
        mock_tool.get_quote.side_effect = Exception("API error")
        mock_tool.get_financials.return_value = None

        agent = MarketDataAgent()
        result = agent.analyze(["NVDA"])

        assert any("Error fetching quote" in e for e in result.errors)

    @patch("src.agents.market_data.YFinanceTool")
    def test_analyze_financials_exception(self, mock_yfinance_class):
        """Test handling of financials fetch exception."""
        from src.agents.market_data import MarketDataAgent

        mock_tool = MagicMock()
        mock_yfinance_class.return_value = mock_tool
        mock_tool.get_quote.return_value = None
        mock_tool.get_financials.side_effect = Exception("Financials error")

        agent = MarketDataAgent()
        result = agent.analyze(["NVDA"])

        assert any("Error fetching financials" in e for e in result.errors)

    def test_format_price(self):
        """Test price formatting."""
        from src.agents.market_data import MarketDataAgent

        with patch("src.agents.market_data.YFinanceTool"):
            agent = MarketDataAgent()

        assert agent._format_price(None) == "N/A"
        assert agent._format_price(875.50) == "$875.50"

    def test_format_large_number(self):
        """Test large number formatting."""
        from src.agents.market_data import MarketDataAgent

        with patch("src.agents.market_data.YFinanceTool"):
            agent = MarketDataAgent()

        assert agent._format_large_number(None) == "N/A"
        assert agent._format_large_number(1500000000000) == "$1.50T"
        assert agent._format_large_number(2500000000) == "$2.50B"
        assert agent._format_large_number(5000000) == "$5.00M"
        assert agent._format_large_number(50000) == "$50,000"

    def test_format_percent(self):
        """Test percentage formatting."""
        from src.agents.market_data import MarketDataAgent

        with patch("src.agents.market_data.YFinanceTool"):
            agent = MarketDataAgent()

        assert agent._format_percent(None) == "N/A"
        assert agent._format_percent(0.33) == "33.00%"
        assert agent._format_percent(1.5) == "1.50%"

    @patch("src.agents.market_data.YFinanceTool")
    def test_generate_summary_empty(self, mock_yfinance_class):
        """Test summary generation with no data."""
        from src.agents.market_data import MarketDataAgent

        agent = MarketDataAgent()
        summary = agent._generate_summary({}, {}, {})

        assert summary == "No market data available."

    @patch("src.agents.market_data.YFinanceTool")
    def test_generate_summary_with_data(self, mock_yfinance_class):
        """Test summary generation with data."""
        from src.agents.market_data import MarketDataAgent

        agent = MarketDataAgent()

        quotes = {
            "NVDA": {
                "name": "NVIDIA Corporation",
                "price": 875.50,
                "change_percent": 1.42,
                "market_cap": 2150000000000,
                "pe_ratio": 65.5,
                "market_state": "REGULAR",
            },
            "AMD": {
                "name": "AMD Inc",
                "price": 150.00,
                "change_percent": -0.5,
                "market_cap": 250000000000,
                "pe_ratio": 45.0,
                "market_state": "REGULAR",
            },
        }
        financials = {
            "NVDA": {
                "revenue": 60000000000,
                "net_income": 20000000000,
                "profit_margin": 0.33,
            }
        }
        pe_comparison = {"NVDA": 65.5, "AMD": 45.0}

        summary = agent._generate_summary(quotes, financials, pe_comparison)

        assert "NVDA" in summary
        assert "AMD" in summary
        assert "P/E Ratio Comparison" in summary


class TestMarketDataNode:
    """Tests for market data LangGraph node."""

    @patch("src.agents.market_data.MarketDataAgent")
    def test_run_market_data_node_success(self, mock_agent_class):
        """Test node execution with tickers."""
        from src.agents.market_data import MarketDataResult, run_market_data_node

        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.analyze.return_value = MarketDataResult(
            quotes={"NVDA": {}},
            financials={},
            pe_comparison={},
            market_summary="Summary",
            errors=[],
        )

        state = {"tickers": ["NVDA"], "errors": []}
        result = run_market_data_node(state)

        assert result["market_data"] is not None
        assert "summary" in result["market_data"]

    def test_run_market_data_node_no_tickers(self):
        """Test node with no tickers."""
        from src.agents.market_data import run_market_data_node

        state = {"tickers": [], "errors": []}
        result = run_market_data_node(state)

        assert result["market_data"] is None
        assert "No tickers provided" in result["errors"]


class TestNewsSentimentAgent:
    """Tests for NewsSentimentAgent."""

    @patch("src.agents.news_sentiment.DuckDuckGoSearchTool")
    def test_analyze_success(self, mock_search_class):
        """Test successful news analysis."""
        from src.agents.news_sentiment import NewsAnalysisResult, NewsSentimentAgent

        mock_tool = MagicMock()
        mock_search_class.return_value = mock_tool

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "title": "NVIDIA Stock Surges",
            "source": "TechNews",
            "date": "2024-01-01",
            "snippet": "Great news...",
            "url": "https://example.com",
        }
        mock_tool.search_stock_news.return_value = [mock_result]

        agent = NewsSentimentAgent()
        result = agent.analyze("NVDA", "NVIDIA Corporation")

        assert isinstance(result, NewsAnalysisResult)
        assert result.ticker == "NVDA"
        assert len(result.articles) == 1
        assert len(result.errors) == 0

    @patch("src.agents.news_sentiment.DuckDuckGoSearchTool")
    def test_analyze_search_error(self, mock_search_class):
        """Test handling of search error."""
        from src.agents.news_sentiment import NewsSentimentAgent

        mock_tool = MagicMock()
        mock_search_class.return_value = mock_tool
        mock_tool.search_stock_news.side_effect = Exception("Search failed")

        agent = NewsSentimentAgent()
        result = agent.analyze("NVDA")

        assert len(result.articles) == 0
        assert any("News search failed" in e for e in result.errors)

    @patch("src.agents.news_sentiment.DuckDuckGoSearchTool")
    def test_generate_summary_empty(self, mock_search_class):
        """Test summary with no articles."""
        from src.agents.news_sentiment import NewsSentimentAgent

        agent = NewsSentimentAgent()
        summary = agent._generate_summary("NVDA", "NVIDIA", [])

        assert "No recent news found" in summary

    @patch("src.agents.news_sentiment.DuckDuckGoSearchTool")
    def test_generate_summary_with_articles(self, mock_search_class):
        """Test summary with articles."""
        from src.agents.news_sentiment import NewsSentimentAgent

        agent = NewsSentimentAgent()
        articles = [
            {
                "title": "Test Article",
                "source": "Source",
                "date": "2024-01-01",
                "snippet": "x" * 400,  # Long snippet
                "url": "https://example.com",
            }
        ]
        summary = agent._generate_summary("NVDA", "NVIDIA", articles)

        assert "Test Article" in summary
        assert "..." in summary  # Truncated

    @patch("src.agents.news_sentiment.DuckDuckGoSearchTool")
    def test_search_topic_success(self, mock_search_class):
        """Test topic search."""
        from src.agents.news_sentiment import NewsSentimentAgent

        mock_tool = MagicMock()
        mock_search_class.return_value = mock_tool

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"title": "China Supply Chain"}
        mock_tool.search_financial_topic.return_value = [mock_result]

        agent = NewsSentimentAgent()
        results = agent.search_topic("China supply chain", "NVDA")

        assert len(results) == 1

    @patch("src.agents.news_sentiment.DuckDuckGoSearchTool")
    def test_search_topic_error(self, mock_search_class):
        """Test topic search error handling."""
        from src.agents.news_sentiment import NewsSentimentAgent

        mock_tool = MagicMock()
        mock_search_class.return_value = mock_tool
        mock_tool.search_financial_topic.side_effect = Exception("Search error")

        agent = NewsSentimentAgent()
        results = agent.search_topic("China")

        assert results == []


class TestNewsSentimentNode:
    """Tests for news sentiment LangGraph node."""

    @patch("src.agents.news_sentiment.NewsSentimentAgent")
    def test_run_news_sentiment_node_success(self, mock_agent_class):
        """Test node execution."""
        from src.agents.news_sentiment import NewsAnalysisResult, run_news_sentiment_node

        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.analyze.return_value = NewsAnalysisResult(
            ticker="NVDA",
            company_name="NVIDIA",
            articles=[],
            summary="Summary",
            errors=[],
        )

        state = {
            "tickers": ["NVDA"],
            "market_data": {"quotes": {"NVDA": {"name": "NVIDIA"}}},
            "errors": [],
        }
        result = run_news_sentiment_node(state)

        assert result["news_analysis"] is not None

    def test_run_news_sentiment_node_no_tickers(self):
        """Test node with no tickers."""
        from src.agents.news_sentiment import run_news_sentiment_node

        state = {"tickers": [], "errors": []}
        result = run_news_sentiment_node(state)

        assert result["news_analysis"] is None
        assert any("No tickers provided" in e for e in result["errors"])


class TestDocumentReaderAgent:
    """Tests for DocumentReaderAgent."""

    @patch("src.agents.document_reader.QdrantStore")
    @patch("src.agents.document_reader.DocumentChunker")
    @patch("src.agents.document_reader.SECEdgarTool")
    def test_init(self, mock_sec, mock_chunker, mock_qdrant):
        """Test agent initialization."""
        from src.agents.document_reader import DocumentReaderAgent

        agent = DocumentReaderAgent()
        assert agent._temp_dir.exists()

    @patch("src.agents.document_reader.QdrantStore")
    @patch("src.agents.document_reader.DocumentChunker")
    @patch("src.agents.document_reader.SECEdgarTool")
    def test_search_filing_no_results(self, mock_sec, mock_chunker, mock_qdrant):
        """Test search with no results."""
        from src.agents.document_reader import DocumentReaderAgent

        mock_qdrant_instance = MagicMock()
        mock_qdrant.return_value = mock_qdrant_instance
        mock_qdrant_instance.search_sec_filing.return_value = []

        mock_sec_instance = MagicMock()
        mock_sec.return_value = mock_sec_instance
        mock_sec_instance.get_latest_10k.return_value = None

        agent = DocumentReaderAgent()
        result = agent.search_filing("NVDA", "China risks", auto_index=True)

        assert result.ticker == "NVDA"
        assert len(result.passages) == 0

    @patch("src.agents.document_reader.QdrantStore")
    @patch("src.agents.document_reader.DocumentChunker")
    @patch("src.agents.document_reader.SECEdgarTool")
    def test_search_filing_with_results(self, mock_sec, mock_chunker, mock_qdrant):
        """Test search with results."""
        from src.agents.document_reader import DocumentReaderAgent

        mock_qdrant_instance = MagicMock()
        mock_qdrant.return_value = mock_qdrant_instance
        mock_qdrant_instance.search_sec_filing.return_value = [
            {"content": "China risks...", "score": 0.85, "metadata": {"filing_date": "2024-01-01"}}
        ]

        agent = DocumentReaderAgent()
        result = agent.search_filing("NVDA", "China risks", auto_index=False)

        assert len(result.passages) == 1
        assert result.filing_date == "2024-01-01"

    @patch("src.agents.document_reader.QdrantStore")
    @patch("src.agents.document_reader.DocumentChunker")
    @patch("src.agents.document_reader.SECEdgarTool")
    def test_index_filing_unsupported_form(self, mock_sec, mock_chunker, mock_qdrant):
        """Test indexing unsupported form type."""
        from src.agents.document_reader import DocumentReaderAgent

        agent = DocumentReaderAgent()
        result = agent.index_filing("NVDA", form_type="8-K")

        assert result is False

    @patch("src.agents.document_reader.QdrantStore")
    @patch("src.agents.document_reader.DocumentChunker")
    @patch("src.agents.document_reader.SECEdgarTool")
    def test_index_filing_no_filing_found(self, mock_sec, mock_chunker, mock_qdrant):
        """Test indexing when no filing found."""
        from src.agents.document_reader import DocumentReaderAgent

        mock_sec_instance = MagicMock()
        mock_sec.return_value = mock_sec_instance
        mock_sec_instance.get_latest_10k.return_value = None

        agent = DocumentReaderAgent()
        result = agent.index_filing("INVALID")

        assert result is False

    @patch("src.agents.document_reader.QdrantStore")
    @patch("src.agents.document_reader.DocumentChunker")
    @patch("src.agents.document_reader.SECEdgarTool")
    def test_index_filing_download_failed(self, mock_sec, mock_chunker, mock_qdrant):
        """Test indexing when download fails."""
        from src.agents.document_reader import DocumentReaderAgent

        mock_sec_instance = MagicMock()
        mock_sec.return_value = mock_sec_instance
        mock_filing = MagicMock()
        mock_sec_instance.get_latest_10k.return_value = mock_filing
        mock_sec_instance.download_filing.return_value = None

        agent = DocumentReaderAgent()
        result = agent.index_filing("NVDA")

        assert result is False

    @patch("src.agents.document_reader.QdrantStore")
    @patch("src.agents.document_reader.DocumentChunker")
    @patch("src.agents.document_reader.SECEdgarTool")
    def test_index_filing_text_too_short(self, mock_sec, mock_chunker, mock_qdrant):
        """Test indexing when extracted text is too short."""
        import tempfile
        from pathlib import Path

        from src.agents.document_reader import DocumentReaderAgent

        mock_sec_instance = MagicMock()
        mock_sec.return_value = mock_sec_instance
        mock_filing = MagicMock()
        mock_sec_instance.get_latest_10k.return_value = mock_filing

        # Create a temp file with short content
        with tempfile.NamedTemporaryFile(mode="w", suffix=".htm", delete=False) as f:
            f.write("<html>short</html>")
            temp_path = Path(f.name)

        mock_sec_instance.download_filing.return_value = temp_path

        agent = DocumentReaderAgent()
        result = agent.index_filing("NVDA")

        assert result is False
        temp_path.unlink()

    @patch("src.agents.document_reader.QdrantStore")
    @patch("src.agents.document_reader.DocumentChunker")
    @patch("src.agents.document_reader.SECEdgarTool")
    def test_index_filing_success(self, mock_sec, mock_chunker, mock_qdrant):
        """Test successful indexing."""
        import tempfile
        from pathlib import Path

        from src.agents.document_reader import DocumentReaderAgent

        mock_sec_instance = MagicMock()
        mock_sec.return_value = mock_sec_instance
        mock_filing = MagicMock()
        mock_filing.filing_date = "2024-01-01"
        mock_filing.company_name = "NVIDIA"
        mock_filing.accession_number = "001"
        mock_filing.file_url = "https://example.com"
        mock_sec_instance.get_latest_10k.return_value = mock_filing

        # Create a temp file with enough content
        with tempfile.NamedTemporaryFile(mode="w", suffix=".htm", delete=False) as f:
            f.write("<html><body>" + "Test content. " * 500 + "</body></html>")
            temp_path = Path(f.name)

        mock_sec_instance.download_filing.return_value = temp_path

        mock_chunker_instance = MagicMock()
        mock_chunker.return_value = mock_chunker_instance
        mock_chunker_instance.chunk_text.return_value = [MagicMock()]

        mock_qdrant_instance = MagicMock()
        mock_qdrant.return_value = mock_qdrant_instance
        mock_qdrant_instance.add_chunks.return_value = 1

        agent = DocumentReaderAgent()
        result = agent.index_filing("NVDA")

        assert result is True
        temp_path.unlink()

    @patch("src.agents.document_reader.QdrantStore")
    @patch("src.agents.document_reader.DocumentChunker")
    @patch("src.agents.document_reader.SECEdgarTool")
    def test_index_filing_chunking_failed(self, mock_sec, mock_chunker, mock_qdrant):
        """Test indexing when chunking fails."""
        import tempfile
        from pathlib import Path

        from src.agents.document_reader import DocumentReaderAgent

        mock_sec_instance = MagicMock()
        mock_sec.return_value = mock_sec_instance
        mock_filing = MagicMock()
        mock_filing.filing_date = "2024-01-01"
        mock_filing.company_name = "NVIDIA"
        mock_filing.accession_number = "001"
        mock_filing.file_url = "https://example.com"
        mock_sec_instance.get_latest_10k.return_value = mock_filing

        with tempfile.NamedTemporaryFile(mode="w", suffix=".htm", delete=False) as f:
            f.write("<html><body>" + "Test content. " * 500 + "</body></html>")
            temp_path = Path(f.name)

        mock_sec_instance.download_filing.return_value = temp_path

        mock_chunker_instance = MagicMock()
        mock_chunker.return_value = mock_chunker_instance
        mock_chunker_instance.chunk_text.return_value = []  # No chunks

        agent = DocumentReaderAgent()
        result = agent.index_filing("NVDA")

        assert result is False
        temp_path.unlink()

    @patch("src.agents.document_reader.QdrantStore")
    @patch("src.agents.document_reader.DocumentChunker")
    @patch("src.agents.document_reader.SECEdgarTool")
    def test_extract_text_fallback(self, mock_sec, mock_chunker, mock_qdrant):
        """Test text extraction fallback when unstructured not available."""
        import tempfile
        from pathlib import Path

        from src.agents.document_reader import DocumentReaderAgent

        with tempfile.NamedTemporaryFile(mode="w", suffix=".htm", delete=False) as f:
            f.write("<html><body><p>Test paragraph</p></body></html>")
            temp_path = Path(f.name)

        agent = DocumentReaderAgent()

        # Just test that extraction works (will use fallback HTML parsing)
        text = agent._extract_text_from_html(temp_path)
        assert "Test paragraph" in text

        temp_path.unlink()

    @patch("src.agents.document_reader.QdrantStore")
    @patch("src.agents.document_reader.DocumentChunker")
    @patch("src.agents.document_reader.SECEdgarTool")
    def test_extract_text_exception(self, mock_sec, mock_chunker, mock_qdrant):
        """Test text extraction when an exception occurs."""
        import sys
        import tempfile
        from pathlib import Path

        from src.agents.document_reader import DocumentReaderAgent

        with tempfile.NamedTemporaryFile(mode="w", suffix=".htm", delete=False) as f:
            f.write("<html><body><p>Test content</p></body></html>")
            temp_path = Path(f.name)

        agent = DocumentReaderAgent()

        # Mock the unstructured import to raise a generic exception
        mock_module = MagicMock()
        mock_module.partition.html.partition_html.side_effect = Exception("Parse error")

        with patch.dict(
            sys.modules,
            {
                "unstructured": mock_module,
                "unstructured.partition": mock_module.partition,
                "unstructured.partition.html": mock_module.partition.html,
            },
        ):
            text = agent._extract_text_from_html(temp_path)
            # Should still get some text via fallback
            assert len(text) > 0

        temp_path.unlink()

    @patch("src.agents.document_reader.QdrantStore")
    @patch("src.agents.document_reader.DocumentChunker")
    @patch("src.agents.document_reader.SECEdgarTool")
    def test_generate_summary_empty(self, mock_sec, mock_chunker, mock_qdrant):
        """Test summary generation with no results."""
        from src.agents.document_reader import DocumentReaderAgent

        agent = DocumentReaderAgent()
        summary = agent._generate_summary("NVDA", "China", [])

        assert "No relevant passages found" in summary

    @patch("src.agents.document_reader.QdrantStore")
    @patch("src.agents.document_reader.DocumentChunker")
    @patch("src.agents.document_reader.SECEdgarTool")
    def test_generate_summary_with_results(self, mock_sec, mock_chunker, mock_qdrant):
        """Test summary generation with results."""
        from src.agents.document_reader import DocumentReaderAgent

        agent = DocumentReaderAgent()
        results = [
            {
                "content": "x" * 600,  # Long content
                "score": 0.85,
                "metadata": {"section": "Risk Factors"},
            }
        ]
        summary = agent._generate_summary("NVDA", "China", results)

        assert "Passage 1" in summary
        assert "..." in summary


class TestDocumentReaderNode:
    """Tests for document reader LangGraph node."""

    def test_run_document_reader_node_no_input(self):
        """Test node with no input."""
        from src.agents.document_reader import run_document_reader_node

        state = {"tickers": [], "document_queries": [], "errors": []}
        result = run_document_reader_node(state)

        assert result["document_analysis"] is None

    @patch("src.agents.document_reader.DocumentReaderAgent")
    def test_run_document_reader_node_success(self, mock_agent_class):
        """Test node execution."""
        from src.agents.document_reader import DocumentSearchResult, run_document_reader_node

        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.search_filing.return_value = DocumentSearchResult(
            ticker="NVDA",
            filing_type="10-K",
            filing_date="2024-01-01",
            query="China",
            passages=[],
            summary="Summary",
            errors=[],
        )

        state = {"tickers": ["NVDA"], "document_queries": ["China"], "errors": []}
        result = run_document_reader_node(state)

        assert result["document_analysis"] is not None


class TestSynthesizerAgent:
    """Tests for SynthesizerAgent."""

    def test_create_llm_groq(self):
        """Test LLM creation with Groq."""
        with patch("src.agents.synthesizer.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.use_groq = True
            mock_settings_obj.groq_api_key.get_secret_value.return_value = "test-key"
            mock_settings.return_value = mock_settings_obj

            with patch("langchain_groq.ChatGroq") as mock_groq:
                from src.agents.synthesizer import SynthesizerAgent

                agent = SynthesizerAgent()
                mock_groq.assert_called_once()

    def test_create_llm_azure(self):
        """Test LLM creation with Azure OpenAI."""
        with patch("src.agents.synthesizer.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.use_groq = False
            mock_settings_obj.use_azure_openai = True
            mock_settings_obj.azure_openai_endpoint = "https://test.openai.azure.com"
            mock_settings_obj.azure_openai_api_key.get_secret_value.return_value = "test-key"
            mock_settings_obj.azure_openai_deployment = "gpt-4"
            mock_settings.return_value = mock_settings_obj

            with patch("langchain_openai.AzureChatOpenAI") as mock_azure:
                from src.agents.synthesizer import SynthesizerAgent

                agent = SynthesizerAgent()
                mock_azure.assert_called_once()

    def test_create_llm_openai(self):
        """Test LLM creation with OpenAI."""
        with patch("src.agents.synthesizer.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.use_groq = False
            mock_settings_obj.use_azure_openai = False
            mock_settings_obj.openai_api_key.get_secret_value.return_value = "test-key"
            mock_settings.return_value = mock_settings_obj

            with patch("langchain_openai.ChatOpenAI") as mock_openai:
                from src.agents.synthesizer import SynthesizerAgent

                agent = SynthesizerAgent()
                mock_openai.assert_called_once()

    def test_create_llm_no_provider(self):
        """Test LLM creation with no provider."""
        with patch("src.agents.synthesizer.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.use_groq = False
            mock_settings_obj.use_azure_openai = False
            mock_settings_obj.openai_api_key = None
            mock_settings.return_value = mock_settings_obj

            from src.agents.synthesizer import SynthesizerAgent

            with pytest.raises(RuntimeError, match="No LLM provider configured"):
                SynthesizerAgent()

    def test_format_context(self):
        """Test context formatting."""
        with patch("src.agents.synthesizer.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.use_groq = True
            mock_settings_obj.groq_api_key.get_secret_value.return_value = "test"
            mock_settings.return_value = mock_settings_obj

            with patch("langchain_groq.ChatGroq"):
                from src.agents.synthesizer import SynthesizerAgent

                agent = SynthesizerAgent()

            context = agent._format_context(
                query="Analyze NVDA",
                market_data={"summary": "Market summary"},
                document_analysis=[{"ticker": "NVDA", "query": "China", "summary": "Doc summary"}],
                news_analysis=[{"summary": "News summary"}],
            )

            assert "Analyze NVDA" in context
            assert "Market summary" in context

    def test_format_context_with_json(self):
        """Test context formatting with JSON market data."""
        with patch("src.agents.synthesizer.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.use_groq = True
            mock_settings_obj.groq_api_key.get_secret_value.return_value = "test"
            mock_settings.return_value = mock_settings_obj

            with patch("langchain_groq.ChatGroq"):
                from src.agents.synthesizer import SynthesizerAgent

                agent = SynthesizerAgent()

            context = agent._format_context(
                query="Analyze NVDA",
                market_data={"quotes": {"NVDA": {"price": 875}}},  # No summary key
                document_analysis=None,
                news_analysis=None,
            )

            assert "quotes" in context

    def test_format_context_with_passages(self):
        """Test context formatting with document passages."""
        with patch("src.agents.synthesizer.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.use_groq = True
            mock_settings_obj.groq_api_key.get_secret_value.return_value = "test"
            mock_settings.return_value = mock_settings_obj

            with patch("langchain_groq.ChatGroq"):
                from src.agents.synthesizer import SynthesizerAgent

                agent = SynthesizerAgent()

            context = agent._format_context(
                query="Analyze NVDA",
                market_data=None,
                document_analysis=[
                    {
                        "ticker": "NVDA",
                        "query": "China",
                        "filing_date": "2024-01-01",
                        "passages": [{"content": "Risk content here", "score": 0.85}],
                    }
                ],
                news_analysis=None,
            )

            assert "NVDA" in context
            assert "Passage" in context

    def test_extract_executive_summary(self):
        """Test executive summary extraction."""
        with patch("src.agents.synthesizer.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.use_groq = True
            mock_settings_obj.groq_api_key.get_secret_value.return_value = "test"
            mock_settings.return_value = mock_settings_obj

            with patch("langchain_groq.ChatGroq"):
                from src.agents.synthesizer import SynthesizerAgent

                agent = SynthesizerAgent()

            report = """# Report
## Executive Summary
This is the summary.

## Detailed Analysis
More content here.
"""
            summary = agent._extract_executive_summary(report)
            assert "This is the summary" in summary

    def test_extract_executive_summary_fallback(self):
        """Test executive summary extraction fallback."""
        with patch("src.agents.synthesizer.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.use_groq = True
            mock_settings_obj.groq_api_key.get_secret_value.return_value = "test"
            mock_settings.return_value = mock_settings_obj

            with patch("langchain_groq.ChatGroq"):
                from src.agents.synthesizer import SynthesizerAgent

                agent = SynthesizerAgent()

            report = "Just some text without headers. " * 50
            summary = agent._extract_executive_summary(report)
            assert "..." in summary

    def test_generate_fallback_report(self):
        """Test fallback report generation."""
        with patch("src.agents.synthesizer.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.use_groq = True
            mock_settings_obj.groq_api_key.get_secret_value.return_value = "test"
            mock_settings.return_value = mock_settings_obj

            with patch("langchain_groq.ChatGroq"):
                from src.agents.synthesizer import SynthesizerAgent

                agent = SynthesizerAgent()

            report = agent._generate_fallback_report(
                query="Analyze NVDA",
                tickers=["NVDA"],
                market_data={"summary": "Market summary"},
                document_analysis=[{"summary": "Doc summary"}],
                news_analysis=[{"summary": "News summary"}],
            )

            assert "NVDA" in report
            assert "Market summary" in report

    def test_synthesize_success(self):
        """Test successful synthesis."""
        with patch("src.agents.synthesizer.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.use_groq = True
            mock_settings_obj.groq_api_key.get_secret_value.return_value = "test"
            mock_settings.return_value = mock_settings_obj

            with patch("langchain_groq.ChatGroq") as mock_groq:
                mock_llm = MagicMock()
                mock_groq.return_value = mock_llm
                mock_response = MagicMock()
                mock_response.content = (
                    "## Executive Summary\nGreat report.\n\n## Analysis\nDetails."
                )
                mock_llm.invoke.return_value = mock_response

                from src.agents.synthesizer import ResearchReport, SynthesizerAgent

                agent = SynthesizerAgent()
                result = agent.synthesize(
                    query="Analyze NVDA",
                    tickers=["NVDA"],
                    market_data={"quotes": {}},
                    document_analysis=[{"passages": []}],
                    news_analysis=[{"summary": "News"}],
                )

                assert isinstance(result, ResearchReport)
                assert "NVDA" in result.title

    def test_synthesize_llm_error(self):
        """Test synthesis with LLM error."""
        with patch("src.agents.synthesizer.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.use_groq = True
            mock_settings_obj.groq_api_key.get_secret_value.return_value = "test"
            mock_settings.return_value = mock_settings_obj

            with patch("langchain_groq.ChatGroq") as mock_groq:
                mock_llm = MagicMock()
                mock_groq.return_value = mock_llm
                mock_llm.invoke.side_effect = Exception("LLM error")

                from src.agents.synthesizer import SynthesizerAgent

                agent = SynthesizerAgent()
                result = agent.synthesize(
                    query="Analyze NVDA",
                    tickers=["NVDA"],
                )

                assert any("LLM synthesis failed" in e for e in result.errors)


class TestSynthesizerNode:
    """Tests for synthesizer LangGraph node."""

    @patch("src.agents.synthesizer.SynthesizerAgent")
    def test_run_synthesizer_node(self, mock_agent_class):
        """Test node execution."""
        from src.agents.synthesizer import ResearchReport, run_synthesizer_node

        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.synthesize.return_value = ResearchReport(
            title="Report",
            tickers=["NVDA"],
            generated_at="2024-01-01",
            executive_summary="Summary",
            full_report="Full report",
            data_sources=["Yahoo Finance"],
            errors=[],
        )

        state = {
            "query": "Analyze NVDA",
            "tickers": ["NVDA"],
            "market_data": {},
            "document_analysis": [],
            "news_analysis": [],
            "errors": [],
        }
        result = run_synthesizer_node(state)

        assert result["report"] is not None


class TestGraph:
    """Tests for LangGraph orchestration."""

    def test_parse_query(self):
        """Test query parsing."""
        from src.agents.graph import parse_query

        state = {
            "query": "Analyze NVDA and AMD for China risks",
            "tickers": [],
            "document_queries": [],
        }
        result = parse_query(state)

        assert "NVDA" in result["tickers"]
        assert "AMD" in result["tickers"]
        assert "China" in result["document_queries"]

    def test_parse_query_with_existing_tickers(self):
        """Test query parsing with pre-set tickers."""
        from src.agents.graph import parse_query

        state = {"query": "Analyze stocks", "tickers": ["AAPL"], "document_queries": []}
        result = parse_query(state)

        assert result["tickers"] == ["AAPL"]

    def test_should_analyze_documents_yes(self):
        """Test document analysis decision - yes."""
        from src.agents.graph import should_analyze_documents

        state = {"document_queries": ["China"]}
        result = should_analyze_documents(state)

        assert result == "document_reader"

    def test_should_analyze_documents_no(self):
        """Test document analysis decision - no."""
        from src.agents.graph import should_analyze_documents

        state = {"document_queries": []}
        result = should_analyze_documents(state)

        assert result == "parallel_analysis"

    @patch("src.agents.graph.StateGraph")
    def test_create_research_graph(self, mock_graph_class):
        """Test graph creation."""
        from src.agents.graph import create_research_graph

        mock_graph = MagicMock()
        mock_graph_class.return_value = mock_graph
        mock_graph.compile.return_value = MagicMock()

        result = create_research_graph()

        assert result is not None
        mock_graph.add_node.assert_called()
        mock_graph.compile.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.agents.graph.create_research_graph")
    async def test_run_research(self, mock_create_graph):
        """Test async research execution."""
        from src.agents.graph import run_research

        mock_graph = MagicMock()
        mock_create_graph.return_value = mock_graph
        mock_graph.ainvoke = AsyncMock(
            return_value={
                "tickers": ["NVDA"],
                "report": {"title": "Report"},
                "errors": [],
            }
        )

        result = await run_research("Analyze NVDA", ["NVDA"])

        assert result["tickers"] == ["NVDA"]

    @patch("src.agents.graph.create_research_graph")
    def test_run_research_sync(self, mock_create_graph):
        """Test sync research execution."""
        from src.agents.graph import run_research_sync

        mock_graph = MagicMock()
        mock_create_graph.return_value = mock_graph
        mock_graph.invoke.return_value = {
            "tickers": ["NVDA"],
            "report": {"title": "Report"},
            "errors": [],
        }

        result = run_research_sync("Analyze NVDA")

        assert result["report"] is not None
