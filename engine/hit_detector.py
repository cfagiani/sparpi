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

    def __init__(self, threshold, timeout, samples, sensor=None):
        self.threshold = threshold
        self.reference_curves = {}
        self.samples = samples
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
        baseline = self.sensor.get_sample()
        deadline = time.time() + timeout
        stable = False
        while time.time() < deadline and not stable:
            new_val = self.sensor.get_sample()
            diff = tuple(map(operator.sub, baseline, new_val))
            if all(abs(val) < self.threshold for val in diff):
                stable = True
                self.baseline = new_val
                break
        if not stable:
            raise SensorInitializationError("Sensor readings did not stabilize. Cannot calibrate.")

    def calibrate_hit(self, side, timeout):
        """
        Records a hit as the canonical representation of a hit from the specified direction. This will be used
        by later calls to wait_for_hit to determine if the hit came from the correct side or not. If no hit is
        detected within the timeout, this method throws a SensorInitializationError.

        :param side:
        :param timeout:
        :return:
        """
        val = self.wait_for_hit(None, timeout)
        if val is None:
            raise SensorInitializationError("Could not calibrate {dir} hit direction".format(dir=side))
        curves = self.reference_curves.get(side, [])
        data = self.get_samples(self.samples)
        curves.append(normalize(data))
        self.reference_curves[side] = curves

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
            for val in diff:
                if abs(val) > self.threshold:
                    samples = self.get_samples(self.samples)
                    if side is None:
                        return samples
                    else:
                        detected_side = self.get_hit_side(normalize(samples))
                        if side == detected_side:
                            return samples
                        else:
                            # TODO do we want to return something else indicating the wrong side was hit?
                            return None
        return None

    def get_hit_side(self, hit):
        min_side = None
        min_val = sys.float_info.max
        for side, ref_curves in self.reference_curves.iteritems():
            dist = 0
            for ref_curve in ref_curves:
                dist += get_procrustes_dist(hit, ref_curve)
            if dist < min_val:
                min_side = side
                min_val = dist
        return min_side

    def get_samples(self, num=1):
        samples = []
        for i in range(0, num):
            samples.append(tuple(map(operator.sub, self.baseline, self.sensor.get_sample())))
        return samples


def get_procrustes_dist(a, b):
    """ Calculates the Procrustes distance between two curves a and b. This assumes len(a) == len(b) and that each point
    in each list is the same length.
    At a high level, this computes sqrt(sum(A-B)^2)) (take the square root of the sum of squared differences of all
    coordinates in A and B)
    See https://en.wikipedia.org/wiki/Procrustes_analysis#Shape_comparison
    """
    ssds = 0
    for i, aVal in enumerate(a):
        # get the difference between the 2 points
        diff = tuple(map(operator.sub, aVal, b[i]))
        # square them (i.e. take the dot product with itself)
        ssds += sum(p * q for p, q in zip(diff, diff))
    return math.sqrt(ssds)


def normalize(data):
    """
    Returns a "normalized" copy of the data array by smoothing out the curve so it has min of -1 and max of 1
    to reduce the impact of magnitude differences when comparing curves.
    :param data:
    :return:
    """
    # initialize mins/maxes to system limits
    min_values = [sys.float_info.max, sys.float_info.max, sys.float_info.max]
    max_values = [sys.float_info.min, sys.float_info.min, sys.float_info.min]
    # iterate the data and find the min/max in each axis. Prevent storing 0 as the value
    # to prevent divide by zero errors later
    for point in data:
        for pos, val in enumerate(point):
            if val < min_values[pos] and val != 0:
                min_values[pos] = val
            if val > max_values[pos] and val != 0:
                max_values[pos] = val

    # build the "normalized" values by dividing negative values by -min and pos values by max
    results = []
    for point in data:
        normalized = [0, 0, 0]
        for pos, val in enumerate(point):
            if val > 0:
                normalized[pos] = val / max_values[pos]
            elif val < 0:
                normalized[pos] = val / (0 - min_values[pos])
            else:
                normalized[pos] = 0
        results.append(tuple(normalized))
    return results


class SensorInitializationError(Exception):
    pass
