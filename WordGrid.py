from codecs import latin_1_decode
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from itertools import product

class TextArea:
    def __init__(self, dimensions, image_dimensions, anchor_location):
        # This is an area for drawing with the pillow module
        # width, height are the size, and anchor_location = point on main image where top left corner of text area will be placed
        self.width, self.height = dimensions # Text Area dimensions
        x_anchor, y_anchor = anchor_location
        # this coordinates are all in absolute position
        self.image_width, self.image_height = image_dimensions
        self.left = x_anchor
        self.right = x_anchor + self.width
        self.top = y_anchor
        self.bottom = y_anchor + self.height
        if (self.right > self.image_width) or (self.bottom > self.image_height):
            print(f"Text area does not fit with image")
            print(f"Text area Left={self.left}, Right={self.right}, Top={self.top}, Bottom={self.bottom}")
            print(f"Image area {self.image_width}, {self.image_height}")
        self.rectangle = [(self.left, self.top), (self.right, self.bottom)]


class Word:
    def __init__(self, word_text, order):
        self.word_text = word_text
        self.order = order
        self.x = 0
        self.y = 0
        self.width = 0
        self.max_width = 0
        self.left_neighbor = None
        self.right_neighbor = None
        self.font_size = 0
    
    def width_rectangle(self):
        return [(self.x - (self.width/2), self.y - 10), (self.x + (self.width/2), self.y + 10)]

    def max_width_rectangle(self):
        return [(self.x - (self.max_width/2), self.y - 10), (self.x + (self.max_width/2), self.y + 10)]
    
        


class WordGrid:
    MAX_ROWS = 2
    MAX_COLUMNS = 4
    MIN_FONT_SIZE = 6
    MAX_FONT_SIZE = 44


    def __init__(self, text_area, word_strings, font_name):
        self.text_area = text_area
        self.words = self.create_word_objects(word_strings)
        self.numwords = len(self.words)
        self.font_name = font_name
        self.rows = 1
        self.columns = 1

        #self.max_widths = [] # maximum width for each word
        #self.word_widths = self.max_widths # default is whole length
        self.max_height = 18
        self.padding = 20 # pixels between words
        self.calculate_grid_dimensions()
        self.calculate_word_positions()
        self.calculate_word_widths()
        self.assign_neighbors()
        self.stretch_word_borders()
        self.calculate_word_widths()

        
        #self.show_neighbors()
        #self.show_word_info()
    def create_word_objects(self, word_strings):
        words = []
        i = 1
        for w in word_strings:
            words.append(Word(w.strip(), i))
            i = i + 1
        return words

    def assign_neighbors(self):
        for w in self.words:
            if w.order == 1: # first word
                w.left_neighbor = None
                w.right_neighbor = self.find_word(w.order + 1)
            if self.rows > 1:
                if w.order == self.numwords: # last word
                    w.right_neighbor = None
                    if w.order % self.columns == 1: # 1st word on second row
                        w.left_neighbor = None
                    else:
                        w.left_neighbor = self.find_word(w.order - 1)
                elif w.order == self.columns: # last word on 1st row
                    w.left_neighbor = self.find_word(w.order - 1)
                    w.right_neighbor = None
                elif w.order == self.columns + 1: # first row on second row
                    w.right_neighbor = self.find_word(w.order + 1)
                    w.left_neighbor = None

                else:
                    w.right_neighbor = self.find_word(w.order + 1)
                    w.left_neighbor = self.find_word(w.order - 1)
            else:
                if w.order == self.columns: # last word (only 1 row)
                    w.right_neighbor = None
                    w.left_neighbor = self.find_word(w.order - 1)
                else:
                    w.right_neighbor = self.find_word(w.order + 1)
                    w.left_neighbor = self.find_word(w.order - 1)

    def show_neighbors(self):
        for w in self.words:
            if not w.left_neighbor:
                left = "None"
            else:
                left = w.left_neighbor.word_text
            if not w.right_neighbor:
                right = "None"
            else:
                right = w.right_neighbor.word_text
            print(f"Word = {w.word_text}\tLeft={left}\tRight={right}")    

    def show_word_info(self):
        for w in self.words:
            print(f"{w.word_text} ---> (x,y) ({w.x},{w.y})  width={w.width} max_width={w.max_width}")
    
    def find_word(self, order):
        for w in self.words:
            if w.order == order:
                return w
        return None

    def calculate_grid_dimensions(self):
        numwords = len(self.words)
        if numwords == 0:
            print("No words added.  Cannot compute positions")
            return None
 
        elif numwords <= self.MAX_COLUMNS:
            self.rows = 1
            self.columns = numwords
        else:
            self.rows = 2
            self.columns = self.MAX_COLUMNS
        
        if numwords > (self.rows * self.columns):
            print(f"This is only able to handle {self.MAX_ROWS * self.MAX_COLUMNS} words.  There were {numwords} submitted")
            return None
        
        max_width = (self.text_area.width / (self.columns+1) - (self.padding * 2))
        #self.max_widths.extend([max_width] * len(self.words)) # add default max width multiple times to list.  will evaluate and adjust words as necessary
        for w in self.words:
            w.max_width = max_width
        return self.rows, self.columns
    
    def reorder(self, coords):
        # want to sort the coordinates horizontally instead of vertically
        # sorts list of tuples by y then x
        return sorted(coords, key=lambda element: (element[1], element[0]))

    def calculate_word_positions(self):
        x_offset = self.text_area.width / (self.columns + 1)
        y_offset = self.text_area.height / (self.rows)
        x = []
        for c in range(self.columns):
            x.append(self.text_area.left + x_offset*c + x_offset)
        
        y = [self.text_area.top + y_offset*0.50, self.text_area.top + y_offset*1.5] # adjust offset multipliers to adjust vertical spacing

        positions = self.reorder(list(product(x,y)))
        for word, (x, y) in zip(self.words, positions):
                word.x = x
                word.y = y

    
    def calculate_word_widths(self):
        widths = []
        for word in self.words:
            if word.width == 0:
                font = ImageFont.truetype(self.font_name, self.MAX_FONT_SIZE)
                width = font.getlength(word.word_text)
                if width < word.max_width: # text wont have to be resized
                    word.width = width
                    word.max_width = width
                else:  # text will have to be resized
                    widths.append(0)

    def stretch_word_borders(self):
        for w in self.words:
            if w.width == 0: # too long for the default spacing
                ln = w.left_neighbor
                rn = w.right_neighbor
                left_offset = 0
                right_offset = 0
                if not ln is None:
                    left_offset = w.max_width - ln.max_width
                else:
                    left_offset = w.max_width
                if not rn is None:
                    right_offset = w.max_width - rn.max_width
                else:
                    right_offset = w.max_width
                if left_offset > right_offset:
                    w.max_width = w.max_width + right_offset
                else:
                    w.max_width = w.max_width + left_offset
    
    def draw_word_rectangles(self, draw):
        for word in self.words:
            w = word.max_width / 2
            h = self.max_height / 2
            top_left = (word.x-w, word.y-h)
            bottom_right = (word.x+w, word.y+h)
            draw.rectangle([top_left, bottom_right], fill=(0,0,0), outline=(255,0,0), width=2)

    def draw_text_area(self, draw, fill=(0,0,0)):
        draw.rectangle(self.text_area.rectangle, fill, outline=0, width=1)


    def break_text_into_lines(self, word, font):
        min_diff = 1000
        # take the string, split into words
        # need to figure out best place to split text
        lines = word.word_text.split(" ")
        numwords = len(lines)
        for i in range(numwords):
            l1 = lines[0:i]
            l2 = lines[i:]
            l1 = ' '.join(l1)
            l2 = ' '.join(l2)
            l1width = font.getlength(l1)
            l2width = font.getlength(l2)
            if abs(l1width - l2width) < min_diff:
                min_diff = abs(l1width - l2width)
                min_split = i

        #print(f"Min split L1 = {' '.join(lines[0:min_split])} L2 = {' '.join(lines[min_split:])}")
        l1 = ' '.join(lines[0:min_split])
        l2 = ' '.join(lines[min_split:])
        return [l1, l2]

        

        
        for l in lines:
                width = font.getlength(word.word_text)

    def draw_words(self, draw, fill=(255,255,255)):
        for w in self.words:
            font = ImageFont.truetype(self.font_name, self.MAX_FONT_SIZE)
            if w.width > 0:
                draw.text((w.x, w.y),w.word_text,fill, anchor = "mm", font=font)
            # The word is too long to fit in the expanded space
            else:
                # need to caluclate expanded space using right/left neighbors here
                font_size = self.MAX_FONT_SIZE - 10
                w.font_size = font_size
                font = ImageFont.truetype(self.font_name, w.font_size)
                lines = self.break_text_into_lines(w, font)

                while w.width == 0:
                    w.font_size = font_size
                    font = ImageFont.truetype(self.font_name, w.font_size)
                    l1width = font.getlength(lines[0])
                    l2width = font.getlength(lines[1])

                    if l1width > w.max_width or l2width > w.max_width:
                        font_size -= 2
                    else:
                        w.width = max(l1width, l2width)
                        w.max_width = w.width
                        draw.text((w.x, w.y-15),lines[0],fill, anchor = "mm", font=font)
                        draw.text((w.x, w.y+15),lines[1],fill, anchor = "mm", font=font)

def add_text_area(pil_img, top, bottom, left, right, color):
    width, height = pil_img.size
    new_width = width + right + left
    new_height = height + top + bottom
    result = Image.new(pil_img.mode, (new_width, new_height), color)
    result.paste(pil_img, (left, top))
    return result

def resize_image(img, width, height):
    new_img = img.resize((width,height))
    return new_img

def prepare_image(image_name, text_area, width, height, add_text = False):
    im = Image.open(image_name)
    if add_text:
        im = add_text_area(im, 0, text_area.height, 0, 0, (0,0,0))
        #im.save("./working/text_area.jpg")
    w, h = im.size
    mult = height / h
    text_area.height = mult * text_area.height
    im = im.resize((width,height))
    #im.save("./working/resized.jpg")
    return im



if __name__ == "__main__":
    PIC_FOLDER = "./working/"
    FILE1 = "Omegle Bars 34.jpg"
    FILE2 = "Omegle Bars 64.jpg"
    #FONT_NAME = "Acme-Regular.ttf"
    #FONT_SIZE = 48
    #MAX_FONT_SIZE = 48
    #MIN_FONT_SIZE = 2

    #ORIG_HEIGHT = 720
    #ORIG_WIDTH = 1280
    f1 = PIC_FOLDER + FILE1
    f2 = PIC_FOLDER + FILE2
    


    #word_strings = ["Jameyis coming homeaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"]#, "a", "I love you, Lindsay!!!!!"]#, "Anotherreally longlineof text", "My Girlfriend Thinks I'm An Option", "Pickles", "McDonald's", "Orange you glad i didn't say banana"]
    
    
    anchor_location = (0,1100) #will be (0, 1160?) after testing
    image_dimensions = (1280, 1280)
    text_area_dimensions = (1280, 120) # will be (1280, 120?) after testing
    text_area = TextArea(text_area_dimensions, image_dimensions, anchor_location)
    word_strings = ["King", "Tiger", "Clout", "TEST", "Long string of Words. what happens if its too long?", "orange", "blue"]
    
    
    im = prepare_image(f2, text_area, 1280, 1280)
    draw = ImageDraw.Draw(im)
    font_name = "Acme-Regular.ttf"
    
    
    wg = WordGrid(text_area, word_strings, font_name)

    if wg:
        wg.draw_text_area(draw)
        for w in wg.words:
            wr = w.width_rectangle()
            mwr = w.max_width_rectangle()
            #draw.rectangle(wr, fill=(0,0,255), outline=(0,0,255), width=2)
            #draw.rectangle(mwr, fill=(0,255,255), outline=(0,255,255), width=2)
        wg.draw_words(draw)
    else:
        print("Error creating WordGrid.  Check the words and try again")
        exit()
    
    im.save("./working/testing.jpg")
