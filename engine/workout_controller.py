"""
__author__ = 'Christopher Fagiani'
"""

import ConfigParser
import time
from random import randrange


class WorkoutController(object):
    """
    This class handles the main logic of a "workout" which consists of a number of punching bag hits. It will use
    the led_controls to signal the user to hit the bag and the hit_detector to wait for the hit.
    """

    def __init__(self, conf_file, controller=None, detector=None):
        try:
            # read the configuration file
            config = ConfigParser.RawConfigParser()
            config.read(conf_file)
            if controller:
                self.led_controller = controller
            else:
                from engine.io import led_controls
                # initialize the led_controller by building a dictionary of light_id to pins
                self.led_controller = led_controls.LedController({"r": config.getint("lights", "right"),
                                                                  "l": config.getint("lights", "left"),
                                                                  "c": config.getint("lights", "center")})

            self.hit_timeout = config.getfloat("workout", "reaction_timeout")
            self.recoil_wait = config.getfloat("workout", "recoil_wait")
            self.calibration_hits = config.getint("workout", "calibration_hits")
            if detector:
                self.hit_detector = detector
            else:
                import hit_detector
                # initialize the hit_detector
                self.hit_detector = hit_detector.HitDetector(config.getfloat("sensor", "threshold"),
                                                             config.getfloat("sensor", "calibration_timeout"),
                                                             config.getint("sensor", "samples"))
            # ask the user to hit the bag so we can calibrate
            self.calibrate_orientation(config.getint("sensor", "calibration_timeout"))
        except BaseException as e:
            # if we had an error during initialization call clean-up so we can release any resources
            self.cleanup()
            raise e

    def calibrate_orientation(self, timeout):
        """
        Since we do not know how the hardware was mounted on the bag, we need to ask the user to hit the bag on each side
        so we can calibrate the hit-detector for that direction.
        :param timeout:
        :return:
        """
        self.led_controller.flash()
        for i in range(self.calibration_hits):
            self.led_controller.activate_lights('r')
            self.hit_detector.calibrate_hit('r', timeout)
            time.sleep(0.5)
            self.led_controller.activate_lights('l')
            self.hit_detector.calibrate_hit('l', timeout)
            time.sleep(0.5)
            self.led_controller.activate_lights('c')
            self.hit_detector.calibrate_hit('c', timeout)

    def start_workout(self, mode, workout_time):
        """
        Executes the workout loop until it is over (either time elapses or the programmed workout is finished).

        :param mode:
        :param workout_time:
        :return:
        """
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
        """
        Turns on a light and waits for the hit_detector to register a hit.
        :param side:
        :return:
        """
        self.led_controller.activate_lights(side)
        return self.hit_detector.wait_for_hit(side, self.hit_timeout)

    def cleanup(self):
        self.led_controller.cleanup()
