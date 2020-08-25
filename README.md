# Find Columns
This repo is an experiment to see if I can use openCV to generate pretty good cropped images of newspaper columns

# Running on windows
* open powershell
* run env\Scripts\activate.ps1
* modify any needed variables (at the top of the python scripts)
* run `python.exe .\<SCRIPT NAME>` where <SCRIPT NAME> is the name of the python script you want to run
* find the generated `.hocr` and `.txt` files that contain the OCR pulled from the found columns

# Process workflow for findText_usingFindContours.py
The idea behind this way of finding columns is to morph the image so that the columns of text become big white blobs that can be found using the built in method `findContours()`

* Stage 1
	* try and remove banner or long lines because when we morph the image it causes areas to connect that shouldn't and ruins the find contours step
		* we find the contours, and any that match a certain width and are in the "top" (can be adjusted) are used to blank out the image in that area.
* Stage 2 
	* we take the modified image from stage 1 and morph it to make the white areas (the text) grow in the Y axis. This will allow us to create big blobs that will tell use where the columns are
	* we find the contours  - this finds the big blobs that are white
	* we filter the contours to make sure they are the upper most contour in the hierarchy - this usually weeds out the sub contours but not always
	* We find the bounding box of that contour (because the column may be skewed slightly)
	* we filter the contours to make sure they meet minimum width and height
	* we then crop the image to the size of the bounding box WIDTH and the page height and write it out (due to jp2 no longer being supported we must write it as a tiff)
		* we do the full height because even if there are multiple paragraphs as long as they all match up it doesn't matter and the OCR from Tesseract should be good
* Stage 3
	* we then run Tesseract on the cropped image - because the image is only the columns, the text makes way more sense then when running it on the whole image
	
# Process workflow for findText_usingSums.py
The idea behind this way of finding columns is that each column of text is separated by some sort of white space. When an image is inverted, this whitespace becomes black which has a RGB value of 0. If we then sum up every pixel in each column together, the columns that have low values are mostly whitespace, and therefore are most likely to be the edges of the column. We invert those low values and then use the build in `find_peaks()` to find those peaks.

* Stage 1
	* We convert the image to an inverted black and white image
	* We sum each column of the image - creating a 1 dimensional array with the total values
	* We multiple all the values in the array above by -4 to invert and exagerate the column totals. This transforms the minimums to maximums
	* Since now they are the maximums, we run `find_peaks()` to get the index of each column
* Stage 2
	* Now that we have the column indexes, we use them to generate the start and stop indexes of each column
	* Using the start and stop indexes, we crop the image and write it out (due to jp2 no longer being supported we must write it as a tiff)
		* we do the full height because even if there are multiple paragraphs as long as they all match up it doesn't matter and the OCR from Tesseract should be good
* Stage 3
	* we then run Tesseract on the cropped image - because the image is only the columns, the text makes way more sense then when running it on the whole image
	
## Future work
There is still work to be done after running these experimental scripts to futher generate better OCR for old newspapers
* Stage 3a
	* we merge the text together and output it as the text for the whole page
	* we format the text file so that chronam (or others) can use it?
	
* Stage 4a
	* review the cropped images from stage 2 to make sure they correctly identify the columns in the page and clean/regenerate them if they don't
	* use the reviewed/regenerated images to train a neural network AI to create the columns automatically
	
* Stage 4b
	* review the text output from stage 2 and fix any mistakes (very labor intensive. look into mechanical turk or crowd sourcing)
	* use the corrected text and the original image to help train a neural network AI to do OCR for newspapers