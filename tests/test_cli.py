"""Tests for the card-rendering CLI used by the GitHub Action."""

from datetime import UTC, datetime

import pytest

from app import cli
from app.github.models import GithubUser
from app.stats.service import build_stats
from tests.fixtures import github_user_payload


@pytest.fixture
def fetched_at(monkeypatch):
    """Control the timestamp stamped on generated cards."""
    holder = {"value": datetime(2026, 1, 1, tzinfo=UTC)}

    async def fake_get_user_stats(username: str):
        return build_stats(GithubUser(**github_user_payload(login=username)), holder["value"])

    monkeypatch.setattr(cli, "get_user_stats", fake_get_user_stats)
    return holder


def test_writes_requested_cards(tmp_path, fetched_at):
    assert cli.main(["octocat", "--out", str(tmp_path), "--cards", "overview,streak"]) == 0

    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "history.json",
        "overview.svg",
        "streak.svg",
    ]


def test_no_history_flag(tmp_path, fetched_at):
    cli.main(["octocat", "--out", str(tmp_path), "--cards", "overview", "--no-history"])

    assert not (tmp_path / "history.json").exists()


def test_timestamp_only_change_leaves_file_untouched(tmp_path, fetched_at):
    cli.main(["octocat", "--out", str(tmp_path), "--cards", "profile"])
    before = (tmp_path / "profile.svg").read_text()

    fetched_at["value"] = datetime(2026, 1, 2, tzinfo=UTC)
    cli.main(["octocat", "--out", str(tmp_path), "--cards", "profile"])

    assert (tmp_path / "profile.svg").read_text() == before


def test_rejects_unknown_card(tmp_path, fetched_at):
    with pytest.raises(SystemExit):
        cli.main(["octocat", "--out", str(tmp_path), "--cards", "nope"])
