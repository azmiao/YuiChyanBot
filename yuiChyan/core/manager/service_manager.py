import secrets
import time
from typing import List, Dict, Optional

from quart import request, render_template, redirect, make_response

from yuiChyan.exception import FunctionException
from yuiChyan.service import Service
from .help_utils import build_auth_view
from .util import sv, get_group_services, get_database
from yuiChyan.permission import check_permission
from yuiChyan.config import SUPERUSERS, NICKNAME, MANAGER_PASSWORD, TRUSTED_PROXY_IPS, ENABLE_AUTH
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


# 后台认证状态（单进程部署）
_AUTH_SESSIONS: Dict[str, Dict[str, float]] = {}
_LOGIN_FAILURES: Dict[str, tuple] = {}
_SESSION_TTL = 7200
_MAX_PASSWORD_LENGTH = 256
_FAILURE_WINDOW = 300
_FAILURE_LIMIT = 5
_LOCK_SECONDS = 60


def _client_ip() -> str:
    peer = request.remote_addr or ''
    if peer in TRUSTED_PROXY_IPS:
        forwarded = request.headers.get('X-Real-IP', '').strip()
        if forwarded and ',' not in forwarded and ' ' not in forwarded:
            return forwarded
    return peer


def _https_request() -> bool:
    return request.scheme == 'https' or (
        request.remote_addr in TRUSTED_PROXY_IPS
        and request.headers.get('X-Forwarded-Proto', '').strip().lower() == 'https'
    )


def _set_auth_cookie(response, token: str):
    response.set_cookie('user_id', token, max_age=_SESSION_TTL, httponly=True,
                       secure=_https_request(), samesite='Lax', path='/')
    return response


def _csrf_cookie(response, token: str):
    response.set_cookie('csrf_token', token, max_age=_SESSION_TTL, httponly=False,
                       secure=_https_request(), samesite='Lax', path='/')
    return response


def _no_store(response):
    response.headers['Cache-Control'] = 'no-store'
    return response


def _csrf_valid(form_token: Optional[str]) -> bool:
    token = request.cookies.get('csrf_token')
    return bool(token and form_token and secrets.compare_digest(token, form_token))


# 登录校验
@yui_bot.server_app.before_request
async def _():
    # 路由不存在时不参与认证跳转，保留正常 404
    if request.url_rule is None:
        return
    if request.url_rule.endpoint == 'static':
        return
    if request.path in ['/login', '/', '/help', '/clan']:
        return
    token = request.cookies.get('user_id')
    record = _AUTH_SESSIONS.get(token or '')
    if not record or record['expires'] <= time.time():
        if token:
            _AUTH_SESSIONS.pop(token, None)
        return redirect('/login')
    if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'} and not _csrf_valid((await request.form).get('csrf_token')):
        return ('CSRF 校验失败', 403)


# 登录页面
@yui_bot.server_app.route('/login', methods=['GET', 'POST'])
async def manager_login():
    if request.method == 'GET':
        csrf_token = secrets.token_urlsafe(32)
        response = await make_response(await render_template('manager_login.html', config={'bot_name': NICKNAME, 'csrf_token': csrf_token}))
        _csrf_cookie(response, csrf_token)
        return _no_store(response)
    login_data = await request.form
    if not _csrf_valid(login_data.get('csrf_token')):
        return _no_store(await make_response(('CSRF 校验失败', 403)))
    username = str(login_data.get('username') or '')
    user_ip = _client_ip()
    now = time.time()
    failures, first_at = _LOGIN_FAILURES.get(user_ip, (0, now))
    if now - first_at >= _FAILURE_WINDOW:
        failures, first_at = 0, now
    if failures >= _FAILURE_LIMIT and now - first_at < _LOCK_SECONDS:
        return _no_store(await make_response(redirect('/login')))
    if len(username) > _MAX_PASSWORD_LENGTH or username != MANAGER_PASSWORD:
        _LOGIN_FAILURES[user_ip] = (failures + 1, first_at)
        sv.logger.error(f'> 来自 [{user_ip}] 的用户 [{username}] 登录失败')
        return _no_store(await make_response(redirect('/login')))
    _LOGIN_FAILURES.pop(user_ip, None)
    token = secrets.token_urlsafe(32)
    _AUTH_SESSIONS[token] = {'expires': now + _SESSION_TTL}
    response = await make_response(redirect('/manager'))
    _set_auth_cookie(response, token)
    _csrf_cookie(response, secrets.token_urlsafe(32))
    return _no_store(response)


@yui_bot.server_app.route('/logout', methods=['POST'])
async def manager_logout():
    token = request.cookies.get('user_id')
    _AUTH_SESSIONS.pop(token or '', None)
    response = await make_response(redirect('/login'))
    response.delete_cookie('user_id', path='/')
    response.delete_cookie('csrf_token', path='/')
    return _no_store(response)


# 管理主页面
@yui_bot.server_app.route('/manager', methods=['GET'])
async def manager_page():
    group_list = await yui_bot.get_cached_group_list()
    auth_db = await get_database() if ENABLE_AUTH else {}
    data = []
    for group in group_list:
        group_id = group['group_id']
        group_name = group['group_name']
        enable_list, disable_list = await get_group_services(group_id, True)
        service_list = [_service.to_simple_dict(True) for _service in enable_list]
        service_list += [_service.to_simple_dict(False) for _service in disable_list]
        auth = build_auth_view(auth_db.get(group_id)) if ENABLE_AUTH else None
        data.append({
            'group_id': group_id,
            'group_name': group_name,
            'group_show': f'【{str(group_id)}】' + truncate_string(group_name),
            'auth': auth,
            'service_list': service_list
        })
    csrf_token = request.cookies.get('csrf_token') or secrets.token_urlsafe(32)
    response = await make_response(await render_template('manager_page.html', config={'bot_name': NICKNAME, 'data': data, 'csrf_token': csrf_token}))
    if not request.cookies.get('csrf_token'):
        _csrf_cookie(response, csrf_token)
    return _no_store(response)


@yui_bot.server_app.route('/modify', methods=['POST'])
async def manager_modify():
    modify_data = await request.form
    try:
        group_id = int(str(modify_data.get('group_id', '')).strip())
    except ValueError:
        return ('非法群号', 400)
    service_name = str(modify_data.get('name') or '')
    target_enabled = modify_data.get('enabled') == '1'
    group_list = await yui_bot.get_cached_group_list()
    if group_id not in {int(group['group_id']) for group in group_list}:
        return ('非法群号', 400)
    enable_list, disable_list = await get_group_services(group_id, True)
    service: Optional[Service] = next((item for item in enable_list + disable_list if item.name == service_name), None)
    if not service:
        return ('非法服务', 400)
    if target_enabled != service.judge_enable(group_id):
        (service.enable_service if target_enabled else service.disable_service)(group_id)
    return redirect('/manager')
