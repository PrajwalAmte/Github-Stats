"""GitHub GraphQL queries.

Everything a card needs comes back from one query: profile counts, the
contribution calendar, and per-repo language sizes inlined on each repo
node. The old design made one extra request per repository for
languages, which is what made syncs slow enough to need a database.

Repositories are always filtered to `privacy: PUBLIC`. Cards and
history.json get published, so a token that can see private repos
must not leak their count, stars or language mix.
"""

_REPO_FIELDS = """
      totalCount
      nodes {
        stargazerCount
        forkCount
        isFork
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
              color
            }
          }
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
"""

USER_QUERY = f"""
query($login: String!) {{
  user(login: $login) {{
    login
    name
    followers {{
      totalCount
    }}
    contributionsCollection {{
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      contributionCalendar {{
        totalContributions
        weeks {{
          contributionDays {{
            date
            contributionCount
          }}
        }}
      }}
    }}
    repositories(
      first: 100
      ownerAffiliations: OWNER
      privacy: PUBLIC
      orderBy: {{field: STARGAZERS, direction: DESC}}
    ) {{{_REPO_FIELDS}    }}
  }}
}}
"""

REPOS_PAGE_QUERY = f"""
query($login: String!, $cursor: String!) {{
  user(login: $login) {{
    repositories(
      first: 100
      after: $cursor
      ownerAffiliations: OWNER
      privacy: PUBLIC
      orderBy: {{field: STARGAZERS, direction: DESC}}
    ) {{{_REPO_FIELDS}    }}
  }}
}}
"""
