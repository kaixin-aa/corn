'''
这段代码通过遍历多个 Excel 文件，将它们中的水分含量数据合并成一个 DataFrame，
并对其中的种子编号进行重新编号，
最终将合并后的数据保存为一个新的 CSV 文件。
这样可以方便后续对所有玉米种子的水分含量数据进行统一分析和处理。
'''

import pandas as pd

# 定义水分含量数据文件路径(改成自己的文件路径)
moisture_files = [
    r"/home/x45880/Elements SE/caoge/光谱数据/第一批/A组_64粒无处理/20250727.xlsx",
    r"/home/x45880/Elements SE/caoge/光谱数据/第一批/C组1-32(10ml_12h)_33-64(15ml_12h)/20250801.xlsx",
    r"/home/x45880/Elements SE/caoge/光谱数据/第一批/D组1-32(5ml_24h)_33-64(20ml_24h)/20250803.xlsx",
    r"/home/x45880/Elements SE/caoge/光谱数据/第一批/E组1-32(10ml_24h)_33-64(15ml_24h)/20250805.xlsx",

    r"/home/x45880/Elements SE/caoge/光谱数据/第二批/A组_64粒（无处理）/20250808.xlsx",
    r"/home/x45880/Elements SE/caoge/光谱数据/第二批/B组_1-32(5ml_12h)_33-64(20ml_12h)/20250810.xlsx",
    r"/home/x45880/Elements SE/caoge/光谱数据/第二批/C组_1-32(10ml_12h)_33-64(15ml_12h)/20250813.xlsx",
    r"/home/x45880/Elements SE/caoge/光谱数据/第二批/D组_1-32(5ml_24h)_33-64(20ml_24h)/20250815.xlsx",
    #r"/home/x45880/Elements SE/caoge/光谱数据/第二批/E组_1-32(10ml_24h)_33-64(15ml_24h)/20250817.xlsx"
    
]

# 初始化一个空的 DataFrame 用于存储合并后的水分含量数据
combined_moisture_df = pd.DataFrame()

# 初始化种子编号计数器
seed_id_counter = 1

# 遍历所有水分含量数据文件路径
for file_path in moisture_files:
    # 读取当前文件，跳过第一行
    df = pd.read_excel(file_path, header=None, skiprows=1, usecols="A:D")
    
    # 为列设置名称
    df.columns = ['Seed_ID', 'M1', 'M2', 'Moisture_Content']
    
    # 提取种子编号和种子水分含量列
    df = df[['Seed_ID', 'Moisture_Content']]
    
    # 将水分含量列保留四位小数
    df['Moisture_Content'] = df['Moisture_Content'].round(4)
    
    # 重新编号种子
    df['Seed_ID'] = range(seed_id_counter, seed_id_counter + len(df))
    
    # 更新种子编号计数器
    seed_id_counter += len(df)
    
    # 检查是否是第一个文件，如果是，则直接赋值
    if combined_moisture_df.empty:
        combined_moisture_df = df
    else:
        # 否则，将当前文件的数据追加到 combined_moisture_df 中
        combined_moisture_df = pd.concat([combined_moisture_df, df], ignore_index=True)

# 查看合并后的水分含量数据
print(combined_moisture_df.head())


# 保存合并后的水分含量数据
output_moisture_file = r"/home/x45880/桌面/bgz/after_drying/mix_data/combined_moisture_content(lack_1B_all_&_2E_all).csv"
combined_moisture_df.to_csv(output_moisture_file, index=False)
print(f"合并后的水分含量数据已保存为 {output_moisture_file}")