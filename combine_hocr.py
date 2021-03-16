import os
import re
import argparse
from bs4 import BeautifulSoup as Soup

BATCH_LOCATION = "E:\\backups\\chronam\\dlc_flavory_ver01"

def addXBboxValue(offset, item):
    titleValues = []
    for titleItem in item['title'].split(";"):
        if "bbox" in titleItem:
            values = titleItem.strip().split(" ")
            x0 = int(values[1]) + offset
            values[1] = str(x0)
            x1 = int(values[3]) + offset
            values[3] = str(x1)
            titleValues.append(" ".join(values))
        else:
            titleValues.append(titleItem)
    item['title'] = "; ".join(titleValues)
    #print("[" + item['title'] + "]")

def fixPageTitle(soup, xendingValue):
    titleValues = []
    for titleItem in soup.html.body.div['title'].split(";"):
        if "bbox" in titleItem:
            values = titleItem.strip().split(" ")
            values[1] = "0"
            values[3] = str(xendingValue)
            titleValues.append(" ".join(values))
        elif "image" in titleItem:
            pathParts = titleItem.split("\\")
            pathParts[-1] = re.sub(r"_.*", ".tiff", pathParts[-1])
            titleValues.append("\\".join(pathParts))
        else:
            titleValues.append(titleItem)
    soup.html.body.div['title'] = "; ".join(titleValues)
    
def combineHocrFiles(batch_dir):
    for root, dirs, files in os.walk(batch_dir):
        fileNumbers = set([f[:4] for f in files])
            
        for fileNumber in fileNumbers:
            filteredFiles = list(filter(lambda file: file.startswith(fileNumber) and file.endswith(".hocr"), files))
            hocrFilenames = [os.path.join(root, f) for f in filteredFiles]
            print("DEBUG: processing files", hocrFilenames)
            
            maxOffset = 0
            combinedSoup = None
            
            with open(hocrFilenames[0], 'r', encoding='utf8') as f:
                combinedSoup = Soup(f.read(), "xml")
                #remove all the findings so we can easily add them when iterating over each file
                for child in combinedSoup.html.body.div('div'):
                    child.decompose()
            
            for hocrFilename in hocrFilenames:
                with open(hocrFilename, 'r', encoding='utf8') as f:
                    soup = Soup(f.read(), "xml")
                    offsets = os.path.basename(hocrFilename).split("_")
                    offset = int(offsets[1][6:])
                    maxOffset = max(maxOffset, int(offsets[2][4:-5]))
                    
                    #don't include the ocr_page div, find all divs, update their X value, and then add them to the combined XML
                    for item in soup.html.body.div.find_all('div'):
                        addXBboxValue(offset, item)
                        combinedSoup.html.body.div.append(item)
            
            fixPageTitle(combinedSoup, maxOffset)

            #write out updated dom...
            print("check out", os.path.join(root, fileNumber + ".xml"))
            with open(os.path.join(root, fileNumber + ".xml"), 'w', encoding='utf8') as f:
                f.write(combinedSoup.prettify())
            
            #delete old hocr files?

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='combine the hocr files for each column into 1 combined hocr file with updated x coordinates.')
    parser.add_argument('--chronamdir', help='The directory of the chronicling america batch')
    args = parser.parse_args()
    
    if args.chronamdir:
        BATCH_LOCATION = args.chronamdir
        
    combineHocrFiles(BATCH_LOCATION)
    
    print('finished')