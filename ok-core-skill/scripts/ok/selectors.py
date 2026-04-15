"""OK.com CSS 选择器集中管理

所有 CSS 选择器在此统一维护，避免散落在各模块中。
ok.com 使用 React SSR，部分 class 带有 hash 后缀，可能随版本更新变化。
"""

# ─── 搜索 ─────────────────────────────────────────────────
SEARCH_INPUT = "#custom-input"
SEARCH_BUTTON = "button[class*='searchButton']"

# ─── 列表页 ─────────────────────────────────────────────────
# 首页推荐卡片
LISTING_CARD_HOME = ".home-recommend-item-card"
# 列表页（搜索/分类）卡片
LISTING_CARD_LIST = "a[class*='item-card-default']"
# 通用：二者之一
LISTING_CARD = f"{LISTING_CARD_HOME}, {LISTING_CARD_LIST}"

# 卡片内部元素
CARD_TITLE = "[class*='itemTitle'], [class*='card-title'], h3"
CARD_PRICE = "[class*='itemPrice'], [class*='card-price'], [class*='price']"
CARD_LOCATION = "[class*='itemLocation'], [class*='card-location'], [class*='location']"
CARD_IMAGE = "img"

# ─── 详情页 ─────────────────────────────────────────────────
DETAIL_TITLE = "h1"
DETAIL_PRICE = "[class*='price'], [class*='Price']"
DETAIL_DESCRIPTION = "[class*='description'], [class*='Description'], [class*='detail-content']"
DETAIL_SELLER = (
    "[class*='agencyUserInfoName'], [class*='AgencyCard'] [class*='Name'], "
    "[class*='seller'], [class*='Seller'], [class*='user-name']"
)
DETAIL_LOCATION = "[class*='location'], [class*='Location'], [class*='address']"
DETAIL_IMAGES = "img[loading='lazy']"
DETAIL_TIME = "[class*='time'], [class*='Time'], [class*='date']"
DETAIL_FEATURE_ITEM = "[class*='MainInfo_item'], [class*='featureItem'], [class*='FeatureItem']"
DETAIL_FEATURE_VALUE = "[class*='value'], [class*='Value']"
DETAIL_CATEGORY = "[class*='Breadcrumb'] a, [class*='breadcrumb'] a"
DETAIL_CONTACT_BTN = "[class*='applyButton'], [class*='contact'], button[class*='message']"

# ─── 导航/头部 ─────────────────────────────────────────────
NAV_BROWSE_MENU = "[class*='browse'], [class*='Browse']"
NAV_CATEGORY_ITEMS = "[class*='dropdownItemLabel'], [class*='categoryItem']"
BREADCRUMB = "[class*='Breadcrumb'] a, [class*='breadcrumb'] a"

# ─── 城市选择器 ─────────────────────────────────────────────
# 筛选栏上的城市 filter（列表页顶部，文本为当前城市名）
# 用 __ 后缀精确匹配容器 div，排除 filterItemIcon/Content/Point 等子元素
CITY_FILTER_ITEM = "[class*='FilterItem_filterItem__']"
# 城市搜索弹出面板（点击城市 filter 后展开）
CITY_SEARCH_OVERLAY = "[class*='FilterItemPC_newLocationOverlay']"
CITY_SEARCH_INPUT = "input[placeholder='Search City']"
CITY_SEARCH_RESULT_ITEM = "[class*='LocationWrapperNew_searchResultItem']"
CITY_SEARCH_RESULT_NAME = "[class*='LocationWrapperNew_resultName']"
CITY_SEARCH_RESULT_ADDR = "[class*='LocationWrapperNew_resultAddress']"

# ─── 国家/语言选择器 ─────────────────────────────────────────
COUNTRY_SELECTOR_TRIGGER = "[class*='flagIcon'], [class*='flag-icon']"
COUNTRY_CHANGE_BTN = "[class*='changeCountry'], [class*='change-country']"

# ─── 首页分类图标 ─────────────────────────────────────────────
HOMEPAGE_CATEGORY_LINK = "a[href*='/cate-']"
HOMEPAGE_CATEGORY_ICON = "a[href*='/cate-'], [class*='categoryIcon'], [class*='category-icon']"

# ─── 筛选/排序 ─────────────────────────────────────────────
FILTER_SORT = "[class*='sortFilter'], [class*='sort-filter']"
# 筛选条上的 FilterItem 按钮（文本匹配 "Price"）
FILTER_ITEM = "[class*='FilterItem_filterItem__']"
# Price 面板（点击 Price 按钮后展开的浮层）
FILTER_PRICE_OVERLAY = "[class*='FilterItemPC_filterItemOverlay']"
# 价格输入框
FILTER_PRICE_MIN = "input.native-numeric-input[placeholder='Min']"
FILTER_PRICE_MAX = "input.native-numeric-input[placeholder='Max']"
# 筛选浮层底部的 Confirm/Clear 按钮
FILTER_CONFIRM_BTN = "button[type='submit'][class*='FilterItemPC_button']"
FILTER_CLEAR_BTN = "button[type='reset'][class*='FilterItemPC_button']"

# ─── 分页/加载更多 ─────────────────────────────────────────
LOAD_MORE_BTN = "[class*='loadMore'], [class*='load-more'], button[class*='more']"
PAGINATION = "[class*='pagination'], [class*='Pagination']"

# ─── Cookie 横幅 ─────────────────────────────────────────
COOKIE_BANNER = "[class*='cookie'], [class*='Cookie']"
COOKIE_ACCEPT_BTN = "[class*='cookie'] button, [class*='Cookie'] button"

# ─── 登录相关 ─────────────────────────────────────────────
LOGIN_BTN = "[class*='login'], [class*='Login'], [class*='signIn']"
USER_AVATAR = "[class*='avatar'], [class*='Avatar'], [class*='userIcon']"
USER_NAME = "[class*='userName'], [class*='user-name']"
