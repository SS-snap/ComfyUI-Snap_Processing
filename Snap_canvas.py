# 文件路径: ComfyUI/custom_nodes/ComfyUI-Snap_Processing/Snap_canvas.py

from PyQt5.QtCore import QEventLoop
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QImage
import time
import os
import torch
from PIL import Image
import numpy as np
from io import BytesIO
from .ui.canvas_window import CanvasWindow


class PyQtCanvasNode:
    @staticmethod
    def INPUT_TYPES():
        return {
            "required": {
                "image": ("IMAGE",),  # 必需的图像输入
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            }
        }

    RETURN_TYPES = ("IMAGE", "INT", "STRING", "INT", "INT", "FLOAT")  # IMAGE, seed, path, x, y, scale_factor
    RETURN_NAMES = ("image", "seed", "string", "X", "Y", "factor")
    FUNCTION = "activate_pyqt"
    CATEGORY = "Snap Processing"

    def activate_pyqt(self, image, seed):
        try:
            # 使用用户提供的种子值
            print(f"Received seed: {seed}")

            # 将张量转换为 QImage
            qimage = self.tensor_to_qimage(image)
            print("Converted tensor to QImage")

            # 运行 PyQt GUI 并阻塞主线程，直到用户完成操作
            modified_image, x, y, scale_factor = self.run_pyqt_gui(qimage)
            print("PyQt GUI closed")

            # 将修改后的 QImage 转换为 NumPy 数组
            numpy_array = self.qimage_to_numpy(modified_image)
            print("Converted QImage to NumPy array")

            save_directory = os.path.join(os.getcwd(), "canvas")

            # 如果目录不存在，则创建该目录
            if not os.path.exists(save_directory):
                os.makedirs(save_directory)

            # 使用固定文件名 'output.png'
            png_image_filename = "output.png"
            png_image_path = os.path.join(save_directory, png_image_filename)

            # 保存图像
            self.numpy_to_png(numpy_array, png_image_path)
            print(f"已将图像保存到 {png_image_path}")

            # 返回修改后的图像和其他参数
            return (self.qimage_to_tensor(modified_image), seed, png_image_path, x, y, scale_factor)
        except Exception as e:
            print(f"激活 PyQt 时出错: {e}")
            raise e

    def run_pyqt_gui(self, input_image):
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])  # 创建全局应用程序

            # 始终创建一个新的 CanvasWindow 实例
            dialog = CanvasWindow(input_image)
            dialog.save_signal.connect(self.on_save)
            dialog.close_signal.connect(self.on_close)

            print("PyQt CanvasWindow shown")
            dialog.exec_()  # 阻塞，直到对话框关闭

            print("Dialog closed")
            modified_image = dialog.get_modified_image()
            x = dialog.get_top_left_x()
            y = dialog.get_top_left_y()
            scale_factor = dialog.get_scale_factor()
            dialog.deleteLater()  # 确保窗口被正确销毁
            print("CanvasWindow deleted")
            return modified_image, x, y, scale_factor
        except Exception as e:
            print(f"Error in run_pyqt_gui: {e}")
            raise e

    def on_save(self):
        print("Image saved successfully")

    def on_close(self):
        print("Window closed")

    def tensor_to_qimage(self, tensor):
        if tensor.ndim == 4:
            tensor = tensor.squeeze(0)
        if tensor.ndim != 3:
            raise ValueError(f"Expected tensor with 3 dimensions, but got {tensor.ndim} dimensions.")

        if tensor.shape[0] in [1, 3, 4]:
            pass
        elif tensor.shape[2] in [1, 3, 4]:
            tensor = tensor.permute(2, 0, 1)
        else:
            raise ValueError("Tensor has unsupported shape.")

        num_channels = tensor.shape[0]
        if num_channels == 1:
            tensor = tensor.repeat(3, 1, 1)
        elif num_channels == 2:
            tensor = torch.cat([tensor, tensor[0:1, :, :]], dim=0)
        elif num_channels == 4:
            tensor = tensor[:3, :, :]
        elif num_channels != 3:
            raise ValueError(f"Unsupported number of channels: {num_channels}")

        image_data = tensor.mul(255).byte().cpu().numpy()
        image_data = image_data.transpose(1, 2, 0)

        pil_image = Image.fromarray(image_data, 'RGB')
        qimage = self.pil_image_to_qimage(pil_image)
        return qimage

    def qimage_to_tensor(self, qimage):
        qimage = qimage.convertToFormat(QImage.Format_RGB888)
        width = qimage.width()
        height = qimage.height()

        ptr = qimage.bits()
        ptr.setsize(qimage.byteCount())
        image_np = np.array(ptr).reshape((height, width, 3))

        tensor = torch.from_numpy(image_np).permute(2, 0, 1).float() / 255.0
        return tensor

    def qimage_to_numpy(self, qimage):
        qimage = qimage.convertToFormat(QImage.Format_RGB888)
        width = qimage.width()
        height = qimage.height()

        ptr = qimage.bits()
        ptr.setsize(qimage.byteCount())
        image_np = np.array(ptr).reshape((height, width, 3))

        return image_np

    def numpy_to_png(self, numpy_array, save_path):
        if numpy_array.dtype != np.uint8:
            numpy_array = (numpy_array * 255).astype(np.uint8)

        image = Image.fromarray(numpy_array)
        image.save(save_path, format='PNG')

    def pil_image_to_qimage(self, pil_image):
        buffer = BytesIO()
        pil_image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()
        qimage = QImage.fromData(image_bytes, "PNG")
        return qimage
