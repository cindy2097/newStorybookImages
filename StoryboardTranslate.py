import sys              # getting the arguments
import pdf2image        # Thankfully, this handles most of step 1
from tqdm import tqdm   # Progress bar!
import os, sys          # Path
sys.path.insert(1, "./src/")
from textDetection import processText # Text detection for 2nd step
from changeImage import changeImage   # Change the image from text detection for 3rd step
import fpdf                               # Used for connecting images to a single pdf
from termcolor import colored             # For color on terminal
import pickle                         # For reading cache of pages

def img_to_pdf (input_dir, output_file): 
    pdf = fpdf.FPDF('L', 'mm', 'A4')
    
    list_dir = os.listdir(input_dir)
    sorted_arr = {}
    for path in list_dir:
        full_path = os.path.join(input_dir, path)
        index = int(str(path).split(".")[0][4:])
        sorted_arr[index] = full_path 

    # imagelist is the list with all image filenames
    for key in sorted(sorted_arr.keys()):
        image = sorted_arr[key]
        if not image.endswith(".jpg"):
            continue
        pdf.add_page()
        pdf.image(image,0,0,300,225) #the 300 and 250 is the size for the image to be blown up to
    pdf.output(output_file, "F")

def convertPDFToImage (path, cut_begin, cut_end): 
    for file in os.listdir(os.path.join(os.getcwd(), "src", "PNGImgs")):
        if file.endswith(".jpg"):
            print(colored("Skipping Image Extraction! Using images in src/PNGImgs directory. (pages removed from beginning/end are not executed)", "red"))
            return
    print("Converting pdf to images...", end="")
    pages = pdf2image.convert_from_path(path)
    for index, page in enumerate(pages):
        if index < cut_begin:
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
    pdf_cut_begin = int(input("How much pages do you want to remove from the beginning? "))
    pdf_cut_end = int(input("How much pages do you want to remove from the end? "))

    # Initializes all the directories
    full_path_img_dir = os.path.join(os.getcwd(), "src", "PNGImgs")
    pages_cache_dir = os.path.join(os.getcwd(), "src", "PagesCache")
    out_img_dir = os.path.join(os.getcwd(), "src", "PNGImgsOutput")

    # check if cache 
    pages = None
    for filename in os.listdir(pages_cache_dir):
        full_path = os.path.join(pages_cache_dir, filename)
        print(colored("Skipping text detection! Using cache.", "red"))
        with open(full_path, "rb") as f:
            pages = pickle.load(f)
            break

    # If we do not have cache, then generate the pages manually
    if pages == None: 
        # First step: Convert PDF into multiple PNG images
        convertPDFToImage(input_pdf_path, pdf_cut_begin, pdf_cut_end) 

        # Second step: get text detection file to get bounding boxes, translation, and average color 
        pages = processText(full_path_img_dir, target_language)

    # Third Step: Alter image to for fill bounding box with average color, and with new translation
    changeImage(pages)

    # Fourth Step: Create PDF based on the images, then save the PDF to the output folder
    print("Converting images to pdf...", end="")
    img_to_pdf(out_img_dir, output_pdf_file)
    print("Done")

    # Fifth Step: Delete contents in directories: PNGImgs, PNGImgsOutput
    print("Remove contents from directories...",end="")
    # [os.remove(os.path.join(full_path_img_dir, file)) for file in os.listdir(full_path_img_dir)]
    # [os.remove(os.path.join(out_img_dir, file)) for file in os.listdir(out_img_dir)]
    [os.remove(os.path.join(pages_cache_dir, file)) for file in os.listdir(pages_cache_dir)]
    print("Done")
    