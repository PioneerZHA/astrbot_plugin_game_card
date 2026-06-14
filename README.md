# AstrBot Steam Card

一个最小可用的 AstrBot Steam 查询插件：

- `/steam搜索 游戏名称`：只返回 1 句提示 + 5 个相似 Steam 游戏和商店链接。
- 群消息里直接发送 Steam 商店链接：自动生成 HTML 图卡并发送图片。

## 安装

把本目录放到 AstrBot 的插件目录：

```text
AstrBot/data/plugins/astrbot_plugin_steam_card
```

安装 Python 依赖：

```bash
pip install -r requirements.txt
playwright install chromium
```

如果不想下载 Playwright Chromium，插件会自动尝试使用系统 Chrome/Edge。也可以在配置里填写：

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

生成图片：

```text
https://store.steampowered.com/app/1245620/ELDEN_RING/
```

## 图片模板

图片由 `templates/steam_card.html` 渲染后截图生成。Python 逻辑没有写死输出图片高度，截图会按 HTML 完整页面高度输出。

可在 AstrBot 插件配置里调整：

- `render_viewport_width`：浏览器截图视口宽度。
- `render_device_scale_factor`：截图缩放倍率。
- `browser_executable_path`：可选 Chrome/Edge 路径。
- `enable_watermark`：是否显示图片底部水印，默认开启。
- `watermark_text`：水印文案，默认 `Crafted by pioneerzha`。

后续改图片样式时，优先修改 `templates/steam_card.html`。
