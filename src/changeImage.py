import cv2                # Image processing and countour detection
import os                 # Path
from tqdm import tqdm     # Progress Bar
import math               # Math operations for calculating contrast
from PIL import ImageDraw # Library for drawing
from PIL import ImageFont # Library for drawing 
from PIL import Image     # Library for drawing
import numpy              # For image conversion 

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

def changeImage (processTextResult, lan): 
    for img_result in tqdm(processTextResult, desc="Changing image: "): 
        img = img_result[0]
        index_image = img_result[1]
        fontpath = os.path.join(os.getcwd(), "src", "Fonts", "ArialUnicodeMs.ttf")
        img_fraction = 0.95 # portion of image width you want text width to be
        optimal_font_size = 1
        font = ImageFont.truetype(fontpath, optimal_font_size)
        for index in range(2, len(img_result)):
            x, y, w, h, text, r_avg, g_avg, b_avg = img_result[index]

            # fill image with average color
            img[y:y + h, x:x + w, 0] = r_avg
            img[y:y + h, x:x + w, 1] = g_avg
            img[y:y + h, x:x + w, 2] = b_avg

            # Figure out which best contrasts which average color
            color = (0,0,0)
            if contrast([255, 255, 255], [r_avg, g_avg, b_avg]) > contrast([0, 0, 0], [r_avg, g_avg, b_avg]):
                color = (255, 255, 255)

            # get optimal font size 
            if optimal_font_size == 1: 
                while font.getsize(text)[1] < img_fraction*h:
                    optimal_font_size += 1 # iterate until the text size is just larger than the criteria
                    font = ImageFont.truetype(fontpath, optimal_font_size)
            while font.getsize(text)[0] > img_fraction*w:
                optimal_font_size -= 1
                font = ImageFont.truetype(fontpath, optimal_font_size)

            # Then, add text 
            img_pil = Image.fromarray(img)
            draw = ImageDraw.Draw(img_pil)
            draw.text((x, y+(h/2)),text, fill=color, font = font)
            img = numpy.array(img_pil)

        # save image
        file = os.path.join(os.getcwd(), "src", "PNGImgsOutput", "page"+str(index_image)+".jpg")
        cv2.imwrite(file, img) 