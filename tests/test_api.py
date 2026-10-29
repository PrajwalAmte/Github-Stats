"""Tests for the HTTP endpoints, with GitHub stubbed out."""

import pytest
from fastapi.testclient import TestClient

from app.api import routes_cards, routes_stats
from app.exceptions import GithubApiError, GithubNotFoundError
from app.github.models import GithubUser
from app.main import app
from app.stats.service import build_stats
from tests.fixtures import github_user_payload

client = TestClient(app)


@pytest.fixture
def stub_stats(monkeypatch):
    """Make get_user_stats return fixture stats, or raise a given error."""
    state: dict = {"error": None}

    async def fake_get_user_stats(username: str):
        if state["error"]:
            raise state["error"]
        return build_stats(GithubUser(**github_user_payload(login=username)))

    monkeypatch.setattr(routes_cards, "get_user_stats", fake_get_user_stats)
    monkeypatch.setattr(routes_stats, "get_user_stats", fake_get_user_stats)
    return state


@pytest.mark.parametrize("card", ["overview", "profile", "streak", "languages"])
def test_card_renders_with_edge_cache_headers(stub_stats, card):
    response = client.get(f"/v1/users/octocat/cards/{card}.svg")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    assert "stale-while-revalidate" in response.headers["cache-control"]
    assert "max-age=" in response.headers["cache-control"]
    assert "stale-if-error=" in response.headers["cache-control"]
    assert response.text.startswith("<svg")
    assert "octocat" in response.text


def test_unknown_user_renders_error_card(stub_stats):
    stub_stats["error"] = GithubNotFoundError("nope")
    response = client.get("/v1/users/ghost/cards/overview.svg")

    assert response.status_code == 200
    assert "user not found" in response.text


def test_github_outage_is_a_5xx_so_the_cdn_keeps_its_stale_card(stub_stats):
    stub_stats["error"] = GithubApiError("down")
    response = client.get("/v1/users/octocat/cards/overview.svg")

    assert response.status_code == 503
    assert "GitHub unavailable" in response.text
    assert response.headers["cache-control"] == "no-store"


def test_invalid_username_never_reaches_github(stub_stats):
    stub_stats["error"] = AssertionError("should not be called")
    response = client.get("/v1/users/-bad--name-/cards/overview.svg")

    assert response.status_code == 200
    assert "invalid username" in response.text


def test_unknown_card(stub_stats):
    response = client.get("/v1/users/octocat/cards/nope.svg")

    assert response.status_code == 200
    assert "unknown card" in response.text


def test_stats_json(stub_stats):
    response = client.get("/v1/users/octocat/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["total_commits"] == 120
    assert "fetched_at" in body["meta"]


def test_languages_json(stub_stats):
    response = client.get("/v1/users/octocat/languages")

    assert response.status_code == 200
    names = [lang["name"] for lang in response.json()["data"]["languages"]]
    assert names == ["Python", "Shell"]


def test_stats_json_not_found(stub_stats):
    stub_stats["error"] = GithubNotFoundError("nope")
    assert client.get("/v1/users/ghost/stats").status_code == 404


def test_stats_json_github_down(stub_stats):
    stub_stats["error"] = GithubApiError("down")
    assert client.get("/v1/users/octocat/stats").status_code == 503
