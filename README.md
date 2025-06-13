<p align="center">
  <a href="https://github.com/azmiao/YuiChyanBot">
    <img src="https://raw.githubusercontent.com/azmiao/YuiChyanBot/main/yuiChyan.jpg" width="200" height="200" alt="YuiChyanBot">
  </a>
</p>

# ✦ YuiChyanBot 优衣酱 ✦

- 上方图片偷自 PID: 82685587
- 一个自用的机器人框架，部分架构设计思想参考自咖啡的[HoshinoBot](https://github.com/Ice9Coffee/HoshinoBot)

## 所需环境

- 系统: 仅限 64位 Win10+ 系统
- python: 推荐直接最新版本，最低建议`3.13.1`
- 协议实现: 任选其一：LLOneBot >= 5.0.0 或 NapCat >= 4.5.0 或 其他协议实现客户端

## 框架局限性

1. 仅支持单BOT实例，不支持同时使用多个BOT账户
2. 虽然已做了很多兼容处理，但仍不保证所有协议实现客户端的接口兼容性，LLOneBot测试稳定可用
3. BOT框架本意为纯自用，不保证更新和问题修复

## 支持的核心功能

1. BOT业务实现、服务管理和控制
2. 网页端的服务管理
3. 网页版的帮助菜单
4. 自带授权管理系统

## 自带的基础功能

1. 群空调
2. 翻译、文字识别、漫画翻译、选择困难症、群抽奖、掷骰子、猜拼音是啥、解析B站封面、解析二维码 （部分功能不稳定，经常炸了是正常的）
3. 每日新闻
4. 搜歌点歌
5. PCR公主连结基础功能魔改版，带台服客户端解析核心功能
6. XQA高级你问我答

## 如何使用

1. 拉代码，安装依赖`pip install -r requirements.txt`
2. 启动BOT：`python runYuiChyan.py`
3. 第一次启动会在config下生成配置，请修改后关闭BOT重启启动即可使用

## 其他说明后续慢慢更新
