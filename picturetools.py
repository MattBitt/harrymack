from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
from harrymack import resize_image

def add_margin(pil_img, top, right, bottom, left, color):
    width, height = pil_img.size
    new_width = width + right + left
    new_height = height + top + bottom
    result = Image.new(pil_img.mode, (new_width, new_height), color)
    result.paste(pil_img, (left, top))
    return result

def draw_text(pil_img, left, top, color, text, size):
    
    draw = ImageDraw.Draw(pil_img)
    # font = ImageFont.truetype(<font-file>, <font-size>)
    font = ImageFont.truetype("Acme-Regular.ttf", size)
    # draw.text((x, y),"Sample Text",(r,g,b))
    draw.text((left, top),text,color,font=font)
    return pil_img

def calculate_location(width, height, rows, columns, row, column, font_size):
    # if only 1 row.  going to need columns evenly spaced. not worried about
    center = 45 # since border is 90 pixels high
    x_offset = width / (columns + 1)
    y = center - font_size / 2 #center the text in the space
    x = column * x_offset + x_offset

    return x,y



if __name__ == "__main__":
    PIC_FOLDER = "./working/"
    FILE1 = "Omegle Bars 34.jpg"
    FILE2 = "Omegle Bars 64.jpg"
    FONT_SIZE = 64
    f1 = PIC_FOLDER + FILE1
    f2 = PIC_FOLDER + FILE2
    im = Image.open(f1)
    im_new = add_margin(im, 0, 0, 90, 0, (0, 0, 0))
    im_new.save(f1 + " modified.jpg", quality=95)
    resize_image(f1 + " modified.jpg", f1 + " resized.jpg", 1280, 1280)
    words = ["King", "Tiger", "Clout"]
    rows = 1
    columns = 3
    r = 0
    c = 0
    im = Image.open(f1 + " resized.jpg")
    for word in words:

        x, y = calculate_location(1280, 1280, 1, 3, r, c, FONT_SIZE)
        im = draw_text(im, x, y + 1150, (255,255,255), word, FONT_SIZE)

        c = c + 1
        if c > columns:
            c = 0
            r = r + 1
            if r > rows:
                #should be done here
                pass
    im.save('./working/sample-out.jpg')


