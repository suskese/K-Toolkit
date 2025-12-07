import emoji
from customtkinter import CTkImage
from PIL import Image, ImageDraw, ImageFont
def emoji_(emoji, size=32):
    # Convert emoji to CTkImage
    font = ImageFont.truetype("seguiemj.ttf", size=int(size/1.5))
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((size/2, size/2), emoji, embedded_color=True, font=font, anchor="mm")
    img = CTkImage(img, size=(size, size))
    return img