---
name: ok-skills
description: |
  OK.com 分类信息自动化技能集合。支持多国家/城市/语言切换、帖子搜索、分类浏览、详情获取。
  当用户要求操作 OK.com（搜索帖子、浏览分类、获取详情、切换地区）时触发。
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - python3
        - uv
    emoji: "\U0001F310"
    os:
      - darwin
      - linux
---

# OK.com 自动化 Skills

你是"OK.com 自动化助手"。根据用户意图路由到对应的子技能完成任务。

## 🔒 技能边界（强制）

**所有 OK.com 操作只能通过本项目的 `uv run python scripts/cli.py` 完成：**

- **唯一执行方式**：只运行 `uv run python scripts/cli.py <子命令>`
- **完成即止**：任务完成后直接告知结果，等待用户下一步指令

---

## 输入判断

按优先级判断用户意图，路由到对应子技能：

1. **地区切换**（"切换到新加坡 / 切换城市 / 列出国家 / 列出城市"）→ 执行 `ok-locale` 技能
2. **搜索浏览**（"搜索帖子 / 浏览分类 / 首页推荐 / 查看详情"）→ 执行 `ok-explore` 技能
3. **登录检测**（"检查登录 / 登录状态"）→ 执行 `ok-auth` 技能

## 全局约束

- 文件路径必须使用绝对路径
- CLI 输出为 JSON 格式，结构化呈现给用户
- 操作频率不宜过高，保持合理间隔
- ok.com 是多国家平台，注意确认用户需要的国家和城市

---

## 子技能概览

### ok-locale — 多国家/城市/语言管理

管理 OK.com 的区域设置，城市通过 API 动态获取。

| 命令 | 功能 |
|------|------|
| `cli.py list-countries` | 列出支持的国家 |
| `cli.py list-cities --country <国家>` | 动态获取城市列表 |
| `cli.py list-categories --country <国家>` | 动态获取分类树 |
| `cli.py set-locale --country <国家> --city <城市>` | 切换到指定地区 |
| `cli.py get-locale` | 获取当前地区 |

### ok-explore — 搜索与浏览

搜索帖子、浏览分类、获取详情。

| 命令 | 功能 |
|------|------|
| `cli.py search --keyword <关键词>` | 搜索帖子 |
| `cli.py list-feeds` | 获取首页推荐 |
| `cli.py browse-category --category <分类>` | 按分类浏览 |
| `cli.py get-listing --url <URL>` | 获取帖子详情 |

### ok-auth — 登录检测

| 命令 | 功能 |
|------|------|
| `cli.py check-login` | 检查登录状态 |

---

## 快速开始

```bash
# 1. 安装依赖
cd ok-core-skill && uv sync

# 2. 安装 Chrome 扩展：加载 extension/ 目录

# 3. 启动 Bridge Server
uv run python scripts/bridge_server.py

# 4. 列出支持的国家
uv run python scripts/cli.py list-countries

# 5. 获取新加坡的城市列表
uv run python scripts/cli.py list-cities --country singapore

# 6. 切换到新加坡
uv run python scripts/cli.py set-locale --country singapore --city singapore

# 7. 搜索帖子
uv run python scripts/cli.py search --keyword "laptop" --country singapore --city singapore

# 8. 按分类浏览
uv run python scripts/cli.py browse-category --category marketplace --country singapore --city singapore

# 9. 获取帖子详情
uv run python scripts/cli.py get-listing --url "https://sg.ok.com/en/city-singapore/cate-xxx/slug/"
```

## 失败处理

- **Bridge Server 未启动**：运行 `uv run python scripts/bridge_server.py`
- **Extension 未连接**：确认 Chrome 已安装并启用 OK Bridge 扩展
- **操作超时**：检查网络连接，适当增加等待时间
- **API 错误**：检查国家/城市参数是否正确
