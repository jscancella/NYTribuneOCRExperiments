import cv2
import os

kernel = cv2.getStructuringElement(cv2.MORPH_CROSS,(3,1))

def convertToGrayscale(img, lccn, debug=False):
    print("converting to greyscale")
    temp_img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    if debug:
        cv2.imwrite('%s-invert.jp2' % lccn, temp_img)
    return temp_img

def invert(img, lccn, debug=False):
    print("invert image")
    _,temp_img = cv2.threshold(img, 140, 255, cv2.THRESH_BINARY_INV)
    if debug:
        cv2.imwrite('%s-invert.jp2' % lccn, temp_img)
    return temp_img

def findEdges(img, lccn, debug=False):
    print("get edges")
    temp_img = cv2.Canny(img, 30, 200)
    if debug:
        cv2.imwrite('%s-canny.jp2' % lccn, temp_img)
    return temp_img

def dilateXDirection(img, lccn, debug=False):
    print("applying dilation morph")
    temp_img = cv2.dilate(img, kernel, iterations=6)
   
    if debug:
        cv2.imwrite('%s-dilation.jp2' % lccn, temp_img)
    return temp_img

def closeXDirection(img, lccn, debug=False):
    print("applying closing morph")
    temp_img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
    if debug:
        cv2.imwrite('%s-close.jp2' % lccn, temp_img)
    return temp_img

def findContours(img, lccn, debug=False):
    """
    Takes an image and performs a number of transformations on it to find the areas where there is (possibly) text
    It then returns these areas (contours) as well as the hierarchy of the areas.
    """
    
    temp_img = convertToGrayscale(img, lccn, debug=debug)
    temp_img = invert(temp_img, lccn, debug=debug)
    temp_img = findEdges(temp_img, lccn, debug=debug)
    temp_img = dilateXDirection(temp_img, lccn, debug=debug)
    temp_img = closeXDirection(temp_img, lccn, debug=debug)

    _, contours, hierarchy = cv2.findContours(temp_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return contours, hierarchy

def createTextTiles(img, lccn, contours, hierarchy, directory, debug=False):
    """
    creates a bunch of tiles that are boxes around the found contours
    """
    boxed = None
    green = (0, 255, 0)
    for component in zip(contours, hierarchy[0]):
        contour = component[0]
        currentHierarchy = component[1]
        x,y,w,h = cv2.boundingRect(contour)
        if currentHierarchy[3] < 0: #outer most contour
            if h > 20 and w > 20:
                print("writing out word")
                filepath = os.path.join(directory, '%s_x%s_y%s_w%s_h%s.jp2' % (lccn, x,y,w,h))
                if not os.path.exists(filepath):
                    crop_img = img[y:y+h, x:x+w]
                    cv2.imwrite(filepath, crop_img)
                if debug:
                    if boxed is None:
                        boxed = img.copy()
                    cv2.rectangle(boxed,(x,y),(x+w,y+h), green, 3)

    if debug:
        filepath = os.path.join(directory, '%s-contours.jp2' % lccn)
        if not os.path.exists(filepath):
            cv2.imwrite(filepath, boxed)

if __name__ == "__main__":
    print("reading test image")
    img = cv2.imread('sn85038709.jp2')
    lccn = "sn85038709"
    create_intermediate_images=true
    contours, hierarchy = findContours(img, lccn, create_intermediate_images, debug=create_intermediate_images)
    output_directory = "words"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    createTextTiles(img, lccn, contours, hierarchy, output_directory, debug=create_intermediate_images)