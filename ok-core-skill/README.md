# OK Skills AG

OK.com 分类信息自动化 Skills，通过 Chrome 扩展 + Python 引擎，让 AI Agent 以真实用户身份操作 OK.com。

支持 [OpenClaw](https://github.com/anthropics/openclaw) 及所有兼容 `SKILL.md` 格式的 AI Agent 平台（如 Claude Code）。

> **⚠️ 使用建议**：控制使用频率，避免短时间内大量操作。

## 功能概览

| 技能 | 说明 | 核心能力 |
|------|------|----------|
| **ok-locale** | 地区管理 | 多国家切换、城市动态获取、分类动态获取 |
| **ok-explore** | 内容发现 | 关键词搜索、分类浏览、帖子详情、首页推荐 |
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

> "列出支持的国家" / "获取新加坡的城市列表"

> "在新加坡搜索 laptop" / "浏览加拿大多伦多的 marketplace"

> "获取这个帖子的详情"

### 作为 CLI 工具使用

```bash
# 启动 Bridge Server
python scripts/bridge_server.py

# 列出国家
python scripts/cli.py list-countries

# 获取城市列表（动态 API）
python scripts/cli.py list-cities --country singapore

# 获取分类树（动态 API）
python scripts/cli.py list-categories --country singapore

# 切换地区
python scripts/cli.py set-locale --country singapore --city singapore

# 搜索帖子
python scripts/cli.py search --keyword "laptop" --country singapore --city singapore

# 浏览分类
python scripts/cli.py browse-category --category marketplace --country singapore --city singapore

# 获取帖子详情
python scripts/cli.py get-listing --url "https://sg.ok.com/en/city-singapore/cate-xxx/slug/"

# 首页推荐
python scripts/cli.py list-feeds --country singapore --city singapore

# 检查登录
python scripts/cli.py check-login
```

## CLI 命令参考

| 子命令 | 说明 |
|--------|------|
| `list-countries` | 列出支持的国家（固定映射） |
| `list-cities` | 动态获取城市列表（API） |
| `list-categories` | 动态获取分类树（API） |
| `set-locale` | 切换国家/城市/语言 |
| `get-locale` | 获取当前 locale |
| `search` | 搜索帖子 |
| `list-feeds` | 首页推荐 |
| `browse-category` | 按分类浏览 |
| `get-listing` | 获取帖子详情 |
| `check-login` | 检查登录状态 |

退出码：`0` 成功 · `2` 错误

## 项目结构

```
ok-skills-ag/
├── extension/                  # Chrome 扩展
│   ├── manifest.json
│   ├── background.js           # WebSocket 通信 + 命令路由
│   └── content.js              # DOM 操作
├── scripts/                    # Python 自动化引擎
│   ├── ok/                     # 核心自动化包
│   │   ├── bridge.py           # 扩展通信客户端
│   │   ├── locale.py           # 多国家/城市管理（API 动态获取）
│   │   ├── selectors.py        # CSS 选择器（集中管理）
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
│   ├── ok-locale/SKILL.md
│   ├── ok-explore/SKILL.md
│   └── ok-auth/SKILL.md
├── SKILL.md                    # 技能路由入口
├── CLAUDE.md                   # 开发指南
├── pyproject.toml
└── README.md
```

## License

MIT
