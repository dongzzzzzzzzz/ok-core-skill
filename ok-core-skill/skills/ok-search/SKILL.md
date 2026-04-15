---
name: ok-search
description: |
  OK.com 复合搜索技能。处理"在某地找某类内容"的完整流程：解析意图、定位城市、切换地区、搜索/浏览、展示结果。支持价格区间筛选。
  当用户请求包含 地点+内容 两个要素时触发（如"找夏威夷房源"、"搜索东京的工作"、"温哥华二手车"、"夏威夷50万以下的房子"）。
---

# ok-search — 复合搜索工作流

处理"在某地找某类内容"的完整流程。当用户请求同时包含**地点**和**内容**两个要素时使用此技能。

## 执行约束（强制）

- 所有操作只能通过 `uv run python scripts/cli.py` 执行，**禁止自行编写代码或直接调用 API**
- **使用 `full-search` 一站式命令**（单次调用完成全部流程）

---

## 步骤 1 — 解析用户意图

从用户自然语言中提取要素：

| 要素 | 说明 | 示例 |
|------|------|------|
| 国家 | **必须从下方 10 个值中选** | usa, japan, canada |
| 城市关键词 | 地点英文名 | hawaii, tokyo, vancouver |
| 内容类型 | 分类 code 或搜索关键词 | property, jobs, "laptop" |
| 价格区间 | 可选 | 50万以下、100-200万、$500以内 |

**`--country` 只接受以下 10 个值（不可自造）：**
`singapore` `canada` `usa` `uae` `australia` `hong_kong` `japan` `uk` `malaysia` `new_zealand`

**中文→英文映射必须在此步完成：**

| 中文地名 | country | city |
|---------|---------|------|
| 夏威夷 | usa | hawaii |
| 新加坡 | singapore | singapore |
| 多伦多 | canada | toronto |
| 温哥华 | canada | vancouver |
| 东京 | japan | tokyo |
| 迪拜 | uae | dubai |
| 悉尼 | australia | sydney |
| 香港 | hong_kong | hong-kong |
| 吉隆坡 | malaysia | kuala-lumpur |
| 伦敦 | uk | london |
| 奥克兰 | new_zealand | auckland |

| 中文内容类型 | --category |
|------------|-----------|
| 房源/房子/租房/公寓 | property |
| 工作/招聘/求职 | jobs |
| 二手/买卖/市场 | marketplace |
| 车/汽车/买车 | cars |
| 服务/维修 | services |
| 具体物品（如"笔记本电脑"） | 不传 category，用 `--keyword "laptop"` |

**价格区间映射：**

| 用户说的 | --min-price | --max-price |
|---------|-------------|-------------|
| 50万以下 | 不传 | 500000 |
| 100万以上 | 1000000 | 不传 |
| 100-200万 | 1000000 | 2000000 |
| $500以内 | 不传 | 500 |
| 5000刀以上 | 5000 | 不传 |
| 便宜的/低价 | 不传 | 不传（建议用户指定范围） |

注意：ok.com 价格为当地货币（美国=USD、新加坡=SGD 等），"万"需乘以 10000。

如果用户**未指定地点**，先询问"您想在哪个国家/城市搜索？"，不要猜测。

---

## 步骤 2 — 执行 full-search

```bash
uv run python scripts/cli.py full-search \
  --country <国家> --city <城市名> \
  [--category <分类code>] [--keyword <搜索关键词>] \
  [--min-price <数值>] [--max-price <数值>] \
  [--max-results 20]
```

- `--country` 和 `--city` 必填
- `--category` 和 `--keyword` 至少提供一个；同时提供时先进入分类页再搜索
- 内部自动完成：打开网站 → UI 搜索城市并点选切换 → 点击分类 → 输入关键词搜索 → 价格筛选 → 提取结果

### 示例

```bash
# 找夏威夷房源
uv run python scripts/cli.py full-search --country usa --city hawaii --category property

# 夏威夷50万到200万的房子
uv run python scripts/cli.py full-search --country usa --city hawaii --category property --min-price 500000 --max-price 2000000

# 在新加坡搜索笔记本电脑
uv run python scripts/cli.py full-search --country singapore --city singapore --keyword "laptop"

# 东京的工作
uv run python scripts/cli.py full-search --country japan --city tokyo --category jobs
```

---

## 步骤 3 — 展示结果

将 JSON 输出结构化展示给用户：

```
1. **标题** — 价格
   地点 | [查看详情](url)
```

如果用户想看某条帖子的详情：
```bash
uv run python scripts/cli.py get-listing --url "<帖子URL>"
```

## 结果为空时的处理

- 搜索无结果 → 告知用户"该地区暂无相关帖子"，建议更换关键词或分类
- 如果不确定分类 → 建议用 `--keyword` 代替 `--category`
