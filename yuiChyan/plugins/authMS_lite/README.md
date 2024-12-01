# authMS_lite

[授权管理](https://github.com/pcrbot/authMS)的自用精简版

精简了超多东西，仅限超级管理员自用，限单BOT，无页面，去除卡密

## 支持的软件版本

 - hoshino >= 2.0
 - go-cqhttp >= 1.0.0
  
## 指令
**注意, 以下指令中的空格均不可省略**
### 仅限超级管理员私聊的指令

* 【授权列表】查看所有授权群的信息,后跟数字来查看对应页数
* 【快速检查】立刻检查群的授权, 检查方式与定时任务一样
* 【刷新事件过滤器】手动刷新事件过滤器

### 仅限超级管理员的指令

* 【变更授权 123456789+5】为群123456789增加5天授权, 也可以是减
* 【转移授权 123456*987654】将群123456的剩余时间转移至群987654
* 【授权状态】查询此机器人授权信息的统计, 仅限超级管理员
* 【清除授权 987654】清除群987654的全部授权, 并自动退群(如果配置了的话)
* 【退群 987654】命令退出群聊987654, 但并不清除剩余授权时间
* 【变更所有授权 3】为所有已有授权的群增加3天授权时间
* 【不检查人数 987654】不检查群987654的人数是否超标, 直接在群聊中发送则不必附加群号
* 【不检查授权 987654】不检查群987654的授权是否过期, 直接在群聊中发送则不必附加群号
* 【添加白名单 987654】不检查群987654的授权是否过期以及人数是否超标, 直接在群聊中发送则不必附加群号
* 【移除白名单 987654】将群987654从白名单中移出
* 【全部白名单】查询全部白名单信息

## 开始使用

1. 在hoshino的modules目录下克隆本项目:
   ```
   git clone https://github.com/azmiao/authMS_lite.git
   ```
2. 安装依赖, 如下载过慢建议清华镜像: 
   ```
   pip install -r requirements.txt
   ```
3. 打开配置样例`config/authMS_lite.py.example`, 按照注释修改为您需要的配置，然后将其改名为`authMS_lite.py`并复制到HoshinoBot统一配置目录下(hoshino/config/)
   > ！！！重点注意：如果您是初次使用authMS, 建议保持默认`ENABLE_AUTH`为`False`, 然后手动给每个群都增加授权时间, 再修改成`True`，然后重启bot

4. 打开go-cqhttp的目录，找到`config.yml`，设置里面的事件过滤器的路径，对应到本项目的`config/filter.json`
   > 例如：`filter: 'C:/HoshinoBot/hoshino/modules/authMS_lite/config/filter.json'`，注意请务必写单正斜杠，不然授权重载无效，然后重启go-cqhttp

5. 开始快乐的玩耍吧

## 贡献

[GitHub@wdvxdr1123](https://github.com/wdvxdr1123)

[GitHub@xhl6699](https://github.com/xhl6666)

[GitHub@var](https://github.com//var-mixer)