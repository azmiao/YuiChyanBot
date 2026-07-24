@echo off
chcp 65001 >nul
setlocal
set "ROOT=%~dp0"
set "PORTABLE_PYTHON=%ROOT%python\python.exe"
set "VENV_DIR=%ROOT%.venv-portable"
set "VENV_PYTHON=%ROOT%.venv-portable\Scripts\python.exe"
set "WHEELS_DIR=%ROOT%wheels"
set "REQUIREMENTS_FILE=%ROOT%requirements-portable.txt"
set "BUILD_ID=%ROOT%portable-build-id.txt"
set "VENV_BUILD_ID=%ROOT%.venv-portable\.build-id"
set "NEED_REBUILD=0"

if not exist "%PORTABLE_PYTHON%" goto source_mode
if not exist "%VENV_PYTHON%" goto prepare_env
if not exist "%BUILD_ID%" goto start_bot
if not exist "%VENV_BUILD_ID%" set "NEED_REBUILD=1"
if not exist "%VENV_BUILD_ID%" goto prepare_env
fc /b "%BUILD_ID%" "%VENV_BUILD_ID%" >nul 2>nul
if errorlevel 1 set "NEED_REBUILD=1"
if "%NEED_REBUILD%"=="1" goto prepare_env
goto start_bot

:source_mode
uv run "%ROOT%runYuiChyan.py"
goto end

:prepare_env
echo ========================================
echo   YuiChyanBot 便携环境初始化
echo ========================================
echo.

if not exist "%WHEELS_DIR%" (
    echo [错误] 未找到离线依赖目录：%WHEELS_DIR%
    goto end
)

if not exist "%REQUIREMENTS_FILE%" (
    echo [错误] 未找到依赖清单：%REQUIREMENTS_FILE%
    goto end
)

if "%NEED_REBUILD%"=="1" (
    echo [提示] 检测到绿色包版本变化，正在重建本地运行环境...
    echo.
    if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%"
)

echo [1/3] 正在创建本地虚拟环境...
echo.
if not exist "%VENV_PYTHON%" (
    "%PORTABLE_PYTHON%" -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo.
        echo [错误] 虚拟环境创建失败
        goto end
    )
)

echo [2/3] 正在离线安装 Python 依赖...
echo.
"%VENV_PYTHON%" -m pip install --no-index --find-links="%WHEELS_DIR%" -r "%REQUIREMENTS_FILE%"
if errorlevel 1 (
    echo.
    echo [错误] 离线依赖安装失败
    goto end
)

echo [3/3] 正在联网安装 Playwright Chromium...
echo.
"%VENV_PYTHON%" -m playwright install chromium
if errorlevel 1 (
    echo.
    echo [错误] Playwright Chromium 安装失败，请检查网络连接后重试
    goto end
)

if exist "%BUILD_ID%" copy /y "%BUILD_ID%" "%VENV_BUILD_ID%" >nul

echo.
echo ========================================
echo   便携环境初始化完成！
echo ========================================
echo.

:start_bot
"%VENV_PYTHON%" "%ROOT%runYuiChyan.py"

:end
pause
