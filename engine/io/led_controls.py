"""
__author__ = 'Christopher Fagiani'
"""

import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    raise ImportError("GPIO must be installed. Please install and try again")

GPIO.setmode(GPIO.BCM)


class LedController(object):
    """
    Class to control toggling LED lights.
    """

    def __init__(self, lights):
        """
        Initializes GPIO and stores the mapping of light identifier to pin number.
        :param lights: dictionary where key is light identifier and value is pin number for that light.
        """
        self.lights = lights

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
        self.setup_pins()
        """Turns all lights in vals on and all other configured lights off."""
        for n, p in self.lights.iteritems():
            if n in vals:
                GPIO.output(p, True)
            else:
                GPIO.output(p, False)

    def cleanup(self):
        """
        Performs GPIO cleanup. This should only be called prior to exiting.
        :return:
        """
        for pin in self.lights.itervalues():
            GPIO.output(pin, False)
        GPIO.cleanup()

    def setup_pins(self):
        """
        Since we're calling the GPIO from another thread it seems we need to do the setup each time.
        :return:
        """
        GPIO.setmode(GPIO.BCM)
        for pin in self.lights.itervalues():
            GPIO.setup(pin, GPIO.OUT)
