"""Custom exceptions for GitHub API interactions."""


class GithubApiError(Exception):
    """Base exception for GitHub API errors."""

    pass


class GithubRateLimitError(GithubApiError):
    """GitHub API rate limit exceeded."""

    pass


class GithubNotFoundError(GithubApiError):
    """GitHub user or resource not found."""

    pass


class GithubAuthenticationError(GithubApiError):
    """GitHub authentication failed."""

    pass
