from re import I
import cv2                # Image processing and countour detection
import os                 # Path
from tqdm import tqdm     # Progress Bar
import math               # Math operations for calculating contrast
from PIL import ImageDraw # Library for drawing
from PIL import ImageFont # Library for drawing 
from PIL import Image     # Library for drawing
import numpy as np        # For image conversion 
from Paragraph import *   # Import Paragraph, BoundingBox, and Page classes
from typing import cast   # To enable accurate and helpful autocomplete during developing :) 
from copy import deepcopy # For deepcopying the bounding boxes for comparison

# https://stackoverflow.com/questions/9733288/how-to-programmatically-calculate-the-contrast-ratio-between-two-colors
def luminance (r, g, b): 
    array = []
    for a in [r, g, b]:
        a /= 255
        if a <= 0.03928: 
            a /= 12.92
        else: 
            a = math.pow(((a + 0.055) / 1.055), 2.4)
        array.append(a)
    return array[0] * 0.2126 + array[1] * 0.7152 + array[2] * 0.0722

def contrast (rgb1, rgb2): 
    lum1 = luminance(rgb1[0], rgb1[1], rgb1[2])
    lum2 = luminance(rgb2[0], rgb2[1], rgb2[2])
    brightest = max(lum1, lum2)
    darkest = min(lum1, lum2)
    return (brightest + 0.05) / (darkest + 0.05)

def changeImage (processTextResult:list[Page]): 
    for page in tqdm(processTextResult, desc="Changing image: "): 
        pageNum = 0
        page = cast(Page, page) 
        img = page.original_image
        img_h = img.shape[0] 
        img_w = img.shape[1]  

        for orig_paragraph in page.paragraphs:
            #================ Find the Appropiate Bounding Box to Place next to original Text ================#
            
            # get all potential boxes in all four directions
            left_para = deepcopy(orig_paragraph).apply_offset(offset_x=-orig_paragraph.paragraphBox.w)
            right_para = deepcopy(orig_paragraph).apply_offset(offset_x=orig_paragraph.paragraphBox.w)
            top_para = deepcopy(orig_paragraph).apply_offset(offset_y=-orig_paragraph.paragraphBox.h)
            bottom_para = deepcopy(orig_paragraph).apply_offset(offset_y=orig_paragraph.paragraphBox.h)
            options:list[Paragraph] = [left_para, right_para, top_para, bottom_para]

            # Elimate all boxes that are out of bounds from image
            elim:list[Paragraph] = [] 
            for option in options: 
                if option.out_of_bounds(img_w, img_h):
                    elim.append(option)
            for el in elim: 
                options.remove(el)
            
            # If there's no boxes left, then complain 
            if len(options) == 0:
                print("Unable to find suitable location")
                continue

            # For the rest of the boxes, assign a score to them that has the most average color closer to paragraph dominant color
            lowest_score = -1 
            best_para:Paragraph = None
            for option in options: 
                cropped_img = option.paragraphBox.crop_img(img)
                avg_color = np.average(cropped_img, axis=(0,1)).tolist()
                score = contrast(avg_color, orig_paragraph.dominant_color)
                if score < lowest_score or lowest_score == -1: 
                    score = lowest_score
                    best_para = option
            bb_best = best_para.paragraphBox

            #============== Add Translated Text to Bounding Box ==============#
            # get best font size 
            img_fraction = 0.95
            fontpath = os.path.join(os.getcwd(), "src", "Fonts", "ArialUnicodeMs.ttf")
            optimal_font_size = 1
            font = ImageFont.truetype(fontpath, optimal_font_size)

            # get largest text
            largest_text = ""
            for text in best_para.texts: 
                if len(text) > len(largest_text): 
                    largest_text = text

            # Adjust font according to height and width
            font_dim_text = font.getsize(largest_text)
            while (font_dim_text[0] < img_fraction * bb_best.w) and (font_dim_text[1] < img_fraction * bb_best.h):
                optimal_font_size += 1 
                font = ImageFont.truetype(fontpath, optimal_font_size)
                font_dim_text = font.getsize(largest_text)

            # Fill in background color
            img[bb_best.y : bb_best.y + bb_best.h, bb_best.x : bb_best.x + bb_best.w, 0] = best_para.dominant_color[0]
            img[bb_best.y : bb_best.y + bb_best.h, bb_best.x : bb_best.x + bb_best.w, 1] = best_para.dominant_color[1]
            img[bb_best.y : bb_best.y + bb_best.h, bb_best.x : bb_best.x + bb_best.w, 2] = best_para.dominant_color[2]

            # Find which color best contrasts dominant color
            color = (0,0,0)
            if contrast([255, 255, 255], best_para.dominant_color) > contrast([0,0,0], best_para.dominant_color):
                color = (255, 255, 255)

            # Add text
            img_pil = Image.fromarray(img)
            draw = ImageDraw.Draw(img_pil)
            for index in range(len(best_para.lines)):
                bb = best_para.lines[index]
                text = best_para.texts[index]
                draw.text((bb.x, bb.y + (bb.h/2)), text, fill=color, font=font)
            img = np.array(img_pil)

            # set page number
            pageNum = best_para.pageNum
        
        # Save image
        file = os.path.join(os.getcwd(), "src", "PNGImgsOutput", "page"+str(pageNum)+".jpg")
        cv2.imwrite(file, img)