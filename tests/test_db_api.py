import json
import os
from unittest.mock import MagicMock

import pytest

from db import api as db_api


@pytest.fixture
def cache_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(db_api, "API_DIR", str(tmp_path))
    return tmp_path


class FakeResponse:
    def __init__(self, status=200, json_data=None):
        self.status = status
        self._json_data = json_data

    async def json(self):
        return self._json_data


class FakeGetContextManager:
    def __init__(self, response=None, exception=None):
        self._response = response
        self._exception = exception

    async def __aenter__(self):
        if self._exception is not None:
            raise self._exception
        return self._response

    async def __aexit__(self, *args):
        return False


def make_session(response=None, exception=None):
    session = MagicMock()
    session.get = MagicMock(return_value=FakeGetContextManager(response=response, exception=exception))
    return session


class FakeClientSession:
    """Stands in for `aiohttp.ClientSession()` used as an async context manager."""

    def __init__(self, response_by_url):
        self._response_by_url = response_by_url

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def get(self, url, timeout=None):
        entry = self._response_by_url.get(url)
        if isinstance(entry, Exception):
            return FakeGetContextManager(exception=entry)
        return FakeGetContextManager(response=entry)


class TestFetchOrLoadCache:
    async def test_fetches_and_caches_on_success(self, cache_dir):
        url = "https://example.com/data"
        payload = {"results": [{"id": 1}]}
        session = make_session(response=FakeResponse(200, payload))

        result = await db_api.fetch_or_load_cache(session, url, "data.json")

        assert result == payload
        cached_path = os.path.join(str(cache_dir), "data.json")
        assert os.path.exists(cached_path)
        with open(cached_path, encoding="utf-8") as f:
            assert json.load(f) == payload

    async def test_falls_back_to_cache_on_http_error(self, cache_dir):
        url = "https://example.com/data"
        cached_path = os.path.join(str(cache_dir), "data.json")
        with open(cached_path, "w", encoding="utf-8") as f:
            json.dump({"results": ["cached"]}, f)
        session = make_session(response=FakeResponse(500))

        result = await db_api.fetch_or_load_cache(session, url, "data.json")

        assert result == {"results": ["cached"]}

    async def test_falls_back_to_cache_on_network_exception(self, cache_dir):
        url = "https://example.com/data"
        cached_path = os.path.join(str(cache_dir), "data.json")
        with open(cached_path, "w", encoding="utf-8") as f:
            json.dump({"results": ["cached2"]}, f)
        session = make_session(exception=ConnectionError("boom"))

        result = await db_api.fetch_or_load_cache(session, url, "data.json")

        assert result == {"results": ["cached2"]}

    async def test_returns_empty_results_when_no_cache_and_error(self, cache_dir):
        url = "https://example.com/data"
        session = make_session(response=FakeResponse(500))

        result = await db_api.fetch_or_load_cache(session, url, "missing.json")

        assert result == {"results": []}

    async def test_returns_empty_results_when_cache_file_corrupt(self, cache_dir):
        url = "https://example.com/data"
        cached_path = os.path.join(str(cache_dir), "data.json")
        with open(cached_path, "w", encoding="utf-8") as f:
            f.write("not valid json")
        session = make_session(response=FakeResponse(500))

        result = await db_api.fetch_or_load_cache(session, url, "data.json")

        assert result == {"results": []}


class TestGetApiData:
    async def test_get_api_data_returns_lessons_and_chords(self, cache_dir, monkeypatch):
        response_map = {
            db_api.LESSONS_API_URL: FakeResponse(200, {"results": ["lesson"]}),
            db_api.CHORDS_API_URL: FakeResponse(200, {"results": ["chord"]}),
        }
        monkeypatch.setattr(db_api.aiohttp, "ClientSession", lambda: FakeClientSession(response_map))

        result = await db_api.get_api_data()

        assert result == [{"results": ["lesson"]}, {"results": ["chord"]}]


class TestGetLessonDetail:
    async def test_get_lesson_detail_fetches_by_uuid(self, cache_dir, monkeypatch):
        lesson_uuid = "abc-123"
        url = f"https://api.guitar0.net/api/v1/lessons/{lesson_uuid}/"
        payload = {"uuid": lesson_uuid, "songs": []}
        monkeypatch.setattr(
            db_api.aiohttp, "ClientSession", lambda: FakeClientSession({url: FakeResponse(200, payload)})
        )

        result = await db_api.get_lesson_detail(lesson_uuid)

        assert result == payload
