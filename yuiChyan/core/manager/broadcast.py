import asyncio

from yuiChyan import get_bot, logger, YuiChyan
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


def parse_command(ev, command_raw: str):
    if ' ' not in command_raw:
        return 'all', command_raw
    args = command_raw.split(' ', 1)
    bc_sv_name = args[0]
    bc_msg = args[1]
    if bc_sv_name != 'all' and not bc_sv_name.startswith('g-') and not bc_sv_name.startswith('exg-'):
        raise CommandErrorException(ev, f'> 广播命令错误，{bc_example}')
    return bc_sv_name, bc_msg


# 广播消息
@sv.on_command('广播', force_private=True)
async def broadcast(bot: YuiChyan, ev: CQEvent):
    command_raw = str(ev.message).strip()
    bc_sv_name, bc_msg = parse_command(ev, command_raw)
    yui_bot = get_bot()
    self_id_list = yui_bot.get_self_ids()
    for self_id in self_id_list:
        match self_id:
            case 'all':
                _group_id_list = await bot.get_group_list(self_id=self_id)
                group_id_list = [int(group['group_id']) for group in _group_id_list]
            case x if x.startswith('g-'):
                bc_l = bc_sv_name.replace('g-', '')
                group_id_list = [int(x) for x in bc_l.split(r'/')]
            case x if x.startswith('exg-'):
                _group_id_list = await bot.get_group_list(self_id=self_id)
                group_id_list = [int(group['group_id']) for group in _group_id_list]
                bc_l = bc_sv_name.replace('exg-', '')
                exclude_gl = [int(x) for x in bc_l.split(r'/')]
                for ex_gid in exclude_gl:
                    group_id_list.remove(ex_gid)
            case _:
                group_id_list = []
        for group_id in group_id_list:
            try:
                await yui_bot.send_group_msg(self_id=self_id, group_id=group_id, message=bc_msg)
                logger.info(f'> 广播 [{self_id}, {group_id}, {bc_msg}] 发送成功')
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f'> 广播 [{self_id}, {group_id}, {bc_msg}] 发送失败：{str(e)}')
