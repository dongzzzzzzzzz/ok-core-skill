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

**客户端选择**（`scripts/ok/client/factory.py` 的 `get_client()`）

1. **Chrome 扩展 + Bridge**：`BridgeClient` ping 成功时使用。
2. **CDP**：未使用扩展时，若设置环境变量 `OK_CDP_URL`（例如 `http://127.0.0.1:9222`），则通过 Playwright `connect_over_cdp` 连接本机已开启远程调试的 Chrome，复用真实用户会话。连接超时约 3s；失败时降级到 Playwright，除非设置 `OK_CDP_STRICT=1`（此时连接失败会抛错）。
3. **Playwright 无头**：以上皆不可用时兜底（`playwright_client.py`）。

实现见 `scripts/ok/client/cdp_client.py`。需本机存在可访问的 CDP HTTP 端点（可由用户、`bb-browser` daemon 或其他工具代为开启 Chrome 调试端口）。

## 关键设计

1. **Locale 管理**：国家固定映射 + 城市/分类通过 API 动态获取
2. **API 端点**：`https://{subdomain}pub.ok.com/smartProbe/api/`
3. **选择器集中**：所有 CSS 选择器在 `scripts/ok/selectors.py` 统一维护
4. **Bridge 端口**：9334（避免与其他 Bridge 冲突）

## 添加新国家

1. 在 `scripts/ok/locale.py` 的 `COUNTRIES` 字典中添加
2. 需要确认该国家的 `busId`（通过浏览器 Network 面板捕获）
