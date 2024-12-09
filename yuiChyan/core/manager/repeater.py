import random

from aiocqhttp import Event as CQEvent
from nonebot import CQHttpError

from yuiChyan.util import filter_message
from .util import *

PROB_A = 1.4
group_stat = {}


# 随机复读
@sv.on_message()
async def random_repeater(bot, ev: CQEvent):
    group_id = ev.group_id
    msg = str(ev.message)

    if group_id not in group_stat:
        group_stat[group_id] = (msg, False, 0)
        return

    last_msg, is_repeated, p = group_stat[group_id]

    if last_msg == msg:
        # 群友正在复读
        if not is_repeated:
            # 机器人尚未复读过，开始测试复读
            if random.random() < p:
                # 概率测试通过，复读并设flag
                try:
                    group_stat[group_id] = (msg, True, 0)
                    msg = await filter_message(ev.message)
                    await bot.send(ev, msg)
                except CQHttpError as e:
                    yuiChyan.logger.error(f'复读失败: {type(e)}')
            else:
                # 概率测试失败，蓄力
                p = 1 - (1 - p) / PROB_A
                group_stat[group_id] = (msg, False, p)
    else:
        # 不是复读，重置
        group_stat[group_id] = (msg, False, 0)
