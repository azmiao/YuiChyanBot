from .based_config import NICKNAME

# 授权系统总开关
ENABLE_AUTH = True
# 授权到期后是否自动退群
AUTO_LEAVE = False
# 新群试用天数
NEW_GROUP_DAYS = 7
# 到期前的多少天开始提醒, 设置为0时将不会提醒
REMIND_BEFORE_EXPIRED = 2
# 到期后多少天退群, 仅当配置AUTO_LEAVE为True是此项有效, 设置为0则立即退群
LEAVE_AFTER_DAYS = 7
# 私聊使用授权列表时, 每页显示的群的个数
GROUPS_IN_PAGE = 5
# 离开群之前的发言
GROUP_LEAVE_MSG = f'> {NICKNAME}即将退出本群，感谢您的使用~\n退群原因:'
