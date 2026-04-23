# 配置文件详解

所有配置文件位于 `yuiChyan/config/` 目录下，首次启动时自动生成。格式为 [JSON5](https://json5.org/)，支持注释。

## base_config.json5 — 基础配置

| 字段 | 类型 | 默认值 | 说明 |
|:-----|:-----|:-------|:-----|
| HOST | string | `"0.0.0.0"` | 监听 IP 地址 |
| PORT | int | `2333` | 监听端口，需与 LLOneBot 反向 WebSocket 地址中的端口一致 |
| ACCESS_TOKEN | string | `""` | 签验 Token，需与协议实现客户端配置一致，为空则不校验 |
| DEBUG | bool | `false` | 调试模式，开启后输出更详细的日志 |
| SUPERUSERS | list[int] | `[12345678]` | 维护组（超级管理员）QQ 号列表 |
| NICKNAME | string | `"优衣酱"` | 机器人昵称 |
| PUBLIC_PROTOCOL | string | `"http"` | 外网访问协议（用于帮助网页等外部访问场景） |
| PUBLIC_DOMAIN | string\|null | `null` | 外网域名，为 null 时使用本地地址 |
| PROXY | string\|null | `null` | 全局网络代理地址，需要在插件代码中主动调用 |
| MANAGER_PASSWORD | string | `"12345"` | 网页端后台管理密码，必填 |

## auth_config.json5 — 授权管理配置

| 字段 | 类型 | 默认值 | 说明 |
|:-----|:-----|:-------|:-----|
| ENABLE_AUTH | bool | `true` | 授权系统总开关，关闭后所有群均可使用 |
| REMIND_BEFORE_EXPIRED | int | `3` | 授权到期前多少天开始提醒，设为 0 则不提醒 |
| GROUPS_IN_PAGE | int | `5` | 私聊查询授权列表时每页显示的群数量 |
| GROUP_LEAVE_MSG | string | `"管理员操作"` | BOT 退群时的默认退群原因 |

## xqa_config.json5 — XQA 问答配置

| 字段 | 类型 | 默认值 | 说明 |
|:-----|:-----|:-------|:-----|
| IS_SPILT_MSG | bool | `true` | 是否启用消息分段发送 |
| MSG_LENGTH | int | `1000` | 消息分段长度限制，不宜设置过小 |
| SPLIT_INTERVAL | int | `1` | 分段发送的时间间隔（秒） |
| IS_FORWARD | bool | `false` | 是否使用转发消息发送（仅查询问题时生效） |
| IS_JUDGE_LENGTH | bool | `false` | 设置问答时是否校验回答长度，最大长度与 MSG_LENGTH 一致 |
| IS_DIRECT_SINGER | bool | `true` | 开启分段和转发时，若只有一条消息是否直接发送而非转发 |
| SPLIT_MSG | string | `" \| "` | 查看问答时的分隔符，可改为 `\n` 或空格等 |
| IS_BASE64 | bool | `false` | 是否使用 base64 格式发送图片 |

## core_plugins.json5 — 核心插件注册

注册框架自带的核心插件。格式为 `"文件夹名": "显示名称"`。

默认内容：

```json5
{
    "basic": "基础功能",
    "manager": "核心管理",
    "xqa": "XQA你问我答",
}
```

核心插件位于 `yuiChyan/core/` 目录下，大多数耦合较深，不建议删除。

## extra_plugins.json5 — 第三方插件注册

注册第三方插件。格式与核心插件相同：`"文件夹名": "显示名称"`。

```json5
{
    // key 是 yuiChyan/plugins/ 下的文件夹名
    // value 是显示名称，会在帮助页面展示
    "daily_news": "每日新闻",
    "music": "点歌",
}
```

添加或移除插件后需重启 BOT 生效。详见 [插件说明](plugins.md)。
