from turtle import width
import cv2              # Image processing and countour detection
import os               # Path
from tqdm import tqdm   # Progress Bar
import math             # Math operations for calculating contrast

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

def changeImage (processTextResult): 
    for img_result in tqdm(processTextResult, desc="Changing image: "): 
        img = img_result[0]
        index_image = img_result[1]
        for index in range(2, len(img_result)):
            x, y, w, h, text, r_avg, g_avg, b_avg = img_result[index]

            # fill image with average color
            img[y:y + h, x:x + w, 0] = r_avg
            img[y:y + h, x:x + w, 1] = g_avg
            img[y:y + h, x:x + w, 2] = b_avg

            # Figure out which best contrasts which average color
            color = [0,0,0]
            if contrast([255, 255, 255], [r_avg, g_avg, b_avg]) > contrast([0, 0, 0], [r_avg, g_avg, b_avg]):
                color = [255, 255, 255]

            # font scale
            scale = 1
            fontScale = 0.7 

            # thickness 
            thickness = 2

            # Then, add text 
            img = cv2.putText(img, text, (x, y+h), cv2.FONT_HERSHEY_SIMPLEX, fontScale, color, thickness)

        # save image
        file = os.path.join(os.getcwd(), "src", "PNGImgsOutput", "page"+str(index_image)+".jpg")
        cv2.imwrite(file, img) 