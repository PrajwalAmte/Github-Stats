"""GitHub GraphQL queries."""

# Main user query - fetches profile, contributions, and repositories
USER_QUERY = """
query($username: String!, $repoCount: Int!) {
  user(login: $username) {
    login
    name
    avatarUrl
    followers {
      totalCount
    }
    following {
      totalCount
    }
    repositories(
      first: $repoCount
      ownerAffiliations: OWNER
      orderBy: {field: STARGAZERS, direction: DESC}
    ) {
      nodes {
        id
        databaseId
        name
        stargazerCount
        forkCount
        primaryLanguage {
          name
        }
        isFork
        pushedAt
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
    }
  }
}
"""

# Repository languages query - fetches language byte counts for a single repo
REPO_LANGUAGES_QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    languages(first: 100) {
      edges {
        size
        node {
          name
        }
      }
    }
  }
}
"""

# Paginated repositories query - for users with >100 repos
PAGINATED_REPOS_QUERY = """
query($username: String!, $cursor: String!, $repoCount: Int!) {
  user(login: $username) {
    repositories(
      first: $repoCount
      after: $cursor
      ownerAffiliations: OWNER
      orderBy: {field: STARGAZERS, direction: DESC}
    ) {
      nodes {
        id
        databaseId
        name
        stargazerCount
        forkCount
        primaryLanguage {
          name
        }
        isFork
        pushedAt
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""
