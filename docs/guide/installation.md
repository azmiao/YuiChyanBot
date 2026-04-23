# 安装部署

## 阶段一：安装 uv

本项目使用 [uv](https://docs.astral.sh/uv/) 管理 Python 环境和依赖。

在 PowerShell 中执行以下命令安装 uv：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

安装完成后，重新打开终端，运行以下命令确认安装成功：

```bash
uv --version
```

## 阶段二：部署 YuiChyanBot

### 1. 克隆仓库

```bash
git clone https://github.com/azmiao/YuiChyanBot.git
cd YuiChyanBot
```

### 2. 安装依赖

双击运行项目根目录下的 `更新依赖.bat`，脚本会自动完成：

- 通过 `uv sync` 同步 Python 依赖（含自动创建虚拟环境和安装 Python 解释器）
- 通过 `playwright install chromium` 安装 Playwright 所需的 Chromium 浏览器

也可以手动执行：

```bash
uv sync
uv run playwright install chromium
```

### 3. 首次启动

双击 `启动YuiChyan.bat` 或手动执行：

```bash
uv run runYuiChyan.py
```

首次启动会在 `yuiChyan/config/` 目录下自动生成以下配置文件：

- `base_config.json5` — 基础配置
- `auth_config.json5` — 授权管理配置
- `xqa_config.json5` — XQA 问答配置
- `core_plugins.json5` — 核心插件注册
- `extra_plugins.json5` — 第三方插件注册

请关闭 BOT，修改配置文件后再重新启动。配置文件详解请参考 [配置文件详解](configuration.md)。

## 阶段三：安装 LLOneBot

### 1. 安装 NTQQ

前往 [QQ 官网](https://im.qq.com/pcqq) 下载并安装最新版 NTQQ 客户端，安装完成后登录你的 QQ 机器人账号。

### 2. 安装 LLOneBot 插件

1. 前往 [LLOneBot Releases](https://github.com/LLOneBot/LLOneBot/releases) 下载最新版本的插件包（`LLOneBot-Plugin-xxx.zip`）
2. 解压后将插件文件夹放入 NTQQ 的插件目录：
   - 默认路径：`%APPDATA%/LiteLoaderQQNT/plugins/`
   - 如果目录不存在，请先安装 [LiteLoaderQQNT](https://github.com/LiteLoaderQQNT/LiteLoaderQQNT)
3. 重启 NTQQ

### 3. 配置 LLOneBot

打开 NTQQ，进入 LLOneBot 设置页面：

1. 启用 **反向 WebSocket 服务**
2. 添加反向 WebSocket 地址：`ws://127.0.0.1:2333/ws/`
   - 端口号 `2333` 需与 `base_config.json5` 中的 `PORT` 一致
3. 如果 `base_config.json5` 中配置了 `ACCESS_TOKEN`，需要在 LLOneBot 中同步配置相同的 Token

## 阶段四：验证连接

1. 确保 NTQQ（LLOneBot）已启动并登录
2. 启动 YuiChyanBot（双击 `启动YuiChyan.bat`）
3. 观察控制台日志，确认出现类似以下信息表示连接成功：

```
> YuiChyanBot实例 启动成功
```

4. 在已授权的群中发送 `查询授权` 测试 BOT 是否正常响应

## 调试模式

项目提供了 FakeBot 用于本地调试，无需连接协议实现客户端：

```bash
uv run runFakeBot.py
```

或双击 `启动FakeBot.bat`。FakeBot 模拟 OneBot 协议客户端，支持在终端中输入消息进行测试：

- 直接输入：模拟群聊消息
- `/` 前缀：模拟私聊消息
- `~` 前缀：模拟戳一戳事件
