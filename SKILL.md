---
name: property-advisor
description: |
  房产搜索与决策执行 skill。遇到租房、买房、找房、筛房、比较房源、通勤、周边配套、安全、区域判断等请求时触发。
  这是一个 OpenClaw 优先的编排型 skill：主动调用 ok-core-skill 获取房源，补齐详情，再显式调用仓库内的 public-osm-map-context-skill 做地图增强，最后输出结构化候选表。
metadata:
  short-description: 房产搜索与地图增强编排
---

# Property Advisor

## 角色

你不是“只看文档的决策层”。

你是一个执行型房产编排 skill，必须把请求推进到可交付结果，而不是只描述应该怎么做。

## 必走主链路

当用户提出搜索、筛选、比较房源，或要求看通勤、周边、安全、区域时，默认执行下面的链路：

1. 识别用户需求和最小约束
2. 先判断请求应走 `ok-core-skill` 还是 `gt-core-skill`
3. 对所选上游 skill 做 preflight
4. 用上游 skill 获取房源列表
4. 对优先候选补齐详情页
5. 保存原始房源快照
6. 显式调用仓库内 `public-osm-map-context-skill/scripts/cli.py`
7. 基于房源原始信息和地图 assessments 生成结论
8. 输出固定 8 列候选表

不要把这条链路交给模型自由发挥，也不要只停在“我建议你去调用某个 skill”。

## 运行时硬规则

### 市场路由

- 默认 `market=auto`
- 英国相关请求默认走 `gt-core-skill`
- 非英国请求继续走 `ok-core-skill`
- 如果同时出现英国和非英国高置信地理信号，停止自动路由，明确要求用户确认市场

### ok-core-skill

路径发现顺序固定为：

1. `OK_CORE_SKILL_ROOT`
2. `PROPERTY_OK_SKILL_ROOT`
3. `/Users/a58/Desktop/skills/ok-core-skill`
4. 历史兼容路径 `/Users/a58/Desktop/ok-core-skill/skills/ok-core-skill`

执行顺序固定为：

1. `uv run python scripts/cli.py`
2. `ok-core-skill/.venv/bin/python scripts/cli.py`

禁止：

- 用裸 `python3 scripts/cli.py` 调 `ok-core-skill`
- 假设历史路径一定存在
- 不做 preflight 就直接开跑

### gt-core-skill

路径发现顺序固定为：

1. `GT_CORE_SKILL_ROOT`
2. `PROPERTY_GT_SKILL_ROOT`
3. 当前工作区 `.agents/skills` 与 `skills`
4. `$CODEX_HOME/skills` / `~/.codex/skills`
5. 本地桌面 `gt-core-skill` 开发路径

运行规则固定为：

1. 优先使用支持 `search + detail` 的 Bridge 版 Gumtree skill
2. Bridge 版优先 `uv run python scripts/cli.py`
3. Bridge 版失败时回退 `.venv/bin/python scripts/cli.py`
4. 只有找不到 Bridge 版时，才回退 API `search-listings` 模式

补充规则：

- `gt-core-skill` 的 `logged_in=false` 只记 warning，不算 preflight 失败
- GT API 版不支持详情补全时，必须把缺口写进 `缺失/未知`
- 英国请求默认仍然要补详情，不允许只停在搜索列表

### 地图 skill

- 不依赖 nested skill 自动发现
- 直接调用当前仓库内的 `public-osm-map-context-skill/scripts/cli.py`
- 搜索类场景默认自动跑地图增强
- 地图失败时继续给出候选表，但状态必须写成 `待补地图` 或 `待人工复核`

## 何时必须跑地图增强

只要请求涉及以下任一项，就必须跑地图：

- 位置
- 通勤
- 地铁 / 公交 / tram / train
- 周边配套
- 生活便利度
- 安全
- 噪音
- 区域是否成熟

如果是标准找房搜索，即使用户没有显式强调，也默认首轮跑地图。

## 最终输出硬规则

默认输出固定 8 列：

1. `候选房源`
2. `状态`
3. `价格`
4. `位置`
5. `已满足`
6. `缺失/未知`
7. `淘汰原因/风险`
8. `房源链接`

补充规则：

- `房源链接` 只能用房源原帖链接，不能用 Google Maps / OSM 链接代替
- 可以额外保留地图复核链接，但不能替代原帖链接
- 没有原帖链接的候选不能点名展示，只能汇总进 `hidden_candidates`
- `已满足` 必须由房源原始信息 + 地图 assessments 共同生成
- `缺失/未知` 必须显式列出面积、卫浴、地图降级、路线未验证等缺口
- `淘汰原因/风险` 必须可回溯到价格异常、地图风险、信息不完整、预算不符等事实

## 地图 assessments 消费规则

每套房固定消费 4 个维度：

- `transport_access`
- `daily_convenience`
- `environment_risk`
- `area_maturity`

每个维度都必须带：

- `conclusion`
- `evidence`
- `confidence`
- `limitations`

不要把地图原始 POI 统计直接平铺给用户。
必须把地图数据转成“结论 + 证据”。

## 降级规则

### `precision=address`

- 可以作为首轮排序证据
- 也必须保留 `straight_line_estimate` 的边界说明

### `precision=area`

- 只能做片区判断
- 不能写成楼栋级精确距离
- 状态通常应为 `待人工复核`

### `precision=missing` 或 `status=degraded`

- 不能输出精确交通/配套断言
- 必须保留地图复核链接
- 候选表仍然要出，只是状态降级

## 调试入口

本仓库提供根级 CLI 供调试和回归使用：

```bash
python3 scripts/cli.py doctor --skip-browser-smoke
python3 scripts/cli.py search --keyword "southbank apartment" --city melbourne --country australia
python3 scripts/cli.py search --keyword "studio flat" --query-text "找 London 的 studio flat" --market auto
```

OpenClaw 是正式入口，但本地 CLI 是排查执行层问题的唯一推荐调试入口。

## 参考文档

- [references/data-contract.md](references/data-contract.md)
- [references/map-context-contract.md](references/map-context-contract.md)
- [references/output-contract.md](references/output-contract.md)
- [references/response-examples.md](references/response-examples.md)
