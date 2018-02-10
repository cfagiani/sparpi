import unittest
import os
from engine import workout_controller
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

        workout_controller.WorkoutController(os.path.join(DATA_DIR_PATH, "test.ini"),
                                             controller=self.led,
                                             detector=self.detector)
        self.assertEqual(1, self.led.get_invocation_count("flash"))
        self.assertEqual(3, self.detector.get_invocation_count("calibrate_hit"))

    def test_init_exception_triggers_cleanup(self):
        """
        Ensures that an exception during initialization will trigger call to cleanup
        :return:
        """

        self.detector.register_override("calibrate_hit", throw_error)
        try:
            controller = workout_controller.WorkoutController(os.path.join(DATA_DIR_PATH, "test.ini"),
                                                              controller=self.led,
                                                              detector=self.detector)
        except Exception as e:
            self.assertEquals(type(e), SensorInitializationError)
        self.assertEqual(1, self.led.get_invocation_count("cleanup"))


def throw_error(val):
    raise SensorInitializationError
