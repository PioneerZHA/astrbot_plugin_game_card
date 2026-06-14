# AstrBot Game Card

AstrBot 游戏商店图卡插件。目前支持 Steam 游戏搜索和 Steam 商店链接图卡生成，后续计划扩展 Xbox、PlayStation、Nintendo 等平台，但当前版本尚未接入这些平台。

本项目代码由作者维护，并在开发过程中使用 Codex 辅助生成和整理部分代码、文档与发布配置。

## 功能

- `/steam搜索 游戏名称`：按游戏名搜索 Steam 商店，返回相似游戏和商店链接。
- 自动识别群聊和私聊中的 Steam 商店游戏链接，生成 HTML 图卡并发送图片。
- 支持 Steam 商店语言和地区配置，用于控制详情、价格和本地化文本。
- 支持使用 Playwright Chromium 渲染 HTML/Jinja2 模板并截图。
- 支持配置 Chromium 兼容浏览器路径作为渲染浏览器。
- 支持内置模板和自定义 HTML/Jinja2 模板。
- 支持图片水印开关和水印文案配置。
- 可选使用当前 AstrBot provider 为中文搜索词扩展英文候选词。

## 安装

把本目录放到 AstrBot 插件目录：

```text
AstrBot/data/plugins/astrbot_plugin_game_card
```

安装 Python 依赖：

```bash
pip install -r requirements.txt
```

安装 Playwright Chromium：

```bash
playwright install chromium
```

注意：`playwright install chromium` 是额外步骤，不会由 `pip install -r requirements.txt` 自动完成。

## 平台兼容性

插件逻辑本身不限制 Windows，使用 Playwright 自带 Chromium 时，Windows、Linux、macOS 理论上都可以运行。

目前只有系统浏览器自动探测内置了 Windows 常见 Chrome/Edge 路径。如果在 Linux、macOS 或非标准 Windows 路径上不安装 Playwright Chromium，需要手动配置 `browser_executable_path` 指向可用的 Chromium 兼容浏览器。

示例：

```text
browser_executable_path = C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
```

## 用法

搜索游戏：

```text
/steam搜索 艾尔登法环
/steam搜索 Elden Ring
```

返回格式：

```text
找到了~你说的是不是：
1. ELDEN RING - https://store.steampowered.com/app/1245620/
2. ...
3. ...
4. ...
5. ...
```

发送 Steam 游戏链接即可生成图卡：

```text
https://store.steampowered.com/app/1245620/ELDEN_RING/
```

## 配置

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `enable_search_command` | `true` | 启用 `/steam搜索` 指令 |
| `enable_link_card` | `true` | 识别 Steam 链接并发送图片图卡 |
| `use_llm_translate_for_chinese` | `false` | 中文搜索时使用当前 AstrBot provider 扩展英文候选词 |
| `search_result_count` | `5` | 搜索结果数量 |
| `steam_language` | `schinese` | Steam 商店语言 |
| `steam_country` | `cn` | Steam 商店地区代码 |
| `render_viewport_width` | `1200` | 图片截图视口宽度 |
| `render_device_scale_factor` | `1` | 图片截图倍率 |
| `browser_executable_path` | 空 | 可选 Chromium 兼容浏览器可执行文件路径；自动探测系统浏览器目前仅内置 Windows 常见路径 |
| `card_template` | `steam_card.html` | 内置模板文件名 |
| `custom_template_path` | 空 | 自定义 HTML/Jinja2 模板路径 |
| `enable_watermark` | `true` | 显示图片水印 |
| `watermark_text` | `Crafted by pioneerzha` | 水印文案 |

`use_llm_translate_for_chinese` 开启后会调用 AstrBot 当前配置的 provider，可能消耗模型额度，并依赖当前 provider 可用性。不开启时插件会直接使用用户输入搜索 Steam。

## 图片模板

默认模板是：

```text
templates/steam_card.html
```

备用模板：

```text
templates/steam_magazine_card.html
```

如果配置了 `custom_template_path`，插件会优先使用自定义模板，并忽略 `card_template`。模板可读取游戏名称、简介、价格、截图、类型、平台、开发商、发行商、水印等数据，详细变量见 `templates/README_templates.md`。

## 缓存

生成的图片会缓存到：

```text
data/cache/cards
```

插件当前不会自动清理历史图片。如果使用频率较高，建议定期检查并清理该目录，或在部署环境中自行配置清理策略。

## 常见问题

如果提示图片渲染浏览器不可用，请先执行：

```bash
playwright install chromium
```

如果服务器不方便安装 Playwright Chromium，可以安装 Chromium、Chrome、Edge 等兼容浏览器，并在配置里填写 `browser_executable_path`。

如果 Steam 搜索没有结果，可以尝试：

- 换用英文名搜索。
- 检查服务器是否能访问 Steam 商店接口。
- 开启 `use_llm_translate_for_chinese`，让当前 AstrBot provider 辅助扩展英文候选词。

## 开源协议

本项目使用 MIT License。
