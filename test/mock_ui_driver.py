from mocks import MockWorkoutController
from ui import ui_server

"""
Simple utility to run the UI/API server with a mocked controller. You can run from the project root with:
python -m test.mock_ui_driver
"""


def run():
    controller = MockWorkoutController()
    api = ui_server.SparpiServer(8888, controller)
    api.start()


if __name__ == "__main__":
    run()
