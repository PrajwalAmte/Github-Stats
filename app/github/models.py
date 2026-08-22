
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


class LanguageEdge(BaseModel):
    """Language with byte size."""

    size: int
    node: dict  # {name: str}


class RepositoryLanguages(BaseModel):
    """Repository language breakdown."""

    edges: list[LanguageEdge]


class PrimaryLanguage(BaseModel):
    """Primary language of a repository."""

    name: str


class GithubRepository(BaseModel):
    """GitHub repository from GraphQL."""

    id: str
    database_id: int = Field(alias="databaseId")
    name: str
    stargazer_count: int = Field(alias="stargazerCount", default=0)
    fork_count: int = Field(alias="forkCount", default=0)
    primary_language: PrimaryLanguage | None = Field(alias="primaryLanguage", default=None)
    is_fork: bool = Field(alias="isFork", default=False)
    pushed_at: str | None = Field(alias="pushedAt", default=None)
    languages: RepositoryLanguages | None = None


class RepositoryConnection(BaseModel):
    """Paginated repository connection."""

    nodes: list[GithubRepository]
    page_info: dict = Field(alias="pageInfo")  # {hasNextPage, endCursor}


class FollowersConnection(BaseModel):
    """Followers connection."""

    total_count: int = Field(alias="totalCount")


class FollowingConnection(BaseModel):
    """Following connection."""

    total_count: int = Field(alias="totalCount")


class GithubUser(BaseModel):
    """GitHub user from GraphQL."""

    login: str
    name: str | None = None
    avatar_url: str = Field(alias="avatarUrl")
    followers: FollowersConnection
    following: FollowingConnection
    repositories: RepositoryConnection
    contributions_collection: ContributionsCollection = Field(alias="contributionsCollection")


class GithubUserResponse(BaseModel):
    """Top-level GraphQL response."""

    user: GithubUser | None = None
