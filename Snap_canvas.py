from PyQt5.QtCore import QEventLoop
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QImage
import time
import os
import random
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
                "image": ("IMAGE",),  # Required image input
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            }
        }

    RETURN_TYPES = ("IMAGE", "INT", "STRING")  # Added "STRING" to the return types
    FUNCTION = "activate_pyqt"
    CATEGORY = "Snap Processing"

    def activate_pyqt(self, image, seed):
        try:
            # Use the user-provided seed value
            print(f"Received seed: {seed}")

            # Convert tensor to QImage
            qimage = self.tensor_to_qimage(image)
            print("Converted tensor to QImage")

            # Run PyQt GUI and block the main thread until the user finishes
            modified_image = self.run_pyqt_gui(qimage)
            print("PyQt GUI closed")

            # Convert the modified QImage to a NumPy array
            numpy_array = self.qimage_to_numpy(modified_image)
            print("Converted QImage to NumPy array")

            # Define the save directory
            save_directory = os.path.join(os.getcwd(), "ComfyUI", "custom_nodes", "Comfyui_Snap-Processing", "save")
            if not os.path.exists(save_directory):
                os.makedirs(save_directory)

            # Create a unique file name using the seed and current timestamp
            timestamp = int(time.time())
            png_image_filename = f"output_image_seed{seed}_{timestamp}.png"
            png_image_path = os.path.join(save_directory, png_image_filename)
            self.numpy_to_png(numpy_array, png_image_path)
            print(f"Saved image to {png_image_path}")

            # Get the absolute path for consistency
            absolute_png_image_path = os.path.abspath(png_image_path)

            # Return the modified image, seed, and the file path
            return (self.qimage_to_tensor(modified_image), seed, absolute_png_image_path)
        except Exception as e:
            print(f"Error in activate_pyqt: {e}")
            raise e

    def run_pyqt_gui(self, input_image):
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])  # Create the global application

            # Always create a new CanvasWindow instance
            dialog = CanvasWindow(input_image)
            dialog.save_signal.connect(self.on_save)
            dialog.close_signal.connect(self.on_close)

            print("PyQt CanvasWindow shown")
            dialog.exec_()  # Block until the dialog is closed

            print("Dialog closed")
            modified_image = dialog.get_modified_image()
            dialog.deleteLater()  # Ensure the window is properly destroyed
            print("CanvasWindow deleted")
            return modified_image
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
