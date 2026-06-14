import re
from typing import Any
from urllib.parse import quote_plus

import httpx


APP_URL_RE = re.compile(
    r"https?://store\.steampowered\.com/app/(?P<appid>\d+)(?:/[^?\s]*)?",
    re.IGNORECASE,
)


class SteamClientError(Exception):
    """Base exception for Steam client failures."""


class SteamAPIError(SteamClientError):
    """Raised when Steam API data cannot be fetched or parsed."""


class SteamInvalidAppError(SteamClientError):
    """Raised when an appid does not resolve to a valid Steam game."""


def extract_appid(text: str) -> str | None:
    match = APP_URL_RE.search(text or "")
    return match.group("appid") if match else None


def steam_app_url(appid: str | int) -> str:
    return f"https://store.steampowered.com/app/{appid}/"


class SteamClient:
    def __init__(self, language: str = "schinese", country: str = "cn", timeout: float = 20.0):
        self.language = language
        self.country = country
        self.timeout = timeout

    async def search(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        params = {
            "term": query,
            "l": self.language,
            "cc": self.country,
        }
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get("https://store.steampowered.com/api/storesearch/", params=params)
            response.raise_for_status()
            payload = response.json()

        items = payload.get("items", [])
        results: list[dict[str, Any]] = []
        for item in items[: max(limit, 1)]:
            appid = item.get("id")
            name = item.get("name")
            if not appid or not name:
                continue
            results.append(
                {
                    "appid": str(appid),
                    "name": str(name),
                    "url": steam_app_url(appid),
                    "tiny_image": item.get("tiny_image"),
                }
            )
        return results

    async def get_app_details(self, appid: str) -> dict[str, Any]:
        params = {
            "appids": appid,
            "l": self.language,
            "cc": self.country,
        }
        url = f"https://store.steampowered.com/api/appdetails?appids={quote_plus(appid)}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise SteamAPIError(f"Steam appdetails request failed for appid {appid}") from exc
        except ValueError as exc:
            raise SteamAPIError(f"Steam appdetails returned invalid JSON for appid {appid}") from exc

        app_payload = payload.get(str(appid), {})
        if not app_payload.get("success"):
            raise SteamInvalidAppError(f"Steam appdetails returned no data for appid {appid}")

        data = app_payload.get("data") or {}
        if data.get("type") and data.get("type") != "game":
            raise SteamInvalidAppError(f"appid {appid} is not a Steam game")
        return self._normalize_details(str(appid), data)

    def _normalize_details(self, appid: str, data: dict[str, Any]) -> dict[str, Any]:
        price = self._normalize_price(data)
        screenshots = [
            shot.get("path_full") or shot.get("path_thumbnail")
            for shot in data.get("screenshots", [])
            if shot.get("path_full") or shot.get("path_thumbnail")
        ]

        return {
            "appid": appid,
            "url": steam_app_url(appid),
            "name": data.get("name", "Unknown Game"),
            "short_description": data.get("short_description") or "",
            "header_image": data.get("header_image"),
            "capsule_image": data.get("capsule_image"),
            "screenshots": screenshots,
            "release_date": (data.get("release_date") or {}).get("date") or "未知",
            "developers": data.get("developers") or [],
            "publishers": data.get("publishers") or [],
            "genres": [genre.get("description") for genre in data.get("genres", []) if genre.get("description")],
            "platforms": [name for name, enabled in (data.get("platforms") or {}).items() if enabled],
            "price": price,
        }

    @staticmethod
    def _normalize_price(data: dict[str, Any]) -> dict[str, Any]:
        if data.get("is_free"):
            return {
                "current": "免费开玩",
                "original": "",
                "discount_percent": 0,
                "has_discount": False,
            }

        overview = data.get("price_overview") or {}
        discount = int(overview.get("discount_percent") or 0)
        current = overview.get("final_formatted") or "暂无价格"
        original = overview.get("initial_formatted") or ""
        return {
            "current": current,
            "original": original if discount > 0 else "",
            "discount_percent": discount,
            "has_discount": discount > 0,
        }
