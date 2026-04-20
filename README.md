# Property Advisor V2

全球房产**决策** Skill — 面向买房、卖房、租房、短租场景的 Agent 决策助手。

## 设计理念

**本 Skill 是纯决策层，不做任何数据获取。**

- `SKILL.md` — 决策大脑：场景识别、用户画像、分析维度、避坑清单、输出规范
- `references/` — 决策知识库：区域画像、价格框架、看房清单、工具使用方法论、地图上下文契约
- 数据由外部 skill（如 ok-core-skill、public-osm-map-context-skill）提供，本 skill 只消费数据、做判断

### 为什么这样设计？

1. **解耦**：决策逻辑和数据获取分离。换数据源时不需要改决策 skill
2. **可扩展**：未来可对接 PropertyGuru scraper、99.co API、公共 OSM 地图上下文等任何数据源
3. **专注**：SKILL.md 只关心"拿到数据后怎么判断"，不关心"数据从哪来"

## 项目结构

```
Property_skill_v2/
├── SKILL.md                              # 核心决策文档（Agent 的决策策略）
├── public-osm-map-context-skill/         # 可选地图上下文 skill（零 API key，公共 OSM best-effort）
├── references/
│   ├── data-contract.md                  # 数据输入 schema（对接数据源的契约）
│   ├── decision-dimensions.md            # 价格分析、信息完整度、投资维度
│   ├── map-context-contract.md           # 地图上下文 schema、精度和表达边界
│   ├── region-profiles.md                # 区域画像：新加坡/迪拜/美国/日本/英国/香港
│   ├── viewing-checklist.md              # 看房决策清单：噪音/朝向/设施/费用/租约
│   └── decision-toolkit.md              # 决策辅助工具使用方法论
├── pyproject.toml
└── README.md
```

## 数据源对接

本 skill 通过 `references/data-contract.md` 定义标准数据 schema。任何数据源 skill 只要输出符合 schema 的 JSON，即可与本 skill 配合使用。

当前支持：
- **ok-core-skill** — 全球房源（OK.com）

可选支持：
- **public-osm-map-context-skill** — 公共 OSM 地图上下文（地址/区域级周边、交通点、风险信号）。不要求 ok-core-skill 改字段。

对接新数据源时：
1. 确保数据源输出符合 `data-contract.md` 的 schema
2. 地图上下文类数据源需符合 `references/map-context-contract.md`
3. 在 SKILL.md 的"数据来源"章节注册

## 决策能力一览

| 维度 | 内容 |
|------|------|
| 场景覆盖 | 买/卖/租/短租 |
| 用户画像 | 家庭、白领、学生、投资者、外派、退休、数字游民 |
| 区域画像 | 新加坡 8 区、迪拜 6 区、美国/日本/英国/香港通用框架 |
| 通勤评估 | 按数据精度区分地址级/区域级/缺失，避免伪精确结论 |
| 生活便利 | 可消费公共 OSM 周边 POI 统计；结果需标注来源和复核边界 |
| 看房清单 | 噪音(5类) + 朝向 + 设施 + 费用 + 租约条款 20+ 检查项 |
| 决策工具 | 公共 OSM 地图上下文 + Google Maps/当地 App 复核建议 + 各地房产平台 |
| 价格分析 | 异常检测 + 周期标准化 + 信息完整度评分 |
| 投资分析 | 毛回报率 + 地区市场特征 |
| 避坑清单 | 全球通用 + 7 个地区特有 |

## 与 V1 的区别

| 维度 | V1 | V2 |
|------|-----|-----|
| 定位 | 数据管道 + 简单决策 | **纯决策层**，不含任何数据获取代码 |
| SKILL.md | 300+ 行（含 CLI 示例） | 250+ 行纯决策策略 |
| references | 2 个文件 | 数据契约 + 地图上下文契约 + 决策维度 + 区域画像 + 看房清单 + 工具方法论 |
| 代码 | ~170 行 CLI | 0 行（无代码） |
| 数据源耦合 | 硬编码 ok-core-skill 路径 | 通过 data-contract.md 解耦，可对接任意数据源 |
| 区域深度 | 地区避坑一句话 | 精确到区域/楼盘级别画像 |
| 工具指导 | 无 | 详细的工具使用方法论（Google Maps 4 种用途 + 地区平台 + 交通 App） |
| 看房支持 | 无 | 20+ 项看房检查清单 |
