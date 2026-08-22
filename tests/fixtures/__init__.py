"""Test fixtures and utilities."""

import pytest


@pytest.fixture
def mock_github_user_response():
    """Mock GitHub GraphQL user response."""
    return {
        "user": {
            "login": "testuser",
            "name": "Test User",
            "avatarUrl": "https://example.com/avatar.jpg",
            "followers": {"totalCount": 100},
            "following": {"totalCount": 50},
            "repositories": {
                "nodes": [
                    {
                        "id": "repo1",
                        "databaseId": 123456,
                        "name": "test-repo",
                        "stargazerCount": 10,
                        "forkCount": 2,
                        "primaryLanguage": {"name": "Python"},
                        "isFork": False,
                        "pushedAt": "2026-08-20T10:00:00Z",
                    }
                ],
                "pageInfo": {
                    "hasNextPage": False,
                    "endCursor": None,
                },
            },
            "contributionsCollection": {
                "contributionCalendar": {
                    "weeks": [
                        {
                            "contributionDays": [
                                {"date": "2026-08-20", "contributionCount": 5},
                                {"date": "2026-08-21", "contributionCount": 3},
                                {"date": "2026-08-22", "contributionCount": 7},
                            ]
                        }
                    ]
                },
                "totalCommitContributions": 100,
                "totalPullRequestContributions": 20,
                "totalIssueContributions": 10,
                "totalPullRequestReviewContributions": 15,
            },
        }
    }
