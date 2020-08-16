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
		* we move banner by knowing that all pictures that have the name 0001.jp2 are the front page and color the top 900 pixels white. This has the effect that they are ignored when we invert the image and run it through various processes in openCV
		* we remove long lines 
			* by inverting the picture and running the find contours method of openCV
			* filter to only those that have a width of 1/2 the page and are skinny in height We need to make sure they are skinny otherwise we will accidentally use the bounding box that covers the entire page...
			* we color those areas white on the image used for stage 2
			* filter to only those that have a height of 1/2 the page and are skinny in width. We need to make sure they are skinny otherwise we will accidentally use the bounding box that covers the entire page...
			* we color those areas white on the image used for stage 2
* Stage 2 
	* we take the modified image from stage 1 and morph it to make the white areas (the text) grow in the Y axis. This will allow us to create big blobs that will tell use where the columns are
	* we try and fill in any small holes (MORPH_CLOSE in openCV speak)
	* we remove any noise (small white spots randomly, might be from dirt or specks of dust originally)
	* we find the contours  - this finds the big blobs that are white
	* we filter the contours to make sure they are the upper most contour in the hierarchy - this usually weeds out the sub contours but not always
	* We find the bounding box of that contour (because the column may be skewed slightly)
	* we then crop the image to the size of the bounding box and write it out (due to jp2 no longer being supported we must write it as a tiff)
	* we then run tesseract on the cropped image - because the image is only the columns, the text makes way more sense then when running it on the whole image
	* we merge the text together and output it as the text for the whole page
	* we format the text file so that chronam (or others) can use it?
	
* Stage 3a
	* review the cropped images from stage 2 to make sure they correctly identify the columns in the page and clean/regenerate them if they don't
	* use the reviewed/regenerated images to train a neural network AI to create the columns automatically
	
* Stage 3b
	* review the text output from stage 2 and fix any mistakes (very labor intensive. look into mechanical turk or crowd sourcing)
	* use the corrected text and the original image to help train a neural network AI to do OCR for newspapers