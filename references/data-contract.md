# 数据输入契约

本 skill 是纯决策层，不获取数据。数据由外部 skill（如 ok-core-skill、PropertyGuru scraper 等）提供。

任何数据源只要满足以下 schema，即可与本 skill 对接。Agent 在拿到数据后按 SKILL.md 的决策策略进行分析。

---

## 房源列表 (ListingList)

搜索或浏览返回的结果集。

```json
{
  "total": 25,
  "listings": [ /* ListingItem[] */ ]
}
```

### ListingItem

| 字段 | 类型 | 必须 | 说明 |
|------|------|------|------|
| `title` | string | 是 | 房源标题 |
| `price` | string | 是 | 原始价格文本（含币种和周期，如 `S$ 3,200 /mo`） |
| `location` | string | 是 | 区域级别位置（如 `Bedok, Singapore`） |
| `url` | string | 是 | 原帖链接 |
| `image_url` | string \| null | 否 | 封面图 URL |
| `listing_id` | string | 否 | 平台唯一 ID |
| `address` | string \| null | 否 | 完整或半完整地址。数据源没有时不要强求 |
| `lat` | number \| null | 否 | 纬度。仅在数据源天然提供时使用 |
| `lng` | number \| null | 否 | 经度。仅在数据源天然提供时使用 |
| `geo_precision` | string \| null | 否 | `address` / `area` / `missing`，表示位置精度 |

---

## 房源详情 (ListingDetail)

单条房源的完整信息。

```json
{
  "title": "2BR Apartment in Bedok",
  "price": "S$ 3,200 /mo",
  "description": "Well furnished apartment...",
  "location": "Bedok, Singapore",
  "seller_name": "John Property Agent",
  "images": ["https://...", "https://..."],
  "url": "https://...",
  "listing_id": "12345678",
  "category": "Property > Apartment",
  "posted_time": "2 days ago"
}
```

### 字段清单

| 字段 | 类型 | 必须 | 说明 |
|------|------|------|------|
| `title` | string | 是 | 房源标题 |
| `price` | string | 是 | 原始价格文本 |
| `location` | string | 是 | 区域级位置 |
| `url` | string | 是 | 原帖链接 |
| `description` | string \| null | 否 | 房源描述全文 |
| `seller_name` | string \| null | 否 | 发布者名称 |
| `images` | string[] | 否 | 完整图片列表 |
| `listing_id` | string | 否 | 平台唯一 ID |
| `category` | string \| null | 否 | 分类路径 |
| `posted_time` | string \| null | 否 | 发布时间（可能是相对时间） |
| `address` | string \| null | 否 | 完整或半完整地址。可从详情页文本中获得时提供 |
| `lat` | number \| null | 否 | 纬度。仅在数据源天然提供时使用 |
| `lng` | number \| null | 否 | 经度。仅在数据源天然提供时使用 |
| `geo_precision` | string \| null | 否 | `address` / `area` / `missing`，表示位置精度 |

---

## 价格统计 (PriceStats)

可选。数据源 skill 如果能计算价格统计则提供，否则由决策层根据 listings 自行推算。

```json
{
  "count": 20,
  "min": 2200.0,
  "max": 5800.0,
  "mean": 3450.0,
  "median": 3200.0
}
```

---

## 对比矩阵 (CompareMatrix)

可选。多房源横向对比的结构化数据。

```json
{
  "compared": 3,
  "matrix": [
    {
      "title": "...",
      "price": "...",
      "price_numeric": 3200.0,
      "location": "...",
      "images_count": 12,
      "has_description": true,
      "seller_name": "...",
      "url": "..."
    }
  ],
  "full_details": [ /* ListingDetail[] */ ]
}
```

---

## 数据局限性声明

无论数据来自哪个 skill，以下信息通常**不可用**，Agent 不应假装拥有：

- 精确地理坐标（经纬度）。如果数据源没有提供，不能要求上游数据源改造，只能由地图上下文 skill 做 best-effort 补充
- 实际通勤时间（需借助 Google Maps 等工具验证）
- 学区信息
- 安全评级 / 犯罪率
- 历史价格变动 / 成交价
- 房东联系方式（只有发布者名称）
- 合同细节（押金、最短租期等）

当需要上述信息辅助决策时，参考 [decision-toolkit.md](decision-toolkit.md) 中的工具使用方法。

地图上下文数据由可选外部 skill 提供，契约见 [map-context-contract.md](map-context-contract.md)。如果地图结果只有区域级精度或处于 degraded 状态，决策层必须降低结论强度。

---

## 对接新数据源

如果要接入新的数据源 skill：

1. 确保其输出符合上述 schema（至少覆盖必须字段）
2. 在 SKILL.md 的"数据来源"章节注册该 skill 的名称和获取方式
3. 字段映射差异在数据源 skill 侧处理，决策层只消费标准 schema
