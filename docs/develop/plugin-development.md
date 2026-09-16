# 插件开发

本文介绍主项目提供的插件接口，不涉及任何第三方插件的实现。需要会写基本的 Python；只是安装插件的话，看 [插件安装](../guide/plugins.md) 即可。

可以先写一个收到“你好”就回复的功能，确认能运行，再添加其他命令。

## 快速开始

### 插件目录结构

```
yuiChyan/plugins/<插件名>/
├── __init__.py        # 必须，插件入口
├── HELP.md            # 可选，帮助文档
└── ...                # 其他模块文件
```

### 第一个回复

在 `yuiChyan/plugins/my_plugin/__init__.py` 中写入：

```python
from yuiChyan.service import Service

# 创建服务实例
sv = Service('我的插件')

# 注册前缀触发器
@sv.on_prefix('你好')
async def hello(bot, ev):
    await bot.send(ev, '你好呀！')
```

### 注册插件

在 `yuiChyan/config/extra_plugins.json5` 中添加：

```json5
{
    "my_plugin": "我的插件",
}
```

保留配置中原有的插件条目，添加后重启机器人。在已授权、已启用该服务的群里发送“你好”测试。这里的 `Service` 可以理解成一组能一起开关的功能，名字不能与其他服务重复。

## Service 常用写法

### 创建服务

```python
Service(
    name: str,                    # 服务名称（必填，全局唯一）
    manage: Permission = ADMIN,   # 管理启用/禁用所需的权限，默认群管理
    use_exclude: bool = True,     # True=黑名单模式（默认启用），False=白名单模式（默认禁用）
    visible: bool = True,         # 是否在服务列表中可见
    need_auth: bool = True,       # 是否需要群授权才能使用
    help_cmd: str | tuple = None, # 帮助命令，设置后自动注册帮助触发器
    help_at: bool = False,        # 帮助命令是否需要 @BOT 触发
)
```

### 收到什么消息时执行

下面的 `@sv.on_...` 写在函数前面，指定什么消息会调用这个函数。`bot` 用来发送回复，`ev` 包含当前消息、发送人和群等信息。

`on_prefix`、`on_match`、`on_suffix` 和 `on_rex` 只处理群消息。维护组私聊命令使用后面的 `on_command(..., force_private=True)`。

#### on_prefix(prefixes, only_to_me=False)

消息以指定文字开头时执行。函数拿到的 `ev.message` 已去掉这段开头，剩下的就是参数。以下几种写法任选一种，不要把同名命令重复注册。

```python
@sv.on_prefix('查询')
async def query(bot, ev):
    # ev.message 中前缀 "查询" 已被剥离
    keyword = str(ev.message).strip()
    await bot.send(ev, f'你查询的是：{keyword}')

# 多前缀
@sv.on_prefix(('查询', '搜索'))
async def query(bot, ev):
    ...

# 需要 @BOT 触发
@sv.on_prefix('查询', only_to_me=True)
async def query(bot, ev):
    ...
```

#### on_match(matches, only_to_me=False)

完全匹配。消息必须完全等于匹配词，不能带其他字符。

```python
@sv.on_match('签到')
async def sign_in(bot, ev):
    await bot.send(ev, '签到成功！')
```

#### on_suffix(suffixes, only_to_me=False)

消息以指定文字结尾时执行。函数拿到的 `ev.message` 已去掉这段结尾。

```python
@sv.on_suffix('是什么')
async def explain(bot, ev):
    # ev.message 中后缀 "是什么" 已被剥离
    keyword = str(ev.message).strip()
    await bot.send(ev, f'{keyword}的解释是...')
```

#### on_rex(rex, only_to_me=False)

正则匹配。匹配结果存入 `ev['match']`。

```python
import re

@sv.on_rex(r'^(\d+)d(\d+)$')
async def dice(bot, ev):
    match = ev['match']
    times = int(match.group(1))
    faces = int(match.group(2))
    await bot.send(ev, f'掷 {times} 次 {faces} 面骰子')
```

#### on_command(commands, only_to_me=False, force_private=False, cmd_permission=ADMIN)

命令匹配，带权限校验。

```python
from yuiChyan.permission import SUPERUSER

# 群管理命令
@sv.on_command('清空数据')
async def clear_data(bot, ev):
    ...

# 维护组私聊命令
@sv.on_command('重载配置', force_private=True)
async def reload_config(bot, ev):
    ...

# 自定义权限要求
@sv.on_command('管理设置', cmd_permission=SUPERUSER)
async def admin_setting(bot, ev):
    ...
```

参数说明：

- `force_private`：为 True 时仅接受私聊消息，且只有维护组（SUPERUSERS）可触发
- `cmd_permission`：命令所需的最低权限级别，默认 ADMIN（群管理员）

#### on_message(message_type='group')

直接监听消息，不用先匹配命令。当前实现按群号检查服务开关，不会自动检查群授权；这里仅展示群消息用法，需要授权限制时自行检查。

```python
@sv.on_message('group')
async def on_group_msg(bot, ev):
    # 本群启用了服务时执行
    ...
```

### 定时任务

#### scheduled_job(silence=False, custom_id=None, **kwargs)

按指定时间执行函数，时间按项目默认的上海时区计算。`hour=8, minute=0` 表示每天 8 点；更多参数可查 APScheduler 的 CronTrigger 文档。

```python
# 每天 8:00 执行
@sv.scheduled_job(hour=8, minute=0)
async def daily_task():
    await sv.broadcast('早上好！')

# 每 30 分钟执行，静默模式（不打印日志）
@sv.scheduled_job(silence=True, minute='*/30')
async def check_update():
    ...

# 自定义任务 ID
@sv.scheduled_job(custom_id='weekly_report', day_of_week='mon', hour=9)
async def weekly_report():
    ...
```

可用的 kwargs 参数：`year`、`month`、`day`、`week`、`day_of_week`、`hour`、`minute`、`second`。

没有任何已启用且有授权记录的群时，定时任务会跳过；否则调用一次任务函数。同一个服务的定时任务会依次执行。

任务函数自己决定向哪些群发消息。`get_enable_groups()` 只检查功能开关，不检查授权；发送给所有可用群时，优先使用 `sv.broadcast()`。当前定时任务和广播都会检查授权记录，即使 `ENABLE_AUTH=False` 或 `need_auth=False` 也一样。

### 广播

```python
# 向所有启用本服务且已授权的群发送消息
await sv.broadcast('这是一条广播消息')

# 多条消息 + 自定义标签和间隔
await sv.broadcast(
    ('消息1', '消息2'),
    tag='更新通知',
    interval_time=3  # 每条消息间隔 3 秒
)
```

### 其他常用属性和方法

```python
sv.bot                          # 获取 YuiChyan BOT 实例
sv.logger                       # 获取服务专属的 Logger 实例
sv.name                         # 服务名称
await sv.get_enable_groups()    # 获取所有启用本服务的群 ID 列表
sv.judge_enable(group_id)       # 判断某个群是否启用了本服务
sv.enable_service(group_id)     # 对某个群启用服务
sv.disable_service(group_id)    # 对某个群禁用服务
```

## 权限控制

### 权限级别表

| 常量 | 名称 | 数值 | 说明 |
|:-----|:-----|:-----|:-----|
| `BLACK` | 黑名单 | -999 | 匿名用户 |
| `NORMAL` | 群员 | 1 | 普通群成员 |
| `PRIVATE` | 私聊 | 10 | 私聊用户 |
| `ADMIN` | 群管理 | 20 | 群管理员 |
| `OWNER` | 群主 | 21 | 群主 |
| `SUPERUSER` | 维护组 | 999 | base_config 中 SUPERUSERS 列表的 QQ 号 |

### 在插件中使用权限

```python
from yuiChyan.permission import ADMIN, SUPERUSER, check_permission, get_user_permission

# 方式一：通过 on_command 的 cmd_permission 参数（推荐）
@sv.on_command('管理操作', cmd_permission=ADMIN)
async def admin_op(bot, ev):
    ...

# 方式二：手动校验
@sv.on_prefix('敏感操作')
async def sensitive_op(bot, ev):
    if not check_permission(ev, SUPERUSER):
        await bot.send(ev, '权限不足')
        return
    ...

# 方式三：获取用户权限级别
@sv.on_prefix('我的权限')
async def my_perm(bot, ev):
    perm = get_user_permission(ev)
    await bot.send(ev, f'你的权限：{perm.name}')
```

Service 构造函数中的 `manage` 参数控制谁可以启用/禁用该服务（通过 `@BOT启用服务` / `@BOT禁用服务` 命令）。

## 异常处理

Service 会处理下面几种项目自定义错误，并决定回复用户还是只记日志。这不代表所有错误都能自动处理；网络失败、数据格式不对等情况，仍要按需要使用 `try/except`。

### 返回错误提示

下面的 `do_query()` 和 `parse_data()` 是示意函数，需要换成自己的查询和解析代码。

```python
from yuiChyan.exception import (
    FunctionException,
    InterFunctionException,
    CommandErrorException,
    LakePermissionException,
)

@sv.on_prefix('查询')
async def query(bot, ev):
    keyword = str(ev.message).strip()

    # 命令格式错误 - BOT 发送提示给用户
    if not keyword:
        raise CommandErrorException(ev, '请输入查询关键词，例如：查询 xxx')

    # 业务异常 - BOT 发送错误消息给用户
    result = await do_query(keyword)
    if not result:
        raise FunctionException(ev, f'未找到 [{keyword}] 的相关结果')

    # 内部异常 - 仅记录日志，不发送消息
    try:
        data = parse_data(result)
    except Exception:
        raise InterFunctionException(f'解析 [{keyword}] 的数据失败')

    await bot.send(ev, data)
```

### 异常类型对照

| 异常类 | 何时使用 | 行为 |
|:-------|:---------|:-----|
| `FunctionException(ev, msg)` | 需要告知用户的业务错误 | BOT 发送 msg 给用户 |
| `InterFunctionException(msg)` | 内部错误，用户无需知道 | 仅记录日志 |
| `CommandErrorException(ev, msg)` | 用户命令格式不对 | BOT 发送 msg 给用户 |
| `LakePermissionException(ev, msg)` | 权限不足 | BOT 发送 msg 给用户 |

## HELP.md 编写规范

在插件根目录下创建 `HELP.md`，加载插件时会把内容加入帮助网页。需要图片帮助时，再为 Service 设置 `help_cmd`。

### 推荐格式

- 标题使用三级标题 `###`
- 命令列表使用 Markdown 表格
- 表格包含"功能命令"和"介绍"两列

### 示例

```markdown
### 我的插件 / 插件功能说明

| 功能命令 | 介绍 |
|:---------|:-----|
| 你好 | 和 BOT 打招呼 |
| 查询 xxx | 查询某个内容 |
| @BOT帮助 | 查看本插件帮助 |
```

设置 `help_cmd` 后，框架会添加对应的帮助命令，读取创建该 Service 的 Python 文件旁边的 `HELP.md`，生成图片发送。帮助内容会缓存，修改后重启机器人。

## 完整示例插件

下面把查询回复、打招呼、定时消息和帮助放在同一个插件中。示例不会保存签到或查询数据。

### yuiChyan/plugins/example/__init__.py

```python
from yuiChyan.service import Service
from yuiChyan.exception import FunctionException, CommandErrorException

# 创建服务
# help_cmd 设置后，用户发送 "示例帮助" 即可查看 HELP.md 生成的帮助图片
sv = Service(
    '示例插件',
    help_cmd='示例帮助',
)

# 前缀触发
@sv.on_prefix('示例查询')
async def example_query(bot, ev):
    keyword = str(ev.message).strip()
    if not keyword:
        raise CommandErrorException(ev, '请输入查询内容，例如：示例查询 xxx')

    result = f'你查询的是：{keyword}'
    await bot.send(ev, result)

# 完全匹配
@sv.on_match('示例签到')
async def example_sign(bot, ev):
    await bot.send(ev, '签到成功！')

# 定时任务：每天 9:00 执行
@sv.scheduled_job(hour=9, minute=0)
async def daily_greeting():
    await sv.broadcast('早上好！')
```

### yuiChyan/plugins/example/HELP.md

```markdown
### 示例插件 / 示例功能说明

| 功能命令 | 介绍 |
|:---------|:-----|
| 示例查询 xxx | 查询某个内容 |
| 示例签到 | 每日签到 |
| 示例帮助 | 查看本插件帮助 |
```

### 注册到 extra_plugins.json5

```json5
{
    "example": "示例插件",
}
```
