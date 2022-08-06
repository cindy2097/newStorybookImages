# Storybook Translation

This project will attempt extract text from a pdf and then try to output a new version of the PDF, but with the translated version. 

## Dependencies

* However, `pdf2image` requires `pdftoppm`, so install this using `sudo apt install poppler-utils`. You could install the [Mac Version](https://macappstore.org/poppler/) or the [Windows Version](https://sourceforge.net/projects/poppler-win32/) as well.
* However, you do have to install the backend of pytesseract using `sudo apt install tesseract-ocr`. Then, you add the file into line `66` of the file `Paragraph.py` (alternatively, you could add the file to your path).
* If you are on a mac, do  `brew list tesseract` and use the first result to add to your path.
* You also need to install requirements, it's just a simple `pip install -r requirements.txt`.
* Please create a file, SensitiveInfo.py, containing a single line, "auth_token=[neuralspace auth token]". Please ask Subha for the auth token
* Please create two folders in the src foler, "PNGImgs" and "PNGImgsOutput" and "PagesCache", also create a folder in the project called "output"

## RAQM:

Check https://stackoverflow.com/questions/62939101/how-to-install-pre-built-pillow-wheel-with-libraqm-dlls-on-windows for instructions on how to install RAQM, a library that's suppose to help with special character rendering.
Make sure that you put the <strong>64</strong> bit versions of raqm when you extract the .zip file into your Python path. 
You can check if RAQM is installed if you do:

```py
from PIL import features
features.check('raqm')
```

## Usage: 

Then, you could use the program in this format: <br>
`python3 StoryboardTranslate.py [path to input PDF] [path to output PDF]` <br>
Example (Linux): <br>
`python3 StoryboardTranslate.py ./input/GreenEggsHam.pdf ./output/TranslatedGreenEggsHam.pdf`

### Run on Ubuntu Linux 
#### Install the tesseract
If you run on the Ubuntu Linux, please follow the instructions: 
```
sudo apt update
sudo add-apt-repository ppa:alex-p/tesseract-ocr-devel
sudo apt install -y tesseract-ocr
```

If you can type in ```tesseract --version```, and get the reponse info about your version, then the installation should be finished.

#### Launch Project Environment
After we finished all the environment installations there, just do:
```
git clone https://github.com/linguisticsjusticeleague/newStorybookImages.git
pip -r requirements.txt
cd newStorybookImages/src
vim Paragraph.py
```
Please change the ```$PATH``` to your local address, in case that your machine will not find your tesseract. You can find your tesseract local path by: ```which tesseract```
```
# ---------------- CHANGE THIS TO YOUR TESSERACT OCR FILE ------------------------------------------ #
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract(please change your $path if necessary)"
# -------------------------------------------------------------------------------------------------- #
```
We can install the language OCR packages by simply run:
```
sudo apt-get install tesseract-ocr-eng  #for english
sudo apt-get install tesseract-ocr-tam  #for tamil
sudo apt-get install tesseract-ocr-deu  #for deutsch (German)
```
After you finished all of these settings, then you may enjoy your EduLang Journey on Ubuntu Linux!
## Pipeline: 

1. First converts the PDF into a PNG image (no image extraction occurs, just simple conversion between PDF to multiple PNG images), Then stores the PNG images in a seperate, private folder

2. For each PNG image, text detection will occur. After this process, it should store a bounding box of the text, the translation of the selected text, and the average color in that bounding box (this will be used for font).

3. Then, fill the bounding box with the average color, and put the text in the middle of the bounding box. The font size will be calculated according to height of the bounding box and the font color will be either white or black, which is determined by the average color.

4. Link the new PNG images bimageack into a PDF format, and ten save the PDF into the output folder.

5. Delete the PNG images



## TODO: 
* Add the text in a seperate area instead of a whole seperate image
* Improve contour system (sometimes it doesn't recognize all the words in the page)
* Font recognizer.
