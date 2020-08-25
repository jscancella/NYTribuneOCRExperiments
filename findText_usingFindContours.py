import os
from pathlib import Path
os.environ['OPENCV_IO_ENABLE_JASPER']='True' #has to be set before importing cv2 otherwise it won't read the variable
import cv2
import numpy as np
from multiprocessing import Pool
import subprocess

#Items to tweak if needed for different results
MIN_COLUMN_WIDTH=450 #what to consider is the minimum width of a column. Anything smaller will be rejected
MIN_COLUMN_HEIGHT=100 #what to consider is the minimum height of a column. Anything smaller will be rejected
LINE_THICKNESS = 3 #how thick to make the line around the found contours in the debug output
PADDING = 10 #padding to add around the found contour(possible column) to help account for image skew and such
LAST_LINE_OF_TOP_OF_IMAGE = 1000 #only check up to this line for possible lines or title
LINE_LENGTH_TO_REMOVE = 1000 #any line that is this long or longer will be removed from the top of the image
CREATE_INTERMEDIATE_IMAGES=False #create debug files that show how each step is transforming the image.
BATCH_LOCATION = 'F:/dlc_gritty_ver01' #directory to start in to find the .jp2 files to process
TESSERACT = 'C:/Program Files/Tesseract-OCR/tesseract.exe'

"""
# Cross-shaped Kernel
>>> cv2.getStructuringElement(cv2.MORPH_CROSS,(5,5))
array([[0, 0, 1, 0, 0],
       [0, 0, 1, 0, 0],
       [1, 1, 1, 1, 1],
       [0, 0, 1, 0, 0],
       [0, 0, 1, 0, 0]], dtype=uint8)
"""
#kernel = cv2.getStructuringElement(cv2.MORPH_CROSS,(5,5))

#custom kernel that is used to blend together text in the Y axis
DILATE_KERNEL = np.array([
       [0, 0, 0, 0, 1, 0, 0, 0, 0],
       [0, 0, 0, 0, 1, 0, 0, 0, 0],
       [0, 0, 0, 0, 1, 0, 0, 0, 0],
       [0, 0, 0, 0, 1, 0, 0, 0, 0],
       [0, 0, 0, 0, 1, 0, 0, 0, 0],
       [0, 0, 0, 0, 1, 0, 0, 0, 0],
       [0, 0, 0, 0, 1, 0, 0, 0, 0],
       [0, 0, 0, 0, 1, 0, 0, 0, 0],
       [0, 0, 0, 0, 1, 0, 0, 0, 0]], dtype=np.uint8)
       
NOISE_KERNEL = np.array([
       [1, 1, 0, 1, 1],
       [1, 1, 0, 1, 1],
       [1, 1, 0, 1, 1],
       [1, 1, 0, 1, 1],
       [1, 1, 0, 1, 1]], dtype=np.uint8)
       
# CLOSE_KERNEL = cv2.getStructuringElement(cv2.MORPH_CROSS,(5,5))
CLOSE_KERNEL = NOISE_KERNEL

BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
       
def blankOutTopOfImage(img, basename, debugOutputDirectory, debug=False):
    """
    assume the image has already been inverted and closed,
    try and find the bounding box around the title or top line and remove it by making it black
    """
    print("removing title and or top lines")
    temp_img = np.copy(img)
    contours, hierarchy = cv2.findContours(temp_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    fillRectangle = -1
    yStart = 0 #never changes because we always want to go from the top
    for contour in contours:
        #print("contour: ", contour)
        x,y,w,h = cv2.boundingRect(contour)
        
        if w > LINE_LENGTH_TO_REMOVE and y < LAST_LINE_OF_TOP_OF_IMAGE: #limit to long lines and in the top of the image
            temp_img = cv2.rectangle(temp_img,(x,0),(x+w,y+h), BLACK, fillRectangle)
    
    if debug:
        filepath = os.path.join(debugOutputDirectory, '%s-blankedout.tiff' % basename)
        cv2.imwrite(filepath, temp_img)
    
    return temp_img

def convertToGrayscale(img, basename, debugOutputDirectory, debug=False):
    print("converting to greyscale")
    temp_img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    if debug:
        filepath = os.path.join(debugOutputDirectory, '%s-greyscale.tiff' % basename)
        cv2.imwrite(filepath, temp_img)
    return temp_img

def invert(img, basename, debugOutputDirectory, debug=False):
    """
    Black becomes white in the image
    """
    print("invert image")
    _,temp_img = cv2.threshold(img, 140, 255, cv2.THRESH_BINARY_INV)
    if debug:
        filepath = os.path.join(debugOutputDirectory, '%s-invert.tiff' % basename)
        cv2.imwrite(filepath, temp_img)
    return temp_img
    
def removeNoise(img, basename, debugOutputDirectory, debug=False):
    """
    erosion followed by dilation. It is useful in removing noise
    """
    print("remove noise")
    temp_img = cv2.morphologyEx(img, cv2.MORPH_OPEN, NOISE_KERNEL)
    if debug:
        filepath = os.path.join(debugOutputDirectory, '%s-removeNoise.tiff' % basename)
        cv2.imwrite(filepath, temp_img)
    return temp_img

def dilateDirection(img, basename, debugOutputDirectory, debug=False):
    """
    It is just opposite of erosion. Here, a pixel element is '1' if atleast one pixel under the kernel is '1'. 
    So it increases the white region in the image or size of foreground object increases. 
    Normally, in cases like noise removal, erosion is followed by dilation. 
    Because, erosion removes white noises, but it also shrinks our object. 
    So we dilate it. Since noise is gone, they won't come back, but our object area increases. 
    It is also useful in joining broken parts of an object. 
    """
    print("applying dilation morph")
    temp_img = cv2.dilate(img, DILATE_KERNEL, iterations=15) #the more iterations the more the text gets stretched in the Y axis, 15 seems about right.
   
    if debug:
        filepath = os.path.join(debugOutputDirectory, '%s-dilation.tiff' % basename)
        cv2.imwrite(filepath, temp_img)
    return temp_img

def closeDirection(img, basename, debugOutputDirectory, debug=False):
    """
    Dilation followed by Erosion. It is useful in closing small holes inside the foreground objects, or small black points on the object
    """
    print("applying closing morph")
    temp_img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, CLOSE_KERNEL)
    if debug:
        filepath = os.path.join(debugOutputDirectory, '%s-close.tiff' % basename)
        cv2.imwrite(filepath, temp_img)
    return temp_img

def findContours(img, basename, debugOutputDirectory, debug=False):
    """
    Takes an image and performs a number of transformations on it to find the areas where there is (possibly) text
    It then returns these areas (contours) as well as the hierarchy of the areas.
    """
    
    temp_img = convertToGrayscale(img, basename, debugOutputDirectory, debug=debug)
    temp_img = invert(temp_img, basename, debugOutputDirectory, debug=debug)
    temp_img = closeDirection(temp_img, basename, debugOutputDirectory, debug=debug)
    temp_img = blankOutTopOfImage(temp_img, basename, debugOutputDirectory, debug=debug)
    temp_img = dilateDirection(temp_img, basename, debugOutputDirectory, debug=debug)
    temp_img = removeNoise(temp_img, basename, debugOutputDirectory, debug=debug)

#TODO use RETR_LIST instead of RETR_TREE so we don't waste time building a hierarchy?
    contours, hierarchy = cv2.findContours(temp_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def createTextTiles(img, basename, contours, directory, debug=False):
    """
    creates a bunch of tiles that are boxes around the found contours
    """
    print("creating cropped images")
    boxed = np.copy(img)
    
    files = []
    
    for contour in contours:
        x,y,w,h = cv2.boundingRect(contour)
        #TODO check if boundbox is COMPLETELY within already found bounding box? This could remove duplicate boxes within columns?
        if h > MIN_COLUMN_HEIGHT and w > MIN_COLUMN_WIDTH: #in general columns will be about 450 pixels wide, and we should make sure we aren't getting crazy small ones, 
                                #so minimum of 100 pixels tall
            filepath = os.path.join(directory, '%s_x%s_y%s_w%s_h%s.tiff' % (basename, x,y,w,h))
            files.append(filepath)
            ystart = max(y-PADDING, 0)
            yend = min(y+h+PADDING, img.shape[0])
            xstart = max(x-PADDING, 0)
            xend = min(x+w+PADDING, img.shape[1])
            crop_img = img[ystart:yend, xstart:xend]
            if not os.path.exists(filepath):
                print("writing out cropped image: ", filepath)
                cv2.imwrite(filepath, crop_img)
            if debug:
                #draw this specific bounding box on the copy of the image
                cv2.rectangle(boxed,(xstart,ystart),(xend,yend), GREEN, LINE_THICKNESS)
                    

    if debug:
        filepath = os.path.join(directory, '%s-contours.tiff' % basename)
        #cv2.drawContours(boxed, contours, -1, green, LINE_THICKNESS) #use this to draw all found contours
        cv2.imwrite(filepath, boxed)
        
    return files
        
def createOCRFiles(dirFilePair):
    directory = dirFilePair[0]
    file = dirFilePair[1]
    fullPath = os.path.join(directory, file)
    print('processing file: ', fullPath)
    basename = Path(file).stem
    img = cv2.imread(fullPath)

    contours = findContours(img, basename, directory, debug=CREATE_INTERMEDIATE_IMAGES)
    files = createTextTiles(img, basename, contours, directory, debug=CREATE_INTERMEDIATE_IMAGES)
    for inputFile in files:
        outputFile = os.path.join(directory, Path(inputFile).stem)
        print('creating OCR files from: ', inputFile)
        if not os.path.exists(outputFile + '.txt') or not os.path.exists(outputFile + '.hocr'):
            subprocess.run([TESSERACT, inputFile, outputFile, 'hocr', 'txt'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not CREATE_INTERMEDIATE_IMAGES:
            os.remove(inputFile) #we are done with the column image, so we delete it to save space

if __name__ == "__main__":
    with Pool(10) as p:
        filesToProcess = []
        for root,dirs,files in os.walk(BATCH_LOCATION):
            for file in files:
                if file.lower().endswith('.jp2'): #TODO ignore images at the F:\dlc_gritty_ver01\data\sn83030212\00206530157\ directory level as they are just for quality and don't contain newspaper pages
                    filesToProcess.append([root, file])
        
        p.map(createOCRFiles, filesToProcess)
    print("finished")
    
    