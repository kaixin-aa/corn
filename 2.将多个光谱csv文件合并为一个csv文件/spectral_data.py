'''
这段代码的主要目的是：
读取多个 CSV 文件中的数据。
对这些数据中的种子编号进行重新编号，确保编号是连续且唯一的。
将所有数据合并到一个单一的 DataFrame 中。
保存合并后的数据到一个新的 CSV 文件中。
这样可以方便地处理和分析来自多个文件的数据，同时保持数据的一致性和完整性。
'''

import pandas as pd
import os

# 定义了一个包含多个 CSV 文件路径的列表 file_paths（这里替换为自己的文件路径）
file_paths = [
    r"/home/x45880/Elements SE/caoge/光谱数据/第一批/A组_64粒无处理/20250729（烘干后）/FS-17/1-32_down/1-32_down_ref_masked_spectra.csv",
    r"/home/x45880/Elements SE/caoge/光谱数据/第一批/A组_64粒无处理/20250729（烘干后）/FS-17/33-64_down/33-64_down_ref_masked_spectra.csv",
    r"/home/x45880/Elements SE/caoge/光谱数据/第一批/C组1-32(10ml_12h)_33-64(15ml_12h)/20250803（烘干后）/FS-17/1-32_down/1-32_down_ref_masked_spectra.csv",
    r"/home/x45880/Elements SE/caoge/光谱数据/第一批/C组1-32(10ml_12h)_33-64(15ml_12h)/20250803（烘干后）/FS-17/33-64_down/33-64_down_ref_masked_spectra.csv",
    r"/home/x45880/Elements SE/caoge/光谱数据/第一批/D组1-32(5ml_24h)_33-64(20ml_24h)/20250805（烘干后）/FS-17/1-32_down/1-32_down_ref_masked_spectra.csv",
    r"/home/x45880/Elements SE/caoge/光谱数据/第一批/D组1-32(5ml_24h)_33-64(20ml_24h)/20250805（烘干后）/FS-17/33-64_down/33-64_down_ref_masked_spectra.csv",
    r"/home/x45880/Elements SE/caoge/光谱数据/第一批/E组1-32(10ml_24h)_33-64(15ml_24h)/20250808（烘干后）/FS-17/1-32_down/1-32_down_ref_masked_spectra.csv",
    r"/home/x45880/Elements SE/caoge/光谱数据/第一批/E组1-32(10ml_24h)_33-64(15ml_24h)/20250808（烘干后）/FS-17/33-64_down/33-64_down_ref_masked_spectra.csv",
    
    r"/home/x45880/Elements SE/caoge/光谱数据/第二批/A组_64粒（无处理）/20250810（烘干后）/FS-17/1-32_down/1-32_down_ref_masked_spectra.csv",
    r"/home/x45880/Elements SE/caoge/光谱数据/第二批/A组_64粒（无处理）/20250810（烘干后）/FS-17/33-64_down/33-64_down_ref_masked_spectra.csv",
    r"/home/x45880/Elements SE/caoge/光谱数据/第二批/B组_1-32(5ml_12h)_33-64(20ml_12h)/20250813(烘干后)/FS-17/1-32_down/1-32_down_ref_masked_spectra.csv",
    r"/home/x45880/Elements SE/caoge/光谱数据/第二批/B组_1-32(5ml_12h)_33-64(20ml_12h)/20250813(烘干后)/FS-17/33-64_down/33-64_down_ref_masked_spectra.csv",
    r"/home/x45880/Elements SE/caoge/光谱数据/第二批/C组_1-32(10ml_12h)_33-64(15ml_12h)/20250815(烘干后)/FS-17/1-32_down/1-32_down_ref_masked_spectra.csv",
    r"/home/x45880/Elements SE/caoge/光谱数据/第二批/C组_1-32(10ml_12h)_33-64(15ml_12h)/20250815(烘干后)/FS-17/33-64_down/33-64_down_ref_masked_spectra.csv",
    r"/home/x45880/Elements SE/caoge/光谱数据/第二批/D组_1-32(5ml_24h)_33-64(20ml_24h)/20250817(烘干后)/FS-17/1-32_down/1-32_down_ref_masked_spectra.csv",
    r"/home/x45880/Elements SE/caoge/光谱数据/第二批/D组_1-32(5ml_24h)_33-64(20ml_24h)/20250817(烘干后)/FS-17/33-64_down/33-64_down_ref_masked_spectra.csv",
    #r"/home/x45880/Elements SE/caoge/光谱数据/第二批/E组_1-32(10ml_24h)_33-64(15ml_24h)/20250819(烘干后)/FS-13/1-32_down/1-32_down_ref_masked_spectra.csv",
    #r"/home/x45880/Elements SE/caoge/光谱数据/第二批/E组_1-32(10ml_24h)_33-64(15ml_24h)/20250819(烘干后)/FS-13/33-64_down/33-64_down_ref_masked_spectra.csv"
]


# 初始化一个空的 DataFrame 用于存储合并后的数据
combined_df = pd.DataFrame()

# 初始化种子编号计数器
seed_id_counter = 1

# 遍历所有文件路径
for file_path in file_paths:
    # 读取当前文件
    df = pd.read_csv(file_path)
    
    # # 将百分比数据转换为反射率（0-1范围）
    # df.iloc[:, 1:] = df.iloc[:, 1:] / 100.0
    
    # 重新编号种子
    df.iloc[:, 0] = range(seed_id_counter, seed_id_counter + len(df))
    
    # 更新种子编号计数器
    seed_id_counter += len(df)
    
    # 检查是否是第一个文件，如果是，则直接赋值
    if combined_df.empty:
        combined_df = df
    else:
        # 否则，将当前文件的数据追加到 combined_df 中
        combined_df = pd.concat([combined_df, df], ignore_index=True)

# 查看合并后的数据
print(combined_df.head())

# 保存合并后的数据
output_file = r"/home/x45880/桌面/bgz/after_drying/mix_data/FS-17_down(lack_1B_all_&_2E_all).csv"
combined_df.to_csv(output_file, index=False)
print(f"合并后的数据已保存为 {output_file}")