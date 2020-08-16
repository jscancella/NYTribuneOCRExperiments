# Find Columns
This repo is an experiment to see if I can use openCV to generate pretty good cropped images of newspaper columns

#running on windows
* open powershell
* run env\Scripts\activate.ps1
* run `python.exe .\findText.py`
* look at `columns` folder for output and `debugFiles` folder for intermidiate steps done to the image to find columns

#process workflow
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
	* we merge the text together and output it as the text for the whole page
	* we format the text file so that chronam (or others) can use it?
	
* Stage 4a
	* review the cropped images from stage 2 to make sure they correctly identify the columns in the page and clean/regenerate them if they don't
	* use the reviewed/regenerated images to train a neural network AI to create the columns automatically
	
* Stage 4b
	* review the text output from stage 2 and fix any mistakes (very labor intensive. look into mechanical turk or crowd sourcing)
	* use the corrected text and the original image to help train a neural network AI to do OCR for newspapers