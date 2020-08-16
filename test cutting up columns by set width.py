import os
import sys
os.environ['OPENCV_IO_ENABLE_JASPER']='True' #has to be set before importing cv2 otherwise it won't read the variable
import cv2

LEFT_MARGIN = 30 #account for the fact there is more whitespace around the edge of the newspaper
NUMBER_OF_COLUMNS = 5
PADDING = 20

#start of first column:  0 (min)
#end of first column:    1265
#start of second column: 1245
#end of second column:   2500
#start of third column:  2475
#end of third column:    3700
#start of fourth column: 3695
#end of fourth column:   4935
#start of fifth column:  4910
#end of fifth column:    (max x)

COLUMN_START_STOPS = [(0,1265), (1245, 2500), (2475, 3700), (3695, 4935), (4910, sys.maxsize)]


if __name__ == "__main__":
    print("reading test image")
    # img = cv2.imread(os.path.abspath('./testFiles/newYorkTribune/sn83030212-1841-04-10-frontpage.jp2'))
    #img = cv2.imread('F:/dlc_gritty_ver01/data/sn83030212/00206530157/1841041001/0001.jp2')
    # img = cv2.imread('F:/dlc_gritty_ver01/data/sn83030212/00206530157/1841041001/0002.jp2')
    img = cv2.imread('F:/dlc_gritty_ver01/data/sn83030212/00206530157/1841041001/0003.jp2')
    cv2.imwrite('testOutput/full.tiff', img)
    
    ystart = 0
    yend = img.shape[0]
    maxX = img.shape[1]
    
    for columnPoints in COLUMN_START_STOPS:
        xstart = columnPoints[0]
        xend = min(columnPoints[1], maxX)
        
        crop_img = img[ystart:yend, xstart:xend]
        filepath = os.path.join('testOutput', '%s_x%s_y%s_w%s_h%s.tiff' % ('sn83030212', xstart,ystart,xend,yend))
        print("writing out cropped image: ", filepath)
        cv2.imwrite(filepath, crop_img)
    
    
    # columnStep = int(maxX/NUMBER_OF_COLUMNS)
    
    # ystart = 0
    # yend = maxY
    # xstart = 0 + LEFT_MARGIN
    # xend = columnStep
    
    # while xend < maxX:
        # xstartPadded = max(0, xstart - PADDING)
        # xendPadded = min(xend + PADDING, maxX) #make sure we don't try and go out of bounds
        # crop_img = img[ystart:yend, xstartPadded:xendPadded]
        
        # filepath = os.path.join('testOutput', '%s_x%s_y%s_w%s_h%s.tiff' % ('sn83030212', xstartPadded,ystart,xendPadded,yend))
        # print("writing out cropped image: ", filepath)
        # cv2.imwrite(filepath, crop_img)
        
        # xstart += columnStep
        # xend += columnStep
    print("finished")