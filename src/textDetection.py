from distutils.command.clean import clean
import cv2                      # Image processing and countour detection
import os                       # Path
from tqdm import tqdm           # Progress Bar
import numpy as np              # average color calculations
import pickle                   # For caching detection (brings it MUCH easier to changeImage.py)
from termcolor import colored   # For color on terminal (used to send out warnings)
import easyocr                  # Easy OCR for text detection and extraction

import re                # For some reason pytesseract adds in \n and \x0c. This will remove it
from Paragraph import *  # Paragraph class and Bounding Box class


def get_overall_box (boxs): 
    TLminX = -1
    TLminY = -1
    BRmaxX = -1 
    BRmaxY = -1
    for box in boxs: 
        if TLminX == -1: TLminX = box[0]
        if TLminY == -1: TLminY = box[1]
        if BRmaxX == -1: BRmaxX = box[0] + box[2]
        if BRmaxY == -1: BRmaxY = box[1] + box[3]
        
        if box[0] < TLminX: TLminX = box[0]
        if box[1] < TLminY: TLminY = box[1]
        if box[0] + box[2] > BRmaxX: BRmaxX = box[0] + box[2]
        if box[1] + box[3] > BRmaxY: BRmaxY = box[1] + box[3]
    return TLminX, TLminY, BRmaxX - TLminX, BRmaxY - TLminY

def is_surrounded (boxOne, boxTwo):
    x_val = boxTwo[0]
    y_val = boxTwo[1]
    if  x_val >= boxOne[0] and x_val <= boxOne[0] + boxOne[2] and \
        y_val >= boxOne[1] and y_val <= boxOne[1] + boxOne[3]:
        return True
    
    x_val = boxTwo[0] + boxTwo[2]
    y_val = boxTwo[1]
    if  x_val >= boxOne[0] and x_val <= boxOne[0] + boxOne[2] and \
        y_val >= boxOne[1] and y_val <= boxOne[1] + boxOne[3]:
        return True

    x_val = boxTwo[0] 
    y_val = boxTwo[1] + boxTwo[3]
    if  x_val >= boxOne[0] and x_val <= boxOne[0] + boxOne[2] and \
        y_val >= boxOne[1] and y_val <= boxOne[1] + boxOne[3]:
        return True

    x_val = boxTwo[0] + boxTwo[2]
    y_val = boxTwo[1] + boxTwo[3]
    if  x_val >= boxOne[0] and x_val <= boxOne[0] + boxOne[2] and \
        y_val >= boxOne[1] and y_val <= boxOne[1] + boxOne[3]:
        return True

    return False

def orderResult (result):
    arr = []
    result = sorted(result , key=lambda k: k[1])
    for obj in result:
        if len(arr) == 0: 
            arr = [[obj]]
            continue
        
        for index, out in enumerate(arr): 
            lead_box = out[-1]

            if len(obj[4]) < 20: break

            if abs(obj[1] - lead_box[1]) == 0 and abs(obj[0] - lead_box[0]) == 0:
                break

            if abs(obj[1] - lead_box[1]) < obj[3]:
                arr[index].append(obj)
                break

            if index == len(arr) - 1: 
                arr.append([obj])

    output = []
    for i in arr: 
        output.extend(sorted(i, key=lambda k: k[0]))

    return output

def constructPage (result, page_num, target_lang, image, threshold_similarity=100):
    # Construct the page class based on the EasyOCR result

    # First, clean the result
    cleaned_result = []
    for res in result: 
        bbox = res[0]
        text = res[1] 
        confidenceStore = res[2]
    
        # else get x, y, w, h from bounding box
        x = bbox[0][0]
        y = bbox[0][1]
        w = bbox[1][0] - bbox[0][0]
        h = bbox[2][1] - bbox[1][1]
        
        cleaned_result.append( (x, y, w, h, text, confidenceStore) )

    cleaned_result = orderResult(cleaned_result)
    print(cleaned_result)

    # Then, group bounding boxes according to proximitity
    threshold_similarity = 150
    arr = {}

    for line in cleaned_result:
        if len(arr) == 0:
            arr[(line[0], line[1], line[2], line[3])] = [line]
            continue
        index = 0 
        while True: 
            bbox = list(arr.keys())[index]
            
            # If it is next the left
            if abs(bbox[0] - (line[0] + line[2])) < threshold_similarity and abs(line[1] - bbox[1]) < line[3]:
                other_bbox = arr[bbox]
                other_bbox.append(line)
                arr.pop(bbox, None)
                arr[get_overall_box(other_bbox)] = other_bbox
                break

            # If it is next to the right
            if abs(line[0] - (bbox[0] + bbox[2])) < threshold_similarity and abs(line[1] - bbox[1]) < line[3]: 
                other_bbox = arr[bbox]
                other_bbox.append(line)
                arr.pop(bbox, None)
                arr[get_overall_box(other_bbox)] = other_bbox
                break
            
            # If it is to the top
            if abs(bbox[1] - (line[1] + line[3])) < threshold_similarity and abs(line[0] - bbox[0]) < line[2]:
                other_bbox = arr[bbox]
                other_bbox.append(line)
                arr.pop(bbox, None)
                arr[get_overall_box(other_bbox)] = other_bbox
                break

            # If it is to the bottom
            if abs(line[1] - (bbox[1] + bbox[3])) < threshold_similarity and abs(line[0] - bbox[0]) < line[2]:
                other_bbox = arr[bbox]
                other_bbox.append(line)
                arr.pop(bbox, None)
                arr[get_overall_box(other_bbox)] = other_bbox
                break

            if is_surrounded(bbox, line): 
                other_bbox = arr[bbox]
                other_bbox.append(line)
                arr.pop(bbox, None)
                arr[get_overall_box(other_bbox)] = other_bbox
                break
        
            # Else append to new section
            if index == len(arr) - 1:
                arr[(line[0], line[1], line[2], line[3])] = [line]
                break

            # Increment index
            index += 1

    # for each group, construct paragraph
    paragraphs = []
    paragraph_id = 0
    for overallBox in arr.keys(): 
        lines = [] 
        texts = []
        group = arr[overallBox]
        for line in group: 
            lines.append(BoundingBox(line[0], line[1], line[2], line[3]))
            texts.append(line[4])
        paragraphs.append(Paragraph(lines, overallBox, texts, page_num, paragraph_id, target_lang))
        paragraph_id += 1

    return Page(paragraphs, image)

def processText (path, target_language): 
    reader = easyocr.Reader(['en'])
    # This is the actual processtext array that stores an array of paragraphs 
    pages = []

    for filename in tqdm(os.listdir(path), desc="Processing Pages", unit="page"):
        if not filename.endswith(".jpg"):
            continue
        index = int(re.findall(r'\d+', filename.split(".")[0])[0])
        full_path = os.path.join(path, filename)
        image = cv2.imread(full_path)
    
        # Put image into EasyOCR
        result = reader.readtext(full_path)  

        # Construct page and append
        page = constructPage(result, index, target_language, image)
        page.display_page()
        page.translate()
        pages.append(page)
    
    # cache pages
    with open(os.path.join(os.getcwd(), "src", "PagesCache", "Page.pkl"), "wb") as f: # "wb" because we want to write in binary mode
        pickle.dump(pages, f)
        
    return pages