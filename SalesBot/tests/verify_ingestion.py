import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import asyncio


# A more robust mocking function
def mock_package(name):
    mock = MagicMock()
    sys.modules[name] = mock
    return mock


# Mock ALL external dependencies that might be imported
mock_package("agents")
mock_package("agents.extensions")
mock_package("agents.extensions.models")
mock_package("agents.extensions.models.litellm_model")
mock_package("agents.extensions.handoff_prompt")
mock_package("opik")
mock_package("opik.integrations")
mock_package("opik.integrations.litellm")
mock_package("opik.integrations.openai")
mock_package("opik.integrations.openai.agents")
mock_package("crawl4ai")
mock_package("crawl4ai.deep_crawling")
mock_package("crawl4ai.async_configs")
mock_package("crawl4ai.content_scraping_strategy")
mock_package("crawl4ai.markdown_generation_strategy")
mock_package("logger")

# Add the root directory to sys.path to find 'app' and 'rag'
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

# Now import the module
try:
    import app.agents.crawl_persona.agent as crawl_agent

    print("✓ Module app.agents.crawl_persona.agent imported successfully")
except Exception as e:
    print(f"✗ Failed to import app.agents.crawl_persona.agent: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)


class TestIngestionLogic(unittest.TestCase):

    @patch("app.agents.crawl_persona.agent.ingest_text_content")
    @patch("app.agents.crawl_persona.agent.ETLPipeLine")
    @patch("app.agents.crawl_persona.agent.AsyncWebCrawler")
    @patch("app.agents.crawl_persona.agent.Runner")
    async def test_chromadb_ingestion(
        self, mock_runner, mock_crawler, mock_etl, mock_ingest
    ):
        # Setup mocks
        mock_runner.run = MagicMock()
        mock_runner.run.return_value = MagicMock(final_output=MagicMock())

        mock_crawler_instance = MagicMock()
        mock_crawler.return_value.__aenter__.return_value = mock_crawler_instance
        mock_crawler_instance.arun.return_value = [
            MagicMock(
                success=True,
                markdown="Sample content",
                url="https://example.com",
                metadata={},
            )
        ]

        # Test ChromaDB path
        with patch.dict(os.environ, {"VECTORDB": "chromadb"}):
            await crawl_agent.run_crawl_persona_agent("https://example.com", "user123")
            mock_ingest.assert_called_once()
            mock_etl.assert_not_called()

    @patch("app.agents.crawl_persona.agent.ingest_text_content")
    @patch("app.agents.crawl_persona.agent.ETLPipeLine")
    @patch("app.agents.crawl_persona.agent.AsyncWebCrawler")
    @patch("app.agents.crawl_persona.agent.Runner")
    async def test_qdrant_ingestion(
        self, mock_runner, mock_crawler, mock_etl, mock_ingest
    ):
        # Setup mocks
        mock_runner.run = MagicMock()
        mock_runner.run.return_value = MagicMock(final_output=MagicMock())

        mock_crawler_instance = MagicMock()
        mock_crawler.return_value.__aenter__.return_value = mock_crawler_instance
        mock_crawler_instance.arun.return_value = [
            MagicMock(
                success=True,
                markdown="Sample content",
                url="https://example.com",
                metadata={},
            )
        ]

        mock_etl_instance = MagicMock()
        mock_etl.return_value = mock_etl_instance
        mock_etl_instance.run_pipeline_from_json.return_value = (True, "Success")

        # Test Qdrant path
        with patch.dict(os.environ, {"VECTORDB": "qdrant"}):
            await crawl_agent.run_crawl_persona_agent("https://example.com", "user123")
            mock_etl.assert_called_once()
            mock_ingest.assert_not_called()


async def run_tests():
    test = TestIngestionLogic()

    print("Testing ChromaDB path...")
    try:
        await test.test_chromadb_ingestion()
        print("✓ ChromaDB path OK")
    except Exception as e:
        print(f"✗ ChromaDB path FAILED: {e}")
        import traceback

        traceback.print_exc()

    print("Testing Qdrant path...")
    try:
        await test.test_qdrant_ingestion()
        print("✓ Qdrant path OK")
    except Exception as e:
        print(f"✗ Qdrant path FAILED: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(run_tests())
    except Exception as e:
        print(f"Test runner error: {e}")
        sys.exit(1)
