# Steam 图卡模板说明

本目录用于存放 Steam 链接图卡的 HTML 模板。模板由 Jinja2 渲染，再交给浏览器截图生成图片。

默认模板：

```text
steam_magazine_card.html
```

保留模板：

```text
steam_card.html
```

## 配置规则

插件配置里有两个模板相关字段：

```json
{
  "card_template": "steam_magazine_card.html",
  "custom_template_path": ""
}
```

- `card_template`：填写插件 `templates` 目录下的模板文件名。
- `custom_template_path`：填写用户自己的 HTML 模板路径。
- `custom_template_path` 不为空时，优先使用它，忽略 `card_template`。
- `custom_template_path` 可以是绝对路径，也可以是相对插件目录的路径。
- 模板文件必须是 `.html` 或 `.htm`。
- `card_template` 只能写文件名，不能写子目录路径。

示例：

```json
{
  "card_template": "steam_card.html",
  "custom_template_path": ""
}
```

```json
{
  "card_template": "steam_magazine_card.html",
  "custom_template_path": "templates/my_card.html"
}
```

```json
{
  "custom_template_path": "C:\\Users\\YourName\\Desktop\\my_card.html"
}
```

## 可用变量

模板中可以直接使用 `app` 和 `watermark`。

### 基础信息

```jinja2
{{ app.appid }}
{{ app.name }}
{{ app.url }}
{{ app.short_description }}
{{ app.release_date }}
```

### 图片

```jinja2
{{ app.header_image }}
{{ app.capsule_image }}
{{ app.screenshots }}
{{ app.screenshots[0] }}
```

注意：

- `app.header_image` 是 Steam 商店头图。
- `app.capsule_image` 是 Steam 胶囊图。
- `app.screenshots` 是截图列表，可能为空。
- 使用截图下标前，建议先判断长度。

示例：

```jinja2
{% set screenshots = app.screenshots or [] %}

{% if app.header_image %}
<img src="{{ app.header_image }}" alt="{{ app.name }}">
{% elif screenshots %}
<img src="{{ screenshots[0] }}" alt="{{ app.name }}">
{% elif app.capsule_image %}
<img src="{{ app.capsule_image }}" alt="{{ app.name }}">
{% endif %}
```

### 开发与发行

```jinja2
{{ app.developers }}
{{ app.publishers }}
{{ app.developers | join(", ") }}
{{ app.publishers | join(", ") }}
```

注意：

- `app.developers` 是列表，可能为空。
- `app.publishers` 是列表，可能为空。

示例：

```jinja2
{% if app.developers %}
<span>开发商：{{ app.developers | join(", ") }}</span>
{% endif %}
```

### 类型与平台

```jinja2
{{ app.genres }}
{{ app.platforms }}
```

示例：

```jinja2
{% for genre in app.genres[:6] %}
<span>{{ genre }}</span>
{% endfor %}

{% for platform in app.platforms[:3] %}
<span>{{ platform }}</span>
{% endfor %}
```

### 价格

```jinja2
{{ app.price.current }}
{{ app.price.original }}
{{ app.price.discount_percent }}
{{ app.price.has_discount }}
```

示例：

```jinja2
{% if app.price.has_discount %}
<span>-{{ app.price.discount_percent }}%</span>
{% endif %}

{% if app.price.original %}
<span>{{ app.price.original }}</span>
{% endif %}

<strong>{{ app.price.current }}</strong>
```

### 水印

```jinja2
{{ watermark.enabled }}
{{ watermark.text }}
```

水印由插件配置控制：

```json
{
  "enable_watermark": true,
  "watermark_text": "Crafted by pioneerzha"
}
```

模板里需要自己写水印位置，否则即使配置开启也不会显示。

示例：

```jinja2
{% if watermark.enabled %}
<div class="watermark">{{ watermark.text }}</div>
{% endif %}
```

## 推荐写法

### 先设置默认列表

```jinja2
{% set screenshots = app.screenshots or [] %}
{% set genres = app.genres or [] %}
{% set platforms = app.platforms or [] %}
```

这样可以避免空值导致模板判断复杂。

### 控制图片比例

建议给图片容器设置稳定比例：

```css
.cover {
  aspect-ratio: 16 / 9;
  overflow: hidden;
}

.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
```

### 避免固定高度页面

截图使用完整页面高度。模板可以固定局部图片比例，但不建议给 `body` 或主容器写死高度，否则长标题、长简介、长开发商名称可能溢出。

### 保持文字可换行

游戏名、开发商、发行商、简介和链接都可能很长，建议给文字区域加：

```css
overflow-wrap: anywhere;
```

### 谨慎使用外部资源

模板可以引用网络图片和 CSS，但截图时需要浏览器能访问这些资源。为了稳定，建议：

- 字体优先使用系统字体。
- 不依赖第三方 JS。
- 不使用需要登录、Cookie 或跨域鉴权的资源。

### 页面宽度

截图视口宽度由配置 `render_viewport_width` 控制，默认是 `1200`。模板应至少兼容：

- 桌面宽度：`1200px`
- 窄屏宽度：`320px` 以上

## 最小模板示例

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <style>
    body {
      margin: 0;
      font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
      background: #111;
      color: #fff;
    }

    .card {
      padding: 32px;
    }

    img {
      width: 100%;
      max-height: 360px;
      object-fit: cover;
    }
  </style>
</head>
<body>
  {% set screenshots = app.screenshots or [] %}

  <main class="card">
    <h1>{{ app.name }}</h1>

    {% if app.header_image %}
    <img src="{{ app.header_image }}" alt="{{ app.name }}">
    {% elif screenshots %}
    <img src="{{ screenshots[0] }}" alt="{{ app.name }}">
    {% endif %}

    {% if app.short_description %}
    <p>{{ app.short_description }}</p>
    {% endif %}

    <p>{{ app.price.current }}</p>
    <p>{{ app.url }}</p>

    {% if watermark.enabled %}
    <small>{{ watermark.text }}</small>
    {% endif %}
  </main>
</body>
</html>
```
