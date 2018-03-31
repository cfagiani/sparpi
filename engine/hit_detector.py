"""
__author__ = 'Christopher Fagiani'
"""
import time
import sys
import math
import operator


class HitDetector(object):
    """
    Class that uses the accelerometer to detect when the bag is hit.
    """

    def __init__(self, threshold, timeout, samples, detect_dir=True, sensor=None):
        self.threshold = threshold
        self.reference_angles = {}
        self.baseline = None
        self.samples = samples
        self.stability_threshold = 5
        self.min_calibration_distance = 10
        self.detect_direction = detect_dir
        if sensor is None:
            from engine.io import accel
            self.sensor = accel.Accelerometer()
        else:
            self.sensor = sensor
        self.__calibrate(timeout)

    def __calibrate(self, timeout):
        """
        Performs initial calibration by getting the current, at-rest, sensor values and using those as a
        baseline that can be subtracted from later readings to return relative acceleration. If the readings
        from the sensor don't stabilize within the specified timeout, this method will throw a
        SensorInitializationError.
        :param timeout:
        :return:
        """
        baseline = self.wait_for_stability(timeout)
        if baseline:
            self.baseline = baseline
        else:
            raise SensorInitializationError("Sensor readings did not stabilize. Cannot calibrate.")

    def wait_for_stability(self, timeout):
        stable_count = 0
        deadline = time.time() + timeout
        baseline = self.baseline if self.baseline else self.sensor.get_sample()
        while time.time() < deadline and stable_count < self.samples:
            new_val = self.sensor.get_sample()
            diff = tuple(map(operator.sub, baseline, new_val))
            if get_magnitude(diff) < self.stability_threshold:
                stable_count += 1
            else:
                if self.baseline is None:
                    baseline = new_val
                stable_count = 0
        if stable_count >= self.samples:
            return baseline
        else:
            return None

    def calibrate_hit(self, side, timeout):
        """
        Records a hit as the canonical representation of a hit from the specified direction. This will be used
        by later calls to wait_for_hit to determine if the hit came from the correct side or not. If no hit is
        detected within the timeout, this method throws a SensorInitializationError.

        :param side:
        :param timeout:
        :return:
        """
        val, _ = self.wait_for_hit(None, timeout)
        if val is None:
            raise SensorInitializationError("Could not calibrate {dir} hit direction".format(dir=side))
        self.reference_angles[side] = get_angle(val)
        return self.reference_angles[side]

    def wait_for_hit(self, side, timeout):
        """
        Waits for a hit by continually reading from the sensor until readings exceed the configured threshold or
        the timeout elapses.

        :param side:
        :param timeout:
        :return: either a tuple containing acceleration in each direction or None (if no hit was detected before timeout)
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            new_val = self.sensor.get_sample()
            diff = tuple(map(operator.sub, self.baseline, new_val))
            mag = get_magnitude(diff)
            if mag > self.threshold:
                if side is None:
                    return diff, True
                else:
                    if self.detect_direction:
                        detected_side = get_hit_side(self.reference_angles, get_angle(diff))
                    else:
                        return diff, True
                if side == detected_side:
                    return diff, True
                else:
                    return diff, False
        return None, False

    def has_valid_calibration(self):
        """
        Returns True if all calibrated sides are at least min_calibration_distance apart.
        :return:
        """
        if len(list(self.reference_angles.itervalues())) != 3:
            return False
        for i, ang in self.reference_angles.iteritems():
            for j, val in self.reference_angles.iteritems():
                if i != j and abs(val - ang) < self.min_calibration_distance:
                    return False

        return True


def get_magnitude(data):
    """Computes the magnitude of the hit vector."""
    return math.sqrt(sum([a * a for a in data]))


def get_hit_side(reference_angles, hit_angle):
    """Determines which reference_angle is closest to the hit_angle and returns that label."""
    min_side = None
    min_val = sys.float_info.max
    for side, ref_angle in reference_angles.iteritems():
        dist = abs(ref_angle - hit_angle)
        if dist < min_val:
            min_side = side
            min_val = dist
    return min_side


def get_angle(hit):
    """
    Computes the angle of a hit.
    :param hit:
    :return:
    """
    mag = get_magnitude(hit)
    if mag == 0:
        mag = 1
    x = math.acos(hit[0] / mag)
    y = math.acos(hit[1] / mag)
    angle = ((math.atan2(y, x) * 180) / math.pi) + 180
    return angle


class SensorInitializationError(Exception):
    pass
