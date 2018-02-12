Spar-Pi
==================

This project allows you to build a component comprised of an accelerometer and three LEDs that can sit on top of any flat-topped punching bag (like a Wavemaster). The center, left, or right lights will flash indicating that you should hit that side of the bag. The accelerometer is used to measure time to impact as well as an approximation of force.

## Required Hardware:
* Raspberry Pi
* Breadboard
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

## Configuration
The scarpi.ini file contains all the configurable options for the system. These properties are described below:
### Sensor section
* threshold - absolute change in acceleration along any 1 axis that must be detected for a movement to be condsidered a hit
* calibration_timeout - time in seconds to wait for the user to finish each hit during calibration
* samples - the number of samples to capture after a hit is detected
### Workout section
* reaction_timeout - time in seconds the system will wait for a hit after activating a light
* recoil_wait - time in seconds after a hit to wait before starting to wait for the next hit
### Lights section
* right - GPIO pin connected to the right LED
* left - GPIO pin connected to the left LED
* center - GPIO pin connected to the center LED


## Usage
After wiring the sensor and LED, the program can be used by running the sparpi.py script as root:
```
sudo python sparpi.py
```
This will run a "random" workout for 2 minutes. The lenght of the workout can be changed via the --time command line option.

## Unit Tests
Tests are contained in the "test" directory. To run all tests:
```
python -m unittest discover -v 
```

## TODO:
* selectable workout types (random, combinations)
* build-your-own combination (ui configurable)
* hit count-based workouts
* more tests
* log workout stats & have ui for browsing history

