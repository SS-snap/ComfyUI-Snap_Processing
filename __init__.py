from .area_calculator import AreaCalculator

VERSION = "1.0"

NODE_CLASS_MAPPINGS = {
    "AreaCalculator": AreaCalculator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AreaCalculator": "Snap Area",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']