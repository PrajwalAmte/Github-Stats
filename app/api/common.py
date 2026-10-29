"""Shared helpers for API routes."""

import re

# GitHub logins: alphanumeric or single hyphens, no leading/trailing hyphen, max 39.
_USERNAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")


def is_valid_username(username: str) -> bool:
    return bool(_USERNAME_RE.match(username))


# Vercel's CDN honors s-maxage / stale-while-revalidate and strips them
# before the response leaves the edge; max-age is what GitHub's image
# proxy and browsers see. After the first request, every card is served
# from the edge and refreshed in the background — no request waits on
# GitHub except the very first one per region.
#
# stale-if-error is what keeps a card up through a GitHub outage: when a
# revalidation comes back 5xx, the CDN keeps serving the last good copy
# for up to a week instead of passing the error on.
CACHE_OK = (
    "public, max-age=1800, s-maxage=3600, " "stale-while-revalidate=86400, stale-if-error=604800"
)

# Bad username / unknown user: stable answer, cache it so typos don't
# cost GitHub API calls.
CACHE_NOT_FOUND = "public, max-age=3600, s-maxage=3600"

# GitHub is failing and this instance has nothing stale to serve. Sent
# with a 503 so the CDN treats it as an error (and falls back to its
# stale copy via stale-if-error) rather than caching it as a success.
CACHE_NONE = "no-store"
