---
name: ok-auth
description: |
  OK.com 登录检测技能。检查用户登录状态。
---

# ok-auth — 登录检测

检查 OK.com 的登录状态。

## 执行约束

`<SKILL_DIR>` 是本 SKILL.md 的**上两级目录**（即包含 `pyproject.toml` 的项目根目录）。

## 命令

```bash
# 检查登录状态
uv run --project <SKILL_DIR> ok-cli check-login
```

## 返回值

```json
{
  "logged_in": true,
  "user_name": "用户名"
}
```

## 说明

- OK.com 浏览帖子不需要登录
- 发布帖子、联系卖家等操作需要登录
- 登录需要在浏览器中手动完成
