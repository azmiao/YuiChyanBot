# 插件说明

## 插件机制

YuiChyanBot 的插件分为两类：

- **核心插件**：位于 `yuiChyan/core/` 目录下，通过 `core_plugins.json5` 注册，与框架耦合较深
- **第三方插件**：位于 `yuiChyan/plugins/` 目录下，通过 `extra_plugins.json5` 注册，可自由安装和卸载

两类插件的加载机制相同：框架启动时读取对应的 json5 配置文件，按注册顺序使用 nonebot 的 `load_plugins()` 加载。

## 官方插件列表

目前可用的第三方插件：https://github.com/stars/azmiao/lists/yuichyanbot-plugins

## 安装插件

1. 下载插件文件夹，放入 `yuiChyan/plugins/` 目录下
2. 在 `yuiChyan/config/extra_plugins.json5` 中注册插件：

```json5
{
    "插件文件夹名": "显示名称",
}
```

3. 重启 BOT

### 示例

假设要安装一个名为 `daily_news` 的插件：

```
yuiChyan/plugins/
└── daily_news/
    ├── __init__.py
    └── HELP.md        # 可选，有则自动生成帮助菜单
```

在 `extra_plugins.json5` 中添加：

```json5
{
    "daily_news": "每日新闻",
}
```

## 卸载插件

1. 从 `extra_plugins.json5` 中移除对应的注册行
2. 重启 BOT
3. 插件文件夹可以保留也可以删除，不注册就不会加载

## 帮助菜单

如果插件目录下存在 `HELP.md` 文件，框架会自动收集并生成帮助菜单图片和帮助网页。编写规范详见 [插件开发说明](../develop/plugin-development.md#helpmd-编写规范)。
