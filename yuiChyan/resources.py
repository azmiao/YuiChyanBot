import os
import sys
from typing import Optional

from matplotlib import font_manager
from playwright.async_api import async_playwright, Browser, Playwright
from rocksdict import Rdict

# 是否是打包文件
is_packaged: bool = not sys.argv[0].endswith('.py')

# 基础文件路径
if is_packaged:
    current_dir = sys.path[0]
else:
    current_dir = os.path.dirname(__file__)
# 代码路径
code_dir = os.path.dirname(__file__)

# 基础资源路径
base_res_path = os.path.join(current_dir, 'res')
os.makedirs(base_res_path, exist_ok=True)
# 本项目使用高性能并发数据库 rocksdict 底层为 rocksdb | YuiChyanBot 结束时会自动触发 db.close()
base_db_path = os.path.join(base_res_path, 'db')
os.makedirs(base_db_path, exist_ok=True)
# 基础图片路径
base_img_path = os.path.join(base_res_path, 'img')
os.makedirs(base_img_path, exist_ok=True)
# XQA资源路径
xqa_img_path = os.path.join(base_img_path, 'xqa')
os.makedirs(xqa_img_path, exist_ok=True)


# 授权管理数据库
auth_db_ = Rdict(os.path.join(base_db_path, 'auth.db'))
# 服务管理数据库
service_db_ = Rdict(os.path.join(base_db_path, 'service.db'))
# XQA数据库
xqa_db_ = Rdict(os.path.join(base_db_path, 'xqa.db'))
# 抽奖数据库
group_gacha_db_ = Rdict(os.path.join(base_db_path, 'group_gacha.db'))

# 全局本地字体
font_path = os.path.join(code_dir, 'core', 'manager', 'help_res', 'static', 'fonts', 'HarmonyOS_SansSC_Regular.ttf')
font_prop = font_manager.FontProperties(fname=font_path)

# 全局CSS
base_css_path = os.path.join(code_dir, 'core', 'manager', 'help_res', 'static', 'css', 'bootstrap.min.css')
md_css_path = os.path.join(code_dir, 'core', 'manager', 'help_res', 'static', 'css', 'github-markdown.css')

# 全局JS
base_js_path = os.path.join(code_dir, 'core', 'manager', 'help_res', 'static', 'js', 'bootstrap.bundle.min.js')
jq_js_path = os.path.join(code_dir, 'core', 'manager', 'help_res', 'static', 'js', 'jquery.min.js')


# 关闭所有数据库实例
def close_all_db():
    for db in (auth_db_, service_db_, xqa_db_, group_gacha_db_):
        try:
            db.close()
        except Exception:
            pass


# Playwright 浏览器实例
_playwright: Optional[Playwright] = None
_browser: Optional[Browser] = None


# 启动 Playwright 浏览器
async def start_browser():
    global _playwright, _browser
    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(headless=True)


# 获取全局浏览器实例
def get_browser() -> Browser:
    if _browser is None:
        raise RuntimeError('Playwright 浏览器实例未启动')
    return _browser


# 关闭 Playwright 浏览器
async def close_browser():
    global _playwright, _browser
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None
