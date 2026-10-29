from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # GitHub. GITHUB_TOKEN may hold several comma-separated tokens; the
    # client rotates to the next one when a token is rate-limited or
    # revoked, so one exhausted token never takes the service down.
    github_token: str = ""
    github_api_url: str = "https://api.github.com/graphql"

    # Hard ceiling on one fetch from GitHub. Kept well under the timeout
    # of GitHub's image proxy (camo) so a slow upstream produces a
    # rendered card, not a broken image.
    github_timeout_seconds: float = 8.0

    # Repos are fetched 100 at a time, most-starred first, and each page
    # is a sequential round trip (~1-4s on large accounts). Stop paging
    # at max_repo_pages, or earlier once the next page would end past the
    # soft budget, so a cold card still renders fast. Remaining repos are
    # the least-starred ones, so stars and languages barely move.
    max_repo_pages: int = 5
    github_soft_budget_seconds: float = 4.0

    # In-process cache. The CDN does the heavy lifting; this keeps a warm
    # instance from re-fetching and lets it serve the last good result
    # when GitHub is failing.
    cache_ttl_seconds: int = 900
    stale_ttl_seconds: int = 86400
    cache_max_entries: int = 2000

    # Application
    environment: str = "development"
    log_level: str = "INFO"

    @property
    def github_tokens(self) -> list[str]:
        return [t.strip() for t in self.github_token.split(",") if t.strip()]


settings = Settings()
