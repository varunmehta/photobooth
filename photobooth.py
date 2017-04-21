#!/usr/bin/env python
# created by chris@drumminhands.com
# modified by varunmehta
# see instructions at http://www.drumminhands.com/2014/06/15/raspberry-pi-photo-booth/

import atexit
import glob
import logging
import math
import os
import subprocess
import sys
import time
import traceback
from time import sleep

import RPi.GPIO as GPIO
import picamera  # http://picamera.readthedocs.org/en/release-1.4/install2.html
import pygame
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE

import config  # this is the config python file config.py

########################
### Variables Config ###
########################
led_pin = 17  # LED
btn_pin = 2  # pin for the start button

total_pics = 2  # number of pics to be taken
capture_delay = 1  # delay between pics
prep_delay = 3  # number of seconds at step 1 as users prep to have photo taken
restart_delay = 3  # how long to display finished message before beginning a new session

# full frame of v1 camera is 2592x1944. Wide screen max is 2592,1555
# if you run into resource issues, try smaller, like 1920x1152.
# or increase memory http://picamera.readthedocs.io/en/release-1.12/fov.html#hardware-limits
high_res_w = 1190  # width of high res image, if taken
high_res_h = 790  # height of high res image, if taken

#############################
### Variables that Change ###
#############################
# Do not change these variables, as the code will change it anyway
transform_x = config.monitor_w  # how wide to scale the jpg when replaying
transfrom_y = config.monitor_h  # how high to scale the jpg when replaying
offset_x = 0  # how far off to left corner to display photos
offset_y = 0  # how far off to left corner to display photos
replay_delay = 1  # how much to wait in-between showing pics on-screen after taking
replay_cycles = 1  # how many times to show each photo on-screen after taking

####################
### Other Config ###
####################
real_path = os.path.dirname(os.path.realpath(__file__))

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(led_pin, GPIO.OUT)  # LED
GPIO.setup(btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.output(led_pin, False)  # for some reason the pin turns on at the beginning of the program. Why?

# initialize pygame
pygame.init()
pygame.display.set_mode((config.monitor_w, config.monitor_h))
screen = pygame.display.get_surface()
pygame.display.set_caption('Photo Booth Pics')
pygame.mouse.set_visible(False)  # hide the mouse cursor
pygame.display.toggle_fullscreen()

# init logging
logging.basicConfig(format='%(asctime)s %(message)s', filename='photobooth.log', level=logging.INFO)


#################
### Functions ###
#################

# clean up running programs as needed when main program exits
def cleanup():
    logging.critical('Ended abruptly')
    pygame.quit()
    GPIO.cleanup()
    atexit.register(cleanup)


# A function to handle keyboard/mouse/device input events
def input(events):
    for event in events:  # Hit the ESC key to quit the slideshow.
        if (event.type == QUIT or
                (event.type == KEYDOWN and event.key == K_ESCAPE)):
            pygame.quit()


# delete files in folder
def clear_pics(channel):
    files = glob.glob(config.file_path + '*')
    for f in files:
        os.remove(f)
    # light the lights in series to show completed
    logging.warning("Deleted previous pics")
    for x in range(0, 3):  # blink light
        GPIO.output(led_pin, True)
        sleep(0.25)
        GPIO.output(led_pin, False)
        sleep(0.25)


def init_event_folders():
    if (not os.path.exists(config.file_path)):
        os.mkdir(config.file_path)
        os.mkdir(config.file_path + "/final")
        logging.info("Initalized event folder")


# set variables to properly display the image on screen at right ratio
def set_dimensions(img_w, img_h):
    # Note this only works when in booting in desktop mode.
    # When running in terminal, the size is not correct (it displays small). Why?

    # connect to global vars
    global transform_y, transform_x, offset_y, offset_x

    # based on output screen resolution, calculate how to display
    ratio_h = (config.monitor_w * img_h) / img_w

    if (ratio_h < config.monitor_h):
        # Use horizontal black bars
        # print("horizontal black bars")
        transform_y = ratio_h
        transform_x = config.monitor_w
        offset_y = (config.monitor_h - ratio_h) / 2
        offset_x = 0
    elif (ratio_h > config.monitor_h):
        # Use vertical black bars
        # print("vertical black bars")
        transform_x = (config.monitor_h * img_w) / img_h
        transform_y = config.monitor_h
        offset_x = (config.monitor_w - transform_x) / 2
        offset_y = 0
    else:
        # No need for black bars as photo ratio equals screen ratio
        # print("no black bars")
        transform_x = config.monitor_w
        transform_y = config.monitor_h
        offset_y = offset_x = 0

    # Ceil and floor floats to integers
    transform_x = math.ceil(transform_x)
    transform_y = math.ceil(transform_y)
    offset_x = math.floor(offset_x)
    offset_y = math.floor(offset_y)

    # uncomment these lines to troubleshoot screen ratios
    # print(str(img_w) + " x " + str(img_h))
    # print("ratio_h: " + str(ratio_h))
    # print("transform_x: " + str(transform_x))
    # print("transform_y: " + str(transform_y))
    # print("offset_y: " + str(offset_y))
    # print("offset_x: " + str(offset_x))

# display one image on screen
def show_image(image_path):
    # print(" Displaying... " + image_path)
    # clear the screen
    screen.fill((0, 0, 0))

    # load the image
    img = pygame.image.load(image_path)
    img = img.convert()

    # set pixel dimensions based on image
    set_dimensions(img.get_width(), img.get_height())

    # rescale the image to fit the current display
    img = pygame.transform.scale(img, (transform_x, transfrom_y))
    screen.blit(img, (offset_x, offset_y))
    pygame.display.flip()


# display a blank screen
def clear_screen():
    screen.fill((0, 0, 0))
    pygame.display.flip()


# display a group of images
def display_pics(jpg_group):
    for i in range(0, replay_cycles):  # show pics a few times
        for i in range(1, total_pics + 1):  # show each pic
            show_image(config.file_path + jpg_group + "-0" + str(i) + ".jpg")
            time.sleep(replay_delay)  # pause


# define the photo taking function for when the big button is pressed
def start_photobooth():
    input(pygame.event.get())  # press escape to exit pygame. Then press ctrl-c to exit python.

    ################################# Begin Step 1 #################################

    logging.info("Get Ready")
    GPIO.output(led_pin, False)
    show_image(real_path + "/instructions.png")
    sleep(prep_delay)

    # clear the screen
    clear_screen()

    camera = picamera.PiCamera()
    camera.vflip = False
    camera.hflip = True  # flip for preview, showing users a mirror image
    camera.rotation = 0  # revisit this depending upon final camera placement
    # camera.saturation = -100  # comment out this line if you want color images
    # camera.iso = config.camera_iso

    camera.resolution = (high_res_w, high_res_h)  # set camera resolution to high res

    ################################# Begin Step 2 #################################

    logging.info("Starting to take pics...")

    # All images will be number appended by now, 20160310113034-01.jpg
    now = time.strftime("%Y%m%d-%H%M%S")  # get the current date and time for the start of the filename
    montage_img = now + "-" + config.event_name + ".jpg"  # montage file name

    if config.capture_count_pics:
        logging.debug("Decided to go count pics")
        try:  # take the photos
            for i in range(1, total_pics + 1):
                show_image(real_path + "/pose" + str(i) + ".png")
                time.sleep(capture_delay)  # pause in-between shots
                clear_screen()
                camera.hflip = True  # preview a mirror image
                camera.start_preview(
                    resolution=(high_res_w, high_res_h))  # start preview at low res but the right ratio
                time.sleep(2)  # warm up camera
                # GPIO.output(led_pin, True)  # turn on the LED
                filename = config.file_path + now + '-0' + str(i) + '.jpg'
                camera.hflip = False  # flip back when taking photo
                camera.capture(filename)
                logging.info("captured: " + filename)
                # GPIO.output(led_pin, False)  # turn off the LED
                camera.stop_preview()
                # show_image(real_path + "/pose" + str(i) + ".png")
                time.sleep(capture_delay)  # pause in-between shots
                clear_screen()
                if i == total_pics + 1:
                    break
        finally:
            camera.close()
    else:
        logging.debug("capture_continuous")
        camera.start_preview(
            resolution=(high_res_w, high_res_h))  # start preview at low res but the right ratio
        time.sleep(2)  # warm up camera

        try:  # take the photos
            for i, filename in enumerate(camera.capture_continuous(config.file_path + now + '-' + '{counter:02d}.jpg')):
                GPIO.output(led_pin, True)  # turn on the LED
                logging.info("captured: " + filename)
                time.sleep(capture_delay)  # pause in-between shots
                GPIO.output(led_pin, False)  # turn off the LED
                if i == total_pics - 1:
                    break
        finally:
            camera.stop_preview()
            camera.close()

    ########################### Begin Step 3 #################################

    input(pygame.event.get())  # press escape to exit pygame. Then press ctrl-c to exit python.

    logging.info("Creating mosaic ")
    show_image(real_path + "/processing.png")

    # Create a montage of the images
    montage = "gm montage -mode concatenate -resize 1190x1770 -borderwidth 5 -bordercolor white " \
              + config.file_path + "/" + now + "-01.jpg  " + real_path + "/holi-middle.jpg " \
              + config.file_path + "/" + now + "-02.jpg -tile 1x3 " \
              + config.file_path + "/final/" + montage_img

    print(montage)

    processed = subprocess.call(montage, shell=True)

    logging.info("gm montage for " + now + "-final.jpg = " + str(processed))

    ########################### Begin Step 4 #################################

    input(pygame.event.get())  # press escape to exit pygame. Then press ctrl-c to exit python.

    try:
        display_pics(now)
        # show preview of finally created image
        show_image(config.file_path + "/final/" + montage_img)
        time.sleep(2)
    except Exception as e:
        tb = sys.exc_info()[2]
        traceback.print_exception(e.__class__, e, tb)
        pygame.quit()

    logging.info("Session for " + now + " complete")

    show_image(real_path + "/finished2.png")

    # upload to dropbox
    # subprocess.call(
    #     "/opt/Dropbox-Uploader/dropbox_uploader.sh -f /home/pi/.dropbox_uploader upload " + config.file_path + "final/" + montage_img + " " + montage_img)

    time.sleep(restart_delay)
    show_image(real_path + "/intro.png");
    GPIO.output(led_pin, True)  # turn on the LED


####################
### Main Program ###
####################

## clear the previously stored pics based on config settings
if config.clear_on_startup:
    clear_pics(1)

# check if files and folders exist for the event, or create them
init_event_folders()

logging.warning("Starting photo booth...")

for x in range(0, 5):  # blink light to show the app is running
    GPIO.output(led_pin, True)
    sleep(0.25)
    GPIO.output(led_pin, False)
    sleep(0.25)

show_image(real_path + "/intro.png")

while True:
    GPIO.output(led_pin, True)  # turn on the light showing users they can push the button
    input(pygame.event.get())  # press escape to exit pygame. Then press ctrl-c to exit python.
    GPIO.wait_for_edge(btn_pin, GPIO.FALLING)
    time.sleep(config.debounce)  # debounce
    start_photobooth()
    logging.warning("----------------------")
