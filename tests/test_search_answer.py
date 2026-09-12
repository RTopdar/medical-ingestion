"""Tests for SearchService.answer() using ChatRouterService instead of ChatOpenRouter directly."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import MagicMock, patch

from retrieval.search import SearchService


class _FakeStreamChunk:
    def __init__(self, content: str):
        self.choices = [MagicMock(delta=MagicMock(content=content))]


class TestSearchServiceAnswer:
    def test_answer_streams_text_from_chat_router_service(self):
        service = SearchService.__new__(SearchService)  # bypass __init__ (needs live BM25/Qdrant)
        fake_router = MagicMock()
        fake_router.stream.return_value = iter(
            [_FakeStreamChunk("Hello "), _FakeStreamChunk("world")]
        )
        service.chat_router = fake_router

        chunks = list(service.answer("What is X?", ["some context chunk"], citations=[{"source": "doc1"}]))

        assert "".join(chunks) == "Hello world"
        fake_router.stream.assert_called_once()
        call_args = fake_router.stream.call_args
        messages = call_args.args[0] if call_args.args else call_args.kwargs["messages"]
        assert messages[0]["role"] == "user"
        assert "What is X?" in messages[0]["content"]
        assert "some context chunk" in messages[0]["content"]
        assert "[Source: doc1]" in messages[0]["content"]

    def test_answer_skips_empty_content_chunks(self):
        service = SearchService.__new__(SearchService)
        fake_router = MagicMock()
        fake_router.stream.return_value = iter(
            [_FakeStreamChunk(""), _FakeStreamChunk("only this")]
        )
        service.chat_router = fake_router

        chunks = list(service.answer("Q", ["ctx"]))

        assert chunks == ["only this"]
