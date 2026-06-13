'''
这段代码通过读取两个 CSV 文件（分别包含光谱数据和水分含量数据），
提取所需列，然后使用种子编号作为键进行合并，
最终生成一个包含光谱数据和水分含量数据的完整数据集，
并将其保存为一个新的 CSV 文件。
这样可以方便后续对这些数据进行综合分析和处理。
'''

import pandas as pd

# 读取合并后的光谱数据
spectra_file = r"/home/x45880/桌面/bgz/after_drying/mix_data/FS-17_down(lack_1B_all_&_2E_all).csv"
spectra_df = pd.read_csv(spectra_file)

# 读取水分含量数据
moisture_file = r"/home/x45880/桌面/bgz/after_drying/mix_data/combined_moisture_content(lack_1B_all_&_2E_all).csv"
moisture_df = pd.read_csv(moisture_file)

# 提取种子编号和种子水分含量列
moisture_df = moisture_df[['Seed_ID', 'Moisture_Content']]

# 合并数据集
# 使用种子编号作为键进行合并
complete_dataset = pd.merge(spectra_df, moisture_df, on='Seed_ID', how='inner')

# 查看合并后的数据集
print(complete_dataset.head())

# 保存完整的数据集
output_file = r"/home/x45880/桌面/bgz/after_drying/final_data/FS-17_down_complete_dataset(lack_1B_all_&_2E_all).csv"
complete_dataset.to_csv(output_file, index=False)
print(f"完整的数据集已保存为 {output_file}")
