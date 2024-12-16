import os

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from plottable import Table

current_dir = os.path.dirname(__file__)
base_dir = os.path.dirname(current_dir)
local_font = os.path.join(base_dir, 'core', 'manager', 'help_res', 'static', 'fonts', 'HarmonyOS_SansSC_Regular.ttf')
# 应用字体
font_prop = font_manager.FontProperties(fname=local_font)
# 字典数据
raw_data = {
    'title': '啊这',
    'show_columns': {
        'id': 'ID',
        'name': '名称',
        'text': '文本'
    },
    'data_list': [
        {
            'id': '1',
            'name': '测试',
            'text': '哈哈',
            'other': '11111'
        },
        {
            'id': '2',
            'name': 'xxx',
            'text': 'yyy'
        }
    ]
}


def create_table(_raw_data):
    show_columns = _raw_data.get('show_columns', {})
    data_list = _raw_data.get('data_list', [])
    # 创建 DataFrame
    df = pd.DataFrame([{col: entry.get(col, None) for col in show_columns.keys()} for entry in data_list])
    # 重命名列
    df.rename(columns=show_columns, inplace=True)
    df = df.reset_index(drop=True)

    # 动态计算图形的大小
    num_rows, num_cols = df.shape
    default_width_per_col = 2  # 每列的默认宽度
    default_height_per_row = 0.5  # 每行的默认高度
    width = num_cols * default_width_per_col  # 根据列数调整宽度
    height = num_rows * default_height_per_row + 2  # 根据行数调整高度，加给标题等等
    fig, ax = plt.subplots(figsize=(width, height))

    # 标题
    title = _raw_data.get('title', None)
    if title:
        ax.set_title(title, fontproperties=font_prop, fontsize=18)

    # 文本属性
    text_props = {
        'fontsize': 15,
        'fontproperties': font_prop,
        'ha': 'center',
        'va': 'center'
    }
    # 美化展示
    Table(
        df,
        textprops=text_props,
        row_dividers=False,
        odd_row_color="#FFDFDF",
        even_row_color="#E0F6FF"
    )
    # 显示表格
    plt.show()


create_table(raw_data)
