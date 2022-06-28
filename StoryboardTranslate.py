import sys              # getting the arguments
import pdf2image        # Thankfully, this handles most of step 1
from tqdm import tqdm   # Progress bar!
import os               # Path
from src.textDetection import processText # Text detection for 2nd step
from src.changeImage import changeImage   # Change the image from text detection for 3rd step

def convertPDFToImage (path): 
    for file in os.listdir(os.path.join(os.getcwd(), "src", "PNGImgs")):
        if file.endswith(".jpg"):
            print("Images already extracted.")
            return
    print("Converting pdf to images...")
    pages = pdf2image.convert_from_path(path)
    for index, page  in tqdm(enumerate(pages)):
        cwd = os.getcwd()
        path = os.path.join(cwd, "src", "PNGImgs", "page"+str(index)+".jpg")
        page.save(path, "JPEG")

if __name__ == "__main__":
    argument_count = len(sys.argv) - 1 
    if argument_count != 2: 
        print("There must be two arguments: [path to input PDF] and [path to output folder]")
        exit(-1)
    input_pdf_path = sys.argv[1]
    output_pdf_folder = sys.argv[2]
    target_language = input("What's the language you want to convert it to? ") 

    # First step: Convert PDF into multiple PNG images
    convertPDFToImage(input_pdf_path) 

    # Second step: get text detection file to get bounding boxes, translation, and average color 
    full_path_img_dir = os.path.join(os.getcwd(), "src", "PNGImgs")
    result = processText(full_path_img_dir, target_language)

    # Third Step: Alter image to for fill bounding box with average color, and with new translation
    changeImage(result)
    