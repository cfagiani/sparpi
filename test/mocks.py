import time
from random import randrange
from engine.workout_controller import WorkoutState


class Mock(object):

    def __init__(self):
        self.invocation_map = {}
        self.overrides = {}

    def get_invocation_count(self, method):
        return self.invocation_map.get(method, 0)

    def handle_invocation(self, method, *args):
        cur = self.get_invocation_count(method)
        self.invocation_map[method] = cur + 1
        override = self.overrides.get(method, None)
        if override:
            return override(args)

    def register_override(self, method, func_override):
        self.overrides[method] = func_override


class MockSensor(Mock):
    """
    Mock object that implements the accelerometer interface so we can test just the hit detector.
    """

    def __init__(self, data_provider):
        super(MockSensor, self).__init__()
        self.data_provider = data_provider
        self.pos = 0

    def get_sample(self):
        val = self.handle_invocation("get_sample")
        if val is None:
            val = self.data_provider(self.pos)
        self.pos += 1
        return val


class MockLedController(Mock):
    """
    Mock LED interface
    """

    def __init__(self, lights):
        super(MockLedController, self).__init__()
        self.lights = lights

    def activate_lights(self, lights):
        self.handle_invocation("activate_lights")

    def flash(self):
        self.handle_invocation("flash")

    def cleanup(self):
        self.handle_invocation("cleanup")


class MockHitDetector(Mock):
    """
    Mock hitDetector implementation
    """

    def __init__(self, threshold, timeout, samples, sensor):
        super(MockHitDetector, self).__init__()
        self.threshold = threshold
        self.reference_curves = {}
        self.samples = samples
        self.sensor = sensor

    def calibrate_hit(self, side, timeout):
        return self.handle_invocation("calibrate_hit", side, timeout)

    def wait_for_stability(self, timeout):
        return 0, 0, 0

    def has_valid_calibration(self):
        return True


class MockWorkoutController(Mock):

    def __init__(self):
        super(MockWorkoutController, self).__init__()
        self.cur_workout = None
        self.is_running = False

    def start_workout(self, mode, workout_time):
        self.is_running = True
        self.cur_workout = WorkoutState(time.time() + workout_time)
        while time.time() < self.cur_workout.deadline and self.is_running:
            time.sleep(1)
        self.is_running = False

    def get_state(self):
        sides = ['r', 'c', 'l']
        self.cur_workout.record_hit(sides[randrange(0, 3)], randrange(1, 8), True if randrange(0, 2) < 1 else False)
        self.cur_workout.server_time = time.time()
        return self.cur_workout

    def stop_workout(self):
        self.is_running = False
