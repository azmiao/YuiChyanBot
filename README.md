<p align="center">
  <a href="https://github.com/azmiao/YuiChyanBot">
    <img src="https://raw.githubusercontent.com/azmiao/YuiChyanBot/main/yuiChyan.jpg" width="200" height="200" alt="YuiChyanBot">
  </a>
</p>

# YuiChyanBot 优衣酱

一个自用的 Windows QQ 机器人框架。自带你问我答、翻译、图片文字识别、群抽奖等功能，也可以按群开关功能、管理群授权和查看网页帮助。

项目使用 NoneBot 1.x 和 OneBot V11，部分设计参考了 [HoshinoBot](https://github.com/Ice9Coffee/HoshinoBot)。连接 QQ 需要另外安装 LLOneBot 或 NapCat；一个程序只连接一个机器人账号。

## 开始使用

第一次使用，先看 [安装说明](docs/guide/installation.md)。可以下载绿色包，也可以从源码安装。源码运行需要 Python 3.13 及以上，由 uv 管理运行环境。

| 文档 | 内容 |
|:-----|:-----|
| [项目介绍](docs/guide/introduction.md) | 适合什么用途、使用前要准备什么 |
| [安装说明](docs/guide/installation.md) | 下载、启动和连接 QQ |
| [配置说明](docs/guide/configuration.md) | 设置管理员、连接信息和群授权 |
| [自带功能](docs/guide/features.md) | 常用命令和使用示例 |
| [更新说明](docs/guide/update.md) | 更新程序、备份和保留数据 |
| [插件安装](docs/guide/plugins.md) | 添加、停用和卸载第三方插件 |

## 开发文档

- [代码结构](docs/develop/architecture.md)：主要文件放在哪里，消息怎样交给功能处理。
- [插件开发](docs/develop/plugin-development.md)：从一个简单回复开始，介绍命令、权限和定时任务的写法。

## 第三方插件

[插件列表](https://github.com/stars/azmiao/lists/yuichyanbot-plugins)中的插件需要单独安装，不属于主项目自带功能。具体用法和依赖以各插件自己的说明为准。

## 许可证

[AGPL-3.0](LICENSE)
