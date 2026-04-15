# OK Skills AG

OK.com 分类信息自动化 Skills，通过 Chrome 扩展 + Python 引擎，让 AI Agent 以真实用户身份操作 OK.com。

支持 [OpenClaw](https://github.com/anthropics/openclaw) 及所有兼容 `SKILL.md` 格式的 AI Agent 平台（如 Claude Code）。

> **⚠️ 使用建议**：控制使用频率，避免短时间内大量操作。

## 功能概览

| 技能 | 说明 | 核心能力 |
|------|------|----------|
| **ok-search** | 复合搜索 | 一站式搜索（城市切换+分类+关键词+价格筛选） |
| **ok-locale** | 地区管理 | 多国家切换、城市动态获取、分类动态获取 |
| **ok-explore** | 内容发现 | 首页推荐、帖子详情 |
| **ok-auth** | 登录检测 | 登录状态检查 |

## 安装

### 前置条件

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) 包管理器
- Google Chrome 浏览器

### 第一步：安装依赖

```bash
cd ok-core-skill
uv sync
```

### 第二步：安装浏览器扩展

1. 打开 Chrome，地址栏输入 `chrome://extensions/`
2. 右上角开启**开发者模式**
3. 点击**加载已解压的扩展程序**，选择本项目的 `extension/` 目录
4. 确认扩展 **OK Bridge** 已启用

## 使用方式

### 作为 AI Agent 技能使用（推荐）

安装到 skills 目录后，直接用自然语言与 Agent 对话：

> "找夏威夷房源" / "夏威夷50万到200万的房子" / "在新加坡搜索 laptop"

> "列出支持的国家" / "获取新加坡的城市列表"

> "获取这个帖子的详情"

### 作为 CLI 工具使用

```bash
# 启动 Bridge Server
uv run python scripts/bridge_server.py

# 一站式搜索（推荐）— 自动完成城市切换+分类+搜索+价格筛选
uv run python scripts/cli.py full-search --country usa --city hawaii --category property
uv run python scripts/cli.py full-search --country usa --city hawaii --category property --min-price 500000 --max-price 2000000
uv run python scripts/cli.py full-search --country singapore --city singapore --keyword "laptop"

# 列出国家
uv run python scripts/cli.py list-countries

# 获取城市列表（动态 API）
uv run python scripts/cli.py list-cities --country singapore

# 搜索城市（推荐，能找到小城市）
uv run python scripts/cli.py search-cities --country usa --keyword hawaii

# 获取分类树（动态 API）
uv run python scripts/cli.py list-categories --country singapore

# 切换地区
uv run python scripts/cli.py set-locale --country singapore --city singapore

# 获取当前地区
uv run python scripts/cli.py get-locale

# 搜索帖子
uv run python scripts/cli.py search --keyword "laptop" --country singapore --city singapore

# 浏览分类
uv run python scripts/cli.py browse-category --category marketplace --country singapore --city singapore

# 首页推荐
uv run python scripts/cli.py list-feeds --country singapore --city singapore

# 获取帖子详情
uv run python scripts/cli.py get-listing --url "https://sg.ok.com/en/city-singapore/cate-xxx/slug/"

# 检查登录
uv run python scripts/cli.py check-login
```

## CLI 命令参考

| 子命令 | 说明 | 关键参数 |
|--------|------|----------|
| `full-search` | **一站式搜索**（打开→城市切换→分类→搜索→价格筛选→提取结果） | `--country --city [--category] [--keyword] [--min-price] [--max-price] [--max-results]` |
| `list-countries` | 列出支持的国家（固定映射） | — |
| `list-cities` | 动态获取城市列表（API） | `--country [--mode] [--keyword]` |
| `search-cities` | 通过搜索接口匹配城市（推荐，能找到小城市） | `--country --keyword` |
| `list-categories` | 动态获取分类树（API） | `--country` |
| `set-locale` | 切换国家/城市/语言 | `--country --city [--lang]` |
| `get-locale` | 获取当前 locale | — |
| `search` | 搜索帖子 | `--keyword --country --city [--min-price] [--max-price]` |
| `browse-category` | 按分类浏览 | `--category --country --city [--min-price] [--max-price]` |
| `list-feeds` | 首页推荐 | `--country --city [--max-results]` |
| `get-listing` | 获取帖子详情 | `--url` |
| `check-login` | 检查登录状态 | — |

退出码：`0` 成功 · `2` 错误

### 支持的国家

`singapore` `canada` `usa` `uae` `australia` `hong_kong` `japan` `uk` `malaysia` `new_zealand`

> `--country` 只接受以上 10 个值，不可自造（如 ~~united-states~~）。

## 客户端优先级（自动化底层）

CLI 通过 `get_client()` 按顺序选用：**扩展 + Bridge** → **CDP（可选）** → **Playwright 无头**。

- **不装扩展、但已用远程调试启动 Chrome**（例如 `bb-browser` daemon 或其他工具已暴露 CDP）：可设置 `OK_CDP_URL=http://127.0.0.1:9222`（端口以实际为准），再运行 CLI。调试端口仅应本机可信环境使用。
- **调试 CDP 连接**：设置 `OK_CDP_STRICT=1` 时，若 CDP 连接失败则直接报错，不静默降级到 Playwright。

## 项目结构

```
ok-core-skill/
├── extension/                  # Chrome 扩展
│   ├── manifest.json
│   ├── background.js           # WebSocket 通信 + 命令路由
│   └── content.js              # DOM 操作
├── scripts/                    # Python 自动化引擎
│   ├── ok/                     # 核心自动化包
│   │   ├── bridge.py           # 扩展通信客户端
│   │   ├── locale.py           # 多国家/城市管理（API 动态获取）
│   │   ├── selectors.py        # CSS 选择器（集中管理）
│   │   ├── full_search.py      # 一站式搜索流程
│   │   ├── urls.py             # URL 构建器
│   │   ├── types.py            # 数据类型
│   │   ├── errors.py           # 异常体系
│   │   ├── login.py            # 登录检测
│   │   ├── search.py           # 搜索
│   │   ├── listing_detail.py   # 帖子详情
│   │   ├── categories.py       # 分类浏览
│   │   ├── feeds.py            # 首页推荐
│   │   ├── human.py            # 行为模拟
│   │   └── cookies.py          # Cookie 管理
│   ├── cli.py                  # 统一 CLI 入口
│   └── bridge_server.py        # 本地通信服务
├── skills/                     # 技能定义
│   ├── ok-search/SKILL.md
│   ├── ok-locale/SKILL.md
│   ├── ok-explore/SKILL.md
│   └── ok-auth/SKILL.md
├── SKILL.md                    # 技能路由入口
├── CLAUDE.md                   # 开发指南
├── pyproject.toml
└── README.md
```

## 失败处理

- **Bridge Server 未启动**：运行 `uv run python scripts/bridge_server.py`
- **Extension 未连接**：确认 Chrome 已安装并启用 OK Bridge 扩展；或使用 `OK_CDP_URL` 走 CDP
- **操作超时**：检查网络连接，适当增加等待时间
- **API 错误**：检查国家/城市参数是否正确

## License

MIT
