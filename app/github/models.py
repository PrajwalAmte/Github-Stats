from pydantic import BaseModel, Field


class ContributionDay(BaseModel):
    """A single day's contribution count."""

    date: str
    contribution_count: int = Field(alias="contributionCount")


class ContributionWeek(BaseModel):
    """A week of contribution days."""

    contribution_days: list[ContributionDay] = Field(alias="contributionDays")


class ContributionCalendar(BaseModel):
    """Full contribution calendar."""

    total_contributions: int = Field(alias="totalContributions")
    weeks: list[ContributionWeek]


class ContributionsCollection(BaseModel):
    """User contributions collection."""

    contribution_calendar: ContributionCalendar = Field(alias="contributionCalendar")
    total_commit_contributions: int = Field(alias="totalCommitContributions")
    total_pull_request_contributions: int = Field(alias="totalPullRequestContributions")
    total_issue_contributions: int = Field(alias="totalIssueContributions")
    total_pull_request_review_contributions: int = Field(
        alias="totalPullRequestReviewContributions"
    )


class LanguageNode(BaseModel):
    name: str
    color: str | None = None


class LanguageEdge(BaseModel):
    """Language with byte size."""

    size: int
    node: LanguageNode


class RepositoryLanguages(BaseModel):
    """Repository language breakdown."""

    edges: list[LanguageEdge] = []


class GithubRepository(BaseModel):
    """GitHub repository from GraphQL."""

    stargazer_count: int = Field(alias="stargazerCount", default=0)
    fork_count: int = Field(alias="forkCount", default=0)
    is_fork: bool = Field(alias="isFork", default=False)
    languages: RepositoryLanguages | None = None


class PageInfo(BaseModel):
    has_next_page: bool = Field(alias="hasNextPage", default=False)
    end_cursor: str | None = Field(alias="endCursor", default=None)


class RepositoryConnection(BaseModel):
    """Paginated repository connection."""

    total_count: int = Field(alias="totalCount", default=0)
    nodes: list[GithubRepository]
    page_info: PageInfo = Field(alias="pageInfo")


class FollowersConnection(BaseModel):
    """Followers connection."""

    total_count: int = Field(alias="totalCount")


class GithubUser(BaseModel):
    """GitHub user from GraphQL."""

    login: str
    name: str | None = None
    followers: FollowersConnection
    repositories: RepositoryConnection
    contributions_collection: ContributionsCollection = Field(alias="contributionsCollection")
