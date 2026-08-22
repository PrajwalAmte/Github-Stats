# GitHub Stats Service — Copilot Build Specification

Build a production-quality, lightweight GitHub statistics service for GitHub README profiles.

The service must periodically synchronize GitHub data into PostgreSQL, precompute all statistics, and expose a fast read-only API and SVG cards.

The most important architectural property is:

> **The read path must NEVER depend on GitHub being available.**

GitHub is an external source of truth. PostgreSQL is the application's source of truth for serving data. A failed synchronization must never corrupt or partially replace previously valid user-facing data.

Do not build an MVP or throwaway prototype. Build the complete architecture described below, but keep the implementation intentionally small and maintainable.

---

# 1. Goals

The service should:

1. Synchronize GitHub profile/repository/contribution/activity/language data.
2. Store normalized data in PostgreSQL.
3. Precompute expensive statistics during synchronization.
4. Serve statistics entirely from PostgreSQL.
5. Never call GitHub from a GET/read request.
6. Continue serving the last successful dataset if GitHub is unavailable.
7. Track synchronization freshness and failures.
8. Prevent concurrent synchronization for the same GitHub user.
9. Support historical daily snapshots.
10. Provide JSON API endpoints.
11. Provide SVG README cards using the same database statistics.
12. Be deployable using:

* Python
* FastAPI
* Vercel
* Supabase PostgreSQL
* GitHub Actions

13. Avoid Redis unless there is a demonstrated need.
14. Use HTTP/CDN caching rather than maintaining a separate cache service.

---

# 2. Technology stack

Use:

* Python 3.12+
* FastAPI
* Pydantic v2
* PostgreSQL
* Supabase PostgreSQL
* `httpx` for HTTP
* GitHub GraphQL API
* GitHub REST API only where GraphQL is insufficient
* SQLAlchemy 2.x OR a lightweight PostgreSQL driver such as `psycopg`
* Alembic for migrations
* pytest
* Ruff
* mypy where practical
* GitHub Actions
* Vercel

Prefer a simple architecture.

Do NOT introduce:

* Redis
* Celery
* Kafka
* RabbitMQ
* Kubernetes
* background daemons
* unnecessary microservices

The application is intentionally a small stateless API + scheduled synchronization system.

---

# 3. Repository structure

Create a clean structure similar to:

```
github-stats/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── routes_stats.py
│   │   ├── routes_sync.py
│   │   └── routes_health.py
│   ├── github/
│   │   ├── client.py
│   │   ├── graphql.py
│   │   ├── models.py
│   │   └── queries.py
│   ├── db/
│   │   ├── connection.py
│   │   ├── models.py
│   │   └── repositories.py
│   ├── sync/
│   │   ├── service.py
│   │   ├── locking.py
│   │   ├── aggregation.py
│   │   └── language_sync.py
│   ├── stats/
│   │   ├── streaks.py
│   │   ├── languages.py
│   │   └── metrics.py
│   └── cards/
│       ├── profile.py
│       └── streak.py
├── migrations/
├── tests/
│   ├── test_streaks.py
│   ├── test_aggregation.py
│   ├── test_sync.py
│   ├── test_api.py
│   └── fixtures/
├── .github/
│   └── workflows/
│       └── sync.yml
├── alembic.ini
├── requirements.txt
├── pyproject.toml
├── vercel.json
├── .env.example
└── README.md
```

Adjust the structure if necessary, but preserve the separation between:

* API
* GitHub client
* database
* synchronization
* aggregation/statistics
* rendering

Do not put all logic in `main.py`.

---

# 4. Configuration

Use environment variables.

Required:

```
DATABASE_URL
GITHUB_TOKEN
SYNC_SECRET
```

Optional:

```
GITHUB_API_URL
LOG_LEVEL
ENVIRONMENT
```

Create a typed settings object.

Never hardcode secrets.

`.env` must be ignored by git.

Provide `.env.example`.

---

# 5. Database schema

Use PostgreSQL.

Create migrations for the following logical tables.

## users

Store GitHub identity/profile information.

Fields should include approximately:

```
username
name
avatar_url
followers
following
public_repos
public_gists
updated_at
```

Use username as the stable API-facing identifier.

---

## user_stats

Store current precomputed statistics.

Fields:

```
username
total_commits
total_pull_requests
total_issues
total_reviews
current_streak
longest_streak
contribution_count
repository_count
fork_count
star_count
stats_computed_at
```

Do not compute these values during GET requests.

---

## repositories

Fields:

```
github_id
owner
name
stars
forks
primary_language
is_fork
pushed_at
synced_at
```

Use the GitHub repository ID as the primary identity where appropriate.

Add indexes useful for synchronization.

---

## contribution_days

Fields:

```
username
date
count
```

Primary key:

```
(username, date)
```

This stores GitHub's contribution calendar.

Fetch the current year's contribution calendar during synchronization.

Do NOT treat the contribution calendar as an incremental cursor.

---

## language_totals

Fields:

```
username
language
byte_count
updated_at
```

Primary key:

```
(username, language)
```

Language totals should be derived from GitHub repository language byte counts.

Do not use only `primaryLanguage` to calculate language percentages.

---

## daily_snapshots

Fields:

```
username
date
total_commits
total_pull_requests
total_issues
total_reviews
total_stars
total_followers
contribution_count
```

Primary key:

```
(username, date)
```

Use this for historical statistics.

If a snapshot for the date already exists, update it rather than inserting duplicates.

---

## sync_state

Fields:

```
username
locked_until
lock_token
last_success_at
last_failure_at
consecutive_failures
status
last_error
updated_at
```

Status values:

```
ok
degraded
failing
```

The sync state is metadata only.

A failed synchronization must not modify valid user statistics.

---

# 6. GitHub API strategy

Use GitHub GraphQL as the primary source.

The first GraphQL query should retrieve:

* username
* name
* avatar URL
* followers
* following
* public repositories
* contribution calendar
* total commit contributions
* total pull request contributions
* total issue contributions
* total pull request review contributions
* repositories owned by the user
* stars
* forks
* primary language
* fork status
* pushedAt
* repository count

Conceptually:

```
user(login: $username) {
    login
    name
    avatarUrl
    followers { totalCount }
    following { totalCount }
    repositories(...)
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
```

Use appropriate GraphQL pagination.

Do not blindly assume 100 repositories is enough.

If repository count exceeds the first page:

* paginate
* collect all repositories
* stop correctly at `hasNextPage == false`

The implementation should work correctly for users with more than 100 repositories.

---

# 7. Repository language synchronization

GitHub repository `primaryLanguage` is insufficient for language distribution.

For each repository, GitHub's language byte data should be fetched using the repository language API/query.

However, do NOT query languages for every repository on every sync.

Use:

```
pushed_at
languages_synced_at
```

to determine whether language data needs refreshing.

If:

```
pushed_at > languages_synced_at
```

refresh the language data.

For unchanged repositories, retain the previously synchronized language totals.

Make this logic explicit and testable.

---

# 8. Contribution synchronization

On every successful sync:

1. Fetch the current year's contribution calendar.
2. Upsert all contribution days.
3. Recalculate:

   * contribution count
   * current streak
   * longest streak

Do not depend on GitHub HTML scraping.

Do not scrape the GitHub contribution graph.

The contribution calendar returned by GraphQL is the source.

---

# 9. Metric definitions

Document the exact definition of every public metric.

For example:

```
contribution_count
    Sum of contribution counts represented by the GitHub contribution calendar
    for the synchronized period.

current_streak
    Number of consecutive contribution days ending at the latest relevant day,
    using the same semantics as the stored contribution calendar.

longest_streak
    Longest consecutive sequence of days with contribution_count > 0.

total_pull_requests
    GitHub's totalPullRequestContributions value.

total_reviews
    GitHub's totalPullRequestReviewContributions value.

total_issues
    GitHub's totalIssueContributions value.
```

Do not label metrics ambiguously.

If GitHub's definition differs from an intuitive interpretation, use names/documentation that make the distinction clear.

---

# 10. Streak calculation

Implement streak calculation as a pure Python function.

Input:

```
list[date, contribution_count]
```

Output:

```
current_streak
longest_streak
```

Test at minimum:

* empty calendar
* one active day
* multiple consecutive days
* gaps
* activity ending yesterday
* activity ending today
* longest historical streak vs current streak
* all zero
* single contribution between two gaps

Keep this logic completely independent from FastAPI and PostgreSQL.

---

# 11. Synchronization architecture

Implement synchronization as a service.

Conceptually:

```
sync(username)

    acquire_lock()

    try:

        fetch GitHub data
        validate response

        BEGIN TRANSACTION

            upsert user
            upsert repositories
            upsert contribution days
            update language totals

            calculate aggregates

            update user_stats

            upsert daily snapshot

            mark sync_state as successful

        COMMIT

    except:

        record failure

    finally:

        release lock
```

The external GitHub API calls must happen BEFORE the database transaction.

Do not hold a PostgreSQL transaction open while waiting for GitHub.

---

# 12. Synchronization lock

Do not use a PostgreSQL session advisory lock unless the implementation guarantees that acquisition and release occur on the same database connection.

Because this runs on Vercel/serverless infrastructure, prefer a database-backed lease.

Use:

```
locked_until
lock_token
```

Acquire the lock atomically.

Conceptually:

```
UPDATE sync_state
SET
    locked_until = now() + interval '5 minutes',
    lock_token = :token
WHERE
    username = :username
    AND (
        locked_until IS NULL
        OR locked_until < now()
    );
```

If zero rows are updated:

```
return 409
```

Generate a cryptographically random lock token.

Release the lock only if the token matches.

Make the lock expire automatically so a killed serverless invocation cannot permanently block synchronization.

The lock duration should be configurable.

---

# 13. Failure behavior

This is critical.

A failed sync must NOT:

* delete repositories
* overwrite good contribution data
* overwrite good aggregates
* modify daily snapshots
* set statistics to zero
* partially update the user-facing dataset

Only synchronization metadata should be updated on failure.

On failure:

```
consecutive_failures += 1
last_failure_at = now()
last_error = sanitized_error_message
```

Set:

```
status = "degraded"
```

after 3 consecutive failures.

You may use `"failing"` for more severe or prolonged failures, but define the transition clearly.

On the next successful sync:

```
consecutive_failures = 0
status = "ok"
last_success_at = now()
last_error = NULL
```

---

# 14. Transaction design

All user-facing database mutations from a successful sync must occur in one transaction:

```
repositories
contribution_days
language_totals
user_stats
daily_snapshots
successful sync_state update
```

If any part fails:

```
ROLLBACK
```

The previous complete dataset must remain available.

Do NOT catch a database exception and continue committing partial data.

---

# 15. Sync endpoint

Implement:

```
POST /v1/sync/{username}
```

Require:

```
Authorization: Bearer <SYNC_SECRET>
```

Reject:

* missing authorization
* invalid token
* malformed username

Return:

```
200
successful synchronization
```

or:

```
409
synchronization already running
```

or:

```
4xx/5xx
appropriate failure
```

Do not expose the GitHub token.

Do not expose raw exception traces.

---

# 16. Read API

Implement:

```
GET /v1/users/{username}/stats
```

Response:

```
{
  "data": {
    "username": "PrajwalAmte",
    "total_commits": 4213,
    "total_pull_requests": 83,
    "total_issues": 27,
    "total_reviews": 142,
    "current_streak": 12,
    "longest_streak": 73,
    "contribution_count": 642,
    "repository_count": 42,
    "star_count": 184,
    "fork_count": 31
  },
  "meta": {
    "generated_at": "...",
    "last_sync": "...",
    "sync_status": "ok"
  }
}
```

The GET endpoint must ONLY query PostgreSQL.

It must never invoke GitHub.

It must never perform expensive aggregation.

---

# 17. History API

Implement:

```
GET /v1/users/{username}/history
```

Return daily snapshots.

Support optional:

```
from
to
```

query parameters.

Default to a reasonable recent period if no range is specified.

Do not load unlimited history accidentally.

Add a sensible maximum range.

---

# 18. Language API

Implement:

```
GET /v1/users/{username}/languages
```

Return normalized language statistics.

Example:

```
{
  "data": {
    "languages": [
      {
        "name": "Java",
        "bytes": 123456,
        "percentage": 32.4
      },
      {
        "name": "Python",
        "bytes": 84211,
        "percentage": 22.1
      }
    ]
  },
  "meta": {
    "last_sync": "..."
  }
}
```

Percentages should be calculated from byte totals.

Sort descending by byte count.

Define whether generated/vendor repositories are included and document the decision.

---

# 19. Repository API

Implement:

```
GET /v1/users/{username}/repositories
```

Return useful repository metadata.

Support pagination.

Do not calculate repository statistics dynamically.

---

# 20. HTTP caching

For GET endpoints use:

```
Cache-Control:
public,
s-maxage=3600,
stale-while-revalidate=86400
```

Adjust formatting as necessary for the framework.

The API should remain correct even if the CDN cache is bypassed.

Caching is an optimization, not a correctness mechanism.

Do not introduce Redis.

---

# 21. Health endpoints

Implement:

```
GET /health
```

This means:

> The application process can respond.

Return HTTP 200 when the application is reachable.

Implement:

```
GET /ready
```

This means:

> The service has enough database state to serve useful data.

Check:

* database connectivity
* whether at least one valid synchronized dataset exists

If there is no data at all, return an appropriate non-ready status.

If the last sync is stale but valid data exists, `/ready` should generally remain usable and expose the stale state rather than pretending there is no data.

---

# 22. SVG cards

Implement SVG rendering only after the JSON API is complete.

Endpoints:

```
GET /v1/users/{username}/cards/profile.svg
GET /v1/users/{username}/cards/streak.svg
```

Cards must use the exact same data exposed by the API.

Do not make SVG rendering call GitHub.

Keep SVG generation deterministic.

Avoid external image dependencies where possible.

Return:

```
Content-Type: image/svg+xml
```

Use a clean dark theme suitable for GitHub README usage.

Do not overdesign the cards.

---

# 23. GitHub Actions scheduler

Create:

```
.github/workflows/sync.yml
```

It should:

* run on a schedule
* support `workflow_dispatch`
* call the sync endpoint
* send the sync secret securely
* fail the workflow if synchronization fails

Start with a reasonable schedule such as every 3 hours.

Do not assume Vercel's built-in cron is required.

The scheduler is intentionally decoupled from the API host.

Example conceptual workflow:

```
schedule:
  - cron: "0 */3 * * *"

workflow_dispatch:

steps:
  curl -X POST \
    https://<deployment>/v1/sync/PrajwalAmte \
    -H "Authorization: Bearer $SYNC_SECRET"
```

Use GitHub Actions secrets.

---

# 24. Vercel deployment

Create the necessary Vercel configuration for FastAPI.

The application must be stateless.

Do not rely on:

* local filesystem persistence
* in-memory caches
* background processes
* long-running workers

All durable state belongs in PostgreSQL.

---

# 25. Supabase connection handling

Use a connection strategy appropriate for serverless deployment.

Do not create an unlimited connection pool.

Keep database connections bounded.

If Supabase provides a pooler/serverless-friendly connection string, document which connection string should be used for Vercel.

Make local development work with the same application code.

---

# 26. Error handling

Create clear exception types for:

```
GithubApiError
GithubRateLimitError
GithubNotFoundError
SyncAlreadyRunningError
DatabaseError
ValidationError
```

Do not leak:

* GitHub tokens
* database URLs
* SQL credentials
* internal stack traces

Log useful diagnostics server-side.

---

# 27. Logging

Use structured logs where practical.

Every sync should include:

```
username
sync_id
start_time
duration
GitHub request count
GitHub GraphQL cost if available
repositories processed
language queries performed
sync result
```

Example:

```
sync_id=abc123
username=PrajwalAmte
repositories=42
language_queries=3
duration_ms=842
result=success
```

Do not log secrets.

---

# 28. Tests

Write meaningful tests.

At minimum:

## Unit tests

* streak calculation
* language percentage calculation
* aggregate calculation
* snapshot generation
* metric transformation

## Integration tests

* successful synchronization
* GitHub failure
* database transaction rollback
* concurrent sync lock
* expired lock recovery
* successful sync after previous failure

## API tests

* authentication
* stats endpoint
* history endpoint
* language endpoint
* repository endpoint
* health
* readiness
* cache headers

Mock GitHub in tests.

Tests must not require a real GitHub token.

---

# 29. Idempotency

Running the same sync twice should produce the same database state.

Use PostgreSQL upserts.

Examples:

```
INSERT ... ON CONFLICT (...) DO UPDATE
```

Never blindly insert duplicate contribution days or snapshots.

---

# 30. Data freshness

Every user-facing response should expose:

```
generated_at
last_sync
sync_status
```

Optionally expose:

```
data_age_seconds
```

Do not hide stale data.

If GitHub hasn't synchronized for 12 hours, the API should still serve the last valid dataset while clearly indicating the freshness.

---

# 31. Security

Implement:

* bearer authentication for sync
* parameterized SQL
* environment-based secrets
* no secrets in source control
* no GitHub token in API responses
* no unauthenticated sync endpoint
* input validation for usernames
* reasonable request limits where useful

GET endpoints can be public.

POST sync must be authenticated.

---

# 32. README/documentation

Create a proper README explaining:

1. What the service does
2. Architecture
3. Why read requests never call GitHub
4. Database schema
5. Synchronization model
6. Failure semantics
7. API endpoints
8. Environment variables
9. Local development
10. Database migration
11. GitHub token requirements
12. GitHub Actions setup
13. Vercel deployment
14. Supabase setup
15. Example README usage
16. Metric definitions

Include an architecture diagram using Mermaid.

---

# 33. GitHub token permissions

Use the minimum permissions necessary.

Do not request broad write permissions.

The application only needs to read GitHub data.

Document the required token configuration and why each permission is necessary.

---

# 34. Important architectural constraints

These are non-negotiable:

1. GET requests NEVER call GitHub.
2. GitHub failures NEVER erase valid data.
3. Successful sync database writes are atomic.
4. Synchronization must be idempotent.
5. Concurrent synchronization for the same username must be prevented.
6. Database is the durable source for the API.
7. Redis is not required.
8. CDN caching is an optimization only.
9. GitHub Actions is the scheduler.
10. The application must remain stateless.
11. Expensive calculations happen during synchronization.
12. API responses expose freshness.
13. API is versioned under `/v1`.
14. Do not scrape GitHub HTML.
15. Do not introduce unnecessary infrastructure.

---

# 35. Implementation approach

Do not generate the entire project as one giant file.

Implement incrementally in this order:

1. Initialize repository and Python project.
2. Configure FastAPI.
3. Configure settings.
4. Configure PostgreSQL.
5. Create Alembic migrations.
6. Implement database models/repositories.
7. Implement GitHub GraphQL client.
8. Implement GitHub response models.
9. Implement contribution processing.
10. Implement streak calculations.
11. Implement repository synchronization.
12. Implement language synchronization.
13. Implement aggregate calculations.
14. Implement sync lease/locking.
15. Implement atomic synchronization service.
16. Implement failure tracking.
17. Implement authenticated sync endpoint.
18. Implement stats API.
19. Implement history API.
20. Implement languages API.
21. Implement repositories API.
22. Implement health/readiness.
23. Implement HTTP caching.
24. Implement SVG cards.
25. Add tests.
26. Add GitHub Actions scheduler.
27. Add Vercel configuration.
28. Complete deployment documentation.

After each major component, run tests and fix issues before continuing.

Do not leave TODO placeholders for core functionality.

---

# 36. Code quality expectations

Prefer:

* small functions
* explicit types
* dependency injection where useful
* pure functions for calculations
* clear database boundaries
* clear API schemas
* clear error handling

Avoid:

* giant service classes
* global mutable state
* hidden side effects
* unnecessary abstractions
* generic "utils.py" dumping grounds
* duplicated GitHub API logic
* duplicated SQL

Keep the project understandable to one engineer.

---

# 37. Final acceptance criteria

The project is complete when the following works:

### Local

```
docker/local PostgreSQL or Supabase
uvicorn app.main:app --reload
```

Then:

```
POST /v1/sync/PrajwalAmte
```

populates the database.

Then:

```
GET /v1/users/PrajwalAmte/stats
```

returns the statistics.

### Failure test

Simulate GitHub being unavailable.

The GET endpoint must still return the previous valid data.

`sync_status` should become degraded after the configured failure threshold.

### Concurrent test

Trigger two syncs simultaneously.

Only one may perform synchronization.

### Rollback test

Force an aggregation/database error after repository upserts begin.

After the failure:

* previous statistics remain intact
* previous contribution data remains intact
* previous snapshot remains intact
* sync metadata records the failure

### README

The following should work:

```
<img src="https://<domain>/v1/users/PrajwalAmte/cards/profile.svg">
```

and:

```
<img src="https://<domain>/v1/users/PrajwalAmte/cards/streak.svg">
```

No GitHub request should occur when these URLs are requested.

---

# 38. Important implementation judgment

Do not blindly follow this specification if the actual GitHub GraphQL schema/API behavior contradicts it.

If a GitHub field behaves differently than expected:

1. verify the current GitHub API/schema,
2. adapt the implementation,
3. preserve the architectural invariants,
4. document the deviation.

The architecture is more important than any particular query shape.

The primary objective is:

> **A small, reliable, cache-friendly GitHub statistics service where synchronization is isolated from reads and failed external dependencies cannot corrupt the last known-good dataset.**

Build the complete project, not a mock or pseudo implementation.
