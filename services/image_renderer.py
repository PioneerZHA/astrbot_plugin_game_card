import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape


class ImageRenderError(Exception):
    """Raised when the HTML card cannot be rendered into an image."""


class BrowserUnavailableError(ImageRenderError):
    """Raised when Playwright or a Chromium-compatible browser is unavailable."""


class HtmlImageRenderer:
    def __init__(
        self,
        plugin_dir: Path,
        viewport_width: int = 1200,
        device_scale_factor: int = 1,
        browser_executable_path: str = "",
        enable_watermark: bool = True,
        watermark_text: str = "Crafted by pioneerzha",
        card_template: str = "steam_card.html",
        custom_template_path: str = "",
    ):
        self.plugin_dir = plugin_dir
        self.template_dir = plugin_dir / "templates"
        self.output_dir = plugin_dir / "data" / "cache" / "cards"
        self.viewport_width = max(int(viewport_width or 1200), 320)
        self.device_scale_factor = max(int(device_scale_factor or 1), 1)
        self.browser_executable_path = browser_executable_path.strip()
        self.enable_watermark = bool(enable_watermark)
        self.watermark_text = (watermark_text or "").strip()
        self.card_template = self._normalize_template_name(card_template)
        self.custom_template_path = (custom_template_path or "").strip()
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(("html", "xml")),
        )

    async def render_card(self, app: dict[str, Any]) -> Path:
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise BrowserUnavailableError("missing playwright dependency") from exc

        self.output_dir.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(app.get("name") or app.get("appid") or "steam"))
        safe_template = re.sub(r"[^a-zA-Z0-9_-]+", "_", self._template_label())
        output_path = self.output_dir / f"{app['appid']}_{safe_name[:40]}_{safe_template[:24]}.png"

        html = self._render_html(app)

        try:
            async with async_playwright() as p:
                browser = await self._launch_browser(p)
                try:
                    page = await browser.new_page(
                        viewport={"width": self.viewport_width, "height": 1},
                        device_scale_factor=self.device_scale_factor,
                    )
                    await page.set_content(html, wait_until="networkidle")
                    await page.screenshot(path=str(output_path), full_page=True)
                finally:
                    await browser.close()
        except BrowserUnavailableError:
            raise
        except Exception as exc:
            raise ImageRenderError("failed to render Steam card image") from exc

        return output_path

    def _render_html(self, app: dict[str, Any]) -> str:
        context = {
            "app": app,
            "watermark": {
                "enabled": self.enable_watermark and bool(self.watermark_text),
                "text": self.watermark_text,
            },
        }

        if self.custom_template_path:
            template_path = self._resolve_custom_template_path(self.custom_template_path)
            env = Environment(
                loader=FileSystemLoader(str(template_path.parent)),
                autoescape=select_autoescape(("html", "xml")),
            )
            return env.get_template(template_path.name).render(**context)

        try:
            return self.env.get_template(self.card_template).render(**context)
        except TemplateNotFound as exc:
            raise ImageRenderError(f"template not found: {self.card_template}") from exc

    def _template_label(self) -> str:
        if self.custom_template_path:
            return Path(self.custom_template_path).stem or "custom_template"
        return Path(self.card_template).stem or "steam_card"

    def _resolve_custom_template_path(self, template_path: str) -> Path:
        path = Path(template_path).expanduser()
        if not path.is_absolute():
            path = self.plugin_dir / path
        path = path.resolve()

        if not path.is_file():
            raise ImageRenderError(f"custom template not found: {path}")
        if path.suffix.lower() not in {".html", ".htm"}:
            raise ImageRenderError("custom template must be an .html or .htm file")
        return path

    @staticmethod
    def _normalize_template_name(template_name: str) -> str:
        name = (template_name or "steam_card.html").strip() or "steam_card.html"
        if not name.lower().endswith((".html", ".htm")):
            name = f"{name}.html"

        path = Path(name)
        if path.name != name:
            raise ImageRenderError("card_template must be a file name in the templates directory")
        return name

    async def _launch_browser(self, playwright: Any) -> Any:
        errors: list[str] = []
        candidates = self._browser_candidates()

        for executable_path in candidates:
            try:
                if executable_path:
                    return await playwright.chromium.launch(headless=True, executable_path=executable_path)
                return await playwright.chromium.launch(headless=True)
            except Exception as exc:
                errors.append(str(exc))

        raise BrowserUnavailableError(
            "Playwright cannot launch Chromium. Run `playwright install chromium`, "
            "or set browser_executable_path to a Chromium-compatible browser executable."
        ) from RuntimeError("\n".join(errors))

    def _browser_candidates(self) -> list[str]:
        candidates = [self.browser_executable_path, ""]
        candidates.extend(
            [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            ]
        )

        deduped: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            candidate = candidate.strip()
            key = candidate.lower()
            if key in seen:
                continue
            if not candidate or Path(candidate).exists():
                deduped.append(candidate)
                seen.add(key)
        return deduped
