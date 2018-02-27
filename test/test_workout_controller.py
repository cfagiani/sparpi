import unittest
import os
from engine import workout_controller
from engine.workout_controller import ConfigurationError
from engine.hit_detector import SensorInitializationError
from mocks import MockHitDetector
from mocks import MockLedController
from mocks import MockSensor

DATA_DIR_PATH = os.path.join(os.path.dirname(__file__), 'data')


class TestWorkoutController(unittest.TestCase):

    def setUp(self):
        """
        Sets up default mocked dependencies for use in the controller constructor
        :return:
        """
        self.detector = MockHitDetector(1, 1, 1, MockSensor(lambda x: (x, x, x)))
        self.led = MockLedController({'r': 1, 'c': 2, 'l': 3})

    def test_initialization(self):
        """
        Ensure the initialization calibrates orientation.
        :return:
        """

        controller = workout_controller.WorkoutController(os.path.join(DATA_DIR_PATH, "test.ini"),
                                                          controller=self.led,
                                                          detector=self.detector)
        controller.calibrate_orientation()
        self.assertEqual(1, self.led.get_invocation_count("flash"))
        self.assertEqual(3, self.detector.get_invocation_count("calibrate_hit"))

    def test_calibration_error(self):
        """
        Ensures that an exception during initialization will trigger call to cleanup
        :return:
        """
        got_error = False
        self.detector.register_override("calibrate_hit", throw_error)
        try:
            controller = workout_controller.WorkoutController(os.path.join(DATA_DIR_PATH, "test.ini"),
                                                              controller=self.led,
                                                              detector=self.detector)
            controller.calibrate_orientation()
        except Exception as e:
            self.assertEquals(type(e), SensorInitializationError)
            got_error = True
        self.assertTrue(got_error)

    def test_single_side_selection(self):
        freq = {'l': 0, 'c': 0, 'r': 100}
        for i in range(1000):
            self.assertEqual(workout_controller.get_next_side(freq), 'r')

    def test_two_side_selection(self):
        freq = {'l': 50, 'c': 0, 'r': 50}
        for i in range(1000):
            self.assertNotEqual(workout_controller.get_next_side(freq), 'c')

    def test_frequency_validation_over_100(self):
        try:
            workout_controller.validate_frequencies({'l': 50, 'c': 0, 'r': 51})
            self.assertFalse(True, "Expected exception")
        except Exception as e:
            self.assertEquals(type(e), ConfigurationError)

    def test_frequency_validation_negative(self):
        try:
            workout_controller.validate_frequencies({'l': -5, 'c': 55, 'r': 50})
            self.assertFalse(True, "Expected exception")
        except Exception as e:
            self.assertEquals(type(e), ConfigurationError)


def throw_error(val):
    raise SensorInitializationError
