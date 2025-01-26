import os
import re
from typing import List, Optional, Tuple
from urllib import request

from aiocqhttp import Event as CQEvent

from yuiChyan import FunctionException, get_bot


# 解析第一张图片数据
async def parse_single_image(ev: CQEvent, str_raw: str) -> (str, str, str):
    cq_code = re.search(r'(\[CQ:image,(\S+?)])', str_raw)
    if not cq_code:
        raise FunctionException(ev, f'无法从消息中获取图片，请检查')
    _, image_file, image_file_name, image_url = await extract_file(cq_code[1])
    return image_file, image_file_name, image_url


# 解析所有图片数据
async def parse_all_image(ev: CQEvent, str_raw: str) -> List[Tuple[str, str, str]]:
    cq_list = re.findall(r'(\[CQ:image,(\S+?)])', str_raw)
    if not cq_list:
        raise FunctionException(ev, f'无法从消息中获取图片，请检查')
    cq_code_list = []
    for cq_code in cq_list:
        _, image_file, image_file_name, image_url = await extract_file(cq_code[1])
        cq_code_list.append((image_file, image_file_name, image_url))
    return cq_code_list


# 获取真实URL
async def get_real_url(ev: Optional[CQEvent], image_file: str) -> str:
    try:
        img_data = await get_bot().get_image(file=image_file)
    except Exception as e:
        raise FunctionException(ev, f'调用get_image接口查询图片{image_file}出错:{str(e)}')
    return img_data['url']  # type: ignore


# 保存图片
async def save_image(ev: Optional[CQEvent],
                     image_file: str, image_name: str, image_url: Optional[str], image_path: str) -> str:
    # 如果没有image_url，说明是GO-CQ的客户端，重新取一下图片URL
    image_url = image_url if image_url else await get_real_url(ev, image_file)

    # 开始下载图片
    try:
        if not os.path.isfile(image_path):
            request.urlretrieve(url=image_url, filename=image_path)
    except Exception as e:
        raise FunctionException(ev, f'从{image_url}下载图片{image_name}出错:{str(e)}')
    return image_name


# 根据CQ中的"xxx=xxxx,yyy=yyyy,..."提取出file和file_name还有url
async def extract_file(cq_code_str: str) -> (bool, str, str, str):
    """
    根据CQ中的"xxx=xxxx,yyy=yyyy,..."提取出file和file_name还有url

    :param cq_code_str: 原始CQ中提取的"xxx=xxxx,yyy=yyyy,..."

    :return: is_base64: 是否是base64编码 |
    image_file: file参数 |
    image_file_name: 文件名，GO-CQ没有这个参数因此和image_file保持一致，LLOneBot为filename参数，NapCat为file_unique参数，其他为file_id参数 |
    image_url: 图片URL，GO-CQ的URL不正确不建议使用所以这里会返回None，LLOneBot 和 NapCat 有这个参数直接返回对应URL
    """
    # 解析所有CQ码参数
    cq_split = cq_code_str.split(',')

    # 拿到file参数 | 如果是单文件名：原始CQ | 如果是带路径的文件名：XQA本地已保存的图片，需要获取到单文件名
    image_file_raw = next(filter(lambda x: x.startswith('file='), cq_split), '')
    file_data = image_file_raw.replace('file=', '')

    # base64就不需要花里胡哨的代码了 | 直接返回
    if 'base64://' in file_data:
        return True, file_data, None, None

    # 文件参数
    image_file = file_data.split('\\')[-1].split('/')[-1] if 'file:///' in file_data else file_data

    # 文件名参数：对于LLOneBot | 需要取 filename 参数做文件名
    image_file_name = (next(filter(lambda x: x.startswith('filename='), cq_split), '')
                       .replace('filename=', ''))
    # 文件名参数：对于NapCat | 需要取 file_unique 参数做文件名
    image_file_name = (next(filter(lambda x: x.startswith('file_unique='), cq_split), '')
                       .replace('file_unique=', '')) if not image_file_name else image_file_name
    # 文件名参数：对于其他可能的协议 | 需要取 file_id 参数做文件名
    image_file_name = (next(filter(lambda x: x.startswith('file_id='), cq_split), '')
                       .replace('file_id=', '')) if not image_file_name else image_file_name

    # 如果有文件名参数：LLOneBot 和 NapCat
    if image_file_name:
        # 文件URL参数：LLOneBot 和 NapCat 有这个参数 | Go-CQ也有但不使用(URL缓存可能有问题)
        image_url = (next(filter(lambda x: x.startswith('url='), cq_split), '').replace('url=', ''))
    else:
        image_url = None
        # 文件名参数：对于GO-CQ | image_file 和 image_file_name 一致即可
        image_file_name = image_file
    # 文件名参数：替换特殊字符为下划线
    image_file_name = re.sub(r'[\\/:*?"<>|{}]', '_', image_file_name)
    # 文件名参数：最后10个字符里没有点号 | 补齐文件拓展名
    image_file_name = image_file_name if '.' in image_file_name[-10:] else image_file_name + '.png'

    return False, image_file, image_file_name, image_url
