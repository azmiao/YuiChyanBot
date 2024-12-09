from yuiChyan import FunctionException, ThrowException
from yuiChyan.service import Service
from yuiChyan.util import translate

sv = Service('base_func')


# 翻译
@sv.on_prefix('翻译', only_to_me=True)
async def translate_text(bot, ev):
    messages = str(ev.message).strip()
    text_list = messages.split(' ', 2)
    try:
        _, _, _ = text_list[0], text_list[1], text_list[2]
    except:
        raise FunctionException(ev, '翻译指令错误! \n示例：翻译 en zh 文本')

    try:
        msg = await translate(text_list[2], text_list[0], text_list[1])
        await bot.send(ev, msg)
    except ThrowException as e:
        raise FunctionException(ev, e.message)
    except Exception as e:
        raise FunctionException(ev, f'翻译失败，未知原因{str(e)}')
