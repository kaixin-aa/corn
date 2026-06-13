# 玉米种子高光谱最佳区分波段筛选工具
# 功能：自动分析高光谱数据中玉米种子与背景区分度最高的波段
# 核心逻辑：
#   1. 加载ENVI格式高光谱数据（.hdr+.spe），获取波段及波长信息
#   2. 通过初始阈值分割和形态学操作，提取可靠的种子区域与背景区域掩码
#   3. 计算每个波段的"种子-背景区分度"（基于均值差异与标准差的比值，值越大区分度越高）
#   4. 筛选出区分度最高的波段，并可视化区分度曲线及最佳波段效果（叠加种子边界）
# 依赖库：spectral（高光谱处理）、numpy（数据计算）、matplotlib（可视化）、scipy（统计）、skimage（形态学与分割）
# 使用说明：
#   1. 修改hdr_file和spe_file为实际高光谱数据路径
#   2. 可通过调整min_area和max_area参数筛选有效种子区域（默认500~7000像素）
#   3. 运行后返回最佳波段索引、波长，并显示可视化结果
# 输出：控制台打印最佳波段信息，窗口显示区分度曲线及最佳波段灰度图

import spectral.io.envi as envi
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

def find_best_band(hdr_path, spe_path, min_area=500, max_area=7000):
    """
    自动筛选玉米种子与背景区分度最高的波段
    返回：区分度最高的波段索引、波长及可视化结果
    """
    # 1. 加载高光谱数据
    img = envi.open(hdr_path, spe_path)
    data = img.load()
    lines, samples, bands = data.shape
    wavelengths = np.array(img.bands.centers)
    print(f"数据加载完成：{lines}×{samples}，共{bands}个波段（{wavelengths[0]:.1f}~{wavelengths[-1]:.1f}nm）")

    # 2. 先通过简单阈值获取初始种子区域（用于后续计算差异）
    # 选一个中间波段做初始分割（如第100波段，可根据数据调整）
    init_band = 100 if bands > 100 else bands//2
    gray_init = data[:, :, init_band].squeeze()
    thresh_init = stats.mode(gray_init, keepdims=False)[0] * 1.2  # 简单阈值
    binary_init = gray_init > thresh_init  # 初始二值化（种子为True）

    # 3. 形态学处理+区域筛选，获取可靠的种子和背景掩码
    from skimage import morphology, measure
    binary_init = morphology.binary_opening(binary_init, morphology.disk(2))
    binary_init = morphology.binary_closing(binary_init, morphology.disk(3))
    labeled_init = measure.label(binary_init)
    regions_init = measure.regionprops(labeled_init)

    # 筛选有效种子区域，生成最终种子掩码
    seed_mask = np.zeros_like(binary_init, dtype=bool)
    for region in regions_init:
        if min_area < region.area < max_area:
            seed_mask[labeled_init == region.label] = True
    background_mask = ~seed_mask  # 背景掩码（种子区域的反集）

    # 4. 计算每个波段的区分度（用种子与背景的均值差异量化）
    # 区分度指标：(种子均值 - 背景均值) / 标准差（越大越好）
    separability = []
    for b in range(bands):
        band_data = data[:, :, b].squeeze()
        seed_mean = np.mean(band_data[seed_mask]) if np.any(seed_mask) else 0
        bg_mean = np.mean(band_data[background_mask]) if np.any(background_mask) else 0
        combined_std = np.std(band_data) + 1e-8  # 避免除零
        score = abs(seed_mean - bg_mean) / combined_std  # 区分度得分
        separability.append(score)

    # 5. 找到区分度最高的波段
    separability = np.array(separability)
    best_idx = np.argmax(separability)
    best_wavelength = wavelengths[best_idx]
    print(f"\n区分度最高的波段：索引{best_idx+1}（{best_wavelength:.2f}nm），得分{separability[best_idx]:.2f}")

    # 6. 可视化结果
    plt.figure(figsize=(12, 5))
    # 左图：区分度曲线
    plt.subplot(121)
    plt.plot(wavelengths, separability, color='blue')
    plt.scatter(best_wavelength, separability[best_idx], color='red', s=80, label=f'best_wavelength:{best_wavelength:.2f}nm')
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Separability(Higher = Better)')
    plt.title('Seed-Background Separability Across Bands')
    plt.legend()

    # 右图：最佳波段的灰度图（叠加种子掩码边界）
    plt.subplot(122)
    best_band_data = data[:, :, best_idx].squeeze()
    plt.imshow(best_band_data, cmap='gray')
    # 叠加种子区域边界
    from skimage.segmentation import find_boundaries
    boundaries = find_boundaries(seed_mask, mode='outer')
    plt.imshow(boundaries, cmap='Reds', alpha=0.5)  # 红色边界标记种子
    plt.title(f'Best Band ({best_wavelength:.2f}nm) with Seed Regions')
    plt.tight_layout()
    plt.show()

    return best_idx, best_wavelength

if __name__ == "__main__":
    # 替换为你的文件路径
    hdr_file = r"D:\000_data\260603_corn\test.hdr"
    spe_file = r"D:\000_data\260603_corn\test.spe"
    # 运行筛选
    best_idx, best_wl = find_best_band(hdr_file, spe_file)