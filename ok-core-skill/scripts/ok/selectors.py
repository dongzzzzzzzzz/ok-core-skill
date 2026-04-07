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
DETAIL_SELLER = "[class*='seller'], [class*='Seller'], [class*='user-name']"
DETAIL_LOCATION = "[class*='location'], [class*='Location'], [class*='address']"
DETAIL_IMAGES = "[class*='gallery'] img, [class*='slider'] img, [class*='swiper'] img"
DETAIL_TIME = "[class*='time'], [class*='Time'], [class*='date']"
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

# ─── 登录弹窗流程 ─────────────────────────────────────────
LOGIN_TRIGGER = "#pcUserInfoArea [class*='PcUserInfo_loginButton']"
LOGIN_MODAL = "[class*='LoginPC_loginContainer']"
LOGIN_MODAL_CLOSE = "[class*='TopBar_closeBtn']"
LOGIN_MODAL_BACK = "[class*='TopBar_backBtn']"

# 第一步：邮箱输入
LOGIN_EMAIL_INPUT = ".ok_login_input_label_content_input"
LOGIN_CONTINUE_BTN = "[class*='ValidAccount_loginBtn']"
LOGIN_CLEAR_INPUT = ".ok_login_input_label_suffix_clear"

# 第二步：密码输入
# 已注册用户登录页使用 CustomCounterInput，注册页使用 ok_login_input
LOGIN_PASSWORD_INPUT_LOGIN = "[class*='CustomCounterInput_customInput']"
LOGIN_PASSWORD_INPUT_REGISTER = ".ok_login_input_label_content_input"
LOGIN_SUBMIT_BTN = "[class*='LoginPC_continueButton'], [class*='ValidAccount_loginBtn']"

# 页面标题（区分登录 vs 注册）
LOGIN_TITLE_WELCOME = "[class*='WelcomeTip_welcomeTitle']"
LOGIN_TITLE_REGISTER = "[class*='ValidAccount_title']"

# 忘记密码
LOGIN_FORGOT_PASSWORD = "[class*='LoginPC_forgottenPassword']"

# 第三方登录图标
SOCIAL_LOGIN_GOOGLE = "[class*='SocialLoginIcons'] img[alt='google']"
SOCIAL_LOGIN_FACEBOOK = "[class*='SocialLoginIcons'] img[alt='facebook']"
SOCIAL_LOGIN_APPLE = "[class*='SocialLoginIcons'] img[alt='apple']"

# 登录错误提示
LOGIN_ERROR_MSG = "[class*='errorMsg'], [class*='error-msg'], [class*='ErrorTip']"

# 已登录状态（非 login 按钮，说明已登录）
LOGGED_IN_INDICATOR = "[class*='PcUserInfo_userInfoArea'] [class*='avatar'], [class*='PcUserInfo_userInfoArea'] img[class*='Avatar']"
