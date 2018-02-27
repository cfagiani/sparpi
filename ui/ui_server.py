"""
__author__ = 'Christopher Fagiani'
"""
import json
import threading
import logging
import time
import os
from engine.workout_controller import HitStats
from engine.hit_detector import SensorInitializationError

RESOURCE_DIR_PATH = os.path.join(os.path.dirname(__file__), 'resources')

try:
    from flask import Flask, request, send_from_directory
except ImportError:
    raise ImportError("flask is not installed. Please install (sudo apt-get install flask)")

logger = logging.getLogger(__name__)
app = Flask(__name__)
apiInstance = None


@app.route('/')
def root():
    return send_from_directory(RESOURCE_DIR_PATH, 'index.html')


@app.route('/js/<path:path>')
def js(path):
    return send_from_directory(RESOURCE_DIR_PATH + '/js', path)


@app.route('/css/<path:path>')
def css(path):
    return send_from_directory(RESOURCE_DIR_PATH + '/css', path)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(RESOURCE_DIR_PATH + '/img', "favicon.ico")


@app.route("/workout", methods=["PUT"])
def start_workout():
    global apiInstance
    config = request.json
    apiInstance.start_workout(config)
    return '{"msg": "Workout Started"}', 201


@app.route("/workout", methods=["POST"])
def stop_workout():
    apiInstance.stop_workout()
    time.sleep(3);
    return '{"msg": "Workout Stopped"}', 202


@app.route("/workout", methods=["GET"])
def get_status():
    """Returns current workout status
    """
    global apiInstance
    return apiInstance.get_status()


@app.route("/calibration", methods=["POST"])
def trigger_calibration():
    """
    Runs calibration.
    :return:
    """
    global apiInstance
    try:
        apiInstance.trigger_calibration()
        return '{"msg": "Calibrated"}', 200
    except SensorInitializationError:
        return '{"msg": "Calibration failed"}', 500



class SparpiServer:
    def __init__(self, port, workout_controller):
        """Sets up the Flask webserver to run on the port passed in
        """
        global apiInstance
        self.driver = workout_controller
        self.port = port
        self.workout_thread = None

        apiInstance = self

    def start(self):
        thread = threading.Thread(target=self.run_app)
        thread.daemon = False
        thread.start()

    def run_app(self):
        app.run(host="0.0.0.0", port=self.port)

    def start_workout(self, config):
        if not self.driver.has_valid_calibration():
            self.driver.calibrate_orientation()
        if self.workout_thread is None or not self.workout_thread.isAlive():
            self.workout_thread = threading.Thread(target=self.driver.start_workout, args=(config['mode'],
                                                                                           config['time'],
                                                                                           config['frequencies']))
            self.workout_thread.start()

    def stop_workout(self):
        self.driver.stop_workout()

    def get_status(self):
        workout_data = self.driver.get_state()
        return json.dumps(workout_data, default=serialize_status)

    def trigger_calibration(self):
        self.driver.calibrate_orientation()


def serialize_status(obj):
    if isinstance(obj, HitStats):
        return obj.__dict__
    else:
        return obj.__dict__
