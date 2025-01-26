import asyncio
import base64
import json
import random
import re

from rocksdict import Rdict

from yuiChyan import logger, YuiChyan, CQEvent
from yuiChyan.config import *
from yuiChyan.resources import xqa_db_, xqa_img_path, base_db_path
from yuiChyan.util import filter_message
from yuiChyan.util.parse import extract_file, save_image


# 获取数据库
async def get_database() -> Rdict:
    return xqa_db_


# 判断是否启用个人问答功能
async def judge_enable_self(group_id: str):
    xqa_db = await get_database()
    group_auth = xqa_db.get('config', {})
    auth_config = group_auth.get(group_id, {})
    return auth_config.get('self', True)


# 修改启用个人问答功能的状态
async def modify_enable_self(group_id: str, enable: bool) -> str:
    xqa_db = await get_database()
    group_auth = xqa_db.get('config', {})
    auth_config = group_auth.get(group_id, {})
    # 判断原来的状态
    self_enable = auth_config.get('self', True)
    if self_enable and enable:
        return '本群已经启用了个人问答哦，无需再次启用'
    elif (not self_enable) and (not enable):
        return '本群已经禁用了个人问答哦，无需再次禁用'
    # 修改
    auth_config['self'] = enable
    group_auth[group_id] = auth_config
    xqa_db['config'] = group_auth
    return ''


# 判断是否在群里
async def judge_ismember(bot: YuiChyan, group_id: str, user_id: str) -> bool:
    member_list = await bot.get_group_member_list(group_id=int(group_id))
    user_list = []
    for member in member_list:
        user_id_tmp = member['user_id']
        user_list.append(str(user_id_tmp))
    if user_id in user_list:
        return True
    else:
        return False


# 数据库导出至JSON文件
async def export_json():
    xqa_db = await get_database()
    db_json_path = os.path.join(base_db_path, 'xqa_db.json')
    data = {}
    for key, value in xqa_db.items():
        data[key] = value
    with open(db_json_path, 'w', encoding='UTF-8') as file:
        # noinspection PyTypeChecker
        json.dump(data, file, indent=4, ensure_ascii=False)


# JSON文件转换回数据库文件
async def import_json():
    db_json_path = os.path.join(base_db_path, 'xqa_db.json')
    with open(db_json_path, 'r', encoding='UTF-8') as file:
        data = dict(json.load(file))
    xqa_db_temp = Rdict(os.path.join(base_db_path, 'xqa_temp.db'))
    # 将数据写入数据库
    for key, value in data.items():
        xqa_db_temp[key] = value


# 获取群列表
async def get_g_list(bot: YuiChyan) -> list:
    group_list = await bot.get_cached_group_list()
    g_list = []
    for group in group_list:
        group_id = group['group_id']
        g_list.append(str(group_id))
    return g_list


# 搜索问答 | 这里也需要处理一下图片，但不用保存
async def get_search(que_list: list, search_str: str) -> list:
    if not search_str:
        return que_list
    search_list = []
    search_str_ = await adjust_img(search_str, False, False)
    for question in que_list:
        if re.search(rf'\S*{search_str_}\S*', question):
            search_list.append(question)
    return search_list


# 匹配替换字符
async def replace_message(match_que: re.Match, match_dict: dict, que: str) -> str:
    ans_tmp = match_dict.get(que)
    # 随机选择
    ans = random.choice(ans_tmp)
    flow_num = re.search(r'\S*\$([0-9])\S*', ans)
    if not flow_num:
        return ans
    for i in range(int(flow_num.group(1))):
        ans = ans.replace(f'${i + 1}', match_que.group(i + 1))
    return ans


# 调整转义分割字符 “#”
async def adjust_list(list_tmp: list, char: str) -> list:
    ans_list = []
    str_tmp = list_tmp[0]
    i = 0
    while i < len(list_tmp):
        if list_tmp[i].endswith('\\'):
            str_tmp += char + list_tmp[i + 1]
        else:
            ans_list.append(str_tmp)
            str_tmp = list_tmp[i + 1] if i + 1 < len(list_tmp) else list_tmp[i]
        i += 1
    return ans_list


# 下载图片并转换图片路径
async def doing_img(image_file: str, image_name: str, image_url: str, save: bool) -> str:
    image_path = os.path.join(xqa_img_path, image_name)

    # 调用协议客户端实现接口下载图片
    if save:
        await save_image(None, image_file, image_name, image_url, image_path)
        # 只有在需要保存后，并且开启BASE64模式的时候才转化，普通的问题不需要转
        if IS_BASE64:
            with open(image_path, 'rb') as file_:
                return 'base64://' + base64.b64encode(file_.read()).decode()
    else:
        # 如果是问题的话不用保存图片，原来是啥就是啥，但是没关系，问题只用作匹配
        return image_file
    # 正常的回答还是返回文件路径
    return 'file:///' + os.path.abspath(image_path)


# 进行图片处理 | 问题：无需过滤敏感词，回答：需要过滤敏感词
async def adjust_img(str_raw: str, is_ans: bool, save: bool) -> str:
    # 找出其中所有的CQ码
    cq_list = re.findall(r'(\[CQ:(\S+?),(\S+?)])', str_raw)
    # 整个消息过滤敏感词，问题：无需过滤
    flit_msg = await filter_message(str_raw) if is_ans else str_raw
    # 对每个CQ码元组进行操作
    for cq_code in cq_list:
        # 对当前的完整的CQ码过滤敏感词，问题：无需过滤
        flit_cq = await filter_message(cq_code[0]) if is_ans else cq_code[0]
        # 判断是否是图片
        if cq_code[1] == 'image':
            # 解析file和file_name
            is_base64, image_file, image_file_name, image_url = await extract_file(cq_code[2])
            # 不是base64才需要保存图片或处理图片路径
            if not is_base64:
                # 对图片单独保存图片，并修改图片路径为真实路径
                image_file = await doing_img(image_file, image_file_name, image_url, save)
            # 图片CQ码：替换
            flit_msg = flit_msg.replace(flit_cq, f'[CQ:{cq_code[1]},file={image_file}]')
        else:
            # 其他CQ码：原封不动放回去，防止CQ码被敏感词过滤成错的了
            flit_msg = flit_msg.replace(flit_cq, cq_code[0])
    # 解决回答中不用于随机回答的\#
    flit_msg = flit_msg.replace('\\#', '#')
    return flit_msg


# 匹配消息
async def match_ans(info: dict, message: str, ans: str) -> str:
    list_tmp = list(info.keys())
    list_tmp.reverse()
    # 优先完全匹配
    if message in list_tmp:
        return random.choice(info[message])
    # 其次正则匹配
    for que in list_tmp:
        try:
            # 找出其中所有的CQ码
            cq_list = re.findall(r'\[(CQ:(\S+?),(\S+?)=(\S+?))]', que)
            que_new = que
            for cq_msg in cq_list:
                que_new = que_new.replace(cq_msg[0], '[' + cq_msg[1] + ']')
            try:
                match = re.match(fr'^{que_new}$', message)
                if match:
                    ans = await replace_message(match, info, que)
                    break
            except:
                pass
        except re.error:
            # 如果que不是re.pattern的形式就跳过
            continue
    return ans


# 删啊删
def delete_img(list_raw: list):
    for str_raw in list_raw:
        # 这里理论上是已经规范好了的图片 | file参数就直接是路径或者base64
        cq_list = re.findall(r'(\[CQ:(\S+?),(\S+?)])', str_raw)
        for cq_code in cq_list:
            cq_split = str(cq_code[2]).split(',')
            image_file_raw = next(filter(lambda x: x.startswith('file='), cq_split), '')
            image_file = image_file_raw.replace('file=', '').replace('file:///', '')
            if 'base64' in image_file:
                # 目前屎山架构base64不好删，不管了
                continue
            img_path = os.path.join(xqa_img_path, image_file)
            try:
                os.remove(img_path)
                logger.info(f'XQA: 已删除图片{image_file}')
            except Exception as e:
                logger.info(f'XQA: 图片{image_file}删除失败：' + str(e))


# 消息分段 | 输入：问题列表 和 初始的前缀消息内容 | 返回：需要发送的完整消息列表（不分段列表里就一个）
def spilt_msg(msg_list: list, init_msg: str) -> list:
    result_list = []
    # 未开启长度限制
    if not IS_SPILT_MSG:
        logger.info('XQA未开启长度限制')
        result_list.append(init_msg + SPLIT_MSG.join(msg_list))
        return result_list

    # 开启了长度限制
    logger.info(f'XQA已开启长度限制，长度限制{MSG_LENGTH}')
    length = len(init_msg)
    tmp_list = []
    for msg_tmp in msg_list:
        if msg_list.index(msg_tmp) == 0:
            msg_tmp = init_msg + msg_tmp
        length += len(msg_tmp)
        # 判断如果加上当前消息后会不会超过字符串限制
        if length < MSG_LENGTH:
            tmp_list.append(msg_tmp)
        else:
            result_list.append(SPLIT_MSG.join(tmp_list))
            # 长度和列表置位
            tmp_list = [msg_tmp]
            length = len(msg_tmp)
    result_list.append(SPLIT_MSG.join(tmp_list))
    return result_list


# 发送消息函数
async def send_result_msg(bot: YuiChyan, ev: CQEvent, result_list):
    # 未开启转发消息
    if not IS_FORWARD:
        logger.info('XQA未开启转发消息，将循环分时直接发送')
        # 循环发送
        for msg in result_list:
            await bot.send(ev, msg)
            await asyncio.sleep(SPLIT_INTERVAL)
        return

    # 开启了转发消息但总共就一条消息，且 IS_DIRECT_SINGER = True
    if IS_DIRECT_SINGER and len(result_list) == 1:
        logger.info('XQA已开启转发消息，但总共就一条消息，将直接发送')
        await bot.send(ev, result_list[0])
        return

    # 开启了转发消息
    logger.info('XQA已开启转发消息，将以转发消息形式发送')
    forward_list = []
    for result in result_list:
        data = {
            "type": "node",
            "data": {
                "name": "你问我答BOT",
                "uin": str(ev.self_id),
                "content": result
            }
        }
        forward_list.append(data)
    await bot.send_group_forward_msg(group_id=ev['group_id'], messages=forward_list)
