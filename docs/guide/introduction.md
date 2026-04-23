# BOT 说明介绍

## 项目简介

YuiChyanBot（优衣酱）是一个基于 Windows 平台的 QQ 机器人框架，部分架构设计思想参考自 [HoshinoBot](https://github.com/Ice9Coffee/HoshinoBot)。

项目于 2025-07-24 正式转为开源项目。

## 技术栈

- 运行框架：[NoneBot 1.x](https://github.com/nonebot/nonebot) + [aiocqhttp](https://github.com/nonebot/aiocqhttp)
- 通信协议：[OneBot V11](https://github.com/botuniverse/onebot-11)（反向 WebSocket）
- 协议实现：[LLOneBot](https://github.com/LLOneBot/LLOneBot)（推荐）/ [NapCat](https://github.com/NapNeko/NapCatQQ)
- 包管理：[uv](https://docs.astral.sh/uv/)
- 数据库：[RocksDB](https://rocksdb.org/)（通过 rocksdict）
- 页面渲染：[Playwright](https://playwright.dev/)（Chromium）
- Web 服务：[Quart](https://quart.palletsprojects.com/) + [Jinja2](https://jinja.palletsprojects.com/)

## 系统要求

| 项目 | 要求 |
|:-----|:-----|
| 操作系统 | 仅限 64 位 Windows 10 及以上 |
| Python | >= 3.13（推荐最新版本） |
| 协议实现 | LLOneBot >= 5.0.0 或 NapCat >= 4.5.0 |

## 框架局限性

1. 仅支持单 BOT 实例，不支持同时使用多个 BOT 账户
2. 虽然已做了很多兼容处理，但仍不保证所有协议实现客户端的接口兼容性，LLOneBot 测试稳定可用
3. BOT 框架本意为纯自用，不保证更新和问题修复

## 核心能力

- **服务管理**：插件级别的服务启用/禁用控制，支持黑名单和白名单模式
- **网页端管理**：通过 Web 界面管理服务状态
- **帮助系统**：根据插件目录下的 `HELP.md` 自动生成帮助菜单图片和帮助网页
- **授权系统**：独立的群授权管理，支持授权到期提醒
- **XQA 问答**：支持正则回流的高级你问我答系统
