
# 监听IP和端口
HOST = '0.0.0.0'
PORT = 2333
# 调试模式
DEBUG = False
# 超级管理员列表
SUPERUSERS = [2362020227]
# 机器人昵称
NICKNAME = '优衣酱'
# 外网协议
PUBLIC_PROTOCOL = 'http'
# 外网域名
PUBLIC_DOMAIN = ''
# 全局统一的网络代理配置 | 需要自己代码调用
PROXY = {
    "http": "http://localhost:1081",
    "https": "http://localhost:1081"
}
# 核心插件文件夹和对应的名称 | key是plugins下的文件夹名，value是想给它取的名称，都必填
CORE_PLUGINS = {
    'basic': '基础功能',
    'manager': '核心管理',
    'xqa': 'XQA你问我答',
    'princess': 'PCR插件'
}
# 第三方插件文件夹和对应的名称 | key是plugins下的文件夹名，value是想给它取的名称，都必填
EXTRA_PLUGINS = {
}
