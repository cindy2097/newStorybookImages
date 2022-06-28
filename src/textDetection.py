import cv2               # Image processing and countour detection
import pytesseract       # OCR 
import os                # Path
from tqdm import tqdm    # Progress Bar
import numpy as np       # average color calculations
import requests          # For requesting translation to server.
import time              # For sleep
import json              # For extraction of translation from server
import src.SensitiveInfo # Sensitive Info (ex: auth token) regarding connection to the server
import re                # For some reason pytesseract adds in \n and \x0c. This will remove it
from PIL import Image    # Image class for getting dominant color

# -------------- CHANGE THIS TO YOUR TESSERACT OCR FILE -------------- #
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract' 
# -------------------------------------------------------------------- #

# most of the code is from https://www.geeksforgeeks.org/text-detection-and-extraction-using-opencv-and-ocr/
def getCountours (path): 
    img = cv2.imread(path)
    
    # Convert the image to gray scale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Performing OTSU threshold
    _, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
    
    # Specify structure shape and kernel size.
    # Kernel size increases or decreases the area
    # of the rectangle to be detected.
    # A smaller value like (10, 10) will detect
    # each word instead of a sentence.
    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (18, 18))
    
    # Applying dilation on the threshold image
    dilation = cv2.dilate(thresh1, rect_kernel, iterations = 1)
    
    # Finding contours
    contours, _ = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return contours, img.copy()

def translateText (text, target_language): 
    # How to convert target_language (ex: turkish) to language token?
    # What is the auth token?
    auth_token = src.SensitiveInfo.auth_token 

    url = "https://platform.neuralspace.ai/api/translation/v1/translate"
    headers = {}
    headers["Accept"] = "application/json, text/plain, */*"
    headers["authorization"] = auth_token
    headers["Content-Type"] = "application/json;charset=UTF-8"

    # send request
    data = f""" 
    {{
        "text": "{text}",
        "sourceLanguage": "en",
        "targetLanguage": "{target_language}"
    }}
    """
    resp = requests.post(url, headers=headers, data=data)
    response_dict = json.loads(resp.text)
    return response_dict["data"]["translatedText"]

def get_dominant_color(pil_img, palette_size=16):
    # Resize image to speed up processing
    img = pil_img.copy()
    img.thumbnail((100, 100))

    # Reduce colors (uses k-means internally)
    paletted = img.convert('P', palette=Image.ADAPTIVE, colors=palette_size)

    # Find the color that occurs most often
    palette = paletted.getpalette()
    color_counts = sorted(paletted.getcolors(), reverse=True)
    palette_index = color_counts[0][1]
    dominant_color = palette[palette_index*3:palette_index*3+3]

    return dominant_color

def processText (path, target_language): 
    result = [] 
    for filename in os.listdir(path):
        index = int(filename.split(".")[0][4:])
        if not filename.endswith(".jpg"):
            continue
        full_path = os.path.join(path, filename)

        # get countours 
        contours, im2 = getCountours(full_path)

        # Initialize arrays 
        arr = []
        arr.append(im2)
        arr.append(index)
        for cnt in tqdm(contours, desc="Processing text of image " + str(index) + ": "):
            x, y, w, h = cv2.boundingRect(cnt)

            # don't have our bounding boxes too big!
            if h > im2.shape[0] * 0.5 or w > im2.shape[1] * 0.5:
                continue
            
            # Cropping the text block for giving input to OCR
            cropped = im2[y:y + h, x:x + w]
            
            # dominant color
            dominant_color = get_dominant_color(Image.fromarray(cropped))
            r, g, b = dominant_color 
            
            # Apply OCR on the cropped image
            text = re.sub(r'[\x00-\x1f]+', '',  pytesseract.image_to_string(cropped))
            if len(text) <= 1: continue; # no short text

            # Translate ----------------- TEST (for now, not translating) ---------------- 
            if text != "": 
                text = translateText(text, target_language)
            
            # append to array
            arr.append([x, y, w, h, text, r, g, b])
        result.append(arr)
    return result