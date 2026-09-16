# 代码结构

这篇供准备修改主项目或编写插件的人查阅。只想运行机器人，可以直接看 [安装说明](../guide/installation.md)。

## 从哪里看起

| 文件或目录 | 作用 |
|:-----------|:-----|
| `runYuiChyan.py` | 启动入口 |
| `runFakeBot.py` | 在终端模拟消息，供本地测试 |
| `pyproject.toml`、`uv.lock` | 项目依赖及锁定版本 |
| `yuiChyan/__init__.py` | 创建机器人、加载插件、分发消息 |
| `yuiChyan/service.py` | 定义 Service，用来组织命令、功能开关和定时任务 |
| `yuiChyan/trigger.py` | 根据消息开头、结尾或正则表达式找到处理函数 |
| `yuiChyan/permission.py` | 判断用户权限 |
| `yuiChyan/exception.py` | 定义错误类型 |
| `yuiChyan/config/` | 生成和读取配置 |
| `yuiChyan/resources.py` | 管理数据目录、数据库和生成图片用的浏览器 |
| `yuiChyan/core/` | 自带的 basic、manager、xqa 功能 |
| `yuiChyan/util/` | 图片、翻译、日期等工具 |
| `yuiChyan/http_request.py` | HTTP 请求工具 |
| `yuiChyan/log.py` | 日志设置 |

运行后，个人配置放在 `yuiChyan/config/`，数据放在 `yuiChyan/res/`。第三方插件目录 `yuiChyan/plugins/` 不属于主项目代码，本文不介绍其中的实现。

## 启动过程

`runYuiChyan.py` 调用 `create_instance()` 创建机器人，再启动服务。主要步骤是：

1. 读取配置，不存在的配置文件会用默认内容创建。
2. 创建 `YuiChyan` 实例，设置帮助网页使用的模板和静态文件。
3. 安排启动时开启定时器和浏览器，退出时关闭浏览器和数据库。
4. 按配置加载自带功能和第三方插件，收集各插件根目录下的 `HELP.md`。
5. 注册消息处理函数。

`YuiChyan` 继承自 `nonebot.NoneBot`，通过 `get_bot()` 获取当前实例。它会缓存机器人 QQ 号和群列表，目前只支持一个机器人账号。

## 一条消息怎样被处理

```text
QQ 连接工具（如 LLOneBot）
    ↓ OneBot V11 反向 WebSocket
NoneBot 收到消息
    ↓
按前缀、后缀、正则的顺序查找处理函数
    ↓
检查是否需要 @机器人、群是否有授权、功能是否开启
    ↓
调用对应函数，发送回复或记录错误
```

前缀和后缀会选最长的匹配项。例如同时注册“查询”和“查询天气”，消息以“查询天气”开头时会选择后者。匹配的文字会从 `ev.message` 中去掉，函数可以直接读取剩余参数。

正则匹配使用 `search()`，结果保存在 `ev['match']`，整理后的消息文本在 `ev.normal_text`。同一个匹配条件可以对应多个函数；不要假设一条消息只会触发一个功能。

上面的流程适用于 `on_prefix`、`on_match`、`on_suffix`、`on_rex` 和 `on_command`。`on_message` 是单独的消息监听，不走这套群授权检查。

## Service 是什么

一个 `Service` 表示一组可以一起启用或禁用的功能。一个插件可以创建多个 Service，服务名必须全局唯一。

常用参数：

| 参数 | 作用 |
|:-----|:-----|
| `name` | 服务名，也是群里管理功能时使用的名称 |
| `manage` | 谁可以开关此服务，默认群管理员 |
| `use_exclude` | `True` 表示默认开启，仅关闭指定群；`False` 表示默认关闭，仅开启指定群 |
| `visible` | 是否出现在服务列表中 |
| `need_auth` | 普通消息功能是否要求群授权 |
| `help_cmd` | 查看本服务帮助图片的命令 |
| `help_at` | 帮助命令是否需要 @机器人 |

各群的开关状态会写入 `service.db`，重启后保留。`ServiceFunc` 则记录处理函数、所属服务和是否需要 @机器人，供消息匹配时使用。

具体写法见 [插件开发](plugin-development.md)。

## 权限检查

| 常量 | 对应身份 | 数值 |
|:-----|:---------|:-----|
| `BLACK` | 匿名用户等不接受的身份 | -999 |
| `NORMAL` | 普通群成员 | 1 |
| `PRIVATE` | 私聊用户 | 10 |
| `ADMIN` | 群管理员 | 20 |
| `OWNER` | 群主 | 21 |
| `SUPERUSER` | SUPERUSERS 中的维护组账号 | 999 |

`get_user_permission(ev)` 先检查维护组名单，再判断群内身份或是否为私聊。

`check_permission(ev, require)` 只接受群消息，比较用户权限是否达到要求；私聊会返回 `False`。维护组私聊命令使用 `on_command(..., force_private=True)`。

## 错误提示

需要给用户反馈时，可以抛出 `FunctionException`、`CommandErrorException` 或 `LakePermissionException`，传入事件和提示文字。只需要记日志时，可以用 `InterFunctionException`。

`service.py` 中的 `exception_handler` 处理 `BotException` 及其子类。它不是所有 Python 异常的兜底处理，网络失败等情况仍应按功能需要处理。

## 数据和图片

主项目通过 rocksdict 保存数据，不用另外安装数据库服务：

| 路径（相对 yuiChyan/） | 内容 |
|:-----------------------|:-----|
| `res/db/auth.db` | 群授权 |
| `res/db/service.db` | 功能开关 |
| `res/db/xqa.db` | 你问我答 |
| `res/db/group_gacha.db` | 群抽奖 |
| `res/img/xqa/` | 问答图片 |

这些 `.db` 路径是数据库目录，备份时应先关闭机器人，再复制整个 `res/`，不要只挑其中某个文件。

Playwright 启动一个后台 Chromium 浏览器，用于生成帮助图片。`start_browser()`、`get_browser()` 和 `close_browser()` 分别负责启动、获取和关闭，插件一般直接使用现有的图片生成工具即可。

## 常用工具

| 模块（位于 yuiChyan/util/） | 用途 |
|:---------------------------|:-----|
| `__init__.py` | 撤回、禁言、调用频率和每日次数限制 |
| `chart_generator.py` | 将 Markdown 生成图片 |
| `image_utils.py` | 图片处理 |
| `translator/` | 翻译接口 |
| `date_utils.py` | 日期处理 |
| `parse.py`、`common_code_utils.py` | 链接解析和文字转换 |
| `rss_utils.py` | RSS 处理 |
| `textfilter/` | 文本过滤 |
