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

def draw_text(pil_img, left, top, color, text, font_name, size):
    
    draw = ImageDraw.Draw(pil_img)
    
    # font = ImageFont.truetype(<font-file>, <font-size>)
    font = ImageFont.truetype(font_name, size)
    width = font.getlength(text)
    print(width)
    # draw.text((x, y),"Sample Text",(r,g,b))
    draw.text((left, top),text,color,anchor = "mm",font=font)
    return pil_img

def calculate_word_widths(words, font_name, max_font, max_width):
    widths = []
    for w in words:
        font = ImageFont.truetype(font_name, max_font)
        width = font.getlength(w)
        if width < max_width: # text wont have to be resized
            widths.append(width)
        else:  # text will have to be resized
            widths.append(0) 
    return widths

def calculate_font_size(text, font_name, max_width, min_font, max_font):
    font_size = max_font

    for w in range(max_font, min_font, -2):
        font = ImageFont.truetype(font_name, w)
        width = font.getlength(text)
        if width < max_width:
            return font_size
        else:
            font_size = w
    return font_size


def calculate_grid_locations(width, height, rows, columns):
    
    grid = []
    x_offset = width / (columns + 1)
    y_offset = height / (rows + 1)
    x = []
    for c in range(columns):
        x.append(x_offset*c + x_offset)
    
    y = []
    for r in range(rows):
        y.append(y_offset*r + y_offset)
    print(x)
    print(y)
    return x,y



if __name__ == "__main__":
    PIC_FOLDER = "./working/"
    FILE1 = "Omegle Bars 34.jpg"
    FILE2 = "Omegle Bars 64.jpg"
    FONT_NAME = "Acme-Regular.ttf"
    FONT_SIZE = 48
    MAX_FONT_SIZE = 48
    MIN_FONT_SIZE = 2

    ORIG_HEIGHT = 720
    ORIG_WIDTH = 1280
    f1 = PIC_FOLDER + FILE1
    f2 = PIC_FOLDER + FILE2
    
    
    
    # This is the size of the border added to the image.  Note this border is added before the image is resized.  The final border height will be larger by a multiple
    # 
    bottom_border = 120
    multiplier = (ORIG_WIDTH / (ORIG_HEIGHT + bottom_border))
    new_image_height = ORIG_HEIGHT * multiplier # height of image not including border
    new_border_height = bottom_border * multiplier
    im = Image.open(f1)
    im_new = add_margin(im, 0, 0, bottom_border, 0, (0, 0, 0))
    im_new.save(f1 + " modified.jpg", quality=95)
    im_new = Image.open(resize_image(f1 + " modified.jpg", f1 + " resized.jpg", 1280, 1280))
    
    words = ["King", "Tiger", "Clout", "TEST", "Long string of Words. what happens if its too long?", "orange", "blue"]
    if len(words) > 4:
        rows = 2
        columns = 4
    else:
        rows = 1
        columns = len(words)
    x, y = calculate_grid_locations(ORIG_WIDTH,new_border_height,rows,columns)

    r = 0
    c = 0
    word_widths = calculate_word_widths(words, FONT_NAME, MAX_FONT_SIZE, 2*x[0])
         
    for word, width in zip(words, word_widths):
        if width == 0: # font size has to be reduced
            font_size = calculate_font_size(word, FONT_NAME, 2*x[0] * 0.8, MIN_FONT_SIZE, MAX_FONT_SIZE)
        else:
            font_size = MAX_FONT_SIZE
        im_new = draw_text(im_new, x[c], y[r] + new_image_height, (255,255,255), word + f"({font_size})", FONT_NAME, font_size)

        c = c + 1
        if c > columns-1:
            c = 0
            r = r + 1
            if r > rows:
                #should be done here
                pass
    im_new.save('./working/sample-out.jpg')


