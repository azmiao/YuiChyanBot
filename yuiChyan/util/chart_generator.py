import base64
import io

import matplotlib.pyplot as plt
import pandas as pd
from plottable import Table

from yuiChyan.resources import font_prop


# 数据样例
# raw_data = {
#     'title': '啊这',
#     'index_column': 'id',
#     'show_columns': {
#         'id': 'ID',
#         'name': '名称',
#         'text': '文本'
#     },
#     'data_list': [
#         {
#             'id': '1',
#             'name': '测试',
#             'text': '哈哈'
#         }
#     ]
# }

# 创建表格
async def create_table(_raw_data: dict) -> plt.Figure:
    show_columns = _raw_data.get('show_columns', {})
    data_list = _raw_data.get('data_list', [])
    # 创建 DataFrame
    df = pd.DataFrame([{col: entry.get(col, None) for col in show_columns.keys()} for entry in data_list])
    # 手动设置索引列
    df.set_index(_raw_data.get('index_column', ''), inplace=True)
    # 重命名列
    df.rename(columns=show_columns, inplace=True)

    # 动态计算图形的大小
    num_rows, num_cols = df.shape
    default_width_per_col = 2  # 每列的默认宽度
    default_height_per_row = 0.5  # 每行的默认高度
    width = num_cols * default_width_per_col  # 根据列数调整宽度
    height = num_rows * default_height_per_row + 1.5  # 根据行数调整高度，加给标题等等
    fig, ax = plt.subplots(figsize=(width, height))

    # 去掉x轴和y轴
    ax.axis('off')
    # 标题
    title = _raw_data.get('title', '')
    if title:
        ax.set_title(title, fontproperties=font_prop, fontsize=18, fontweight='bold', color='#302828')

    # 文本属性
    text_props = {
        'fontsize': 15,
        'fontproperties': font_prop,
        'ha': 'center',
        'va': 'center',
        'color': '#8B4513'
    }
    # 美化展示
    Table(
        df,
        ax=ax,
        textprops=text_props,
        row_dividers=False,
        odd_row_color='#FFE1E1',
        even_row_color='#E0F6FF'
    )
    # 自动调整布局
    plt.tight_layout(pad=2.0)
    return fig


# 保存 fig 为 PNG 文件
async def save_fig_as_image(fig: plt.Figure, file_path: str):
    fig.savefig(file_path, format='png', bbox_inches='tight')
    plt.close(fig)


# 将 fig 转换为 base64 字符串
async def fig_to_base64(fig: plt.Figure) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64
