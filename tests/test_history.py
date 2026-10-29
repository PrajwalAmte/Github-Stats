"""Tests for the history.json snapshot file."""

import json
from dataclasses import replace
from datetime import UTC, datetime

from app.github.models import GithubUser
from app.stats.history import update_history
from app.stats.service import build_stats
from tests.fixtures import github_user_payload


def _stats(when: datetime):
    return build_stats(GithubUser(**github_user_payload()), when)


def test_creates_file_with_one_snapshot(tmp_path):
    path = tmp_path / "history.json"

    assert update_history(path, _stats(datetime(2026, 1, 1, 9, tzinfo=UTC))) is True

    data = json.loads(path.read_text())
    assert data["username"] == "octocat"
    assert [s["date"] for s in data["snapshots"]] == ["2026-01-01"]
    assert data["snapshots"][0]["total_commits"] == 120


def test_same_day_rerun_overwrites_instead_of_appending(tmp_path):
    path = tmp_path / "history.json"
    update_history(path, _stats(datetime(2026, 1, 1, 9, tzinfo=UTC)))

    later = replace(_stats(datetime(2026, 1, 1, 21, tzinfo=UTC)), total_commits=121)
    assert update_history(path, later) is True

    snapshots = json.loads(path.read_text())["snapshots"]
    assert len(snapshots) == 1
    assert snapshots[0]["total_commits"] == 121


def test_identical_rerun_leaves_file_untouched(tmp_path):
    path = tmp_path / "history.json"
    update_history(path, _stats(datetime(2026, 1, 1, 9, tzinfo=UTC)))

    assert update_history(path, _stats(datetime(2026, 1, 1, 21, tzinfo=UTC))) is False


def test_new_day_appends_in_date_order(tmp_path):
    path = tmp_path / "history.json"
    update_history(path, _stats(datetime(2026, 1, 2, tzinfo=UTC)))
    update_history(path, _stats(datetime(2026, 1, 1, tzinfo=UTC)))

    dates = [s["date"] for s in json.loads(path.read_text())["snapshots"]]
    assert dates == ["2026-01-01", "2026-01-02"]
