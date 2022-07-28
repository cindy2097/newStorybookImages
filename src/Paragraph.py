from PIL import Image    # Image class for getting dominant color
import re                # For some reason pytesseract adds in \n and \x0c. This will remove it
import pytesseract       # OCR 
import cv2               # For drawing circles and rectangles on image
import requests          # For requesting translation to server.
import json              # For extraction of translation from server
import SensitiveInfo     # Sensitive Info (ex: auth token) regarding connection to the server
from copy import deepcopy# For deep copying images
from time import sleep   # For creating downtime between each API request
from PIL import ImageEnhance

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

    def apply_offset (self, offset_x=0, offset_y=0): 
        self.x += offset_x
        self.y += offset_y
        return self

    def crop_img (self, img):
        return img[self.y:self.y+self.h, self.x:self.x+self.w]

    def drawBoundingBox (self, img): 
        return cv2.rectangle(img, (self.x, self.y), (self.x + self.w, self.y + self.h), (0,0,0), 5)

    def out_of_bounds (self, img_w, img_h, margin=0):
        if (self.x + self.w > img_w + margin) or (self.y + self.h > img_h + margin) or self.x < 0 or self.y < 0: 
            return True
        return False
    
class Paragraph: 
    lines : list[BoundingBox] = [] # Array of BoundingBox
    texts : list[str] = [] # Array of strings that correspond with each line
    paragraphBox : BoundingBox = None # BoundingBox of general Paragraph
    pageNum = -1           # The page number the paragraph is in
    paragraphId = -1    # The paragraph unique id in the page
    dominant_color = [] # The rgb values of the dominant color
    translated = "" # The translated text of the paragraph  

    def __init__ (self, lines, page, paragraphId, target_lang): 
        self.lines = lines
        self.texts = ["" for _ in self.lines]
        self.pageNum = page
        self.paragraphId = paragraphId
        self.target_lang = target_lang
        
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

    def removeChar(self, text): 
        special_char_dict = {
            "’": "'",
            "”": "'",
            "“": "'",
            "—": "-"
        }
        for key in special_char_dict:
            text = text.replace(key, special_char_dict[key])

        return text 

    def translateText (self, text, target_language, delay=0.5): 
        if text.strip() != "":
            # How to convert target_language (ex: turkish) to language token?
            # What is the auth token?
            auth_token = SensitiveInfo.auth_token 

            url = "https://platform.neuralspace.ai/api/translation/v1/translate"
            headers = {}
            headers["Accept"] = "application/json, text/plain, */*"
            headers["authorization"] = auth_token
            headers["Content-Type"] = "application/json;charset=UTF-8"

            # send request
            data = f""" 
            {{
                "text": "{self.removeChar(text)}",
                "sourceLanguage": "en",
                "targetLanguage": "{target_language}"
            }}
            """
            sleep(delay) # If we send too much requests at once, then the server won't respond to the overflow of requests
            print("sent request", data)
            resp = requests.post(url, headers=headers, data=data)
            print("request done")
            response_dict = json.loads(resp.text)
            return response_dict["data"]["translatedText"]
        else: 
            return ""
    
    def process_lines (self, original_img): 
        # Initialize delete variable (delete lines if no detect text)
        index_delete = []

        def order_by_y (elem):
            return elem.y

        print("cropped")
        cropped = Image.fromarray(self.paragraphBox.crop_img(original_img))

        enhancer1 = ImageEnhance.Sharpness(cropped)
        enhancer2 = ImageEnhance.Contrast(cropped)
        img_edit = enhancer1.enhance(20.0)
        img_edit = enhancer2.enhance(1.5)
        print("enhanced done")

        result = pytesseract.image_to_string(img_edit)
        print("text recognition done", result)

        # for index, bb in enumerate(sorted(self.lines, key=order_by_y)):
        #     # Crop the image
        #     cropped = original_img[bb.y:bb.y + bb.h, bb.x:bb.x + bb.w]
        
        #     # Apply OCR on the cropped image
        #     text = re.sub(r'[\x00-\x1f]+', '',  pytesseract.image_to_string(cropped))
        #     if text.strip() == "": 
        #         index_delete.append(index)
        #         continue

        #     # add total text
        #     self.texts[index] = text

        #     # Check if we should delete index
        #     if len(text) <= 3: 
        #         index_delete.append(index)

        # get translated text
        # self.translated = self.translateText(" ".join(self.texts), self.target_lang, delay=0.2)
        self.translated = self.translateText(result, self.target_lang, delay=0.2)
        print("translation done")

        # delete everything from index array
        for num, index in enumerate(index_delete):
            self.texts.pop(index-num)
            self.lines.pop(index-num)

        # if we have no useful lines, then reset everything
        if len(self.texts) == 0: 
            self.paragraphBox = 0 
            self.pageNum = -1
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

    def apply_offset (self, offset_x=0, offset_y=0):
        for index in range(len(self.lines)):
            self.lines[index].apply_offset(offset_x, offset_y)
        self.paragraphBox.apply_offset(offset_x, offset_y)        
        return self

    def out_of_bounds (self, img_w, img_h):
        return self.paragraphBox.out_of_bounds(img_w, img_h)

    def text_to_string (self, text_sep, info_sep): 
        text_lines = [] 
        for index, line in enumerate(self.texts): 
            string = info_sep.join([str(self.pageNum), str(self.paragraphId), str(index), line]) 
            text_lines.append(string)
        self.text_sep = text_sep
        self.info_sep = info_sep
        return text_sep.join(text_lines)

    def draw_text_box (self, img):
        def order_by_y (elem):
            return elem.y
        for index, _ in enumerate(sorted(self.lines, key=order_by_y)):
            img = cv2.putText(img, self.texts[index], (self.lines[index].x, self.lines[index].y), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(0,0,255), thickness=2) 
        img = cv2.rectangle(img, (self.paragraphBox.x, self.paragraphBox.y), (self.paragraphBox.x + self.paragraphBox.w, self.paragraphBox.y + self.paragraphBox.h), (0,0,255), 5)
        return img

class Page: 
    paragraphs: list[Paragraph] = []
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
            info = paragraph.text_to_string(text_sep,info_sep)
            arr.append(info)
        return text_sep.join(arr)

    def string_to_text (self, string): 
        for paragraph in self.paragraphs: 
            paragraph.string_to_text(string)