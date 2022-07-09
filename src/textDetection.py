import cv2               # Image processing and countour detection
import os                # Path
from tqdm import tqdm    # Progress Bar
import numpy as np       # average color calculations
import requests          # For requesting translation to server.
import json              # For extraction of translation from server
import SensitiveInfo     # Sensitive Info (ex: auth token) regarding connection to the server
import re                # For some reason pytesseract adds in \n and \x0c. This will remove it
from Paragraph import *  # Paragraph class and Bounding Box class

# most of the code is from https://www.geeksforgeeks.org/text-detection-and-extraction-using-opencv-and-ocr/
def getCountours (path): 
    img = cv2.imread(path)
    
    # Convert the image to gray scale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Performing OTSU threshold (highlights edges)
    _, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
    
    # Specify structure shape and kernel size.
    # Kernel size increases or decreases the area
    # of the rectangle to be detected.
    # A smaller value like (10, 10) will detect
    # each word instead of a sentence.
    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    
    # Applying dilation on the threshold image (somewhat blurs the image so that the bounding box can generalize)
    dilation = cv2.dilate(thresh1, rect_kernel, iterations = 1)

    # Finding contours
    contours, _ = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return contours, img.copy()

def removeChar(text): 
    special_char_dict = {
        "’": "'",
        "”": "'",
        "“": "'",
        "—": "-"
    }
    for key in special_char_dict:
        text = text.replace(key, special_char_dict[key])

    return text 

def translateText (text, target_language): 
    if text != "":
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
            "text": "{removeChar(text)}",
            "sourceLanguage": "en",
            "targetLanguage": "{target_language}"
        }}
        """
        resp = requests.post(url, headers=headers, data=data)
        response_dict = json.loads(resp.text)
        return response_dict["data"]["translatedText"]
    else: 
        return ""

def detectParagraphs (lines, page, x_threshold=50): 
    # Given a set of points, give a bounding box of each point
    arr = [] 
    for line in lines:
        if len(arr) == 0:
            arr.append([line])
            continue
        for index, value in enumerate(arr): 
            if abs(value[0].x - line.x) <= x_threshold:
                arr[index].append(line)
                break
            if index == len(arr) - 1: arr.append([line])

    # Replace each array of points with Paragraph class 
    for index, value in enumerate(arr): 
        arr[index] = Paragraph(value, page, index)        

    return arr

def processText (path, target_language): 
    # This is the actual processtext array that stores an array of paragraphs 
    pages = []

    for filename in tqdm(os.listdir(path), desc="Processing Pages", unit="page"):
        if not filename.endswith(".jpg"):
            continue
        index = int(re.findall(r'\d+', filename.split(".")[0])[0])
        full_path = os.path.join(path, filename)

        # get countours 
        contours, im2 = getCountours(full_path)

        # Array that stores x, y, w, and h of the line
        lines = []

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)

            # don't have our bounding boxes too big!
            if h > im2.shape[0] * 0.5 or w > im2.shape[1] * 0.5:
                continue

            # don't have our bounding boxes too small!
            if w < im2.shape[0] * 0.01 or h < im2.shape[1] * 0.01:
                continue
        
            # Append points
            lines.append(BoundingBox(x, y, w, h))

        # Get paragraph and page
        paragraphs = detectParagraphs(lines, index) 
        page = Page(paragraphs, im2)
        page.apply_ocr()
    
        # Append to pages 
        pages.append(page)
        
    # ----- Translation ---- 
    print("Translating Text...", end="")
    text_sep = " +++ "
    info_sep = " === "
    send_string = [] 
    for page in pages:
        send_string.append(page.text_to_string(text_sep, info_sep))
    send_string = text_sep.join(send_string)
    translated_string = translateText(send_string, target_language)
    for page in pages: 
        page.string_to_text(translated_string)
    print("Done")

    return pages