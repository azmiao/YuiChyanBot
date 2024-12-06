import asyncio
from collections import deque

from yuiChyan import get_bot, logger
from yuiChyan.exception import *
from .util import sv


class Broadcast:

    def __init__(self, self_id, group_id, msg):
        self.self_id = self_id
        self.group_id = group_id
        self.msg = msg


class BroadcastQueue:

    def __init__(self):
        self.queue = deque()

    def is_empty(self):
        return len(self.queue) == 0

    def enqueue(self, item: Broadcast):
        self.queue.append(item)

    def dequeue(self) -> Broadcast:
        if not self.is_empty():
            return self.queue.popleft()

    def size(self):
        return len(self.queue)


lock = asyncio.Lock()
broadcast_queue = BroadcastQueue()
broadcast_record = []
bc_example = f'''
广播命令样例：
1.广播 all 广播内容
2.广播 g-13131313 广播内容
3.广播 exg-13131313 广播内容
'''.strip()


def parse_command(command_raw: str):
    if ' ' not in command_raw:
        return 'all', command_raw
    args = command_raw.split(' ', 1)
    bc_sv_name = args[0]
    bc_msg = args[1]
    if bc_sv_name != 'all' and not bc_sv_name.startswith('g-') and not bc_sv_name.startswith('exg-'):
        raise CommandErrorException('> broadcast command error!')
    return bc_sv_name, bc_msg


# 广播消息 | 仅添加队列
@sv.on_command('广播', force_private=True)
async def broadcast(bot, ev):
    command_raw = str(ev.message).strip()
    try:
        bc_sv_name, bc_msg = parse_command(command_raw)
    except CommandErrorException:
        await bot.send(ev, '命令格式错误，请参考' + bc_example)
        return
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
            bc_entity = Broadcast(self_id, group_id, bc_msg)
            broadcast_queue.enqueue(bc_entity)
            logger.debug(f'> Broadcast[{self_id}, {group_id}, {bc_msg}] has added to BroadcastQueue!')


@sv.scheduled_job(second='*/2')
async def send_broadcast():
    if broadcast_queue.size() == 0:
        return
    bc_entity = broadcast_queue.dequeue()
    self_id = bc_entity.self_id
    group_id = bc_entity.group_id
    msg = bc_entity.msg
    yui_bot = get_bot()
    try:
        msg_obj = await yui_bot.send_group_msg(self_id=self_id, group_id=group_id, message=msg)
        logger.info(f'> Broadcast[{self_id}, {group_id}, {msg}] send success, message id is [{msg_obj["message_id"]}].')
    except Exception as e:
        logger.error(f'> Broadcast[{self_id}, {group_id}, {msg}] send failed：{str(e)}')
