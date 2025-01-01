import asyncio
import json
import os
import time
from asyncio import Lock
from math import log
from random import random
from typing import List

import httpx

from yuiChyan.service import Service
from .. import chara

sv = Service('pcr-arena')

# 查询锁
query_lock = Lock()
# 路径
cur_path = os.path.dirname(__file__)

buffer_path = os.path.join(cur_path, 'buffer')
os.makedirs(buffer_path, exist_ok=True)

buffer_json_path = os.path.join(buffer_path, 'buffer.json')
if not os.path.exists(buffer_json_path):
    with open(buffer_json_path, 'w', encoding='utf8') as f:
        # noinspection PyTypeChecker
        json.dump({}, f, ensure_ascii=False)

config_path = os.path.join(cur_path, 'pcr_config.json')
with open(config_path, 'r', encoding='utf-8') as _config:
    _data = json.load(_config)
AUTH_KEY: str = _data.get('AUTH_KEY', '')


# ID列表转字符串
def id_list2str(id_list: list) -> str:  # [1001, 1002, 1018, 1052, 1122] -> "10011002101810521122"
    return ''.join([str(x) for x in id_list])


# ID字符串转列表
def id_str2list(id_str: str) -> List[int]:  # 20~21位str
    if len(id_str) not in [20, 21]:
        return []
    return [int(id_str[x:x + 4]) for x in range(0, 20, 4)]


# 查询近似解
def findApproximateTeamResult(id_list):
    if len(id_list) == 4:
        id_list.append(1000)
    if len(id_list) != 5:
        raise
    sv.logger.info(f'查询近似解：{list(sorted(id_list))}')
    result = []
    with open(buffer_json_path, 'r', encoding="utf-8") as fp:
        buffer = json.load(fp)
    for buffer_id_str in buffer:  # "100110021018105211222"
        if len(buffer_id_str) != 21:
            continue
        if buffer_id_str[-1] not in ["1", "2"]:
            continue
        buffer_id_list = id_str2list(buffer_id_str)  # [1001, 1002, 1018, 1052, 1122]
        if len(set(buffer_id_list) & set(id_list)) >= 4:
            pa = os.path.join(cur_path, f'buffer/{buffer_id_str}.json')
            if os.path.exists(pa):
                with open(pa, 'r', encoding="utf-8") as fp:
                    result += json.load(fp)

    sv.logger.info(f'    共有{len(result)}条记录')
    render = result2render(result, "approximation", id_list)
    if len(render) > 10:
        render = list(sorted(render, key=lambda x: x.get("val", -100), reverse=True))[:10]
    return render


# 计算阵容推荐度权值
def calculateVal(record) -> float:
    up_vote = int(record["up"])
    down_vote = int(record["down"])
    val_1 = up_vote / (down_vote + up_vote + 0.0001) * 2 - 1  # 赞踩比占比 [-1, 1]
    val_2 = log(up_vote + down_vote + 0.01, 100)  # 置信度占比（log(100)）[-1,+inf]
    return val_1 + val_2 + random() / 1000  # 阵容推荐度权值


# 生成结果图片
def result2render(result, team_type="normal", id_list=None):
    """
    team_type:
    "normal":正常查询的阵容
    "approximation":根据近似解推荐的阵容 由id_list字段自动计算uid_4_1 uid_4_2

    "approximation uid_4_1 uid_4_2":根据近似解推荐的阵容 原查询角色uid_4_1 被替换为 近似查询角色uid_4_2 # 本函数不支持
    "frequency":根据频率推荐的阵容 # 本函数不支持
    """
    if id_list is None:
        id_list = []
    render = []
    for entry in result:
        # atk up down val: 都一样
        # team_type: approximation要手动算 normal直接贴
        write_type = team_type
        if team_type == "approximation":
            try:
                entry_id_list = [c["id"] // 100 for c in entry["def"]]
                uid_4_1 = list(set(id_list) - set(entry_id_list))[0]
                uid_4_2 = list(set(entry_id_list) - set(id_list))[0]
                write_type = f'approximation {uid_4_1} {uid_4_2}'
            except:
                pass

        render.append({
            "atk": [chara.get_chara_by_id(c["id"] // 100, c["star"], c["equip"]) for c in entry["atk"]],
            "up": entry["up"],
            "down": entry["down"],
            "val": calculateVal(entry),
            "team_type": write_type
        })

    return render


# 实际查询
async def do_query(id_list, region=1, try_cnt=1):
    if len(id_list) < 4 or len(id_list) > 5:
        return []
    if len(id_list) == 4:
        return findApproximateTeamResult(id_list)

    defense = id_list
    key = ''.join([str(x) for x in sorted(defense)]) + str(region)
    if try_cnt <= 1:
        print()
    if try_cnt != -1:
        sv.logger.info(f'查询阵容：{key} try_cnt={try_cnt}')
    else:
        sv.logger.info(f'查询阵容：{key} 仅使用缓存')
    value = int(time.time())

    with open(buffer_json_path, 'r', encoding="utf-8") as fp:
        buffer = json.load(fp)

    if ((value - buffer.get(key, 0) < 3600 * 24 * 5) and
            (os.path.exists(os.path.join(cur_path, f'buffer', '{key}.json')))):  # 5天内查询过 直接返回
        sv.logger.info(f'    存在本服({region})近缓存，直接使用')
        with open(os.path.join(cur_path, f'buffer/{key}.json'), 'r', encoding="utf-8") as fp:
            result = json.load(fp)
    else:
        degrade_result = None
        if try_cnt <= 1:
            if os.path.exists(os.path.join(cur_path, f'buffer/{key}.json')):
                sv.logger.info(f'    存在本服({region})远缓存，作为降级备用')
                with open(os.path.join(cur_path, f'buffer/{key}.json'), 'r', encoding="utf-8") as fp:
                    degrade_result = json.load(fp)
            else:
                sv.logger.info(f'    不存在本服({region})缓存，查找它服缓存')
                query_seq = {
                    1: [3, 4, 2],  # 全服查询顺序为[台,日,B]
                    2: [1, 3, 4],  # B服查询顺序为[全,台,日]
                    3: [1, 2, 4],  # 台服查询顺序为[全,B,日]
                    4: [1, 3, 2]  # 日服查询顺序为[全,台,B]
                }

                query_seq = query_seq.get(region, [])
                for other_region in query_seq:
                    other_key = ''.join([str(x) for x in sorted(defense)]) + str(other_region)
                    if os.path.exists(os.path.join(cur_path, f'buffer/{other_key}.json')):
                        sv.logger.info(f'        存在它服({other_region})缓存，作为降级备用')
                        with open(os.path.join(cur_path, f'buffer/{other_key}.json'), 'r', encoding="utf-8") as fp:
                            degrade_result = json.load(fp)
                        break
                else:
                    sv.logger.info(f'        不存在它服缓存')
        if try_cnt == -1:
            result = degrade_result if degrade_result else []
        else:
            id_list_query = [x * 100 + 1 for x in id_list]
            header = {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/78.0.3904.87 Safari/537.36",
                "authorization": AUTH_KEY,
            }
            payload = {
                "_sign": "a",
                "def": id_list_query,
                "nonce": "a",
                "page": 1,
                "sort": 1,
                "ts": int(time.time()),
                "region": region,
            }

            query_again = False
            should_sleep = False
            if query_lock.locked():
                should_sleep = True  # 旨在不要连续调用api
            async with query_lock:
                if should_sleep:
                    await asyncio.sleep(1)
                try:
                    async with httpx.AsyncClient() as session:
                        resp = await session.post(
                            "https://api.pcrdfans.com/x/v1/search",
                            headers=header,
                            json=payload,
                            timeout=5,
                        )
                    res = resp.json()
                    sv.logger.info("    服务器有返回")
                    if res["code"]:
                        sv.logger.info(f'        服务器报错：返回值{res["code"]}')
                        raise Exception()
                    result = res["data"]["result"]
                except:
                    if degrade_result:
                        sv.logger.info("    查询失败，使用缓存")
                        result = degrade_result
                    else:
                        sv.logger.info("    查询失败，查询近似解")
                        return findApproximateTeamResult(id_list)
                else:
                    sv.logger.info(f'    查询成功，共有{len(result)}条结果')
                    if len(result):
                        sv.logger.info("        保存结果至缓存库")
                        buffer[key] = value

                        with open(buffer_json_path, 'w', encoding="utf-8") as fp:
                            # noinspection PyTypeChecker
                            json.dump(buffer, fp, ensure_ascii=False, indent=4)

                        homework_path = os.path.join(cur_path, f'buffer/{key}.json')
                        with open(homework_path, 'w', encoding="utf-8") as fp:
                            # noinspection PyTypeChecker
                            json.dump(result, fp, ensure_ascii=False, indent=4)
                    else:
                        if degrade_result:
                            sv.logger.info(f'    使用缓存')
                            result = degrade_result
                        else:
                            sv.logger.info(f'    查询近似解')
                            return findApproximateTeamResult(id_list)

            if query_again:
                await asyncio.sleep(1)
                return await do_query(id_list, region, try_cnt + 1)

    render = result2render(result)
    sv.logger.info(f'    共有{len(render)}条结果')
    return render
