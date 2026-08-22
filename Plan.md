---
title: GitHub Stats Service — Final Build Plan
tags: [architecture, github-api, vercel, supabase, python, fastapi]
stack: Python/FastAPI on Vercel, Supabase Postgres, GitHub Actions scheduler
---

## What this refines from the general pattern

Three real additions, not optional polish:

1. **Sync writes are transactional** — upsert, aggregate recompute, and
   `sync_state` update happen in one transaction. A failure anywhere
   rolls back the whole thing, not just "doesn't overwrite" loosely.
2. **A sync lock prevents overlapping runs.** Cheap insurance against a
   retried GitHub Action and a manual trigger colliding.
3. **The API is versioned from day one** (`/v1/...`), because "what
   counts as a commit" is a definition that will change before the data
   model does.

One place I'd simplify relative to a naive multi-collector design:
GitHub's GraphQL `contributionsCollection` field returns total commits,
PRs, issues, and review counts as pre-aggregated numbers — you don't
need to paginate every PR and issue yourself to get those totals. That
collapses most of the sync into one GraphQL query, which matters
directly for staying inside Vercel's 10s Hobby timeout.

---

## GitHub API strategy

```text
Single GraphQL query per sync, covering:

  user {
    login, name, avatarUrl
    contributionsCollection {
      contributionCalendar { weeks { contributionDays { date, count } } }
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
    }
    repositories(first: 100, ownerAffiliations: OWNER, orderBy: STARGAZERS) {
      nodes { name, stargazerCount, forkCount, primaryLanguage, isFork }
    }
    repositoriesContributedTo { totalCount }
  }
```

This gets you profile + full contribution calendar + repo list +
language-per-repo in **one request**. Only fall back to a second,
paginated request if `repositories` exceeds 100 (unlikely at personal
scale — revisit if you ever sync org accounts with large repo counts).

Language *byte* totals (not just primary language) require one
additional query per repo (`languages { edges { size, node { name } } }`)
— only fetch this for repos that changed since last sync (compare
`pushedAt` against `sync_state.cursor`), not every repo every time.

```text
sync():
    1 query  → profile + contributions + repo list
    N queries → languages, only for repos with pushedAt > last_sync
```

That keeps the common case (nothing changed since last sync) at exactly
one GraphQL call.

---

## Data model

```text
users
  username PK, name, avatar_url,
  total_commits, total_prs, total_issues, total_reviews,
  current_streak, longest_streak,
  stats_computed_at

repositories
  id PK, owner, name, stars, forks, primary_language,
  is_fork, pushed_at, synced_at

contribution_days
  username, date, count            -- PK (username, date)

language_totals
  username, language, byte_count   -- PK (username, language)

daily_snapshots                    -- historical trend, cheap to keep
  username, date, total_commits, total_prs, total_issues,
  total_stars, followers           -- PK (username, date)

sync_state
  username PK, cursor, locked_until,
  last_success_at, last_failure_at,
  consecutive_failures, status     -- 'ok' | 'degraded' | 'failing'
```

`daily_snapshots` is one row per day, a handful of integers — negligible
against Supabase's free 500MB cap even over years, and it's what turns
"current stats" into "how this changed over time" for later card designs.

---

## Sync flow

```python
def sync(username: str):
    # 1. acquire lock
    if not acquire_lock(username):
        return 409  # sync already running

    try:
        # 2. fetch (outside transaction — network I/O)
        data = fetch_github_data(username, since=get_cursor(username))

        # 3. everything below is one transaction
        with db.transaction():
            upsert_repositories(data.repos)
            upsert_contribution_days(data.contributions)
            upsert_language_totals(data.changed_repo_languages)

            aggregates = compute_aggregates(username)  # streaks, totals
            update_user_aggregates(username, aggregates)
            insert_daily_snapshot(username, aggregates)

            update_sync_state(username, status="ok",
                               consecutive_failures=0)
        # transaction commits here — all or nothing

    except GithubApiError:
        record_sync_failure(username)  # separate, small write —
                                        # increments consecutive_failures,
                                        # flips status to 'degraded' at 3
    finally:
        release_lock(username)
```

`acquire_lock` / `release_lock` use a Postgres advisory lock keyed on a
hash of the username — no extra table, no extra infra:

```sql
SELECT pg_try_advisory_lock(hashtext($1));
-- ... work ...
SELECT pg_advisory_unlock(hashtext($1));
```

---

## API

```text
POST /v1/sync/{username}          -- authenticated, called by GitHub Actions
GET  /v1/users/{username}/stats
GET  /v1/users/{username}/history          -- daily_snapshots, for trend cards
GET  /v1/users/{username}/cards/profile.svg
GET  /v1/users/{username}/cards/streak.svg
GET  /health
GET  /ready
```

Response shape, unchanged from the general pattern:

```json
{
  "data": { "total_commits": 4213, "current_streak": 12 },
  "meta": {
    "generated_at": "2026-08-22T20:00:00Z",
    "last_sync": "2026-08-22T18:04:11Z",
    "sync_status": "ok"
  }
}
```

`Cache-Control: public, s-maxage=3600, stale-while-revalidate=86400` on
every GET.

---

## Reliability table

| Failure | What happens |
|---|---|
| GitHub down / rate limited | Old data keeps serving, `sync_status: degraded` after 3 failures |
| Sync crashes mid-write | Transaction rolls back — no partial state, ever |
| Two syncs triggered at once | Second returns 409, first proceeds |
| Vercel cold start | Slightly slower single request, no data impact |
| Supabase temporarily unreachable | API returns an error, but no corruption — nothing to corrupt without a completed transaction |
| Scheduler (GitHub Actions) down | Data goes stale but stays correct; visible via `last_sync` in every response |

---

## Build order

```text
1. Schema: 6 tables above, including sync_state with locked_until
2. GitHub GraphQL client: single query (profile+contributions+repos)
3. Language backfill query, gated on pushedAt vs cursor
4. Postgres advisory lock: acquire/release helpers
5. Sync transaction: upsert → aggregate → snapshot → sync_state, atomic
6. Failure path: consecutive_failures tracking, outside the transaction
7. POST /v1/sync/{username} — bearer auth via SYNC_SECRET
8. GitHub Actions workflow: schedule + workflow_dispatch, calls sync route
9. GET /v1/users/{username}/stats + /history — read-only, Cache-Control set
10. /health, /ready
11. SVG card rendering over the same stats row
12. Deploy: Vercel (FastAPI) + Supabase (schema + connection string) + Actions secret
```

Steps 1–10 are the entire reliability core. 11–12 are the actual
product surface sitting on top of a core that won't need to change
again for this project.