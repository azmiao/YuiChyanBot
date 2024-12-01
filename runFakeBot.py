import asyncio
import json
import time
import random

import websockets
from aiocqhttp.message import Message

# 所有配置
config = {
    'bot_id': 3100271297,
    'sender_id': 123456789,
    'group_name': '测试群',
    'group_id': 66666666,
    'ws_url': 'ws://127.0.0.1:2333/ws/',
    'reconnect_interval': 3,
    'rate_limiter': {
        'enable': False,
        'frequency': 1,
        'bucket_size': 5
    }
}


class RateLimiter:
    def __init__(self, frequency, bucket_size):
        self.limit = frequency
        self.bucket_size = bucket_size
        self.tokens = bucket_size
        self.last = time.time()

    async def wait(self):
        while self.tokens <= 0:
            now = time.time()
            self.tokens += (now - self.last) * self.limit
            self.last = now
            if self.tokens > self.bucket_size:
                self.tokens = self.bucket_size
            await asyncio.sleep(0.1)
        self.tokens -= 1


async def rate_limit_middleware(limiter, coro):
    if limiter:
        await limiter.wait()
    return await coro


async def connect_ws(ws_url, reconnect_interval, rate_limiter, headers):
    async def send_messages(ws):
        try:
            while True:
                message_ = await asyncio.to_thread(input)
                msg_id = random.randint(10000000, 99999999)
                data = {
                    "time": int(time.time()),
                    "self_id": config['bot_id'],
                    "group_id": config['group_id'],
                    "post_type": "message",
                    "message_type": "group",
                    "sub_type": "normal",
                    "message_id": msg_id,
                    "user_id": config['sender_id'],
                    "message": message_,
                    "raw_message": message_,
                    "font": 0,
                    "sender": {
                        "nickname": "TEST",
                        "sex": "male",
                        "age": 0
                    }
                }
                print(f'收到群 {config["group_name"]}({config["group_id"]}) 的消息: {message_} ({msg_id})')
                await rate_limit_middleware(rate_limiter, ws.send(json.dumps(data)))
        except asyncio.CancelledError:
            pass

    async def receive_messages(ws):
        try:
            while True:
                message = await rate_limit_middleware(rate_limiter, ws.recv())
                message_ = json.loads(message)
                # 消息内容
                msg_list = message_.get('params', {}).get('message', [])
                echo = message_.get("echo", {})
                msg = Message(msg_list).extract_plain_text()
                # print(f'\n> 收到WS上报数据：{msg}')
                # 动作
                action = message_.get('action', '')
                if action == 'send_msg':
                    msg_id = random.randint(10000000, 99999999)
                    print(f'发送群 {config["group_name"]}({config["group_id"]}) 的消息: {msg} ({msg_id})')
                    data = {
                        'echo': echo,
                        'data': {'message_id': msg_id},
                        'retcode': 0,
                        'status': 'ok',
                        'message': ''
                    }
                    await ws.send(json.dumps(data))
        except asyncio.CancelledError:
            pass

    while True:
        try:
            print(f'> 正在尝试连接至[{ws_url}]...')
            async with websockets.connect(ws_url, additional_headers=headers) as websocket:
                print(f'> 已连接至[{ws_url}]')

                # 使用 asyncio.gather 来同时运行发送和接收函数
                send_task = asyncio.create_task(send_messages(websocket))
                receive_task = asyncio.create_task(receive_messages(websocket))

                # 结合两个任务，直到最快完成的任务
                await asyncio.gather(send_task, receive_task)
        except (websockets.ConnectionClosed, ConnectionRefusedError, websockets.exceptions.InvalidStatus) as e:
            print(f'连接[{ws_url}]失败[{str(e)}]，将于{reconnect_interval}秒后重试...')
            await asyncio.sleep(reconnect_interval)


async def main():

    # 频次限制中间件
    rate_limiter = RateLimiter(
        frequency=config['rate_limiter']['frequency'],
        bucket_size=config['rate_limiter']['bucket_size']
    ) if config['rate_limiter']['enable'] else None

    # 启动
    await connect_ws(
        config['ws_url'],
        config['reconnect_interval'],
        rate_limiter,
        {
            'X-Self-ID': config['bot_id'],
            'X-Client-Role': 'Universal',
            'Content-Type': 'application/json'
        }
    )


if __name__ == '__main__':
    asyncio.run(main())
