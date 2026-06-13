# 高光谱图像波段查看工具
# 功能：加载ENVI格式高光谱数据（.hdr+.spe），支持两种模式查看波段灰度图
#   1. 遍历模式：自动逐个显示所有波段，按回车切换下一个，输入"q"退出
#   2. 指定模式：根据输入的波段编号，显示对应波段的灰度图及波长信息
# 依赖库：spectral（处理高光谱数据）、numpy（数据处理）、matplotlib（可视化）
# 使用说明：
#   - 修改代码中hdr_file和spe_file路径为实际文件路径
#   - 调用view_band_gray函数时，不传target_band参数则启用遍历模式
#   - 传入target_band=波段号（如50）则启用指定模式，查看对应波段
# 注意：波段编号从1开始，需在有效范围内（1~总波段数）
import spectral.io.envi as envi
import numpy as np
import matplotlib.pyplot as plt
import sys


def view_band_gray(hdr_path, spe_path, target_band=None):
    """
    独立查看高光谱图像波段灰度图：
    1. 支持指定波段查看
    2. 支持遍历所有波段查看
    3. 自动识别波长信息
    """
    # 1. 加载高光谱数据
    try:
        img = envi.open(hdr_path, spe_path)
        data = img.load()
        lines, samples, bands = data.shape
        wavelengths = img.bands.centers  # 所有波段波长
        print(f"✅ 成功加载高光谱数据：{lines}行×{samples}列×{bands}波段")
        print(f"   波长范围：{wavelengths[0]:.2f}nm ~ {wavelengths[-1]:.2f}nm")

    except Exception as e:
        print(f"❌ 数据加载失败：{e}")
        return

    # 2. 波段选择逻辑
    if target_band is None:
        # 遍历所有波段
        print("\n========== 开始遍历所有波段灰度图 ==========")
        for b in range(bands):
            band_data = data[:, :, b].squeeze()  # 确保2D
            wavelength = wavelengths[b]

            # 可视化
            plt.figure(figsize=(6, 5))
            plt.imshow(band_data, cmap='gray')
            plt.title(f"Band {b + 1} • Wavelength: {wavelength:.2f}nm", fontsize=12)
            plt.colorbar(label='Pixel Value', fraction=0.045)  # 适配颜色条
            plt.tight_layout()
            plt.show(block=False)  # 非阻塞显示
            plt.pause(1)  # 每个波段显示1秒（可修改）

            # 按回车继续，按Q退出
            key = input("→ 按【回车】看下一个波段，输入【q】退出：").strip().lower()
            if key == 'q':
                plt.close('all')
                print("🛑 用户手动退出遍历")
                break
            plt.close()

    else:
        # 查看指定波段
        if 1 <= target_band <= bands:
            b = target_band - 1  # 转0索引
            band_data = data[:, :, b].squeeze()
            wavelength = wavelengths[b]

            plt.figure(figsize=(8, 6))
            plt.imshow(band_data, cmap='gray')
            plt.title(f"指定波段 • Band {target_band} • {wavelength:.2f}nm", fontsize=14)
            plt.colorbar()
            plt.show()
        else:
            print(f"❌ 波段编号无效！有效范围：1~{bands}")
            return


if __name__ == "__main__":
    # 配置文件路径
    hdr_file = r"X:\FS-17\第一批\A组_64粒无处理\33-64_up\33-64_up_ref.hdr"
    spe_file = r"X:\FS-17\第一批\A组_64粒无处理\33-64_up\33-64_up_ref.spe"

    # 两种模式可选：
    # 1. 遍历所有波段（注释掉下面一行则默认遍历）
    #view_band_gray(hdr_file, spe_file)

    # 2. 查看指定波段（示例：查看第50个波段）
    view_band_gray(hdr_file, spe_file, target_band=512)
    view_band_gray(hdr_file, spe_file, target_band=600)
    view_band_gray(hdr_file, spe_file, target_band=700)

