import sys              # getting the arguments
import pdf2image        # Thankfully, this handles most of step 1
from tqdm import tqdm   # Progress bar!
import os               # Path
from src.textDetection import processText # Text detection for 2nd step
from src.changeImage import changeImage   # Change the image from text detection for 3rd step
import fpdf                               # Used for connecting images to a single pdf

def img_to_pdf (input_dir, output_file): 
    pdf = fpdf.FPDF('L', 'mm', 'A4')
    # imagelist is the list with all image filenames
    for image in sorted(os.listdir(input_dir)):
        full_path = os.path.join(input_dir, image)
        pdf.add_page()
        #the 300 and 250 is the size for the image to be blown up to
        pdf.image(full_path,0,0,300,225)
    pdf.output(output_file, "F")

def convertPDFToImage (path, cut_begin, cut_end): 
    for file in os.listdir(os.path.join(os.getcwd(), "src", "PNGImgs")):
        if file.endswith(".jpg"):
            print("Images already extracted.")
            return
    print("Converting pdf to images...", end="")
    pages = pdf2image.convert_from_path(path)
    for index, page in enumerate(pages):
        if index <= cut_begin:
            continue
        if index > len(pages) - cut_end:
            break 
        cwd = os.getcwd()
        path = os.path.join(cwd, "src", "PNGImgs", "page"+str(index+1)+".jpg")
        page.save(path, "JPEG")
    print("Done")

if __name__ == "__main__":
    argument_count = len(sys.argv) - 1 
    if argument_count != 2: 
        print("There must be two arguments: [path to input PDF] and [path to output file]")
        exit(-1)
    input_pdf_path = sys.argv[1]
    output_pdf_file = sys.argv[2]
    target_language = input("What's the language you want to convert it to? ") 
    pdf_cut_begin = int(input("How much pages do you want to remove from the beggining? "))
    pdf_cut_end = int(input("How much pages do you want to remove from the end? "))

    # First step: Convert PDF into multiple PNG images
    convertPDFToImage(input_pdf_path, pdf_cut_begin, pdf_cut_end) 

    # Second step: get text detection file to get bounding boxes, translation, and average color 
    full_path_img_dir = os.path.join(os.getcwd(), "src", "PNGImgs")
    result = processText(full_path_img_dir, target_language)

    # Third Step: Alter image to for fill bounding box with average color, and with new translation
    changeImage(result, target_language)

    # Fourth Step: Create PDF based on the images, then save the PDF to the output folder
    print("Combining images...", end="")
    out_img_dir = os.path.join(os.getcwd(), "src", "PNGImgsOutput")
    img_to_pdf(out_img_dir, output_pdf_file)
    print("Done")

    # Fifth Step: Delete contents in directories: PNGImgs, PNGImgsOutput
    print("Remove contents from directories...",end="")
    [os.remove(os.path.join(full_path_img_dir, file)) for file in os.listdir(full_path_img_dir)]
    [os.remove(os.path.join(out_img_dir, file)) for file in os.listdir(out_img_dir)]
    print("Done")
    