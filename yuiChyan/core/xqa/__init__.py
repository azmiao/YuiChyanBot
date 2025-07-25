from yuiChyan.exception import *
from yuiChyan.permission import *
from yuiChyan.service import Service
from .operate_msg import *
from .util import *

sv = Service('core_xqa', help_cmd=('XQA帮助', 'xqa帮助', '问答帮助'))


# 设置问答，支持正则表达式和回流
@sv.on_message('group')
async def set_question(bot: YuiChyan, ev: CQEvent):
    results = re.match(r'^(全群|有人|我)问([\s\S]*)你答([\s\S]*)$', ev.normal_text)
    if not results:
        return

    # (全群|有人|我) | 问题 | 回答
    que_type, que_raw, ans_raw = results.group(1), results.group(2), results.group(3)
    # 群 | 用户
    group_id, user_id = str(ev.group_id), str(ev.user_id)

    # 匹配类型
    match que_type:
        case '全群':
            if get_user_permission(ev) < SUPERUSER:
                await bot.send(ev, f'全群问只能维护组设置呢')
                return
            group_id = 'all'
        case '有人':
            if get_user_permission(ev) < ADMIN:
                await bot.send(ev, f'有人问只能群管理设置呢')
                return
            user_id = 'all'
        case _:
            self_enable = await judge_enable_self(group_id)
            if not self_enable:
                await bot.send(ev, f'本群管理员已禁用"个人问答"功能')
                return

        # 没有问题或没有回答
    if (not que_raw) or (not ans_raw):
        await bot.send(ev, f'发送“{que_type}问XXX你答XXX”我才记得住~')
        return
    # 是否限制问答长度
    if IS_JUDGE_LENGTH and len(ans_raw) > MSG_LENGTH:
        await bot.send(ev, f'回答的长度超过最大字符限制，限制{MSG_LENGTH}字符，包括符号和图片转码后的长度，您设置的回答字符长度为[{len(ans_raw)}]')
        return

    # 检查是否泛匹配
    if re.match(fr'{que_raw}', '检测文本'):
        await bot.send(ev, f'不可设置泛匹配问题哦')
        return

    # 设置问答
    msg = await set_que(bot, group_id, user_id, que_raw, ans_raw)
    await bot.send(ev, msg)


# 看问答，支持模糊搜索
@sv.on_rex(r'^看看(有人|我|全群)问([\s\S]*)$')
async def show_question(bot: YuiChyan, ev: CQEvent):
    # # (全群|有人|我) | 搜索问题
    que_type, search_str = ev['match'].group(1), ev['match'].group(2)
    # 群 | 用户
    group_id, user_id = str(ev.group_id), str(ev.user_id)

    # 消息头
    msg_head = f'查询"{search_str}"相关的结果如下：\n' if search_str else ''
    # 匹配类型
    match que_type:
        case '全群':
            group_list = await get_g_list(bot)
            result_list = await show_all_group_que(search_str, group_list)
        case '有人':
            result_list = await show_que(group_id, 'all', search_str, msg_head)
        case _:
            self_enable = await judge_enable_self(group_id)
            if not self_enable:
                raise SubFuncDisabledException('本群管理员已禁用"个人问答"功能')
            result_list = await show_que(group_id, user_id, search_str, msg_head)

    # 发送消息
    await send_result_msg(bot, ev, result_list)


# 搜索某个成员的问题和回答，限群管理员
@sv.on_message('group')
async def search_question(bot: YuiChyan, ev: CQEvent):
    query_msg = re.match(r'查问答 ?\[CQ:at,qq=([0-9]+)\S*] ?(\S*)', ev.normal_text)
    if not query_msg:
        return

    if get_user_permission(ev) < ADMIN:
        await bot.send(ev, f'搜索某个成员的问答只能群管理操作呢。个人查询问答请使用“看看我问”+搜索内容')
        return

    group_id = str(ev.group_id)
    # 匹配
    user_id, search_str = query_msg.group(1), query_msg.group(2)

    # 看看要查的用户是否在群里
    if not await judge_ismember(bot, group_id, user_id):
        await bot.send(ev, f'该成员{user_id}不在该群中，请检查')
        return

    # 查询内容
    search_str_new = f'"{search_str}"的' if search_str else ''
    # 消息头
    msg_head = f'QQ({user_id})个人问答的查询{search_str_new}结果：\n'
    # 查问答
    result_list = await show_que(group_id, user_id, search_str, msg_head)
    # 发送消息
    await send_result_msg(bot, ev, result_list)


# 不要回答，管理员可以@人删除回答
@sv.on_message('group')
async def delete_question(bot: YuiChyan, ev: CQEvent):
    no_que_match = re.match(r'^(\[CQ:at,qq=[0-9]+\S*])? ?(全群)?不要回答([\s\S]*)$', ev.normal_text)
    if not no_que_match:
        return

    # 用户 | 是否全群 | 不要回答的问题
    user, is_all, no_que_str = no_que_match.group(1), no_que_match.group(2), no_que_match.group(3)
    # 群 | 用户
    group_id, user_id = str(ev.group_id), str(ev.user_id)

    if not no_que_str:
        raise FunctionException(ev, f'删除问答请带上删除内容哦')

    # 全群问的删除
    if is_all:
        if get_user_permission(ev) < SUPERUSER:
            raise LakePermissionException(ev, f'只有维护组可以删除所有群设置的有人问')
        group_list = await get_g_list(bot)
        msg_dict = {}
        msg = f''
        for group_id in group_list:
            m, _ = await del_que(group_id, 'all', no_que_str, False)
            if m and not msg_dict.get(m):
                msg_dict[m] = []
            if m:
                msg_dict[m].append(group_id)
        for msg_tmp in list(msg_dict.keys()):
            g_list = msg_dict[msg_tmp]
            g_msg = ','.join(g_list)
            msg += f'\n在群{g_msg}中' + msg_tmp
        msg = '没有在任何群里找到该问题呢' if msg == f'' else msg.strip()
        await bot.send(ev, msg)
        return

    # 有人问和我问的删除
    if user:
        user_id_at = str(re.findall(r'[0-9]+', user)[0])
        if str(user_id_at) != str(ev.self_id) and get_user_permission(ev) < ADMIN:
            raise LakePermissionException(ev, f'删除他人问答仅限群管理员呢')
        if str(user_id_at) != str(ev.self_id) and not await judge_ismember(bot, group_id, user_id):
            raise FunctionException(ev, f'该成员{user_id}不在该群')
        user_id = user_id if str(user_id_at) == str(ev.self_id) else user_id_at

    # 仅调整不要回答的问题中的图片
    no_que_str = await adjust_img(no_que_str, False, False)
    msg, del_image = await del_que(group_id, user_id, no_que_str, True, get_user_permission(ev) < ADMIN)
    await bot.send(ev, msg)
    # 删除图片
    delete_img(del_image)


# 回复问答
@sv.on_message('group')
async def xqa(bot: YuiChyan, ev: CQEvent):
    group_id, user_id, message = str(ev.group_id), str(ev.user_id), ev.normal_text
    db = await get_database()
    group_dict = db.get(group_id, {'all': {}})
    # 仅调整问题中的图片
    message = await adjust_img(message, False, False)

    # 优先回复自己的问答
    ans = None
    # 判断是否允许设置个人问答
    self_enable = await judge_enable_self(group_id)
    if self_enable:
        # 启用我问功能才会回复个人问答
        ans = await match_ans(group_dict.get(user_id, {}), message, '')

    # 没有自己的问答才回复有人问
    ans = await match_ans(group_dict['all'], message, ans) if not ans else ans
    if ans:
        ans = await adjust_img(ans, True, False)
        await bot.send(ev, ans)


# 复制问答
@sv.on_prefix('XQA复制问答from')
async def copy_question(bot: YuiChyan, ev: CQEvent):
    match = re.match(r'^([0-9]+)to([0-9]+)(full|self)?$', str(ev.message))
    if not match:
        return

    if not check_permission(ev, SUPERUSER):
        raise LakePermissionException(ev, permission=SUPERUSER)

    group_1, group_2, copy_type = match.group(1), match.group(2), match.group(3)
    group_list = await get_g_list(bot)
    if (group_1 not in group_list) or (group_2 not in group_list):
        raise FunctionException(ev, f'群号输入错误！请检查')
    msg = await copy_que(group_1, group_2, copy_type)
    await bot.send(ev, msg)


# 分群控制个人问答权限-禁用我问
@sv.on_match('XQA禁用我问')
async def xqa_disable_self(bot: YuiChyan, ev: CQEvent):
    if not check_permission(ev, SUPERUSER):
        raise LakePermissionException(ev, permission=SUPERUSER)

    msg = await modify_enable_self(str(ev.group_id), False)
    if msg:
        await bot.send(ev, msg)
    else:
        await bot.send(ev, f'本群已成功禁用个人问答功能！')


# 分群控制个人问答权限-启用我问
@sv.on_match('XQA启用我问')
async def xqa_enable_self(bot: YuiChyan, ev: CQEvent):
    if not check_permission(ev, SUPERUSER):
        raise LakePermissionException(ev, permission=SUPERUSER)

    msg = await modify_enable_self(str(ev.group_id), True)
    if msg:
        await bot.send(ev, msg)
    else:
        await bot.send(ev, f'本群已成功启用个人问答功能！')


# 清空本群所有我问
@sv.on_match('XQA清空本群所有我问')
async def xqa_delete_self(bot: YuiChyan, ev: CQEvent):
    if not check_permission(ev, SUPERUSER):
        raise LakePermissionException(ev, permission=SUPERUSER)

    group_id = str(ev.group_id)
    try:
        await delete_all(group_id, True)
        msg = '所有我问清空成功'
    except Exception as e:
        msg = '所有我问清空失败：' + str(e)
    await bot.send(ev, msg)


# 清空本群所有有人问
@sv.on_match('XQA清空本群所有有人问')
async def xqa_delete_all(bot: YuiChyan, ev: CQEvent):
    if not check_permission(ev, SUPERUSER):
        raise LakePermissionException(ev, permission=SUPERUSER)

    group_id = str(ev.group_id)
    try:
        await delete_all(group_id, False)
        msg = '所有有人问清空成功'
    except Exception as e:
        msg = '所有有人问清空失败：' + str(e)
    await bot.send(ev, msg)


# 提取数据
@sv.on_match('XQA提取数据')
async def xqa_export_data(bot: YuiChyan, ev: CQEvent):
    if not check_permission(ev, SUPERUSER):
        raise LakePermissionException(ev, permission=SUPERUSER)

    await export_json()
    await bot.send(ev, 'XQA提取完成，请检查日志')


# 重建数据
@sv.on_match('XQA重建数据')
async def xqa_import_data(bot: YuiChyan, ev: CQEvent):
    if not check_permission(ev, SUPERUSER):
        raise LakePermissionException(ev, permission=SUPERUSER)

    await import_json()
    await bot.send(ev, 'XQA重建完成，新数据将存在"xqa_temp.db"中，请自行备份替换')
