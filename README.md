<p align="center">
  <a href="https://github.com/azmiao/YuiChyanBot">
    <img src="https://raw.githubusercontent.com/azmiao/YuiChyanBot/main/yuiChyan.jpg" width="200" height="200" alt="YuiChyanBot">
  </a>
</p>

# ✦ YuiChyanBot 优衣酱 ✦

- 上方图片偷自 PID: 82685587
- 一个自用的机器人框架，部分架构设计思想参考自咖啡的[HoshinoBot](https://github.com/Ice9Coffee/HoshinoBot)
- 2025-07-24 正式转为开源项目，不过目前文档不完整，后续陆续补充（~~有空再搞~~）

## 所需环境

- 系统: 仅限 64位 Win10+ 系统
- python: 推荐直接最新版本，最低建议`3.13.1`
- 协议实现: LLOneBot

## 框架局限性

1. 仅支持单BOT实例，不支持同时使用多个BOT账户
2. 虽然已做了很多兼容处理，但仍不保证所有协议实现客户端的接口兼容性，LLOneBot测试稳定可用
3. BOT框架本意为纯自用，不保证更新和问题修复

## 支持的核心功能

1. BOT业务实现、服务管理和控制
2. 网页端的服务管理
3. 网页版的帮助菜单
4. 自带授权管理系统

## 自带的基础功能

1. 群内服务管理/网页端服务管理
2. 根据`HELP.md`自动生成的帮助菜单/帮助网页
3. 独立的授权管理系统
4. XQA支持正则回流的高级你问我答
5. 基础自带功能：文本翻译、文字识别、漫画翻译、选择困难症、群抽奖、掷骰子、猜拼音是啥、解析二维码 （部分功能不稳定，经常炸了是正常的）

## 如何使用

### 1. 安装 uv

本项目使用 [uv](https://docs.astral.sh/uv/) 管理 Python 环境和依赖，请先安装 uv：

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

安装完成后，重新打开终端，运行 `uv --version` 确认安装成功。

### 2. 安装依赖

双击运行项目根目录下的 `更新依赖.bat`，脚本会自动完成以下操作：

- 通过 `uv sync` 同步 Python 依赖（含自动创建虚拟环境和安装 Python 解释器）
- 通过 `playwright install chromium` 安装 Playwright 所需的 Chromium 浏览器

或者也可以手动在项目根目录执行：

```bash
uv sync
uv run playwright install chromium
```

### 3. 启动 BOT

双击 `启动YuiChyan.bat` 或者手动执行：

```bash
uv run runYuiChyan.py
```

首次启动会在 config 目录下生成配置文件，并仅启用核心插件，请修改各项配置后重启 BOT 即可使用。

## 插件

目前仅有自用插件：https://github.com/stars/azmiao/lists/yuichyanbot-plugins

## 其他说明后续慢慢更新
