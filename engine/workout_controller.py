"""
__author__ = 'Christopher Fagiani'
"""

import ConfigParser
import time
import hit_detector
from random import randrange
from engine.io import led_controls

try:
    import RPi.GPIO as GPIO
except ImportError:
    raise ImportError("GPIO must be installed. Please install and try again")


class WorkoutController(object):
    def __init__(self, conf_file):
        try:
            config = ConfigParser.RawConfigParser()
            config.read(conf_file)
            self.led_controller = led_controls.LedController({"r": config.getint("lights", "right"),
                                                              "l": config.getint("lights", "left"),
                                                              "c": config.getint("lights", "center")})

            self.hit_timeout = config.getfloat("workout", "reaction_timeout")
            self.recoil_wait = config.getfloat("workout", "recoil_wait")
            self.hit_detector = hit_detector.HitDetector(config.getfloat("sensor", "threshold"),
                                                         config.getfloat("sensor", "calibration_timeout"),
                                                         config.getint("sensor", "samples"))
            self.calibrate_orientation(config.getint("sensor", "calibration_timeout"))
        except BaseException as e:
            self.cleanup()
            raise e

    def calibrate_orientation(self, timeout):
        self.led_controller.flash()
        self.led_controller.activate_lights('r')
        self.hit_detector.calibrate_hit('r', timeout)
        time.sleep(0.5)
        self.led_controller.activate_lights('l')
        self.hit_detector.calibrate_hit('l', timeout)
        time.sleep(0.5)
        self.led_controller.activate_lights('c')
        self.hit_detector.calibrate_hit('c', timeout)

    def start_workout(self, mode, workout_time):
        deadline = time.time() + workout_time * 60
        round_num = 0
        hit_count = 0
        miss_count = 0
        sides = ['r', 'c', 'l']
        while time.time() < deadline:
            self.led_controller.activate_lights('')
            time.sleep(self.recoil_wait)
            if mode == 'random':
                side = sides[randrange(0, 3)]
            else:
                side = sides[round_num % 3]
            if self.await_hit(side):
                hit_count += 1
            else:
                miss_count += 1
            round_num += 1
        return round_num, hit_count, miss_count

    def await_hit(self, side):
        self.led_controller.activate_lights(side)
        return self.hit_detector.wait_for_hit(side, self.hit_timeout)

    def cleanup(self):
        self.led_controller.cleanup()
