# 更新方式

## 标准更新流程

### 1. 拉取最新代码

```bash
git pull
```

### 2. 更新依赖

双击运行 `更新依赖.bat`，或手动执行：

```bash
uv sync
uv run playwright install chromium
```

### 3. 重启 BOT

关闭正在运行的 BOT，重新双击 `启动YuiChyan.bat` 或执行：

```bash
uv run runYuiChyan.py
```

## 注意事项

- **配置文件不会被覆盖**：`yuiChyan/config/` 下的 json5 配置文件已被 `.gitignore` 排除，`git pull` 不会影响你的配置
- **第三方插件需单独更新**：`yuiChyan/plugins/` 目录被 `.gitignore` 排除，框架更新不会影响已安装的第三方插件，插件需要自行前往对应仓库拉取更新
- **数据库文件不受影响**：`yuiChyan/res/` 目录下的 RocksDB 数据库文件同样被排除，更新不会丢失数据
