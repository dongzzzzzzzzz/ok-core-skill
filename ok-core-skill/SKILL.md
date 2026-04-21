---
name: ok-skills
description: |
  OK.com 分类信息自动化技能集合。支持多国家/城市/语言切换、帖子搜索、分类浏览、详情获取、收藏管理、我的帖子管理。
  当用户要求操作 OK.com（搜索帖子、浏览分类、获取详情、切换地区、管理收藏、管理帖子）时触发。
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

## 执行约束（强制）

**项目根目录**就是本 SKILL.md 所在的目录。读取到本文件后，将其父目录记为 `SKILL_DIR`。

**唯一执行方式**（从任意工作目录均可运行）：

```bash
uv run --project <SKILL_DIR> ok-cli <子命令> [参数]
```

- 第一次运行前，先执行一次 `uv sync --project <SKILL_DIR>` 安装依赖
- 完成即止：任务完成后直接告知结果，等待用户下一步指令

## 运行模式（Bridge / Playwright）

本技能支持两种运行模式：

1. **Bridge 模式（推荐）**：连接本地 Chrome 扩展 `OK Bridge`，在用户真实浏览器里执行。
2. **Playwright 模式（免扩展）**：未检测到 Bridge 时自动降级到 Playwright 静默浏览器。

首次使用 Playwright 前需要安装浏览器：

```bash
uv run playwright install chromium
```

如果看到报错包含 `Executable doesn't exist` 或 `playwright install`，说明浏览器未安装。

---

## 输入判断

按优先级判断用户意图，路由到对应处理：

0. **搜索/浏览**（"找夏威夷房源 / 搜索东京的工作 / 温哥华二手车 / 夏威夷50万以下的房子"）→ **先读取 `skills/ok-search/SKILL.md`**，按其中步骤执行（禁止跳过）
1. **地区切换**（"切换到新加坡 / 切换城市 / 列出国家 / 列出城市"）→ 执行 `ok-locale` 技能
2. **推荐/详情**（"首页推荐 / 查看帖子详情"）→ 执行 `ok-explore` 技能
3. **登录检测**（"检查登录 / 登录状态"）→ 执行 `ok-auth` 技能
4. **收藏管理**（"查看收藏 / 收藏帖子 / 取消收藏"）→ **先读取 `skills/ok-account/SKILL.md`**，按其步骤执行（需登录）
5. **我的帖子**（"查看我的帖子 / 删除帖子 / 编辑帖子"）→ **先读取 `skills/ok-account/SKILL.md`**，按其步骤执行（需登录）

---

## 全局约束

- CLI 输出为 JSON 格式，结构化呈现给用户
- 操作频率不宜过高，保持合理间隔
- ok.com 是多国家平台，注意确认用户需要的国家和城市
- **`--country` 只接受以下 10 个固定值**：`singapore` `canada` `usa` `uae` `australia` `hong_kong` `japan` `uk` `malaysia` `new_zealand`
- **`--country` 和 `--city` 在 search / browse-category / list-feeds 中默认值为 singapore，搜索其他地区时必须显式传入**

---

## 子技能概览

### ok-search — 搜索与浏览

所有搜索/浏览请求，**必须先读取 `skills/ok-search/SKILL.md`**，按其步骤解析意图、查询城市、执行搜索。

### ok-locale — 多国家/城市/语言管理

```bash
uv run --project <SKILL_DIR> ok-cli list-countries
uv run --project <SKILL_DIR> ok-cli list-cities --country <国家> --mode search --keyword <城市关键词>
uv run --project <SKILL_DIR> ok-cli list-categories --country <国家>
uv run --project <SKILL_DIR> ok-cli set-locale --country <国家> --city <城市>
uv run --project <SKILL_DIR> ok-cli get-locale
```

### ok-explore — 首页推荐与帖子详情

```bash
uv run --project <SKILL_DIR> ok-cli list-feeds --country <国家> --city <城市>
uv run --project <SKILL_DIR> ok-cli get-listing --url <URL>
```

### ok-auth — 登录检测

```bash
uv run --project <SKILL_DIR> ok-cli check-login
```

### ok-account — 收藏与我的帖子（需登录）

所有收藏/帖子操作，**必须先读取 `skills/ok-account/SKILL.md`**，按其步骤检查登录、执行命令。
