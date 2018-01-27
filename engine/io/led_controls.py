"""
__author__ = 'Christopher Fagiani'
"""

import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    raise ImportError("GPIO must be installed. Please install and try again")


class LedController(object):
    """
    Class to control toggling LED lights.
    """

    def __init__(self, lights):
        self.lights = lights
        GPIO.setmode(GPIO.BCM)
        for pin in self.lights.itervalues():
            GPIO.setup(pin, GPIO.OUT, initial=False)

    def flash(self, interval=0.25, times=3):
        """ Flashes all the lights
        :param interval - time lights should remain on/off
        :param times - number of times to flash
        """
        for i in range(times):
            self.activate_lights('rcl')
            time.sleep(interval)
            self.activate_lights('')
            time.sleep(interval)

    def activate_lights(self, vals):
        for n, p in self.lights.iteritems():
            if n in vals:
                GPIO.output(p, True)
            else:
                GPIO.output(p, False)

    def cleanup(self):
        for pin in self.lights.itervalues():
            GPIO.output(pin, False)
        GPIO.cleanup()
