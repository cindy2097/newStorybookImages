# Storybook Translation

This project will attempt extract text from a pdf and then try to output a new version of the PDF, but with the translated version. 

## Dependencies

* Install `pdf2image` python library using `pip3 install pdf2image`
* However, `pdf2image` requires `pdftoppm`, so install this using `sudo apt install poppler-utils`. You could install the [Mac Version](https://macappstore.org/poppler/) or the [Windows Version](https://sourceforge.net/projects/poppler-win32/) as well. 
* Also install `img2pdf` using `pip3 install img2pdf`
* Install cv2 (image processing) using `pip3 install opencv-python`
* Install pytesseract (OCR) python library using `pip3 install pytesseract`
* However, you do have to install the backend of pytesseract using `sudo apt install tesseract-ocr`. Then, you add the file into line `11` of the file `textDetection.py` (alternatively, you could add the file to your path).
* Install tqdm (progress bar) using `pip3 install tqdm`
* Install numpy using `pip3 install numpy`

## Usage: 

Then, you could use the program in this format: <br>
`python3 StoryboardTranslate.py [path to input PDF] [path to output folder]` <br>
Example (Linux): <br>
`python3 StoryboardTranslate.py ./input/MaryHadALittleLamb.pdf ./output/`

## Pipeline: 

1. First converts the PDF into a PNG image (no image extraction occurs, just simple conversion between PDF to multiple PNG images), Then stores the PNG images in a seperate, private folder

2. For each PNG image, text detection will occur. After this process, it should store a bounding box of the text, the translation of the selected text, and the average color in that bounding box (this will be used for font).

3. Then, fill the bounding box with the average color, and put the text in the middle of the bounding box. The font size will be calculated according to height of the bounding box and the font color will be either white or black, which is determined by the average color.

4. Link the new PNG images back into a PDF format, and then save the PDF into the output folder.

5. Delete the PNG images

## TODO: 
* Collect all the images and combine them into the PDF (for now, it's just outputting to folder `./src/PNGImgsOutput`)
* Make font size adjust to the bounding box width & height.
* Improve contour system (sometimes it doesn't recognize all the words in the page)
* Font recognizer.