from typing import List, Dict

from yuiChyan.exception import FunctionException
from yuiChyan.service import Service
from .util import sv
from yuiChyan.permission import check_permission
from yuiChyan.config import SUPERUSERS


# 查询本群所有可见的服务
@sv.on_command('服务列表', only_to_me=True)
async def list_group_services(bot, ev):
    group_id = ev.group_id
    enable_list = []
    disable_list = []
    loaded_services = Service.get_loaded_services()
    for service in loaded_services.values():
        # 判断是否隐藏
        if not service.visible:
            continue
        # 判断是否启用
        if service.judge_enable(group_id):
            enable_list.append(service)
        else:
            disable_list.append(service)
    # 生成消息
    msg = f'本群可见的服务列表：\n'
    msg += '\n'.join([f'- [启用] {service.name}' for service in enable_list])
    msg += '\n'
    msg += '\n'.join([f'- [禁用] {service.name}' for service in disable_list])
    await bot.send(ev, msg.strip())


# 对本群启用指定的服务 | 英文逗号间隔多个服务
@sv.on_command('启用服务', only_to_me=True)
async def list_group_services(bot, ev):
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
async def list_group_services(bot, ev):
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
