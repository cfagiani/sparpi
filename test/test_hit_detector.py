import unittest
import os
from mocks import MockSensor
from engine import hit_detector

DATA_DIR_PATH = os.path.join(os.path.dirname(__file__), 'data')


class TestHitDetector(unittest.TestCase):

    def test_initialization_timeout(self):
        sensor = MockSensor(lambda x: [x * 12, x * 12, x * 12])
        timeout = 1
        try:
            hit_detector.HitDetector(1, timeout, 1, sensor)
            self.assertTrue(False, "Expected a timeout")
        except Exception as e:
            self.assertEquals(type(e), hit_detector.SensorInitializationError)

    def test_calibration_timeout(self):
        sensor = MockSensor(lambda x: [0, 0, 0])
        timeout = 1
        finished_init = False
        got_error = False
        try:
            detector = hit_detector.HitDetector(1, timeout, 1, sensor)
            finished_init = True
            detector.calibrate_hit('r', 1)
        except Exception as e:
            self.assertEquals(type(e), hit_detector.SensorInitializationError)
            got_error = True
        self.assertTrue(got_error)
        self.assertTrue(finished_init)

    def test_calibration(self):
        sensor = MockSensor(lambda x: [0, 0, 0] if x <= 4 else [5, 5, 5])
        timeout = 10
        detector = hit_detector.HitDetector(3, timeout, 1, sensor)
        detector.calibrate_hit('r', timeout)

    def test_zero_magnitude(self):
        mag = hit_detector.get_magnitude((0, 0, 0))
        self.assertEqual(0.0, mag)

    def test_magnitude(self):
        self.assertEqual(hit_detector.get_magnitude((1, 10, 1)), hit_detector.get_magnitude((10, 1, 1)))

    def test_get_angle(self):
        # hit with value only in X axis should be 270 degrees
        self.assertEqual(270.0, hit_detector.get_angle((100, 0, 0)))
        # only Y should be 180
        self.assertEqual(180.0, hit_detector.get_angle((0, 100, 0)))
        # X and Y should be 225
        self.assertEqual(225.0, hit_detector.get_angle((100, 100, 0)))


def read_sample_file(filename):
    data = []
    sample_len = 0
    with open(os.path.join(DATA_DIR_PATH, filename), "r") as in_file:
        for line in in_file.readlines():
            if sample_len > 2:
                break
            data.append(tuple([float(x) for x in line.split(",")]))
            sample_len += 1
    return data
