import asyncio
import os
import sys
from pathlib import Path
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
_browser_lock = asyncio.Lock()
_browser_close_timeout = 1.5


async def _wait_and_ignore(awaitable):
    try:
        await asyncio.wait_for(awaitable, timeout=_browser_close_timeout)
    except Exception:
        pass


async def _start_playwright():
    import subprocess

    if os.name != 'nt':
        return await async_playwright().start()

    original_create_subprocess_exec = asyncio.create_subprocess_exec

    async def detached_create_subprocess_exec(*args, **kwargs):
        startupinfo = kwargs.get('startupinfo') or subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        kwargs['startupinfo'] = startupinfo
        creationflags = kwargs.get('creationflags', 0)
        creationflags |= subprocess.DETACHED_PROCESS
        creationflags |= subprocess.CREATE_NEW_PROCESS_GROUP
        creationflags |= subprocess.CREATE_NO_WINDOW
        kwargs['creationflags'] = creationflags
        return await original_create_subprocess_exec(*args, **kwargs)

    asyncio.create_subprocess_exec = detached_create_subprocess_exec
    try:
        return await async_playwright().start()
    finally:
        asyncio.create_subprocess_exec = original_create_subprocess_exec


def _get_windows_chromium_path() -> Optional[str]:
    if os.name != 'nt':
        return None
    local_app_data = os.environ.get('LOCALAPPDATA')
    if not local_app_data:
        return None
    chromium_root = Path(local_app_data) / 'ms-playwright'
    candidates = sorted(chromium_root.glob('chromium-*'), reverse=True)
    for candidate in candidates:
        chrome_path = candidate / 'chrome-win64' / 'chrome.exe'
        if chrome_path.exists():
            return str(chrome_path)
    return None


# 启动 Playwright 浏览器
async def start_browser():
    global _playwright, _browser
    async with _browser_lock:
        if _playwright and _browser:
            return
        if _playwright is None:
            _playwright = await _start_playwright()
        if _browser is None:
            launch_kwargs = {
                'headless': True,  # 无头模式，无UI渲染
                'args': [
                    "--disable-gpu",  # 禁用GPU加速
                    "--disable-dev-shm-usage",  # 避免/dev/shm分区不足
                    "--disable-extensions",  # 禁用扩展
                    "--disable-background-networking",  # 禁用后台网络活动
                    "--no-sandbox",  # 非沙箱模式(部分环境需要)
                    "--mute-audio",  # 静音
                    "--blink-settings=imagesEnabled=false"  # 禁用图片加载
                ],
                'chromium_sandbox': False
            }
            chromium_path = _get_windows_chromium_path()
            if chromium_path:
                launch_kwargs['executable_path'] = chromium_path
            _browser = await _playwright.chromium.launch(
                **launch_kwargs
            )


# 获取全局浏览器实例
def get_browser() -> Browser:
    if _browser is None:
        raise RuntimeError('Playwright 浏览器实例未启动')
    return _browser


# 关闭 Playwright 浏览器
async def close_browser():
    global _playwright, _browser
    async with _browser_lock:
        browser = _browser
        playwright = _playwright
        _browser = None
        _playwright = None
        if browser:
            await _wait_and_ignore(browser.close())
        if playwright:
            await _wait_and_ignore(playwright.stop())
