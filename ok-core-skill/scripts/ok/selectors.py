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
CITY_SELECTOR_TRIGGER = "[class*='locationIcon'], [class*='location-icon']"
CITY_MODAL = "[class*='SearchArea'], [class*='searchArea'], [class*='cityModal']"
CITY_SEARCH_INPUT = "[class*='SearchArea'] input, [class*='cityModal'] input"
CITY_LIST_ITEM = "[class*='cityItem'], [class*='city-item']"
CITY_TOP_CITIES = "[class*='topCities'], [class*='popularCities']"
CITY_SEARCH_RESULT_ITEM = "[class*='locationWrapperContent'] div[class*='item'], [class*='SearchArea'] div[class*='item'], [class*='cityItem'], [class*='city-item']"

# ─── 国家/语言选择器 ─────────────────────────────────────────
COUNTRY_SELECTOR_TRIGGER = "[class*='flagIcon'], [class*='flag-icon']"
COUNTRY_CHANGE_BTN = "[class*='changeCountry'], [class*='change-country']"

# ─── 筛选/排序 ─────────────────────────────────────────────
FILTER_SORT = "[class*='sortFilter'], [class*='sort-filter']"
FILTER_PRICE = "[class*='priceFilter'], [class*='price-filter']"
FILTER_LOCATION = "[class*='locationFilter'], [class*='location-filter']"

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
