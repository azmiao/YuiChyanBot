from hoshino.config.__bot__ import SUPERUSERS
from nonebot import on_command

from . import util


@on_command('查询授权', only_to_me=False)
async def auth_query_chat(session):
    uid = session.event.user_id
    if not session.current_arg:
        # 无参，检查群聊与否
        if session.event.detail_type == 'private':
            # 私聊禁止无参数查询授权
            await session.finish('私聊查询授权请发送“查询授权 群号”来进行指定群的授权查询（请注意空格）')
            return
        else:
            # 群聊，获取gid
            gid = session.event.group_id
    else:
        # 有参数，检查权限
        if uid not in SUPERUSERS:
            await session.finish('抱歉，您的权限不足')
            return
        else:
            # 权限为超级管理员
            gid = session.current_arg.strip() 
            if not gid.isdigit():
                await session.finish('请输入正确的群号')
                return

    result = util.check_group(gid)
    if not result:
        msg = '此群未获得授权'
    else:
        msg = await util.process_group_msg(gid, result, title='授权查询结果\n')
    await session.finish(msg)
