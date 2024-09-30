from .area_calculator import AreaCalculator
from .Snap_canvas import PyQtCanvasNode
from .Snapload import Snapload

VERSION = "1.0"

NODE_CLASS_MAPPINGS = {
    "AreaCalculator": AreaCalculator,
    "PyQtCanvasNode": PyQtCanvasNode,
    "Snapload": Snapload,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AreaCalculator": "Snap Area",
    "PyQtCanvasNode": "Snap Canvas",
    "Snapload": "Snap load", 
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']