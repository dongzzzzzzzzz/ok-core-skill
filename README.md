# Property Advisor

OpenClaw 优先的房产搜索与地图增强编排 skill。

这个仓库不再是“只会分析文档的纯决策层”，而是一个完整的执行型编排层：

1. 解析用户的房产需求
2. 预检 `ok-core-skill` 运行环境
3. 通过 `ok-core-skill` 搜索房源并补齐详情
4. 保存原始房源快照
5. 显式调用仓库内的 `public-osm-map-context-skill`
6. 生成带证据的地图结论
7. 输出固定 8 列候选表

## 当前能力

- 自动发现 `ok-core-skill` 路径
- 固定优先使用 `uv run python scripts/cli.py`
- `uv` 不可用或 smoke 失败时回退到 `ok-core-skill/.venv/bin/python`
- 显式调用 bundled `public-osm-map-context-skill/scripts/cli.py`
- 输出固定候选表：
  - `候选房源`
  - `状态`
  - `价格`
  - `位置`
  - `已满足`
  - `缺失/未知`
  - `淘汰原因/风险`
  - `房源链接`
- 缺少原帖链接的房源 fail-closed，不会被点名展示

## 项目结构

```text
Property-Advisor/
├── SKILL.md
├── agents/openai.yaml
├── scripts/cli.py
├── property_advisor/
│   ├── analysis.py
│   ├── map_client.py
│   ├── models.py
│   ├── ok_client.py
│   └── orchestrator.py
├── public-osm-map-context-skill/
│   ├── scripts/cli.py
│   └── tests/
├── references/
│   ├── data-contract.md
│   ├── map-context-contract.md
│   ├── output-contract.md
│   └── response-examples.md
└── tests/
```

## 运行规则

### ok-core-skill 路径发现

按下面顺序解析：

1. `OK_CORE_SKILL_ROOT`
2. `PROPERTY_OK_SKILL_ROOT`
3. `/Users/a58/Desktop/skills/ok-core-skill`
4. 历史兼容路径 `/Users/a58/Desktop/ok-core-skill/skills/ok-core-skill`

### ok-core-skill 执行顺序

固定顺序：

1. `uv run python scripts/cli.py`
2. `ok-core-skill/.venv/bin/python scripts/cli.py`

禁止：

- 直接用裸 `python3 scripts/cli.py` 调 `ok-core-skill`
- 依赖模型临场决定如何调用 `ok-core-skill`

### 地图 skill 执行规则

- 不依赖 nested skill 自动发现
- 始终由编排层显式调用仓库内的 `public-osm-map-context-skill/scripts/cli.py`
- 搜索类场景默认自动跑地图增强

## 本地调试

### 1. 环境预检

```bash
python3 scripts/cli.py doctor --skip-browser-smoke
```

### 2. 走完整编排链路

```bash
python3 scripts/cli.py search \
  --keyword "southbank apartment" \
  --country australia \
  --city melbourne \
  --destination "Melbourne CBD VIC" \
  --budget-max 3500 \
  --bedrooms 1
```

### 3. 用地图 fixture 跑稳定回归

```bash
python3 scripts/cli.py search \
  --keyword "southbank apartment" \
  --country australia \
  --city melbourne \
  --destination "Melbourne CBD VIC" \
  --map-fixture-dir public-osm-map-context-skill/tests/fixtures/osm
```

## 输出说明

搜索结果默认返回 JSON，其中包含：

- `preflight`
- `raw_listing_snapshots`
- `map_report`
- `candidate_rows`
- `hidden_candidates`
- `rendered_table`

`candidate_rows[*].display_row` 是最终展示层可直接消费的 8 列结构。

## 测试

```bash
python3 -B -m unittest discover -s tests
python3 -B -m unittest discover -s public-osm-map-context-skill/tests
```

目前已覆盖：

- skill 路径发现
- runner 选择与 fallback
- browser smoke 失败分支
- 房源详情补全
- 地图自动调用
- 地图结构化 assessments
- 缺原帖链接 fail-closed
- 最终 8 列候选表 golden test
