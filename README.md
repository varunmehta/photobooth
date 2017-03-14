# Pi-booth: photobooth

A DIY photo booth using a Raspberry Pi that automatically:
- Clicks 2 pictures
- Creates a mosaic of the images, with the event banner.
- Prints the mosiac to a Canon Selphy printer (4x6).

## Software:
  - PiCamera -- http://picamera.readthedocs.org/
  - GraphicsMagick -- http://www.graphicsmagick.org/

## Hardware List
  - http://a.co/ebQM8nK
  
### Based off: 
 - http://www.drumminhands.com/2014/06/15/raspberry-pi-photo-booth/ -  [Code - Github](https://github.com/drumminhands/drumminhands_photobooth)


## TODO:
 - Migrate to [gpiozero](https://gpiozero.readthedocs.io/en/stable/) library, from GPIO 
 - Allow multiple template options, so they can be dynamically picked up, via configuration 
 - Make the template scanning dynamic.
 - Clean up assets and artifacts 
 - Check [#issues](https://github.com/varunmehta/photobooth/issues) for any future enhancements. 
 - Write [blog post](http://protonfever.blogspot.com) with my build steps and details.