from pathlib import Path
from collections.abc import Mapping
from typing import Any

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

try:
    from .services.image_renderer import BrowserUnavailableError, HtmlImageRenderer, ImageRenderError
    from .services.llm_translator import LLMTranslator, contains_cjk
    from .services.search_service import SteamSearchService
    from .services.steam_client import SteamAPIError, SteamClient, SteamInvalidAppError, extract_appid
except ImportError:
    from services.image_renderer import BrowserUnavailableError, HtmlImageRenderer, ImageRenderError
    from services.llm_translator import LLMTranslator, contains_cjk
    from services.search_service import SteamSearchService
    from services.steam_client import SteamAPIError, SteamClient, SteamInvalidAppError, extract_appid


DEFAULT_CONFIG = {
    "enable_search_command": True,
    "enable_link_card": True,
    "use_llm_translate_for_chinese": False,
    "search_result_count": 5,
    "steam_language": "schinese",
    "steam_country": "cn",
    "render_viewport_width": 1200,
    "render_device_scale_factor": 1,
    "browser_executable_path": "",
    "enable_watermark": True,
    "watermark_text": "Crafted by pioneerzha",
    "card_template": "steam_card.html",
    "custom_template_path": "",
}


@register(
    "astrbot_plugin_game_card",
    "PioneerZHA",
    "Search games and render store links as shareable image cards.",
    "0.1.0",
)
class SteamCardPlugin(Star):
    def __init__(self, context: Context, config: dict[str, Any] | None = None):
        super().__init__(context)
        self.config = {**DEFAULT_CONFIG, **self._config_to_dict(config)}
        self.plugin_dir = Path(__file__).resolve().parent
        self.steam = SteamClient(
            language=str(self.config["steam_language"]),
            country=str(self.config["steam_country"]),
        )
        self.search_service = SteamSearchService(self.steam)
        self.translator = LLMTranslator(context)
        self.renderer = HtmlImageRenderer(
            self.plugin_dir,
            viewport_width=int(self.config["render_viewport_width"]),
            device_scale_factor=int(self.config["render_device_scale_factor"]),
            browser_executable_path=str(self.config.get("browser_executable_path", "")),
            enable_watermark=bool(self.config.get("enable_watermark", True)),
            watermark_text=str(self.config.get("watermark_text", "Crafted by pioneerzha")),
            card_template=str(self.config.get("card_template", "steam_card.html")),
            custom_template_path=str(self.config.get("custom_template_path", "")),
        )

    @filter.command("steam搜索")
    async def search_game(self, event: AstrMessageEvent, query: str = ""):
        if not self.config.get("enable_search_command", True):
            return

        query = self._normalize_search_query(event, query)
        if not query:
            yield event.plain_result("用法：/steam搜索 游戏名称")
            return

        queries = [query]
        if self.config.get("use_llm_translate_for_chinese", False) and contains_cjk(query):
            queries = await self.translator.expand_queries(query)

        limit = int(self.config.get("search_result_count", 5))
        results = await self.search_service.search_ranked(queries, limit=limit)
        if not results:
            yield event.plain_result("没找到相关游戏，可以换个名称再试试。")
            return

        lines = ["找到了~你说的是不是："]
        for index, item in enumerate(results, start=1):
            lines.append(f"{index}. {item['name']} - {item['url']}")
        yield event.plain_result("\n".join(lines))

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def handle_group_steam_link(self, event: AstrMessageEvent):
        async for result in self._handle_steam_link(event):
            yield result

    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    async def handle_private_steam_link(self, event: AstrMessageEvent):
        async for result in self._handle_steam_link(event):
            yield result

    async def _handle_steam_link(self, event: AstrMessageEvent):
        if not self.config.get("enable_link_card", True):
            return

        message = self._message_text(event)
        if "/steam搜索" in message:
            return

        appid = extract_appid(message)
        if not appid:
            return

        try:
            app = await self.steam.get_app_details(appid)
            image_path = await self.renderer.render_card(app)
        except SteamAPIError as exc:
            logger.exception(f"Steam API failed for appid {appid}: {exc}")
            yield event.plain_result("Steam 商店暂时访问失败，稍后再试。")
            return
        except SteamInvalidAppError as exc:
            logger.exception(f"invalid Steam appid {appid}: {exc}")
            yield event.plain_result("这个链接好像不是有效的 Steam 游戏页面。")
            return
        except BrowserUnavailableError as exc:
            logger.exception(f"browser unavailable while rendering Steam card for appid {appid}: {exc}")
            yield event.plain_result("图片渲染浏览器不可用，请检查插件环境。")
            return
        except ImageRenderError as exc:
            logger.exception(f"failed to render Steam card for appid {appid}: {exc}")
            yield event.plain_result("生成图片时出了点问题，稍后再试。")
            return
        except Exception as exc:
            logger.exception(f"failed to render Steam card for appid {appid}: {exc}")
            yield event.plain_result("生成图片时出了点问题，稍后再试。")
            return

        yield event.image_result(str(image_path))

    def _normalize_search_query(self, event: AstrMessageEvent, query: str) -> str:
        query = (query or "").strip()
        if query:
            return query

        message = self._message_text(event).strip()
        for prefix in ("/steam搜索", "steam搜索"):
            if message.startswith(prefix):
                return message[len(prefix) :].strip()
        return message

    @staticmethod
    def _message_text(event: AstrMessageEvent) -> str:
        for attr in ("message_str", "raw_message"):
            value = getattr(event, attr, None)
            if isinstance(value, str):
                return value
        getter = getattr(event, "get_message_str", None)
        if callable(getter):
            try:
                return str(getter())
            except Exception:
                return ""
        return ""

    @staticmethod
    def _config_to_dict(config: Any) -> dict[str, Any]:
        if config is None:
            return {}
        if isinstance(config, Mapping):
            return dict(config)

        result: dict[str, Any] = {}
        for key in DEFAULT_CONFIG:
            try:
                value = config.get(key)
            except Exception:
                value = getattr(config, key, None)
            if value is not None:
                result[key] = value
        return result
