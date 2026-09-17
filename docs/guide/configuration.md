# 配置说明

配置文件在 `yuiChyan/config/` 下，首次启动时生成。修改后需要重启机器人。

文件使用 JSON5 格式：文字加引号，数字不加引号，`true` 表示开启，`false` 表示关闭，`null` 表示未设置。支持用 `//` 写注释。配置项名称要保持原样。

第一次使用，先改 `SUPERUSERS` 和 `MANAGER_PASSWORD`，再检查连接地址、端口和 `ACCESS_TOKEN`。其他设置大多可以先用默认值。

## base_config.json5：基本设置

| 配置项 | 默认值 | 说明 |
|:-------|:-------|:-----|
| HOST | `"0.0.0.0"` | 接受连接的地址。只在本机使用时建议改为 `"127.0.0.1"`；默认值也允许其他电脑连接，能否访问还取决于网络和防火墙 |
| PORT | `2333` | 连接端口，要与 LLOneBot 或 NapCat 中填写的一致 |
| ACCESS_TOKEN | `""` | 连接验证密钥，两边必须一致；留空则不验证，建议设置 |
| DEBUG | `false` | 是否记录详细日志；排查问题时再开启，分享日志前注意去除私人信息 |
| SUPERUSERS | `[12345678]` | 管理机器人的 QQ 号。多个账号写成 `[11111111, 22222222]`，文档中的“维护组”就是这些账号 |
| NICKNAME | `"优衣酱"` | 机器人昵称 |
| PUBLIC_PROTOCOL | `"http"` | 帮助链接使用 `http` 还是 `https`；填写 `https` 不会自动开启加密访问 |
| PUBLIC_DOMAIN | `null` | 帮助链接使用的域名，不带 `http://` 或 `https://`；留空时用 HOST 和 PORT 拼接地址 |
| PROXY | `null` | 供代码读取的网络代理地址，不会自动让所有请求走代理 |
| MANAGER_PASSWORD | `"12345"` | 网页后台密码，务必修改，不要使用默认值 |
| TRUSTED_PROXY_IPS | `[]` | 可信反向代理的直接对端 IP 列表。只有请求直接来自这些地址时，后台才会采用 `X-Real-IP` 和 `X-Forwarded-Proto`；不使用反代时保持空列表 |

`0.0.0.0` 不是用来在浏览器中打开的地址。同一台电脑上查看帮助，请访问 `http://127.0.0.1:2333/help`。填写域名也不会自动完成公网访问配置，不要直接把管理后台开放到公网。

### Nginx 反向代理配置

如果通过 Nginx 使用 HTTPS 访问后台，Python 服务看到的直接来源通常是 Nginx 的地址，而不是访问者的公网 IP。请把这个地址写入 `TRUSTED_PROXY_IPS`，例如 Nginx 与 YuiChyanBot 在同一台电脑上时：

```json5
// yuiChyan/config/base_config.json5
{
    "HOST": "127.0.0.1",
    "PORT": 2333,
    "TRUSTED_PROXY_IPS": ["127.0.0.1"]
}
```

Nginx 需要覆盖转发头，避免客户端自行伪造：

```nginx
location / {
    proxy_pass http://127.0.0.1:2333;

    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

安全注意事项：

- `TRUSTED_PROXY_IPS` 填写的是 Python 服务看到的 Nginx 对端地址，不是访客公网 IP；跨机器部署时不要照抄 `127.0.0.1`。
- 只有直接对端 IP 在列表中时，程序才信任 `X-Real-IP` 和 `X-Forwarded-Proto`；不要把它配置成任意用户可连接的地址范围。
- 应用支持 HTTP 和 HTTPS：直接 HTTPS 或可信代理转发 HTTPS 时，认证 Cookie 会设置 `Secure`；普通 HTTP 访问时不设置 `Secure`。实际公网部署仍建议只开放 HTTPS。
- 后端端口应通过防火墙限制为本机或 Nginx 可访问，避免攻击者绕过 Nginx 直接连接应用。
- 修改配置后需要重启机器人。

## auth_config.json5：群授权

群授权决定哪些群可以使用需要授权的功能，与 QQ 自身的权限无关。

| 配置项 | 默认值 | 说明 |
|:-------|:-------|:-----|
| ENABLE_AUTH | `true` | 是否检查普通消息功能的群授权；关闭后这类功能不再要求群授权，但仍受各群功能开关限制 |
| REMIND_BEFORE_EXPIRED | `3` | 提前多少天提醒授权到期，`0` 表示不提醒 |
| GROUPS_IN_PAGE | `5` | 私聊查看授权列表时，每页显示几个群，填写大于 0 的整数 |
| GROUP_LEAVE_MSG | `"管理员操作"` | 机器人退群时使用的默认原因 |

保持授权开启时，维护组可以私聊发送 `变更授权 123456789+30`，为该群增加 30 天授权。群内发送 `查询授权` 可以查看状态；关闭授权开关后，这条查询不会回复。

注意：当前定时任务和 `Service.broadcast()` 仍会检查授权记录，不随 `ENABLE_AUTH` 一起关闭。使用这些功能时仍需给群添加授权。

## xqa_config.json5：你问我答

| 配置项 | 默认值 | 说明 |
|:-------|:-------|:-----|
| IS_SPILT_MSG | `true` | 是否把长消息拆成多条发送，名称中的 `SPILT` 是代码现有拼写，请勿改名 |
| MSG_LENGTH | `1000` | 每段消息的长度上限，不要设得太小 |
| SPLIT_INTERVAL | `1` | 每段消息之间间隔几秒 |
| IS_FORWARD | `false` | 查看问答时，是否用合并转发消息发送 |
| IS_JUDGE_LENGTH | `false` | 添加问答时是否限制回答长度，上限由 MSG_LENGTH 决定 |
| IS_DIRECT_SINGER | `true` | 同时开启分段和转发时，只有一条消息就直接发送，不用合并转发 |
| SPLIT_MSG | `" \| "` | 查看问答时用什么分隔内容，可改成 `"\n"` 换行 |
| IS_BASE64 | `false` | 是否把图片转为 base64 后发送；没有图片发送问题时可保持默认 |

## core_plugins.json5：自带功能

保存主项目自带功能的文件夹名和显示名称：

```json5
{
    "basic": "基础功能",
    "manager": "核心管理",
    "xqa": "XQA你问我答",
}
```

它们位于 `yuiChyan/core/`，包含帮助、管理等基础功能，建议保留。只想关闭某个群的功能，用群内的启用、禁用服务命令即可。

## extra_plugins.json5：第三方插件

默认没有第三方插件。安装后，在这里添加 `"插件文件夹名": "显示名称"`，重启后加载。安装和卸载步骤见 [插件安装](plugins.md)。
