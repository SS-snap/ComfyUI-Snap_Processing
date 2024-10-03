import torch
import hashlib
from pathlib import Path
from typing import Iterable
from PIL import Image, ImageOps
import numpy as np
import folder_paths
import os  # 引入 os 库用于创建目录

class Snapload:
    @classmethod
    def INPUT_TYPES(s):
        return {"required":
                    {"image": ("STRING", {"default": r"请转换为输入并SnapCanvas的string输出"})},
                }

    CATEGORY = "Snap Processing"

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_image"
    
    def load_image(self, image):
        # 调用 _resolve_path 来获取图像路径
        image_path = Snapload._resolve_path(image)

        # 打开并处理图像
        i = Image.open(image_path)
        i = ImageOps.exif_transpose(i)
        image = i.convert("RGB")
        image = np.array(image).astype(np.float32) / 255.0
        image = torch.from_numpy(image)[None,]
        
        # 如果有 Alpha 通道，则生成掩码
        if 'A' in i.getbands():
            mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
            mask = 1. - torch.from_numpy(mask)
        else:
            # 否则生成一个全为零的掩码
            mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
        
        return (image, mask)

    # 将图像路径解析为相对路径，默认为指定的路径
    def _resolve_path(image) -> Path:
        # 如果未提供图像路径，则使用默认路径
        if not image:
            default_path = Path("ComfyUI/custom_nodes/ComfyUI-Snap_Processing/save/output.png").resolve()
        else:
            default_path = Path(folder_paths.get_annotated_filepath(image)).resolve()

        # 创建默认保存目录，如果不存在
        save_directory = default_path.parent
        if not save_directory.exists():
            os.makedirs(save_directory)

        # 返回默认路径或解析后的路径
        return default_path

    @classmethod
    def IS_CHANGED(s, image):
        # 获取图像路径并计算其哈希值，判断是否改变
        image_path = Snapload._resolve_path(image)
        m = hashlib.sha256()
        with open(image_path, 'rb') as f:
            m.update(f.read())
        return m.digest().hex()

    @classmethod
    def VALIDATE_INPUTS(s, image):
        # 如果图像为空，则返回 True
        if image is None:
            return True

        # 验证图像路径是否存在
        image_path = Snapload._resolve_path(image)
        if not image_path.exists():
            return "Invalid image path: {}".format(image_path)

        return True
        
