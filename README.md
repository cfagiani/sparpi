Spar-Pi
==================

This project allows you to build a component comprised of an accelerometer and three LEDs that can sit on top of any flat-topped punching bag (like a Wavemaster). The center, left, or right lights will flash indicating that you should hit that side of the bag. The accelerometer is used to measure time to impact as well as an approximation of force.

## Required Hardware:
* Raspberry Pi
* Breadboard
* PiCobbler
* ~3' ribbon cable (for connecting Pi to breadboard)
* 3 LEDs
* 3 330 Ohm Resistors
* Jumper wires
* ADXL345 accelerometer


## Initial Setup:
Add i2C modules to pi:
```
sudo nano /etc/module
```
add the following two lines to that file and save:
```
i2c-bcm2708
i2c-dev
```
Remove I2C from the blacklist:
```
sudo nano /etc/modprobe.d/raspi-blacklist.conf
```
comment out the blacklist id2-bcm2708 line by pre-pending it with #

reboot the pi
```
sudo shutdown -r now
```

install the smbus & GPIO python libraries:
```
sudo apt-get install python-smbus i2c-tools python-dev python-rpi.gpio
```

Install flask unless only running headless:
```
sudo pip install flask
```

## Configuration
The scarpi.ini file contains all the configurable options for the system. These properties are described below:
### Sensor section
* threshold - absolute change in acceleration along any 1 axis that must be detected for a movement to be condsidered a hit
* calibration_timeout - time in seconds to wait for the user to finish each hit during calibration
* samples - the number of samples to capture after a hit is detected
### Workout section
* reaction_timeout - time in seconds the system will wait for a hit after activating a light
* recoil_wait - time in seconds after a hit to wait before starting to wait for the next hit
* detect_direction - flag (True or False) indicating whether the direction of impact should be considered when evaluating a hit. If fase, any impact counts.
* random_delay - flag (True or False) indicating whether the system should use a random delay between hits. If false, the next hit signal is triggered immedately after the previous.
### Lights section
* right - GPIO pin connected to the right LED
* left - GPIO pin connected to the left LED
* center - GPIO pin connected to the center LED


## Usage
After wiring the sensor and LED, the program can be used by running the sparpi.py script as root:
```
sudo python sparpi.py
```
This will launch the UI server on port 80 (port can be overridden via the --port option). Connect to the UI via a browser
and use it to start a workout. 

Alternatively, the system can run in "headless" mode. In this mode, it takes the workout time on the command line and terminates after the workout concludes:
```
sudo python sparpi.py --headless --time .5 
```


## Unit Tests
Tests are contained in the "test" directory. To run all tests:
```
python -m unittest discover -v 
```

## TODO:
* more/better tests
* log workout stats & have ui for browsing history
* wiring diagram & photos
* move all headless config to config file & remove cli options (except for --config and --time)
