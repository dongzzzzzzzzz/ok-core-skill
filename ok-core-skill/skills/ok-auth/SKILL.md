---
name: ok-auth
description: |
  OK.com 登录检测技能。检查用户登录状态。
---

# ok-auth — 登录检测

检查 OK.com 的登录状态。

## 命令

```bash
# 检查登录状态
python scripts/cli.py check-login
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
