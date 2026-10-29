"""Tests for stats aggregation and the in-process cache."""

import pytest

from app.config import settings
from app.exceptions import GithubApiError, GithubNotFoundError
from app.github.models import GithubUser
from app.stats import service
from app.stats.service import build_stats, get_user_stats
from tests.fixtures import github_user_payload


class FakeClient:
    """Stands in for GithubClient; returns or raises whatever it's given."""

    def __init__(self, result):
        self.result = result
        self.calls = 0

    async def fetch_user(self, login: str) -> GithubUser:
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


@pytest.fixture(autouse=True)
def _clear_cache():
    service.clear_cache()
    yield
    service.clear_cache()


def test_build_stats_aggregates_counts():
    stats = build_stats(GithubUser(**github_user_payload()))

    assert stats.username == "octocat"
    assert stats.followers == 42
    assert stats.total_commits == 120
    assert stats.total_pull_requests == 8
    assert stats.total_issues == 4
    assert stats.total_reviews == 6
    assert stats.contribution_count == 3
    assert stats.repository_count == 3
    assert stats.star_count == 115  # forks still count toward stars
    assert stats.fork_count == 53


def test_build_stats_streaks():
    stats = build_stats(GithubUser(**github_user_payload(days_active=3)))

    assert stats.current_streak == 3
    assert stats.longest_streak == 3


def test_build_stats_languages_skip_forks_and_keep_colors():
    stats = build_stats(GithubUser(**github_user_payload()))

    assert [lang.name for lang in stats.languages] == ["Python", "Shell"]
    assert stats.languages[0].bytes == 4000
    assert stats.languages[0].percentage == 80.0
    assert stats.languages[0].color == "#3572A5"


def test_build_stats_no_repos():
    stats = build_stats(GithubUser(**github_user_payload(repos=[])))

    assert stats.languages == []
    assert stats.star_count == 0


async def test_cache_hit_skips_github():
    client = FakeClient(GithubUser(**github_user_payload()))

    first = await get_user_stats("octocat", client)
    second = await get_user_stats("OctoCat", client)  # usernames are case-insensitive

    assert first is second
    assert client.calls == 1


async def test_serves_stale_copy_when_github_fails(monkeypatch):
    good = FakeClient(GithubUser(**github_user_payload()))
    cached = await get_user_stats("octocat", good)

    monkeypatch.setattr(settings, "cache_ttl_seconds", 0)  # force a refetch
    result = await get_user_stats("octocat", FakeClient(GithubApiError("boom")))

    assert result is cached


async def test_raises_when_github_fails_and_nothing_cached():
    with pytest.raises(GithubApiError):
        await get_user_stats("octocat", FakeClient(GithubApiError("boom")))


async def test_not_found_is_not_masked_by_stale_copy(monkeypatch):
    await get_user_stats("octocat", FakeClient(GithubUser(**github_user_payload())))

    monkeypatch.setattr(settings, "cache_ttl_seconds", 0)
    with pytest.raises(GithubNotFoundError):
        await get_user_stats("octocat", FakeClient(GithubNotFoundError("gone")))
