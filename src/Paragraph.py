from PIL import Image    # Image class for getting dominant color
import re                # For some reason pytesseract adds in \n and \x0c. This will remove it
import pytesseract       # OCR 
import cv2               # For drawing circles and rectangles on image

class BoundingBox: 
    x = -1
    y = -1 
    w = -1
    h = -1
    def __init__ (self, x=-1, y=-1, w=-1, h=-1): 
        self.x = x
        self.y = y
        self.w = w 
        self.h = h

    def __str__ (self):
        return "x: " + str(self.x) + " y: " + str(self.y) + " w: " + str(self.w) + " h: " + str(self.h)

class Paragraph: 
    lines = [] # Array of BoundingBox
    texts = [] # Array of strings that correspond with each line
    paragraphBox = None # BoundingBox of general Paragraph
    page = -1           # The page number the paragraph is in
    paragraphId = -1    # The paragraph unique id in the page
    dominant_color = [] # The rgb values of the dominant color

    def __init__ (self, lines, page, paragraphId): 
        self.lines = lines
        self.texts = ["" for _ in self.lines]
        self.page = page
        self.paragraphId = paragraphId
        
        # Get paragraph box of the general paragraph using self.lines
        self.paragraphBox = BoundingBox()
        max_y = 0 
        for line_bounding_box in self.lines: 
            if line_bounding_box.x < self.paragraphBox.x or self.paragraphBox.x == -1: 
                self.paragraphBox.x = line_bounding_box.x 
            if line_bounding_box.y < self.paragraphBox.y or self.paragraphBox.y == -1:
                self.paragraphBox.y = line_bounding_box.y
            if line_bounding_box.w > self.paragraphBox.w: 
                self.paragraphBox.w = line_bounding_box.w
            if line_bounding_box.y + line_bounding_box.h > max_y: 
                max_y = line_bounding_box.y + line_bounding_box.h
        self.paragraphBox.h = max_y - self.paragraphBox.y

        # -------------- CHANGE THIS TO YOUR TESSERACT OCR FILE -------------- #
        pytesseract.pytesseract.tesseract_cmd = "C:\\msys64\\mingw32\\bin\\tesseract.exe" 
        # -------------------------------------------------------------------- #

    def process_lines (self, original_img): 
        # Initialize delete variable (delete lines if no detect text)
        index_delete = []

        for index, bb in enumerate(self.lines):
            # Crop the image
            cropped = original_img[bb.y:bb.y + bb.h, bb.x:bb.x + bb.w]
        
            # Apply OCR on the cropped image
            text = re.sub(r'[\x00-\x1f]+', '',  pytesseract.image_to_string(cropped))
            self.texts[index] = text

            # Check if we should delete index
            if len(text) <= 3: 
                index_delete.append(index)

        # delete everything from index array
        for num, index in enumerate(index_delete):
            self.texts.pop(index-num)
            self.lines.pop(index-num)
        
        # if we have no useful lines, then reset everything
        if len(self.texts) == 0: 
            self.paragraphBox = 0 
            self.page = -1
            self.paragraphId = -1
            self.dominant_color = []
            return -1

        # Get dominant color 
        cropped = Image.fromarray(cropped)
        cropped.thumbnail((100, 100))
        paletted = cropped.convert('P', palette=Image.ADAPTIVE, colors=16)
        palette = paletted.getpalette()
        color_counts = sorted(paletted.getcolors(), reverse=True)
        palette_index = color_counts[0][1]
        self.dominant_color = palette[palette_index*3:palette_index*3+3]
        
        return self.texts, self.dominant_color     

    def text_to_string (self, text_sep, info_sep): 
        text_lines = [] 
        for index, line in enumerate(self.texts): 
            string = info_sep.join([str(self.page), str(self.paragraphId), str(index), line]) 
            text_lines.append(string)
        self.text_sep = text_sep
        self.info_sep = info_sep
        return text_sep.join(text_lines)

    def string_to_text (self, string):
        try:
            lines_sep = self.text_sep.strip()
            infoSep = self.info_sep.strip()
        except Exception:
            print("Error getting line seperator and info seperator! Did you call lines_to_string() before calling this function?")
            exit(-1)
        
        for line in string.split(lines_sep):
            arr = line.split(infoSep)
            if int(arr[0]) == self.page and int(arr[1]) == self.paragraphId: 
                self.texts[int(arr[2])] = arr[3]

        return self.lines

    def draw_text_box (self, img):
        for index in range(len(self.lines)):
            img = cv2.putText(img, self.texts[index], (self.lines[index].x, self.lines[index].y), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(0,0,255), thickness=2) 
        img = cv2.rectangle(img, (self.paragraphBox.x, self.paragraphBox.y), (self.paragraphBox.x + self.paragraphBox.w, self.paragraphBox.y + self.paragraphBox.h), (0,0,255), 5)
        return img

class Page: 
    paragraphs = []
    original_image = None

    def __init__(self, paragraphs, original_image) -> None:
        self.paragraphs = paragraphs
        self.original_image = original_image

    def apply_ocr (self): 
        remove = [] 
        for p in self.paragraphs: 
            result = p.process_lines(self.original_image)
            if result == -1: 
                remove.append(p)
        # remove paragraphs that have no useful OCR output 
        for r in remove:
            self.paragraphs.remove(r)

    def display_page (self, name="Display"):
        img = self.original_image
        for paragraph in self.paragraphs:
            img = paragraph.draw_text_box(img)
        cv2.imshow(name, img) 
        cv2.waitKey(0)

    def text_to_string (self, text_sep, info_sep):
        arr = [] 
        for paragraph in self.paragraphs:
            arr.append(paragraph.text_to_string(text_sep,info_sep))
        return text_sep.join(arr)

    def string_to_text (self, string): 
        for paragraph in self.paragraphs: 
            paragraph.string_to_text(string)