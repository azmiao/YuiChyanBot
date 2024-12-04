import asyncio
import json
import time
import random

import websockets
from aiocqhttp.message import Message

# 所有配置
config = {
    'bot_id': 3100271297,
    'sender_id': 2362020227,
    'name': 'message.group.admin',
    'group_name': '测试群',
    'group_id': 66666666,
    'ws_url': 'ws://127.0.0.1:2333/ws/',
    'reconnect_interval': 3,
    'nickname': 'AZMIAO',
    'sex': 'male',
    'age': 0,
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
                is_private = message_.startswith('/')
                message_ = message_[1:] if is_private else message_
                data = {
                    'time': int(time.time()),
                    'self_id': config['bot_id'],
                    'post_type': 'message',
                    'message_type': 'private' if is_private else 'group',
                    'sub_type': 'normal',
                    'message_id': msg_id,
                    'user_id': config['sender_id'],
                    'message': message_,
                    'raw_message': message_,
                    'font': 0,
                    'sender': {
                        'nickname': config['nickname'],
                        'sex': config['sex'],
                        'age': config['age']
                    }
                }

                if not is_private:
                    data['group_id'] = config['group_id']
                    msg_from = f'群 {config["group_name"]}({config["group_id"]})'
                else:
                    msg_from = f'私聊 {config["nickname"]}({config["sender_id"]})'

                print(f'收到{msg_from} 的消息: {message_} ({msg_id})')
                await rate_limit_middleware(rate_limiter, ws.send(json.dumps(data)))
        except asyncio.CancelledError as error:
            print(error)
        except Exception as _:
            raise websockets.ConnectionClosed

    async def receive_messages(ws):
        try:
            while True:
                message = await rate_limit_middleware(rate_limiter, ws.recv())
                message_ = json.loads(message)
                # print(message_)

                # 消息内容
                msg_list = message_.get('params', {}).get('message', [])
                message_type = message_.get('params', {}).get('message_type', '')
                echo = message_.get("echo", {})
                msg = Message(msg_list).extract_plain_text()

                # 准备返回API
                msg_id = random.randint(10000000, 99999999)
                # 动作
                action = message_.get('action', '')
                match action:
                    case 'send_msg':
                        if message_type == 'group':
                            print(f'发送群 {config["group_name"]}({config["group_id"]}) 的消息: {msg} ({msg_id})')
                        else:
                            print(f'发送私聊 {config["nickname"]}({config["sender_id"]}) 的消息: {msg} ({msg_id})')
                        data = {'message_id': msg_id}
                    case 'get_group_member_info':
                        data = {
                            'group_id': config["group_id"],
                            'user_id': config["sender_id"],
                            'nickname': config["nickname"],
                            'sex': config["sex"],
                            'age': config["age"],
                            'role': 'owner'
                        }
                    case 'get_group_list':
                        data = [
                            {
                                'group_id': config["group_id"],
                                'group_name': config["group_name"],
                                'member_count': 10,
                                'max_member_count': 500
                            }
                        ]
                    case _:
                        continue
                json_data = json.dumps({'echo': echo, 'data': data, 'retcode': 0, 'status': 'ok', 'message': ''})
                # print(f'Send msg: {json_data}')
                await ws.send(json_data)

        except asyncio.CancelledError as error:
            print(error)
        except Exception as _:
            raise websockets.ConnectionClosed

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
        except Exception as e:
            print(e)


async def main():

    # 频次限制中间件
    rate_limiter = RateLimiter(
        frequency=config.get('rate_limiter', {}).get('frequency', ''),
        bucket_size=config.get('rate_limiter', {}).get('bucket_size', '')
    ) if config.get('rate_limiter', {}).get('enable', True) else None

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
