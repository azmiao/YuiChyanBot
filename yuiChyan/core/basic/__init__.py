import httpx
from nonebot import on_notice, NoticeSession

from yuiChyan import LakePermissionException, CommandErrorException, FunctionException
from yuiChyan.config import NICKNAME
from yuiChyan.permission import check_permission, ADMIN
from yuiChyan.service import Service
from yuiChyan.util import translate, DailyNumberLimiter, filter_message
from .create_info import *
from .group_gacha import *
from .manga_trans import *

sv = Service('base_func', help_cmd='基础功能帮助')


# 翻译
@sv.on_prefix('翻译', only_to_me=True)
async def translate_text(bot, ev):
    messages = str(ev.message).strip()
    text_list = messages.split(' ', 2)
    try:
        _, _, _ = text_list[0], text_list[1], text_list[2]
    except:
        raise CommandErrorException(ev, '> 翻译指令错误! \n示例：翻译 en zh 文本')

    try:
        msg = await translate(text_list[2], text_list[0], text_list[1])
    except Exception as e:
        raise FunctionException(ev, f'> 翻译出现错误：{str(e)}')
    await bot.send(ev, msg)


# 文字识别
@sv.on_prefix(('文字识别', 'ocr'), only_to_me=True)
async def get_ocr(bot, ev):
    img_text = str(ev.message)
    if not img_text.startswith('[CQ:image,file='):
        raise CommandErrorException(ev, '> 文字识别指令错误! \n示例：文字识别 {图片}，注意{图片}换成自己实际需要的图片')
    user_id = ev.user_id
    img_id_tmp = re.findall(r'CQ:image,file=.+?\.image', img_text)
    img_id = img_id_tmp[0].replace('CQ:image,file=', '')
    data = await bot.ocr_image(image=img_id)
    text_list = list(data['texts'])
    msg = f'[CQ:at,qq={user_id}]\n'
    for text_info in text_list:
        msg = msg + ' | ' + text_info['text']
    await bot.send(ev, msg)


# 漫画翻译
@sv.on_prefix('漫画翻译', only_to_me=True)
async def manga_translate(bot, ev):
    img_text = str(ev.message)
    if not img_text.startswith('[CQ:image,'):
        raise CommandErrorException(ev, '> 文字识别指令错误! \n示例：漫画翻译 {图片}，注意{图片}换成自己实际需要的图片')
    # 保存图片
    img_name = await parse_and_save_image(ev, img_text)
    await bot.send(ev, '> 已收到图片，翻译非常慢，请耐心等待')
    try:
        msg = await manga_tran(img_name)
        await bot.send(ev, msg)
    except Exception as e:
        raise FunctionException(ev, f'漫画 [{img_name}] 翻译出错，请联系维护组：{str(e)}')


# 生成消息
@sv.on_prefix('生成消息', only_to_me=True)
async def create_msg(bot, ev):
    group_id = ev.group_id
    all_text = str(ev.message)
    try:
        forward_msg_list = await get_create_msg(bot, all_text, group_id, False)
    except:
        raise CommandErrorException(ev, '> 生成消息命令错误，实例：\n生成消息 qq号:内容1|qq号:内容2\n注意：冒号使用英文冒号')
    if not forward_msg_list:
        raise CommandErrorException(ev, '> 生成消息命令错误，实例：\n生成消息 qq号:内容1|qq号:内容2\n注意：冒号使用英文冒号')
    elif forward_msg_list == ['QQ号错误!本群里没有这个人哦']:
        raise FunctionException(ev, f'> {forward_msg_list[0]}')
    elif forward_msg_list == ['QQ号错误!被@的人不在本群里']:
        raise FunctionException(ev, f'> {forward_msg_list[0]}')
    else:
        await bot.send_group_forward_msg(group_id=group_id, messages=forward_msg_list)


# 生成陌生消息
@sv.on_prefix('生成陌生消息', only_to_me=True)
async def create_msg(bot, ev):
    group_id = ev.group_id
    all_text = str(ev.message)
    try:
        forward_msg_list = await get_create_msg(bot, all_text, group_id, True)
    except:
        raise CommandErrorException(ev, '> 生成陌生消息命令错误，实例：\n生成陌生消息 qq号:内容1|qq号:内容2\n注意：冒号使用英文冒号')
    if not forward_msg_list:
        raise CommandErrorException(ev, '> 生成陌生消息命令错误，实例：\n生成陌生消息 qq号:内容1|qq号:内容2\n注意：冒号使用英文冒号')
    elif forward_msg_list == ['QQ号错误!被@的人不在本群里']:
        raise FunctionException(ev, f'> {forward_msg_list[0]}')
    else:
        await bot.send_group_forward_msg(group_id=group_id, messages=forward_msg_list)


# 帮助选择器
@sv.on_prefix('选择', only_to_me=True)
async def make_choice(bot, ev):
    all_text = str(ev.message).strip()
    if '还是' not in all_text:
        return
    split = all_text.split('还是')
    msg_list = []
    for choice in split:
        index = split.index(choice) + 1
        msg_list.append(f'{index}. {choice}')
    split.append('全都要')
    await bot.send(ev, '> 您的选项:\n' + '\n'.join(msg_list) + f'\n{NICKNAME}建议你选择: {random.choice(split)} 哦~')


# 创建抽奖
@sv.on_prefix('创建抽奖')
async def create_gacha(bot, ev):
    if not check_permission(ev, ADMIN):
        raise LakePermissionException(ev, '创建抽奖仅限群管理员哦~')
    all_text = str(ev.message).strip()
    if not all_text:
        raise CommandErrorException(ev, '创建抽奖命令错误，样例：创建抽奖 抽奖名字 1')
    if ' ' not in all_text:
        raise CommandErrorException(ev, '创建抽奖命令错误，样例：创建抽奖 抽奖名字 1')
    split = all_text.split(' ')
    try:
        number = int(split[1])
    except Exception:
        raise CommandErrorException(ev, '创建抽奖命令错误，样例：创建抽奖 抽奖名字 1')
    msg = await create_group_gacha(str(ev.group_id), str(split[0]), number)
    await bot.send(ev, msg)


# 结束抽奖
@sv.on_prefix('结束抽奖')
async def finish_gacha(bot, ev):
    if not check_permission(ev, ADMIN):
        raise LakePermissionException(ev, '结束抽奖仅限群管理员哦~')
    all_text = str(ev.message).strip()
    if not all_text:
        raise CommandErrorException(ev, '结束抽奖命令错误，样例：结束抽奖 抽奖名字')
    msg = await finish_group_gacha(str(ev.group_id), all_text)
    await bot.send(ev, msg)


# 参与抽奖
@sv.on_match(('参与抽奖', '参加抽奖'))
async def join_gacha(bot, ev):
    msg = await join_group_gacha(str(ev.group_id), int(ev.user_id))
    await bot.send(ev, msg)


# 查询抽奖
@sv.on_match('查询抽奖')
async def query_gacha(bot, ev):
    msg = await query_group_gacha(str(ev.group_id))
    await bot.send(ev, msg)


# 让 YuiChyan 戳戳你
@sv.on_match(('戳一戳我', '戳戳我'), only_to_me=True)
async def send_point(bot, ev):
    await bot.send(ev, f'[CQ:poke,qq={int(ev.user_id)}]')


# YuiChyan 被戳提醒
@on_notice('notify.poke')
async def poke_back(session: NoticeSession):
    # 单次戳我的冷却
    time_limit = 10
    # 每日戳我的总上限
    daily_limit = 10
    # 返回的消息列表
    msg_list = [
        f'呜喵~',
        f'嗯哼？找{NICKNAME}有啥事呢',
        f'{NICKNAME}饿了，能给我买点吃的吗~',
        f'嘎哦~ 嘎哦~',
        f'每天最多戳我十次哦~',
        f'嗯...{NICKNAME}..正在睡大觉呢',
        f'看我的必杀技————花朵射击！',
        f'喵喵喵？',
        f'{NICKNAME}我啊，以前可是{NICKNAME}哦',
        f'你戳的对，{NICKNAME}我啊是由{NICKNAME}自主研发的{NICKNAME}',
        f'大家要早睡早起哦，指第一天早上睡，第二天早上起',
        f'俗话说的好，早期的虫儿被鸟吃',
        f'欸嘿嘿，{NICKNAME}打牌又赢了，荣！段幺九！',
        f'偷偷告诉你，{NICKNAME}其实不是机器人，我只是打字比较快而已'
    ]

    uid = session.ctx['user_id']
    self_ids = session.bot.get_self_ids()
    if session.ctx['target_id'] not in self_ids:
        return

    # 频次和单日次数检测
    lmt = FreqLimiter(time_limit)
    daily_limit = DailyNumberLimiter(daily_limit)
    if not lmt.check(uid):
        return
    if not daily_limit.check(uid):
        return

    lmt.start_cd(uid)
    daily_limit.increase(uid, 1)
    await session.send(random.choice(msg_list))


# 掷骰子
@sv.on_rex(r'掷骰子 ?(\d{1,3})d(\d{1,3})')
async def query_dice(bot, ev):
    # 次数和面数
    times, ranges = int(ev['match'].group(1)), int(ev['match'].group(2))

    if times == 0:
        raise FunctionException(ev, '欸欸欸...0个骰子？')
    if ranges == 0:
        raise FunctionException(ev, '欸欸欸...0面的骰子？')

    # 骰子的结果列表
    results = []
    # 投掷 times 次骰子
    for _ in range(times):
        result = random.randint(1, ranges)
        results.append(result)
    # 计算所有投掷的总和
    total = sum(results)
    # 格式化每一次投掷的结果为字符串
    results_str = '+'.join(map(str, results))
    if len(results) == 1:
        msg = f'掷骰子{times}次的结果是：\n{results_str}'
    else:
        msg = f'掷骰子{times}次的结果是：\n{results_str}={total}'
    await bot.send(ev, msg, at_sender=True)


@sv.on_match('我好了')
async def are_you_ok(bot, ev):
    await bot.send(ev, '不许好，憋回去！')


@sv.on_suffix('是啥', only_to_me=True)
async def what_to_say(bot, ev):
    text = str(ev.message).strip()
    if not text:
        return

    async with httpx.AsyncClient(verify=False) as session:
        response = await session.post(
            'https://lab.magiconch.com/api/nbnhhsh/guess',
            json={'text': text},
            timeout=5,
            headers={'content-type': 'application/json'},
        )
    data = list(response.json())
    if not data:
        await bot.send(ev, f'{NICKNAME}也不知道 [{text}] 是啥呢~')
        return

    msg_list = []
    for translated in data:
        name = translated.get('name')
        trans_list = translated.get('trans', [])
        msg = f'> [{name}] 可能的翻译为：\n' + '\n'.join(trans_list)
        msg_list.append(msg)

    msg_result = '\n'.join(msg_list).strip()
    if not msg_result:
        await bot.send(ev, f'{NICKNAME}也不知道 [{text}] 是啥呢~')
        return

    await bot.send(ev, await filter_message(msg_result))