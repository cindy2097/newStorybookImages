from distutils.command.clean import clean
import cv2
from matplotlib.pyplot import box

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

def is_surrounded (boxOne, boxTwo, margin=10):
    if  boxOne[0] < boxTwo[0] + margin and boxOne[1] < boxTwo[1] + margin and \
        boxOne[0] + boxOne[2] > boxTwo[0] + boxTwo[2] - margin and boxOne[1] + boxOne[3] > boxTwo[1] + boxTwo[3] - margin: 
        return True
    else: 
        return False

cleaned_result = [
   (682, 1148, 1046, 76, 'She makes every day a BIG adventure:', 0.7314303598532425),
   (504, 1221, 1402, 78, 'Like the time we had to get out of a murukku maze:', 0.6275720523885695),
   (588, 1297, 844, 75, '"Iknow! Let\'s eat our way out;', 0.8384795330620138), 
   (1462, 1297, 361, 66, 'Ameera said:', 0.4576488462756366), 
   (2213, 1567, 86, 38, '11/12', 0.9999868852341599), 
   (415, 659, 204, 162, 'J', 0.8500133120126208),
   (0, 0, 200, 100, 'hello', 0.6633)
]

image = cv2.imread("./src/PNGImgs/page11.jpg")
for result in cleaned_result: 
    image = cv2.rectangle(image, (result[0], result[1]), (result[0] + result[2], result[1] + result[3]), (255, 0, 0), 3)

threshold_similarity = 50
arr = {}

for line in cleaned_result:
    if len(arr) == 0:
        arr[(line[0], line[1], line[2], line[3])] = [line]
        continue
    index = 0 
    while True: 
        bbox = list(arr.keys())[index]
        
        # If box is circumstanced
        if is_surrounded(bbox, line): 
            other_bbox = arr[bbox]
            other_bbox.append(line)
            arr.pop(bbox, None)
            arr[get_overall_box(other_bbox)] = other_bbox
            break

        # If it is next the right
        if line[0] + line[2] - bbox[0] > 0 and line[0] + line[2] - bbox[0] < threshold_similarity and abs(line[1] - bbox[1]) < line[3]:
            other_bbox = arr[bbox]
            other_bbox.append(line)
            arr.pop(bbox, None)
            arr[get_overall_box(other_bbox)] = other_bbox
            break

        # If it is next to the left
        if bbox[0] + bbox[2] - line[0] > 0 and bbox[0] + bbox[2] - line[0] < threshold_similarity and abs(line[1] - bbox[1]) < line[3]: 
            other_bbox = arr[bbox]
            other_bbox.append(line)
            arr.pop(bbox, None)
            arr[get_overall_box(other_bbox)] = other_bbox
            break
        
        # If it is to the bottom
        if line[1] + line[3] - bbox[1] > 0 and line[1] + line[3] - bbox[1] < threshold_similarity and abs(line[0] - bbox[0]) < line[2]:
            other_bbox = arr[bbox]
            other_bbox.append(line)
            arr.pop(bbox, None)
            arr[get_overall_box(other_bbox)] = other_bbox
            break

        # If it is to the up
        if bbox[1] + bbox[3] - line[1] > 0 and bbox[1] + bbox[3] - line[1] < threshold_similarity and abs(line[0] - bbox[0]) < line[2]:
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

# Then, for each group, order the boxes so that the text is read from left to right, top to bottom

print(arr)
for result in arr.keys(): 
    image = cv2.rectangle(image, (result[0], result[1]), (result[0] + result[2], result[1] + result[3]), (0, 255, 0), 1)


cv2.imshow("sdf", image)
cv2.waitKey(0)