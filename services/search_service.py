from rapidfuzz import fuzz

from astrbot.api import logger

from .steam_client import SteamClient


class SteamSearchService:
    def __init__(self, client: SteamClient):
        self.client = client

    async def search_ranked(self, queries: list[str], limit: int = 5) -> list[dict]:
        merged: dict[str, dict] = {}
        for query_index, query in enumerate(queries):
            if not query.strip():
                continue
            try:
                results = await self.client.search(query, limit=max(limit * 2, 8))
            except Exception as exc:
                logger.warning(f"Steam search failed for query {query!r}: {exc}")
                continue
            for rank, result in enumerate(results):
                appid = result["appid"]
                score = self._score(query, result["name"], query_index, rank)
                existing = merged.get(appid)
                if existing is None or score > existing["_score"]:
                    result["_score"] = score
                    merged[appid] = result

        ranked = sorted(merged.values(), key=lambda item: item["_score"], reverse=True)
        for item in ranked:
            item.pop("_score", None)
        return ranked[:limit]

    @staticmethod
    def _score(query: str, name: str, query_index: int, rank: int) -> float:
        query_norm = query.lower().strip()
        name_norm = name.lower().strip()
        similarity = max(
            fuzz.WRatio(query_norm, name_norm),
            fuzz.partial_ratio(query_norm, name_norm),
        )
        query_bonus = max(0, 20 - query_index * 4)
        rank_bonus = max(0, 15 - rank)
        contains_bonus = 10 if query_norm and query_norm in name_norm else 0
        return similarity + query_bonus + rank_bonus + contains_bonus
