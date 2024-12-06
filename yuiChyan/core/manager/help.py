import os

from jinja2 import FileSystemLoader
from quart import render_template

import yuiChyan
from yuiChyan.config import PUBLIC_PROTOCOL, PUBLIC_DOMAIN, HOST, PORT
from .util import sv

# 优衣酱APP
server_app = yuiChyan.yui_bot.server_app
template_dir = os.path.abspath(os.path.dirname(__file__))
template_loader = FileSystemLoader(template_dir)
server_app.jinja_env.loader = template_loader

# 示例服务列表数据
service_list = [
    {"name": "Service1", "help": "Help description for Service1"},
    {"name": "Service2", "help": "Help description for Service2"},
]


# 帮助页面
@server_app.route('/help')
async def help_view():
    # 通过 Quart 的 render_template 方法渲染 Jinja2 模板
    return await render_template('template.html', services=service_list)


# 帮助菜单
@sv.on_match(('help', '帮助', '菜单'))
async def sv_help(bot, ev):
    address = f'{PUBLIC_PROTOCOL}://{PUBLIC_DOMAIN}' if PUBLIC_DOMAIN else f'http://{HOST}:{PORT}'
    await bot.send(ev, f'> 优衣酱帮助菜单：\n{address}/help')
