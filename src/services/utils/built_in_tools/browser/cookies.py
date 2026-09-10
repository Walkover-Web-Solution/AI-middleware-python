"""Remember a conversation's browser logins so a new tab resumes signed in.

A tab's cookies live in its own jar and die with the tab, so a user who logged in
yesterday would have to log in again today. Before a tab closes its cookies are
exported, encrypted and stored; when the conversation opens a new tab they go back in
and the sites see the user as still signed in.

Two tiers. MongoDB is the source of truth, because a login is user state and must
survive a Redis flush. Redis holds the same encrypted blob for a short while so the
common case costs one cache read. The scope is the conversation, matching one tab per
thread and sub-thread.

Cookies are full account access. Only the encrypted blob is ever stored, it is scoped
to one conversation, and it expires on its own.
"""

import json

from config import Config
from globals import logger
from src.configs.constant import redis_keys
from src.services.cache_service import find_in_cache, store_in_cache

from .connection import export_jar_cookies, import_jar_cookies

CACHE_PREFIX = redis_keys["gtwy_browser_ctx_"]
# Chrome returns extra read-only fields (size, session, sameParty...) that Storage.setCookies
# rejects, so only these are kept.
SAFE_COOKIE_FIELDS = {
    "name",
    "value",
    "domain",
    "path",
    "secure",
    "httpOnly",
    "sameSite",
    "expires",
    "priority",
    "sourceScheme",
    "sourcePort",
}


def is_enabled() -> bool:
    if str(getattr(Config, "GTWY_BROWSER_PERSIST_COOKIES", "") or "").strip().lower() not in ("1", "true", "yes"):
        return False
    if not (Config.Encreaption_key and Config.Secret_IV):
        logger.warning("Gtwy_Browser: cookie persistence is on but encryption keys are missing; not saving cookies")
        return False
    return True


def cookie_ttl_seconds() -> int:
    """How long a saved login stays valid, stamped onto the Mongo document."""
    return max(3600, int(getattr(Config, "GTWY_BROWSER_COOKIE_TTL_DAYS", 30) or 30) * 86400)


def cache_ttl_seconds() -> int:
    """How long Redis keeps its copy. A cache window, not a lifetime."""
    return max(60, int(getattr(Config, "GTWY_BROWSER_COOKIE_CACHE_TTL_SECONDS", 3600) or 3600))


def _cache_key(scope_key: str) -> str:
    return f"{CACHE_PREFIX}{scope_key}"


def _trim(cookies: list[dict]) -> list[dict]:
    return [{k: v for k, v in cookie.items() if k in SAFE_COOKIE_FIELDS} for cookie in (cookies or [])]


async def _load_blob(scope_key: str) -> str | None:
    """The encrypted blob for this conversation: Redis first, then Mongo, warming Redis."""
    cached = await find_in_cache(_cache_key(scope_key))
    if cached:
        try:
            return json.loads(cached)["cookies"]
        except (TypeError, ValueError, KeyError):
            logger.warning(f"Gtwy_Browser: ignoring malformed cached cookies for {scope_key}")

    from src.db_services.browserCookieService import get_browser_cookies

    document = await get_browser_cookies(scope_key)
    if not document or not document.get("cookies"):
        return None
    blob = document["cookies"]
    await store_in_cache(_cache_key(scope_key), {"cookies": blob}, ttl=cache_ttl_seconds())
    return blob


async def _store_blob(scope_key: str, blob: str, cookie_count: int, meta: dict | None) -> None:
    """Write to Mongo, then refresh Redis with the same blob.

    A failed Mongo write still updates Redis, so browsing keeps working and the login
    survives at least the cache window.
    """
    from src.db_services.browserCookieService import upsert_browser_cookies

    stored = await upsert_browser_cookies(scope_key, blob, cookie_count, cookie_ttl_seconds(), meta)
    if not stored:
        logger.error(f"Gtwy_Browser: cookies for {scope_key} are cached but not persisted")
    await store_in_cache(_cache_key(scope_key), {"cookies": blob}, ttl=cache_ttl_seconds())


async def save_jar(browser, browser_context_id: str | None, scope_key: str | None, meta: dict | None = None) -> int:
    """Export a tab's cookies and store them for its conversation. Returns how many were saved."""
    if not is_enabled() or not browser_context_id or not scope_key:
        return 0

    from src.services.utils.helper import Helper  # imported here: helper imports back into this package

    try:
        cookies = _trim(await export_jar_cookies(browser, browser_context_id))
        if not cookies:
            return 0
        await _store_blob(scope_key, Helper.encrypt(json.dumps(cookies)), len(cookies), meta)
        logger.info(f"Gtwy_Browser: saved {len(cookies)} cookies for {scope_key}")
        return len(cookies)
    except Exception as exc:
        # Never let a cookie problem break the browser flow: the user just logs in again.
        logger.error(f"Gtwy_Browser: could not save cookies for {scope_key}: {exc.__class__.__name__}: {exc}")
        return 0


async def restore_jar(browser, browser_context_id: str | None, scope_key: str | None) -> int:
    """Put a conversation's saved cookies into a fresh tab. Returns how many were restored."""
    if not is_enabled() or not browser_context_id or not scope_key:
        return 0

    from src.services.utils.helper import Helper  # see save_jar

    try:
        blob = await _load_blob(scope_key)
        if not blob:
            return 0
        cookies = json.loads(Helper.decrypt(blob))
        applied = await import_jar_cookies(browser, browser_context_id, cookies)
        logger.info(f"Gtwy_Browser: restored {applied} cookies for {scope_key}")
        return applied
    except Exception as exc:
        logger.error(f"Gtwy_Browser: could not restore cookies for {scope_key}: {exc.__class__.__name__}: {exc}")
        return 0
