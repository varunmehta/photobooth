#!/usr/bin/env python

import os
import subprocess
import time

fps = 1 # delay between pics
total_pics = 4 # number of pics  to be taken
# file_path = '/home/pi/photobooth/' #where do you want to save the photos
file_path = os.path.dirname(os.path.abspath(__file__))


now = time.strftime("%Y%m%d%H%M%S") #get the current date and time for the start of the filename
file_name = file_path + now + '.jpg'
print(file_name)
# for a proper 4x6 print, we need the image at 1200x1800
subprocess.call(["raspistill", "-f", "-vf", "-o", file_name, "-sa", "100", "-w", "1800", "-h", "1200"])

print("Done")
