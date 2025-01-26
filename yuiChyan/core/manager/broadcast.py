import asyncio

from yuiChyan import logger, YuiChyan
from yuiChyan.exception import *
from .util import sv

lock = asyncio.Lock()
broadcast_record = []
bc_example = f'''
广播命令样例：
1.广播 all 广播内容
2.广播 g-13131313 广播内容
3.广播 exg-13131313 广播内容
'''.strip()


def parse_command(ev: CQEvent, command_raw: str):
    if ' ' not in command_raw:
        return 'all', command_raw
    args = command_raw.split(' ', 1)
    bc_group = args[0]
    bc_msg = args[1]
    if bc_group != 'all' and not bc_group.startswith('g-') and not bc_group.startswith('exg-'):
        raise CommandErrorException(ev, f'> 广播命令错误，{bc_example}')
    return bc_group, bc_msg


# 广播消息
@sv.on_command(('广播', 'bc'), force_private=True)
async def broadcast(bot: YuiChyan, ev: CQEvent):
    command_raw = str(ev.message).strip()
    bc_group, bc_msg = parse_command(ev, command_raw)
    self_id = bot.get_self_id()
    match bc_group:
        case 'all':
            _group_id_list = await bot.get_cached_group_list()
            group_id_list = [int(group['group_id']) for group in _group_id_list]
        case bc_group if bc_group.startswith('g-'):
            bc_l = bc_group.replace('g-', '')
            group_id_list = [int(x) for x in bc_l.split(r'/')]
        case bc_group if bc_group.startswith('exg-'):
            _group_id_list = await bot.get_cached_group_list()
            group_id_list = [int(group['group_id']) for group in _group_id_list]
            bc_l = bc_group.replace('exg-', '')
            exclude_gl = [int(x) for x in bc_l.split(r'/')]
            for ex_gid in exclude_gl:
                group_id_list.remove(ex_gid)
        case _:
            group_id_list = []
    for group_id in group_id_list:
        try:
            await bot.send_group_msg(self_id=self_id, group_id=group_id, message=bc_msg)
            logger.info(f'> 广播 [{self_id}, {group_id}, {bc_msg}] 发送成功')
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f'> 广播 [{self_id}, {group_id}, {bc_msg}] 发送失败：{str(e)}')
