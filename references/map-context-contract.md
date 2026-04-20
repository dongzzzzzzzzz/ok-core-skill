# 地图上下文契约

本文档定义 `property-advisor` 如何消费可选地图上下文数据。地图上下文通常来自 `public-osm-map-context-skill` 这类外部 skill。

本 skill 不要求 `ok-core-skill` 或其他房源数据源改造字段。地图 skill 应基于当前已有的 `title`、`location`、`url`、`description`、`address`、`lat`、`lng` 做 best-effort 分析。

如果 `address` 和 `location` 缺失或质量低，地图 skill 应尝试从 `title` 或 `description` 中提取地址。OK.com 常见标题会把楼名、城市、地址和价格粘在一起，例如 `The Archive, Melbourne205 Normanby Rd, Southbank VIC 3006, Australia`，地图 skill 应先提取 `205 Normanby Rd, Southbank VIC 3006, Australia` 再 geocode。

发布时建议把 `public-osm-map-context-skill` 作为独立 skill 安装或注册；如果运行环境不能发现 nested skill，Agent 仍可按本契约调用当前仓库的参考 CLI。`property-advisor` 不应假设地图 skill 一定存在。

当前仓库提供一个参考实现：

```bash
python3 public-osm-map-context-skill/scripts/cli.py analyze-batch --input listings.json --destination "Melbourne CBD VIC" --city melbourne --incremental
```

参考实现必须快速降级，不能为了地图上下文阻塞整个房产决策。默认 live 行为：

- 单个 HTTP 请求最多等待 8 秒
- 整次 live 分析最多等待 45 秒
- Overpass 每个 endpoint 默认只尝试 1 次
- 批量 geocoding 默认 `photon-first`，Nominatim 只做 fallback，避免 50-100 套房源被 Nominatim 限速拖死
- 超出预算时返回 `status=partial` 或 `status=degraded`，并在 `usage.errors` 中写明 `runtime_budget_exhausted`

---

## 一、能力边界

公共 OSM 地图上下文适合做筛选级增强：

- 地址或区域 geocoding
- 周边 POI 数量统计
- 最近公交 / tram / train 站点距离
- 主路、铁路、工业区等环境风险粗判
- OpenStreetMap / Google Maps 手动验证链接

不适合承诺：

- Google Maps 已验证
- 实时公共交通通勤时间
- Street View 环境判断
- 商户评分、评论、实时营业状态
- POI 数据完整覆盖

---

## 二、输入约定

地图 skill 可接收房源列表：

```json
{
  "listings": [
    {
      "id": "listing_001",
      "title": "The Archive, Southbank",
      "price": "A$786/wk",
      "location": "Southbank VIC",
      "url": "https://...",
      "description": null,
      "address": null,
      "lat": null,
      "lng": null
    }
  ],
  "destination": "Melbourne CBD VIC"
}
```

如果只有 `location`，地图 skill 应返回区域级结果，不应伪装成地址级精度。如果 `location` 只是城市/区域但 `title` 或 `description` 能提取完整街道地址，应优先使用提取出的街道地址。

---

## 三、输出约定

```json
{
  "status": "ok",
  "provider": "public_osm",
  "listings": [
    {
      "id": "listing_001",
      "geo": {
        "lat": -37.823,
        "lng": 144.958,
        "precision": "address",
        "source": "nominatim_or_photon",
        "confidence": "medium",
        "geocode_query_used": "205 Normanby Rd, Southbank VIC 3006, Australia",
        "address_extraction_source": "title"
      },
      "destination_access": {
        "origin": "205 Normanby Rd, Southbank VIC 3006",
        "destination": "Melbourne CBD VIC",
        "distance_type": "straight_line_estimate",
        "straight_line_km": 2.1,
        "walk_minutes_range": "25-40",
        "verified_route": false
      },
      "transit_access": {
        "origin": "205 Normanby Rd, Southbank VIC 3006",
        "nearest_stop_name": "Southbank Tram Stop",
        "distance_type": "straight_line_estimate",
        "distance_meters_range": "350-500",
        "source": "overpass_osm"
      },
      "amenities": {
        "radius_meters": 800,
        "supermarket_count": 3,
        "pharmacy_count": 2,
        "restaurant_count": 18,
        "source": "overpass_osm"
      },
      "risk_signals": {
        "near_primary_road_meters": 90,
        "near_railway_meters": null,
        "industrial_landuse_nearby": false
      },
      "verification_links": {
        "openstreetmap": "https://www.openstreetmap.org/...",
        "google_maps_manual": "https://www.google.com/maps/search/?api=1&query=..."
      },
      "limitations": [
        "not_google_maps_verified",
        "public_transport_time_not_verified",
        "osm_coverage_may_be_incomplete"
      ]
    }
  ]
}
```

`status` 可以是：

- `ok`：地图上下文可用
- `partial`：部分房源或部分区域失败
- `degraded`：公共 OSM 服务不可用或关键字段不足，只能给验证链接

`partial` 是正常可消费状态。`property-advisor` 应继续做推荐，但只能把已完成的地图字段作为辅助信号；不能因为部分 Overpass/geocode 超时而中断整轮回答。

`geo.precision` 可以是：

- `address`：地址级或接近地址级位置
- `area`：区域中心点或片区级位置
- `missing`：无法定位

`geo.confidence` 可以是：

- `high`
- `medium`
- `low`

---

## 四、消费规则

`property-advisor` 消费地图上下文时必须按精度降级：

| 地图结果 | 可用表达 | 禁止表达 |
| --- | --- | --- |
| `precision=address`, `confidence=high/medium` | “基于 OSM 估算，约 350-500m 到最近 tram stop” | “Google Maps 确认步行 6 分钟” |
| `precision=area` | “Southbank 区域整体生活配套较成熟” | “这套房 800m 内有 3 个超市” |
| `precision=missing` | “地图信息不足，需手动验证” | 任何精确距离或设施数量 |
| `status=degraded` | “地图深度分析暂不可用，建议打开链接复核” | 假装已完成地图分析 |

如果 `geo.precision=missing`，仍必须输出 `verification_links.google_maps_manual`。最终回答应说明该链接用于手动验证通勤路线、最近公共交通、超市/药店和噪音源。

所有距离表达必须有明确对象：

- 到目的地：必须写成“从 `[房源地址/标题]` 到 `[用户目的地]` 的直线估算距离约 X km”，不能只写“直线约 X km”
- 到公共交通：必须写出 `nearest_stop_name`，例如“从 `[房源地址]` 到 OSM 记录的 `[Stop 19: Shrine of Remembrance]` 直线估算约 100-150m”
- 如果 `distance_type=straight_line_estimate`，必须说明不是 Google Maps 步行路线
- 如果 `confidence=low` 或 `source=photon`，不得使用具体米数作为强推荐理由，只能写“地图定位置信度低，需打开验证链接复核”

如果 OSM 没记录到某类设施，只能写“OSM 未记录到”，不能写“周边没有”。

如果 `source=photon` 或 `confidence=low`，应按区域级或低置信结果消费，不要把距离和周边统计作为强推荐理由。

低置信地图结果不能让最终回答失去可用性。`property-advisor` 应继续根据价格、区域、卧室数、异常价、房源信息完整度和下一步核验动作给出初筛建议。

---

## 五、编排规则

推荐 Agent 编排：

1. 先获取房源列表和详情
2. 如果用户关心通勤、周边或区域风险，且环境中存在地图 skill，则调用地图 skill
3. 将地图 skill 的 JSON 与房源数据一起交给 `property-advisor`
4. 如果地图 skill 不存在或返回 degraded，仍继续完成初筛推荐，并明确地图信息未确认
5. 不要因为 `address/location` 为空就跳过地图；地图 skill 可以从 `title` 或 `description` 做 best-effort 地址提取

不要要求房源数据源增加经纬度字段；如果上游没有坐标，地图 skill 自行降级处理。
