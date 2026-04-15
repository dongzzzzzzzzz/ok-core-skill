# OK Skills AG 开发指南

## 技术栈

- Python >= 3.11 + uv
- Chrome Extension Manifest V3
- WebSocket (bridge 通信)

## 开发命令

```bash
uv sync                    # 安装依赖
uv run ruff check .        # Lint 检查
uv run ruff format .       # 代码格式化
uv run pytest              # 运行测试
```

## 架构

**扩展路径（默认推荐）**

```
AI Agent / CLI
    ↓ (WebSocket)
Bridge Server (port 9334)
    ↓ (WebSocket)
Chrome Extension (OK Bridge)
    ↓ (DOM 操作)
ok.com 网页
```

**客户端四级检测**（`scripts/ok/client/factory.py` 的 `get_client()`，零配置）

1. **Bridge**：Chrome 扩展 + bridge_server.py 均在线时使用（最佳体验）。
2. **CDP 探测**：探测 `127.0.0.1:9222/9223/9224` 是否有已开调试端口的 Chrome。也可通过环境变量 `OK_CDP_URL` 强制指定。
3. **CDP 自启动**：本地找不到调试端口时，自动启动一个 headed Chrome 实例（`--remote-debugging-port`），使用持久化 profile `~/.ok-agent/chrome-profile/`，首次登录后后续自动复用会话。设置 `OK_NO_AUTO_LAUNCH=1` 或 `OK_HEADLESS=1` 可跳过此步。
4. **Playwright 无头**：以上皆不可用时兜底，使用 `launch_persistent_context`（profile 在 `~/.ok-agent/pw-profile/`），cookies/localStorage 自动跨 session 保留。

| 环境变量 | 作用 | 默认 |
|---|---|---|
| `OK_CDP_URL` | 强制指定 CDP 地址，跳过探测 | 空 |
| `OK_CDP_STRICT` | CDP 失败时报错而非降级 | `0` |
| `OK_NO_AUTO_LAUNCH` | 禁止自启动 Chrome | `0` |
| `OK_HEADLESS` | 强制无头模式（跳过 Level 3） | `0` |

## 关键设计

1. **Locale 管理**：国家固定映射 + 城市/分类通过 API 动态获取
2. **API 端点**：`https://{subdomain}pub.ok.com/smartProbe/api/`
3. **选择器集中**：所有 CSS 选择器在 `scripts/ok/selectors.py` 统一维护
4. **Bridge 端口**：9334（避免与其他 Bridge 冲突）

## 添加新国家

1. 在 `scripts/ok/locale.py` 的 `COUNTRIES` 字典中添加
2. 需要确认该国家的 `busId`（通过浏览器 Network 面板捕获）
