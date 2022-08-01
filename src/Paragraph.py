from socket import BTPROTO_RFCOMM
from PIL import Image    # Image class for getting dominant color
import re                # For some reason pytesseract adds in \n and \x0c. This will remove it
import pytesseract       # OCR 
import cv2               # For drawing circles and rectangles on image
import requests          # For requesting translation to server.
import json              # For extraction of translation from server
import SensitiveInfo     # Sensitive Info (ex: auth token) regarding connection to the server
from copy import deepcopy# For deep copying images
from time import sleep   # For creating downtime between each API request

class BoundingBox: 
    x = -1
    y = -1 
    w = -1
    h = -1

    def __init__ (self, x=-1, y=-1, w=-1, h=-1): 
        self.x = round(x)
        self.y = round(y)
        self.w = round(w) 
        self.h = round(h)

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

    def out_of_bounds (self, img_w, img_h, margin=100):
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

    def __init__ (self, lines, overallBox, texts, pageNum, paragraphId, target_lang): 
        self.lines = lines
        self.texts = texts
        self.pageNum = pageNum
        self.paragraphId = paragraphId
        self.target_lang = target_lang
        self.paragraphBox = BoundingBox(overallBox[0], overallBox[1], overallBox[2], overallBox[3])

        # -------------- CHANGE THIS TO YOUR TESSERACT OCR FILE -------------- #
        pytesseract.pytesseract.tesseract_cmd = "C:\\msys64\\mingw32\\bin\\tesseract.exe" 
        # -------------------------------------------------------------------- #

    def __str__(self) -> str:
        return f"Page Number: {self.pageNum} Paragraph ID: {self.paragraphId} Texts: {self.texts} Lines: {[i.__str__() for i in self.lines]}"

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

    def translateText (self, delay=0.5): 
        overall_text = " ".join(self.texts)
        print(f"\nOverall Text: {overall_text}")
        if overall_text.strip() != "":
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
                "text": "{self.removeChar(overall_text)}",
                "sourceLanguage": "en",
                "targetLanguage": "{self.target_lang}"
            }}
            """
            sleep(delay) # If we send too much requests at once, then the server won't respond to the overflow of requests
            resp = requests.post(url, headers=headers, data=data)
            response_dict = json.loads(resp.text)
            self.translated = response_dict["data"]["translatedText"]
    
    def apply_offset (self, offset_x=0, offset_y=0):
        for index in range(len(self.lines)):
            self.lines[index].apply_offset(offset_x, offset_y)
        self.paragraphBox.apply_offset(offset_x, offset_y)        
        return self

    def out_of_bounds (self, img_w, img_h):
        return self.paragraphBox.out_of_bounds(img_w, img_h)

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

    def display_page (self, name="Display"):
        img = deepcopy(self.original_image)
        for paragraph in self.paragraphs:
            img = paragraph.draw_text_box(img)
        cv2.imshow(name, img) 
        cv2.waitKey(0)

    def translate (self):
        for para in self.paragraphs: 
            para.translateText()