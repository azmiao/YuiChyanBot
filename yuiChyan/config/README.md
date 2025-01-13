# 配置文件

## 基础配置 `base_config.json5`

```json5
{
    // 监听IP和端口
    "HOST": "0.0.0.0",
    "PORT": 2333,
    // 调试模式
    "DEBUG": false,
    // 超级管理员列表
    "SUPERUSERS": [],
    // 机器人昵称
    "NICKNAME": "优衣酱",
    // 外网协议
    "PUBLIC_PROTOCOL": "http",
    // 外网域名
    "PUBLIC_DOMAIN": "",
    // 全局统一的网络代理配置 | 需要自己代码调用
    "PROXY": ""
}
```

## 核心插件配置 `core_plugins.json5`

> 核心插件大多数都耦合较深，不建议删除

```json5
{
    // 核心插件文件夹和对应的名称 | key是plugins下的文件夹名，value是想给它取的名称，会在帮助页面显示
    "basic": "基础功能",
    "manager": "核心管理",
    "air_con": "群空调",
    "xqa": "XQA你问我答",
    "daily_news": "今日早报",
    "princess": "PCR公主连结基础插件"
}
```

## 额外插件配置 `extra_plugins.json5`

```json5
{
    // 第三方插件文件夹和对应的名称 | key是plugins下的文件夹名，value是想给它取的名称，会在帮助页面显示
}
```

## 授权管理配置 `auth_config.json`

```json5
{
    // 授权系统总开关
    "ENABLE_AUTH": true,
    // 到期前的多少天开始提醒, 设置为0时将不会提醒
    "REMIND_BEFORE_EXPIRED": 3,
    // 私聊使用授权列表时, 每页显示的群的个数
    "GROUPS_IN_PAGE": 5,
    // 退群原因
    "GROUP_LEAVE_MSG": '管理员操作'
}
```

## XQA配置 `xqa_config.json5`

```json5
{
    // 是否要启用消息分段发送
    "IS_SPILT_MSG": true,  // 是否要启用消息分段，默认开启，关闭改成False
    "MSG_LENGTH": 1000,  // 消息分段长度限制，只能数字，千万不能太小，默认1000
    "SPLIT_INTERVAL": 1,  // 消息分段发送时间间隔，只能数字，单位秒，默认1秒
    // 是否使用转发消息发送，仅在查询问题时生效，和上方消息分段可同时开启（可随时改动，重启BOT生效）
    "IS_FORWARD": false,  // 开启后将使用转发消息发送，默认关闭
    // 设置问答的时候，是否校验回答的长度，最大长度和上方 MSG_LENGTH 保持一致（可随时改动，重启BOT生效）
    "IS_JUDGE_LENGTH": false,  // 校验回答的长度，在长度范围内就允许设置问题，超过就不允许，默认开启
    // 如果开启分段发送，且长度没超限制，且开启转发消息时，由于未超长度限制只有一条消息，这时是否需要直接发送而非转发消息（可随时改动，重启BOT生效）
    "IS_DIRECT_SINGER": true,  // 直接发送，默认开启
    // 看问答的时候，展示的分隔符（可随时改动，重启BOT生效）
    "SPLIT_MSG": " | ",  // 默认' | '，可自行换成'\n'或者' '等。单引号不能漏
    // 是否使用base64格式发送图片
    "IS_BASE64": false,
}
```