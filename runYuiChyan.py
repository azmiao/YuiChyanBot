import asyncio

from yuiChyan import create_instance, start_scheduler

# 优衣酱，启动！
if __name__ == '__main__':

    # 启动计时器
    schedule_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(schedule_loop)
    schedule_loop.run_until_complete(start_scheduler())

    # 启动BOT
    bot = create_instance()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot.run(use_reloader=False, loop=loop)
