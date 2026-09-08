"""Save a conversation's browser logins and put them back into a later tab.

A tab's cookies live in its own jar and die with the tab, so a user who logged in
yesterday would have to log in again today. Before a tab is closed its cookies are
exported, encrypted and stored in Redis; when a new tab is opened for the same owner
they are restored, and the sites see the user as still signed in.

The owner is the end user when the caller sends a ``user_id``, so one login serves
every later conversation of that person. Without a ``user_id`` the owner falls back
to the conversation, which still carries a login across days within that thread.

Cookies are full account access. They are encrypted at rest with the gateway's AES
helper, scoped to one owner, and expire on their own.
"""

import json

from config import Config
from globals import logger
from src.configs.constant import redis_keys
from src.services.cache_service import delete_in_cache, find_in_cache, store_in_cache

from .connection import export_jar_cookies, import_jar_cookies

COOKIE_PREFIX = redis_keys["gtwy_browser_ctx_"]
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
    return max(3600, int(getattr(Config, "GTWY_BROWSER_COOKIE_TTL_DAYS", 30) or 30) * 86400)


def owner_key(org_id, user_id, thread_key: str) -> str:
    """Who these cookies belong to: the end user when known, else the conversation."""
    if user_id:
        return f"{org_id}:user:{user_id}"
    return f"{org_id}:thread:{thread_key}"


def _redis_key(owner: str) -> str:
    return f"{COOKIE_PREFIX}{owner}"


def _trim(cookies: list[dict]) -> list[dict]:
    return [{k: v for k, v in cookie.items() if k in SAFE_COOKIE_FIELDS} for cookie in (cookies or [])]


async def save_jar(browser, browser_context_id: str | None, owner: str | None) -> int:
    """Export a tab's cookies and store them for its owner. Returns how many were saved."""
    if not is_enabled() or not browser_context_id or not owner:
        return 0
    from src.services.utils.helper import Helper  # imported here: helper imports back into this package

    try:
        cookies = _trim(await export_jar_cookies(browser, browser_context_id))
        if not cookies:
            return 0
        await store_in_cache(_redis_key(owner), {"cookies": Helper.encrypt(json.dumps(cookies))}, ttl=cookie_ttl_seconds())
        logger.info(f"Gtwy_Browser: saved {len(cookies)} cookies for {owner}")
        return len(cookies)
    except Exception as exc:
        # Never let a cookie problem break the browser flow: the user just logs in again.
        logger.error(f"Gtwy_Browser: could not save cookies for {owner}: {exc.__class__.__name__}: {exc}")
        return 0


async def restore_jar(browser, browser_context_id: str | None, owner: str | None) -> int:
    """Put an owner's saved cookies into a fresh tab. Returns how many were restored."""
    if not is_enabled() or not browser_context_id or not owner:
        return 0
    from src.services.utils.helper import Helper  # see save_jar

    try:
        stored = await find_in_cache(_redis_key(owner))
        if not stored:
            return 0
        payload = json.loads(stored)
        cookies = json.loads(Helper.decrypt(payload["cookies"]))
        applied = await import_jar_cookies(browser, browser_context_id, cookies)
        logger.info(f"Gtwy_Browser: restored {applied} cookies for {owner}")
        return applied
    except Exception as exc:
        logger.error(f"Gtwy_Browser: could not restore cookies for {owner}: {exc.__class__.__name__}: {exc}")
        return 0


async def forget(owner: str | None) -> None:
    """Drop an owner's saved logins, for a sign-out or a privacy request."""
    if owner:
        await delete_in_cache(_redis_key(owner))
        logger.info(f"Gtwy_Browser: cleared saved cookies for {owner}")
