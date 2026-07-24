@echo off
chcp 65001 >nul
echo ========================================
echo   YuiChyanBot 依赖安装脚本
echo ========================================
echo.

:: 检查 uv 是否已安装
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 uv，请先安装 uv：https://docs.astral.sh/uv/getting-started/installation/
    echo.
    pause
    exit /b 1
)

echo [1/2] 正在同步 Python 依赖...
echo.
uv sync
if %errorlevel% neq 0 (
    echo.
    echo [错误] 依赖同步失败，请检查网络连接或 pyproject.toml 配置
    pause
    exit /b 1
)
echo.
echo [1/2] Python 依赖同步完成
echo.

echo [2/2] 正在安装 Playwright Chromium 浏览器...
set "USE_PROXY="
set "PROXY_URL=http://127.0.0.1:1081"
echo 是否使用代理安装 Playwright? (Y/N)
set /p USE_PROXY=

if /i "%USE_PROXY%"=="y" goto install_with_proxy

echo [提示] 未使用代理安装 Playwright
echo.
uv run playwright install chromium
set "PLAYWRIGHT_ERRORLEVEL=%errorlevel%"
goto after_playwright_install

:install_with_proxy
set "INPUT_PROXY_URL="
echo 请输入代理地址
echo 直接回车使用默认值: http://127.0.0.1:1081
set /p INPUT_PROXY_URL=
if not "%INPUT_PROXY_URL%"=="" set "PROXY_URL=%INPUT_PROXY_URL%"
echo [提示] 已启用代理: %PROXY_URL%
echo.
set "HTTPS_PROXY=%PROXY_URL%"
uv run playwright install chromium
set "PLAYWRIGHT_ERRORLEVEL=%errorlevel%"
set "HTTPS_PROXY="

:after_playwright_install
echo.
if not "%PLAYWRIGHT_ERRORLEVEL%"=="0" (
    echo.
    echo [错误] Playwright Chromium 安装失败，请检查网络连接
    pause
    exit /b 1
)
echo.
echo [2/2] Playwright Chromium 安装完成
echo.

echo ========================================
echo   全部依赖安装完成！
echo ========================================
echo.
pause
