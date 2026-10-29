"""Shared test fixtures."""

from datetime import date, timedelta


def github_user_payload(
    login: str = "octocat",
    days_active: int = 3,
    repos: list[dict] | None = None,
) -> dict:
    """A GraphQL `user` payload shaped like the real USER_QUERY response.

    The last `days_active` days of the calendar (ending today) have one
    contribution each; everything earlier is zero.
    """
    today = date.today()
    days = [
        {
            "date": (today - timedelta(days=i)).isoformat(),
            "contributionCount": 1 if i < days_active else 0,
        }
        for i in range(13, -1, -1)
    ]
    if repos is None:
        repos = [
            _repo(10, 2, False, [("Python", 3000, "#3572A5"), ("Shell", 1000, "#89e051")]),
            _repo(5, 1, False, [("Python", 1000, "#3572A5")]),
            _repo(100, 50, True, [("C", 999999, "#555555")]),  # fork: languages ignored
        ]
    return {
        "login": login,
        "name": "The Octocat",
        "followers": {"totalCount": 42},
        "contributionsCollection": {
            "totalCommitContributions": 120,
            "totalPullRequestContributions": 8,
            "totalIssueContributions": 4,
            "totalPullRequestReviewContributions": 6,
            "contributionCalendar": {
                "totalContributions": days_active,
                "weeks": [
                    {"contributionDays": days[:7]},
                    {"contributionDays": days[7:]},
                ],
            },
        },
        "repositories": {
            "totalCount": len(repos),
            "nodes": repos,
            "pageInfo": {"hasNextPage": False, "endCursor": None},
        },
    }


def _repo(stars: int, forks: int, is_fork: bool, langs: list[tuple[str, int, str]]) -> dict:
    return {
        "stargazerCount": stars,
        "forkCount": forks,
        "isFork": is_fork,
        "languages": {
            "edges": [{"size": size, "node": {"name": n, "color": c}} for n, size, c in langs]
        },
    }
