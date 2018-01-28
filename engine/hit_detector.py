"""
__author__ = 'Christopher Fagiani'
"""

from engine.io import accel
import time

sensor = accel.Accelerometer()


class HitDetector(object):
    """
    Class that uses the accelerometer to detect when the bag is hit.
    """

    def __init__(self, threshold, timeout, samples, debug=False):
        self.threshold = threshold
        self.orientation = {'r': [0, 0, 0], 'c': [0, 0, 0], 'l': [0, 0, 0]}
        self.samples = samples
        self.debug = debug
        self.__calibrate(timeout)

    def __calibrate(self, timeout):
        baseline = sensor.get_sample()
        deadline = time.time() + timeout
        stable = False
        while time.time() < deadline and not stable:
            new_val = sensor.get_sample()
            diff = tuple(x - y for x, y in zip(baseline, new_val))
            for val in diff:
                if abs(val) > self.threshold:
                    continue
            stable = True
            self.baseline = new_val
            break
        if not stable:
            raise SensorInitializationError("Sensor readings did not stabilize. Cannot calibrate.")

    def calibrate_hit(self, side, timeout):
        val = self.wait_for_hit(None, timeout)
        if val is None:
            raise SensorInitializationError("Could not calibrate {dir} hit direction".format(dir=side))
        max_item = max(enumerate(val), key=lambda item: abs(item[1]))
        self.orientation[side][max_item[0]] = 1 if max_item[1] > 0 else -1

    def wait_for_hit(self, side, timeout):
        deadline = time.time() + timeout
        while time.time() < deadline:
            new_val = sensor.get_sample()
            diff = tuple(x - y for x, y in zip(self.baseline, new_val))
            for val in diff:
                if abs(val) > self.threshold:
                    diff = self.get_more_samples(diff)
                    self.wait_for_recoil(diff)
                    # TODO fix side detection. current version is inaccurate
                    # if side is None or side == self.get_hit_side(diff):
                    return diff
                    # else:
                    # TODO do we want to return something else indicating the wrong side was hit?
                    #   return None
        return None

    def get_hit_side(self, hit):
        max_item = max(enumerate(hit), key=lambda item: abs(item[1]))
        orientation = [0, 0, 0]
        orientation[max_item[0]] = 1 if max_item[1] > 0 else -1
        for side, ref_orientation in self.orientation.iteritems():
            if ref_orientation == orientation:
                return side
        return None

    def get_more_samples(self, diff):
        max_value = sum([abs(z) for z in diff])
        max_reading = diff
        for i in range(0, self.samples):
            new_reading = sensor.get_sample()
            if self.debug:
                print new_reading
            new_max = sum([abs(z) for z in new_reading])
            if new_max > max_value:
                max_reading = new_reading
                max_value = new_max
        return max_reading

    def wait_for_recoil(self, diff):
        pass


class SensorInitializationError(Exception):
    pass
