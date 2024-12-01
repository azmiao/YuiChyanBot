import nonebot
from nonebot import message_preprocessor

from yuiChyan import YuiChyan
from yuiChyan.trigger import *


@message_preprocessor
async def handle_message(bot: YuiChyan, event: CQEvent, _):

    if event.detail_type != 'group':
        return

    for t in trigger_chain:
        for service_func in t.find_handler(event):
            # not to me, ignore.
            if service_func.only_to_me and not event['to_me']:
                continue

            # permission denied.
            group_id = int(event.group_id)
            if not service_func.sv.judge_enable(group_id):
                continue

            service_func.sv.logger.info(f'Message {event.message_id} triggered {service_func.__name__}.')
            try:
                await service_func.func(bot, event)
            except nonebot.command.SwitchException:
                continue
            except nonebot.message.CanceledException:
                raise
            except Exception as e:
                service_func.sv.logger.error(f'{type(e)} occurred when {service_func.__name__} '
                                             f'handling message {event.message_id}.')
                service_func.sv.logger.exception(e)
