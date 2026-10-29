"""Tests for the GitHub client, with the network call stubbed out."""

import re

from app.config import settings
from app.github.client import GithubClient
from tests.fixtures import github_user_payload


async def test_every_repository_query_is_public_only(monkeypatch):
    """Cards and history.json are published, so even a token that can see
    private repos must never pull them in — on the first page or later ones."""
    monkeypatch.setattr(settings, "github_soft_budget_seconds", 60)
    sent: list[str] = []

    first = github_user_payload()
    first["repositories"]["pageInfo"] = {"hasNextPage": True, "endCursor": "c1"}
    second = {"repositories": github_user_payload()["repositories"]}

    async def fake_execute(self, http, token, query, variables):
        sent.append(query)
        return {"user": first if len(sent) == 1 else second}

    monkeypatch.setattr(GithubClient, "_execute_with_token", fake_execute)

    user = await GithubClient(tokens=["t"]).fetch_user("octocat")

    assert len(sent) == 2  # the first page and one paginated page
    assert len(user.repositories.nodes) == 6
    for query in sent:
        blocks = re.findall(r"repositories\((.*?)\)", query, re.S)
        assert blocks, "expected a repositories connection"
        assert all("privacy: PUBLIC" in b for b in blocks)
