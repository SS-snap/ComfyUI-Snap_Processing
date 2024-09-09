import torch

class AreaCalculator:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),  
                "color_choice": (["black", "white"],),  
            },
        }

    RETURN_TYPES = ("INT", "INT")  
    RETURN_NAMES = ("面积","占比%")
    FUNCTION = "calculate_area"  
    CATEGORY = "Snap Processing"  

    def calculate_area(self, image, color_choice):

        gray_image = torch.mean(image, dim=0)  

        if color_choice == "black":

            mask = gray_image < 0.5
        else:

            mask = gray_image >= 0.5


        color_area = torch.sum(mask).item() 


        color_area = round(color_area)


        total_area = gray_image.numel()


        color_ratio = int((color_area / total_area) * 100)

        return (int(color_area), color_ratio)

NODE_CLASS_MAPPINGS = {
    "AreaCalculator": AreaCalculator
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AreaCalculator": "Snap Area"
}