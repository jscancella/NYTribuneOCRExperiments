import os
os.environ['OPENCV_IO_ENABLE_JASPER']='True' #has to be set before importing cv2 otherwise it won't read the variable
import cv2
import numpy as np 

MIN_COLUMN_WIDTH=450
MIN_COLUMN_HEIGHT=100

"""
# Cross-shaped Kernel
>>> cv.getStructuringElement(cv.MORPH_CROSS,(5,5))
array([[0, 0, 1, 0, 0],
       [0, 0, 1, 0, 0],
       [1, 1, 1, 1, 1],
       [0, 0, 1, 0, 0],
       [0, 0, 1, 0, 0]], dtype=uint8)
"""
#kernel = cv2.getStructuringElement(cv2.MORPH_CROSS,(5,5))

#custom kernel that is used to blend together text in the Y axis
kernel = np.array([
       [0, 0, 0, 0, 1, 0, 0, 0, 0],
       [0, 0, 0, 0, 1, 0, 0, 0, 0],
       [0, 0, 0, 0, 1, 0, 0, 0, 0],
       [0, 0, 0, 0, 1, 0, 0, 0, 0],
       [0, 0, 0, 0, 1, 0, 0, 0, 0],
       [0, 0, 0, 0, 1, 0, 0, 0, 0],
       [0, 0, 0, 0, 1, 0, 0, 0, 0],
       [0, 0, 0, 0, 1, 0, 0, 0, 0],
       [0, 0, 0, 0, 1, 0, 0, 0, 0]], dtype=np.uint8)
       
def blankOutTopOfImage(img, lccn, debug=False):
    """
    makes the top of the image black in order to remove the newspaper title
    """
    print("blanking out the top off the image")
    #TODO find the last row of the title banner
    temp_img = np.copy(img)
    for row in range(0,950):
        temp_img[row] = np.full(temp_img[row].shape, 255)
    if debug:
        filepath = os.path.join('debugFiles', '%s-blankedout.tiff' % lccn)
        cv2.imwrite(filepath, temp_img)
    return temp_img

def convertToGrayscale(img, lccn, debug=False):
    print("converting to greyscale")
    temp_img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    if debug:
        filepath = os.path.join('debugFiles', '%s-greyscale.tiff' % lccn)
        cv2.imwrite(filepath, temp_img)
    return temp_img

def invert(img, lccn, debug=False):
    """
    Black becomes white in the image
    """
    print("invert image")
    _,temp_img = cv2.threshold(img, 140, 255, cv2.THRESH_BINARY_INV)
    if debug:
        filepath = os.path.join('debugFiles', '%s-invert.tiff' % lccn)
        cv2.imwrite(filepath, temp_img)
    return temp_img
    
def removeNoise(img, lccn, debug=False):
    """
    erosion followed by dilation. It is useful in removing noise
    """
    print("remove noise")
    noiseKernel = np.array([
       [1, 1, 0, 1, 1],
       [1, 1, 0, 1, 1],
       [1, 1, 0, 1, 1],
       [1, 1, 0, 1, 1],
       [1, 1, 0, 1, 1]], dtype=np.uint8)
    temp_img = cv2.morphologyEx(img, cv2.MORPH_OPEN, noiseKernel)
    if debug:
        filepath = os.path.join('debugFiles', '%s-removeNoise.tiff' % lccn)
        cv2.imwrite(filepath, temp_img)
    return temp_img

def findEdges(img, lccn, debug=False):
    """
    basically draws a line around found white objects
    """
    print("get edges")
    temp_img = cv2.Canny(img, 30, 200)
    if debug:
        filepath = os.path.join('debugFiles', '%s-canny.tiff' % lccn)
        cv2.imwrite(filepath, temp_img)
    return temp_img

def dilateDirection(img, lccn, debug=False):
    """
    It is just opposite of erosion. Here, a pixel element is '1' if atleast one pixel under the kernel is '1'. 
    So it increases the white region in the image or size of foreground object increases. 
    Normally, in cases like noise removal, erosion is followed by dilation. 
    Because, erosion removes white noises, but it also shrinks our object. 
    So we dilate it. Since noise is gone, they won't come back, but our object area increases. 
    It is also useful in joining broken parts of an object. 
    """
    print("applying dilation morph")
    temp_img = cv2.dilate(img, kernel, iterations=10)
   
    if debug:
        filepath = os.path.join('debugFiles', '%s-dilation.tiff' % lccn)
        cv2.imwrite(filepath, temp_img)
    return temp_img

def closeDirection(img, lccn, debug=False):
    """
    Dilation followed by Erosion. It is useful in closing small holes inside the foreground objects, or small black points on the object
    """
    print("applying closing morph")
    temp_img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
    if debug:
        filepath = os.path.join('debugFiles', '%s-close.tiff' % lccn)
        cv2.imwrite(filepath, temp_img)
    return temp_img

def findContours(img, lccn, debug=False):
    """
    Takes an image and performs a number of transformations on it to find the areas where there is (possibly) text
    It then returns these areas (contours) as well as the hierarchy of the areas.
    """
    
    temp_img = convertToGrayscale(img, lccn, debug=debug)
    temp_img = invert(temp_img, lccn, debug=debug)
    #temp_img = findEdges(temp_img, lccn, debug=debug)
    temp_img = dilateDirection(temp_img, lccn, debug=debug)
    temp_img = closeDirection(temp_img, lccn, debug=debug)
    temp_img = removeNoise(temp_img, lccn, debug=debug)

#TODO use RETR_LIST instead of RETR_TREE so we don't waste time building a hierarchy
    contours, hierarchy = cv2.findContours(temp_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return contours, hierarchy

def createTextTiles(img, lccn, contours, hierarchy, directory, debug=False):
    """
    creates a bunch of tiles that are boxes around the found contours
    """
    print("creating cropped images")
    boxed = np.copy(img)
    green = (0, 255, 0)
    lineThickness = 3
    padding = 10 #padding to add around the found contour to help account for image skew and such
    
    for component in zip(contours, hierarchy[0]):
        contour = component[0]
        currentHierarchy = component[1]
        x,y,w,h = cv2.boundingRect(contour)
        #TODO check if boundbox is COMPLETELY within already found bounding box? This could remove duplicate boxes within columns?
        parentContour = currentHierarchy[3] #the structure of the contour hierarchy is (next, previous, first child, parent)
        doesNotExist = -1 #this is how openCV defines that the contour hierarchy item doesn't exist
        if parentContour == doesNotExist: #outer most contour
            if h > MIN_COLUMN_HEIGHT and w > MIN_COLUMN_WIDTH: #in general columns will be about 450 pixels wide, and we should make sure we aren't getting crazy small ones, 
                                    #so minimum of 100 pixels tall
                filepath = os.path.join(directory, '%s_x%s_y%s_w%s_h%s.tiff' % (lccn, x,y,w,h))
                ystart = max(y-padding, 0)
                yend = min(y+h+padding, img.shape[0])
                xstart = max(x-padding, 0)
                xend = min(x+w+padding, img.shape[1])
                crop_img = img[ystart:yend, xstart:xend]
                if not os.path.exists(filepath):
                    print("writing out cropped image: ", filepath)
                    cv2.imwrite(filepath, crop_img)
                if debug:
                    #draw this specific bounding box on the copy of the image
                    cv2.rectangle(boxed,(xstart,ystart),(xend,yend), green, lineThickness)
                    

    if debug:
        filepath = os.path.join('debugFiles', '%s-contours.tiff' % lccn)
        #cv2.drawContours(boxed, contours, -1, green, lineThickness) #use this to draw all found contours
        cv2.imwrite(filepath, boxed)

if __name__ == "__main__":
    print("reading test image")
    img = cv2.imread(os.path.abspath('./testFiles/newYorkTribune/sn83030212-1841-04-10-frontpage.jp2'))
    lccn = "sn83030212"
    create_intermediate_images=True
    if create_intermediate_images and not os.path.exists('debugFiles'):
        os.makedirs('debugFiles')
    
    #TODO detect if img is a title page and only then blank out the top
    temp_img = blankOutTopOfImage(img, lccn, debug=create_intermediate_images)
    contours, hierarchy = findContours(temp_img, lccn, debug=create_intermediate_images)
    output_directory = "columns"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    createTextTiles(img, lccn, contours, hierarchy, output_directory, debug=create_intermediate_images)