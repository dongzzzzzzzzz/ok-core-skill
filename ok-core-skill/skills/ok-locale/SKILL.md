---
name: ok-locale
description: |
  OK.com 多国家/城市/语言管理技能。城市和分类通过 API 动态获取。
---

# ok-locale — 多国家/城市/语言管理

管理 OK.com 的区域设置。国家为固定列表，城市和分类通过 API 动态获取。

## 命令

```bash
# 列出支持的国家
uv run python scripts/cli.py list-countries

# 动态获取城市列表
uv run python scripts/cli.py list-cities --country usa --mode search --keyword 'new york'

# 动态获取分类树
uv run python scripts/cli.py list-categories --country singapore

# 切换到指定地区
uv run python scripts/cli.py set-locale --country singapore --city singapore --lang en
uv run python scripts/cli.py set-locale --country canada --city toronto

# 获取当前地区
uv run python scripts/cli.py get-locale
```

## 参数说明

- `--country`: 国家名（如 `singapore`）、子域名（如 `sg`）或 ISO code（如 `SG`）
- `--city`: 城市 code（可从 `list-cities` 获取，如 `singapore`, `toronto`, `bedok`）
- `--lang`: 语言代码（默认 `en`）
- `--keyword`: 搜索关键词（城市名，用于搜索城市，如`hawaii`）

## 工作流

1. 先用 `list-countries` 确定目标国家
2. 用 `list-cities --country <国家>` 获取可用城市
3. 如果没有找到，可以用 `list-cities --country <国家> --mode search --keyword <城市关键词>` 搜索
4. 用 `set-locale` 切换到目标地区
5. 后续搜索/浏览操作使用对应的 `--country` `--city` 参数
