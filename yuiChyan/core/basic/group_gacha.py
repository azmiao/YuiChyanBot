import json
import os
import random

group_gacha_config = os.path.join(os.path.dirname(__file__), 'group_gacha.json')
if not os.path.exists(group_gacha_config):
    with open(group_gacha_config, 'w', encoding='utf-8') as f:
        # noinspection PyTypeChecker
        json.dump({}, f, indent=4, ensure_ascii=False)


# 创建抽奖
async def create_group_gacha(group_id: str, name: str, number: int):
    with open(group_gacha_config, 'r', encoding='utf-8') as file:
        data = json.load(file)
    gacha_get = data.get(group_id, [])
    if group_id in data:
        gacha_name_list = [x.get(name, '') for x in gacha_get]
        # 目前只支持一个
        return '本群当前已有进行中的抽奖，请先结束：\n' + '\n'.join(gacha_name_list)
    gacha = {
        'name': name,
        'number': number,
        'members': []
    }
    gacha_get.append(gacha)
    data[group_id] = gacha_get
    with open(group_gacha_config, 'w', encoding='utf-8') as file:
        # noinspection PyTypeChecker
        json.dump(data, file, indent=4, ensure_ascii=False)
    return '本群创建抽奖[' + name + ']成功！请发送 参与抽奖 来参加本抽奖'


# 结束抽奖
async def finish_group_gacha(group_id: str, name: str):
    with open(group_gacha_config, 'r', encoding='utf-8') as file:
        data = json.load(file)
    if group_id not in data:
        return '本群没有正在进行的抽奖哦~'
    gacha_get = data.get(group_id, [])
    gacha_name_dict = {x.get('name', ''): x for x in gacha_get}
    if name not in gacha_name_dict:
        return '本群没有找到名为[' + name + ']抽奖哦~'

    gacha = gacha_name_dict.get(name, {})
    sample = list(random.sample(gacha.get('members', []), gacha.get('number', 1)))
    # 删除抽奖
    data.pop(group_id)
    with open(group_gacha_config, 'w', encoding='utf-8') as file:
        # noinspection PyTypeChecker
        json.dump(data, file, indent=4, ensure_ascii=False)
    return '🎉恭喜以下小伙伴中奖了：' + str(sample)


# 参与抽奖
async def join_group_gacha(group_id: str, user_id: int):
    with open(group_gacha_config, 'r', encoding='utf-8') as file:
        data = json.load(file)
    if group_id not in data:
        return '本群没有正在进行的抽奖哦~'
    gacha_get = data.get(group_id, [])
    # 目前只支持一个
    gacha = gacha_get[0]
    member_list = gacha.get('members', [])
    if user_id in member_list:
        return '您已经参加过该抽奖了哦~'
    member_list.append(user_id)
    gacha['members'] = member_list
    gacha_get = [gacha]
    data[group_id] = gacha_get
    with open(group_gacha_config, 'w', encoding='utf-8') as file:
        # noinspection PyTypeChecker
        json.dump(data, file, indent=4, ensure_ascii=False)
    return '用户[' + str(user_id) + ']成功参与抽奖~'


# 查询抽奖
async def query_group_gacha(group_id: str):
    with open(group_gacha_config, 'r', encoding='utf-8') as file:
        data = json.load(file)
    if group_id not in data:
        return '本群没有正在进行的抽奖哦~'
    gacha_get = data.get(group_id, [])

    msg = '本群正在进行的抽奖：\n'
    msg += '\n'.join([
        f'- {x.get("name", "")}\n' +
        f'  抽奖个数：{str(x.get("number", 1))}\n' +
        f'  参加用户：{str(x.get("members", []))}'
        for x in gacha_get
    ])
    return msg
