# 高光谱波段信息查看与指定波段保存工具
# 功能：
#   1. 加载ENVI格式高光谱数据（.hdr+.spe），显示数据总波段数
#   2. 保存指定波段的原始尺寸灰度图片
# 说明：
#   保存出的图片尺寸与高光谱图像的 lines × samples 完全一致，可用于后续制作Mask

import spectral.io.envi as envi
import numpy as np
import os
import cv2


def robust_normalize_to_uint8(image, p_low=1, p_high=99):
    """
    将单波段反射率图像归一化到0~255，便于保存为灰度图。
    使用百分位拉伸可以避免极端值影响显示效果。
    """
    arr = np.asarray(image, dtype=np.float32)
    lo, hi = np.percentile(arr, (p_low, p_high))

    if hi <= lo:
        return np.zeros(arr.shape, dtype=np.uint8)

    arr = np.clip((arr - lo) / (hi - lo), 0, 1)
    return (arr * 255).astype(np.uint8)


def imwrite_unicode(save_path, image):
    """
    支持中文路径的图片保存函数。
    """
    ext = os.path.splitext(save_path)[1]
    if ext == "":
        ext = ".png"

    ok, encoded = cv2.imencode(ext, image)
    if not ok:
        raise IOError(f"图片编码失败：{save_path}")

    encoded.tofile(save_path)


def view_band_gray(hdr_path, spe_path, target_band=None):
    # 1. 加载高光谱数据并显示总波段数
    try:
        img = envi.open(hdr_path, spe_path)
        data = img.open_memmap(writable=False)
        lines, samples, bands = data.shape

        print(f"✅ 成功加载高光谱数据：{lines}行 × {samples}列 × {bands}波段")
        print(f"   总波段数：{bands}，有效编号范围：1~{bands}")

    except Exception as e:
        print(f"❌ 数据加载失败：{e}")
        return

    # 2. 保存指定波段图片
    if target_band is not None:
        if 1 <= target_band <= bands:
            b = target_band - 1
            band_data = np.asarray(data[:, :, b], dtype=np.float32).squeeze()

            # 转换为8位灰度图，但保持原始尺寸 lines × samples
            band_uint8 = robust_normalize_to_uint8(band_data)

            base_name = os.path.splitext(os.path.basename(hdr_path))[0]
            code_dir = os.path.dirname(os.path.abspath(__file__))
            save_path = os.path.join(code_dir, f"{base_name}_band_{target_band}.png")

            imwrite_unicode(save_path, band_uint8)

            print(f"✅ 波段{target_band}已保存至：{save_path}")
            print(f"✅ 保存图片尺寸：{band_uint8.shape[0]}行 × {band_uint8.shape[1]}列")

        else:
            print(f"❌ 波段编号无效！有效范围：1~{bands}")
            return


if __name__ == "__main__":
    hdr_file = r"D:\000_data\260603_corn\test.hdr"
    spe_file = r"D:\000_data\260603_corn\test.spe"

    view_band_gray(hdr_file, spe_file, target_band=130)