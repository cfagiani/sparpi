"""
__author__ = 'Christopher Fagiani'
"""

import ConfigParser
import time
import logging
from random import randrange
from hit_detector import SensorInitializationError

log = logging.getLogger(__name__)


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
            self.cur_workout = None
            self.is_running = False
            self.detect_dir = config.getboolean("workout", "detect_direction")
            self.calibration_timeout = config.getint("sensor", "calibration_timeout")
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
                                                             config.getint("sensor", "samples"),
                                                             detect_dir=self.detect_dir)
        except BaseException as e:
            # if we had an error during initialization call clean-up so we can release any resources
            try:
                self.cleanup()
            except BaseException as e2:
                log.error("Could not clean up {msg}".format(msg=e2.message))
                raise e
            raise e

    def has_valid_calibration(self):
        return self.hit_detector.has_valid_calibration()

    def calibrate_orientation(self):
        """
        Since we do not know how the hardware was mounted on the bag, we need to ask the user to hit the bag on each side
        so we can calibrate the hit-detector for that direction. After getting a reading for all 3 directions, it will
        validate the calibration. If invalid, it will repeat the calibration process up to calibration_hits times. If a
        valid calibration is not read after calibration_hits iterations, a SensorInitializationError is raised.
        :param timeout:
        :return:
        """
        for i in range(self.calibration_hits):
            self.led_controller.flash()
            self.led_controller.activate_lights('r')
            r_val = self.hit_detector.calibrate_hit('r', self.calibration_timeout)
            self.hit_detector.wait_for_stability(self.recoil_wait)
            time.sleep(0.5)
            self.led_controller.activate_lights('l')
            l_val = self.hit_detector.calibrate_hit('l', self.calibration_timeout)
            self.hit_detector.wait_for_stability(self.recoil_wait)
            time.sleep(0.5)
            self.led_controller.activate_lights('c')
            c_val = self.hit_detector.calibrate_hit('c', self.calibration_timeout)
            self.led_controller.activate_lights('')
            if self.hit_detector.has_valid_calibration():
                log.debug("Got valid calibration r: {r}, l: {lv}, c: {c}".format(r=r_val, lv=l_val, c=c_val))
                return
            else:
                log.info("Invalid calibration r: {r}, l: {lv}, c: {c}".format(r=r_val, lv=l_val, c=c_val))
        raise SensorInitializationError("Could not obtain a valid calibration")

    def start_workout(self, mode, workout_time, frequencies={'l': 33, 'c': 33, 'r': 34}):
        """
        Executes the workout loop until it is over (either time elapses or the programmed workout is finished).

        :param mode:
        :param workout_time:
        :param frequencies:
        :return:
        """
        self.is_running = True
        deadline = time.time() + workout_time * 60
        self.cur_workout = WorkoutState(deadline)
        round_num = 0
        hit_count = 0
        miss_count = 0
        sides = ['r', 'c', 'l']
        validate_frequencies(frequencies)
        while time.time() < deadline and self.is_running:
            self.led_controller.activate_lights('')
            self.hit_detector.wait_for_stability(self.recoil_wait)
            if mode == 'random':
                side = get_next_side(frequencies)
            else:
                side = sides[round_num % 3]
            if self.await_hit(side):
                hit_count += 1
            else:
                miss_count += 1
            round_num += 1
        self.led_controller.activate_lights('')
        self.is_running = False
        return self.cur_workout

    def await_hit(self, side):
        """
        Turns on a light and waits for the hit_detector to register a hit.
        :param side:
        :return:
        """
        self.led_controller.activate_lights(side)
        start_time = time.time()
        hit_val, is_correct = self.hit_detector.wait_for_hit(side, self.hit_timeout)
        reaction_time = time.time() - start_time
        if hit_val:
            self.cur_workout.record_hit(side, reaction_time, is_correct)
        if is_correct:
            return hit_val
        else:
            return None

    def cleanup(self):
        self.led_controller.cleanup()

    def get_state(self):
        self.cur_workout.server_time = time.time()
        return self.cur_workout

    def stop_workout(self):
        self.is_running = False


def validate_frequencies(frequencies):
    """
    Validates that the frequencies passed in add up to 100 and do not contain negatives.
    :param frequencies:
    :return:
    """
    if sum(frequencies.values()) != 100:
        raise ConfigurationError("Frequency weights must add up to 100")
    if len([z for z in frequencies.values() if 0 <= z <= 100]) != len(frequencies):
        raise ConfigurationError("Frequency weights must be between 0 and 100, inclusive.")


def get_next_side(frequencies):
    """ Returns a key from frequencies using the values to weigh the likelihood of selection.
    This assumes the frequency map has values in the range of 0,100 (inclusive) and that they add up to 100."""
    val = randrange(1, 101)
    last_weight = 0
    for side, weight in frequencies.iteritems():
        if 0 < val <= last_weight + weight:
            return side
        else:
            last_weight += weight


class WorkoutState(object):

    def __init__(self, deadline):
        self.correct_hits = []
        self.incorrect_hits = []
        self.timeouts = 0
        self.deadline = deadline
        self.server_time = time.time()

    def record_hit(self, direction, reaction_time, is_correct):
        dest = self.correct_hits if is_correct else self.incorrect_hits
        dest.append(HitStats(direction, reaction_time))

    def record_timeout(self):
        self.timeouts += 1


class HitStats(object):

    def __init__(self, direction, reaction_time):
        self.direction = direction
        self.time = reaction_time


class ConfigurationError(Exception):
    pass
