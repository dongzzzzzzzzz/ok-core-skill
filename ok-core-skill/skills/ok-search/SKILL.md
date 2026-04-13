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
- **必须按以下 5 个步骤顺序执行**，不可跳步

---

## 步骤 1 — 解析用户意图（不执行命令，先想清楚）

从用户自然语言中提取要素：

| 要素 | 说明 | 示例 |
|------|------|------|
| 国家 | 地点所属国家英文名 | usa, japan, canada |
| 城市关键词 | 地点英文名，用于搜索城市 | hawaii, tokyo, vancouver |
| 内容类型 | 分类 code 或搜索关键词 | property, jobs, "laptop" |
| 价格区间（可选） | 用户提到的价格范围 | 50万以下、100-200万、$500以内 |

**中文→英文映射必须在此步完成：**

| 中文地名 | country | keyword |
|---------|---------|---------|
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

| 中文内容类型 | 映射方式 |
|------------|---------|
| 房源/房子/租房/公寓 | `browse-category --category property` |
| 工作/招聘/求职 | `browse-category --category jobs` |
| 二手/买卖/市场 | `browse-category --category marketplace` |
| 车/汽车/买车 | `browse-category --category cars` |
| 服务/维修 | `browse-category --category services` |
| 具体物品（如"笔记本电脑"） | `search --keyword "laptop"` （翻译为英文关键词） |

**价格区间映射（用户提到价格时必须提取）：**

| 用户说的 | --min-price | --max-price |
|---------|-------------|-------------|
| 50万以下 / 50万以内 | 不传 | 500000 |
| 100万以上 | 1000000 | 不传 |
| 100-200万 / 100万到200万 | 1000000 | 2000000 |
| $500以内 | 不传 | 500 |
| 5000刀以上 | 5000 | 不传 |
| 便宜的 / 低价 | 不传 | 不传（不猜测，可建议用户指定具体范围） |

注意：ok.com 价格为当地货币（美国=USD、新加坡=SGD 等），映射时保持用户给出的数值单位。"万"需乘以 10000。

如果用户**未指定地点**，先询问"您想在哪个国家/城市搜索？"，不要猜测。

## 步骤 2 — 确定城市 code

直接用 search 模式查找城市（**不要先跑 api 模式**，因为小城市不在 allCities 列表里）：

```bash
uv run python scripts/cli.py list-cities --country <国家> --mode search --keyword <城市英文名>
```

- 从返回 JSON 的 `cities` 数组中选取 `name` 最匹配的那个，记下其 `code` 字段
- 如果返回多个结果，选择名称最精确匹配的；如果不确定，询问用户
- 如果返回空结果，尝试缩短关键词（如 `hawaii` → `hawa`）；仍然为空则告知用户"未找到该城市"

## 步骤 3 — 切换地区

```bash
uv run python scripts/cli.py set-locale --country <国家> --city <city_code>
```

## 步骤 4 — 搜索或浏览

根据步骤 1 确定的内容类型选择命令，**必须显式传入 `--country` 和 `--city`**（默认值是 singapore，不传会搜错地区）：

**按分类浏览（优先，当内容类型对应某个分类时）：**
```bash
uv run python scripts/cli.py browse-category --category <分类code> --country <国家> --city <city_code> [--min-price <数值>] [--max-price <数值>]
```

**按关键词搜索（当用户指定具体物品名称时）：**
```bash
uv run python scripts/cli.py search --keyword "<英文关键词>" --country <国家> --city <city_code> [--min-price <数值>] [--max-price <数值>]
```

## 步骤 5 — 展示结果

将 JSON 输出结构化展示给用户，格式：

```
1. **标题** — 价格
   地点 | [查看详情](url)

2. **标题** — 价格
   地点 | [查看详情](url)
```

如果用户想看某条帖子的详情：
```bash
uv run python scripts/cli.py get-listing --url "<帖子URL>"
```

详情展示包含：标题、价格、描述（前 200 字）、卖家、发布时间、图片链接、分类面包屑。

## 结果为空时的处理

- 搜索无结果 → 告知用户"该地区暂无相关帖子"，建议更换关键词或尝试 `browse-category` 浏览大类
- 浏览分类无结果 → 告知用户"该地区该分类暂无帖子"，建议换一个分类或换关键词搜索

---

## 完整示例

### 示例 1：用户说"找夏威夷房源"

```bash
# 步骤 1: 解析 → country=usa, keyword=hawaii, 内容=property, 价格=不限
# 步骤 2: 查找城市 code
uv run python scripts/cli.py list-cities --country usa --mode search --keyword hawaii
# 步骤 3: 切换地区
uv run python scripts/cli.py set-locale --country usa --city hawaii
# 步骤 4: 浏览房产分类
uv run python scripts/cli.py browse-category --category property --country usa --city hawaii
# 步骤 5: 结构化展示结果给用户
```

### 示例 2：用户说"夏威夷50万到200万的房子"

```bash
# 步骤 1: 解析 → country=usa, keyword=hawaii, 内容=property, 价格=500000-2000000
# 步骤 2: 查找城市 code
uv run python scripts/cli.py list-cities --country usa --mode search --keyword hawaii
# 步骤 3: 切换地区
uv run python scripts/cli.py set-locale --country usa --city hawaii
# 步骤 4: 浏览房产分类 + 价格筛选
uv run python scripts/cli.py browse-category --category property --country usa --city hawaii --min-price 500000 --max-price 2000000
# 步骤 5: 结构化展示结果给用户
```
