import asyncio
import json
import random
import threading
import time

import websockets
from aiocqhttp.message import Message

# 所有配置
config = {
    'bot_id': 233333333,
    'sender_id': 2362020227,
    'role': 'normal',
    'group_name': '测试群',
    'group_id': 66666666,
    'ws_url': 'ws://127.0.0.1:2333/ws/',
    'access_token': 'test',
    'reconnect_interval': 1,  # 首次重连等待秒数，后续按指数退避
    'max_reconnect_interval': 30,  # 重连等待上限秒数
    'stable_reset_sec': 60,  # 稳定在线多久后重置退避计数
    'input_queue_size': 20,  # 待发送控制台输入的队列上限
    'nickname': 'AZMIAO',
    'sex': 'male',
    'age': 0,
    'rate_limiter': {
        'enable': False,
        'frequency': 1,
        'bucket_size': 5
    }
}

# 控制台输入结束的哨兵值 | 用于通知连接循环退出
STDIN_CLOSED = object()


# 计算重连退避时长 | 指数增长 + 抖动 + 上限
def compute_backoff_delay(attempt: int, base: float, max_delay: float, jitter: float = 0.2) -> float:
    delay = min(max_delay, base * (2 ** (max(attempt, 1) - 1)))
    if jitter > 0:
        delay *= random.uniform(1 - jitter, 1 + jitter)
    return delay


class RateLimiter:
    def __init__(self, frequency, bucket_size):
        frequency = float(frequency)
        bucket_size = int(bucket_size)
        if frequency <= 0 or bucket_size <= 0:
            raise ValueError('rate_limiter 的 frequency 和 bucket_size 必须为正数')
        self.limit = frequency
        self.bucket_size = bucket_size
        self.tokens = float(bucket_size)
        self.last = time.monotonic()

    async def wait(self):
        while True:
            now = time.monotonic()
            self.tokens = min(self.bucket_size, self.tokens + (now - self.last) * self.limit)
            self.last = now
            if self.tokens >= 1:
                self.tokens -= 1
                return
            # 按缺少的令牌数一次性睡够，避免高频轮询
            await asyncio.sleep((1 - self.tokens) / self.limit)


# 控制台输入线程 | 仅启动一次，通过队列把输入交给事件循环
def _stdin_reader(loop, queue):
    while True:
        try:
            line = input()
        except (EOFError, KeyboardInterrupt):
            loop.call_soon_threadsafe(_put_input, queue, STDIN_CLOSED)
            return
        loop.call_soon_threadsafe(_put_input, queue, line)


def _put_input(queue, item):
    if queue.full():
        # 队列已满时丢弃最旧的输入，避免离线期间积压过期命令
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            pass
    queue.put_nowait(item)


def _start_stdin_reader(loop, queue):
    thread = threading.Thread(target=_stdin_reader, args=(loop, queue), daemon=True)
    thread.start()
    return thread


async def send_messages(ws, queue, rate_limiter):
    while True:
        message_ = await queue.get()
        if message_ is STDIN_CLOSED:
            raise EOFError('控制台输入已关闭')
        message_ = str(message_).strip()
        msg_id = random.randint(10000000, 99999999)

        data = {
            'time': int(time.time()),
            'self_id': config['bot_id'],
            'post_type': 'message',
            'sub_type': 'normal',
            'message_id': msg_id,
            'user_id': config['sender_id']
        }

        # 消息类型匹配
        msg_header = message_[:1]
        match msg_header:
            case '~':
                # 戳一戳
                data['post_type'] = 'notice'
                data['notice_type'] = 'notify'
                data['sub_type'] = 'poke'
                data['target_id'] = config['bot_id']
                data['group_id'] = config['group_id']
                print(f'收到群 {config["group_name"]}({config["group_id"]}) 的戳一戳事件 ({msg_id})')
            case '/':
                # 私聊
                message_ = message_[1:]
                msg = Message(message_)
                data['post_type'] = 'message'
                data['message_type'] = 'private'
                data['detail_type'] = 'private'
                data['sub_type'] = 'normal'
                data['message'] = msg
                data['raw_message'] = str(msg)
                print(f'收到私聊 {config["nickname"]}({config["sender_id"]}) 的消息: {message_} ({msg_id})')
            case _:
                # 群聊
                message_ = message_.replace('@BOT', f'[CQ:at,qq={config["bot_id"]}]')
                msg = Message(message_)
                data['post_type'] = 'message'
                data['message_type'] = 'group'
                data['detail_type'] = 'group'
                data['sub_type'] = 'normal'
                data['message'] = msg
                data['raw_message'] = str(msg)
                data['group_id'] = config['group_id']
                data['sender'] = {'card': config["nickname"]}
                print(f'收到群 {config["group_name"]}({config["group_id"]}) 的消息: {message_} ({msg_id})')

        if rate_limiter:
            await rate_limiter.wait()
        await ws.send(json.dumps(data))


async def receive_messages(ws):
    while True:
        message = await ws.recv()
        message_ = json.loads(message)

        # 消息内容
        msg_list = message_.get('params', {}).get('message', [])
        message_type = message_.get('params', {}).get('message_type', '')
        echo = message_.get("echo", {})
        msg = Message(msg_list).extract_plain_text().strip()

        # 准备返回API
        msg_id = random.randint(10000000, 99999999)
        # 动作
        action = message_.get('action', '')
        match action:
            case 'send_msg':
                if message_type == 'group':
                    print(f'发送群 {config["group_name"]}({config["group_id"]}) 的消息 ({msg_id}) :\n{msg}')
                else:
                    print(f'发送私聊 {config["nickname"]}({config["sender_id"]}) 的消息 ({msg_id}) :\n{msg}')
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
            case 'get_group_info':
                data = {
                    'group_id': config["group_id"],
                    'group_name': config["group_name"],
                    'member_count': 10,
                    'max_member_count': 500
                }
            case 'send_group_msg':
                print(f'发送群 {config["group_name"]}({config["group_id"]}) 的消息: {msg} ({msg_id})')
                data = {'message_id': msg_id}
            case 'get_friend_list':
                data = [
                    {
                        'user_id': config["sender_id"],
                        'nickname': config["nickname"]
                    }
                ]
            case 'send_group_forward_msg':
                print(f'发送群 {config["group_name"]}({config["group_id"]}) 的合并转发消息: {msg} ({msg_id})')
                data = {'message_id': msg_id}
            case _:
                print(f'> 检测到未知Action: {action}')
                continue
        json_data = json.dumps({'echo': echo, 'data': data, 'retcode': 0, 'status': 'ok', 'message': ''})
        await ws.send(json_data)


# 关闭连接上的收发任务 | 无论哪个任务先结束都取消另一个并等待其收尾
async def _stop_tasks(*tasks):
    for task in tasks:
        if not task.done():
            task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


async def connect_ws(ws_url, reconnect_interval, max_reconnect_interval, stable_reset_sec,
                     rate_limiter, headers, input_queue):
    loop = asyncio.get_running_loop()
    attempt = 0
    while True:
        try:
            print(f'> 正在尝试连接至[{ws_url}]...')
            async with websockets.connect(
                    ws_url,
                    additional_headers=headers,
                    max_size=2 ** 20 * 10,
                    open_timeout=10,
                    close_timeout=5,
                    ping_interval=20,
                    ping_timeout=20
            ) as websocket:
                print(f'> 已连接至[{ws_url}]')
                connected_at = loop.time()

                send_task = asyncio.create_task(send_messages(websocket, input_queue, rate_limiter))
                receive_task = asyncio.create_task(receive_messages(websocket))
                try:
                    await asyncio.wait(
                        {send_task, receive_task},
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    # 有任务结束或失败时，取出结果以触发对应异常
                    for task in (send_task, receive_task):
                        if task.done() and not task.cancelled():
                            task.result()
                finally:
                    await _stop_tasks(send_task, receive_task)

                # 稳定在线足够久后才重置退避计数
                if loop.time() - connected_at >= stable_reset_sec:
                    attempt = 0
        except asyncio.CancelledError:
            raise
        except (websockets.ConnectionClosed, ConnectionRefusedError,
                websockets.exceptions.InvalidStatus, websockets.exceptions.InvalidHandshake,
                websockets.exceptions.InvalidURI, OSError) as e:
            attempt += 1
            delay = compute_backoff_delay(attempt, reconnect_interval, max_reconnect_interval)
            print(f'连接[{ws_url}]失败[{str(e)}]，将于{delay:.1f}秒后重试...')
            await asyncio.sleep(delay)
        except EOFError:
            print('> 控制台输入已关闭，停止重连。')
            return
        except Exception as e:
            # 未知异常记录堆栈并按退避重试，避免忙循环
            attempt += 1
            delay = compute_backoff_delay(attempt, reconnect_interval, max_reconnect_interval)
            print(f'连接[{ws_url}]出现异常[{type(e).__name__}: {e}]，将于{delay:.1f}秒后重试...')
            await asyncio.sleep(delay)


async def main():
    # 频次限制中间件 | 仅限制主动发送，不限制接收
    rate_config = config.get('rate_limiter', {})
    rate_limiter = RateLimiter(
        frequency=rate_config.get('frequency', 1),
        bucket_size=rate_config.get('bucket_size', 5)
    ) if rate_config.get('enable', False) else None

    # 控制台输入队列 | 断线期间最多保留有限条输入
    input_queue: asyncio.Queue = asyncio.Queue(maxsize=config.get('input_queue_size', 20))
    # 控制台输入线程 | 全程只启动一次，重连不会重复创建
    _start_stdin_reader(asyncio.get_running_loop(), input_queue)

    # 启动
    await connect_ws(
        config['ws_url'],
        config['reconnect_interval'],
        config['max_reconnect_interval'],
        config['stable_reset_sec'],
        rate_limiter,
        {
            'X-Self-ID': config['bot_id'],
            'X-Client-Role': 'Universal',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + config['access_token']
        },
        input_queue
    )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n> 已退出。')
