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
echo.
uv run playwright install chromium
if %errorlevel% neq 0 (
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
