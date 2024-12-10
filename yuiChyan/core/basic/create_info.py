import re


async def get_create_msg(bot, all_text, group_id, is_stranger):
    # 替换at相关的信息
    at_text_list = re.findall(r'\[CQ:at,qq=.+?] ', all_text)
    for each_at in at_text_list:
        each_at_tmp = str(each_at)
        each_at_tmp = re.sub(r'] ', '', each_at_tmp)
        each_at_tmp = re.sub(r'\[CQ:at,qq=', '', each_at_tmp)
        if not is_stranger:
            try:
                at = await bot.get_group_member_info(group_id=group_id, user_id=int(each_at_tmp))
            except Exception as _:
                msg = ['QQ号错误!被@的人不在本群里']
                return msg
        else:
            at = await bot.get_stranger_info(user_id=int(each_at_tmp))
        at_nickname = '@' + at['nickname']
        replace_text = fr'\{each_at}'
        all_text = re.sub(replace_text, at_nickname, str(all_text))
    text_list = all_text.split('|')
    forward_msg_list = []
    for each_text in text_list:
        info_list = each_text.split(':', 1)
        sender_id = info_list[0]
        raw_msg = info_list[1]
        # print(raw_msg)
        if not is_stranger:
            try:
                sender = await bot.get_group_member_info(group_id=group_id, user_id=sender_id)
            except Exception as _:
                msg = ['QQ号错误!本群里没有这个人哦']
                return msg
        else:
            sender = await bot.get_stranger_info(user_id=sender_id)
        nickname = sender['nickname']
        data = {
            "type": "node",
            "data": {
                "name": nickname,
                "uin": sender_id,
                "content": raw_msg
            }
        }
        forward_msg_list.append(data)
    return forward_msg_list
