import markdown2
from quart import render_template, Markup, redirect

import yuiChyan
from yuiChyan.config import PUBLIC_PROTOCOL, PUBLIC_DOMAIN, HOST, PORT, NICKNAME
from .util import sv

# 帮助页面的参数
config: dict = {}


# 主页重定向至帮助页面
@yuiChyan.yui_bot.server_app.route('/', methods=['GET'])
async def home_to_help():
    return redirect('/help')


# 帮助页面
@yuiChyan.yui_bot.server_app.route('/help', methods=['GET'])
async def help_view():
    global config
    # 从插件列表里解析模板
    if not config:
        self_help_list = yuiChyan.help_list
        for help_ in self_help_list:
            help_['id'] = self_help_list.index(help_)
            help_path = help_.get('path', '')
            with open(help_path, 'r', encoding='utf-8') as file:
                markdown_content = file.read()
            html_content = markdown2.markdown(markdown_content, extras=['fenced-code-blocks', 'tables'])
            help_['help'] = Markup(html_content)
        # 放入帮助列表
        config['help_list'] = self_help_list
        # 放入BOT别称
        config['bot_name'] = NICKNAME
    # 通过 Quart 的 render_template 方法渲染 Jinja2 模板
    return await render_template('help_page.html', config=config)


# 帮助菜单
@sv.on_match(('help', '帮助', '菜单'))
async def sv_help(bot: yuiChyan.YuiChyan, ev: yuiChyan.CQEvent):
    address = f'{PUBLIC_PROTOCOL}://{PUBLIC_DOMAIN}' if PUBLIC_DOMAIN else f'{PUBLIC_PROTOCOL}://{HOST}:{PORT}'
    await bot.send(ev, f'【{NICKNAME}菜单】\n> 发送"看看有人问"查看本群管理设置的问答\n> 其他功能请看：\n{address}/help')
