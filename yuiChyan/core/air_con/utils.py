import datetime
import json
import os
from typing import Optional

from yuiChyan import CQEvent
from yuiChyan.exception import CommandErrorException, FunctionException

R = 8.314  # 理想气体常数
i = 6  # 多分子气体自由度
K = 273  # 开氏度
gas = 22.4  # 气体摩尔体积
unit_volume = 2  # 每人体积
air_con_off = 0.05  # 关空调后每秒温度变化量
ac_volume = [0.178, 0.213, 0.267]  # 每秒进风量
powers = [5000, 6000, 7500]  # 功率
volume_text = ['低', '中', '高']

ac_central_power = 7500
ac_central_wind_rate = 0.577
ac_central_unit_volume = 100

AIR_CON_HOME = 0
AIR_CON_CENTRAL = 1

required_ranges = {
    'set_temp': (-273, 999999, 26),
    'env_temp': (-273, 999999, 33),
    'wind_rate': (0, 2, 0),
    'balance': (-1000000, 1000000, 0),
    'ac_type': (0, 1, 0)
}


# 确认状态
async def check_status(gid: str, ev: CQEvent, need_on: bool = True) -> dict:
    air_cons = get_group_air_con()
    if gid not in air_cons:
        raise FunctionException(ev, '空调还没装哦~发送“开空调”安装空调')

    air_con = air_cons[gid]
    if need_on and not air_con['is_on']:
        raise FunctionException(ev, '💤你空调没开！')

    return air_con


# 校验传入参数范围
async def check_range(ev: CQEvent, low: int, high: int, errmsg: str, special: Optional[dict] = None) -> int:
    msg = str(ev.message).strip()
    if special and msg[0] in special:
        return special[msg[0]]

    try:
        val = int(msg)
    except:
        raise CommandErrorException(ev, f'命令错误，只能输入{low}至{high}的整数')

    if not low <= val <= high:
        raise CommandErrorException(ev, errmsg)
    return val


# 获取群组空调
def get_group_air_con():
    filename = os.path.join(os.path.dirname(__file__), 'air_con.json')
    if not os.path.isfile(filename):
        write_group_air_con({})
        return {}
    with open(filename, 'r', encoding='utf8') as f:
        _air_cons = json.load(f)
        for gid in _air_cons:
            air_con = _air_cons[gid]
            for item in required_ranges:
                low, high, default = required_ranges[item]
                if (item not in air_con) or (not low <= air_con[item] <= high):
                    air_con[item] = default
    return _air_cons


def sgn(diff):
    return 1 if diff > 0 else -1 if diff < 0 else 0


def write_group_air_con(air_cons):
    filename = os.path.join(os.path.dirname(__file__), 'air_con.json')
    with open(filename, 'w', encoding='utf8') as f:
        # noinspection PyTypeChecker
        json.dump(air_cons, f, ensure_ascii=False, indent=4)


def new_air_con(num_member, set_temp=26, now_temp=33):
    volume = max(num_member * unit_volume, 20)
    return {'is_on': True, 'env_temp': now_temp, 'now_temp': now_temp,
            'set_temp': set_temp, 'last_update': now_second(),
            'volume': volume, 'wind_rate': 0, 'balance': 0, 'ac_type': AIR_CON_HOME}


def now_second():
    return int((datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds())


def get_temp(N, n, setting, prev, T, power):
    direction = sgn(setting - prev)
    threshold = power / (n * 1000 / gas) / (i / 2) / R
    cps = power / (N * 1000 / gas) / (i / 2) / R

    if (abs(setting - prev) - threshold) >= cps * T:
        new_temp = prev + direction * cps * T
    else:
        t1 = max(0, int((abs(setting - prev) - threshold) / cps))
        temp1 = prev + direction * cps * t1
        new_temp = (1 - n / N) ** (T - t1 - 1) * (temp1 - setting) + setting
    return round(new_temp, 1)


def update_air_con(air_con):
    if air_con['is_on']:
        now_temp = air_con['now_temp']
        last_update = air_con['last_update']
        volume = air_con['volume']
        set_temp = air_con['set_temp']
        power = powers[air_con['wind_rate']]
        wind_rate = ac_volume[air_con['wind_rate']]

        new_update = now_second()
        t_delta = new_update - last_update

        ac_type = air_con['ac_type']
        if ac_type == AIR_CON_HOME:
            power = powers[air_con['wind_rate']]
            wind_rate = ac_volume[air_con['wind_rate']]
        elif ac_type == AIR_CON_CENTRAL:
            power = (volume // ac_central_unit_volume + 1) * ac_central_power
            wind_rate = (volume // ac_central_unit_volume + 1) * ac_central_wind_rate
        else:
            pass

        new_temp = get_temp(volume, wind_rate, set_temp, now_temp, t_delta, power)

        air_con['now_temp'] = new_temp
        air_con['last_update'] = new_update

    else:
        env_temp = air_con['env_temp']
        now_temp = air_con['now_temp']
        last_update = air_con['last_update']
        new_update = now_second()
        timedelta = new_update - last_update

        direction = sgn(env_temp - now_temp)
        new_temp = now_temp + direction * timedelta * air_con_off
        if (env_temp - now_temp) * (env_temp - new_temp) < 0:
            new_temp = env_temp

        air_con['now_temp'] = new_temp
        air_con['last_update'] = new_update


def print_air_con(air_con):
    wind_rate = air_con['wind_rate']
    now_temp = air_con['now_temp']
    set_temp = air_con['set_temp']
    env_temp = air_con['env_temp']

    text = f'当前风速{volume_text[wind_rate]}\n' if (air_con['is_on'] and air_con['ac_type'] == AIR_CON_HOME) else ''

    text += f'''
当前设置温度 {set_temp} °C
当前群里温度 {round(now_temp, 1)} °C
当前环境温度 {env_temp} °C'''.strip()

    return text
