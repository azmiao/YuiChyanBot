
from .apis import Youdao

# 默认支持的语言
trans_dict = {
    'en': '英语',
    'zh': '中文',
    'ar': '阿拉伯语',
    'ru': '俄语',
    'fr': '法语',
    'de': '德语',
    'es': '西班牙语',
    'pt': '葡萄牙语',
    'it': '意大利语',
    'ja': '日语',
    'ko': '韩语',
    'nl': '荷兰语',
    'vi': '越南语',
    'id': '印尼语'
}
# 翻译器
_youdao = Youdao()

# 翻译 | 目前只有有道引擎
async def translate(text: str, from_: str = 'auto', to_: str = 'zh') -> str:
    error_msg = ' - 目前支持的语言有：\n' + '\n'.join([f'{key}: {value}' for key, value in trans_dict.items()])
    assert from_ in trans_dict, f'源语言 [{from_}] 不存在\n{error_msg}'
    assert to_ in trans_dict, f'目标语言 [{to_}] 不存在\n{error_msg}'
    return await _youdao.youdao_api(text, from_, to_)
