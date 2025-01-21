from yuiChyan.service import Service
from .utils import write_group_air_con, update_air_con, new_air_con, print_air_con, check_range, \
    check_status, get_group_air_con
from yuiChyan import YuiChyan, CQEvent

sv = Service('air_con', help_cmd='空调帮助')

ac_type_text = ['家用空调', '中央空调']
AIR_CON_HOME = 0
AIR_CON_CENTRAL = 1
air_cons = get_group_air_con()


@sv.on_match('开空调')
async def air_con_on(bot: YuiChyan, ev: CQEvent):
    gid = ev.group_id

    if gid not in air_cons:
        g_info = await bot.get_group_info(group_id=gid)
        g_count = g_info['member_count']
        air_con = new_air_con(num_member=g_count)
        air_cons[gid] = air_con
        await bot.send(ev, '❄空调已安装~')
    else:
        air_con = air_cons[gid]
        if air_con['is_on']:
            await bot.send(ev, '❄空调开着呢！')
            return

    update_air_con(air_con)
    air_con['is_on'] = True
    msg = print_air_con(air_con)
    write_group_air_con(air_cons)
    await bot.send(ev, '❄哔~空调已开\n' + msg)


@sv.on_match('关空调')
async def air_con_off(bot: YuiChyan, ev: CQEvent):
    gid = ev.group_id

    air_con = await check_status(gid, ev)
    if air_con is None:
        return

    update_air_con(air_con)
    air_con['is_on'] = False
    msg = print_air_con(air_con)
    write_group_air_con(air_cons)
    await bot.send(ev, '💤哔~空调已关\n' + msg)


@sv.on_match('当前温度')
async def air_con_now(bot: YuiChyan, ev: CQEvent):
    gid = ev.group_id

    air_con = await check_status(gid, ev, need_on=False)
    if air_con is None:
        return

    air_con = air_cons[gid]
    update_air_con(air_con)
    msg = print_air_con(air_con)
    write_group_air_con(air_cons)

    if not air_con['is_on']:
        msg = '💤空调未开启\n' + msg
    else:
        msg = '❄' + msg

    await bot.send(ev, msg)


@sv.on_prefix(('设置温度', '设定温度'))
async def set_temp(bot: YuiChyan, ev: CQEvent):
    gid = ev.group_id

    air_con = await check_status(gid, ev)
    if air_con is None:
        return

    _set_temp = await check_range(ev, -273, 999999, '只能设置-273-999999°C喔')
    if _set_temp is None:
        return

    if _set_temp == 114514:
        await bot.send(ev, '这么臭的空调有什么装的必要吗')
        return

    update_air_con(air_con)
    air_con['set_temp'] = _set_temp
    msg = print_air_con(air_con)
    write_group_air_con(air_cons)
    await bot.send(ev, '❄' + msg)


@sv.on_prefix(('设置风速', '设定风速', '设置风量', '设定风量'))
async def set_wind_rate(bot: YuiChyan, ev: CQEvent):
    gid = ev.group_id

    air_con = await check_status(gid, ev)
    if air_con is None:
        return

    if air_con['ac_type'] != AIR_CON_HOME:
        await bot.send(ev, '只有家用空调能调风量哦！')
        return

    wind_rate = await check_range(ev, 1, 3, '只能设置1/2/3档喔',
                                  {'低': 1, '中': 2, '高': 3})
    if wind_rate is None:
        return

    update_air_con(air_con)
    air_con['wind_rate'] = wind_rate - 1
    msg = print_air_con(air_con)
    write_group_air_con(air_cons)
    await bot.send(ev, '❄' + msg)


@sv.on_prefix(('设置环境温度', '设定环境温度'))
async def set_env_temp(bot: YuiChyan, ev: CQEvent):
    gid = ev.group_id

    air_con = await check_status(gid, ev, need_on=False)
    if air_con is None:
        return

    env_temp = await check_range(ev, -273, 999999, '只能设置-273-999999°C喔')
    if env_temp is None:
        return

    if env_temp == 114514:
        await bot.send(ev, '这么臭的空调有什么装的必要吗')
        return

    air_con = air_cons[gid]
    update_air_con(air_con)
    air_con['env_temp'] = env_temp
    msg = print_air_con(air_con)
    write_group_air_con(air_cons)

    if not air_con['is_on']:
        msg = '💤空调未开启\n' + msg
    else:
        msg = '❄' + msg

    await bot.send(ev, msg)


@sv.on_match(('空调类型',))
async def show_air_con_type(bot: YuiChyan, ev: CQEvent):
    gid = ev.group_id

    air_con = await check_status(gid, ev, need_on=False)
    if air_con is None:
        return

    air_con = air_cons[gid]
    ac_type = air_con['ac_type']

    msg = f'当前安装了{ac_type_text[ac_type]}哦~'
    await bot.send(ev, msg)


@sv.on_match(('升级空调', '空调升级'))
async def upgrade_air_con(bot: YuiChyan, ev: CQEvent):
    gid = ev.group_id

    air_con = await check_status(gid, ev, need_on=False)
    if air_con is None:
        return

    air_con = air_cons[gid]
    ac_type = air_con['ac_type']
    if ac_type == len(ac_type_text) - 1:
        await bot.send(ev, '已经是最高级的空调啦！')
        return

    update_air_con(air_con)
    ac_type += 1
    air_con['ac_type'] = ac_type
    msg = print_air_con(air_con)
    write_group_air_con(air_cons)
    msg = f'❄已升级至{ac_type_text[ac_type]}~\n' + msg
    await bot.send(ev, msg)


@sv.on_match(('降级空调', '空调降级'))
async def downgrade_air_con(bot: YuiChyan, ev: CQEvent):
    gid = ev.group_id

    air_con = await check_status(gid, ev, need_on=False)
    if air_con is None:
        return

    air_con = air_cons[gid]
    ac_type = air_con['ac_type']
    if ac_type == 0:
        await bot.send(ev, '已经是最基础级别的空调啦！')
        return

    update_air_con(air_con)
    ac_type -= 1
    air_con['ac_type'] = ac_type
    msg = print_air_con(air_con)
    write_group_air_con(air_cons)
    msg = f'❄已降级至{ac_type_text[ac_type]}~\n' + msg
    await bot.send(ev, msg)
