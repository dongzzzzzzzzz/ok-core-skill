---
name: ok-explore
description: |
  OK.com 内容发现技能。搜索帖子、浏览分类、获取详情、首页推荐。
---

# ok-explore — 搜索与浏览

搜索、浏览和获取 OK.com 帖子信息。所有操作支持指定国家和城市。

## 命令

```bash
# 搜索帖子
python scripts/cli.py search --keyword "laptop" --country singapore --city singapore
python scripts/cli.py search --keyword "apartment" --country canada --city toronto --max-results 10

# 获取首页推荐
python scripts/cli.py list-feeds --country singapore --city singapore
python scripts/cli.py list-feeds --country canada --city vancouver --max-results 10

# 按分类浏览
python scripts/cli.py browse-category --category marketplace --country singapore --city singapore
python scripts/cli.py browse-category --category jobs --country canada --city toronto

# 获取帖子详情
python scripts/cli.py get-listing --url "https://sg.ok.com/en/city-singapore/cate-xxx/slug/"
```

## 主要分类 code

| 分类 | Code |
|------|------|
| 市场 | `marketplace` |
| 工作 | `jobs` |
| 房产 | `property` |
| 汽车 | `cars` |
| 服务 | `services` |
| 社区 | `community` |

> 完整分类可通过 `list-categories --country <国家>` 动态获取。

## 参数说明

- `--keyword`: 搜索关键词
- `--category`: 分类 code
- `--country`: 国家（默认 `singapore`）
- `--city`: 城市（默认 `singapore`）
- `--lang`: 语言（默认 `en`）
- `--max-results`: 最大结果数（默认 20）
- `--url`: 帖子 URL（用于 get-listing）
