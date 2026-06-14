import json
import re
from typing import Any


_CJK_RE = re.compile(r"[\u3400-\u9fff]")


def contains_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text or ""))


def _parse_queries(raw: str) -> list[str]:
    raw = (raw or "").strip()
    if not raw:
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = None

    queries: list[str] = []
    if isinstance(data, dict):
        for key in ("primary_query", "alternative_queries", "queries"):
            value = data.get(key)
            if isinstance(value, str):
                queries.append(value)
            elif isinstance(value, list):
                queries.extend(str(item) for item in value if item)
    elif isinstance(data, list):
        queries.extend(str(item) for item in data if item)

    if not queries:
        for line in raw.splitlines():
            cleaned = re.sub(r"^[\s\-\d\.\)、:：]+", "", line).strip()
            if cleaned:
                queries.append(cleaned)

    deduped: list[str] = []
    seen: set[str] = set()
    for query in queries:
        query = query.strip().strip("\"'")
        key = query.lower()
        if query and key not in seen:
            deduped.append(query)
            seen.add(key)
    return deduped


class LLMTranslator:
    def __init__(self, context: Any):
        self.context = context

    async def expand_queries(self, original_query: str) -> list[str]:
        provider = self._get_provider()
        if provider is None:
            return [original_query]

        prompt = (
            "你是 Steam 游戏搜索助手。请把用户输入的中文游戏名、别名或俗称转换成最可能的 Steam 英文搜索词。"
            "只输出 JSON，不要解释。格式："
            "{\"primary_query\":\"...\",\"alternative_queries\":[\"...\",\"...\"]}。"
            f"用户输入：{original_query}"
        )

        try:
            response = await provider.text_chat(prompt=prompt)
        except TypeError:
            try:
                response = await provider.text_chat(prompt)
            except Exception:
                return [original_query]
        except Exception:
            return [original_query]

        content = self._extract_text(response)
        queries = _parse_queries(content)
        return queries + [original_query] if queries else [original_query]

    def _get_provider(self) -> Any:
        for attr in ("get_using_provider", "get_provider"):
            getter = getattr(self.context, attr, None)
            if callable(getter):
                try:
                    provider = getter()
                except Exception:
                    provider = None
                if provider is not None:
                    return provider
        return None

    @staticmethod
    def _extract_text(response: Any) -> str:
        if isinstance(response, str):
            return response
        for attr in ("completion_text", "text", "content"):
            value = getattr(response, attr, None)
            if isinstance(value, str):
                return value
        if isinstance(response, dict):
            for key in ("completion_text", "text", "content"):
                value = response.get(key)
                if isinstance(value, str):
                    return value
        return str(response)
