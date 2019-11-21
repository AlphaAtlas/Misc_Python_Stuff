inputformat = "png"



import subprocess
import pkgutil
if pkgutil.find_loader('PIL') is None:
    subprocess.run("python", "-m", "pip", "install", "pillow")
import glob
import time
import threading
import os, shutil
from datetime import datetime
from PIL import Image
from pprint import pprint
from collections import OrderedDict
import concurrent.futures

def GetFileDict():
    inputfolder = os.getcwd()
    #Generate a dict of image paths inside a folder and its subfolders, filtered by size, and sorted by size/format
    #Also generate empty images in a temporary directory, linked to a mirrored source folder
    udict = dict()
    alphamodes = ("RGBA", "LA", "PA", "RGBa", "La")
    time = str(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    lock = threading.Lock()
    if os.path.isfile(os.path.join(inputfolder, "Broken Image List.txt")):
        os.remove(os.path.join(inputfolder, "Broken Image List.txt"))
    #Check if the target image is valid, and get its parameters
    def imageworker(imdir):
        def logbrokenfile(bfiledir):
            lock.acquire()
            with open(os.path.join(inputfolder, "Broken Image List.txt") , "a+") as broken_file_log:
                #print(r"Directories of broken images as of " + time + "\n", file = broken_file_log)
                print("Broken file: " + bfiledir + "\n", file = broken_file_log)
            lock.release()

        width = 0
        height = 0
        mode = "broken file"
        form = "broken file"	#default to a broken file categorization in case the file is funky
        balpha = False
        try:
            with Image.open(imdir) as im:
                im.verify()
                width, height = im.size
                form = im.format
                mode = im.mode
            if mode in alphamodes:
                balpha = True
            if width == 0 or height == 0:
                logbrokenfile(imdir)
                return 0
            #The key is a size/format tuple, the item is a directory list with image of that size/format
            #A lock theoretically shouldn't be needed with Python's GIL, but you never know...

            lock.acquire()
            udict.setdefault((width, height, form, mode, balpha), []).append(os.path.normpath(imdir))
            lock.release()
        except Exception:
            logbrokenfile(imdir)

    #Multi threaded (but not multicore) executor for globbing and categorizing images
    #True multiprocessing just seems to crash VSEdit.
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for imagedir in glob.iglob(inputfolder + "/**/*." + inputformat, recursive=True):
            executor.submit(imageworker, imagedir)
        executor.shutdown(wait=True)
    if (0, 0, "broken file", "broken file", False) in udict:
        raise Exception("Found broken files in the image dict. This should never happen!")
    sorteddict = OrderedDict(sorted(udict.items()))

    def linkworker(source, n, tempdir): 
        pdest = source
        cachefile = os.path.join(tempdir, str(n) + "." + inputformat)
        os.link(pdest, cachefile)
    
    def dictwriter():
        #Write a text file with all the image categorizations
        dictdir = os.path.normpath(os.path.join(inputfolder, "Image_Formats.txt"))
        if os.path.isfile(dictdir):
            os.remove(dictdir)
        with open(dictdir, "a+") as image_format_log:
            print(r"Categorization of images as of " + time + "\n", file=image_format_log)	
            print(r"""Format is (width, height, file format, image format, alpha layer) [image paths].""" + "\n", file=image_format_log)
            pprint(sorteddict, stream=image_format_log)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.submit(dictwriter)
        for key in sorteddict.keys():
            i = 0
            foldername = (os.path.join(inputfolder, "sorted", str(key)))
            os.makedirs(foldername, exist_ok = True)
            for d in sorteddict[key]:
                executor.submit(linkworker, d, i, foldername)
                i = i + 1
    return 0

GetFileDict()