import cv2

path = "./src/PNGImgs/page18.jpg"
cleaned_result = [
    (189, 255, 564, 44, 'Not on a train! Not in a treel', 0.7288129539465469),
    (189, 327, 578, 44, 'Not in & car! Sam! Let me bel', 0.46120486492448887),
    (186, 465, 616, 51, 'I would not, could not, in a box:', 0.5219111776100407),
    (185, 679, 584, 44, 'I will not eat them in a house.', 0.8977292133846967),
    (186, 536, 659, 52, 'I could not, would not, with a fox:', 0.6324716575390233),
    (187, 607, 641, 44, 'I will not eat them with a mouse.', 0.971793216302286),
    (187, 749, 634, 44, 'I will not eat them here or there.', 0.9693823392082287),
    (183, 814, 578, 60, 'I will not eat them anywhere.', 0.9399067400074017),
    (186, 886, 634, 54, 'I do not eat green eggs and ham.', 0.8434659704566985),
    (186, 956, 577, 52, 'I do not like them, Sam-I-am.', 0.5080469140564196)
]

def orderResult (result):
    arr = []
    result = sorted(cleaned_result , key=lambda k: k[1])
    for obj in result:
        if len(arr) == 0: 
            arr = [[obj]]
            continue
        
        for index, out in enumerate(arr): 
            lead_box = out[-1]

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

cleaned_result = orderResult(cleaned_result)

for i in cleaned_result:
    print("Bbox x:", i[0], "y:", i[1], "w:", i[2], "h:", i[3], "Message:", i[4])


image = cv2.imread(path)
for result in cleaned_result: 
    image = cv2.rectangle(image, (round(result[0]), round(result[1])), (round(result[0]+result[2]), round(result[1]+result[3])), (255, 0, 0), 3)
cv2.namedWindow("Window", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Window", 1000, 800)
cv2.imshow("Window", image)
cv2.waitKey(0)

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

# Then, group bounding boxes according to proximitity
threshold_similarity = 100
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


# Displaying 
image = cv2.imread(path)

for i in arr.keys():
    print("Overall box: ", i)
    print("Children boxes: ")
    for index, child in enumerate(arr[i]):
        print("Index:", index+1, "Bbox:", child)
    print("------------------")
    image = cv2.rectangle(image, (round(i[0]), round(i[1])), (round(i[0]+i[2]), round(i[1]+i[3])), (255, 0, 0), 3)

cv2.namedWindow("Window", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Window", 1000, 800)
cv2.imshow("Window", image)
cv2.waitKey(0)