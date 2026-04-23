# 框架架构解析

## 项目目录结构

### 顶层文件

| 文件/目录 | 职责 |
|:----------|:-----|
| `runYuiChyan.py` | BOT 主入口，调用 `create_instance()` 创建实例并启动 |
| `runFakeBot.py` | 调试用 FakeBot，模拟 OneBot 协议客户端 |
| `pyproject.toml` | 项目依赖和元数据（uv 管理） |
| `启动YuiChyan.bat` | 启动 BOT 的快捷脚本 |
| `启动FakeBot.bat` | 启动 FakeBot 的快捷脚本 |
| `更新依赖.bat` | 同步依赖 + 安装 Playwright Chromium |

### yuiChyan/ 模块

| 模块 | 职责 |
|:-----|:-----|
| `__init__.py` | 框架主模块，`YuiChyan` 类定义、`create_instance()` 工厂函数、插件加载、消息处理 |
| `service.py` | `Service` 类和 `ServiceFunc` 类，插件的核心抽象 |
| `trigger.py` | 触发器系统：前缀/后缀/正则三种触发器和触发链 |
| `permission.py` | 权限系统：5 个权限级别和权限校验 |
| `exception.py` | 异常体系：业务异常、内部异常、命令错误、权限不足等 |
| `resources.py` | 全局资源管理：RocksDB 数据库、Playwright 浏览器、路径定义 |
| `log.py` | 日志模块 |
| `http_request.py` | 基于 httpx 的 HTTP 会话管理 |
| `config/` | 配置模块：读取 json5 配置文件并导出为模块级变量 |
| `core/` | 核心插件目录 |
| `plugins/` | 第三方插件目录 |
| `util/` | 工具模块：撤回、禁言、频次限制器、图片处理、翻译等 |
| `res/` | 资源目录：数据库文件和图片 |

## 核心类与模块

### YuiChyan 类

定义在 `yuiChyan/__init__.py`，继承自 `nonebot.NoneBot`，是全局唯一的 BOT 实例。

通过 `create_instance()` 工厂函数创建，初始化流程：

```
配置加载（importlib.import_module）
    ↓
实例创建（YuiChyan(config)）
    ↓
Quart Web App 配置（静态资源/Jinja2模板/密钥）
    ↓
生命周期钩子注册
  ├── before_serving: APScheduler 定时器启动
  ├── before_serving: Playwright 浏览器启动
  └── after_serving: 资源释放（浏览器关闭 + 数据库关闭）
    ↓
核心插件加载（_load_core_plugins）
    ↓
第三方插件加载（_load_external_plugins）
    ↓
消息预处理器注册（_process_message）
```

实例缓存了 `cached_self_id`（BOT QQ号）和 `cached_group_list`（群列表），通过异步锁保证并发安全。

### Service 类

定义在 `yuiChyan/service.py`，是插件的核心抽象。每个插件通过实例化 Service 注册服务。

构造参数：

- `name` — 服务名称（全局唯一）
- `manage` — 管理启用/禁用所需的权限，默认 ADMIN
- `use_exclude` — True 为黑名单模式（默认启用），False 为白名单模式（默认禁用）
- `visible` — 是否在服务列表中可见
- `need_auth` — 是否需要群授权
- `help_cmd` — 帮助命令，设置后自动注册帮助触发器
- `help_at` — 帮助命令是否需要 @BOT 触发

服务配置（启用/禁用的群列表）持久化到 RocksDB（service.db）。

### ServiceFunc 类

包装了服务函数 + 所属 Service + 是否需要 @BOT，是触发器系统中存储和匹配的基本单元。

## 消息处理流程

```
OneBot 协议端（LLOneBot）
    ↓ 反向 WebSocket
nonebot 消息预处理器
    ↓
trigger_chain 遍历（优先级：前缀 > 后缀 > 正则）
    ↓ 匹配到 ServiceFunc
校验链：@触发检查 → @对象检查 → 授权检查 → 服务启用检查
    ↓ 全部通过
调用处理函数 service_func.func(bot, event)
    ↓ 异常
exception_handler 统一拦截处理
```

校验链详细逻辑：

1. **@触发检查**：如果 `service_func.only_to_me` 为 True，消息必须 @BOT
2. **@对象检查**：如果消息第一个段是 @某人，且 @的不是 BOT 自己，则跳过
3. **授权检查**：如果开启了授权系统（`ENABLE_AUTH`）且服务需要授权（`need_auth`），检查群是否在授权数据库中
4. **服务启用检查**：根据黑/白名单模式判断该群是否启用了此服务

## 触发器系统

定义在 `yuiChyan/trigger.py`，三种触发器按优先级组成触发链。

### PrefixTrigger（前缀匹配）

基于 `pygtrie.CharTrie` 实现最长前缀匹配。消息文本先通过 zhconv 转为简体中文，再在 Trie 树中查找最长匹配前缀从消息中剥离，剥离后的文本可通过 `ev.message` 获取。匹配的前缀存入 `ev['prefix']`。

### SuffixTrigger（后缀匹配）

将后缀字符串反转后同样用 CharTrie 实现。匹配后将后缀从消息尾部剥离。匹配的后缀存入 `ev['suffix']`。

### RegularTrigger（正则匹配）

遍历所有注册的正则表达式，对消息文本（经过 URL 转码处理）执行 `search`。匹配结果存入 `ev['match']`，消息的规范化文本存入 `ev.normal_text`。

### 触发链优先级

```python
trigger_chain = [prefix, suffix, regular]
```

前缀匹配优先级最高，正则匹配最低。同一触发器内，按注册顺序匹配。

## 权限系统

定义在 `yuiChyan/permission.py`。

| 权限级别 | 名称 | 数值 |
|:---------|:-----|:-----|
| BLACK | 黑名单 | -999 |
| NORMAL | 群员 | 1 |
| PRIVATE | 私聊 | 10 |
| ADMIN | 群管理 | 20 |
| OWNER | 群主 | 21 |
| SUPERUSER | 维护组 | 999 |

权限判定逻辑（`get_user_permission`）：

1. 如果用户 QQ 号在 `SUPERUSERS` 列表中 → SUPERUSER
2. 群消息：匿名用户 → BLACK，群主 → OWNER，管理员 → ADMIN，其他 → NORMAL
3. 私聊消息 → PRIVATE
4. 其他 → BLACK

`check_permission(ev, require)` 仅对群聊做判断，比较用户权限是否 >= 要求权限。

## 异常体系

定义在 `yuiChyan/exception.py`。

| 异常类 | 用途 | 行为 |
|:-------|:-----|:-----|
| `BotException` | 基类 | 携带事件和消息 |
| `FunctionException` | 业务异常 | BOT 发送错误消息给用户 |
| `InterFunctionException` | 内部异常 | 仅记录日志，不发送消息 |
| `CommandErrorException` | 命令格式错误 | BOT 发送错误提示给用户 |
| `LakePermissionException` | 权限不足 | BOT 发送权限不足提示 |
| `SessionNotFoundException` | Session 未找到 | 仅记录日志 |
| `SessionExistException` | 同名 Session 已存在 | 仅记录日志 |
| `SubFuncDisabledException` | 子功能被禁用 | 仅记录日志 |

通过 `exception_handler` 装饰器统一拦截：如果异常携带事件和消息，通过 BOT 发送给用户；否则记录日志。所有通过 Service 装饰器注册的函数都会被自动包装。

## 资源管理

定义在 `yuiChyan/resources.py`。

### RocksDB 数据库

| 实例 | 数据库文件 | 用途 |
|:-----|:-----------|:-----|
| `auth_db_` | `res/db/auth.db` | 授权管理 |
| `service_db_` | `res/db/service.db` | 服务配置持久化 |
| `xqa_db_` | `res/db/xqa.db` | XQA 问答数据 |
| `group_gacha_db_` | `res/db/group_gacha.db` | 群抽奖数据 |

BOT 关闭时通过 `close_all_db()` 释放所有数据库连接。

### Playwright 浏览器

全局 Chromium 浏览器实例，用于将 Markdown 渲染为图片（帮助菜单等场景）。通过 `start_browser()` / `get_browser()` / `close_browser()` 管理生命周期，在 Quart App 的 `before_serving` / `after_serving` 钩子中自动启动和关闭。

## 工具模块

位于 `yuiChyan/util/`。

| 模块 | 职责 |
|:-----|:-----|
| `__init__.py` | 撤回消息（`delete_msg`）、禁言（`silence`）、`FreqLimiter`（频次限制器）、`DailyNumberLimiter`（每日限制器） |
| `chart_generator.py` | Markdown 转图片生成器（基于 Playwright） |
| `common_code_utils.py` | 通用编码工具（URL 转码字符处理等） |
| `date_utils.py` | 日期工具 |
| `image_utils.py` | 图片处理工具 |
| `parse.py` | URL 解析工具 |
| `rss_utils.py` | RSS 工具 |
| `textfilter/` | 文本过滤（敏感词检测） |
| `translator/` | 翻译模块（多 API 支持） |
