import os
import argparse
from pathlib import Path
import sys
os.environ['OPENCV_IO_ENABLE_JASPER']='True' #has to be set before importing cv2 otherwise it won't read the variable
import cv2
import numpy as np
import subprocess
from multiprocessing import Pool
from scipy.signal import find_peaks

#static variables for clarity
COLUMNS = 0
GREEN = (0, 255, 0)

#parameters that can be tweaked
LINE_THICKNESS = 3 #how thick to make the line around the found contours in the debug output
PADDING = 10 #padding to add around the found possible column to help account for image skew and such
BATCH_LOCATION = 'E:/chronam/dlc_flavory_ver01' #directory to start in to find the .jp2 files to process
TESSERACT = 'C:/Program Files/Tesseract-OCR/tesseract.exe'
CREATE_COLUMN_OUTLINE_IMAGES = True #if we detect that we didn't find all the columns. Create a debug image (tiff) showing the columns that were found
REMOVE_JP2_AFTER_PROCESSING = True #If we want to save space and remove the jp2 file after we are done processing the OCR

def columnIndexes(a):
    """
    creates pair of indexes for left and right index of the image column
    For example [13, 1257, 2474, 3695, 4907, 6149]
    becomes: [[13 1257], [1257 2474], [2474 3695], [3695 4907], [4907 6149]]
    """
    nrows = (a.size-2)+1
    return a[1*np.arange(nrows)[:,None] + np.arange(2)]
    
def convertToGrayscale(img):
    print("converting to greyscale")
    temp_img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    return temp_img

def invert(img):
    """
    Black becomes white in the image
    """
    print("invert image")
    _,temp_img = cv2.threshold(img, 140, 255, cv2.THRESH_BINARY_INV)
    return temp_img
    
def createColumnImages(img, basename, directory):
    """
    we sum each column of the inverted image. The columns should show up as peaks in the sums
    uses scipy.signal.find_peaks to find those peaks and use them as column indexes
    """
    files = []
    temp_img = convertToGrayscale(img)
    temp_img = invert(temp_img)
    
    sums = np.sum(temp_img, axis = COLUMNS)
    sums[0] = 1000 #some random value so that find_peaks properly detects the peak for the left most column
    sums = sums * -4 #invert so that minimums become maximums and exagerate the data so it is more clear what the peaks are
    peaks, _ = find_peaks(sums, distance=800) #the column indexs of the img array, spaced at least 800 away from the previous peak
    
    if peaks.size == 0:
        with open('troublesomeImages.txt', 'a') as f:
            print("ERROR: something went wrong with finding the peaks for image: ", os.path.join(directory, basename))
            f.write(os.path.join(directory, basename) + ".jp2 0\n")
        return files
        
    peaks[0] = 0 #automatically make the left most column index the start of the image
    peaks[-1] =sums.size -1 #automatically make the right most column index the end of the image
        
    boxed = np.copy(img)
    if peaks.size < 6:
        with open('troublesomeImages.txt', 'a') as f:
            print("found image that is causing problems: ", os.path.join(directory, basename)) 
            f.write(os.path.join(directory, basename) + ".jp2 " + str(peaks.size) + "\n")
    
    columnIndexPairs = columnIndexes(peaks)
    
    ystart = 0
    yend = img.shape[0]
    for columnIndexPair in columnIndexPairs:
        xstart = max(columnIndexPair[0]-PADDING, 0)
        xend = min(columnIndexPair[1]+PADDING, img.shape[1])
        filepath = os.path.join(directory, '%s_xStart%s_xEnd%s.tiff' % (basename, xstart,xend))
        files.append(filepath)
        crop_img = img[ystart:yend, xstart:xend]
        if not os.path.exists(filepath):
            print("writing out cropped image: ", filepath)
            cv2.imwrite(filepath, crop_img)
        
        if CREATE_COLUMN_OUTLINE_IMAGES:
            cv2.rectangle(boxed,(xstart,ystart),(xend,yend), GREEN, LINE_THICKNESS)
        
    if CREATE_COLUMN_OUTLINE_IMAGES:
        filepath = os.path.join(directory, '%s-contours.jpeg' % basename)
        cv2.imwrite(filepath, boxed, [cv2.IMWRITE_JPEG_QUALITY, 50])
        
    if REMOVE_JP2_AFTER_PROCESSING:
        os.remove(os.path.join(directory, basename + ".jp2"))
            
    return files
    
def createOCRFiles(dirFilePair):
    directory = dirFilePair[0]
    file = dirFilePair[1]
    fullPath = os.path.join(directory, file)
    print('processing file: ', fullPath)
    basename = Path(file).stem
    img = cv2.imread(fullPath)

    files = createColumnImages(img, basename, directory)
    for inputFile in files:
        outputFile = os.path.join(directory, Path(inputFile).stem)
        print('creating OCR files from: ', inputFile)
        if not os.path.exists(outputFile + '.txt') or not os.path.exists(outputFile + '.hocr'):
            subprocess.run([TESSERACT, inputFile, outputFile, 'hocr', 'txt'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.remove(inputFile) #we are done with the column image, so we delete it to save space
            
def createColumnHocr(batch_dir):
    with Pool(8) as p:
        filesToProcess = []
        for root,dirs,files in os.walk(batch_dir):
            for file in files:
                if file.lower().endswith('.jp2'): #TODO ignore images at the F:\dlc_gritty_ver01\data\sn83030212\00206530157\ directory level as they are just for quality and don't contain newspaper pages
                    filesToProcess.append([root, file])
        
        p.map(createOCRFiles, filesToProcess)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create columns of text and run OCR on them.')
    parser.add_argument('--chronamdir', help='The directory of the chronicling america batch')
    args = parser.parse_args()
    
    if args.chronamdir:
        BATCH_LOCATION = args.chronamdir

    createColumnHocr(BATCH_LOCATION)
    
    print("finished")