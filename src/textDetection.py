import cv2                      # Image processing and countour detection
import os                       # Path
from tqdm import tqdm           # Progress Bar
import numpy as np              # average color calculations
import pickle                   # For caching detection (brings it MUCH easier to changeImage.py)
from termcolor import colored   # For color on terminal (used to send out warnings)

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



def detectParagraphs (lines, page, target_lang, x_threshold=50): 
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
        # value is a bunch of bounding boxes that correspond to each line in the paragraph
        arr[index] = Paragraph(value, page, index, target_lang)        

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
        paragraphs = detectParagraphs(lines, index, target_language) 
        page = Page(paragraphs, im2)
        page.apply_ocr()

        # Append to pages 
        pages.append(page)
    
    # cache pages
    with open(os.path.join(os.getcwd(), "src", "PagesCache", "Page.pkl"), "wb") as f: # "wb" because we want to write in binary mode
        pickle.dump(pages, f)
        
    return pages