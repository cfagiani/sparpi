import unittest
import os
from mocks import MockSensor
from engine import hit_detector

DATA_DIR_PATH = os.path.join(os.path.dirname(__file__), 'data')


class TestHitDetector(unittest.TestCase):

    def test_procrustes_dist_identity(self):
        self.assertEquals(0, hit_detector.get_procrustes_dist([(1, 2, 3)], [(1, 2, 3)]))

    def test_procrustes_dist_pos(self):
        self.assertTrue(hit_detector.get_procrustes_dist([(1, 2, 3)], [(10, 2, 3)]) > 0)

    def test_initialization_timeout(self):
        sensor = MockSensor(lambda x: [x * 2, x * 2, x * 2])
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
        sensor = MockSensor(lambda x: [x * 2, x * 2, x * 2])
        timeout = 1
        detector = hit_detector.HitDetector(3, timeout, 1, sensor)
        detector.calibrate_hit('r', 1)

    def test_normalization(self):
        data = read_sample_file("c1.txt")
        normalized = hit_detector.normalize(data)
        for point in normalized:
            for val in point:
                self.assertTrue(1 >= val >= -1)

    def test_normalized_dist(self):
        data1 = read_sample_file("c1.txt")
        data2 = read_sample_file("c2.txt")
        dist = hit_detector.get_procrustes_dist(data1, data2)
        norm_dist = hit_detector.get_procrustes_dist(hit_detector.normalize(data1), hit_detector.normalize(data2))
        self.assertTrue(norm_dist < dist)


def read_sample_file(filename):
    data = []
    with open(os.path.join(DATA_DIR_PATH, filename), "r") as in_file:
        for line in in_file.readlines():
            data.append(tuple([float(x) for x in line.split(",")]))
    return data
