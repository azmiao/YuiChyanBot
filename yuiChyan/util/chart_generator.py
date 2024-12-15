import matplotlib.pyplot as plt
import pandas as pd
from plottable import Table

# 假设这是你的字典数据
data = {
    'Name': ['Alice', 'Bob', 'Charlie'],
    'Age': [25, 30, 35],
    'City': ['New York', 'Los Angeles', 'Chicago']
}

# 将字典转换为DataFrame
df = pd.DataFrame(data)
fig, ax = plt.subplots(figsize=(9, 3))

text_props = {
    'fontsize': 15,
    'fontname': 'Arial',
    'ha': 'center',
    'va': 'center'
}

Table(
    df,
    textprops=text_props,
    row_dividers=False,
    odd_row_color="#FFDFDF",
    even_row_color="#E0F6FF"
)

# 显示表格
plt.show()