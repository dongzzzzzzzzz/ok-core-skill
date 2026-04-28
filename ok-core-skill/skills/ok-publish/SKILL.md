---
name: ok-publish
description: |
  OK.com 房产发布技能。发布或填写各国家站 For Sale / For Rent 房产帖子。
  当用户要求发布卖房、出租房、公寓、别墅、townhouse、land 等房产帖子时触发。
---

# ok-publish — 房产发布

发布 OK.com 房产帖子，当前封装 `For Sale` 与 `For Rent` 两条链路。命令会打开真实浏览器页面并填写表单；只有显式传 `--submit` 才会点击 `Post` 正式发布。

## 执行约束

`<SKILL_DIR>` 是本 SKILL.md 的**上两级目录**（即包含 `pyproject.toml` 的项目根目录）。

发布前必须确认目标站点已登录：

```bash
uv run --project <SKILL_DIR> ok-cli check-login --subdomain <子域>
```

目标站点必须显式指定，二选一：

- `--country <国家>`：使用 `singapore` `canada` `usa` `uae` `australia` `hong_kong` `japan` `uk` `malaysia` `new_zealand` 等国家名或 ISO code，CLI 会解析到对应子域。
- `--subdomain <子域>`：直接指定站点子域，如 `sg` `ca` `us` `ae` `au` `hk` `jp` `gb` `my` `nz`。

## 命令

```bash
uv run --project <SKILL_DIR> ok-cli publish-property \
  --country uae \
  --mode sale \
  --property-type apartment \
  --title "Modern 2BR apartment near city center" \
  --description "Bright apartment with balcony, parking, and easy metro access." \
  --price 1200000 \
  --bedrooms 2 \
  --bathrooms 2 \
  --car-spaces 1 \
  --area-size 1200 \
  --location "Dubai Marina" \
  --phone 501234567 \
  --whatsapp 501234567 \
  --image "/absolute/path/photo1.jpg" \
  --submit
```

出租：

```bash
uv run --project <SKILL_DIR> ok-cli publish-property \
  --subdomain ae \
  --mode rent \
  --property-type apartment \
  --rental-type entire \
  --rent-period month \
  --title "Furnished 1BR apartment in Downtown Dubai" \
  --description "Ready to move in, close to metro, pool and gym included." \
  --price 8000 \
  --bedrooms 1 \
  --bathrooms 1 \
  --area-size 850 \
  --location "Downtown Dubai" \
  --phone 501234567 \
  --image "/absolute/path/photo1.jpg" \
  --submit
```

不传 `--submit` 时只填写表单并返回当前页面 URL，方便人工检查。传 `--save-draft` 会点击保存草稿。

## 参数

- `--mode`: `sale` 或 `rent`
- `--country` / `--subdomain`: 目标站点必须显式传一个；两个都传时必须对应同一站点
- `--property-type`: `apartment` `villa` `townhouse` `land` `other`；`land` 仅 For Sale 支持
- `--image`: 图片路径，可重复传入；正式发布通常需要至少一张
- `--floor-plan`: 户型图路径，可重复传入
- `--rent-period`: `day` `week` `month` `quarter` `year`，仅出租
- `--phone` / `--whatsapp`: 页面通常已有当前站点国家码，传本地号码即可；如果传完整国际号码，CLI 会按目标站点剥离常见国家码
- `--unit-feature` / `--amenity` / `--property-service`: 可重复传入页面选项文本

返回 JSON 中 `validation_errors` 非空时，说明页面前端校验未通过，需要补充字段或人工检查。
