# 安装说明

绿色包和源码安装选一种即可。装好后，都需要修改配置并连接 QQ。

## 方式一：绿色包

1. 到项目的 [GitHub Actions](https://github.com/azmiao/YuiChyanBot/actions/workflows/build.yml)，在成功的构建记录中下载 `YuiChyanBot-Portable` 产物（需要登录 GitHub，且产物尚未过期）。
2. 解压后，双击 `启动YuiChyan.bat`。
3. 等待首次初始化完成，再关闭机器人，按下面的说明修改配置。

绿色包自带 Python 和 Python 依赖，首次启动仍需联网下载 Chromium 浏览器，用于生成帮助图片。后续启动通常不需要重复安装。

## 方式二：源码安装

### 1. 安装 uv 和 Git

[uv](https://docs.astral.sh/uv/getting-started/installation/) 用来准备 Python 环境和安装依赖。在 PowerShell 中运行：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

安装后重新打开 PowerShell，运行 `uv --version`，能看到版本号即可。

下载代码还需要 [Git](https://git-scm.com/downloads/win)。下面的命令都在项目文件夹中运行。

### 2. 下载代码和依赖

```powershell
git clone https://github.com/azmiao/YuiChyanBot.git
cd YuiChyanBot
uv sync
uv run playwright install chromium
```

`uv sync` 会准备 Python 环境并安装依赖，最后一条命令安装生成帮助图片用的浏览器。

也可以在下载代码后双击 `更新依赖.bat`。脚本会询问下载浏览器时是否使用代理，没有代理就选 `N`。

### 3. 首次启动

双击 `启动YuiChyan.bat`，或运行：

```powershell
uv run runYuiChyan.py
```

首次启动会生成配置文件。先关闭机器人，再继续下面的设置。

## 修改配置

打开 `yuiChyan/config/base_config.json5`，至少检查这些设置：

- `SUPERUSERS`：改成你自己的 QQ 号，这是管理机器人的账号，不是机器人账号。
- `MANAGER_PASSWORD`：改成自己的后台密码，不要保留默认值。
- `HOST`：机器人和 QQ 在同一台电脑、只需本机访问时，建议设为 `"127.0.0.1"`。
- `PORT`：默认 `2333`，连接工具中的端口要与它一致。
- `ACCESS_TOKEN`：设置连接验证用的密钥，并在连接工具中填写相同的值，不要公开。

默认开启群授权。连接成功后，可以用管理员账号私聊机器人，发送 `变更授权 群号+30`，给指定群增加 30 天授权。更多设置见 [配置说明](configuration.md)。

## 连接 QQ

本项目不会直接登录 QQ，需要配合连接工具使用：

- [LLOneBot](https://github.com/LLOneBot/LLOneBot)
- [NapCat](https://github.com/NapNeko/NapCatQQ)

按照所选工具的官方说明安装并登录机器人账号，再在其设置中添加 **OneBot V11 反向 WebSocket** 连接。同一台电脑上的默认地址为：

```text
ws://127.0.0.1:2333/ws/
```

端口要与 `PORT` 一致。如果设置了 `ACCESS_TOKEN`，两边也要一致。以上地址仅适用于同机连接；不要为了连接方便直接把后台暴露到公网。

## 确认可以使用

1. 启动 QQ 连接工具，确认账号已登录。
2. 启动 YuiChyanBot，检查连接工具是否显示已连上 WebSocket。
3. 保持默认群授权开关时，在机器人所在群发送 `查询授权`。未授权的群也能查询；收到回复即可确认消息能正常往返。
4. 启动后，在同一台电脑打开 `http://127.0.0.1:2333/help`，可以查看帮助网页。修改过端口时，地址也要跟着改。

日志里的“YuiChyanBot实例 启动成功”只表示程序创建了机器人实例，不代表已经连上 QQ。

没有回复时，先检查两边的连接地址和密钥，再检查群授权、功能是否启用，以及命令是否需要 @机器人。

## 本地测试（可选）

源码中提供了 FakeBot，可以在终端里模拟消息，不用登录 QQ。它不会代替机器人主程序，需要先启动 YuiChyanBot，再打开另一个终端运行：

```powershell
uv run runFakeBot.py
```

也可以双击 `启动FakeBot.bat`。测试前检查 `runFakeBot.py` 顶部的连接地址、连接密钥和测试账号设置，确保与机器人配置一致。

- 直接输入文字：模拟群消息。
- 以 `/` 开头：模拟私聊。
- 以 `~` 开头：模拟戳一戳。

测试群同样受群授权和功能开关影响。FakeBot 只适合简单调试，不能代替真实 QQ 环境的测试。
