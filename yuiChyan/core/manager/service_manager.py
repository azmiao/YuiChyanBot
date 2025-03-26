import uuid
from typing import List, Dict, Optional

from quart import request, render_template, session, redirect, make_response

from yuiChyan.exception import FunctionException
from yuiChyan.service import Service
from .util import sv, get_group_services
from yuiChyan.permission import check_permission
from yuiChyan.config import SUPERUSERS, NICKNAME, MANAGER_PASSWORD
from yuiChyan import YuiChyan, CQEvent, yui_bot
from yuiChyan.util import truncate_string


# 查询本群所有可见的服务
@sv.on_command('服务列表', only_to_me=True)
async def list_group_services(bot: YuiChyan, ev: CQEvent):
    enable_list, disable_list = await get_group_services(ev.group_id, False)
    # 生成消息
    msg = f'本群可见的服务列表：\n'
    msg += '\n'.join([f'- [启用] {service.name}' for service in enable_list])
    msg += '\n'
    msg += '\n'.join([f'- [禁用] {service.name}' for service in disable_list])
    await bot.send(ev, msg.strip())


# 对本群启用指定的服务 | 英文逗号间隔多个服务
@sv.on_command('启用服务', only_to_me=True)
async def list_group_services(bot: YuiChyan, ev: CQEvent):
    services = str(ev.message).strip()
    if not services:
        return
    # 要启用的服务列表
    service_name_list = services.split(',')
    success_list, failed_dict = await modify_service_list(ev, service_name_list, True)
    msg = await construct_msg(True, success_list, failed_dict)
    await bot.send(ev, msg)


# 对本群禁用指定的服务 | 英文逗号间隔多个服务
@sv.on_command('禁用服务', only_to_me=True)
async def list_group_services(bot: YuiChyan, ev: CQEvent):
    services = str(ev.message).strip()
    if not services:
        return
    # 要关闭的服务列表
    service_name_list = services.split(',')
    success_list, failed_dict = await modify_service_list(ev, service_name_list, False)
    msg = await construct_msg(False, success_list, failed_dict)
    await bot.send(ev, msg)


# 修改服务状态
async def modify_service_list(ev, service_name_list: List[str], is_enable: bool) -> (List[str], Dict[str, str]):
    # 检查服务名是否正确
    loaded_services = Service.get_loaded_services()
    invalid_name = [x for x in service_name_list if x not in loaded_services]
    if invalid_name:
        raise FunctionException(ev, f'如下服务名不存在，请检查：\n{str(invalid_name)}')

    # 开始修改
    success_list: List[str] = []
    failed_dict: Dict[str, str] = {}
    for service_name in service_name_list:
        # 具体服务
        service = loaded_services[service_name]

        # 检查服务是否隐藏不可修改
        if not service.visible and ev.user_id not in SUPERUSERS:
            failed_dict[service_name] = f'- 服务 [{service_name}] 不可见，无法修改'
            continue

        # 判断是否有权限修改
        manage = service.manage
        if not check_permission(ev, manage):
            failed_dict[service_name] = f'- 服务 [{service_name}] 修改失败，需要权限 [{manage.name}]'
            continue

        # 判断是否已经是所需状态
        old_status = service.judge_enable(ev.group_id)
        if is_enable and old_status:
            failed_dict[service_name] = f'- 服务 [{service_name}] 已经在本群中启用过了!'
            continue
        if (not is_enable) and (not old_status):
            failed_dict[service_name] = f'- 服务 [{service_name}] 已经在本群中禁用过了!'
            continue

        # 修改状态
        if is_enable:
            service.enable_service(ev.group_id)
        else:
            service.disable_service(ev.group_id)
        success_list.append(service_name)

    return success_list, failed_dict


# 构造返回消息
async def construct_msg(is_enable: bool, success_list: List[str], failed_dict: Dict[str, str]) -> str:
    is_enable_str = '启用' if is_enable else '禁用'
    msg = ''
    if success_list:
        msg += f'> {is_enable_str}成功的服务：\n{str(success_list)}\n'
    if failed_dict:
        msg += f'> {is_enable_str}失败的服务：\n' + '\n'.join(failed_dict.values())
    return msg.strip()


# 登录校验
@yui_bot.server_app.before_request
async def _():
    # 排除的请求
    if request.path in ['/login', '/', '/help', '/clan']:
        return
    # 排除静态文件
    if request.path.startswith('/static'):
        return
    # cookie是否过期
    user_id = request.cookies.get('user_id')
    if user_id and session.get('user_id') == user_id:
        return
    return redirect('/login')


# 登录页面
@yui_bot.server_app.route('/login', methods=['GET','POST'])
async def manager_login():
    if request.method == 'GET':
        return await render_template('manager_login.html', config={'bot_name': NICKNAME})
    else:
        login_data = await request.form
        username = login_data.get('username')
        user_ip = request.remote_addr
        if str(username) == MANAGER_PASSWORD:
            sv.logger.info(f'> 来自 [{user_ip}] 的用户 [{str(username)}] 登录成功')
            user_id = str(uuid.uuid4())
            session['user_id'] = user_id
            # 创建响应并设置 cookie
            response = await make_response(redirect('/manager'))
            response.set_cookie('user_id', user_id, max_age=7200)
            return response
        else:
            sv.logger.error(f'> 来自 [{user_ip}] 的用户 [{str(username)}] 登录失败')
            return redirect('/login')


# 管理主页面
@yui_bot.server_app.route('/manager', methods=['GET'])
async def manager_page():
    group_list = await yui_bot.get_cached_group_list()
    data = []
    for group in group_list:
        group_id = group['group_id']
        group_name = group['group_name']
        enable_list, disable_list = await get_group_services(group_id, True)
        service_list = [_service.to_simple_dict(True) for _service in enable_list]
        service_list += [_service.to_simple_dict(False) for _service in disable_list]
        data.append({
            'group_id': group_id,
            'group_name': group_name,
            'group_show': f'【{str(group_id)}】' + truncate_string(group_name),
            'service_list': service_list
        })
    return await render_template('manager_page.html', config={'bot_name': NICKNAME, 'data': data})


@yui_bot.server_app.route('/modify', methods=['POST'])
async def manager_modify():
    # 获取表单数据
    modify_data = await request.form
    group_id = modify_data.get('group_id')
    service_name = modify_data.get('name')
    enable_list, disable_list = await get_group_services(group_id, True)
    # 检查服务在启用列表还是禁用列表，并切换状态
    service: Optional[Service] = next((service for service in enable_list if service.name == service_name), None)
    if service:
        service.disable_service(group_id)
        return redirect('/manager')
    service: Optional[Service] = next((service for service in disable_list if service.name == service_name), None)
    if service:
        service.enable_service(group_id)
        return redirect('/manager')
