from .area_calculator import AreaCalculator
from .Snap_canvas import PyQtCanvasNode
from .Snapload import Snapload
from .canvas_window import CanvasWindow  

VERSION = "1.0"

NODE_CLASS_MAPPINGS = {
    "AreaCalculator": AreaCalculator,
    "PyQtCanvasNode": PyQtCanvasNode,
    "Snapload": Snapload,
    "CanvasWindow": CanvasWindow,  
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AreaCalculator": "Snap Area",
    "PyQtCanvasNode": "Snap Canvas",
    "Snapload": "Snap load",
    "CanvasWindow": "Canvas Window",  
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'CanvasWindow']  
